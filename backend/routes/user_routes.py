from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from werkzeug.security import generate_password_hash
# Importación del módulo UUID de Python para manipulación
import uuid

# 1. Importaciones de Helpers y DB
from backend.db import get_db_cursor
from backend.utils.helpers import (
    get_user_and_role, 
    check_admin_permission, 
    validate_required_fields, 
    ADMIN_ROLE_ID, 
    SELLER_ROLE_ID, 
    CUSTOMER_ROLE_ID # Si lo usas
)
# Constantes de Roles (Asegurando la definición)
ALMACENISTA_ROLE_ID = 3 
ADMIN_ROLE_ID = 1
CONSULTOR_ROLE_ID = 2 # Role 2 es el Vendedor
VISITOR_ROLE_ID = 4 
# Roles permitidos para gestión por el Administrador (1, 2, 3)
ALLOWED_ROLES_FOR_ADMIN = (ADMIN_ROLE_ID, CONSULTOR_ROLE_ID, ALMACENISTA_ROLE_ID,VISITOR_ROLE_ID)


# 2. Importaciones de Cloudinary
from backend.utils.cloudinary_handler import upload_profile_image, delete_profile_image 

# =========================================================
# Blueprints
# =========================================================

user_bp = Blueprint('user', __name__, url_prefix='/api')
admin_bp = Blueprint('admin', __name__)

# =========================================================
# RUTAS DE PERFIL DE USUARIO (Acceso General: /api/profile/*)
# =========================================================

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    """Obtiene la información básica del perfil del usuario autenticado."""
    current_user_id, _ = get_user_and_role()
    if not current_user_id:
        return jsonify({"msg": "Usuario no autenticado o token inválido"}), 401

    try:
        with get_db_cursor() as cur:
            # Consulta para obtener el perfil del usuario autenticado
            cur.execute(
                """
                SELECT u.id, u.email, u.created_at, u.profile_image_url, r.name as role_name, u.role_id
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.id = %s
                """, 
                (current_user_id,)
            )
            user_data = cur.fetchone()

        if user_data:
            profile = dict(user_data)
            profile['id'] = str(profile['id'])
            profile.pop('password', None)
            
            return jsonify(profile), 200
            
        return jsonify({"msg": "Perfil de usuario no encontrado"}), 404

    except Exception as e:
        print(f"Error al obtener perfil: {e}")
        return jsonify({"msg": "Error interno del servidor al cargar el perfil"}), 500

@user_bp.route('/profile/upload-image', methods=['POST'])
@jwt_required()
def upload_profile_image_endpoint():
    """Sube una nueva foto de perfil para el usuario autenticado."""
    current_user_id, _ = get_user_and_role()
    if not current_user_id:
        return jsonify({"msg": "Usuario no autenticado o token inválido"}), 401

    if 'profile_image' not in request.files or request.files['profile_image'].filename == '':
        return jsonify({"msg": "No se encontró el archivo de imagen"}), 400
        
    file = request.files['profile_image']

    try:
        # Aquí, current_user_id ya se usa como str en el helper
        new_image_url = upload_profile_image(file, str(current_user_id)) 

        if new_image_url:
            with get_db_cursor() as cur:
                # current_user_id se pasa como UUID
                cur.execute("SELECT profile_image_url FROM users WHERE id = %s", (current_user_id,))
                old_url_row = cur.fetchone()
                old_url = old_url_row['profile_image_url'] if old_url_row else None
            
            with get_db_cursor(commit=True) as cur:
                cur.execute(
                    "UPDATE users SET profile_image_url = %s WHERE id = %s",
                    (new_image_url, current_user_id)
                )

            if old_url:
                delete_profile_image(old_url) 

            return jsonify({
                "msg": "Foto de perfil actualizada exitosamente", 
                "profile_image_url": new_image_url 
            }), 200
            
        return jsonify({"msg": "Error al subir la imagen"}), 500

    except Exception as e:
        print(f"Error al subir imagen: {e}")
        return jsonify({"msg": "Error interno del servidor al subir la imagen", "error": str(e)}), 500

# =========================================================
# RUTAS DE GESTIÓN DE USUARIOS (Acceso de Administrador: /admin/users/*)
# =========================================================

@admin_bp.route('/users', methods=['GET']) 
@jwt_required()
def admin_list_users():
    """Lista todos los usuarios de negocio (Admin, Consultor, Almacenista)."""
    current_user_id, user_role_id = get_user_and_role()
    
    # 1. Verificar Permisos
    if not check_admin_permission(user_role_id):
        return jsonify({"msg": "Acceso denegado: Se requiere rol de Administrador (1)."}), 403

    try:
        with get_db_cursor() as cur:
            cur.execute(
                """
                SELECT u.id, u.email, u.role_id, r.name as role_name
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.role_id IN %s
                ORDER BY u.role_id, u.email
                """,
                # El ADMIN puede gestionar los roles 1, 2 y 3.
                (ALLOWED_ROLES_FOR_ADMIN,)
            )
            users_list = [dict(row) for row in cur.fetchall()]
            
            for user in users_list:
                 # Se asegura que el ID sea string para el frontend (Vue.js)
                 user['id'] = str(user['id'])

            return jsonify(users_list), 200

    except Exception as e:
        print(f"Error al listar usuarios admin: {e}")
        return jsonify({"msg": "Error interno del servidor al listar usuarios"}), 500


@admin_bp.route('/users', methods=['POST']) 
@jwt_required()
def admin_create_user():
    """Crea un nuevo usuario (solo para roles 1, 2 o 3)."""
    current_user_id, user_role_id = get_user_and_role()
    if not check_admin_permission(user_role_id):
        return jsonify({"msg": "Acceso denegado."}), 403

    data = request.get_json()
    required = ['email', 'password', 'role_id']
    if error := validate_required_fields(data, required):
        return jsonify({"msg": error}), 400

    email = data['email']
    password = data['password']
    role_id = int(data['role_id']) 

    if role_id not in ALLOWED_ROLES_FOR_ADMIN:
        allowed_names = ", ".join(map(str, ALLOWED_ROLES_FOR_ADMIN))
        return jsonify({"msg": f"Solo se permite crear usuarios con Rol {allowed_names}."}), 400

    hashed_password = generate_password_hash(password)

    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO users (email, password, role_id) VALUES (%s, %s, %s) RETURNING id",
                (email, hashed_password, role_id)
            )
            new_user_id = cur.fetchone()['id']
            return jsonify({"msg": "Usuario creado exitosamente", "id": str(new_user_id)}), 201
            
    except Exception as e:
        if 'unique constraint' in str(e).lower():
            return jsonify({"msg": "El email ya está registrado."}), 409
        print(f"Error al crear usuario: {e}")
        return jsonify({"msg": "Error interno del servidor al crear usuario"}), 500


@admin_bp.route('/users/<uuid:user_id>', methods=['PUT']) 
@jwt_required()
def admin_update_user_role(user_id):
    """Permite al administrador actualizar el rol de otro usuario (solo roles 1, 2 o 3)."""
    current_user_id, user_role_id = get_user_and_role()
    if not check_admin_permission(user_role_id):
        return jsonify({"msg": "Acceso denegado."}), 403

    data = request.get_json()
    new_role_id = data.get('role_id')
    
    if new_role_id is None:
        return jsonify({"msg": "El campo 'role_id' es obligatorio para la actualización."}), 400

    new_role_id = int(new_role_id)

    if new_role_id not in ALLOWED_ROLES_FOR_ADMIN:
        allowed_names = ", ".join(map(str, ALLOWED_ROLES_FOR_ADMIN))
        return jsonify({"msg": f"Solo se permite asignar Rol {allowed_names}."}), 400
        
    if str(user_id) == str(current_user_id):
           return jsonify({"msg": "Operación no permitida: No puedes modificar tu propio rol o contraseña."}), 403

    try:
        # 🟢 CORRECCIÓN CLAVE: Convertir el objeto UUID a string para el driver DB
        user_id_str = str(user_id)

        with get_db_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE users SET role_id = %s WHERE id = %s RETURNING id",
                (new_role_id, user_id_str)
            )
            if cur.fetchone():
                return jsonify({"msg": f"Rol del usuario {user_id} actualizado a {new_role_id} exitosamente."}), 200
            else:
                return jsonify({"msg": "Usuario no encontrado."}), 404

    except Exception as e:
        # Usamos print y el mensaje genérico para evitar exponer detalles internos al cliente
        print(f"Error al actualizar rol: {e}")
        return jsonify({"msg": "Error interno del servidor al actualizar el rol"}), 500


@admin_bp.route('/users/<uuid:user_id>', methods=['DELETE']) 
@jwt_required()
def admin_delete_user(user_id):
    """Permite al administrador eliminar un usuario (solo roles 1, 2 o 3)."""
    current_user_id, user_role_id = get_user_and_role()
    if not check_admin_permission(user_role_id):
        return jsonify({"msg": "Acceso denegado."}), 403
        
    if str(user_id) == str(current_user_id):
           return jsonify({"msg": "Operación no permitida: No puedes eliminarte a ti mismo."}), 403

    try:
        # 🟢 CORRECCIÓN CLAVE: Convertir el objeto UUID a string para el driver DB
        user_id_str = str(user_id)

        with get_db_cursor(commit=True) as cur:
            # Usamos la cadena
            cur.execute("SELECT profile_image_url FROM users WHERE id = %s", (user_id_str,))
            user_data = cur.fetchone()
            
            # Usamos la cadena
            cur.execute("DELETE FROM users WHERE id = %s RETURNING id", (user_id_str,))
            
            if cur.fetchone():
                if user_data and user_data.get('profile_image_url'):
                    # La función de Cloudinary ya maneja URLs, no necesita el UUID object
                    delete_profile_image(user_data['profile_image_url']) 
                    
                return jsonify({"msg": f"Usuario {user_id} eliminado exitosamente."}), 200
            else:
                return jsonify({"msg": "Usuario no encontrado."}), 404

    except Exception as e:
        print(f"Error al eliminar usuario: {e}")
        return jsonify({"msg": "Error interno del servidor al eliminar usuario"}), 500