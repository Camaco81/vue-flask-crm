from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.db import get_db_cursor
from backend.utils.helpers import get_user_and_role, check_admin_permission, validate_required_fields

product_bp = Blueprint('product', __name__, url_prefix='/api/products')

# --- Helper para obtener el producto completo después de INSERT/UPDATE ---
def _fetch_product_details(cur, product_row):
    """
    Convierte la fila de la base de datos (después de RETURNING *) a un diccionario.
    Asume que el cursor ha ejecutado una sentencia RETURNING.
    """
    if product_row:
        # Obtiene los nombres de las columnas del cursor
        columns = [desc[0] for desc in cur.description]
        return dict(zip(columns, product_row))
    return None

# --------------------------------------------------------------------------

@product_bp.route('', methods=['GET', 'POST'])
@jwt_required()
def products_collection():
    current_user_id, user_role = get_user_and_role()
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado o token inválido"}), 401

    if request.method == 'POST':
        if not check_admin_permission(user_role):
            return jsonify({"msg": "Acceso denegado: solo administradores pueden crear productos"}), 403
        
        data = request.get_json()
        
        # Validación de campos requeridos (incluyendo 'stock')
        if not validate_required_fields(data, ['name', 'price', 'stock']):
            return jsonify({"msg": "Missing required fields: name, price, stock"}), 400

        try:
            with get_db_cursor(commit=True) as cur:
                # Modificado: Usar 'RETURNING id, name, price, stock' para obtener el objeto completo
                cur.execute(
                    "INSERT INTO products (name, price, stock) VALUES (%s, %s, %s) RETURNING id, name, price, stock;",
                    (data['name'], float(data['price']), int(data['stock']))
                )
                
                # Recuperar y formatear el producto insertado
                new_product_row = cur.fetchone()
                new_product = _fetch_product_details(cur, new_product_row)
            
            if new_product:
                # Retorna el objeto completo del producto creado (incluye stock)
                return jsonify(new_product), 201
            else:
                return jsonify({"msg": "Product creation failed to return data"}), 500

        except Exception as e:
            return jsonify({"msg": "Error creating product", "error": str(e)}), 500

    elif request.method == 'GET':
        # Todos los usuarios autenticados pueden ver la lista de productos
        try:
            with get_db_cursor() as cur:
                # Asegura que 'stock' se incluye en la consulta
                cur.execute("SELECT id, name, price, stock FROM products ORDER BY name;")
                products = cur.fetchall()
                # Se asume que get_db_cursor usa RealDictCursor o se convierte a dict en el frontend
                products_list = [dict(p) for p in products] 
            return jsonify(products_list), 200
        except Exception as e:
            return jsonify({"msg": "Error fetching products", "error": str(e)}), 500

@product_bp.route('/<string:product_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def product_single(product_id):
    current_user_id, user_role = get_user_and_role()
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado o token inválido"}), 401

    # PUT y DELETE solo para administradores
    if request.method in ['PUT', 'DELETE'] and not check_admin_permission(user_role):
        return jsonify({"msg": "Acceso denegado: solo administradores pueden modificar o eliminar productos"}), 403

    if request.method == 'GET':
        try:
            with get_db_cursor() as cur:
                # Asegura que 'stock' se incluye en la consulta
                cur.execute("SELECT id, name, price, stock FROM products WHERE id = %s;", (product_id,))
                product = cur.fetchone()
            if product:
                return jsonify(dict(product)), 200
            return jsonify({"msg": "Product not found"}), 404
        except Exception as e:
            return jsonify({"msg": "Error fetching product", "error": str(e)}), 500

    elif request.method == 'PUT':
        data = request.get_json()
        if not data:
            return jsonify({"msg": "No data provided for update"}), 400
        
        set_clauses = []
        params = []
        
        # Itera sobre los campos y prepara la consulta
        for key, value in data.items():
            if key in ['name', 'price', 'stock']:
                set_clauses.append(f"{key} = %s")
                # Asegura el tipo correcto para la base de datos
                if key == 'price': params.append(float(value))
                elif key == 'stock': params.append(int(value))
                else: params.append(value)
        
        if not set_clauses:
            return jsonify({"msg": "No valid fields to update"}), 400

        params.append(product_id)
        # Modificado: Usar 'RETURNING id, name, price, stock' para obtener el objeto actualizado
        query = f"UPDATE products SET {', '.join(set_clauses)} WHERE id = %s RETURNING id, name, price, stock;"

        try:
            with get_db_cursor(commit=True) as cur:
                cur.execute(query, tuple(params))
                # Recuperar y formatear el producto actualizado
                updated_product_row = cur.fetchone()
                updated_product = _fetch_product_details(cur, updated_product_row)

            if updated_product:
                # Retorna el objeto completo del producto actualizado (incluye stock)
                return jsonify(updated_product), 200
            return jsonify({"msg": "Product not found or no changes made"}), 404
        except Exception as e:
            return jsonify({"msg": "Error updating product", "error": str(e)}), 500

    elif request.method == 'DELETE':
        try:
            with get_db_cursor(commit=True) as cur:
                cur.execute("DELETE FROM products WHERE id = %s RETURNING id;", (product_id,))
                deleted_id = cur.fetchone()
            if deleted_id:
                return jsonify({"msg": "Product deleted successfully"}), 200
            return jsonify({"msg": "Product not found"}), 404
        except Exception as e:
            return jsonify({"msg": "Error deleting product", "error": str(e)}), 500