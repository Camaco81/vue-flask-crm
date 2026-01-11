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

# Definición de Blueprints
user_bp = Blueprint('user', __name__) 
admin_bp = Blueprint('admin', __name__)

def get_current_tenant():
    """Extrae el tenant_id del token JWT del Admin logueado."""
    claims = get_jwt()
    return claims.get('tenant_id', 'default')

# =========================================================
# RUTAS DE USUARIO (user_bp)
# =========================================================

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    # AJUSTE: Usamos "_" para ignorar los valores adicionales que devuelve la función
    current_user_id, user_role_id, *_ = get_user_and_role()
    tenant_id = get_current_tenant()

    try:
        with get_db_cursor() as cur:
            cur.execute(
                """
                SELECT u.id, u.email, u.nombre, u.cedula, u.created_at, u.profile_image_url, r.name as role_name, u.role_id
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.id = %s AND u.tenant_id = %s
                """, 
                (current_user_id, tenant_id)
            )
            user_data = cur.fetchone()

        if user_data:
            profile = dict(user_data)
            profile['id'] = str(profile['id'])
            return jsonify(profile), 200
            
        return jsonify({"msg": "Perfil no encontrado"}), 404
    except Exception as e:
        return jsonify({"msg": "Error interno"}), 500

# =========================================================
# GESTIÓN DE EMPLEADOS (admin_bp)
# =========================================================

@admin_bp.route('/users', methods=['GET']) 
@jwt_required()
def admin_list_users():
    # AJUSTE: Se añade el desempaquetado extendido (*_) para evitar el ValueError
    current_user_id, user_role_id, *_ = get_user_and_role()
    tenant_id = get_current_tenant()
    
    if not check_admin_permission(user_role_id):
        return jsonify({"msg": "Acceso denegado"}), 403

    try:
        with get_db_cursor() as cur:
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
            for user in users_list: user['id'] = str(user['id'])
            return jsonify(users_list), 200
    except Exception as e:
        return jsonify({"msg": "Error al listar"}), 500

@admin_bp.route('/users', methods=['POST']) 
@jwt_required()
def admin_create_user():
    # AJUSTE: Se aplica la corrección aquí también
    current_user_id, user_role_id, *_ = get_user_and_role()
    tenant_id = get_current_tenant()
    
    if not check_admin_permission(user_role_id):
        return jsonify({"msg": "Acceso denegado."}), 403

    data = request.get_json()
    nombre = data.get('nombre')
    cedula = data.get('cedula') # Campo importante en tu DB 📇
    email = data.get('email')
    password_raw = data.get('password')
    role_id = data.get('role_id')

    if not all([nombre, cedula, email, password_raw, role_id]):
        return jsonify({"msg": "Faltan campos obligatorios"}), 400

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
            return jsonify({"msg": "Empleado creado", "id": str(new_user_id)}), 201
    except Exception as e:
        if 'unique constraint' in str(e).lower():
            return jsonify({"msg": "Email o cédula ya registrados."}), 409
        return jsonify({"msg": "Error al crear"}), 500

@admin_bp.route('/users/<uuid:user_id>', methods=['DELETE']) 
@jwt_required()
def admin_delete_user(user_id):
    # AJUSTE: Corrección final para mantener consistencia
    current_user_id, user_role_id, *_ = get_user_and_role()
    tenant_id = get_current_tenant()

    if not check_admin_permission(user_role_id):
        return jsonify({"msg": "Acceso denegado"}), 403

    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM users WHERE id = %s AND tenant_id = %s RETURNING id", 
                (str(user_id), tenant_id)
            )
            if cur.fetchone():
                return jsonify({"msg": "Usuario eliminado"}), 200
            return jsonify({"msg": "Usuario no encontrado"}), 404
    except Exception as e:
        return jsonify({"msg": "Error al eliminar"}), 500