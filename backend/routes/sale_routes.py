from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.db import get_db_cursor
from psycopg2 import sql 
from backend.utils.helpers import get_user_and_role, check_admin_permission, validate_required_fields, check_seller_permission
from backend.utils.bcv_api import get_dolarvzla_rate # <--- ¡IMPORTACIÓN CLAVE AÑADIDA!
import logging

sale_bp = Blueprint('sale', __name__)
app_logger = logging.getLogger('backend.routes.sale_routes') # Usar logger específico para el archivo

# Umbral de stock bajo para la alerta
STOCK_THRESHOLD = 10 

@sale_bp.route('', methods=['GET', 'POST'])
@jwt_required()
def sales_collection():
    """Maneja la creación de una nueva venta (POST) y el listado de ventas (GET)."""
    current_user_id, user_role = get_user_and_role() 
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado o token inválido"}), 401
    
    # Verificar si el usuario tiene permiso de Ventas o Admin para LISTAR y CREAR
    if not check_seller_permission(user_role):
        return jsonify({"msg": "Acceso denegado: solo personal de ventas y administradores pueden acceder a ventas"}), 403

    if request.method == "POST":
        # =========================================================
        # LÓGICA DE CREACIÓN (POST) con Control Transaccional y Stock
        # =========================================================
        data = request.get_json()
        
        # 1. Validación de campos principales
        required_fields = ['customer_id', 'items']
        if error := validate_required_fields(data, required_fields):
            return jsonify({"msg": f"Missing required fields: {error}"}), 400
        
        customer_id = data.get("customer_id")
        items = data.get("items")
        seller_user_id = current_user_id

        if not customer_id or str(customer_id).strip() == "":
            return jsonify({"msg": "customer_id no puede estar vacío"}), 400
        if not isinstance(items, list) or len(items) == 0:
            return jsonify({"msg": "Items must be a non-empty list of products"}), 400

        # 🚨 NUEVO: Obtener la tasa de cambio antes de la transacción
        try:
            exchange_rate = get_dolarvzla_rate()
        except Exception as e:
            # Si el backend no puede obtener la tasa ni la de respaldo, es un error fatal.
            app_logger.error(f"FATAL: No se pudo obtener la tasa de cambio para la venta: {e}", exc_info=True)
            return jsonify({"msg": "Error interno: No se pudo obtener la tasa de cambio del sistema"}), 500


        # Bloque de Transacción
        cur = None
        try:
            with get_db_cursor(commit=False) as cur:
                total_amount_usd = 0.0 # El monto base de los precios (asumimos USD)
                total_amount_ves = 0.0 # El monto calculado en Bolívares
                stock_alerts = []
                
                # Almacenamos los datos necesarios para la inserción
                validated_items = []

                # Paso 1: Verificación de Stock y Cálculo de Totales (LECTURA)
                for item in items:
                    if error := validate_required_fields(item, ['product_id', 'quantity']):
                        cur.connection.rollback()
                        return jsonify({"msg": f"Each item missing field: {error}"}), 400
                        
                    product_id = item.get('product_id')
                    quantity_raw = item.get('quantity')

                    if not product_id or str(product_id).strip() == "":
                        cur.connection.rollback()
                        return jsonify({"msg": "product_id en item no puede estar vacío"}), 400
                        
                    try:
                        quantity = int(quantity_raw)
                        if quantity <= 0:
                            cur.connection.rollback()
                            return jsonify({"msg": "La cantidad debe ser mayor a cero"}), 400
                    except (ValueError, TypeError):
                        cur.connection.rollback()
                        return jsonify({"msg": f"La cantidad ({quantity_raw}) debe ser un número entero válido"}), 400
                        
                    # Obtener stock y precio del producto en una sola consulta
                    cur.execute("SELECT name, price, stock FROM products WHERE id = %s", (product_id,))
                    product_row = cur.fetchone()
                    
                    if not product_row:
                        cur.connection.rollback()
                        return jsonify({"msg": f"Producto con ID {product_id} no encontrado"}), 404
                        
                    current_stock = product_row['stock']
                    product_name = product_row['name']
                    price_usd = float(product_row['price']) # Asumimos que este es el precio en USD
                    
                    # 🚨 VERIFICACIÓN DE STOCK CRÍTICA
                    if current_stock < quantity:
                        cur.connection.rollback()
                        return jsonify({"msg": f"Stock insuficiente para {product_name}. Stock actual: {current_stock}"}), 400
                        
                    # 🚨 CÁLCULO DE TOTALES
                    subtotal_usd = price_usd * quantity
                    subtotal_ves = subtotal_usd * exchange_rate # <--- CÁLCULO EN BOLÍVARES
                    
                    total_amount_usd += subtotal_usd
                    total_amount_ves += subtotal_ves 
                    
                    # 🚨 ALERTA DE STOCK BAJO (Requisito 2)
                    remaining_stock = current_stock - quantity
                    if remaining_stock <= STOCK_THRESHOLD:
                        alert_level = "ALERTA CRÍTICA" if remaining_stock == 0 else "ALERTA"
                        stock_alerts.append(f"{alert_level}: El stock de {product_name} quedará en {remaining_stock} (Umbral: {STOCK_THRESHOLD})")
                        
                    validated_items.append({
                        'product_id': product_id,
                        'quantity': quantity,
                        'price': price_usd # Precio unitario en USD
                    })
            
                # Paso 2: Inserción de Venta, Ítems y Actualización de Stock (ESCRITURA)

                # 2.a) Insertar Venta
                # 🚨 CONSULTA SQL ACTUALIZADA para incluir VES y Tasa
                cur.execute(
                    "INSERT INTO sales (customer_id, user_id, total_amount, total_amount_ves, exchange_rate_used, sale_date) VALUES (%s, %s, %s, %s, %s, NOW()) RETURNING id;",
                    (customer_id, seller_user_id, total_amount_usd, total_amount_ves, exchange_rate)
                )
                new_sale_id = cur.fetchone()['id']

                # 2.b) Insertar Ítems y Disminuir Stock
                for item in validated_items:
                    # Insertar Item de Venta (usa el precio en USD)
                    cur.execute(
                        "INSERT INTO sale_items (sale_id, product_id, quantity, price) VALUES (%s, %s, %s, %s);",
                        (new_sale_id, item['product_id'], item['quantity'], item['price'])
                    )
                    
                    # 🚨 DISMINUIR STOCK (Requisito 1)
                    cur.execute(
                        "UPDATE products SET stock = stock - %s WHERE id = %s;",
                        (item['quantity'], item['product_id'])
                    )
                
                # Confirmar la transacción
                cur.connection.commit()
                
                response = {
                    "msg": "Venta registrada exitosamente", 
                    "sale_id": str(new_sale_id),
                    "total_usd": round(total_amount_usd, 2),
                    "total_ves": round(total_amount_ves, 2),
                    "rate_used": exchange_rate
                }
                if stock_alerts:
                    response['stock_alerts'] = stock_alerts # Añadir alertas a la respuesta
                
                return jsonify(response), 201
            
        except Exception as e:
            # Si cur existe y tiene una conexión, intenta el rollback
            if cur and cur.connection:
                cur.connection.rollback()
            app_logger.error(f"Error al registrar la venta (ROLLBACK): {e}", exc_info=True)
            return jsonify({"msg": "Error interno al registrar la venta. La transacción fue cancelada.", "error": str(e)}), 500
            
    elif request.method == "GET":
        # =========================================================
        # LÓGICA DE LISTADO (GET) - Actualizada para mostrar VES y Tasa
        # =========================================================
        try:
            query = """
                SELECT s.id, s.customer_id, c.name as customer_name, c.email as customer_email,
                        s.sale_date, s.status, s.total_amount AS total_usd, 
                        s.total_amount_ves, s.exchange_rate_used, 
                        u.email as seller_email, u.id as seller_id, 
                        json_agg(json_build_object(
                            'product_name', p.name,
                            'quantity', si.quantity,
                            'price_usd', si.price 
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
                query += " WHERE s.user_id = %s"
                params.append(current_user_id)
            
            # Agrupación para consolidar los ítems en un array JSON
            query += """
                GROUP BY s.id, c.name, c.email, s.sale_date, s.status, 
                s.total_amount, s.total_amount_ves, s.exchange_rate_used, u.email, u.id
                ORDER BY s.sale_date DESC;
            """
            
            with get_db_cursor() as cur:
                cur.execute(query, tuple(params))
                sales_list = [dict(record) for record in cur.fetchall()]
                
            return jsonify(sales_list), 200
            
        except Exception as e:
            app_logger.error(f"Error al obtener las ventas: {e}", exc_info=True)
            return jsonify({"msg": "Error al obtener las ventas", "error": str(e)}), 500

@sale_bp.route('/<uuid:sale_id>', methods=["GET", "DELETE"])
@jwt_required()
def sales_single(sale_id):
    """Maneja la vista individual (GET) y eliminación (DELETE) de una venta."""
    # ... (Resto del código sin cambios, solo se actualiza la consulta GET individual)
    
    current_user_id, user_role = get_user_and_role()
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado o token inválido"}), 401

    if request.method == "GET":
        try:
            base_query = """
                SELECT s.id, s.customer_id, c.name as customer_name, c.email as customer_email, c.address as customer_address,
                        s.sale_date, s.status, s.total_amount AS total_usd, 
                        s.total_amount_ves, s.exchange_rate_used, 
                        u.email as seller_email, u.id as seller_id,
                        json_agg(json_build_object(
                            'product_name', p.name,
                            'quantity', si.quantity,
                            'price_usd', si.price
                        )) AS items
                FROM sales s
                JOIN customers c ON s.customer_id = c.id
                JOIN users u ON s.user_id = u.id
                JOIN sale_items si ON s.id = si.sale_id
                JOIN products p ON si.product_id = p.id
                WHERE s.id = %s
            """
            params = [str(sale_id)]
            if not check_admin_permission(user_role):
                base_query += " AND s.user_id = %s"
                params.append(current_user_id)
            
            base_query += " GROUP BY s.id, s.customer_id, c.name, c.email, c.address, s.sale_date, s.status, s.total_amount, s.total_amount_ves, s.exchange_rate_used, u.email, u.id;"

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
        # Lógica de DELETE individual (sin cambios)
        # ... (código DELETE)
        try:
            # 1. Verificar si el usuario tiene permiso (Admin o vendedor de la venta)
            with get_db_cursor() as cur: 
                cur.execute("SELECT user_id FROM sales WHERE id = %s", (str(sale_id),))
                sale_user_id_row = cur.fetchone()

            if not sale_user_id_row:
                return jsonify({"msg": "Venta no encontrada"}), 404
            
            sale_user_id = sale_user_id_row['user_id']

            if not check_admin_permission(user_role) and str(sale_user_id) != str(current_user_id):
                return jsonify({"msg": "No autorizado para eliminar esta venta"}), 403

            # 2. Eliminar venta e ítems (Transacción implícita si get_db_cursor tiene commit=True por defecto)
            with get_db_cursor(commit=True) as cur: 
                # Eliminar items primero (Foreign Key constraint)
                cur.execute("DELETE FROM sale_items WHERE sale_id = %s;", (str(sale_id),))
                cur.execute("DELETE FROM sales WHERE id = %s;", (str(sale_id),))
                deleted_rows = cur.rowcount
            
            if deleted_rows > 0:
                return jsonify({"msg": "Venta y sus items eliminados exitosamente"}), 200
            return jsonify({"msg": "Error al eliminar la venta o venta ya eliminada"}), 500

        except Exception as e:
            app_logger.error(f"Error al eliminar la venta {sale_id}: {e}", exc_info=True)
            return jsonify({"msg": "Error al eliminar la venta", "error": str(e)}), 500