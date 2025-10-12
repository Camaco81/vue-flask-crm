from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from db import get_db_cursor
from utils.helpers import get_user_and_role, check_admin_permission, check_seller_permission, validate_required_fields
import uuid # Necesario si los IDs son UUID y necesitas validarlos/generarlos

sale_bp = Blueprint('sale', __name__, url_prefix='/api/sales')

@sale_bp.route('', methods=['GET', 'POST'])
@jwt_required()
def sales_collection():
    current_user_id, user_role = get_user_and_role()
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado o token inválido"}), 401

    if request.method == "POST":
        if not check_seller_permission(user_role): # Admins y Vendedores pueden crear ventas
            return jsonify({"msg": "Acceso denegado: solo vendedores y administradores pueden registrar ventas"}), 403

        data = request.get_json()
        if not validate_required_fields(data, ['customer_id', 'items']):
            return jsonify({"msg": "Missing required fields: customer_id, items"}), 400
        if not isinstance(data['items'], list) or not data['items']:
            return jsonify({"msg": "Items must be a non-empty list"}), 400

        customer_id = data.get("customer_id")
        items = data.get("items")
        seller_user_id = current_user_id # La venta siempre se asocia al usuario logueado

        try:
            total_amount = 0
            product_details = {} 
            with get_db_cursor() as cur: # Leer productos para calcular total
                for item in items:
                    if not validate_required_fields(item, ['product_id', 'quantity']):
                        return jsonify({"msg": "Each item must have product_id and quantity"}), 400
                    
                    cur.execute("SELECT name, price FROM products WHERE id = %s", (item['product_id'],))
                    product_row = cur.fetchone()
                    if product_row:
                        product_details[item['product_id']] = {'name': product_row['name'], 'price': float(product_row['price'])}
                        total_amount += float(product_row['price']) * item['quantity']
                    else:
                        return jsonify({"msg": f"Producto con ID {item['product_id']} no encontrado"}), 404

            with get_db_cursor(commit=True) as cur: # Insertar venta e ítems
                cur.execute(
                    "INSERT INTO sales (customer_id, user_id, total_amount) VALUES (%s, %s, %s) RETURNING id;",
                    (customer_id, seller_user_id, total_amount)
                )
                new_sale_id = cur.fetchone()['id'] # Asume que la DB genera el UUID

                for item in items:
                    cur.execute(
                        "INSERT INTO sale_items (sale_id, product_id, quantity, price) VALUES (%s, %s, %s, %s);",
                        (new_sale_id, item['product_id'], item['quantity'], product_details[item['product_id']]['price'])
                    )
            
            return jsonify({"msg": "Venta registrada exitosamente", "sale_id": str(new_sale_id)}), 201
        except Exception as e:
            return jsonify({"msg": "Error al registrar la venta", "error": str(e)}), 500
        
    elif request.method == "GET":
        try:
            query = """
                SELECT s.id, s.customer_id, c.name as customer_name, c.email as customer_email, c.address as customer_address,
                       s.sale_date, s.status, s.total_amount, u.email as seller_email, u.id as seller_user_id,
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
            if not check_admin_permission(user_role): # Vendedores solo ven sus ventas
                query += " WHERE s.user_id = %s"
                params.append(current_user_id)
            
            query += " GROUP BY s.id, s.customer_id, c.name, c.email, c.address, s.sale_date, s.status, s.total_amount, u.email, u.id ORDER BY s.sale_date DESC;"
            
            with get_db_cursor() as cur:
                cur.execute(query, tuple(params))
                sales_records = cur.fetchall()
                sales_list = [dict(record) for record in sales_records]
            return jsonify(sales_list), 200
        except Exception as e:
            return jsonify({"msg": "Error al obtener las ventas", "error": str(e)}), 500

@sale_bp.route('/<uuid:sale_id>', methods=["GET", "DELETE"])
@jwt_required()
def sales_single(sale_id):
    current_user_id, user_role = get_user_and_role()
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado o token inválido"}), 401

    if request.method == "GET":
        try:
            base_query = """
                SELECT s.id, s.customer_id, c.name as customer_name, c.email as customer_email, c.address as customer_address,
                       s.sale_date, s.status, s.total_amount, u.email as seller_email, u.id as seller_user_id,
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
            params = [str(sale_id)]
            if not check_admin_permission(user_role):
                base_query += " AND s.user_id = %s"
                params.append(current_user_id)
            
            base_query += " GROUP BY s.id, s.customer_id, c.name, c.email, c.address, s.sale_date, s.status, s.total_amount, u.email, u.id;"

            with get_db_cursor() as cur:
                cur.execute(base_query, tuple(params))
                sale_record = cur.fetchone()

            if sale_record:
                return jsonify(dict(sale_record)), 200
            return jsonify({"msg": "Venta no encontrada o no tienes permisos para verla"}), 404
        except Exception as e:
            return jsonify({"msg": "Error al obtener la venta", "error": str(e)}), 500

    elif request.method == "DELETE":
        try:
            with get_db_cursor() as cur: # Leer user_id de la venta
                cur.execute("SELECT user_id FROM sales WHERE id = %s", (str(sale_id),))
                sale_user_id_row = cur.fetchone()

            if not sale_user_id_row:
                return jsonify({"msg": "Venta no encontrada"}), 404
            
            sale_user_id = sale_user_id_row['user_id']

            if not check_admin_permission(user_role) and sale_user_id != current_user_id:
                return jsonify({"msg": "No autorizado para eliminar esta venta"}), 403

            with get_db_cursor(commit=True) as cur: # Eliminar venta e ítems
                cur.execute("DELETE FROM sale_items WHERE sale_id = %s;", (str(sale_id),))
                cur.execute("DELETE FROM sales WHERE id = %s;", (str(sale_id),))
                deleted_rows = cur.rowcount
            
            if deleted_rows > 0:
                return jsonify({"msg": "Venta y sus items eliminados exitosamente"}), 200
            return jsonify({"msg": "Error al eliminar la venta"}), 500

        except Exception as e:
            return jsonify({"msg": "Error al eliminar la venta", "error": str(e)}), 500