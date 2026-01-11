from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from backend.db import get_db_cursor
from psycopg2 import sql 
from backend.utils.helpers import (
    get_user_and_role, 
    check_admin_permission, 
    validate_required_fields, 
    check_seller_permission
)
from backend.utils.bcv_api import get_dolarvzla_rate 
from backend.utils.inventory_utils import verificar_stock_y_alertar, STOCK_THRESHOLD
import logging
from datetime import datetime, timedelta
import uuid

sale_bp = Blueprint('sale', __name__, url_prefix='/api/sales')
app_logger = logging.getLogger('backend.routes.sale_routes') 
SECRET_SEED =os.environ.get('ADMIN_SECRET_SEED', 'mi-clave-unica-de-permiso')


# Tolerancia para pagos (evitar errores de redondeo)
PAYMENT_TOLERANCE = 0.01 

def get_current_tenant():
    """Extrae el tenant_id del token JWT."""
    return get_jwt().get('tenant_id', 'default-tenant')

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

def handle_credit_sale_validation(cancellation_code, admin_auth_code):
    """Maneja la validación para ventas a crédito"""
    if not cancellation_code:
        return jsonify({"msg": "Se requiere el código de cancelación para ventas a crédito."}), 400
    
    # Validar el código del administrador
    daily_code = get_daily_security_code_server()
    if admin_auth_code != daily_code:
        return jsonify({"msg": "Código de autorización de administrador incorrecto o expirado. Venta a crédito no autorizada."}), 403
    
    return None


def validate_admin_auth_code(admin_auth_code_input):
    """Valida el código de autorización del administrador"""
    daily_code = get_daily_security_code_server()
    if admin_auth_code_input != daily_code:
        return jsonify({"msg": "Código de autorización de administrador incorrecto o expirado. Operación no autorizada."}), 403
    return None

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

def build_sale_insert_query(is_credit_sale, fields, values, dias_credito, 
                          monto_pendiente, fecha_vencimiento, cancellation_code, admin_auth_code):
    """Construye dinámicamente la consulta SQL para insertar una venta"""
    if is_credit_sale:
        fields.extend([
            "is_credit_sale", "dias_credito", "balance_due_usd", 
            "fecha_vencimiento", "cancellation_code", "admin_auth_code_used"
        ])
        values.extend([
            True, dias_credito, monto_pendiente, 
            fecha_vencimiento, cancellation_code, admin_auth_code
        ])
    else:
        fields.extend(["is_credit_sale", "balance_due_usd"])
        values.extend([False, 0.0])
    
    # Construir la consulta SQL
    placeholders = ["%s"] * len(values)
    query = f"""
        INSERT INTO sales ({', '.join(fields)}) 
        VALUES ({', '.join(placeholders)})
        RETURNING id;
    """
    return query    
    
def get_daily_security_code_server():
    """
    Genera el código de seguridad determinista de 6 dígitos basado en la fecha y una semilla secreta.
    """
    today = datetime.now().date()
    date_string = today.isoformat() # YYYY-MM-DD
    combined_string = date_string + SECRET_SEED
    
    # Generación de hash simple de 6 dígitos
    hash_value = 0
    for char in combined_string:
        hash_value = ((hash_value << 5) - hash_value) + ord(char)
        hash_value &= 0xFFFFFFFF # Convertir a entero de 32 bits
    
    # Devolver un código de 6 dígitos
    return str(abs(hash_value % 1000000)).zfill(6)

def get_current_tenant():
    """Extrae el tenant_id del token JWT."""
    return get_jwt().get('tenant_id', 'default-tenant')

@sale_bp.route('', methods=['GET', 'POST'])
@jwt_required()
def sales_collection():
    """Maneja la creación de una nueva venta (POST) y el listado de ventas (GET)."""
    current_user_id, user_role = get_user_and_role() 
    tenant_id = get_current_tenant()
    
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado"}), 401
    
    if not check_seller_permission(user_role):
        return jsonify({"msg": "Acceso denegado: Solo personal de ventas"}), 403

    if request.method == "POST":
        data = request.get_json()
        
        # Validación inicial
        if error := validate_required_fields(data, ['customer_id', 'items']):
            return jsonify({"msg": f"Campos faltantes: {error}"}), 400
        
        # Procesamiento de variables de pago
        tipo_pago_raw = data.get('tipo_pago', 'Contado')
        dias_credito = int(data.get('dias_credito', 30))
        usd_paid = float(data.get('usd_paid', 0) or 0)
        ves_paid = float(data.get('ves_paid', 0) or 0)
        
        tipo_pago_norm = tipo_pago_raw.lower().replace('é', 'e')
        is_credit_sale = tipo_pago_norm == 'credito'
        
        customer_id = data.get("customer_id")
        items = data.get("items")

        try:
            exchange_rate = get_dolarvzla_rate()
        except Exception as e:
            app_logger.error(f"Error BCV: {e}")
            return jsonify({"msg": "No se pudo obtener la tasa de cambio"}), 500

        cur = None
        try:
            with get_db_cursor(commit=False) as cur: 
                total_amount_usd = 0.0
                validated_items = []

                # PASO 1: Validar Stock y Pertenencia al Tenant
                for item in items:
                    product_id = item.get('product_id')
                    quantity = int(item.get('quantity', 0))
                    
                    cur.execute(
                        "SELECT name, price, stock FROM products WHERE id = %s AND tenant_id = %s FOR UPDATE", 
                        (product_id, tenant_id)
                    )
                    product = cur.fetchone()
                    
                    if not product:
                        cur.connection.rollback()
                        return jsonify({"msg": f"Producto ID {product_id} no pertenece a su empresa"}), 404
                    
                    if product['stock'] < quantity:
                        cur.connection.rollback()
                        return jsonify({"msg": f"Stock insuficiente para {product['name']}"}), 400
                    
                    price_usd = float(product['price'])
                    total_amount_usd += (price_usd * quantity)
                    validated_items.append({
                        'product_id': product_id, 'quantity': quantity, 
                        'price': price_usd, 'current_stock': product['stock']
                    })

                # PASO 2: Cálculo de Totales y Crédito
                total_amount_ves = total_amount_usd * exchange_rate
                usd_from_ves = ves_paid / exchange_rate if exchange_rate > 0 else 0
                total_paid_usd = usd_paid + usd_from_ves
                saldo_pendiente = max(0.0, round(total_amount_usd - total_paid_usd, 2))

                if not is_credit_sale and saldo_pendiente > PAYMENT_TOLERANCE:
                    cur.connection.rollback()
                    return jsonify({"msg": f"Pago insuficiente para contado. Faltan ${saldo_pendiente}"}), 400

                status = 'Crédito' if is_credit_sale else 'Completado'
                fecha_vencimiento = None

                if is_credit_sale:
                    cur.execute(
                        "SELECT credit_limit_usd, balance_pendiente_usd FROM customers WHERE id = %s AND tenant_id = %s FOR UPDATE",
                        (customer_id, tenant_id)
                    )
                    cust_data = cur.fetchone()
                    if not cust_data:
                        cur.connection.rollback()
                        return jsonify({"msg": "Cliente no encontrado en este tenant"}), 404

                    nuevo_balance = float(cust_data['balance_pendiente_usd']) + saldo_pendiente
                    if nuevo_balance > float(cust_data['credit_limit_usd']):
                        cur.connection.rollback()
                        return jsonify({"msg": "Límite de crédito excedido para este cliente"}), 400
                    
                    cur.execute(
                        "UPDATE customers SET balance_pendiente_usd = %s WHERE id = %s AND tenant_id = %s",
                        (nuevo_balance, customer_id, tenant_id)
                    )
                    fecha_vencimiento = datetime.now().date() + timedelta(days=dias_credito)

                # PASO 3: Insertar Venta
                new_sale_id = str(uuid.uuid4())
                fields = [
                    "id", "customer_id", "user_id", "tenant_id", "sale_date", 
                    "total_amount_usd", "total_amount_ves", "exchange_rate_used", 
                    "status", "tipo_pago", "usd_paid", "ves_paid", "balance_due_usd", 
                    "fecha_vencimiento", "dias_credito"
                ]
                values = [
                    new_sale_id, customer_id, current_user_id, tenant_id, datetime.now(),
                    total_amount_usd, total_amount_ves, exchange_rate,
                    status, tipo_pago_raw, usd_paid, ves_paid, saldo_pendiente,
                    fecha_vencimiento, (dias_credito if is_credit_sale else 0)
                ]
                
                placeholders = sql.SQL(', ').join(sql.Placeholder() * len(fields))
                query_insert = sql.SQL("INSERT INTO sales ({}) VALUES ({})").format(
                    sql.SQL(', ').join(map(sql.Identifier, fields)), placeholders
                )
                cur.execute(query_insert, values)

                # PASO 4: Items y Actualización de Inventario
                stock_alerts = []
                for item in validated_items:
                    cur.execute(
                        "INSERT INTO sale_items (sale_id, product_id, quantity, price, tenant_id) VALUES (%s, %s, %s, %s, %s)",
                        (new_sale_id, item['product_id'], item['quantity'], item['price'], tenant_id)
                    )
                    cur.execute(
                        "UPDATE products SET stock = stock - %s WHERE id = %s AND tenant_id = %s",
                        (item['quantity'], item['product_id'], tenant_id)
                    )
                    
                    # Alertas de stock
                    if (item['current_stock'] - item['quantity']) <= STOCK_THRESHOLD:
                        msg = verificar_stock_y_alertar(item['product_id'])
                        if msg: stock_alerts.append(msg)

                cur.connection.commit()
                return jsonify({
                    "msg": "Venta exitosa", 
                    "sale_id": new_sale_id,
                    "total_usd": round(total_amount_usd, 2),
                    "stock_alerts": stock_alerts
                }), 201

        except Exception as e:
            if cur: cur.connection.rollback()
            app_logger.error(f"Error en Venta: {e}", exc_info=True)
            return jsonify({"msg": "Error al procesar la venta"}), 500

    elif request.method == "GET":
        try:
            with get_db_cursor() as cur:
                query = """
                    SELECT s.id, c.name as customer_name, s.sale_date, s.status, 
                           s.total_amount_usd, s.balance_due_usd, s.tipo_pago,
                           json_agg(json_build_object('name', p.name, 'qty', si.quantity)) as items
                    FROM sales s
                    JOIN customers c ON s.customer_id = c.id
                    JOIN sale_items si ON s.id = si.sale_id
                    JOIN products p ON si.product_id = p.id
                    WHERE s.tenant_id = %s
                """
                params = [tenant_id]
                if not check_admin_permission(user_role):
                    query += " AND s.user_id = %s"
                    params.append(current_user_id)
                
                query += " GROUP BY s.id, c.name ORDER BY s.sale_date DESC"
                cur.execute(query, params)
                return jsonify([dict(r) for r in cur.fetchall()]), 200
        except Exception as e:
            return jsonify({"msg": "Error al obtener lista de ventas"}), 500

@sale_bp.route('/<uuid:sale_id>', methods=["GET", "DELETE"])
@jwt_required()
def sales_single(sale_id):
    current_user_id, user_role = get_user_and_role()
    tenant_id = get_current_tenant()
    sale_id_str = str(sale_id)

    if request.method == "GET":
        try:
            with get_db_cursor() as cur:
                cur.execute("""
                    SELECT s.*, c.name as customer_name, u.email as seller_email,
                           json_agg(json_build_object('product', p.name, 'qty', si.quantity, 'price', si.price)) as items
                    FROM sales s
                    JOIN customers c ON s.customer_id = c.id
                    JOIN users u ON s.user_id = u.id
                    JOIN sale_items si ON s.id = si.sale_id
                    JOIN products p ON si.product_id = p.id
                    WHERE s.id = %s AND s.tenant_id = %s
                    GROUP BY s.id, c.name, u.email
                """, (sale_id_str, tenant_id))
                res = cur.fetchone()
                return jsonify(dict(res)) if res else (jsonify({"msg": "No encontrada"}), 404)
        except Exception as e:
            return jsonify({"msg": "Error"}), 500

    elif request.method == "DELETE":
        try:
            with get_db_cursor(commit=False) as cur:
                cur.execute("SELECT * FROM sales WHERE id = %s AND tenant_id = %s FOR UPDATE", (sale_id_str, tenant_id))
                sale = cur.fetchone()
                if not sale: return jsonify({"msg": "No encontrada"}), 404

                # Revertir Crédito
                if sale['status'] == 'Crédito' and float(sale['balance_due_usd']) > 0:
                    cur.execute("UPDATE customers SET balance_pendiente_usd = balance_pendiente_usd - %s WHERE id = %s",
                               (sale['balance_due_usd'], sale['customer_id']))

                # Reponer Stock
                cur.execute("SELECT product_id, quantity FROM sale_items WHERE sale_id = %s", (sale_id_str,))
                for item in cur.fetchall():
                    cur.execute("UPDATE products SET stock = stock + %s WHERE id = %s AND tenant_id = %s",
                               (item['quantity'], item['product_id'], tenant_id))

                cur.execute("DELETE FROM sales WHERE id = %s AND tenant_id = %s", (sale_id_str, tenant_id))
                cur.connection.commit()
                return jsonify({"msg": "Venta revertida exitosamente"}), 200
        except Exception as e:
            return jsonify({"msg": "Error al eliminar"}), 500