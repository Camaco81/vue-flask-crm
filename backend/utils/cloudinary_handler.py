
import os
import cloudinary
import cloudinary.uploader
import cloudinary.api

cloudinary.config( 
  cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'), 
  api_key = os.getenv('CLOUDINARY_API_KEY'), 
  api_secret = os.getenv('CLOUDINARY_API_SECRET'),
  secure = True
)

# =========================================================
# 1. FUNCIÓN DE SUBIDA (REAL)
# =========================================================
def upload_profile_image(file_data, user_id):
    """Sube la imagen a Cloudinary y devuelve la URL segura."""
    if not file_data:
        return None

    try:
        # Nota: Cloudinary puede recibir el objeto de archivo directamente de Flask (file_data.stream)
        # o el archivo guardado temporalmente. Usar el objeto de archivo es más eficiente.
        result = cloudinary.uploader.upload(
            file_data, # Objeto de archivo de request.files
            folder=f"vue_flask_crm/user_profiles", # Carpeta base en Cloudinary
            public_id=f"user_{user_id}_profile", # Nombre del archivo (opcional)
            overwrite=True # Sobrescribe si ya existe un public_id con ese nombre
        )
        
        # 🚨 CLAVE: DEVOLVER EL SECURE_URL REAL
        return result.get('secure_url')
    
    except Exception as e:
        print(f"Error real de Cloudinary al subir: {e}")
        return None

# =========================================================
# 2. FUNCIÓN DE ELIMINACIÓN (REAL)
# =========================================================
def get_public_id_from_url(url):
    """Extrae el public_id del URL de Cloudinary."""
    # Este patrón funciona para URLs con o sin el componente /vXXXXXXXXXX/
    # Busca la parte después de la última carpeta del folder.
    try:
        # Asume que el folder es 'vue_flask_crm/user_profiles'
        parts = url.split(f"vue_flask_crm/user_profiles/")
        if len(parts) > 1:
            # Elimina la extensión (.jpg, .png, etc.)
            public_id_with_ext = parts[1].split('/')[-1]
            return f"vue_flask_crm/user_profiles/{public_id_with_ext.split('.')[0]}"
    except Exception:
        return None

def delete_profile_image(old_url):
    """Elimina la imagen antigua de Cloudinary usando su public_id."""
    
    # Si usaste un public_id fijo (user_id_profile) al subir, usa ese mismo para eliminar.
    # Si la URL de tu base de datos es la que generó la subida (con public_id="user_{user_id}_profile"),
    # lo mejor es extraer el ID.

    # 🚨 NOTA IMPORTANTE: Si usas `overwrite=True` con un `public_id` fijo al subir, 
    # la imagen antigua se borra automáticamente al subir la nueva. 
    # Por simplicidad, y ya que usas overwrite, podrías simplificar o eliminar la llamada a delete_profile_image
    # si la URL es consistente.

    public_id = get_public_id_from_url(old_url)
    if public_id:
        try:
            # Aquí asumes que la parte del public_id que guardaste en la DB (el final) es lo que Cloudinary necesita.
            # DEBES USAR EL PUBLIC_ID COMPLETO, incluyendo la carpeta si lo subiste en una carpeta.
            # Si usaste un public_id fijo (e.g., user_1234_profile) y overwrite, el public_id a borrar es ese mismo.
            
            # Si estás guardando la URL completa y tu folder es 'vue_flask_crm/user_profiles',
            # el public_id completo es: vue_flask_crm/user_profiles/user_1234_profile
            
            cloudinary.uploader.destroy(public_id) 
            return True
        except Exception as e:
            print(f"Error al intentar borrar imagen antigua de Cloudinary: {e}")
            return False
    return False