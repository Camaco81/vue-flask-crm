import os
import uuid
import logging
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from psycopg2 import sql 

# Importaciones Locales
from backend.db import get_db_cursor
from backend.utils.helpers import (
    get_user_and_role, 
    check_admin_permission, 
    validate_required_fields, 
    check_seller_permission
)
from backend.utils.bcv_api import get_dolarvzla_rate 
from backend.utils.inventory_utils import verificar_stock_y_alertar, STOCK_THRESHOLD
from backend.utils.security_utils import generate_daily_admin_code

# Configuración de Blueprint y Logging
# Se asume que el prefijo base /api/sales se maneja en app.py
sale_bp = Blueprint('sale', __name__)
app_logger = logging.getLogger('backend.routes.sale_routes') 

SECRET_SEED = os.environ.get('ADMIN_SECRET_SEED', 'mi-clave-unica-de-permiso')
PAYMENT_TOLERANCE = 0.01 
DEFAULT_CREDIT_DAYS = 30

def get_current_tenant():
    """Extrae el tenant_id del token JWT."""
    return get_jwt().get('tenant_id')

@sale_bp.route('', methods=['GET', 'POST'])
@jwt_required()
def sales_collection():
    current_user_id, user_role, *_ = get_user_and_role() 
    tenant_id = get_current_tenant()
    
    if not tenant_id:
        return jsonify({"msg": "Token inválido: Falta identificador de empresa"}), 401

    if request.method == "POST":
        if not check_seller_permission(user_role):
            return jsonify({"msg": "Acceso denegado: Solo personal de ventas"}), 403

        data = request.get_json()
        if error := validate_required_fields(data, ['customer_id', 'items']):
            return jsonify({"msg": f"Campos faltantes: {error}"}), 400
        
        tipo_pago_raw = data.get('tipo_pago', 'Contado')
        dias_credito = int(data.get('dias_credito', DEFAULT_CREDIT_DAYS))
        usd_paid = float(data.get('usd_paid', 0) or 0)
        ves_paid = float(data.get('ves_paid', 0) or 0)
        
        # Normalización para evitar errores de tildes
        tipo_pago_norm = tipo_pago_raw.lower().replace('é', 'e')
        is_credit_sale = 'credito' in tipo_pago_norm
        
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

                # PASO 1: Validar Stock (tenant_id como VARCHAR)
                for item in items:
                    product_id = item.get('product_id')
                    quantity = int(item.get('quantity', 0))
                    
                    cur.execute(
                        "SELECT name, price, stock FROM products WHERE id = %s AND tenant_id = %s::text FOR UPDATE", 
                        (product_id, tenant_id)
                    )
                    product = cur.fetchone()
                    
                    if not product:
                        cur.connection.rollback()
                        return jsonify({"msg": f"Producto ID {product_id} no encontrado"}), 404
                    
                    if product['stock'] < quantity:
                        cur.connection.rollback()
                        return jsonify({"msg": f"Stock insuficiente para {product['name']}"}), 400
                    
                    price_usd = float(product['price'])
                    total_amount_usd += (price_usd * quantity)
                    validated_items.append({
                        'product_id': product_id, 'quantity': quantity, 
                        'price': price_usd, 'current_stock': product['stock']
                    })

                # PASO 2: Cálculo de Totales
                total_amount_ves = total_amount_usd * exchange_rate
                usd_from_ves = ves_paid / exchange_rate if exchange_rate > 0 else 0
                total_paid_usd = usd_paid + usd_from_ves
                saldo_pendiente = max(0.0, round(total_amount_usd - total_paid_usd, 2))

                if not is_credit_sale and saldo_pendiente > PAYMENT_TOLERANCE:
                    cur.connection.rollback()
                    return jsonify({"msg": f"Pago insuficiente. Faltan ${saldo_pendiente}"}), 400

                status = 'Crédito' if is_credit_sale else 'Completado'
                fecha_vencimiento = None

                if is_credit_sale:
                    cur.execute(
                        "SELECT credit_limit_usd, balance_pendiente_usd FROM customers WHERE id = %s AND tenant_id = %s::text FOR UPDATE",
                        (customer_id, tenant_id)
                    )
                    cust_data = cur.fetchone()
                    if not cust_data:
                        cur.connection.rollback()
                        return jsonify({"msg": "Cliente no encontrado"}), 404

                    nuevo_balance = float(cust_data['balance_pendiente_usd']) + saldo_pendiente
                    if nuevo_balance > float(cust_data['credit_limit_usd']):
                        cur.connection.rollback()
                        return jsonify({"msg": "Límite de crédito excedido"}), 400
                    
                    cur.execute(
                        "UPDATE customers SET balance_pendiente_usd = %s WHERE id = %s AND tenant_id = %s::text",
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

                # PASO 4: Items e Inventario
                for item in validated_items:
                    cur.execute(
                        "INSERT INTO sale_items (sale_id, product_id, quantity, price, tenant_id) VALUES (%s, %s, %s, %s, %s::text)",
                        (new_sale_id, item['product_id'], item['quantity'], item['price'], tenant_id)
                    )
                    cur.execute(
                        "UPDATE products SET stock = stock - %s WHERE id = %s AND tenant_id = %s::text",
                        (item['quantity'], item['product_id'], tenant_id)
                    )
                    if (item['current_stock'] - item['quantity']) <= STOCK_THRESHOLD:
                        verificar_stock_y_alertar(item['product_id'])

                cur.connection.commit()
                return jsonify({"msg": "Venta exitosa", "sale_id": new_sale_id}), 201

        except Exception as e:
            if cur: cur.connection.rollback()
            app_logger.error(f"Error en Venta: {e}", exc_info=True)
            return jsonify({"msg": "Error interno al procesar la venta"}), 500

    elif request.method == "GET":
        try:
            with get_db_cursor() as cur:
                query = """
                    SELECT s.id::text, c.name as customer_name, s.sale_date::text, s.status, 
                           s.total_amount_usd, s.balance_due_usd, s.tipo_pago,
                           u.nombre as seller_name,
                           json_agg(json_build_object('name', p.name, 'qty', si.quantity)) as items
                    FROM sales s
                    JOIN customers c ON s.customer_id = c.id
                    JOIN users u ON s.user_id = u.id
                    JOIN sale_items si ON s.id = si.sale_id
                    JOIN products p ON si.product_id = p.id
                    WHERE s.tenant_id = %s::text
                """
                params = [tenant_id]
                if not check_admin_permission(user_role):
                    query += " AND s.user_id = %s"
                    params.append(current_user_id)
                
                query += " GROUP BY s.id, c.name, u.nombre ORDER BY s.sale_date DESC"
                cur.execute(query, params)
                return jsonify([dict(r) for r in cur.fetchall()]), 200
        except Exception as e:
            app_logger.error(f"Error al listar ventas: {e}")
            return jsonify({"msg": "Error al listar ventas"}), 500

@sale_bp.route('/credits/pending', methods=['GET'])
@jwt_required()
def get_pending_credits():
    tenant_id = get_current_tenant()
    _, user_role, *_ = get_user_and_role()

    if not tenant_id:
        return jsonify({"msg": "Token inválido: Falta tenant_id"}), 401

    try:
        with get_db_cursor() as cur:
            query = """
                SELECT 
                    s.id::text as sale_id,
                    c.name as customer_name,
                    c.cedula as customer_cedula,
                    s.sale_date::text,
                    s.fecha_vencimiento::text,
                    s.total_amount_usd,
                    s.balance_due_usd,
                    s.usd_paid,
                    s.ves_paid,
                    u.nombre as seller_name,
                    u.email as seller_email,
                    (CURRENT_DATE - s.fecha_vencimiento::date) as dias_en_mora,
                    COALESCE(s.admin_auth_code, 'N/A') as admin_approver_email
                FROM sales s
                JOIN customers c ON s.customer_id = c.id
                JOIN users u ON s.user_id = u.id
                WHERE s.tenant_id = %s::text 
                  AND s.balance_due_usd > 0.01
                  AND (LOWER(s.tipo_pago) LIKE 'credito%%' OR LOWER(s.status) = 'credito')
                ORDER BY dias_en_mora DESC, s.fecha_vencimiento ASC
            """
            cur.execute(query, [tenant_id])
            credits = cur.fetchall()
            return jsonify([dict(r) for r in credits]), 200
    except Exception as e:
        app_logger.error(f"Error cartera créditos: {e}")
        return jsonify({"msg": "Error interno al obtener cartera de créditos"}), 500

@sale_bp.route('/admin/security-code', methods=['GET'])
@jwt_required()
def generate_daily_admin_code_endpoint():
    """Endpoint para que el Admin obtenga el código de seguridad diario."""
    current_user_id, user_role, *_ = get_user_and_role()
    tenant_id = get_current_tenant()

    if not check_admin_permission(user_role):
        app_logger.warning(f"Acceso no autorizado: {current_user_id}")
        return jsonify({"msg": "Acceso denegado"}), 403

    code, date_str = generate_daily_admin_code(tenant_id, SECRET_SEED)
    
    if not code:
        return jsonify({"msg": "Error al generar el código"}), 500

    return jsonify({
        "security_code": code,
        "date": date_str,
        "msg": "Código diario obtenido correctamente"
    }), 200