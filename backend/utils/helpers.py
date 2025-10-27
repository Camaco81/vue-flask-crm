from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from backend.db import get_db_cursor
import uuid # Necesario si user_id es un UUID

# --- Constantes de Roles ---
# NOTA: Usar variables de entorno para los IDs en un entorno de producción sería ideal.
ADMIN_ROLE_ID = 1
SELLER_ROLE_ID = 2 # Rol de 'consultor' o 'vendedor'
CUSTOMER_ROLE_ID = 3

# =========================================================
# FUNCIONES DE USUARIO Y ROL
# =========================================================

def get_user_and_role():
    """
    Obtiene el ID del usuario actual (UUID) y su role_id (entero) desde la base de datos.
    Retorna (user_id: str, role_id: int) o (None, None).
    """
    # get_jwt_identity() devuelve el valor que pasaste a create_access_token, que debe ser el UUID.
    current_user_id = get_jwt_identity() 
    
    if not current_user_id:
        return None, None
        
    try:
        # Intenta asegurar que el ID es un UUID válido antes de la consulta
        # Esto previene errores de PostgreSQL si el token es corrupto
        if not isinstance(current_user_id, uuid.UUID):
            # Asumiendo que el ID en el token es un string de UUID.
            current_user_id = str(current_user_id) 

        with get_db_cursor() as cur:
            cur.execute("SELECT role_id FROM users WHERE id = %s", (current_user_id,))
            user_record = cur.fetchone()
            if user_record:
                # Retorna el ID del usuario (str) y el ID del rol (entero)
                return current_user_id, user_record['role_id']
            return None, None
    except Exception as e:
        # Es crucial que el logger capture estos errores en producción
        print(f"Error en get_user_and_role: {e}") 
        return None, None

# =========================================================
# FUNCIONES DE PERMISOS
# =========================================================

def check_admin_permission(user_role_id):
    """
    Verifica si el role_id del usuario es de administrador (ADMIN_ROLE_ID).
    """
    return user_role_id == ADMIN_ROLE_ID

def check_seller_permission(user_role_id):
    """
    Verifica si el role_id del usuario tiene permisos de VENTA.
    (Roles permitidos: Admin (1) y Vendedor (2)).
    """
    return user_role_id == ADMIN_ROLE_ID or user_role_id == SELLER_ROLE_ID

# Mantengo la función anterior si la usas en otros módulos
def check_product_manager_permission(user_role_id):
    """
    Verifica si el role_id del usuario tiene permisos de gestión de productos.
    (Roles permitidos: Admin (1) y Vendedor/Consultor (2)).
    """
    # Alias para la función de vendedor/consultor
    return check_seller_permission(user_role_id) 

# =========================================================
# FUNCIONES DE VALIDACIÓN
# =========================================================

def validate_required_fields(data, fields):
    """
    Valida que los campos requeridos estén presentes, no sean None y no estén vacíos.
    
    :param data: Diccionario de datos JSON del request.
    :param fields: Lista de strings con los nombres de los campos requeridos.
    :return: Nombre del campo faltante (str) si hay un error, o None si todo está bien.
    """
    # Si los datos no son un diccionario, es un error de formato, no de campos faltantes
    if not isinstance(data, dict):
        # Manejar un caso donde data no es un diccionario (ej: request.get_json() falló)
        return "JSON_FORMAT_ERROR" 

    for field in fields:
        # 1. ¿El campo no está en el diccionario?
        if field not in data:
            return field
        
        value = data[field]

        # 2. ¿El valor es None? (E.g., si el JSON vino como {"field": null})
        if value is None:
            return field

        # 3. ¿El valor es un string vacío o solo espacios?
        if isinstance(value, str) and not value.strip():
            return field
            
        # 4. Si es una lista o dict, ¿está vacío? (Comprobación extra útil para 'items': [])
        if isinstance(value, (list, dict)) and not value:
            return field
            
    return None # Todos los campos están presentes y son válidos.