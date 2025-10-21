from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import logging
from dotenv import load_dotenv # Mantenemos esta línea

# 1. Cargar variables de entorno PRIMERO
load_dotenv()

# 2. Importaciones ABSOLUTAS (Asegúrate que las rutas sean consistentes)
from backend.config import Config
from backend.auth import auth_bp
from backend.routes.customer_routes import customer_bp
from backend.routes.product_routes import product_bp
from backend.routes.sale_routes import sale_bp
# 🚨 IMPORTANTE: Verificación de Blueprints
# user_bp: Rutas como /api/profile
# admin_bp: Rutas de administración. Asumimos que maneja /admin/users
from backend.routes.user_routes import user_bp, admin_bp 


# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
app_logger = logging.getLogger(__name__)

# Inicialización de la aplicación
app = Flask(__name__)
# 🚨 Sugerencia: Usar 'backend.config.Config' si no está en el mismo nivel
app.config.from_object(Config)

# Inicializar JWT
jwt = JWTManager(app)

# Configurar CORS (Mantener '*' es flexible para desarrollo)
CORS(
    app, 
    origins="*",
    supports_credentials=True
)

# ----------------------------------------------------
# 3. Registro de Blueprints
# ----------------------------------------------------
# Nota de optimización: Revisa que cada BP tenga su 'url_prefix' definido 
# para modularizar correctamente. (Ej: /api/auth, /api/customers, /admin)

app.register_blueprint(auth_bp, url_prefix='/api/auth')         # Ej: /api/auth/login
app.register_blueprint(customer_bp, url_prefix='/api/customers') # Ej: /api/customers
app.register_blueprint(product_bp, url_prefix='/api/products')   # Ej: /api/products
app.register_blueprint(sale_bp, url_prefix='/api/sales')         # Ej: /api/sales y reportes
app.register_blueprint(user_bp, url_prefix='/api/users')         # Ej: /api/users/profile
app.register_blueprint(admin_bp, url_prefix='/admin')            # Ej: /admin/users

# 🚨 ANÁLISIS CRÍTICO DE RUTAS 🚨
# Para que funcione:
# - El frontend pide: /admin/users -> (admin_bp debe tener la ruta '/users')
# - El frontend pide: /api/orders (o reportes) -> (sale_bp debe tener la ruta '/reportes' o similar)


# Ruta de prueba simple
@app.route('/')
def index():
    return "Welcome to the Sales API!"

# ----------------------------------------------------
# 4. Manejadores de errores
# ----------------------------------------------------
@app.errorhandler(404)
def not_found_error(error):
    # Loguea el intento de acceso a ruta no encontrada
    app_logger.warning(f"404 Not Found: Path accessed: {error.description}")
    return jsonify({"msg": "Resource not found", "error_code": 404}), 404

@app.errorhandler(500)
def internal_error(error):
    app_logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({"msg": "Internal server error", "error_code": 500}), 500

if __name__ == '__main__':
    # Usar host='0.0.0.0' para ser accesible en Docker/Render
    app_logger.info("Starting Flask application...")
    app.run(debug=True, host='0.0.0.0', port=5000)