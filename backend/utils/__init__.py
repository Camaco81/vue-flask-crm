# backend/utils/__init__.py

from .helpers import (
    get_user_and_role, 
    check_admin_permission, 
    check_product_manager_permission, # <-- Añadida
    validate_required_fields, 
    ADMIN_ROLE_ID, 
    CONSULTOR_ROLE_ID, # <-- Corregida para coincidir con el helper
    CUSTOMER_ROLE_ID
)