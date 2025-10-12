from flask import jsonify
from flask_jwt_extended import get_jwt_identity
# from db import get_db_cursor <-- Antiguo
from backend.db import get_db_cursor # <-- Nuevo
# Si usas constantes de config, también:
# from backend.config import Config

ADMIN_ROLE_ID = 1
SELLER_ROLE_ID = 2
CUSTOMER_ROLE_ID = 3 # Si tienes otros roles

def get_user_and_role():
    """
    Obtiene el ID del usuario actual y su role_id desde la base de datos.
    Retorna (user_id, role_id) o (None, None) si no se encuentra.
    """
    current_user_id = int(get_jwt_identity())
    with get_db_cursor() as cur:
        cur.execute("SELECT role_id FROM users WHERE id = %s", (current_user_id,))
        user_record = cur.fetchone()
        if user_record:
            return current_user_id, user_record['role_id']
        return None, None

def check_admin_permission(user_role):
    """
    Verifica si el role_id del usuario es de administrador.
    """
    return user_role == ADMIN_ROLE_ID

def check_seller_permission(user_role):
    """
    Verifica si el role_id del usuario es de vendedor o administrador.
    """
    return user_role == ADMIN_ROLE_ID or user_role == SELLER_ROLE_ID

def validate_required_fields(data, fields):
    """
    Valida que los campos requeridos estén presentes en el diccionario de datos.
    Retorna True si todos están presentes, False en caso contrario.
    """
    for field in fields:
        if field not in data or not data[field]:
            return False
    return True