from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import logging

from config import Config
from auth import auth_bp
from routes.customer_routes import customer_bp
from routes.product_routes import product_bp
from routes.sale_routes import sale_bp


# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
app_logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar JWT
jwt = JWTManager(app)

# Configurar CORS para permitir peticiones desde tu frontend
CORS(app, resources={r"/api/*": {"origins": "*"}}) # Ajusta esto a la URL de tu frontend en producción

# Registrar Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(product_bp)
app.register_blueprint(sale_bp) # Registrar el Blueprint de ventas

# Ruta de prueba simple
@app.route('/')
def index():
    return "Welcome to the Sales API!"

# Manejador de errores general (opcional, para capturar excepciones no manejadas)
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"msg": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    app_logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({"msg": "Internal server error"}), 500


if __name__ == '__main__':
    # Esto es solo para desarrollo. En producción, usa un servidor WSGI como Gunicorn.
    app_logger.info("Starting Flask application in development mode...")
    app.run(debug=True, host='0.0.0.0', port=5000)