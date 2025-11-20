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

def handle_credit_sale_validation(customer_id, pin_raw, cancellation_code):
    """Maneja la validación para ventas a crédito"""
    if not cancellation_code:
        return jsonify({"msg": "Se requiere el código de cancelación para ventas a crédito."}), 400
    
    # 🟢 ELIMINADO: Validación de PIN ya no es requerida
    # Solo código de cancelación es suficiente
    
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
            error_response = handle_credit_sale_validation(customer_id, None, cancellation_code)
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

            # Procesar crédito si aplica
            status, monto_pendiente, fecha_vencimiento = process_credit_sale(
                cur, is_credit_sale, customer_id, saldo_pendiente, dias_credito
            )
            if isinstance(status, tuple):  # Error ocurrió
                return status

            # Insertar venta
            new_sale_id = insert_sale_record(
                cur, customer_id, seller_user_id, total_amount_usd, total_amount_ves,
                exchange_rate, status, tipo_pago_raw, usd_paid, ves_paid,
                is_credit_sale, dias_credito, monto_pendiente, fecha_vencimiento, cancellation_code
            )

            # Procesar items y stock
            stock_alerts = process_sale_items_and_stock(cur, new_sale_id, validated_items)

            cur.connection.commit()
            
            # Construir respuesta
            return build_success_response(
                new_sale_id, tipo_pago_raw, total_amount_usd, total_amount_ves,
                exchange_rate, usd_paid, ves_paid, monto_pendiente, stock_alerts,
                is_credit_sale, cancellation_code
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

def process_credit_sale(cur, is_credit_sale, customer_id, saldo_pendiente, dias_credito):
    """Procesa lógica específica para ventas a crédito"""
    status = 'Completado'
    monto_pendiente = 0.0
    fecha_vencimiento = None
    
    if is_credit_sale:
        status = 'Crédito'
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
            
        # Actualizar balance del cliente
        cur.execute(
            "UPDATE customers SET balance_pendiente_usd = %s WHERE id = %s",
            (nuevo_balance, customer_id)
        )
        
        # Calcular fecha de vencimiento
        fecha_vencimiento = datetime.now().date() + timedelta(days=dias_credito)
    
    return status, monto_pendiente, fecha_vencimiento

def insert_sale_record(cur, customer_id, seller_user_id, total_amount_usd, total_amount_ves,
                      exchange_rate, status, tipo_pago_raw, usd_paid, ves_paid,
                      is_credit_sale, dias_credito, monto_pendiente, fecha_vencimiento, cancellation_code):
    """Inserta el registro de la venta en la base de datos"""
    fields = [
        "id", "customer_id", "user_id", "sale_date", "total_amount_usd", 
        "total_amount_ves", "exchange_rate_used", "status", "tipo_pago", 
        "usd_paid", "ves_paid"
    ]
    
    values = [
        str(uuid.uuid4()), customer_id, seller_user_id, datetime.now(), 
        total_amount_usd, total_amount_ves, exchange_rate, status, 
        tipo_pago_raw, usd_paid, ves_paid
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
        # Insertar item de venta
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
                          is_credit_sale, cancellation_code):
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
        "stock_alerts": stock_alerts
    }
    
    if is_credit_sale:
        response["cancellation_code"] = cancellation_code
    
    return jsonify(response), 201

def handle_sales_listing(current_user_id, user_role):
    """Maneja el listado de ventas"""
    try:
        base_query = """
            SELECT s.id, s.customer_id, c.name as customer_name, c.email as customer_email,
                    s.sale_date, s.status, s.tipo_pago, s.usd_paid, s.ves_paid,
                    s.total_amount_usd AS total_amount, s.total_amount_ves, 
                    s.exchange_rate_used, u.email as seller_email, u.id as seller_id, 
                    s.balance_due_usd AS monto_pendiente, s.fecha_vencimiento, s.dias_credito,
                    s.cancellation_code,
                    json_agg(json_build_object(
                        'product_name', p.name,
                        'quantity', si.quantity,
                        'price', si.price 
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
            GROUP BY s.id, c.name, c.email, s.sale_date, s.status, 
            s.tipo_pago, s.usd_paid, s.ves_paid,
            s.total_amount_usd, s.total_amount_ves, s.exchange_rate_used, u.email, u.id,
            s.balance_due_usd, s.fecha_vencimiento, s.dias_credito, s.cancellation_code
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
                    AND status = 'Crédito' 
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
            
            # Obtener ventas a crédito pendientes
            cur.execute("""
                SELECT 
                    id,
                    sale_date,
                    total_amount_usd,
                    balance_due_usd,
                    dias_credito,
                    fecha_vencimiento,
                    cancellation_code,
                    status
                FROM sales 
                WHERE customer_id = %s 
                AND status = 'Crédito' 
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
def pay_credit():
    """Registrar abono o cancelación de deuda de crédito"""
    current_user_id, user_role = get_user_and_role()
    
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado o token inválido"}), 401
    
    if not check_seller_permission(user_role):
        return jsonify({"msg": "Acceso denegado: solo personal de ventas puede registrar pagos"}), 403

    data = request.get_json()
    
    required_fields = ['customer_id', 'sale_id', 'payment_amount', 'payment_currency', 'cancellation_code']
    if error := validate_required_fields(data, required_fields):
        return jsonify({"msg": f"Missing required fields: {error}"}), 400
    
    customer_id = data.get('customer_id')
    sale_id = data.get('sale_id')
    payment_amount = float(data.get('payment_amount', 0))
    payment_currency = data.get('payment_currency')  # 'USD' o 'VES'
    cancellation_code = data.get('cancellation_code')
    exchange_rate = data.get('exchange_rate', 1.0)  # Tasa para pagos en bolívares
    
    if payment_amount <= 0:
        return jsonify({"msg": "El monto de pago debe ser mayor a 0"}), 400
    
    if payment_currency == 'VES' and (not exchange_rate or exchange_rate <= 0):
        return jsonify({"msg": "La tasa de cambio para pagos en bolívares es requerida"}), 400
    
    cur = None
    try:
        with get_db_cursor(commit=False) as cur:
            # Verificar que la venta existe y pertenece al cliente
            cur.execute("""
                SELECT s.id, s.balance_due_usd, s.cancellation_code, s.total_amount_usd,
                       s.dias_credito, s.fecha_vencimiento, s.status
                FROM sales s 
                WHERE s.id = %s AND s.customer_id = %s AND s.status = 'Crédito'
                FOR UPDATE
            """, (sale_id, customer_id))
            
            sale = cur.fetchone()
            
            if not sale:
                cur.connection.rollback()
                return jsonify({"msg": "Venta a crédito no encontrada o no pertenece al cliente"}), 404
            
            # Verificar código de cancelación
            if sale['cancellation_code'] != cancellation_code:
                cur.connection.rollback()
                return jsonify({"msg": "Código de cancelación incorrecto"}), 401
            
            balance_due = float(sale['balance_due_usd'])
            
            # Calcular monto en USD
            if payment_currency == 'VES':
                payment_amount_usd = payment_amount / exchange_rate
            else:
                payment_amount_usd = payment_amount
            
            # Verificar que el pago no exceda el saldo pendiente
            if payment_amount_usd > balance_due + PAYMENT_TOLERANCE:
                cur.connection.rollback()
                return jsonify({
                    "msg": f"El pago (${payment_amount_usd:.2f} USD) excede el saldo pendiente (${balance_due:.2f} USD)"
                }), 400
            
            # Calcular nuevo saldo
            new_balance = max(0.0, balance_due - payment_amount_usd)
            
            # Actualizar saldo de la venta
            cur.execute(
                "UPDATE sales SET balance_due_usd = %s WHERE id = %s",
                (new_balance, sale_id)
            )
            
            # Si el saldo llega a 0, cambiar status a Completado
            if new_balance <= PAYMENT_TOLERANCE:
                cur.execute(
                    "UPDATE sales SET status = 'Completado' WHERE id = %s",
                    (sale_id,)
                )
            
            # Actualizar balance del cliente
            cur.execute(
                "UPDATE customers SET balance_pendiente_usd = balance_pendiente_usd - %s WHERE id = %s",
                (payment_amount_usd, customer_id)
            )
            
            # Registrar el pago en la tabla de pagos
            try:
                cur.execute("""
                    INSERT INTO credit_payments 
                    (sale_id, customer_id, payment_amount, payment_currency, 
                     exchange_rate, payment_amount_usd, user_id, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                """, (sale_id, customer_id, payment_amount, payment_currency, 
                     exchange_rate, payment_amount_usd, current_user_id))
            except Exception as e:
                app_logger.warning(f"No se pudo registrar en credit_payments: {e}")
                # No hacemos rollback porque el pago principal sí se registró
            
            cur.connection.commit()
            
            response_data = {
                "msg": f"Pago registrado exitosamente. Nuevo saldo: ${new_balance:.2f} USD",
                "sale_id": sale_id,
                "customer_id": customer_id,
                "payment_amount": payment_amount,
                "payment_currency": payment_currency,
                "payment_amount_usd": payment_amount_usd,
                "previous_balance": balance_due,
                "new_balance": new_balance,
                "exchange_rate": exchange_rate if payment_currency == 'VES' else None
            }
            
            if new_balance <= PAYMENT_TOLERANCE:
                response_data["msg"] = "✅ ¡CRÉDITO CANCELADO COMPLETAMENTE!"
            
            return jsonify(response_data), 200
            
    except Exception as e:
        if cur and cur.connection:
            cur.connection.rollback()
        app_logger.error(f"Error al registrar pago de crédito: {e}", exc_info=True)
        return jsonify({"msg": "Error interno al registrar pago"}), 500

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
            SELECT s.id, s.customer_id, c.name as customer_name, c.email as customer_email,
                    s.sale_date, s.status, 
                    s.tipo_pago,
                    s.usd_paid, s.ves_paid,
                    s.total_amount_usd AS total_amount, s.total_amount_ves, s.exchange_rate_used, 
                    u.email as seller_email, u.id as seller_id, 
                    s.balance_due_usd AS monto_pendiente, s.fecha_vencimiento, s.dias_credito,
                    s.cancellation_code,
                    json_agg(json_build_object(
                        'product_name', p.name,
                        'quantity', si.quantity,
                        'price', si.price 
                    )) AS items
            FROM sales s
            JOIN customers c ON s.customer_id = c.id
            JOIN users u ON s.user_id = u.id 
            JOIN sale_items si ON s.id = si.sale_id
            JOIN products p ON si.product_id = p.id
            GROUP BY s.id, c.name, c.email, s.sale_date, s.status, 
            s.tipo_pago, s.usd_paid, s.ves_paid,
            s.total_amount_usd, s.total_amount_ves, s.exchange_rate_used, u.email, u.id,
            s.balance_due_usd, s.fecha_vencimiento, s.dias_credito, s.cancellation_code
            ORDER BY s.sale_date DESC;
        """
        
        with get_db_cursor() as cur:
            cur.execute(query)
            sales_list = [dict(record) for record in cur.fetchall()]
            
        return jsonify(sales_list), 200
        
    except Exception as e:
        app_logger.error(f"Error al obtener los reportes generales admin: {e}", exc_info=True)
        return jsonify({"msg": "Error al cargar los reportes generales del administrador", "error": str(e)}), 500