from flask import Flask, jsonify, request
import logging
import os 

# --- Importaciones de Librerías Externas ---
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
from flask_apscheduler import APScheduler 

# --- Importaciones de Módulos Locales (Absolutas) ---
from backend.config import Config
from backend.utils.inventory_utils import verificar_tendencia_y_alertar

# Blueprints (Rutas)
from backend.auth import auth_bp
from backend.routes.customer_routes import customer_bp
from backend.routes.product_routes import product_bp
from backend.routes.sale_routes import sale_bp
# user_bp contiene /profile; admin_bp contiene /users
from backend.routes.user_routes import user_bp, admin_bp
from backend.routes.common_routes import rate_bp


# --- 1. CONFIGURACIÓN INICIAL (LOAD ENV) ---
# Debe ser lo primero para cargar las variables de entorno antes de la configuración de la app
load_dotenv()

# --- 2. CONFIGURACIÓN DE LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
app_logger = logging.getLogger(__name__)

# --- 3. INICIALIZACIÓN DE LA APLICACIÓN Y CONFIGURACIÓN ---
app = Flask(__name__)
# Cargar configuración desde el objeto Config
app.config.from_object(Config) 

# Inicializar extensiones
jwt = JWTManager(app)

# Configurar CORS (Permisivo para desarrollo)
CORS(
    app, 
    origins="*", # Permite cualquier origen (debería ser suficiente)
    supports_credentials=True, # Permitir cookies, tokens de autorización, etc.
    # 💡 Añadir headers que usa tu frontend (Authorization para JWT)
    allow_headers=["Content-Type", "Authorization"], 
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"] # Permitir todos los métodos
)

# --- 4. CONFIGURACIÓN Y TAREA PROGRAMADA (SCHEDULER) ---
scheduler = APScheduler()
scheduler.init_app(app)

# Asegurarse de que el scheduler se inicie una sola vez
if not scheduler.running:
    scheduler.start()
    app_logger.info("Scheduler iniciado.")

    # Definición de la tarea programada: Verificar tendencias diarias a las 02:00 AM
    scheduler.add_job(
        id='verificar_alertas_estacionales',
        func=verificar_tendencia_y_alertar,
        trigger='cron',
        hour=2,
        minute=0,
    )
    app_logger.info("Tarea de alertas estacionales programada para las 02:00 AM.")

# --- 5. REGISTRO DE BLUEPRINTS (RUTAS) ---

# Rutas API Generales (con prefijo /api)
# Rutas finales: /api/auth/*, /api/customers/*, /api/products/*, /api/sales/*
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(customer_bp, url_prefix='/api/customers')
app.register_blueprint(product_bp, url_prefix='/api/products')
app.register_blueprint(sale_bp, url_prefix='/api/sales') 

# Rutas que están directamente bajo /api (ej. /api/profile, /api/rate)
app.register_blueprint(rate_bp, url_prefix='/api')
app.register_blueprint(user_bp, url_prefix='/api') # Contiene /profile

# Rutas de administración (con prefijo /admin)
# Ruta final: /admin/users
app.register_blueprint(admin_bp, url_prefix='/admin')


# Ruta de prueba simple
@app.route('/')
def index():
    """Ruta de salud simple para verificar que la aplicación está corriendo."""
    return "Welcome to the Sales API!"

# --- 6. MANEJADORES DE ERRORES ---

@app.errorhandler(404)
def not_found_error(error):
    """Maneja el error 404 (Recurso no encontrado)."""
    app_logger.warning(f"404 Not Found: Path accessed: {request.path}") 
    return jsonify({"msg": "Resource not found", "error_code": 404}), 404

@app.errorhandler(500)
def internal_error(error):
    """Maneja el error 500 (Error interno del servidor)."""
    # Se utiliza exc_info=True para registrar el traceback completo del error
    app_logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({"msg": "Internal server error", "error_code": 500}), 500

# --- 7. EJECUCIÓN DEL SERVIDOR ---

if __name__ == '__main__':
    app_logger.info("Starting Flask application...")
    # Usar variables de entorno para puerto y host (buena práctica para despliegue)
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", '0.0.0.0')
    app.run(debug=Config.DEBUG, host=host, port=port)