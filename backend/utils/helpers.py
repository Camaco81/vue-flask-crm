from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from backend.db import get_db_cursor
import uuid
from functools import wraps
import logging

app_logger = logging.getLogger(__name__) 

# --- Constantes de Roles (Alineadas con la DB) ---
# 1: Admin (Control total)
# 2: Seller/Vendedor (Ventas y Clientes)
# 3: Warehouse/Almacenista (Gestión de Productos/Stock)
ADMIN_ROLE_ID = 1
SELLER_ROLE_ID = 2
WAREHOUSE_ROLE_ID = 3

# =========================================================
# FUNCIONES DE USUARIO Y ROL
# =========================================================

def get_user_and_role():
    """
    Obtiene el ID del usuario y su role_id desde la DB.
    """
    current_user_id = get_jwt_identity() 
    
    if not current_user_id:
        return None, None
        
    try:
        # Asegurar formato string para el UUID en la consulta
        u_id = str(current_user_id) 

        with get_db_cursor() as cur:
            cur.execute("SELECT role_id FROM users WHERE id = %s", (u_id,))
            user_record = cur.fetchone()
            if user_record:
                return u_id, user_record['role_id']
            return None, None
    except Exception as e:
        # En producción, usa logging en lugar de print
        return None, None

# =========================================================
# FUNCIONES DE PERMISOS (Lógica de Negocio)
# =========================================================

def check_admin_permission(user_role_id):
    """Solo el administrador principal."""
    return user_role_id == ADMIN_ROLE_ID

def check_seller_permission(user_role_id):
    """Permiso para realizar ventas: Admin y Vendedores."""
    return user_role_id in [ADMIN_ROLE_ID, SELLER_ROLE_ID]

def check_product_manager_permission(user_role_id):
    """Permiso para gestionar inventario: Admin y Almacenistas (y opcionalmente vendedores)."""
    # Aquí incluimos al 1, 2 y 3 para que todos puedan ver/gestionar según tu requerimiento
    allowed_roles = [ADMIN_ROLE_ID, SELLER_ROLE_ID, WAREHOUSE_ROLE_ID]
    return user_role_id in allowed_roles

# =========================================================
# FUNCIONES DE VALIDACIÓN (Sin cambios)
# =========================================================

def validate_required_fields(data, fields):
    """
    Valida que los campos existan y no estén vacíos.
    Retorna el nombre del primer campo con error o None.
    """
    if not isinstance(data, dict):
        return "FORMATO_JSON_INVALIDO" 

    for field in fields:
        if field not in data or data[field] is None:
            return field
        
        value = data[field]
        # Validar strings vacíos
        if isinstance(value, str) and not value.strip():
            return field
        # Validar listas o dicts vacíos (como la lista de items en una venta)
        if isinstance(value, (list, dict)) and len(value) == 0:
            return field
            
    return None