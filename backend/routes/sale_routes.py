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
import bcrypt # 🎯 NUEVO: Importamos bcrypt para la verificación segura del PIN

sale_bp = Blueprint('sale', __name__, url_prefix='/api/sales')
app_logger = logging.getLogger('backend.routes.sale_routes') 

# =========================================================
# CONSTANTES GLOBALES
# =========================================================

SALES_ROLES = ['admin', 'vendedor'] 
PAYMENT_TOLERANCE = 0.01 

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
        data = request.get_json()
        
        # 'pin' es ahora un campo opcional, requerido solo para ventas a crédito.
        required_fields = ['customer_id', 'items']
        if error := validate_required_fields(data, required_fields):
            return jsonify({"msg": f"Missing required fields: {error}"}), 400
        
        # OBTENCIÓN Y NORMALIZACIÓN DE CAMPOS A NIVEL RAÍZ
        tipo_pago_raw = data.get('tipo_pago', 'Contado')
        dias_credito_raw = data.get('dias_credito') 
        usd_paid_raw = data.get('usd_paid', 0)
        ves_paid_raw = data.get('ves_paid', 0)
        
        # 🎯 NUEVO: Capturar el PIN y código de cancelación
        pin_raw = data.get("customer_pin") 
        cancellation_code = data.get("cancellation_code")  # 🆕 NUEVO CAMPO
            
        tipo_pago_normalized = tipo_pago_raw.lower().replace('é', 'e') 
        is_credit_sale = tipo_pago_normalized == 'credito'
        
        # Conversión de montos pagados a float
        try:
            usd_paid = float(usd_paid_raw) if usd_paid_raw is not None and usd_paid_raw != '' else 0.0
            ves_paid = float(ves_paid_raw) if ves_paid_raw is not None and ves_paid_raw != '' else 0.0
            if usd_paid < 0 or ves_paid < 0:
                raise ValueError("Los montos de pago deben ser positivos.")
        except (ValueError, TypeError) as e:
            return jsonify({"msg": f"Los montos de pago deben ser números válidos y positivos: {e}"}), 400

        dias_credito = 0 
        
        if is_credit_sale:
            try:
                dias_credito = int(dias_credito_raw) if dias_credito_raw is not None and dias_credito_raw != '' else 30
                if dias_credito <= 0: dias_credito = 30
            except (ValueError, TypeError):
                dias_credito = 30 

        customer_id = data.get("customer_id")
        items = data.get("items")
        seller_user_id = current_user_id
        
        if not isinstance(items, list) or len(items) == 0:
            return jsonify({"msg": "Items must be a non-empty list of products"}), 400

        try:
            exchange_rate = get_dolarvzla_rate()
        except Exception as e:
            app_logger.error(f"FATAL: No se pudo obtener la tasa de cambio para la venta: {e}", exc_info=True)
            return jsonify({"msg": "Error interno: No se pudo obtener la tasa de cambio del sistema"}), 500
        
        # =========================================================
        # 🎯 VERIFICACIÓN DE PIN Y CÓDIGO PARA VENTAS A CRÉDITO
        # =========================================================
        if is_credit_sale:
            # Verificar PIN
            if not pin_raw:
                return jsonify({"msg": "Se requiere el PIN de transacción (customer_pin) para ventas a crédito."}), 400
            
            # 🆕 NUEVO: Verificar código de cancelación
            if not cancellation_code:
                return jsonify({"msg": "Se requiere el código de cancelación para ventas a crédito."}), 400
            
            try:
                with get_db_cursor(commit=False) as pin_cur:
                    pin_cur.execute("SELECT pin_hash FROM customers WHERE id = %s", (customer_id,))
                    customer_pin_record = pin_cur.fetchone()

                    if not customer_pin_record or not customer_pin_record.get('pin_hash'):
                        return jsonify({"msg": "Cliente no encontrado o PIN de crédito no configurado."}), 404

                    stored_hash = customer_pin_record['pin_hash'].encode('utf-8')
                    
                    if not bcrypt.checkpw(pin_raw.encode('utf-8'), stored_hash):
                        return jsonify({"msg": "PIN de transacción incorrecto. Venta a crédito denegada."}), 401
                        
            except Exception as e:
                app_logger.error(f"Error durante la verificación de PIN del cliente {customer_id}: {e}", exc_info=True)
                return jsonify({"msg": "Error interno en el sistema de seguridad de PIN."}), 500

        # Bloque de Transacción
        cur = None
        try:
            with get_db_cursor(commit=False) as cur: 
                total_amount_usd = 0.0
                validated_items = []

                # Paso 1: Verificación de Stock y Cálculo de Totales (SELECT FOR UPDATE)
                for item in items:
                    if error := validate_required_fields(item, ['product_id', 'quantity']):
                        cur.connection.rollback()
                        return jsonify({"msg": f"Each item missing field: {error}"}), 400
                        
                    product_id = item.get('product_id')
                    quantity_raw = item.get('quantity')
                    
                    try:
                        quantity = int(quantity_raw)
                        if quantity <= 0:
                            raise ValueError
                    except (ValueError, TypeError):
                        cur.connection.rollback()
                        return jsonify({"msg": f"La cantidad ({quantity_raw}) debe ser un número entero válido y positivo"}), 400
                        
                    cur.execute("SELECT name, price, stock FROM products WHERE id = %s FOR UPDATE", (product_id,))
                    product_row = cur.fetchone()
                    
                    if not product_row:
                        cur.connection.rollback()
                        return jsonify({"msg": f"Producto con ID {product_id} no encontrado"}), 404
                        
                    current_stock = product_row['stock']
                    product_name = product_row['name']
                    price_usd = float(product_row['price'])
                    
                    if current_stock < quantity:
                        cur.connection.rollback()
                        return jsonify({"msg": f"Stock insuficiente para {product_name}. Stock actual: {current_stock}"}), 400
                        
                    subtotal_usd = price_usd * quantity
                    total_amount_usd += subtotal_usd
                    
                    validated_items.append({
                        'product_id': product_id,
                        'quantity': quantity,
                        'price': price_usd, 
                        'current_stock': current_stock
                    })

                total_amount_ves = total_amount_usd * exchange_rate
                
                # Paso 2: Cálculo de Abono y Saldo Pendiente
                usd_from_ves = ves_paid / exchange_rate if exchange_rate > 0 else 0.0
                total_paid_usd = usd_paid + usd_from_ves
                saldo_pendiente_venta_usd = max(0.0, round(total_amount_usd - total_paid_usd, 2))

                if not is_credit_sale and saldo_pendiente_venta_usd > PAYMENT_TOLERANCE:
                    cur.connection.rollback()
                    return jsonify({"msg": f"Monto pagado insuficiente para venta al contado. Saldo pendiente: ${round(saldo_pendiente_venta_usd, 2)}"}), 400

                status = 'Completado' 
                monto_pendiente = 0.0 
                fecha_vencimiento_val = None 
                
                if is_credit_sale:
                    status = 'Crédito' 
                    monto_pendiente = saldo_pendiente_venta_usd 
                    
                    # 2.a) Obtener límite y balance del cliente
                    cur.execute(
                        "SELECT credit_limit_usd, balance_pendiente_usd FROM customers WHERE id = %s FOR UPDATE",
                        (customer_id,)
                    )
                    customer = cur.fetchone()

                    if not customer:
                        cur.connection.rollback()
                        return jsonify({"msg": "Cliente de crédito no encontrado"}), 404

                    limite = float(customer['credit_limit_usd'])
                    balance = float(customer['balance_pendiente_usd'])
                    
                    nuevo_balance = balance + monto_pendiente
                    
                    # 2.b) Verificar Límite de Crédito
                    if nuevo_balance > limite:
                        cur.connection.rollback()
                        return jsonify({
                            "msg": f"Límite de crédito excedido. Límite: ${limite}, Pendiente Actual: ${balance}, Venta con abono (Pendiente): ${round(monto_pendiente, 2)}. Nuevo Balance: ${round(nuevo_balance, 2)}",
                            "code": "CREDIT_LIMIT_EXCEEDED"
                        }), 400
                        
                    # 2.c) Actualizar Balance Pendiente del Cliente
                    cur.execute(
                        "UPDATE customers SET balance_pendiente_usd = %s WHERE id = %s",
                        (nuevo_balance, customer_id)
                    )
                    
                    # 2.d) Calcular Fecha de Vencimiento
                    fecha_vencimiento_val = datetime.now().date() + timedelta(days=dias_credito)
                
                # Paso 3: Inserción de Venta - 🆕 AGREGAR CÓDIGO DE CANCELACIÓN
                fields = ["id", "customer_id", "user_id", "sale_date", "total_amount_usd", "total_amount_ves", 
                            "exchange_rate_used", "status", "tipo_pago", "usd_paid", "ves_paid"] 
                
                values = [str(uuid.uuid4()), customer_id, seller_user_id, datetime.now(), total_amount_usd, 
                            total_amount_ves, exchange_rate, status, tipo_pago_raw, usd_paid, ves_paid]
                
                if is_credit_sale:
                    fields.extend(["dias_credito", "balance_due_usd", "fecha_vencimiento", "cancellation_code"])  # 🆕 AGREGADO
                    values.extend([dias_credito, monto_pendiente, fecha_vencimiento_val, cancellation_code])  # 🆕 AGREGADO

                placeholders = sql.SQL(', ').join(sql.Placeholder() * len(fields))
                
                query_insert_sale = sql.SQL(
                    "INSERT INTO sales ({}) VALUES ({}) RETURNING id"
                ).format(
                    sql.SQL(', ').join(map(sql.Identifier, fields)),
                    placeholders
                )
                
                cur.execute(query_insert_sale, values)
                new_sale_id = cur.fetchone()['id']

                # Paso 4: Insertar Ítems y Disminuir Stock
                stock_alerts = []
                for item in validated_items:
                    cur.execute(
                        "INSERT INTO sale_items (sale_id, product_id, quantity, price) VALUES (%s, %s, %s, %s);",
                        (new_sale_id, item['product_id'], item['quantity'], item['price'])
                    )
                    
                    cur.execute(
                        "UPDATE products SET stock = stock - %s WHERE id = %s;",
                        (item['quantity'], item['product_id'])
                    )
                    
                    remaining_stock = item['current_stock'] - item['quantity']
                    if remaining_stock <= STOCK_THRESHOLD:
                        alert_msg = verificar_stock_y_alertar(item['product_id']) 
                        if alert_msg:
                            stock_alerts.append(alert_msg)
                        
                cur.connection.commit()
                
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
                
                # 🆕 NUEVO: Incluir código de cancelación en la respuesta si es crédito
                if is_credit_sale:
                    response["cancellation_code"] = cancellation_code
                
                return jsonify(response), 201
                
        except Exception as e:
            if cur and cur.connection:
                cur.connection.rollback()
            
            error_msg = str(e)
            status_code = 500
            
            if "CREDIT_LIMIT_EXCEEDED" in error_msg or "Monto pagado insuficiente" in error_msg:
                error_msg = "Límite de crédito del cliente excedido." if "CREDIT_LIMIT_EXCEEDED" in error_msg else error_msg
                status_code = 400

            app_logger.error(f"Error al registrar la venta (POST): {error_msg}", exc_info=True)
            return jsonify({"msg": f"Error al registrar la venta: {error_msg}"}), status_code
            

            
    elif request.method == "GET":
        # LÓGICA DE LISTADO (GET /api/sales) - CORREGIDA CON CAMPOS DE PAGO/CRÉDITO
        try:
            base_query = """
                SELECT s.id, s.customer_id, c.name as customer_name, c.email as customer_email,
                        s.sale_date, s.status,
                        s.tipo_pago, -- 🟢 CAMBIO: Incluido
                        s.usd_paid, s.ves_paid, -- 🟢 CAMBIO: Incluidos
                        s.total_amount_usd AS total_amount, s.total_amount_ves, 
                        s.exchange_rate_used, 
                        u.email as seller_email, u.id as seller_id, 
                        s.balance_due_usd AS monto_pendiente, s.fecha_vencimiento, s.dias_credito, 
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
            
            # FILTRO DE PERMISOS: Si no es Admin, solo ve sus ventas.
            if not check_admin_permission(user_role): 
                base_query += " WHERE s.user_id = %s"
                params.append(current_user_id)
            
            # Agrupación y Ordenamiento
            base_query += """
                GROUP BY s.id, c.name, c.email, s.sale_date, s.status, 
                s.tipo_pago, s.usd_paid, s.ves_paid, -- 🟢 CAMBIO: Incluidos en GROUP BY
                s.total_amount_usd, s.total_amount_ves, s.exchange_rate_used, u.email, u.id,
                s.balance_due_usd, s.fecha_vencimiento, s.dias_credito
                ORDER BY s.sale_date DESC;
            """
            
            with get_db_cursor() as cur:
                cur.execute(base_query, tuple(params))
                sales_list = [dict(record) for record in cur.fetchall()]
                
            return jsonify(sales_list), 200
            
        except Exception as e:
            app_logger.error(f"Error al obtener las ventas: {e}", exc_info=True)
            return jsonify({"msg": "Error al obtener las ventas", "error": str(e)}), 500

# ---------------------------------------------------------

@sale_bp.route('/<uuid:sale_id>', methods=["GET", "DELETE"])
@jwt_required()
def sales_single(sale_id):
    """Maneja la vista individual (GET) y eliminación (DELETE) de una venta."""
    
    current_user_id, user_role = get_user_and_role()
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado o token inválido"}), 401

    sale_id_str = str(sale_id)

    if request.method == "GET":
        # LÓGICA DE VISTA INDIVIDUAL (GET) - CORREGIDA CON CAMPOS DE PAGO/CRÉDITO
        try:
            base_query = """
                SELECT s.id, s.customer_id, c.name as customer_name, c.email as customer_email, c.address as customer_address,
                        s.sale_date, s.status, 
                        s.tipo_pago, -- 🟢 CAMBIO: Incluido
                        s.usd_paid, s.ves_paid, -- 🟢 CAMBIO: Incluidos
                        s.total_amount_usd AS total_amount, 
                        s.total_amount_ves, s.exchange_rate_used, 
                        u.email as seller_email, u.id as seller_id,
                        s.balance_due_usd AS monto_pendiente, s.fecha_vencimiento, s.dias_credito, 
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
                WHERE s.id = %s
            """
            params = [sale_id_str]
            if not check_admin_permission(user_role):
                base_query += " AND s.user_id = %s"
                params.append(current_user_id)
            
            # GROUP BY
            base_query += """
                GROUP BY s.id, s.customer_id, c.name, c.email, c.address, s.sale_date, s.status, 
                s.tipo_pago, s.usd_paid, s.ves_paid, -- 🟢 CAMBIO: Incluidos en GROUP BY
                s.total_amount_usd, s.total_amount_ves, s.exchange_rate_used, u.email, u.id,
                s.balance_due_usd, s.fecha_vencimiento, s.dias_credito;
            """

            with get_db_cursor() as cur:
                cur.execute(base_query, tuple(params))
                sale_record = cur.fetchone()

            if sale_record:
                return jsonify(dict(sale_record)), 200
            return jsonify({"msg": "Venta no encontrada o no tienes permisos para verla"}), 404
        except Exception as e:
            app_logger.error(f"Error al obtener la venta {sale_id}: {e}", exc_info=True)
            return jsonify({"msg": "Error al obtener la venta", "error": str(e)}), 500

    elif request.method == "DELETE":
        # LÓGICA DE ELIMINACIÓN (DELETE) - SIN CAMBIOS
        cur = None
        try:
            with get_db_cursor(commit=False) as cur: 
                
                # 1. Obtener datos clave de la venta y bloquear el cliente (si es a crédito)
                cur.execute(
                    "SELECT user_id, customer_id, status, balance_due_usd FROM sales WHERE id = %s FOR UPDATE",
                    (sale_id_str,)
                )
                sale_data = cur.fetchone()

                if not sale_data:
                    cur.connection.rollback()
                    return jsonify({"msg": "Venta no encontrada"}), 404
                
                sale_user_id = sale_data['user_id']
                customer_id = sale_data['customer_id']
                sale_status = sale_data['status'] 
                monto_pendiente = float(sale_data['balance_due_usd'] or 0.0) 
                
                # 2. Verificar Permisos (Admin o vendedor creador)
                if not check_admin_permission(user_role) and str(sale_user_id) != str(current_user_id):
                    cur.connection.rollback()
                    return jsonify({"msg": "No autorizado para eliminar esta venta"}), 403
                
                # 3. ROLLBACK DE CRÉDITO (Si aplica)
                if sale_status == 'Crédito' and monto_pendiente > 0:
                    cur.execute(
                        "SELECT balance_pendiente_usd FROM customers WHERE id = %s FOR UPDATE",
                        (customer_id,)
                    )
                    customer = cur.fetchone()
                    
                    if customer:
                        nuevo_balance = float(customer['balance_pendiente_usd']) - monto_pendiente
                        
                        if nuevo_balance < 0:
                            app_logger.warning(f"Balance de cliente {customer_id} se vuelve negativo al eliminar venta {sale_id_str}. Ajustando a 0.")
                            nuevo_balance = 0 
                            
                        cur.execute(
                            "UPDATE customers SET balance_pendiente_usd = %s WHERE id = %s",
                            (nuevo_balance, customer_id)
                        )

                # 4. Reponer Stock y Eliminar
                cur.execute(
                    "SELECT product_id, quantity FROM sale_items WHERE sale_id = %s",
                    (sale_id_str,)
                )
                items_to_restore = cur.fetchall()

                cur.execute("DELETE FROM sale_items WHERE sale_id = %s;", (sale_id_str,))
                cur.execute("DELETE FROM sales WHERE id = %s;", (sale_id_str,))
                deleted_rows = cur.rowcount

                for item in items_to_restore:
                    cur.execute(
                        "UPDATE products SET stock = stock + %s WHERE id = %s;",
                        (item['quantity'], item['product_id'])
                    )
                
                cur.connection.commit()
                
                if deleted_rows > 0:
                    return jsonify({"msg": "Venta y sus items eliminados exitosamente. Stock y Crédito revertidos."}), 200
                
                return jsonify({"msg": "Error al eliminar la venta"}), 500

        except Exception as e:
            if cur and cur.connection:
                cur.connection.rollback()
            app_logger.error(f"Error al eliminar la venta {sale_id} (ROLLBACK): {e}", exc_info=True)
            return jsonify({"msg": "Error al eliminar la venta", "error": str(e)}), 500


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
                    s.tipo_pago, -- 🟢 CAMBIO: Incluido
                    s.usd_paid, s.ves_paid, -- 🟢 CAMBIO: Incluidos
                    s.total_amount_usd AS total_amount, s.total_amount_ves, s.exchange_rate_used, 
                    u.email as seller_email, u.id as seller_id, 
                    s.balance_due_usd AS monto_pendiente, s.fecha_vencimiento, s.dias_credito, 
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
            s.tipo_pago, s.usd_paid, s.ves_paid, -- 🟢 CAMBIO: Incluidos en GROUP BY
            s.total_amount_usd, s.total_amount_ves, s.exchange_rate_used, u.email, u.id,
            s.balance_due_usd, s.fecha_vencimiento, s.dias_credito 
            ORDER BY s.sale_date DESC;
        """
        
        with get_db_cursor() as cur:
            cur.execute(query)
            sales_list = [dict(record) for record in cur.fetchall()]
            
        return jsonify(sales_list), 200
        
    except Exception as e:
        app_logger.error(f"Error al obtener los reportes generales admin: {e}", exc_info=True)
        return jsonify({"msg": "Error al cargar los reportes generales del administrador", "error": str(e)}), 500