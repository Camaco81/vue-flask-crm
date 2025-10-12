from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
# from db import get_db_cursor <-- Antiguo
from backend.db import get_db_cursor # <-- Nuevo
# from utils.helpers import ... <-- Antiguo
from backend.utils.helpers import get_user_and_role, check_admin_permission, validate_required_fields
customer_bp = Blueprint('customer', __name__, url_prefix='/api/customers')

@customer_bp.route('', methods=['GET', 'POST'])
@jwt_required()
def customers_collection():
    current_user_id, user_role = get_user_and_role()
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado o token inválido"}), 401

    if request.method == 'POST':
        if not check_admin_permission(user_role):
            return jsonify({"msg": "Acceso denegado: solo administradores pueden crear clientes"}), 403
        
        data = request.get_json()
        if not validate_required_fields(data, ['name', 'email']):
            return jsonify({"msg": "Missing required fields: name, email"}), 400

        try:
            with get_db_cursor(commit=True) as cur:
                cur.execute(
                    "INSERT INTO customers (name, email, phone, address) VALUES (%s, %s, %s, %s) RETURNING id;",
                    (data['name'], data['email'], data.get('phone'), data.get('address'))
                )
                new_customer_id = cur.fetchone()[0]
            return jsonify({"msg": "Customer created successfully", "customer_id": new_customer_id}), 201
        except Exception as e:
            if "duplicate key value violates unique constraint" in str(e):
                return jsonify({"msg": "Email already exists"}), 409
            return jsonify({"msg": "Error creating customer", "error": str(e)}), 500

    elif request.method == 'GET':
        # Todos los usuarios autenticados pueden ver la lista de clientes
        try:
            with get_db_cursor() as cur:
                cur.execute("SELECT id, name, email, phone, address FROM customers ORDER BY name;")
                customers = cur.fetchall()
                customers_list = [dict(c) for c in customers]
            return jsonify(customers_list), 200
        except Exception as e:
            return jsonify({"msg": "Error fetching customers", "error": str(e)}), 500

@customer_bp.route('/<int:customer_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def customer_single(customer_id):
    current_user_id, user_role = get_user_and_role()
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado o token inválido"}), 401
    
    # PUT y DELETE solo para administradores
    if request.method in ['PUT', 'DELETE'] and not check_admin_permission(user_role):
        return jsonify({"msg": "Acceso denegado: solo administradores pueden modificar o eliminar clientes"}), 403

    if request.method == 'GET':
        try:
            with get_db_cursor() as cur:
                cur.execute("SELECT id, name, email, phone, address FROM customers WHERE id = %s;", (customer_id,))
                customer = cur.fetchone()
            if customer:
                return jsonify(dict(customer)), 200
            return jsonify({"msg": "Customer not found"}), 404
        except Exception as e:
            return jsonify({"msg": "Error fetching customer", "error": str(e)}), 500

    elif request.method == 'PUT':
        data = request.get_json()
        if not data:
            return jsonify({"msg": "No data provided for update"}), 400
        
        # Construir la query de actualización dinámicamente
        set_clauses = []
        params = []
        for key, value in data.items():
            if key in ['name', 'email', 'phone', 'address']: # Campos permitidos para actualizar
                set_clauses.append(f"{key} = %s")
                params.append(value)
        
        if not set_clauses:
            return jsonify({"msg": "No valid fields to update"}), 400

        params.append(customer_id) # El ID del cliente va al final para la cláusula WHERE
        query = f"UPDATE customers SET {', '.join(set_clauses)} WHERE id = %s RETURNING id;"

        try:
            with get_db_cursor(commit=True) as cur:
                cur.execute(query, tuple(params))
                updated_id = cur.fetchone()
            if updated_id:
                return jsonify({"msg": "Customer updated successfully", "customer_id": updated_id[0]}), 200
            return jsonify({"msg": "Customer not found or no changes made"}), 404
        except Exception as e:
            if "duplicate key value violates unique constraint" in str(e):
                return jsonify({"msg": "Email already exists for another customer"}), 409
            return jsonify({"msg": "Error updating customer", "error": str(e)}), 500

    elif request.method == 'DELETE':
        try:
            with get_db_cursor(commit=True) as cur:
                cur.execute("DELETE FROM customers WHERE id = %s RETURNING id;", (customer_id,))
                deleted_id = cur.fetchone()
            if deleted_id:
                return jsonify({"msg": "Customer deleted successfully"}), 200
            return jsonify({"msg": "Customer not found"}), 404
        except Exception as e:
            return jsonify({"msg": "Error deleting customer", "error": str(e)}), 500