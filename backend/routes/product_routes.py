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
        # Asegura obtener las columnas, necesarias si el cursor no lo hace automáticamente
        columns = [desc[0] for desc in cur.description]
        return dict(zip(columns, product_row))
    return None

# --------------------------------------------------------------------------

@product_bp.route('', methods=['GET', 'POST'])
@jwt_required()
def products_collection():
    # user_role_id ya es un entero (1 o 2)
    current_user_id, user_role_id = get_user_and_role() 
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado o token inválido"}), 401
    
    # ------------------ POST (Crear Producto) ------------------
    if request.method == 'POST':
        # VERIFICACIÓN DE PERMISO
        if not check_product_manager_permission(user_role_id):
            return jsonify({"msg": "Acceso denegado: solo administradores y consultores pueden crear productos"}), 403
        
        data = request.get_json()
        
        # Validar campos requeridos (name, price, stock)
        if not validate_required_fields(data, ['name', 'price', 'stock']):
            return jsonify({"msg": "Missing required fields: name, price, stock"}), 400

        try:
            # Asegurar conversión a los tipos correctos para la base de datos
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
                # Usamos el helper para obtener el diccionario completo
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
                # Se utiliza fetchall_dict para asegurar que el resultado ya sea una lista de diccionarios
                # Si get_db_cursor devuelve un cursor que soporta 'fetchall_dict' (ej: psycopg2.extras.RealDictCursor)
                # Si no, se mantiene la conversión manual de tu código original:
                cur.execute("SELECT id, name, price, stock FROM products ORDER BY name;")
                products = cur.fetchall()
                
                # Conversión manual de filas a diccionarios (según tu código original)
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
    
    # Intenta convertir product_id a entero para validación y uso en SQL
    try:
        product_id_int = int(product_id)
    except ValueError:
        return jsonify({"msg": "Invalid product ID format."}), 400

    # ------------------ GET (Producto Único) ------------------
    if request.method == 'GET':
        try:
            with get_db_cursor() as cur:
                cur.execute("SELECT id, name, price, stock FROM products WHERE id = %s;", (product_id_int,))
                product = cur.fetchone()
            if product:
                # Usamos dict(product) para retornar el formato JSON correcto
                return jsonify(dict(product)), 200
            return jsonify({"msg": "Product not found"}), 404
        except Exception as e:
            return jsonify({"msg": "Error fetching product", "error": str(e)}), 500

    # ------------------ PUT (Actualizar Producto) ------------------
    elif request.method == 'PUT':
        # VERIFICACIÓN DE PERMISO
        if not check_product_manager_permission(user_role_id):
            return jsonify({"msg": "Acceso denegado: solo administradores y consultores pueden modificar o eliminar productos"}), 403

        data = request.get_json()
        if not data:
            return jsonify({"msg": "No data provided for update"}), 400
        
        set_clauses = []
        params = []
        
        # Iterar sobre los datos recibidos y construir la query de actualización
        try:
            for key, value in data.items():
                if key in ['name', 'price', 'stock']:
                    set_clauses.append(f"{key} = %s")
                    
                    # CORRECCIÓN CLAVE: Asegurar la conversión de tipos con manejo de excepciones
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

        params.append(product_id_int) # Usar la versión entera del ID
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
        # VERIFICACIÓN DE PERMISO
        if not check_product_manager_permission(user_role_id):
            return jsonify({"msg": "Acceso denegado: solo administradores y consultores pueden modificar o eliminar productos"}), 403
            
        try:
            with get_db_cursor(commit=True) as cur:
                cur.execute("DELETE FROM products WHERE id = %s RETURNING id;", (product_id_int,)) # Usar el ID entero
                deleted_id = cur.fetchone()
            if deleted_id:
                return jsonify({"msg": "Product deleted successfully"}), 200
            return jsonify({"msg": "Product not found"}), 404
        except Exception as e:
            return jsonify({"msg": "Error deleting product", "error": str(e)}), 500