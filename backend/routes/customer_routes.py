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
    return get_jwt().get('tenant_id', 'default-tenant')

@customer_bp.route('', methods=['GET', 'POST'])
@jwt_required()
def customers_collection():
    current_user_id, user_role = get_user_and_role()
    tenant_id = get_current_tenant()
    
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado"}), 401

    # ------------------ POST (Crear Cliente) ------------------
    if request.method == 'POST':
        # Nota: Puedes decidir si solo Admin o también Vendedores crean clientes
        if not check_admin_permission(user_role):
            return jsonify({"msg": "Acceso denegado: solo administradores"}), 403
        
        data = request.get_json()
        if error := validate_required_fields(data, ['name', 'email', 'cedula']):
            return jsonify({"msg": f"Campos faltantes: {error}"}), 400

        try:
            # Valores por defecto para nuevos clientes
            credit_limit = float(data.get('credit_limit_usd', 500.0))
            
            with get_db_cursor(commit=True) as cur:
                cur.execute(
                    """INSERT INTO customers (name, email, phone, address, cedula, tenant_id, credit_limit_usd, balance_pendiente_usd) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, 0) 
                       RETURNING id;""",
                    (data['name'], data['email'], data.get('phone'), data.get('address'), 
                     data['cedula'], tenant_id, credit_limit)
                )
                new_id = cur.fetchone()[0]
                
            return jsonify({"msg": "Cliente creado", "id": new_id}), 201

        except Exception as e:
            error_msg = str(e)
            if "unique constraint" in error_msg.lower():
                field = "Cédula" if "cedula" in error_msg.lower() else "Email"
                return jsonify({"msg": f"Ese {field} ya está registrado en su empresa"}), 409
            app_logger.error(f"Error cliente: {e}")
            return jsonify({"msg": "Error al crear cliente"}), 500

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
            return jsonify({"msg": "Error al obtener clientes"}), 500

@customer_bp.route('/<int:customer_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def customer_single(customer_id):
    current_user_id, user_role = get_user_and_role()
    tenant_id = get_current_tenant()

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
        if not check_admin_permission(user_role):
            return jsonify({"msg": "Acceso denegado"}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"msg": "Sin datos"}), 400
        
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
        query = f"UPDATE customers SET {', '.join(updates)} WHERE id = %s AND tenant_id = %s RETURNING id;"

        try:
            with get_db_cursor(commit=True) as cur:
                cur.execute(query, tuple(params))
                if cur.fetchone():
                    return jsonify({"msg": "Actualizado correctamente"}), 200
                return jsonify({"msg": "No encontrado"}), 404
        except Exception as e:
            if "unique constraint" in str(e).lower():
                return jsonify({"msg": "Email o Cédula duplicados"}), 409
            return jsonify({"msg": "Error al actualizar"}), 500

    # ------------------ DELETE (Eliminar Cliente) ------------------
    elif request.method == 'DELETE':
        if not check_admin_permission(user_role):
            return jsonify({"msg": "Solo administradores pueden eliminar"}), 403
        try:
            with get_db_cursor(commit=True) as cur:
                # Opcional: Verificar si tiene ventas antes de eliminar
                cur.execute("DELETE FROM customers WHERE id = %s AND tenant_id = %s RETURNING id;", (customer_id, tenant_id))
                return jsonify({"msg": "Eliminado"}), 200 if cur.fetchone() else (jsonify({"msg": "No encontrado"}), 404)
        except Exception as e:
            return jsonify({"msg": "No se puede eliminar: el cliente tiene historial de ventas"}), 400