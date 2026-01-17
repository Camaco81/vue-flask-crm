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
        
        # 🛠️ CORRECCIÓN 1: Normalización robusta para detectar crédito
        tipo_pago_raw = data.get('tipo_pago', 'Contado')
        tipo_pago_clean = tipo_pago_raw.lower().strip().replace('é', 'e').replace('á', 'a')
        
        usd_paid = float(data.get('usd_paid', 0) or 0)
        ves_paid = float(data.get('ves_paid', 0) or 0)
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

                # PASO 1: Validar Stock
                for item in items:
                    cur.execute(
                        "SELECT name, price, stock FROM products WHERE id = %s AND tenant_id = %s::text FOR UPDATE", 
                        (item.get('product_id'), tenant_id)
                    )
                    product = cur.fetchone()
                    if not product:
                        raise Exception(f"Producto ID {item.get('product_id')} no encontrado")
                    
                    if product['stock'] < int(item.get('quantity', 0)):
                        raise Exception(f"Stock insuficiente para {product['name']}")
                    
                    price_usd = float(product['price'])
                    total_amount_usd += (price_usd * int(item.get('quantity')))
                    validated_items.append({**item, 'price': price_usd, 'current_stock': product['stock']})

                # PASO 2: Cálculo de Totales y Saldo
                total_amount_ves = total_amount_usd * exchange_rate
                total_paid_usd = usd_paid + (ves_paid / exchange_rate if exchange_rate > 0 else 0)
                saldo_pendiente = max(0.0, round(total_amount_usd - total_paid_usd, 2))

                # 🛠️ CORRECCIÓN 2: Lógica automática de crédito por saldo
                if 'credito' in tipo_pago_clean or saldo_pendiente > 0.05:
                    status = 'Crédito'
                    dias_credito = int(data.get('dias_credito', DEFAULT_CREDIT_DAYS))
                    fecha_vencimiento = datetime.now().date() + timedelta(days=dias_credito)
                    
                    # Actualizar balance del cliente (usando tenant_id)
                    cur.execute(
                        "UPDATE customers SET balance_pendiente_usd = balance_pendiente_usd + %s WHERE id = %s AND tenant_id = %s::text",
                        (saldo_pendiente, customer_id, tenant_id)
                    )
                else:
                    status = 'Completado'
                    fecha_vencimiento = None
                    dias_credito = 0

                # PASO 3: Insertar Venta (Asegúrate que la tabla tenga tenant_id)
                new_sale_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO sales (
                        id, customer_id, user_id, tenant_id, sale_date, 
                        total_amount_usd, total_amount_ves, exchange_rate_used, 
                        status, tipo_pago, usd_paid, ves_paid, balance_due_usd, 
                        fecha_vencimiento, dias_credito
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    new_sale_id, customer_id, current_user_id, tenant_id, datetime.now(),
                    total_amount_usd, total_amount_ves, exchange_rate,
                    status, tipo_pago_raw, usd_paid, ves_paid, saldo_pendiente,
                    fecha_vencimiento, dias_credito
                ))

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

                cur.connection.commit()
                return jsonify({"msg": "Venta exitosa", "sale_id": new_sale_id}), 201

        except Exception as e:
            if cur: cur.connection.rollback()
            return jsonify({"msg": str(e)}), 500

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
    if not tenant_id:
        return jsonify({"msg": "Falta tenant_id"}), 401

    try:
        with get_db_cursor() as cur:
            # 🛠️ CORRECCIÓN 3: Uso del campo 'cedula' y filtro estricto de tenant
            query = """
                SELECT 
                    s.id::text as sale_id,
                    c.name as customer_name,
                    c.cedula as customer_cedula,
                    s.sale_date::text,
                    s.fecha_vencimiento::text,
                    s.total_amount_usd,
                    s.balance_due_usd,
                    (CURRENT_DATE - s.fecha_vencimiento::date) as dias_en_mora
                FROM sales s
                JOIN customers c ON s.customer_id = c.id
                WHERE s.tenant_id = %s::text 
                  AND s.balance_due_usd > 0.05
                  AND (s.fecha_vencimiento IS NOT NULL OR s.status ILIKE '%%credito%%')
                ORDER BY s.fecha_vencimiento ASC
            """
            cur.execute(query, [tenant_id])
            return jsonify([dict(r) for r in cur.fetchall()]), 200
    except Exception as e:
        return jsonify({"msg": "Error al obtener créditos"}), 500

@sale_bp.route('/customer/<customer_id>/credit-sales', methods=['GET'])
@jwt_required()
def get_customer_credit_sales(customer_id):
    tenant_id = get_current_tenant()
    try:
        with get_db_cursor() as cur:
            # Buscamos ventas con saldo pendiente para este cliente específico
            query = """
                SELECT id::text, sale_date::text, total_amount_usd, 
                       balance_due_usd, fecha_vencimiento::text, status
                FROM sales 
                WHERE customer_id = %s 
                  AND tenant_id = %s::text 
                  AND balance_due_usd > 0.05
                ORDER BY sale_date DESC
            """
            cur.execute(query, (customer_id, tenant_id))
            sales = cur.fetchall()
            return jsonify([dict(r) for r in sales]), 200
    except Exception as e:
        app_logger.error(f"Error al obtener créditos del cliente: {e}")
        return jsonify({"msg": "Error interno del servidor"}), 500

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