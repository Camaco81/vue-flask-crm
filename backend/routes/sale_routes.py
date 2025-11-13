from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.db import get_db_cursor
from psycopg2 import sql 
from backend.utils.helpers import get_user_and_role, check_admin_permission, validate_required_fields, check_seller_permission
from backend.utils.bcv_api import get_dolarvzla_rate 
# 🟢 CORRECCIÓN: Usar el nombre de función que existe en inventory_utils.py
from backend.utils.inventory_utils import verificar_stock_y_alertar 
import logging
from decimal import Decimal
import uuid

sale_bp = Blueprint('sale', __name__)
app_logger = logging.getLogger('backend.routes.sale_routes') 

# Umbral de stock bajo para la alerta
STOCK_THRESHOLD = 10 
# Roles que pueden realizar ventas (admin/vendedor)
SALES_ROLES = ['admin', 'vendedor'] 

@sale_bp.route('', methods=['GET', 'POST'])
@jwt_required()
def sales_collection():
    """Maneja la creación de una nueva venta (POST) y el listado de ventas (GET)."""
    current_user_id, user_role = get_user_and_role() 
    
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado o token inválido"}), 401
    
    # 1. Verificar Permiso General (Admin o Vendedor)
    if not check_seller_permission(user_role):
        return jsonify({"msg": "Acceso denegado: solo personal de ventas y administradores pueden acceder a ventas"}), 403

    if request.method == "POST":
        # =========================================================
        # LÓGICA DE CREACIÓN (POST) - VENTA AL CONTADO / CRÉDITO
        # =========================================================
        data = request.get_json()
        
        # Validación de campos principales
        required_fields = ['customer_id', 'items']
        if error := validate_required_fields(data, required_fields):
            return jsonify({"msg": f"Missing required fields: {error}"}), 400
        
        # Campos de venta a crédito (opcionales para el POST general)
        tipo_pago = data.get('tipo_pago', 'Contado') # Default: Contado
        dias_credito = data.get('dias_credito', 30)

        customer_id = data.get("customer_id")
        items = data.get("items")
        seller_user_id = current_user_id
        
        if not isinstance(items, list) or len(items) == 0:
            return jsonify({"msg": "Items must be a non-empty list of products"}), 400

        # Obtener la tasa de cambio antes de la transacción
        try:
            exchange_rate = get_dolarvzla_rate()
        except Exception as e:
            app_logger.error(f"FATAL: No se pudo obtener la tasa de cambio para la venta: {e}", exc_info=True)
            return jsonify({"msg": "Error interno: No se pudo obtener la tasa de cambio del sistema"}), 500

        # Bloque de Transacción
        cur = None
        try:
            with get_db_cursor(commit=False) as cur:
                total_amount_usd = 0.0
                validated_items = []

                # Paso 1: Verificación de Stock y Cálculo de Totales (LECTURA)
                for item in items:
                    # Validación de items
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
                        
                    # Consulta de producto con bloqueo forzado (SELECT FOR UPDATE) para evitar race conditions
                    cur.execute("SELECT name, price, stock FROM products WHERE id = %s FOR UPDATE", (product_id,))
                    product_row = cur.fetchone()
                    
                    if not product_row:
                        cur.connection.rollback()
                        return jsonify({"msg": f"Producto con ID {product_id} no encontrado"}), 404
                        
                    current_stock = product_row['stock']
                    product_name = product_row['name']
                    price_usd = float(product_row['price'])
                    
                    # VERIFICACIÓN DE STOCK CRÍTICA
                    if current_stock < quantity:
                        cur.connection.rollback()
                        return jsonify({"msg": f"Stock insuficiente para {product_name}. Stock actual: {current_stock}"}), 400
                        
                    # CÁLCULO DE TOTALES
                    subtotal_usd = price_usd * quantity
                    total_amount_usd += subtotal_usd
                    
                    # Almacenar detalles del ítem para su posterior inserción
                    validated_items.append({
                        'product_id': product_id,
                        'quantity': quantity,
                        'price': price_usd, # Precio unitario en USD
                        'current_stock': current_stock
                    })

                total_amount_ves = total_amount_usd * exchange_rate
                
                # Paso 2: Validación de Crédito (Si aplica)
                monto_pendiente = 0.0
                status = 'Completado'
                fecha_vencimiento = None
                
                if tipo_pago == 'Crédito':
                    status = 'Abierto'
                    monto_pendiente = total_amount_usd
                    
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
                    nuevo_balance = balance + total_amount_usd
                    
                    # 2.b) Verificar Límite de Crédito
                    if nuevo_balance > limite:
                        cur.connection.rollback()
                        return jsonify({
                            "msg": f"Límite de crédito excedido. Límite: {limite}, Pendiente: {balance}, Venta: {total_amount_usd}. Nuevo Balance: {round(nuevo_balance, 2)}",
                            "code": "CREDIT_LIMIT_EXCEEDED"
                        }), 400
                        
                    # 2.c) Actualizar Balance Pendiente del Cliente (dentro de la transacción)
                    cur.execute(
                        "UPDATE customers SET balance_pendiente_usd = %s WHERE id = %s",
                        (nuevo_balance, customer_id)
                    )
                    
                    # 2.d) Calcular Fecha de Vencimiento
                    fecha_vencimiento = sql.SQL("CURRENT_DATE + INTERVAL '{} days'").format(sql.Literal(dias_credito))
                
                # Paso 3: Inserción de Venta
                
                # Construir la consulta de inserción de venta dinámicamente
                fields = ["id", "customer_id", "user_id", "sale_date", "total_amount_usd", "total_amount_ves", "exchange_rate_used", "status", "tipo_pago"]
                values = [str(uuid.uuid4()), customer_id, seller_user_id, sql.SQL("NOW()"), total_amount_usd, total_amount_ves, exchange_rate, status, tipo_pago]
                
                if tipo_pago == 'Crédito':
                    fields.extend(["dias_credito", "monto_pendiente", "fecha_vencimiento"])
                    values.extend([dias_credito, monto_pendiente, fecha_vencimiento])

                # Crear el string SQL para la inserción
                query_insert_sale = sql.SQL(
                    "INSERT INTO sales ({}) VALUES ({}) RETURNING id"
                ).format(
                    sql.SQL(', ').join(map(sql.Identifier, fields)),
                    sql.SQL(', ').join(map(sql.Literal, values))
                )
                
                cur.execute(query_insert_sale)
                new_sale_id = cur.fetchone()['id']

                # Paso 4: Insertar Ítems y Disminuir Stock
                for item in validated_items:
                    # 4.a) Insertar Item
                    cur.execute(
                        "INSERT INTO sale_items (sale_id, product_id, quantity, price) VALUES (%s, %s, %s, %s);",
                        (new_sale_id, item['product_id'], item['quantity'], item['price'])
                    )
                    
                    # 4.b) Disminuir Stock
                    cur.execute(
                        "UPDATE products SET stock = stock - %s WHERE id = %s;",
                        (item['quantity'], item['product_id'])
                    )
                    
                    # 4.c) Generar Alerta de Stock (Llamada de función UTILITARIA)
                    remaining_stock = item['current_stock'] - item['quantity']
                    if remaining_stock <= STOCK_THRESHOLD:
                        # 🟢 CORRECCIÓN: Llamada a la función que SÍ existe, pasando solo el ID.
                        verificar_stock_y_alertar(item['product_id'])
                
                # Confirmar la transacción
                cur.connection.commit()
                
                response = {
                    "msg": f"Venta {tipo_pago} registrada exitosamente", 
                    "sale_id": str(new_sale_id),
                    "total_usd": round(total_amount_usd, 2),
                    "total_ves": round(total_amount_ves, 2),
                    "rate_used": exchange_rate,
                    "tipo_pago": tipo_pago
                }
                
                return jsonify(response), 201
                
        except Exception as e:
            if cur and cur.connection:
                cur.connection.rollback()
            app_logger.error(f"Error al registrar la venta (ROLLBACK): {e}", exc_info=True)
            return jsonify({"msg": "Error interno al registrar la venta. La transacción fue cancelada.", "error": str(e)}), 500
            
    elif request.method == "GET":
        # =========================================================
        # LÓGICA DE LISTADO (GET /api/sales) - OPTIMIZADA
        # =========================================================
        try:
            # Consulta común para listado y detalle
            base_query = """
                SELECT s.id, s.customer_id, c.name as customer_name, c.email as customer_email,
                       s.sale_date, s.status, s.tipo_pago,
                       s.total_amount_usd AS total_amount, s.total_amount_ves, 
                       s.exchange_rate_used, 
                       u.email as seller_email, u.id as seller_id, 
                       s.monto_pendiente, s.fecha_vencimiento, s.dias_credito,
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
                GROUP BY s.id, c.name, c.email, s.sale_date, s.status, s.tipo_pago,
                s.total_amount_usd, s.total_amount_ves, s.exchange_rate_used, u.email, u.id,
                s.monto_pendiente, s.fecha_vencimiento, s.dias_credito
                ORDER BY s.sale_date DESC;
            """
            
            with get_db_cursor() as cur:
                cur.execute(base_query, tuple(params))
                sales_list = [dict(record) for record in cur.fetchall()]
                
            return jsonify(sales_list), 200
            
        except Exception as e:
            app_logger.error(f"Error al obtener las ventas: {e}", exc_info=True)
            return jsonify({"msg": "Error al obtener las ventas", "error": str(e)}), 500

@sale_bp.route('/<uuid:sale_id>', methods=["GET", "DELETE"])
@jwt_required()
def sales_single(sale_id):
    """Maneja la vista individual (GET) y eliminación (DELETE) de una venta."""
    
    current_user_id, user_role = get_user_and_role()
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado o token inválido"}), 401

    sale_id_str = str(sale_id)

    if request.method == "GET":
        # =========================================================
        # LÓGICA DE VISTA INDIVIDUAL (GET) - OPTIMIZADA
        # =========================================================
        try:
            base_query = """
                SELECT s.id, s.customer_id, c.name as customer_name, c.email as customer_email, c.address as customer_address,
                       s.sale_date, s.status, s.tipo_pago,
                       s.total_amount_usd AS total_amount, 
                       s.total_amount_ves, s.exchange_rate_used, 
                       u.email as seller_email, u.id as seller_id,
                       s.monto_pendiente, s.fecha_vencimiento, s.dias_credito,
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
                GROUP BY s.id, s.customer_id, c.name, c.email, c.address, s.sale_date, s.status, s.tipo_pago,
                s.total_amount_usd, s.total_amount_ves, s.exchange_rate_used, u.email, u.id,
                s.monto_pendiente, s.fecha_vencimiento, s.dias_credito;
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
        # =========================================================
        # LÓGICA DE ELIMINACIÓN (DELETE) - CON ROLLBACK DE CRÉDITO
        # =========================================================
        cur = None
        try:
            with get_db_cursor(commit=False) as cur: 
                
                # 1. Obtener datos clave de la venta y bloquear el cliente (si es a crédito)
                cur.execute(
                    "SELECT user_id, customer_id, tipo_pago, monto_pendiente FROM sales WHERE id = %s FOR UPDATE",
                    (sale_id_str,)
                )
                sale_data = cur.fetchone()

                if not sale_data:
                    cur.connection.rollback()
                    return jsonify({"msg": "Venta no encontrada"}), 404
                
                sale_user_id = sale_data['user_id']
                customer_id = sale_data['customer_id']
                tipo_pago = sale_data['tipo_pago']
                monto_pendiente = float(sale_data['monto_pendiente'] or 0.0)

                # 2. Verificar Permisos (Admin o vendedor creador)
                if not check_admin_permission(user_role) and str(sale_user_id) != str(current_user_id):
                    cur.connection.rollback()
                    return jsonify({"msg": "No autorizado para eliminar esta venta"}), 403
                
                # 3. ROLLBACK DE CRÉDITO (Si aplica)
                if tipo_pago == 'Crédito' and monto_pendiente > 0:
                    # Bloquear y actualizar balance del cliente
                    cur.execute(
                        "SELECT balance_pendiente_usd FROM customers WHERE id = %s FOR UPDATE",
                        (customer_id,)
                    )
                    customer = cur.fetchone()
                    
                    if customer:
                        nuevo_balance = float(customer['balance_pendiente_usd']) - monto_pendiente
                        # Prevenir balance negativo (aunque no debería pasar si la lógica es correcta)
                        if nuevo_balance < 0:
                            app_logger.warning(f"Balance de cliente {customer_id} se vuelve negativo al eliminar venta {sale_id_str}.")
                            nuevo_balance = 0 
                            
                        cur.execute(
                            "UPDATE customers SET balance_pendiente_usd = %s WHERE id = %s",
                            (nuevo_balance, customer_id)
                        )

                # 4. Eliminar venta e ítems (CASCADE DELETE es mejor, pero lo hacemos explícito)
                # 4.a) Obtener los items vendidos para reponer stock
                cur.execute(
                    "SELECT product_id, quantity FROM sale_items WHERE sale_id = %s",
                    (sale_id_str,)
                )
                items_to_restore = cur.fetchall()

                # 4.b) Eliminar items de venta
                cur.execute("DELETE FROM sale_items WHERE sale_id = %s;", (sale_id_str,))
                
                # 4.c) Eliminar venta
                cur.execute("DELETE FROM sales WHERE id = %s;", (sale_id_str,))
                deleted_rows = cur.rowcount

                # 4.d) Reponer Stock
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


# =========================================================
# RUTAS DE REPORTES ADMIN
# =========================================================

@sale_bp.route('/reports', methods=['GET'])
@jwt_required()
def admin_general_reports():
    """Obtiene el listado COMPLETO de todas las ventas (Admin only)."""
    current_user_id, user_role = get_user_and_role()
    
    # 1. Verificar Permisos (Solo Admin)
    if not check_admin_permission(user_role):
        return jsonify({"msg": "Acceso denegado: Se requiere rol de Administrador."}), 403

    try:
        # Reutilizamos la consulta base
        query = """
            SELECT s.id, s.customer_id, c.name as customer_name, c.email as customer_email,
                   s.sale_date, s.status, s.tipo_pago,
                   s.total_amount_usd AS total_amount, s.total_amount_ves, s.exchange_rate_used, 
                   u.email as seller_email, u.id as seller_id, 
                   s.monto_pendiente, s.fecha_vencimiento, s.dias_credito,
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
            GROUP BY s.id, c.name, c.email, s.sale_date, s.status, s.tipo_pago,
            s.total_amount_usd, s.total_amount_ves, s.exchange_rate_used, u.email, u.id,
            s.monto_pendiente, s.fecha_vencimiento, s.dias_credito
            ORDER BY s.sale_date DESC;
        """
        
        with get_db_cursor() as cur:
            cur.execute(query)
            sales_list = [dict(record) for record in cur.fetchall()]
            
        return jsonify(sales_list), 200
        
    except Exception as e:
        app_logger.error(f"Error al obtener los reportes generales admin: {e}", exc_info=True)
        return jsonify({"msg": "Error al cargar los reportes generales del administrador", "error": str(e)}), 500