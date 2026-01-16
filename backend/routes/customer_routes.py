from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from backend.db import get_db_cursor
from backend.utils.helpers import (
    get_user_and_role, 
    check_admin_permission, 
    validate_required_fields
)
import logging

customer_bp = Blueprint('customer', __name__, url_prefix='/api/customers')
app_logger = logging.getLogger('backend.routes.customer_routes')

def get_current_tenant():
    """Extrae el tenant_id del token JWT."""
    # Como buena práctica, asegúrate de que el token siempre lo tenga
    return get_jwt().get('tenant_id')

@customer_bp.route('', methods=['GET', 'POST'])
@jwt_required()
def customers_collection():
    current_user_id, user_role = get_user_and_role()
    tenant_id = get_current_tenant()
    
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado"}), 401

    # ------------------ POST (Crear Cliente) ------------------
    if request.method == 'POST':
        # AJUSTE: Permitimos que Vendedores TAMBIÉN creen clientes.
        # Es vital para la operatividad del negocio.
        data = request.get_json()
        if error := validate_required_fields(data, ['name', 'email', 'cedula']):
            return jsonify({"msg": f"Campos faltantes: {error}"}), 400

        try:
            # Lógica multitenant: El tenant_id viene del JWT, no del request del cliente (seguridad)
            credit_limit = float(data.get('credit_limit_usd', 500.0))
            
            with get_db_cursor(commit=True) as cur:
                cur.execute(
                    """INSERT INTO customers (name, email, phone, address, cedula, tenant_id, credit_limit_usd, balance_pendiente_usd) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, 0) 
                       RETURNING id, name, email, phone, address, cedula, credit_limit_usd, balance_pendiente_usd;""",
                    (data['name'], data['email'], data.get('phone'), data.get('address'), 
                     data['cedula'], tenant_id, credit_limit)
                )
                new_customer = cur.fetchone()
                
            # Devolvemos el objeto completo para que Vue lo agregue a la lista inmediatamente
            return jsonify(dict(new_customer)), 201

        except Exception as e:
            error_msg = str(e)
            if "unique constraint" in error_msg.lower():
                field = "Cédula" if "cedula" in error_msg.lower() else "Email"
                return jsonify({"msg": f"Ese {field} ya está registrado en su empresa"}), 409
            app_logger.error(f"Error al crear cliente: {e}")
            return jsonify({"msg": "Error interno al crear cliente"}), 500

    # ------------------ GET (Listar Clientes del Tenant) ------------------
    elif request.method == 'GET':
        try:
            with get_db_cursor() as cur:
                cur.execute(
                    """SELECT id, name, email, phone, address, cedula, credit_limit_usd, balance_pendiente_usd 
                       FROM customers WHERE tenant_id = %s ORDER BY name;""",
                    (tenant_id,)
                )
                return jsonify([dict(c) for c in cur.fetchall()]), 200
        except Exception as e:
            app_logger.error(f"Error fetch clientes: {e}")
            return jsonify({"msg": "Error al obtener clientes"}), 500

@customer_bp.route('/<uuid:customer_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def customer_single(customer_id):
    current_user_id, user_role = get_user_and_role()
    tenant_id = get_current_tenant()

    # ------------------ GET SINGLE ------------------
    if request.method == 'GET':
        try:
            with get_db_cursor() as cur:
                cur.execute(
                    "SELECT * FROM customers WHERE id = %s AND tenant_id = %s;", 
                    (customer_id, tenant_id)
                )
                customer = cur.fetchone()
            return jsonify(dict(customer)) if customer else (jsonify({"msg": "No encontrado"}), 404)
        except Exception as e:
            return jsonify({"msg": "Error"}), 500

    # ------------------ PUT (Actualizar Cliente) ------------------
    elif request.method == 'PUT':
        # Permitimos actualizar a Admin y Vendedores (o solo admin según tu regla de negocio)
        data = request.get_json()
        allowed_fields = ['name', 'email', 'phone', 'address', 'cedula', 'credit_limit_usd']
        updates = []
        params = []
        
        for key in allowed_fields:
            if key in data:
                updates.append(f"{key} = %s")
                params.append(data[key])
        
        if not updates:
            return jsonify({"msg": "Nada que actualizar"}), 400

        params.extend([customer_id, tenant_id])
        # RETURNING es clave para sincronizar el frontend
        query = f"""UPDATE customers SET {', '.join(updates)} 
                    WHERE id = %s AND tenant_id = %s 
                    RETURNING id, name, email, phone, address, cedula, credit_limit_usd, balance_pendiente_usd;"""

        try:
            with get_db_cursor(commit=True) as cur:
                cur.execute(query, tuple(params))
                updated_customer = cur.fetchone()
                if updated_customer:
                    return jsonify(dict(updated_customer)), 200
                return jsonify({"msg": "Cliente no encontrado o no pertenece a su tenant"}), 404
        except Exception as e:
            if "unique constraint" in str(e).lower():
                return jsonify({"msg": "Email o Cédula ya existen en otro registro"}), 409
            return jsonify({"msg": "Error al actualizar"}), 500

    # ------------------ DELETE (Eliminar Cliente) ------------------
    elif request.method == 'DELETE':
        # Mantenemos la restricción: Solo administradores borran.
        if not check_admin_permission(user_role):
            return jsonify({"msg": "Solo administradores pueden eliminar registros"}), 403
        try:
            with get_db_cursor(commit=True) as cur:
                # El tenant_id en el WHERE garantiza que no borren datos de otra empresa
                cur.execute("DELETE FROM customers WHERE id = %s AND tenant_id = %s RETURNING id;", (customer_id, tenant_id))
                if cur.fetchone():
                    return jsonify({"msg": "Eliminado"}), 200
                return jsonify({"msg": "No encontrado"}), 404
        except Exception as e:
            # Captura de error de llave foránea si el cliente tiene facturas
            return jsonify({"msg": "Integridad referencial: El cliente tiene historial y no puede ser borrado"}), 400