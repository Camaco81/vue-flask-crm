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
VISITOR_ROLE_ID = 4
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
            # Nota: Asumo que la tabla 'users' tiene una columna 'role_id'
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
# FÁBRICA DE DECORADORES DE PERMISOS
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
                # 401: No autenticado / Token inválido
                return jsonify({'msg': 'Autenticación requerida o token inválido.'}), 401

            # 2. Comprobar si el rol está permitido
            if role_id not in allowed_role_ids:
                # 403: Prohibido / Sin permiso para este recurso
                return jsonify({'msg': error_message}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# =========================================================
# DECORADORES DE ACCESO RÁPIDO (Definición clara de permisos)
# =========================================================

# Vistas de Venta y Cliente (Requieren Vendedor o Admin)
# **ESTE ES EL DECORADOR QUE DEBES USAR PARA CREAR CLIENTES**
check_seller_permission = role_required(
    [ADMIN_ROLE_ID, SELLER_ROLE_ID], 
    "Acceso denegado: solo administradores y vendedores pueden crear/gestionar clientes y ventas."
)

# Vistas de Administración pura (Requieren solo Admin)
check_admin_permission = role_required(
    [ADMIN_ROLE_ID], 
    "Permiso denegado. Se requiere rol de administrador."
)

# Vistas de Productos (Dependiendo de si el cliente puede ver productos, ajusta los roles)
check_product_manager_permission = role_required(
    [ADMIN_ROLE_ID, SELLER_ROLE_ID], # Solo Admin y Vendedor gestionan/ven productos
    "Permiso denegado. Se requiere un rol válido para gestionar productos." 
)


# =========================================================
# FUNCIONES DE VALIDACIÓN (Sin cambios)
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