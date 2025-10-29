from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import logging
from dotenv import load_dotenv

# 1. Cargar variables de entorno PRIMERO
load_dotenv()

# 2. Importaciones ABSOLUTAS
from backend.config import Config
from backend.auth import auth_bp
from backend.routes.customer_routes import customer_bp
from backend.routes.product_routes import product_bp
from backend.routes.sale_routes import sale_bp
# Importamos AMBOS Blueprints: user_bp (profile) y admin_bp (admin/users)
from backend.routes.user_routes import user_bp, admin_bp
from backend.routes.common_routes import rate_bp


# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
app_logger = logging.getLogger(__name__)

# Inicialización de la aplicación
app = Flask(__name__)
app.config.from_object(Config) # Correcto uso de Config

# Inicializar JWT
jwt = JWTManager(app)

# Configurar CORS 
CORS(
    app, 
    origins="*",
    supports_credentials=True
)

# ----------------------------------------------------
# 3. Registro de Blueprints (¡CORREGIDO!)
# ----------------------------------------------------
# Nota: La convención es registrar los Blueprints bajo un prefijo común (/api) 
# y dejar que el Blueprint use rutas relativas (ej. user_bp.route('/profile')).

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(customer_bp, url_prefix='/api/customers')
app.register_blueprint(product_bp, url_prefix='/api/products')
app.register_blueprint(sale_bp, url_prefix='/api/sales') 
app.register_blueprint(rate_bp , url_prefix='/api/exchange-rate') 


# 🚨 CORRECCIÓN CLAVE: El user_bp contiene la ruta /profile, que debe ser accesible bajo /api/profile.
# El url_prefix de este Blueprint debe ser /api.
app.register_blueprint(user_bp, url_prefix='/api') 

# 🚨 CORRECCIÓN CLAVE: El admin_bp debe ser registrado bajo el prefijo /admin, 
# y como contiene /users, la ruta final será /admin/users.
app.register_blueprint(admin_bp, url_prefix='/admin', strict_slashes=False)


# Ruta de prueba simple
@app.route('/')
def index():
    return "Welcome to the Sales API!"

# ----------------------------------------------------
# 4. Manejadores de errores (Sin cambios, son correctos)
# ----------------------------------------------------
@app.errorhandler(404)
def not_found_error(error):
    app_logger.warning(f"404 Not Found: Path accessed: {request.path}") # Usar request.path para mejor log
    return jsonify({"msg": "Resource not found", "error_code": 404}), 404

@app.errorhandler(500)
def internal_error(error):
    app_logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({"msg": "Internal server error", "error_code": 500}), 500

if __name__ == '__main__':
    app_logger.info("Starting Flask application...")
    # El entorno de producción (Render, Gunicorn) manejará el host y port
    app.run(debug=True, host='0.0.0.0', port=5000)