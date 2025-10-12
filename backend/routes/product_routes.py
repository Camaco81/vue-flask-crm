from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
# from db import get_db_cursor <-- Antiguo
from backend.db import get_db_cursor # <-- Nuevo
# from utils.helpers import ... <-- Antiguo
from backend.utils.helpers import get_user_and_role, check_admin_permission, validate_required_fields
product_bp = Blueprint('product', __name__, url_prefix='/api/products')

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
        if not validate_required_fields(data, ['name', 'price', 'stock']):
            return jsonify({"msg": "Missing required fields: name, price, stock"}), 400

        try:
            with get_db_cursor(commit=True) as cur:
                cur.execute(
                    "INSERT INTO products (name, description, price, stock) VALUES (%s, %s, %s, %s) RETURNING id;",
                    (data['name'], data.get('description'), float(data['price']), int(data['stock']))
                )
                new_product_id = cur.fetchone()[0]
            return jsonify({"msg": "Product created successfully", "product_id": new_product_id}), 201
        except Exception as e:
            return jsonify({"msg": "Error creating product", "error": str(e)}), 500

    elif request.method == 'GET':
        # Todos los usuarios autenticados pueden ver la lista de productos
        try:
            with get_db_cursor() as cur:
                cur.execute("SELECT id, name, description, price, stock FROM products ORDER BY name;")
                products = cur.fetchall()
                products_list = [dict(p) for p in products]
            return jsonify(products_list), 200
        except Exception as e:
            return jsonify({"msg": "Error fetching products", "error": str(e)}), 500

@product_bp.route('/<int:product_id>', methods=['GET', 'PUT', 'DELETE'])
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
                cur.execute("SELECT id, name, description, price, stock FROM products WHERE id = %s;", (product_id,))
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
            if key in ['name', 'description', 'price', 'stock']:
                set_clauses.append(f"{key} = %s")
                if key == 'price': params.append(float(value))
                elif key == 'stock': params.append(int(value))
                else: params.append(value)
        
        if not set_clauses:
            return jsonify({"msg": "No valid fields to update"}), 400

        params.append(product_id)
        query = f"UPDATE products SET {', '.join(set_clauses)} WHERE id = %s RETURNING id;"

        try:
            with get_db_cursor(commit=True) as cur:
                cur.execute(query, tuple(params))
                updated_id = cur.fetchone()
            if updated_id:
                return jsonify({"msg": "Product updated successfully", "product_id": updated_id[0]}), 200
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