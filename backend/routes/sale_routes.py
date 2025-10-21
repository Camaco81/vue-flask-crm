from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.db import get_db_cursor
# Importaciones necesarias
from backend.utils.helpers import get_user_and_role, check_admin_permission, validate_required_fields, check_product_manager_permission

sale_bp = Blueprint('sale', __name__, url_prefix='/api/sales')

@sale_bp.route('', methods=['GET', 'POST'])
@jwt_required()
def sales_collection():
    current_user_id, user_role = get_user_and_role() # <-- user_role es el role_id (int)
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado o token inválido"}), 401
    
    # 🚨 Permiso para CREAR (POST) y LISTAR (GET)
    if not check_product_manager_permission(user_role):
        return jsonify({"msg": "Acceso denegado: solo personal de ventas y administradores pueden acceder a ventas"}), 403

    if request.method == "POST":
        # =========================================================
        # LÓGICA DE CREACIÓN (POST)
        # =========================================================
        data = request.get_json()
        if error := validate_required_fields(data, ['customer_id', 'items']):
             return jsonify({"msg": f"Missing required fields: {error}"}), 400
        if not isinstance(data['items'], list) or not data['items']:
            return jsonify({"msg": "Items must be a non-empty list"}), 400

        customer_id = data.get("customer_id")
        items = data.get("items")
        seller_user_id = current_user_id

        try:
            total_amount = 0
            product_details = {} # Almacena precio para evitar re-lecturas
            
            with get_db_cursor() as cur: # 1. Leer productos para calcular total
                for item in items:
                    if error := validate_required_fields(item, ['product_id', 'quantity']):
                        return jsonify({"msg": f"Each item missing field: {error}"}), 400
                    
                    # Cuidado con la cantidad (debe ser un número)
                    quantity = int(item['quantity'])
                    if quantity <= 0:
                        return jsonify({"msg": "La cantidad debe ser mayor a cero"}), 400
                        
                    cur.execute("SELECT name, price FROM products WHERE id = %s", (item['product_id'],))
                    product_row = cur.fetchone()
                    if product_row:
                        price = float(product_row['price'])
                        # 🚨 CORRECCIÓN CLAVE: Multiplicar precio por cantidad para el total
                        total_amount += price * quantity
                        product_details[item['product_id']] = {'name': product_row['name'], 'price': price, 'quantity': quantity}
                    else:
                        return jsonify({"msg": f"Producto con ID {item['product_id']} no encontrado"}), 404

            with get_db_cursor(commit=True) as cur: # 2. Insertar venta e ítems
                # Insertar Venta
                cur.execute(
                    "INSERT INTO sales (customer_id, user_id, total_amount) VALUES (%s, %s, %s) RETURNING id;",
                    (customer_id, seller_user_id, total_amount)
                )
                new_sale_id = cur.fetchone()['id'] 

                # Insertar Ítems
                for product_id, details in product_details.items():
                    cur.execute(
                        "INSERT INTO sale_items (sale_id, product_id, quantity, price) VALUES (%s, %s, %s, %s);",
                        (new_sale_id, product_id, details['quantity'], details['price'])
                    )
                
            return jsonify({"msg": "Venta registrada exitosamente", "sale_id": str(new_sale_id)}), 201
            
        except Exception as e:
            # Aquí es útil manejar errores específicos de la DB (e.g., customer_id o product_id inexistente)
            print(f"Error al registrar la venta: {e}")
            return jsonify({"msg": "Error al registrar la venta", "error": str(e)}), 500
        
    elif request.method == "GET":
        # =========================================================
        # LÓGICA DE LISTADO (GET) - FILTRADO POR ROL
        # =========================================================
        try:
            query = """
                SELECT s.id, s.customer_id, c.name as customer_name, c.email as customer_email,
                       s.sale_date, s.status, s.total_amount,
                       u.email as seller_email, u.id as seller_id, -- <-- Información del vendedor
                       json_agg(json_build_object(
                            'product_name', p.name,
                            'quantity', si.quantity,
                            'price', si.price -- <-- Usamos el precio de VENTA (si.price) no el actual (p.price)
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
                GROUP BY s.id, c.name, c.email, s.sale_date, s.status, s.total_amount, u.email, u.id
                ORDER BY s.sale_date DESC;
            """
            
            with get_db_cursor() as cur:
                cur.execute(query, tuple(params))
                sales_list = [dict(record) for record in cur.fetchall()]
                
            # Tu JSON de salida para la lista YA incluye:
            # - seller_email
            # - seller_id (como seller_id)
            # Esto resuelve el requisito del administrador de saber quién hizo la venta.
            return jsonify(sales_list), 200
            
        except Exception as e:
            print(f"Error al obtener las ventas: {e}")
            return jsonify({"msg": "Error al obtener las ventas", "error": str(e)}), 500

@sale_bp.route('/<uuid:sale_id>', methods=["GET", "DELETE"])
@jwt_required()
def sales_single(sale_id):
    # Lógica de GET y DELETE individual (se mantiene sin cambios mayores, ya estaba bien)
    # ... (El resto de la función 'sales_single' se mantiene igual que tu código)
    # --------------------------------------------------------------------------
    current_user_id, user_role = get_user_and_role()
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado o token inválido"}), 401

    if request.method == "GET":
        try:
            base_query = """
                SELECT s.id, s.customer_id, c.name as customer_name, c.email as customer_email, c.address as customer_address,
                       s.sale_date, s.status, s.total_amount, u.email as seller_email, u.id as seller_id,
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

            if not check_admin_permission(user_role) and str(sale_user_id) != str(current_user_id): # Convertir a str para comparar UUIDs
                return jsonify({"msg": "No autorizado para eliminar esta venta"}), 403

            with get_db_cursor(commit=True) as cur: # Eliminar venta e ítems
                # Se asume que la DB no tiene eliminación en cascada, por lo que borramos los items primero
                cur.execute("DELETE FROM sale_items WHERE sale_id = %s;", (str(sale_id),))
                cur.execute("DELETE FROM sales WHERE id = %s;", (str(sale_id),))
                deleted_rows = cur.rowcount
            
            if deleted_rows > 0:
                return jsonify({"msg": "Venta y sus items eliminados exitosamente"}), 200
            # Si deleted_rows es 0, la venta no existía o el usuario no la poseía (aunque la verificación lo captura)
            return jsonify({"msg": "Error al eliminar la venta o venta ya eliminada"}), 500

        except Exception as e:
            print(f"Error al eliminar la venta: {e}")
            return jsonify({"msg": "Error al eliminar la venta", "error": str(e)}), 500