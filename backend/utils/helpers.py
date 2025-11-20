from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from backend.db import get_db_cursor
import uuid
from functools import wraps
import logging

app_logger = logging.getLogger(__name__) 

# --- Constantes de Roles ---
ADMIN_ROLE_ID = 1
SELLER_ROLE_ID = 2 
CUSTOMER_ROLE_ID = 3
# Puedes añadir más IDs de roles aquí si es necesario
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
        # Aseguramos que el ID sea string si es necesario para la consulta SQL
        if isinstance(current_user_id, uuid.UUID):
            current_user_id = str(current_user_id) 

        with get_db_cursor() as cur:
            # Buscamos role_id directamente
            cur.execute("SELECT role_id FROM users WHERE id = %s", (current_user_id,))
            user_record = cur.fetchone()
            if user_record:
                # Retorna el ID de usuario (str) y el ID de rol (int)
                return current_user_id, user_record['role_id'] 
            return None, None
    except Exception as e:
        app_logger.error(f"Error en get_user_and_role: {e}", exc_info=True) 
        return None, None

# =========================================================
# FÁBRICA DE DECORADORES DE PERMISOS (OPTIMIZACIÓN)
# =========================================================

def role_required(allowed_role_ids, error_message="Permiso denegado por rol."):
    """
    Fábrica de decoradores que verifica si el ID de rol del usuario está en la lista permitida.

    Uso: @role_required([ADMIN_ROLE_ID, SELLER_ROLE_ID])
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id, role_id = get_user_and_role()
            
            # 1. Comprobar si el usuario está autenticado y tiene rol
            if role_id is None:
                return jsonify({'msg': 'Autenticación requerida.'}), 401

            # 2. Comprobar si el rol está permitido
            if role_id not in allowed_role_ids:
                return jsonify({'msg': error_message}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# =========================================================
# DECORADORES DE ACCESO RÁPIDO (REEMPLAZANDO LOS VIEJOS)
# =========================================================

# Vistas de Venta y Cliente (Vendedor o Admin)
check_seller_permission = role_required(
    [ADMIN_ROLE_ID, SELLER_ROLE_ID], 
    "Permiso denegado. Se requiere rol de vendedor o administrador."
)

# Vistas de Administración pura
check_admin_permission = role_required(
    [ADMIN_ROLE_ID], 
    "Permiso denegado. Se requiere rol de administrador."
)

# Vistas de Gestión de Productos (Ahora más explícito)
check_product_manager_permission = role_required(
    [ADMIN_ROLE_ID, SELLER_ROLE_ID, CUSTOMER_ROLE_ID], 
    "Permiso denegado. Se requiere un rol válido para gestionar productos." # Ajusta esto si solo Admin/Vendedor
)


# =========================================================
# FUNCIONES DE VALIDACIÓN (sin cambios, son correctas)
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