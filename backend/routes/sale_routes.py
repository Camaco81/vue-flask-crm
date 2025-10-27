from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.db import get_db_cursor
# Importaciones necesarias
# (Asumo que estas funciones auxiliares están bien implementadas, por lo que no las toco)
# En backend/routes/sale_routes.py - Cerca de las importaciones
from backend.utils.helpers import get_user_and_role, check_admin_permission, validate_required_fields, check_seller_permission # <--- Importa la función correcta
sale_bp = Blueprint('sale', __name__)

@sale_bp.route('', methods=['GET', 'POST'])
@jwt_required()
def sales_collection():
    current_user_id, user_role = get_user_and_role() # <-- user_role es el role_id (int)
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado o token inválido"}), 401
    
    # Permiso para CREAR (POST) y LISTAR (GET)
    # NOTA: Renombré la función de permiso en el FRONTEND a 'check_seller_permission' para ser más claro
    if not check_seller_permission(user_role):
        return jsonify({"msg": "Acceso denegado: solo personal de ventas y administradores pueden acceder a ventas"}), 403

    if request.method == "POST":
        # =========================================================
        # LÓGICA DE CREACIÓN (POST)
        # =========================================================
        data = request.get_json()
        
        # 1. Validación de campos principales y lista de ítems
        if error := validate_required_fields(data, ['customer_id', 'items']):
             return jsonify({"msg": f"Missing required fields: {error}"}), 400
        
        customer_id = data.get("customer_id")
        items = data.get("items")
        seller_user_id = current_user_id

        # 🚨 CORRECCIÓN CLAVE 1: Validar que customer_id no sea un string vacío
        if not customer_id or str(customer_id).strip() == "":
             return jsonify({"msg": "customer_id no puede estar vacío"}), 400

        # 🚨 CORRECCIÓN CLAVE 2: Validar que items es una lista no vacía y contiene diccionarios.
        if not isinstance(items, list) or len(items) == 0:
            return jsonify({"msg": "Items must be a non-empty list of products"}), 400

        try:
            total_amount = 0
            product_details = {} # Almacena precio/cantidad para evitar re-lecturas
            
            with get_db_cursor() as cur: # 1. Leer productos para calcular total
                for item in items:
                    # 2. Validación de campos por ítem
                    if error := validate_required_fields(item, ['product_id', 'quantity']):
                        return jsonify({"msg": f"Each item missing field: {error}"}), 400
                    
                    product_id = item.get('product_id')
                    quantity_raw = item.get('quantity')

                    # 🚨 CORRECCIÓN CLAVE 3: Validar que product_id no sea un string vacío
                    if not product_id or str(product_id).strip() == "":
                        return jsonify({"msg": "product_id en item no puede estar vacío"}), 400
                        
                    # 🚨 CORRECCIÓN CLAVE 4: Asegurar que quantity es un número entero positivo
                    try:
                        quantity = int(quantity_raw)
                        if quantity <= 0:
                            return jsonify({"msg": "La cantidad debe ser mayor a cero"}), 400
                    except (ValueError, TypeError):
                        return jsonify({"msg": f"La cantidad ({quantity_raw}) debe ser un número entero válido"}), 400
                        
                    # Leer detalles del producto
                    # NOTA: Se asume que el ID es un UUID o un tipo compatible con %s
                    cur.execute("SELECT name, price FROM products WHERE id = %s", (product_id,))
                    product_row = cur.fetchone()
                    if product_row:
                        price = float(product_row['price'])
                        # Multiplicar precio por cantidad para el total
                        total_amount += price * quantity
                        product_details[product_id] = {'name': product_row['name'], 'price': price, 'quantity': quantity}
                    else:
                        return jsonify({"msg": f"Producto con ID {product_id} no encontrado"}), 404

            # 3. Insertar venta e ítems (Solo si la validación anterior fue exitosa)
            with get_db_cursor(commit=True) as cur: 
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
            # Capturar y registrar cualquier otro error, como un ID de cliente inválido (UUID)
            print(f"Error al registrar la venta: {e}")
            # El error 500 es genérico, pero el mensaje debe ser útil
            return jsonify({"msg": "Error interno al registrar la venta", "error": str(e)}), 500
        
    elif request.method == "GET":
        # =========================================================
        # LÓGICA DE LISTADO (GET) - SIN CAMBIOS
        # =========================================================
        try:
            query = """
                SELECT s.id, s.customer_id, c.name as customer_name, c.email as customer_email,
                       s.sale_date, s.status, s.total_amount,
                       u.email as seller_email, u.id as seller_id, -- Información del vendedor
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
                
            return jsonify(sales_list), 200
            
        except Exception as e:
            print(f"Error al obtener las ventas: {e}")
            return jsonify({"msg": "Error al obtener las ventas", "error": str(e)}), 500

@sale_bp.route('/<uuid:sale_id>', methods=["GET", "DELETE"])
@jwt_required()
def sales_single(sale_id):
    # =========================================================
    # LÓGICA DE GET y DELETE individual - SIN CAMBIOS
    # =========================================================
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

            if not check_admin_permission(user_role) and str(sale_user_id) != str(current_user_id):
                return jsonify({"msg": "No autorizado para eliminar esta venta"}), 403

            with get_db_cursor(commit=True) as cur: # Eliminar venta e ítems
                cur.execute("DELETE FROM sale_items WHERE sale_id = %s;", (str(sale_id),))
                cur.execute("DELETE FROM sales WHERE id = %s;", (str(sale_id),))
                deleted_rows = cur.rowcount
            
            if deleted_rows > 0:
                return jsonify({"msg": "Venta y sus items eliminados exitosamente"}), 200
            return jsonify({"msg": "Error al eliminar la venta o venta ya eliminada"}), 500

        except Exception as e:
            print(f"Error al eliminar la venta: {e}")
            return jsonify({"msg": "Error al eliminar la venta", "error": str(e)}), 500