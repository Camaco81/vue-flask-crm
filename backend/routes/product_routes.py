from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.db import get_db_cursor
# Importar ahora la versión de helper ajustada (que usa IDs de rol)
from backend.utils.helpers import get_user_and_role, check_product_manager_permission, validate_required_fields
product_bp = Blueprint('product', __name__, url_prefix='/api/products')

# --- Helper para obtener el producto completo después de INSERT/UPDATE/SELECT ---
def _fetch_product_details(cur, product_row):
    """
    Convierte la fila de la base de datos (después de RETURNING * o SELECT) a un diccionario.
    """
    if product_row:
        columns = [desc[0] for desc in cur.description]
        return dict(zip(columns, product_row))
    return None

# --------------------------------------------------------------------------

@product_bp.route('', methods=['GET', 'POST'])
@jwt_required()
def products_collection():
    current_user_id, user_role_id = get_user_and_role() 
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado o token inválido"}), 401
    
    # ------------------ POST (Crear Producto) ------------------
    if request.method == 'POST':
        # VERIFICACIÓN DE PERMISO (Ahora incluye el ID 3: Almacenista)
        if not check_product_manager_permission(user_role_id):
            return jsonify({"msg": "Acceso denegado: solo administradores, consultores y almacenistas pueden crear productos"}), 403
        
        data = request.get_json()
        
        if not validate_required_fields(data, ['name', 'price', 'stock']):
            return jsonify({"msg": "Missing required fields: name, price, stock"}), 400

        try:
            product_name = data['name'].strip()
            product_price = float(data['price'])
            product_stock = int(data['stock'])
            
            if product_price <= 0 or product_stock < 0:
                 return jsonify({"msg": "Price must be positive and Stock non-negative."}), 400

            with get_db_cursor(commit=True) as cur:
                cur.execute(
                    "INSERT INTO products (name, price, stock) VALUES (%s, %s, %s) RETURNING id, name, price, stock;",
                    (product_name, product_price, product_stock)
                )
                
                new_product_row = cur.fetchone()
                new_product = _fetch_product_details(cur, new_product_row)
                
            if new_product:
                return jsonify(new_product), 201
            else:
                return jsonify({"msg": "Product creation failed to return data"}), 500

        except (ValueError, TypeError):
             return jsonify({"msg": "Invalid data type for price or stock. Price must be a number (decimal allowed) and stock must be an integer."}), 400
        except Exception as e:
            return jsonify({"msg": "Error creating product.", "error": str(e)}), 500

    # ------------------ GET (Listar Productos) ------------------
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
    current_user_id, user_role_id = get_user_and_role()
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado o token inválido"}), 401
    
    # El product_id (el UUID) se usa directamente.

    # VERIFICACIÓN DE PERMISO (Ahora incluye el ID 3: Almacenista)
    if request.method in ['PUT', 'DELETE'] and not check_product_manager_permission(user_role_id):
        return jsonify({"msg": "Acceso denegado: solo administradores, consultores y almacenistas pueden modificar o eliminar productos"}), 403

    # ------------------ GET (Producto Único) ------------------
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

    # ------------------ PUT (Actualizar Producto) ------------------
    elif request.method == 'PUT':
        data = request.get_json()
        if not data:
            return jsonify({"msg": "No data provided for update"}), 400
        
        set_clauses = []
        params = []
        
        try:
            for key, value in data.items():
                if key in ['name', 'price', 'stock']:
                    set_clauses.append(f"{key} = %s")
                    
                    if key == 'price': 
                        product_price = float(value)
                        if product_price <= 0:
                            return jsonify({"msg": "Price must be positive."}), 400
                        params.append(product_price)
                        
                    elif key == 'stock': 
                        product_stock = int(value)
                        if product_stock < 0:
                            return jsonify({"msg": "Stock cannot be negative."}), 400
                        params.append(product_stock)
                        
                    else: 
                        params.append(value.strip())
            
        except (ValueError, TypeError):
            return jsonify({"msg": "Invalid data type for price or stock during update. Price must be a number (decimal allowed) and stock must be an integer."}), 400
                
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
            return jsonify({"msg": "Error updating product.", "error": str(e)}), 500

    # ------------------ DELETE (Eliminar Producto) ------------------
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