from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, get_jwt
from backend.db import get_db_cursor
from functools import wraps
import logging

app_logger = logging.getLogger(__name__) 

# --- 1. Constantes de Roles ---
ADMIN_ROLE_ID = 1
SELLER_ROLE_ID = 2
WAREHOUSE_ROLE_ID = 3
CUSTOMER_ROLE_ID = 4

# --- 2. Funciones de Identidad ---
def get_user_and_role():
    """Obtiene u_id, role_id y tenant_id desde el JWT y la DB."""
    current_user_id = get_jwt_identity() 
    claims = get_jwt()
    
    if not current_user_id:
        return None, None, None
        
    try:
        u_id = str(current_user_id)
        tenant_id_token = claims.get('tenant_id')

        with get_db_cursor() as cur:
            cur.execute("SELECT role_id, tenant_id FROM users WHERE id = %s", (u_id,))
            record = cur.fetchone()
            if record:
                # Retornamos el tenant_id de la DB, o el del token como respaldo
                return u_id, record['role_id'], record['tenant_id'] or tenant_id_token
            
        return None, None, None
    except Exception as e:
        app_logger.error(f"Error en get_user_and_role: {e}")
        return None, None, None

# --- 3. Funciones de Permisos (LAS QUE PIDE EL __INIT__) ---
def check_admin_permission(user_role_id):
    """Solo el administrador principal."""
    return int(user_role_id) == ADMIN_ROLE_ID

def check_seller_permission(user_role_id):
    """Permiso para realizar ventas: Admin y Vendedores."""
    return int(user_role_id) in [ADMIN_ROLE_ID, SELLER_ROLE_ID]

def check_product_manager_permission(user_role_id):
    """Permiso para gestionar inventario: Admin, Vendedores y Almacenistas."""
    allowed_roles = [ADMIN_ROLE_ID, SELLER_ROLE_ID, WAREHOUSE_ROLE_ID]
    return int(user_role_id) in allowed_roles

# --- 4. Decoradores (Opcionales, pero recomendados para las rutas) ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        _, role_id, _ = get_user_and_role()
        if not role_id or not check_admin_permission(role_id):
            return jsonify({"msg": "Acceso restringido: Solo Administradores"}), 403
        return f(*args, **kwargs)
    return decorated_function

# --- 5. Validaciones de Datos ---
def validate_required_fields(data, fields):
    if not isinstance(data, dict):
        return "FORMATO_JSON_INVALIDO" 

    for field in fields:
        value = data.get(field)
        if value is None:
            return field
        if isinstance(value, str) and not value.strip():
            return field
        if isinstance(value, (list, dict)) and len(value) == 0:
            return field
    return None