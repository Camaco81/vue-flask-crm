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
    """
    Obtiene u_id, role_id y tenant_id desde el JWT y la DB.
    """
    current_user_id = get_jwt_identity() 
    claims = get_jwt() # Obtenemos datos extra del token
    
    if not current_user_id:
        return None, None, None
        
    try:
        u_id = str(current_user_id)
        # Priorizamos el tenant_id que viene en el token (más rápido)
        tenant_id = claims.get('tenant_id')

        with get_db_cursor() as cur:
            # Si no está en el token, lo buscamos en la DB una vez
            cur.execute("SELECT role_id, tenant_id FROM users WHERE id = %s", (u_id,))
            record = cur.fetchone()
            if record:
                return u_id, record['role_id'], record['tenant_id'] or tenant_id
            
        return None, None, None
    except Exception as e:
        app_logger.error(f"Error en get_user_and_role: {e}")
        return None, None, None

# --- 3. Decoradores de Permisos ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        _, role_id, _ = get_user_and_role()
        if role_id != ADMIN_ROLE_ID:
            return jsonify({"msg": "Acceso restringido: Solo Administradores"}), 403
        return f(*args, **kwargs)
    return decorated_function

# --- 4. Validaciones de Datos ---
def validate_required_fields(data, fields):
    """
    Valida que los campos existan y no estén vacíos.
    """
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