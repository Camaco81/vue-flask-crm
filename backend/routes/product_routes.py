from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.db import get_db_cursor
# Importar ahora la versión de helper ajustada (que usa IDs de rol)
from backend.utils.helpers import get_user_and_role, check_product_manager_permission, validate_required_fields 

product_bp = Blueprint('product', __name__, url_prefix='/api/products')

# --- Helper para obtener el producto completo después de INSERT/UPDATE ---
def _fetch_product_details(cur, product_row):
    """
    Convierte la fila de la base de datos (después de RETURNING *) a un diccionario.
    """
    if product_row:
        columns = [desc[0] for desc in cur.description]
        return dict(zip(columns, product_row))
    return None

# Nota: check_product_manager_permission ahora se importa desde helpers.py
# y espera el role_id (entero), así que se elimina la función local.

# --------------------------------------------------------------------------

@product_bp.route('', methods=['GET', 'POST'])
@jwt_required()
def products_collection():
    # user_role ahora es user_role_id (entero 1 o 2)
    current_user_id, user_role_id = get_user_and_role() 
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado o token inválido"}), 401
    
    # *** CORRECCIÓN CLAVE: Se ELIMINA la lógica de conversión de cadenas fallida ***
    # La variable user_role_id ya es un entero (1 o 2)
    
    if request.method == 'POST':
        # VERIFICACIÓN DE PERMISO (Usa el ID entero)
        if not check_product_manager_permission(user_role_id):
            return jsonify({"msg": "Acceso denegado: solo administradores y consultores pueden crear productos"}), 403
        
        data = request.get_json()
        
        # NOTE: validate_required_fields fue ajustado en helpers.py para corregir un bug de retorno
        if not validate_required_fields(data, ['name', 'price', 'stock']):
            return jsonify({"msg": "Missing required fields: name, price, stock"}), 400

        try:
            with get_db_cursor(commit=True) as cur:
                cur.execute(
                    "INSERT INTO products (name, price, stock) VALUES (%s, %s, %s) RETURNING id, name, price, stock;",
                    (data['name'], float(data['price']), int(data['stock']))
                )
                
                new_product_row = cur.fetchone()
                new_product = _fetch_product_details(cur, new_product_row)
                
            if new_product:
                return jsonify(new_product), 201
            else:
                return jsonify({"msg": "Product creation failed to return data"}), 500

        except Exception as e:
            return jsonify({"msg": "Error creating product. Check data types for price and stock.", "error": str(e)}), 500

    elif request.method == 'GET':
        try:
            with get_db_cursor() as cur:
                cur.execute("SELECT id, name, price, stock FROM products ORDER BY name;")
                products = cur.fetchall()
                products_list = [dict(p) for p in products]  
            return jsonify(products_list), 200
        except Exception as e:
            return jsonify({"msg": "Error fetching products", "error": str(e)}), 500

# --------------------------------------------------------------------------

@product_bp.route('/<string:product_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def product_single(product_id):
    # user_role ahora es user_role_id (entero 1 o 2)
    current_user_id, user_role_id = get_user_and_role()
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado o token inválido"}), 401
    
    # *** CORRECCIÓN CLAVE: Se ELIMINA la lógica de conversión de cadenas fallida ***
    # La variable user_role_id ya es un entero (1 o 2)

    # VERIFICACIÓN DE PERMISO (Usa el ID entero)
    if request.method in ['PUT', 'DELETE'] and not check_product_manager_permission(user_role_id):
        return jsonify({"msg": "Acceso denegado: solo administradores y consultores pueden modificar o eliminar productos"}), 403

    if request.method == 'GET':
        try:
            with get_db_cursor() as cur:
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
        
        for key, value in data.items():
            if key in ['name', 'price', 'stock']:
                set_clauses.append(f"{key} = %s")
                # Asegura la conversión de tipos
                if key == 'price': params.append(float(value))
                elif key == 'stock': params.append(int(value))
                else: params.append(value)
        
        if not set_clauses:
            return jsonify({"msg": "No valid fields to update"}), 400

        params.append(product_id)
        query = f"UPDATE products SET {', '.join(set_clauses)} WHERE id = %s RETURNING id, name, price, stock;"

        try:
            with get_db_cursor(commit=True) as cur:
                cur.execute(query, tuple(params))
                updated_product_row = cur.fetchone()
                updated_product = _fetch_product_details(cur, updated_product_row)

            if updated_product:
                return jsonify(updated_product), 200
            return jsonify({"msg": "Product not found or no changes made"}), 404
        except Exception as e:
            return jsonify({"msg": "Error updating product. Check data types for price and stock.", "error": str(e)}), 500

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