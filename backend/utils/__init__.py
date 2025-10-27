# En backend/utils/__init__.py
from .helpers import (
    ADMIN_ROLE_ID, 
    SELLER_ROLE_ID,          # <--- ¡Debe estar aquí!
    CUSTOMER_ROLE_ID,
    get_user_and_role, 
    check_admin_permission, 
    check_seller_permission,
    check_product_manager_permission,
    validate_required_fields
)