from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import logging

from config import Config
from auth import auth_bp
from routes.customer_routes import customer_bp
from routes.product_routes import product_bp
from routes.sale_routes import sale_bp
# from auth import auth_bp  <-- Antiguo
from backend.auth import auth_bp # <-- Nuevo

# from routes import all_blueprints <-- Antiguo
from backend.routes import all_blueprints # <-- Nuevo

from backend.config import Config # <-- Nuevo
from backend.db import get_db_connection # Si necesitas usarlo directamente en app.py

# Si estás cargando .env, asegúrate de que esté en la raíz del proyecto o accesible
# from dotenv import load_dotenv; load_dotenv()


# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
app_logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar JWT
jwt = JWTManager(app)

# Configurar CORS para permitir peticiones desde tu frontend
# app.py (fragmento)

from flask_cors import CORS

app = Flask(__name__)

# Configura CORS para permitir tu frontend local y el de producción
CORS(
    app, 
    # Añade los orígenes permitidos aquí
    origins=["http://localhost:8080", "https://vue-flask-crm.onrender.com"],
    supports_credentials=True # Necesario si usas cookies o encabezados de autorización
)

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