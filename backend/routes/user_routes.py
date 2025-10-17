from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.db import get_db_cursor
from backend.utils.helpers import get_user_and_role
# Asegúrate de que este archivo exista y contenga las funciones de simulación/integración
from backend.utils.cloudinary_handler import upload_profile_image, delete_profile_image 

user_bp = Blueprint('user', __name__, url_prefix='/api')

# =========================================================
# 1. GET: Obtener Información del Perfil (Solo campos específicos)
# =========================================================

@user_bp.route('profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    current_user_id, user_role = get_user_and_role()
    if not current_user_id:
        # En una aplicación real, esto ya sería atrapado por jwt_required,
        # pero es bueno verificar si el ID del token es válido.
        return jsonify({"msg": "Usuario no autenticado o token inválido"}), 401

    try:
        with get_db_cursor() as cur:
            # AJUSTE CLAVE: Selecciona solo las columnas que necesitas y usa el nombre exacto 'profile_image_url'
            cur.execute(
                """
                SELECT id, email, role_id, profile_image_url
                FROM users 
                WHERE id = %s
                """, 
                (current_user_id,)
            )
            user_data = cur.fetchone()

        if user_data:
            profile = dict(user_data)
            profile['id'] = str(profile['id'])
            
            # Opcional: Si quieres enviar el nombre del rol en lugar del ID,
            # puedes hacer un JOIN a la tabla de roles aquí.
            
            return jsonify(profile), 200
            
        return jsonify({"msg": "Perfil de usuario no encontrado"}), 404

    except Exception as e:
        print(f"Error al obtener perfil: {e}")
        return jsonify({"msg": "Error interno del servidor al cargar el perfil"}), 500

# =========================================================
# 2. POST: Subir Foto de Perfil
# =========================================================

@user_bp.route('/upload-image', methods=['POST'])
@jwt_required()
def upload_profile_image_endpoint():
    current_user_id, _ = get_user_and_role()
    if not current_user_id:
        return jsonify({"msg": "Usuario no autenticado o token inválido"}), 401

    if 'profile_image' not in request.files or request.files['profile_image'].filename == '':
        return jsonify({"msg": "No se encontró el archivo de imagen"}), 400
        
    file = request.files['profile_image']

    try:
        new_image_url = upload_profile_image(file, current_user_id) # Subida a Cloudinary

        if new_image_url:
            with get_db_cursor() as cur:
                # Obtener la URL antigua usando el nombre correcto de la columna
                cur.execute("SELECT profile_image_url FROM users WHERE id = %s", (current_user_id,))
                old_url_row = cur.fetchone()
                old_url = old_url_row['profile_image_url'] if old_url_row else None
            
            # Actualizar la nueva URL en la DB
            with get_db_cursor(commit=True) as cur:
                # Usar el nombre de columna correcto en el UPDATE
                cur.execute(
                    "UPDATE users SET profile_image_url = %s WHERE id = %s",
                    (new_image_url, current_user_id)
                )

            # Simular la eliminación de la imagen antigua
            if old_url:
                 delete_profile_image(old_url) 

            return jsonify({
                "msg": "Foto de perfil actualizada exitosamente", 
                "profile_image_url": new_image_url # Se devuelve el nombre de la columna correcta
            }), 200
            
        return jsonify({"msg": "Error al subir la imagen"}), 500

    except Exception as e:
        print(f"Error al subir imagen: {e}")
        return jsonify({"msg": "Error interno del servidor al subir la imagen", "error": str(e)}), 500

# =========================================================
# 3. PUT: Actualizar Información del Usuario (Optimizado para usar solo email si se necesita)
# =========================================================

@user_bp.route('/', methods=['PUT'])
@jwt_required()
def update_user_info():
    current_user_id, _ = get_user_and_role()
    if not current_user_id:
        return jsonify({"msg": "Usuario no autenticado o token inválido"}), 401

    data = request.get_json()
    # Si quisieras actualizar el email (con cuidado en la DB) o el rol, aquí iría.
    # Por ahora, dejamos la estructura si decides añadir otros campos.
    
    # Ejemplo de un campo que NO tienes en la vista pero podrías querer actualizar:
    # email = data.get('email')
    
    # Si no tienes otros campos de texto para actualizar, puedes eliminar esta ruta.
    
    return jsonify({"msg": "Endpoint de actualización de información de perfil no implementado o campos faltantes"}), 400
    
    # # Si se implementa:
    # try:
    #     # ... lógica de actualización ...
    #     return jsonify({"msg": "Información de perfil actualizada exitosamente"}), 200
    # except Exception as e:
    #     return jsonify({"msg": "Error al actualizar perfil", "error": str(e)}), 500