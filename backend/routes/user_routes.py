from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from werkzeug.security import generate_password_hash
import uuid

# Helpers y DB
from backend.db import get_db_cursor
from backend.utils.helpers import (
    get_user_and_role, 
    check_admin_permission, 
    validate_required_fields
)

# Constantes de Roles
ALMACENISTA_ROLE_ID = 3 
ADMIN_ROLE_ID = 1
CONSULTOR_ROLE_ID = 2 
ALLOWED_ROLES_FOR_ADMIN = (ADMIN_ROLE_ID, CONSULTOR_ROLE_ID, ALMACENISTA_ROLE_ID)

user_bp = Blueprint('user', __name__, url_prefix='/api')
admin_bp = Blueprint('admin', __name__)

# =========================================================
# HELPER PARA EXTRAER TENANT
# =========================================================
def get_current_tenant():
    """Extrae el tenant_id del token JWT."""
    claims = get_jwt()
    return claims.get('tenant_id', 'default')

# =========================================================
# RUTAS DE PERFIL
# =========================================================

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    current_user_id, _ = get_user_and_role()
    tenant_id = get_current_tenant() # <--- AISLAMIENTO

    try:
        with get_db_cursor() as cur:
            # Filtramos por ID Y por Tenant para asegurar que el usuario 
            # pertenezca a la empresa que dice el token
            cur.execute(
                """
                SELECT u.id, u.email, u.created_at, u.profile_image_url, r.name as role_name, u.role_id, u.tenant_id
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
            
        return jsonify({"msg": "Perfil no encontrado en este tenant"}), 404
    except Exception as e:
        return jsonify({"msg": "Error interno"}), 500

# =========================================================
# GESTIÓN DE USUARIOS (ADMIN)
# =========================================================

@admin_bp.route('/users', methods=['GET']) 
@jwt_required()
def admin_list_users():
    current_user_id, user_role_id = get_user_and_role()
    tenant_id = get_current_tenant() # <--- AISLAMIENTO
    
    if not check_admin_permission(user_role_id):
        return jsonify({"msg": "Acceso denegado"}), 403

    try:
        with get_db_cursor() as cur:
            # IMPORTANTE: El admin solo ve usuarios de SU MISMO tenant
            cur.execute(
                """
                SELECT u.id, u.email, u.role_id, r.name as role_name
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.role_id IN %s AND u.tenant_id = %s
                ORDER BY u.role_id, u.email
                """,
                (ALLOWED_ROLES_FOR_ADMIN, tenant_id)
            )
            users_list = [dict(row) for row in cur.fetchall()]
            for user in users_list: user['id'] = str(user['id'])

            return jsonify(users_list), 200
    except Exception as e:
        return jsonify({"msg": "Error al listar"}), 500

@admin_bp.route('/users', methods=['POST']) 
@jwt_required()
def admin_create_user():
    current_user_id, user_role_id = get_user_and_role()
    tenant_id = get_current_tenant() # <--- AISLAMIENTO
    
    if not check_admin_permission(user_role_id):
        return jsonify({"msg": "Acceso denegado."}), 403

    data = request.get_json()
    # ... validaciones de campos ...

    email = data['email']
    password = generate_password_hash(data['password'])
    role_id = int(data['role_id']) 

    try:
        with get_db_cursor(commit=True) as cur:
            # Al crear el usuario, le inyectamos el tenant_id del administrador
            cur.execute(
                """
                INSERT INTO users (email, password, role_id, tenant_id) 
                VALUES (%s, %s, %s, %s) RETURNING id
                """,
                (email, password, role_id, tenant_id)
            )
            new_user_id = cur.fetchone()['id']
            return jsonify({"msg": "Usuario creado", "id": str(new_user_id)}), 201
            
    except Exception as e:
        if 'unique constraint' in str(e).lower():
            return jsonify({"msg": "El email ya existe en este tenant."}), 409
        return jsonify({"msg": "Error al crear"}), 500

@admin_bp.route('/users/<uuid:user_id>', methods=['DELETE']) 
@jwt_required()
def admin_delete_user(user_id):
    current_user_id, user_role_id = get_user_and_role()
    tenant_id = get_current_tenant() # <--- AISLAMIENTO

    if not check_admin_permission(user_role_id):
        return jsonify({"msg": "Acceso denegado"}), 403

    try:
        user_id_str = str(user_id)
        with get_db_cursor(commit=True) as cur:
            # Agregamos tenant_id al WHERE para evitar que un admin de Empresa A 
            # borre a un usuario de Empresa B mediante fuerza bruta de UUIDs
            cur.execute(
                "DELETE FROM users WHERE id = %s AND tenant_id = %s RETURNING id", 
                (user_id_str, tenant_id)
            )
            if cur.fetchone():
                return jsonify({"msg": "Usuario eliminado"}), 200
            return jsonify({"msg": "Usuario no encontrado en tu tenant"}), 404
    except Exception as e:
        return jsonify({"msg": "Error al eliminar"}), 500