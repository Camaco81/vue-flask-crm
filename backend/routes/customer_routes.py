from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.db import get_db_cursor
# Importamos las constantes de roles (IDs) y los decoradores de permisos
from backend.utils.helpers import (
    get_user_and_role, 
    validate_required_fields, 
    ADMIN_ROLE_ID, 
    SELLER_ROLE_ID # Importamos el ID de Vendedor
)

customer_bp = Blueprint('customer', __name__, url_prefix='/api/customers')

# Corregimos la lista para usar los ID de rol enteros importados
# ESTO SOLUCIONA EL ERROR DE PERMISOS PARA EL VENDEDOR
CUSTOMER_REGISTRATION_ROLES = [ADMIN_ROLE_ID, SELLER_ROLE_ID] 

# =========================================================
# RUTAS DE COLECCIÓN (/api/customers)
# =========================================================

@customer_bp.route('', methods=['GET', 'POST'])
@jwt_required()
def customers_collection():
    current_user_id, user_role = get_user_and_role()
    
    # 1. Comprobación de Autenticación
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado o token inválido"}), 401

    if request.method == 'POST':
        # 2. Comprobación de Autorización (POST)
        # El user_role (entero) se compara correctamente con la lista de IDs enteros.
        if user_role not in CUSTOMER_REGISTRATION_ROLES:
            return jsonify({"msg": "Acceso denegado: solo administradores y vendedores pueden crear clientes"}), 403

        data = request.get_json()
        
        # 3. Validación de Campos Requeridos
        missing_field = validate_required_fields(data, ['name', 'email', 'cedula'])
        if missing_field:
            if missing_field == "JSON_FORMAT_ERROR":
                 return jsonify({"msg": "Formato JSON inválido."}), 400
            return jsonify({"msg": f"Falta campo requerido: {missing_field}"}), 400

        try:
            with get_db_cursor(commit=True) as cur:
                cur.execute(
                    "INSERT INTO customers (name, email, phone, address, cedula) VALUES (%s, %s, %s, %s, %s) RETURNING id;",
                    (data['name'], data['email'], data.get('phone'), data.get('address'), data['cedula'])
                )
                new_customer_id = cur.fetchone()[0]
            return jsonify({"msg": "Cliente creado exitosamente", "customer_id": str(new_customer_id)}), 201
        
        except Exception as e:
            error_msg = str(e)
            if "duplicate key value violates unique constraint" in error_msg:
                # Manejo de errores de duplicidad más limpios
                if 'email' in error_msg:
                    return jsonify({"msg": "El correo electrónico ya existe"}), 409
                elif 'cedula' in error_msg:
                    return jsonify({"msg": "La cédula ya existe"}), 409
            return jsonify({"msg": "Error creando cliente", "error": error_msg}), 500

    elif request.method == 'GET':
        # Todos los usuarios autenticados pueden ver la lista de clientes
        try:
            with get_db_cursor() as cur:
                cur.execute("SELECT id, name, email, phone, address, cedula FROM customers ORDER BY name;")
                customers = cur.fetchall()
                # Aseguramos que la lista se devuelva correctamente
                customers_list = [dict(c) for c in customers]
            return jsonify(customers_list), 200
        except Exception as e:
            return jsonify({"msg": "Error obteniendo clientes", "error": str(e)}), 500

# =========================================================
# RUTAS DE RECURSO ÚNICO (/api/customers/<id>)
# =========================================================

@customer_bp.route('/<uuid:customer_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def customer_single(customer_id):
    current_user_id, user_role = get_user_and_role()
    
    # 1. Comprobación de Autenticación
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado o token inválido"}), 401
    
    # 2. Comprobación de Autorización (PUT y DELETE solo para Admin)
    if request.method in ['PUT', 'DELETE']:
        # CORRECCIÓN: Compara el role_id directamente con la constante del Admin
        if user_role != ADMIN_ROLE_ID: 
            return jsonify({"msg": "Acceso denegado: solo administradores pueden modificar o eliminar clientes"}), 403

    if request.method == 'GET':
        try:
            with get_db_cursor() as cur:
                cur.execute("SELECT id, name, email, phone, address, cedula FROM customers WHERE id = %s;", (str(customer_id),))
                customer = cur.fetchone()
            if customer:
                return jsonify(dict(customer)), 200
            return jsonify({"msg": "Cliente no encontrado"}), 404
        except Exception as e:
            return jsonify({"msg": "Error obteniendo cliente", "error": str(e)}), 500

    elif request.method == 'PUT':
        data = request.get_json()
        if not data:
            return jsonify({"msg": "No se proporcionaron datos para actualizar"}), 400
        
        set_clauses = []
        params = []
        for key, value in data.items():
            # Validación de campos permitidos para la actualización
            if key in ['name', 'email', 'phone', 'address', 'cedula']:
                set_clauses.append(f"{key} = %s")
                params.append(value)
        
        if not set_clauses:
            return jsonify({"msg": "No hay campos válidos para actualizar"}), 400

        params.append(str(customer_id)) # El ID del cliente (UUID) va al final
        query = f"UPDATE customers SET {', '.join(set_clauses)} WHERE id = %s RETURNING id;"

        try:
            with get_db_cursor(commit=True) as cur:
                cur.execute(query, tuple(params))
                updated_id = cur.fetchone()
            if updated_id:
                return jsonify({"msg": "Cliente actualizado exitosamente", "customer_id": str(updated_id[0])}), 200
            return jsonify({"msg": "Cliente no encontrado o no se realizaron cambios"}), 404
        except Exception as e:
            error_msg = str(e)
            if "duplicate key value violates unique constraint" in error_msg:
                if 'email' in error_msg:
                    return jsonify({"msg": "El correo electrónico ya existe en otro cliente"}), 409
                elif 'cedula' in error_msg:
                    return jsonify({"msg": "La cédula ya existe en otro cliente"}), 409
            return jsonify({"msg": "Error actualizando cliente", "error": error_msg}), 500

    elif request.method == 'DELETE':
        try:
            with get_db_cursor(commit=True) as cur:
                cur.execute("DELETE FROM customers WHERE id = %s RETURNING id;", (str(customer_id),))
                deleted_id = cur.fetchone()
            if deleted_id:
                return jsonify({"msg": "Cliente eliminado exitosamente"}), 200
            return jsonify({"msg": "Cliente no encontrado"}), 404
        except Exception as e:
            return jsonify({"msg": "Error eliminando cliente", "error": str(e)}), 500