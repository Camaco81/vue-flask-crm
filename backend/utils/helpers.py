from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from backend.db import get_db_cursor
# from backend.config import Config # Descomentar si usas Config

# --- Constantes de Roles (USADAS PARA PERMISOS) ---
ADMIN_ROLE_ID = 1
CONSULTOR_ROLE_ID = 2 # Renombrado de SELLER_ROLE_ID a CONSULTOR_ROLE_ID (basado en el nombre en tu DB)
CUSTOMER_ROLE_ID = 3

def get_user_and_role():
    """
    Obtiene el ID del usuario actual y su role_id desde la base de datos.
    Retorna (user_id, role_id) o (None, None) si no se encuentra.
    """
    current_user_id = get_jwt_identity()
    if not current_user_id:
        return None, None
        
    try:
        with get_db_cursor() as cur:
            # Asegúrate de que tu cursor soporta acceso por columna (ej. psycopg2.extras.DictCursor)
            cur.execute("SELECT role_id FROM users WHERE id = %s", (current_user_id,))
            user_record = cur.fetchone()
            if user_record:
                # Retorna el ID del rol (entero)
                return current_user_id, user_record['role_id']
            return None, None
    except Exception as e:
        # Esto ayuda a depurar si el token es válido pero falla la DB
        print(f"Error en get_user_and_role: {e}") 
        return None, None


def check_admin_permission(user_role_id):
    """
    Verifica si el role_id del usuario es de administrador.
    """
    return user_role_id == ADMIN_ROLE_ID

def check_product_manager_permission(user_role_id):
    """
    Verifica si el role_id del usuario tiene permisos de gestión de productos.
    (Roles permitidos: Admin y Consultor/Vendedor, ID 1 y 2).
    """
    return user_role_id == ADMIN_ROLE_ID or user_role_id == CONSULTOR_ROLE_ID

def validate_required_fields(data, fields):
    """
    Valida que los campos requeridos estén presentes y no vacíos en el diccionario de datos.
    Retorna True si todos están presentes, False en caso contrario.
    """
    for field in fields:
        # Validación: verifica existencia y que no sean None/cadenas vacías
        # NOTA: Para campos numéricos como 'stock' o 'price' que pueden ser 0, 
        # esta validación SÓLO debe fallar si NO EXISTEN o son None.
        if field not in data or data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
            return False
    # Corrección del bug: retorna solo True o False
    return True