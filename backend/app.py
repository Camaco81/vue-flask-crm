from flask import Flask, jsonify, request
import logging
import os 
from .utils.realtime import socketio # 💡 IMPORTANTE: La instancia de socketio
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
from backend.routes.alert_routes import alert_bp


# --- 1. CONFIGURACIÓN INICIAL (LOAD ENV) ---
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

# 🚀 CORRECCIÓN CLAVE: CONECTAR SOCKETIO A LA APLICACIÓN
# Esto registra la ruta /socket.io/ que faltaba, resolviendo el 404.
try:
    socketio.init_app(app)
    app_logger.info("Flask-SocketIO inicializado y conectado a la aplicación.")
except Exception as e:
    app_logger.error(f"Error al inicializar SocketIO: {e}")


CORS(
    app, 
    # Usar la lista de orígenes
    origins="*", 
    supports_credentials=True, 
    allow_headers=["Content-Type", "Authorization"], 
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
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
app.register_blueprint( alert_bp)
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
    # Esta advertencia es la que vimos que Flask emitía antes. Ahora debería ser menos común para /socket.io/
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
    
    # ❌ IMPORTANTE: No usar app.run() para SocketIO con Gunicorn en producción
    # Esta sección solo se usa si ejecutas el archivo directamente para debug local
    # En producción, Gunicorn ejecutará: gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 --bind 0.0.0.0:$PORT backend.app:app
    
    app.run(debug=Config.DEBUG, host=host, port=port)