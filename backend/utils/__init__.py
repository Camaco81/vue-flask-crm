# backend/utils/__init__.py

from .helpers import (
    get_user_and_role, 
    check_admin_permission, 
    # check_seller_permission, <--- ELIMINAR ESTO
    check_product_manager_permission, # <--- AÑADIR ESTA NUEVA FUNCIÓN DE PERMISO
    validate_required_fields, 
    ADMIN_ROLE_ID, 
    CONSULTOR_ROLE_ID, # <--- USAR EL NOMBRE CORREGIDO
    CUSTOMER_ROLE_ID
)

# ... otras líneas si existen