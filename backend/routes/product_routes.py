from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.db import get_db_cursor
from backend.utils.helpers import get_user_and_role, check_product_manager_permission

product_bp = Blueprint('product', __name__, url_prefix='/api/products')

# --- Helper para convertir fila a diccionario ---
def _fetch_product_details(cur, product_row):
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
        return jsonify({"msg": "Usuario no encontrado"}), 401
    
    # ------------------ POST (Crear Producto) ------------------
    if request.method == 'POST':
        if not check_product_manager_permission(user_role_id):
            return jsonify({"msg": "Acceso denegado"}), 403

        data = request.get_json()
        required_fields = ['name', 'price', 'stock', 'category']
        
        # Validar existencia de campos
        if not data or not all(field in data for field in required_fields):
            return jsonify({"msg": "Faltan campos: name, price, stock o category"}), 400

        try:
            # Limpieza y conversión de datos
            product_name = str(data['name']).strip()
            product_category = str(data['category']).strip()
            product_price = float(data['price'])
            product_stock = int(data['stock'])

            if not product_name or not product_category:
                return jsonify({"msg": "Nombre y categoría no pueden estar vacíos"}), 400
            
            if product_price <= 0 or product_stock < 0:
                return jsonify({"msg": "Precio debe ser > 0 y stock >= 0"}), 400

            with get_db_cursor(commit=True) as cur:
                # CORRECCIÓN: Se agregaron los 4 placeholders (%s) para los 4 campos
                cur.execute(
                    """INSERT INTO products (name, price, stock, category) 
                       VALUES (%s, %s, %s, %s) 
                       RETURNING id, name, price, stock, category;""",
                    (product_name, product_price, product_stock, product_category)
                )
                
                new_product_row = cur.fetchone()
                new_product = _fetch_product_details(cur, new_product_row)
                
            return jsonify(new_product), 201

        except (ValueError, TypeError):
            return jsonify({"msg": "Precio debe ser número y stock un entero"}), 400
        except Exception as e:
            return jsonify({"msg": "Error en el servidor", "error": str(e)}), 500

    # ------------------ GET (Listar Productos) ------------------
    elif request.method == 'GET':
        try:
            with get_db_cursor() as cur:
                cur.execute("SELECT id, name, price, category, stock FROM products ORDER BY name;")
                rows = cur.fetchall()
                # Usamos el helper para cada fila
                products_list = [_fetch_product_details(cur, row) for row in rows]
                
            return jsonify(products_list), 200
        except Exception as e:
            return jsonify({"msg": "Error al obtener productos", "error": str(e)}), 500

# --------------------------------------------------------------------------

@product_bp.route('/<string:product_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def product_single(product_id):
    current_user_id, user_role_id = get_user_and_role()
    if not current_user_id:
        return jsonify({"msg": "No autorizado"}), 401
    
    # ------------------ GET (Producto Único) ------------------
    if request.method == 'GET':
        try:
            with get_db_cursor() as cur:
                cur.execute("SELECT id, name, price, stock, category FROM products WHERE id = %s;", (product_id,))
                row = cur.fetchone()
                product = _fetch_product_details(cur, row)
            
            if product:
                return jsonify(product), 200
            return jsonify({"msg": "Producto no encontrado"}), 404
        except Exception as e:
            return jsonify({"msg": "Error", "error": str(e)}), 500

    # ------------------ PUT (Actualizar Producto) ------------------
    elif request.method == 'PUT':
        if not check_product_manager_permission(user_role_id):
            return jsonify({"msg": "Acceso denegado"}), 403

        data = request.get_json()
        if not data:
            return jsonify({"msg": "No hay datos para actualizar"}), 400
        
        set_clauses = []
        params = []
        
        try:
            # Lista blanca de campos permitidos (incluyendo category)
            allowed_fields = ['name', 'price', 'stock', 'category']
            
            for key in allowed_fields:
                if key in data:
                    val = data[key]
                    if key == 'price':
                        val = float(val)
                        if val <= 0: return jsonify({"msg": "Precio debe ser > 0"}), 400
                    elif key == 'stock':
                        val = int(val)
                        if val < 0: return jsonify({"msg": "Stock no puede ser negativo"}), 400
                    elif key in ['name', 'category']:
                        val = str(val).strip()
                        if not val: return jsonify({"msg": f"{key} no puede estar vacío"}), 400
                    
                    set_clauses.append(f"{key} = %s")
                    params.append(val)
            
            if not set_clauses:
                return jsonify({"msg": "Campos no válidos"}), 400

            params.append(product_id) 
            query = f"UPDATE products SET {', '.join(set_clauses)} WHERE id = %s RETURNING id, name, price, stock, category;"

            with get_db_cursor(commit=True) as cur:
                cur.execute(query, tuple(params))
                updated_row = cur.fetchone()
                updated_product = _fetch_product_details(cur, updated_row)

            if updated_product:
                return jsonify(updated_product), 200
            return jsonify({"msg": "Producto no encontrado"}), 404

        except (ValueError, TypeError):
            return jsonify({"msg": "Formato de datos inválido"}), 400
        except Exception as e:
            return jsonify({"msg": "Error al actualizar", "error": str(e)}), 500

    # ------------------ DELETE (Eliminar Producto) ------------------
    elif request.method == 'DELETE':
        if not check_product_manager_permission(user_role_id):
            return jsonify({"msg": "Acceso denegado"}), 403
            
        try:
            with get_db_cursor(commit=True) as cur:
                cur.execute("DELETE FROM products WHERE id = %s RETURNING id;", (product_id,)) 
                if cur.fetchone():
                    return jsonify({"msg": "Producto eliminado"}), 200
                return jsonify({"msg": "Producto no encontrado"}), 404
        except Exception as e:
            return jsonify({"msg": "Error al eliminar", "error": str(e)}), 500