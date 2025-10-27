# backend/utils/__init__.py
from .helpers import (
    get_user_and_role, 
    check_admin_permission, 
    check_product_manager_permission, # <-- Esta debe estar para que la uses en rutas
    validate_required_fields, 
    ADMIN_ROLE_ID, 
    SELLER_ROLE_ID, 
    CUSTOMER_ROLE_ID
)