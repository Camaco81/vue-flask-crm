from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from werkzeug.security import generate_password_hash
import uuid

# Helpers y DB
from backend.db import get_db_cursor
from backend.utils.helpers import (
    get_user_and_role, 
    check_admin_permission
)

# Constantes de Roles
ALMACENISTA_ROLE_ID = 3 
ADMIN_ROLE_ID = 1
CONSULTOR_ROLE_ID = 2 
ALLOWED_ROLES_FOR_ADMIN = (ADMIN_ROLE_ID, CONSULTOR_ROLE_ID, ALMACENISTA_ROLE_ID)

admin_bp = Blueprint('admin', __name__)

def get_current_tenant():
    """Extrae el tenant_id del token JWT del Admin logueado."""
    claims = get_jwt()
    return claims.get('tenant_id', 'default')

# =========================================================
# LISTADO DE EMPLEADOS (Filtrado por Empresa)
# =========================================================
@admin_bp.route('/users', methods=['GET']) 
@jwt_required()
def admin_list_users():
    current_user_id, user_role_id = get_user_and_role()
    tenant_id = get_current_tenant()
    
    if not check_admin_permission(user_role_id):
        return jsonify({"msg": "Acceso denegado"}), 403

    try:
        with get_db_cursor() as cur:
            # Traemos nombre y cedula también para mostrarlos en la tabla
            cur.execute(
                """
                SELECT u.id, u.email, u.nombre, u.cedula, u.role_id, r.name as role_name
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.tenant_id = %s
                ORDER BY u.role_id, u.nombre
                """,
                (tenant_id,)
            )
            users_list = [dict(row) for row in cur.fetchall()]
            for user in users_list: 
                user['id'] = str(user['id'])

            return jsonify(users_list), 200
    except Exception as e:
        return jsonify({"msg": "Error al listar empleados"}), 500

# =========================================================
# CREACIÓN DE EMPLEADOS (Heredando el Tenant)
# =========================================================
@admin_bp.route('/users', methods=['POST']) 
@jwt_required()
def admin_create_user():
    current_user_id, user_role_id = get_user_and_role()
    tenant_id = get_current_tenant() # <--- La jefa (admin) le da su ID de empresa
    
    if not check_admin_permission(user_role_id):
        return jsonify({"msg": "Acceso denegado."}), 403

    data = request.get_json()
    
    # Validamos que vengan los campos nuevos
    nombre = data.get('nombre')
    cedula = data.get('cedula')
    email = data.get('email')
    password_raw = data.get('password')
    role_id = data.get('role_id')

    if not all([nombre, cedula, email, password_raw, role_id]):
        return jsonify({"msg": "Faltan campos obligatorios (nombre, cedula, email, password, role_id)"}), 400

    password_hash = generate_password_hash(password_raw)

    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO users (nombre, cedula, email, password, role_id, tenant_id) 
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                """,
                (nombre, cedula, email, password_hash, int(role_id), tenant_id)
            )
            new_user_id = cur.fetchone()['id']
            return jsonify({
                "msg": "Empleado registrado con éxito", 
                "id": str(new_user_id),
                "empresa_asignada": tenant_id
            }), 201
            
    except Exception as e:
        if 'unique constraint' in str(e).lower():
            return jsonify({"msg": "El email o la cédula ya existen."}), 409
        return jsonify({"msg": f"Error al crear: {str(e)}"}), 500

# =========================================================
# ELIMINACIÓN SEGURA
# =========================================================
@admin_bp.route('/users/<uuid:user_id>', methods=['DELETE']) 
@jwt_required()
def admin_delete_user(user_id):
    current_user_id, user_role_id = get_user_and_role()
    tenant_id = get_current_tenant()

    if not check_admin_permission(user_role_id):
        return jsonify({"msg": "Acceso denegado"}), 403

    try:
        with get_db_cursor(commit=True) as cur:
            # Solo permite borrar si el usuario pertenece al mismo tenant del admin
            cur.execute(
                "DELETE FROM users WHERE id = %s AND tenant_id = %s RETURNING id", 
                (str(user_id), tenant_id)
            )
            if cur.fetchone():
                return jsonify({"msg": "Empleado eliminado"}), 200
            return jsonify({"msg": "No se encontró el empleado o no pertenece a tu empresa"}), 404
    except Exception as e:
        return jsonify({"msg": "Error al eliminar"}), 500