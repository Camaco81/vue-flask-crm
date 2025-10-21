from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import logging
from dotenv import load_dotenv # Asegúrate de tener 'python-dotenv' instalado

# 1. Cargar variables de entorno PRIMERO (si usas un archivo .env)
load_dotenv()

# 2. Importaciones ABSOLUTAS (usando 'backend.' como base)
from backend.config import Config
from backend.auth import auth_bp
from backend.routes.customer_routes import customer_bp
from backend.routes.product_routes import product_bp
from backend.routes.sale_routes import sale_bp
from backend.routes.user_routes import user_bp, admin_user_bp
# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
app_logger = logging.getLogger(__name__)

# Inicialización de la aplicación
app = Flask(__name__)
app.config.from_object(Config)

# Inicializar JWT
jwt = JWTManager(app)

# Configurar CORS
CORS(
    app, 
    origins="*",
    supports_credentials=True
)

# Registrar Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(product_bp)
app.register_blueprint(sale_bp)
app.register_blueprint(user_bp)


# Ruta de prueba simple
@app.route('/')
def index():
    return "Welcome to the Sales API!"

# Manejadores de errores
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"msg": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    # Usar exc_info=True para registrar el traceback completo
    app_logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({"msg": "Internal server error"}), 500

if __name__ == '__main__':
    app_logger.info("Starting Flask application in development mode...")
    app.run(debug=True, host='0.0.0.0', port=5000)