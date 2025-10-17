# backend/utils/cloudinary_handler.py
import os
import uuid
# from cloudinary.uploader import upload # Importación real
# from cloudinary.api import delete_resources # Importación real

# --- SIMULACIÓN DE CLOUDINARY ---
# En un entorno real, aquí iría la lógica de upload y delete de Cloudinary.
# Para este ejemplo, solo simulamos que guardamos un "url" en la DB.

def upload_profile_image(file_data, user_id):
    """Simula la subida de una imagen a Cloudinary."""
    if not file_data:
        return None

    # En la vida real, se sube el archivo (file_data.read()) a Cloudinary.
    # Cloudinary devuelve un URL.
    
    # URL simulada:
    public_id = f"crm_user_profiles/{user_id}/{uuid.uuid4().hex}"
    image_url = f"https://res.cloudinary.com/yourcloudname/image/upload/v1/user_profile/{public_id}.jpg"
    
    print(f"DEBUG: Imagen subida a Cloudinary con URL: {image_url}")
    return image_url

def delete_profile_image(old_url):
    """Simula la eliminación de una imagen de Cloudinary."""
    if old_url and "cloudinary" in old_url:
        # En la vida real, se extrae el public_id y se llama a delete_resources
        print(f"DEBUG: Eliminando imagen antigua de Cloudinary: {old_url}")
        return True
    return False

# Asegúrate de importar esto en tu nuevo Blueprint
# from backend.utils.cloudinary_handler import upload_profile_image, delete_profile_image