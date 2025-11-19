from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from backend.db import get_db_cursor
import uuid

# --- Constantes de Roles ---
ADMIN_ROLE_ID = 1
SELLER_ROLE_ID = 2 # El nuevo nombre para el rol de 'consultor' o 'vendedor'
CUSTOMER_ROLE_ID = 3

# =========================================================
# FUNCIONES DE USUARIO Y ROL
# =========================================================

def get_user_and_role():
    """
    Obtiene el ID del usuario actual (UUID) y su role_id (entero) desde la base de datos.
    Retorna (user_id: str, role_id: int) o (None, None).
    """
    current_user_id = get_jwt_identity() 
    
    if not current_user_id:
        return None, None
        
    try:
        if not isinstance(current_user_id, uuid.UUID):
            current_user_id = str(current_user_id) 

        with get_db_cursor() as cur:
            cur.execute("SELECT role_id FROM users WHERE id = %s", (current_user_id,))
            user_record = cur.fetchone()
            if user_record:
                return current_user_id, user_record['role_id']
            return None, None
    except Exception as e:
        print(f"Error en get_user_and_role: {e}") 
        return None, None

# =========================================================
# FUNCIONES DE PERMISOS
# =========================================================

def check_admin_permission(user_role_id):
    """
    Verifica si el role_id del usuario es de administrador (ADMIN_ROLE_ID).
    """
    return user_role_id == ADMIN_ROLE_ID or user_role_id == SELLER_ROLE_ID

def check_seller_permission(user_role_id):
    """
    Verifica si el role_id del usuario tiene permisos de VENTA.
    (Roles permitidos: Admin (1) y Vendedor (2)).
    """
    return user_role_id == ADMIN_ROLE_ID or user_role_id == SELLER_ROLE_ID

# Mantengo esta función para evitar romper otras dependencias que la usen.
def check_product_manager_permission(user_role_id):
    """
    Alias. Verifica si el role_id del usuario tiene permisos de gestión de productos.
    """
    return check_seller_permission(user_role_id) 

# =========================================================
# FUNCIONES DE VALIDACIÓN
# =========================================================

def validate_required_fields(data, fields):
    """
    Valida que los campos requeridos estén presentes, no sean None y no estén vacíos.
    
    :return: Nombre del campo faltante (str) si hay un error, o None si todo está bien.
    """
    if not isinstance(data, dict):
        return "JSON_FORMAT_ERROR" 

    for field in fields:
        if field not in data:
            return field
        
        value = data[field]

        if value is None:
            return field

        if isinstance(value, str) and not value.strip():
            return field
            
        if isinstance(value, (list, dict)) and not value:
            return field
            
    return None

ALLOWED_PRODUCT_MANAGER_ROLES = [1, 2, 3] 

def check_product_manager_permission(user_role_id):
    """Verifica si el ID de rol tiene permiso para gestionar productos (crear/modificar/eliminar)."""
    return user_role_id in ALLOWED_PRODUCT_MANAGER_ROLES