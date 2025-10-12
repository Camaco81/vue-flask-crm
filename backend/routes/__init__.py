# routes/__init__.py

from .customer_routes import customer_bp # OK: .customer_routes es hermano de __init__.py
from .product_routes import product_bp
from .sale_routes import sale_bp
# Si tuvieras más archivos de rutas, los importarías aquí:
# from .user_routes import user_bp 

# Lista de todas las Blueprints para registrar fácilmente en app.py
all_blueprints = [
    customer_bp,
    product_bp,
    sale_bp,
    # user_bp, # Descomenta si tienes un blueprint para usuarios
]