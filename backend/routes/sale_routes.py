from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.db import get_db_cursor
from psycopg2 import sql 
from backend.utils.helpers import get_user_and_role, check_admin_permission, validate_required_fields, check_seller_permission
from backend.utils.bcv_api import get_dolarvzla_rate 
from backend.utils.inventory_utils import verificar_stock_y_alertar, STOCK_THRESHOLD
import logging
from decimal import Decimal
import uuid
from datetime import datetime, timedelta
import bcrypt

sale_bp = Blueprint('sale', __name__, url_prefix='/api/sales')
app_logger = logging.getLogger('backend.routes.sale_routes') 

# =========================================================
# CONSTANTES GLOBALES
# =========================================================

SALES_ROLES = ['admin', 'vendedor'] 
PAYMENT_TOLERANCE = 0.01 
DEFAULT_CREDIT_DAYS = 30

# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def normalize_payment_type(tipo_pago_raw):
    """Normaliza el tipo de pago a formato consistente"""
    if not tipo_pago_raw:
        return 'contado'
    return tipo_pago_raw.lower().replace('é', 'e').strip()

def validate_payment_amounts(usd_paid_raw, ves_paid_raw):
    """Valida y convierte montos de pago"""
    try:
        usd_paid = float(usd_paid_raw) if usd_paid_raw not in [None, ''] else 0.0
        ves_paid = float(ves_paid_raw) if ves_paid_raw not in [None, ''] else 0.0
        
        if usd_paid < 0 or ves_paid < 0:
            raise ValueError("Los montos de pago deben ser positivos.")
            
        return usd_paid, ves_paid
    except (ValueError, TypeError) as e:
        raise ValueError(f"Los montos de pago deben ser números válidos: {e}")

def validate_credit_days(dias_credito_raw):
    """Valida y establece días de crédito por defecto"""
    try:
        dias_credito = int(dias_credito_raw) if dias_credito_raw not in [None, ''] else DEFAULT_CREDIT_DAYS
        return max(1, dias_credito)  # Mínimo 1 día
    except (ValueError, TypeError):
        return DEFAULT_CREDIT_DAYS

def calculate_payment_totals(total_amount_usd, usd_paid, ves_paid, exchange_rate):
    """Calcula totales de pago y saldo pendiente"""
    usd_from_ves = ves_paid / exchange_rate if exchange_rate > 0 else 0.0
    total_paid_usd = usd_paid + usd_from_ves
    saldo_pendiente = max(0.0, round(total_amount_usd - total_paid_usd, 2))
    
    return total_paid_usd, saldo_pendiente

def handle_credit_sale_validation(cancellation_code):
    """Maneja la validación para ventas a crédito"""
    if not cancellation_code:
        return jsonify({"msg": "Se requiere el código de cancelación para ventas a crédito."}), 400
    return None  # No hay error

def build_sale_insert_query(is_credit_sale, fields, values, dias_credito, monto_pendiente, fecha_vencimiento, cancellation_code):
    """Construye la consulta de inserción de venta dinámicamente"""
    if is_credit_sale:
        fields.extend(["dias_credito", "balance_due_usd", "fecha_vencimiento", "cancellation_code"])
        values.extend([dias_credito, monto_pendiente, fecha_vencimiento, cancellation_code])

    placeholders = sql.SQL(', ').join(sql.Placeholder() * len(fields))
    
    return sql.SQL("INSERT INTO sales ({}) VALUES ({}) RETURNING id").format(
        sql.SQL(', ').join(map(sql.Identifier, fields)),
        placeholders
    )

def determine_sale_status(is_credit_sale, balance_due, paid_amount):
    """Determina el estado correcto de la venta"""
    if not is_credit_sale:
        return 'Completado'
    
    if balance_due <= PAYMENT_TOLERANCE:
        return 'Pagado'
    elif paid_amount > 0:
        return 'Abonado'
    else:
        return 'Crédito'

# =========================================================
# RUTAS DE VENTA
# =========================================================

@sale_bp.route('', methods=['GET', 'POST'])
@jwt_required()
def sales_collection():
    """Maneja la creación de una nueva venta (POST) y el listado de ventas (GET)."""
    current_user_id, user_role = get_user_and_role() 
    
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado o token inválido"}), 401
    
    if not check_seller_permission(user_role):
        return jsonify({"msg": "Acceso denegado: solo personal de ventas y administradores pueden acceder a ventas"}), 403

    if request.method == "POST":
        return handle_sale_creation(current_user_id, user_role)
    elif request.method == "GET":
        return handle_sales_listing(current_user_id, user_role)

def handle_sale_creation(current_user_id, user_role):
    """Maneja la creación de una nueva venta"""
    data = request.get_json()
    
    # Validación básica
    required_fields = ['customer_id', 'items']
    if error := validate_required_fields(data, required_fields):
        return jsonify({"msg": f"Missing required fields: {error}"}), 400
    
    # Extracción y validación de datos
    try:
        customer_id = data.get("customer_id")
        items = data.get("items")
        tipo_pago_raw = data.get('tipo_pago', 'Contado')
        dias_credito_raw = data.get('dias_credito') 
        usd_paid_raw = data.get('usd_paid', 0)
        ves_paid_raw = data.get('ves_paid', 0)
        cancellation_code = data.get("cancellation_code")
        
        # Validaciones
        if not isinstance(items, list) or len(items) == 0:
            return jsonify({"msg": "Items must be a non-empty list of products"}), 400
        
        # Procesamiento de datos
        tipo_pago_normalized = normalize_payment_type(tipo_pago_raw)
        is_credit_sale = tipo_pago_normalized == 'credito'
        usd_paid, ves_paid = validate_payment_amounts(usd_paid_raw, ves_paid_raw)
        dias_credito = validate_credit_days(dias_credito_raw) if is_credit_sale else 0
        
        # Validación para crédito
        if is_credit_sale:
            error_response = handle_credit_sale_validation(cancellation_code)
            if error_response:
                return error_response

        # Obtener tasa de cambio
        try:
            exchange_rate = get_dolarvzla_rate()
        except Exception as e:
            app_logger.error(f"FATAL: No se pudo obtener la tasa de cambio: {e}", exc_info=True)
            return jsonify({"msg": "Error interno: No se pudo obtener la tasa de cambio del sistema"}), 500

        # Procesar la venta en transacción
        return process_sale_transaction(
            customer_id, items, tipo_pago_raw, is_credit_sale, 
            usd_paid, ves_paid, dias_credito, exchange_rate,
            cancellation_code, current_user_id
        )
        
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400
    except Exception as e:
        app_logger.error(f"Error inesperado en creación de venta: {e}", exc_info=True)
        return jsonify({"msg": "Error interno del servidor"}), 500

def process_sale_transaction(customer_id, items, tipo_pago_raw, is_credit_sale, 
                           usd_paid, ves_paid, dias_credito, exchange_rate,
                           cancellation_code, seller_user_id):
    """Procesa la venta dentro de una transacción"""
    cur = None
    try:
        with get_db_cursor(commit=False) as cur: 
            # Validar stock y calcular totales
            total_amount_usd, validated_items = validate_stock_and_calculate_totals(cur, items)
            if isinstance(total_amount_usd, tuple):  # Error ocurrió
                return total_amount_usd

            total_amount_ves = total_amount_usd * exchange_rate
            total_paid_usd, saldo_pendiente = calculate_payment_totals(
                total_amount_usd, usd_paid, ves_paid, exchange_rate
            )

            # Validar pago para ventas al contado
            if not is_credit_sale and saldo_pendiente > PAYMENT_TOLERANCE:
                cur.connection.rollback()
                return jsonify({
                    "msg": f"Monto pagado insuficiente para venta al contado. Saldo pendiente: ${saldo_pendiente:.2f}"
                }), 400

            # Determinar estado inicial
            initial_status = determine_sale_status(is_credit_sale, saldo_pendiente, usd_paid)
            
            # Procesar crédito si aplica
            monto_pendiente, fecha_vencimiento = process_credit_sale(
                cur, is_credit_sale, customer_id, saldo_pendiente, dias_credito, initial_status
            )
            if isinstance(monto_pendiente, tuple):  # Error ocurrió
                return monto_pendiente

            # Insertar venta
            new_sale_id = insert_sale_record(
                cur, customer_id, seller_user_id, total_amount_usd, total_amount_ves,
                exchange_rate, initial_status, tipo_pago_raw, usd_paid, ves_paid,
                is_credit_sale, dias_credito, monto_pendiente, fecha_vencimiento, cancellation_code
            )

            # Procesar items y stock
            stock_alerts = process_sale_items_and_stock(cur, new_sale_id, validated_items)

            cur.connection.commit()
            
            # Construir respuesta
            return build_success_response(
                new_sale_id, tipo_pago_raw, total_amount_usd, total_amount_ves,
                exchange_rate, usd_paid, ves_paid, monto_pendiente, stock_alerts,
                is_credit_sale, cancellation_code, initial_status
            )
                
    except Exception as e:
        if cur and cur.connection:
            cur.connection.rollback()
        app_logger.error(f"Error en transacción de venta: {e}", exc_info=True)
        return jsonify({"msg": f"Error al registrar la venta: {str(e)}"}), 500

def validate_stock_and_calculate_totals(cur, items):
    """Valida stock y calcula totales de la venta"""
    total_amount_usd = 0.0
    validated_items = []

    for item in items:
        # Validar campos requeridos
        if error := validate_required_fields(item, ['product_id', 'quantity']):
            return jsonify({"msg": f"Each item missing field: {error}"}), 400
            
        product_id = item.get('product_id')
        quantity_raw = item.get('quantity')
        
        # Validar cantidad
        try:
            quantity = int(quantity_raw)
            if quantity <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({"msg": f"La cantidad ({quantity_raw}) debe ser un número entero válido y positivo"}), 400
            
        # Verificar producto y stock
        cur.execute("SELECT name, price, stock FROM products WHERE id = %s FOR UPDATE", (product_id,))
        product_row = cur.fetchone()
        
        if not product_row:
            return jsonify({"msg": f"Producto con ID {product_id} no encontrado"}), 404
            
        current_stock = product_row['stock']
        product_name = product_row['name']
        price_usd = float(product_row['price'])
        
        if current_stock < quantity:
            return jsonify({"msg": f"Stock insuficiente para {product_name}. Stock actual: {current_stock}"}), 400
            
        # Calcular subtotal
        subtotal_usd = price_usd * quantity
        total_amount_usd += subtotal_usd
        
        validated_items.append({
            'product_id': product_id,
            'quantity': quantity,
            'price': price_usd, 
            'current_stock': current_stock,
            'product_name': product_name
        })

    return total_amount_usd, validated_items

def process_credit_sale(cur, is_credit_sale, customer_id, saldo_pendiente, dias_credito, initial_status):
    """Procesa lógica específica para ventas a crédito"""
    monto_pendiente = 0.0
    fecha_vencimiento = None
    
    if is_credit_sale:
        monto_pendiente = saldo_pendiente
        
        # Verificar límite de crédito del cliente
        cur.execute(
            "SELECT credit_limit_usd, balance_pendiente_usd FROM customers WHERE id = %s FOR UPDATE",
            (customer_id,)
        )
        customer = cur.fetchone()

        if not customer:
            return jsonify({"msg": "Cliente de crédito no encontrado"}), 404

        limite = float(customer['credit_limit_usd'])
        balance = float(customer['balance_pendiente_usd'])
        
        nuevo_balance = balance + monto_pendiente
        
        # Verificar límite
        if nuevo_balance > limite:
            return jsonify({
                "msg": f"Límite de crédito excedido. Límite: ${limite}, Pendiente Actual: ${balance}, Venta con abono (Pendiente): ${monto_pendiente:.2f}. Nuevo Balance: ${nuevo_balance:.2f}",
                "code": "CREDIT_LIMIT_EXCEEDED"
            }), 400
            
        # Actualizar balance del cliente SOLO si es crédito pendiente
        if initial_status in ['Crédito', 'Abonado']:
            cur.execute(
                "UPDATE customers SET balance_pendiente_usd = %s WHERE id = %s",
                (nuevo_balance, customer_id)
            )
        
        # Calcular fecha de vencimiento
        fecha_vencimiento = datetime.now().date() + timedelta(days=dias_credito)
    
    return monto_pendiente, fecha_vencimiento

def insert_sale_record(cur, customer_id, seller_user_id, total_amount_usd, total_amount_ves,
                      exchange_rate, status, tipo_pago_raw, usd_paid, ves_paid,
                      is_credit_sale, dias_credito, monto_pendiente, fecha_vencimiento, cancellation_code):
    """Inserta el registro de la venta en la base de datos"""
    fields = [
        "id", "customer_id", "user_id", "sale_date", "total_amount_usd", 
        "total_amount_ves", "exchange_rate_used", "status", "tipo_pago", 
        "usd_paid", "ves_paid", "paid_amount_usd"
    ]
    
    values = [
        str(uuid.uuid4()), customer_id, seller_user_id, datetime.now(), 
        total_amount_usd, total_amount_ves, exchange_rate, status, 
        tipo_pago_raw, usd_paid, ves_paid, usd_paid  # paid_amount_usd inicial = usd_paid
    ]
    
    query = build_sale_insert_query(
        is_credit_sale, fields, values, dias_credito, 
        monto_pendiente, fecha_vencimiento, cancellation_code
    )
    
    cur.execute(query, values)
    return cur.fetchone()['id']

def process_sale_items_and_stock(cur, sale_id, validated_items):
    """Procesa los items de la venta y actualiza stock"""
    stock_alerts = []
    
    for item in validated_items:
        # Insertar item de venta - USANDO LA COLUMNA CORRECTA 'price'
        cur.execute(
            "INSERT INTO sale_items (sale_id, product_id, quantity, price) VALUES (%s, %s, %s, %s);",
            (sale_id, item['product_id'], item['quantity'], item['price'])
        )
        
        # Actualizar stock
        cur.execute(
            "UPDATE products SET stock = stock - %s WHERE id = %s;",
            (item['quantity'], item['product_id'])
        )
        
        # Verificar alertas de stock
        remaining_stock = item['current_stock'] - item['quantity']
        if remaining_stock <= STOCK_THRESHOLD:
            alert_msg = verificar_stock_y_alertar(item['product_id']) 
            if alert_msg:
                stock_alerts.append(alert_msg)
    
    return stock_alerts

def build_success_response(new_sale_id, tipo_pago_raw, total_amount_usd, total_amount_ves,
                          exchange_rate, usd_paid, ves_paid, monto_pendiente, stock_alerts,
                          is_credit_sale, cancellation_code, status):
    """Construye la respuesta de éxito"""
    response = {
        "msg": f"Venta {tipo_pago_raw} registrada exitosamente", 
        "sale_id": str(new_sale_id),
        "total_usd": round(total_amount_usd, 2),
        "total_ves": round(total_amount_ves, 2),
        "rate_used": exchange_rate,
        "tipo_pago": tipo_pago_raw,
        "usd_paid": usd_paid,
        "ves_paid": ves_paid,
        "balance_due_usd": monto_pendiente,
        "status": status,
        "stock_alerts": stock_alerts
    }
    
    if is_credit_sale:
        response["cancellation_code"] = cancellation_code
    
    return jsonify(response), 201

def handle_sales_listing(current_user_id, user_role):
    """Maneja el listado de ventas"""
    try:
        base_query = """
            SELECT 
                s.id,
                s.customer_id,
                c.name as customer_name,
                c.email as customer_email,
                c.cedula as customer_cedula,
                s.sale_date,
                s.status,
                s.tipo_pago,
                s.usd_paid,
                s.ves_paid,
                s.total_amount_usd,
                s.total_amount_ves,
                s.exchange_rate_used,
                u.email as seller_email,
                u.id as seller_id,
                s.balance_due_usd,
                s.paid_amount_usd,
                s.fecha_vencimiento,
                s.dias_credito,
                s.cancellation_code,
                json_agg(json_build_object(
                    'product_id', p.id,
                    'product_name', p.name,
                    'quantity', si.quantity,
                    'price_usd', si.price  -- CORREGIDO: usar 'price' en lugar de 'price_usd'
                )) AS items
            FROM sales s
            JOIN customers c ON s.customer_id = c.id
            JOIN users u ON s.user_id = u.id 
            JOIN sale_items si ON s.id = si.sale_id
            JOIN products p ON si.product_id = p.id
        """
        params = []
        
        # Filtro de permisos
        if not check_admin_permission(user_role): 
            base_query += " WHERE s.user_id = %s"
            params.append(current_user_id)
        
        # Agrupación y ordenamiento
        base_query += """
            GROUP BY s.id, c.name, c.email, c.cedula, s.sale_date, s.status, 
            s.tipo_pago, s.usd_paid, s.ves_paid, s.total_amount_usd, s.total_amount_ves, 
            s.exchange_rate_used, u.email, u.id, s.balance_due_usd, s.paid_amount_usd,
            s.fecha_vencimiento, s.dias_credito, s.cancellation_code
            ORDER BY s.sale_date DESC;
        """
        
        with get_db_cursor() as cur:
            cur.execute(base_query, tuple(params))
            sales_list = [dict(record) for record in cur.fetchall()]
            
        return jsonify(sales_list), 200
        
    except Exception as e:
        app_logger.error(f"Error al obtener las ventas: {e}", exc_info=True)
        return jsonify({"msg": "Error al obtener las ventas", "error": str(e)}), 500

@sale_bp.route('/customers-with-credit', methods=['GET'])
@jwt_required()
def get_customers_with_credit():
    """Obtiene clientes que tienen saldo pendiente de crédito"""
    current_user_id, user_role = get_user_and_role()
    
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado o token inválido"}), 401
    
    try:
        search_term = request.args.get('search', '').strip()
        
        base_query = """
            SELECT 
                id,
                name,
                cedula,
                email,
                balance_pendiente_usd as saldo_pendiente
            FROM customers 
            WHERE balance_pendiente_usd > 0
        """
        
        params = []
        
        if search_term:
            # Buscar por cédula o nombre
            base_query += " AND (cedula::text LIKE %s OR name ILIKE %s)"
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern])
        
        base_query += " ORDER BY balance_pendiente_usd DESC, name"
        
        with get_db_cursor() as cur:
            cur.execute(base_query, tuple(params))
            customers = []
            
            for record in cur.fetchall():
                # Obtener ventas activas de crédito para este cliente
                cur.execute("""
                    SELECT COUNT(*) as count
                    FROM sales 
                    WHERE customer_id = %s 
                    AND status IN ('Crédito', 'Abonado')
                    AND balance_due_usd > 0
                """, (record['id'],))
                
                ventas_info = cur.fetchone()
                
                customer_data = {
                    'id': record['id'],
                    'name': record['name'],
                    'cedula': str(record['cedula']) if record['cedula'] else 'N/A',
                    'email': record['email'] or '',
                    'saldo_pendiente': float(record['saldo_pendiente'] or 0),
                    'ventas_credito_activas': ventas_info['count'] or 0
                }
                customers.append(customer_data)
            
        return jsonify(customers), 200
        
    except Exception as e:
        app_logger.error(f"Error al obtener clientes con crédito: {e}", exc_info=True)
        return jsonify({"msg": "Error interno del servidor al buscar clientes"}), 500

@sale_bp.route('/customer/<customer_id>/credit-sales', methods=['GET'])
@jwt_required()
def get_customer_credit_sales(customer_id):
    """Obtiene las ventas a crédito pendientes de un cliente específico"""
    current_user_id, user_role = get_user_and_role()
    
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado o token inválido"}), 401
    
    try:
        with get_db_cursor() as cur:
            # Verificar que el cliente existe
            cur.execute("SELECT id, name FROM customers WHERE id = %s", (customer_id,))
            customer = cur.fetchone()
            
            if not customer:
                return jsonify({"msg": "Cliente no encontrado"}), 404
            
            # Obtener ventas a crédito pendientes y abonadas para mejoes practicas
            cur.execute("""
                SELECT 
                    id,
                    sale_date,
                    total_amount_usd,
                    balance_due_usd,
                    paid_amount_usd,
                    dias_credito,
                    fecha_vencimiento,
                    cancellation_code,
                    status
                FROM sales 
                WHERE customer_id = %s 
                AND status IN ('Crédito', 'Abonado')
                AND balance_due_usd > 0
                ORDER BY sale_date DESC
            """, (customer_id,))
            
            sales = []
            for record in cur.fetchall():
                sale_data = {
                    'id': record['id'],
                    'sale_date': record['sale_date'].isoformat() if record['sale_date'] else None,
                    'total_amount_usd': float(record['total_amount_usd'] or 0),
                    'balance_due_usd': float(record['balance_due_usd'] or 0),
                    'paid_amount_usd': float(record['paid_amount_usd'] or 0),
                    'dias_credito': record['dias_credito'] or 0,
                    'fecha_vencimiento': record['fecha_vencimiento'].isoformat() if record['fecha_vencimiento'] else None,
                    'cancellation_code': record['cancellation_code'],
                    'status': record['status']
                }
                sales.append(sale_data)
            
            return jsonify(sales), 200
            
    except Exception as e:
        app_logger.error(f"Error al obtener ventas a crédito del cliente: {e}", exc_info=True)
        return jsonify({"msg": "Error al cargar las ventas del cliente"}), 500

@sale_bp.route('/pay-credit', methods=['POST'])
@jwt_required()
@check_seller_permission
def pay_credit():
    """Registra un abono o pago completo a una venta a crédito."""
    
    # Asegúrate de que Decimal y sql estén importados
    from decimal import Decimal
    from psycopg2 import sql 
    
    # La variable global PAYMENT_TOLERANCE DEBE ESTAR DEFINIDA al inicio del archivo
    PAYMENT_TOLERANCE = Decimal('0.01') 

    # 1. Obtener datos y validar
    data = request.get_json()
    required = ['sale_id', 'payment_amount', 'payment_currency', 'cancellation_code']

    if error := validate_required_fields(data, required):
        return jsonify({'msg': f'Campo requerido faltante: {error}'}), 400

    try:
        sale_id = data['sale_id']
        raw_payment_amount = Decimal(str(data['payment_amount'])) 
        payment_currency = data['payment_currency'].upper()
        cancellation_code_input = data['cancellation_code'].strip()
        exchange_rate = Decimal(str(data.get('exchange_rate', 1)))
        # NUEVO: Obtener el método de pago (ej: 'transferencia', 'punto', 'efectivo')
        payment_method_input = data.get('payment_method', payment_currency).strip()


        if raw_payment_amount <= 0:
            return jsonify({'msg': 'El monto de pago debe ser positivo.'}), 400

        if payment_currency == 'VES' and exchange_rate <= 0:
            return jsonify({'msg': 'Se requiere una tasa de cambio válida para pagos en VES.'}), 400
        
        # 2. Conectar y obtener datos de la venta
        with get_db_cursor() as cur:
            # Bloquear la fila de la venta para evitar concurrencia (FOR UPDATE)
            cur.execute("""
                SELECT 
                    s.balance_due_usd, s.paid_amount_usd, s.cancellation_code, 
                    s.customer_id
                FROM sales s
                WHERE s.id = %s AND s.status != 'Pagado'
                FOR UPDATE;
            """, (sale_id,))
            
            sale_record = cur.fetchone()
            
            if not sale_record:
                return jsonify({'msg': 'Venta a crédito no encontrada o ya está pagada.'}), 404
            
            balance_due = sale_record['balance_due_usd']
            current_paid_usd = sale_record['paid_amount_usd']
            customer_id = sale_record['customer_id']
            
            if cancellation_code_input != sale_record['cancellation_code']:
                return jsonify({'msg': 'Código de cancelación incorrecto. Pago no autorizado.'}), 401
            
            # 3. Lógica de Conversión y Cálculo del Pago
            amount_paid_usd = raw_payment_amount
            
            if payment_currency == 'VES':
                amount_paid_usd = raw_payment_amount / exchange_rate 

            if amount_paid_usd > balance_due + PAYMENT_TOLERANCE:
                return jsonify({'msg': f"El pago excede el saldo pendiente ($ {balance_due.quantize(Decimal('0.01'))})."}), 400
            
            if amount_paid_usd > balance_due:
                amount_paid_usd = balance_due
            
            # Calcular nuevos saldos y estado
            new_balance_due = balance_due - amount_paid_usd
            new_paid_usd = current_paid_usd + amount_paid_usd
            
            new_status = 'Abonado'
            if new_balance_due.quantize(Decimal('0.01')) <= Decimal('0.00'):
                new_status = 'Pagado'
                new_balance_due = Decimal('0.00') # Asegurar que el saldo quede en cero

            # 4. Actualizar la Venta en la Base de Datos
            
            if new_status == 'Pagado':
                fecha_pago_final_update = sql.SQL("fecha_pago_final = NOW()")
            else:
                fecha_pago_final_update = sql.SQL("fecha_pago_final = fecha_pago_final")

            query = sql.SQL("""
                UPDATE sales
                SET 
                    balance_due_usd = %s, 
                    paid_amount_usd = %s,
                    status = %s,
                    ves_paid = ves_paid + CASE WHEN %s = 'VES' THEN %s ELSE 0 END,
                    usd_paid = usd_paid + CASE WHEN %s = 'USD' THEN %s ELSE 0 END,
                    exchange_rate_used = CASE WHEN %s = 'VES' THEN %s ELSE exchange_rate_used END,
                    updated_at = NOW(),
                    {fecha_final_set}
                WHERE id = %s
                RETURNING balance_due_usd, status;
            """).format(fecha_final_set=fecha_pago_final_update)
            
            cur.execute(query, (
                new_balance_due, 
                new_paid_usd, 
                new_status,
                payment_currency, raw_payment_amount, 
                payment_currency, raw_payment_amount, 
                payment_currency, exchange_rate, 
                sale_id
            ))
            
            updated_sale = cur.fetchone() 
            
            # 5. REGISTRAR ABONO EN LA TABLA credit_payments
            cur.execute("""
                INSERT INTO credit_payments (
                    sale_id, customer_id, amount_usd, amount_ves, exchange_rate, payment_method, payment_date
                ) VALUES (%s, %s, %s, %s, %s, %s, NOW());
            """, (
                sale_id,
                customer_id,
                amount_paid_usd,
                raw_payment_amount if payment_currency == 'VES' else Decimal('0.00'),
                exchange_rate if payment_currency == 'VES' else Decimal('1.00'),
                payment_method_input
            ))

            # 6. Actualizar el saldo global del cliente (SOLO SI SE HIZO LA MIGRACIÓN)
            amount_reduced_from_credit = balance_due - new_balance_due
            
            if amount_reduced_from_credit > Decimal('0.00'):
                 cur.execute("""
                    UPDATE customers
                    SET current_credit_balance = current_credit_balance - %s,
                        updated_at = NOW()
                    WHERE id = %s;
                """, (amount_reduced_from_credit, customer_id))
            
            # 7. Asegurar la transacción
            cur.connection.commit()
            
            # 8. Exito
            return jsonify({
                'msg': f'Pago de $ {amount_paid_usd.quantize(Decimal("0.01"))} USD registrado con éxito. Estado: {new_status}',
                'new_status': updated_sale['status'], 
                'new_balance': updated_sale['balance_due_usd'].quantize(Decimal('0.01'))
            }), 200

    except Exception as e:
        # 9. Manejo de Errores y Rollback
        if 'cur' in locals() and cur and cur.connection:
             cur.connection.rollback()
             
        app_logger.error(f"Error al procesar pago de crédito para venta {sale_id}: {e}", exc_info=True)
        return jsonify({'msg': 'Error interno del servidor al procesar el pago. Por favor, revisa los logs.'}), 500
# ---------------------------------------------------------
# RUTAS DE REPORTES ADMIN
# ---------------------------------------------------------

@sale_bp.route('/reports', methods=['GET'])
@jwt_required()
def admin_general_reports():
    """Obtiene el listado COMPLETO de todas las ventas (Admin only)."""
    current_user_id, user_role = get_user_and_role()
    
    # 1. Verificar Permisos (Solo Admin)
    if not check_admin_permission(user_role):
        return jsonify({"msg": "Acceso denegado: Se requiere rol de Administrador."}), 403

    try:
        query = """
            SELECT 
                s.id,
                s.customer_id,
                c.name as customer_name,
                c.email as customer_email,
                c.cedula as customer_cedula,
                s.sale_date,
                s.status,
                s.tipo_pago,
                s.usd_paid,
                s.ves_paid,
                s.total_amount_usd,
                s.total_amount_ves,
                s.exchange_rate_used,
                u.email as seller_email,
                u.id as seller_id,
                s.balance_due_usd,
                s.paid_amount_usd,
                s.fecha_vencimiento,
                s.dias_credito,
                s.cancellation_code,
                json_agg(json_build_object(
                    'product_id', p.id,
                    'product_name', p.name,
                    'quantity', si.quantity,
                    'price_usd', si.price  -- CORREGIDO: usar 'price' en lugar de 'price_usd'
                )) AS items
            FROM sales s
            JOIN customers c ON s.customer_id = c.id
            JOIN users u ON s.user_id = u.id 
            JOIN sale_items si ON s.id = si.sale_id
            JOIN products p ON si.product_id = p.id
            GROUP BY s.id, c.name, c.email, c.cedula, s.sale_date, s.status, 
            s.tipo_pago, s.usd_paid, s.ves_paid, s.total_amount_usd, s.total_amount_ves, 
            s.exchange_rate_used, u.email, u.id, s.balance_due_usd, s.paid_amount_usd,
            s.fecha_vencimiento, s.dias_credito, s.cancellation_code
            ORDER BY s.sale_date DESC;
        """
        
        with get_db_cursor() as cur:
            cur.execute(query)
            sales_list = [dict(record) for record in cur.fetchall()]
            
        return jsonify(sales_list), 200
        
    except Exception as e:
        app_logger.error(f"Error al obtener los reportes generales admin: {e}", exc_info=True)
        return jsonify({"msg": "Error al cargar los reportes generales del administrador", "error": str(e)}), 500