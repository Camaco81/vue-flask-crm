from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from werkzeug.security import generate_password_hash

# 1. Importaciones de Helpers y DB
from backend.db import get_db_cursor
from backend.utils.helpers import get_user_and_role, check_admin_permission, validate_required_fields, CONSULTOR_ROLE_ID
from backend.utils.cloudinary_handler import upload_profile_image, delete_profile_image # Asumimos que existen y funcionan

# =========================================================
# Blueprints
# =========================================================

# Rutas para que CUALQUIER USUARIO acceda a su perfil (GET /api/profile, POST /api/profile/upload-image)
# Se registra en app.py con url_prefix='/api/users' (idealmente) o se deja así y se usa '/profile'
user_bp = Blueprint('user', __name__, url_prefix='/api')

# Rutas exclusivas para ADMINISTRADORES (GET, POST, PUT, DELETE /admin/users)
# NOTA CRÍTICA: Se define sin prefijo aquí. El prefijo '/admin' se añade en app.py al registrarlo.
# Así, las rutas internas como '/' dan como resultado final '/admin/' (o '/admin/users' si se usa una ruta interna '/users').
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
            # Asegurar la conversión de UUID a string (necesario para JSON)
            profile['id'] = str(profile['id'])
            
            # Limpieza (aunque no deberían estar)
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
        # 1. Subir la imagen a Cloudinary (o similar)
        # Pasamos el current_user_id como str para usarlo en el path de Cloudinary
        new_image_url = upload_profile_image(file, str(current_user_id)) 

        if new_image_url:
            # 2. Obtener la URL antigua (para eliminarla después de la actualización)
            with get_db_cursor() as cur:
                cur.execute("SELECT profile_image_url FROM users WHERE id = %s", (current_user_id,))
                old_url_row = cur.fetchone()
                old_url = old_url_row['profile_image_url'] if old_url_row else None
            
            # 3. Actualizar la nueva URL en la DB y hacer COMMIT
            with get_db_cursor(commit=True) as cur:
                cur.execute(
                    "UPDATE users SET profile_image_url = %s WHERE id = %s",
                    (new_image_url, current_user_id)
                )

            # 4. Eliminar la imagen antigua si existe (Operación post-commit)
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
# RUTAS DE GESTIÓN DE USUARIOS (Acceso de Administrador: /admin/*)
# =========================================================

# Esta ruta se traduce a GET /admin/users/
@admin_bp.route('/users/', methods=['GET']) 
@jwt_required()
def admin_list_users():
    """Lista todos los usuarios con roles de Administrador (1) y Consultor (2)."""
    current_user_id, user_role_id = get_user_and_role()
    
    # 1. Verificar Permisos
    if not check_admin_permission(user_role_id):
        return jsonify({"msg": "Acceso denegado: Se requiere rol de Administrador (1)."}), 403

    try:
        with get_db_cursor() as cur:
            # Selecciona solo usuarios con rol 1 (Administrador) o 2 (Consultor/Vendedor)
            cur.execute(
                """
                SELECT u.id, u.email, u.role_id, r.name as role_name
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.role_id IN (1, 2)
                ORDER BY u.role_id, u.email
                """
            )
            users_list = [dict(row) for row in cur.fetchall()]
            
            # Convertir UUIDs a string para serialización JSON
            for user in users_list:
                 user['id'] = str(user['id'])

            return jsonify(users_list), 200

    except Exception as e:
        print(f"Error al listar usuarios admin: {e}")
        return jsonify({"msg": "Error interno del servidor al listar usuarios"}), 500


# Esta ruta se traduce a POST /admin/users/
@admin_bp.route('/users/', methods=['POST']) 
@jwt_required()
def admin_create_user():
    """Crea un nuevo usuario (solo para roles 1 o 2)."""
    current_user_id, user_role_id = get_user_and_role()
    if not check_admin_permission(user_role_id):
        return jsonify({"msg": "Acceso denegado."}), 403

    data = request.get_json()
    required = ['email', 'password', 'role_id']
    if error := validate_required_fields(data, required):
        return jsonify({"msg": error}), 400

    email = data['email']
    password = data['password']
    role_id = int(data['role_id']) # Aseguramos que sea entero

    # Restricción: Solo permitir crear usuarios con roles 1 (Admin) o 2 (Consultor)
    if role_id not in (1, 2):
        return jsonify({"msg": "Solo se permite crear usuarios con Rol 1 (Admin) o Rol 2 (Consultor)."}), 400

    hashed_password = generate_password_hash(password)

    try:
        with get_db_cursor(commit=True) as cur:
            # Insertar el nuevo usuario y obtener su ID
            cur.execute(
                "INSERT INTO users (email, password, role_id) VALUES (%s, %s, %s) RETURNING id",
                (email, hashed_password, role_id)
            )
            new_user_id = cur.fetchone()['id']
            return jsonify({"msg": "Usuario creado exitosamente", "id": str(new_user_id)}), 201
            
    except Exception as e:
        if 'unique constraint' in str(e).lower(): # Uso .lower() para robustez
            return jsonify({"msg": "El email ya está registrado."}), 409
        print(f"Error al crear usuario: {e}")
        return jsonify({"msg": "Error interno del servidor al crear usuario"}), 500


# Esta ruta se traduce a PUT /admin/users/<uuid:user_id>
@admin_bp.route('/users/<uuid:user_id>', methods=['PUT']) 
@jwt_required()
def admin_update_user_role(user_id):
    """Permite al administrador actualizar el rol de otro usuario (solo roles 1 o 2)."""
    current_user_id, user_role_id = get_user_and_role()
    if not check_admin_permission(user_role_id):
        return jsonify({"msg": "Acceso denegado."}), 403

    data = request.get_json()
    new_role_id = data.get('role_id')
    
    if new_role_id is None:
        return jsonify({"msg": "El campo 'role_id' es obligatorio para la actualización."}), 400

    new_role_id = int(new_role_id)

    # Restricción: Solo permitir asignar roles 1 (Admin) o 2 (Consultor)
    if new_role_id not in (1, 2):
        return jsonify({"msg": "Solo se permite asignar Rol 1 (Admin) o Rol 2 (Consultor)."}), 400
        
    # Restricción de seguridad: Impedir que un admin se cambie su propio rol
    # Se debe comparar la representación string del UUID de la URL con el ID de la sesión.
    if str(user_id) == str(current_user_id):
           return jsonify({"msg": "Operación no permitida: No puedes modificar tu propio rol o contraseña."}), 403

    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE users SET role_id = %s WHERE id = %s RETURNING id",
                (new_role_id, user_id)
            )
            if cur.fetchone():
                return jsonify({"msg": f"Rol del usuario {user_id} actualizado a {new_role_id} exitosamente."}), 200
            else:
                return jsonify({"msg": "Usuario no encontrado."}), 404

    except Exception as e:
        print(f"Error al actualizar rol: {e}")
        return jsonify({"msg": "Error interno del servidor al actualizar el rol"}), 500


# Esta ruta se traduce a DELETE /admin/users/<uuid:user_id>
@admin_bp.route('/users/<uuid:user_id>', methods=['DELETE']) 
@jwt_required()
def admin_delete_user(user_id):
    """Permite al administrador eliminar un usuario (solo roles 1 o 2)."""
    current_user_id, user_role_id = get_user_and_role()
    if not check_admin_permission(user_role_id):
        return jsonify({"msg": "Acceso denegado."}), 403
        
    # Restricción de seguridad: Impedir que un admin se elimine a sí mismo
    if str(user_id) == str(current_user_id):
           return jsonify({"msg": "Operación no permitida: No puedes eliminarte a ti mismo."}), 403

    try:
        # Usamos una transacción para asegurar que la consulta y la eliminación de Cloudinary sean atómicas.
        with get_db_cursor(commit=True) as cur:
            # 1. Obtener la URL de la imagen (para eliminarla después)
            cur.execute("SELECT profile_image_url FROM users WHERE id = %s", (user_id,))
            user_data = cur.fetchone()
            
            # 2. Eliminar el usuario de la DB
            cur.execute("DELETE FROM users WHERE id = %s RETURNING id", (user_id,))
            
            if cur.fetchone():
                # 3. Si la eliminación en la DB fue exitosa, eliminamos la imagen
                if user_data and user_data.get('profile_image_url'):
                    # Si delete_profile_image fallara, la eliminación de la DB ya ocurrió,
                    # lo cual prioriza la integridad de los datos de la app sobre el almacenamiento externo.
                    delete_profile_image(user_data['profile_image_url']) 
                    
                return jsonify({"msg": f"Usuario {user_id} eliminado exitosamente."}), 200
            else:
                return jsonify({"msg": "Usuario no encontrado."}), 404

    except Exception as e:
        print(f"Error al eliminar usuario: {e}")
        return jsonify({"msg": "Error interno del servidor al eliminar usuario"}), 500