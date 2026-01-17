try:
    from gevent import monkey
    monkey.patch_all()
except ImportError:
    pass

from flask import Flask, jsonify, request
import logging
import os 
from .utils.realtime import socketio
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
from flask_apscheduler import APScheduler 
from backend.utils.inventory_utils import verificar_tendencia_y_alertar
from backend.config import Config

# Blueprints
from backend.auth import auth_bp
from backend.routes.customer_routes import customer_bp
from backend.routes.product_routes import product_bp
from backend.routes.sale_routes import sale_bp
from backend.routes.user_routes import user_bp, admin_bp
from backend.routes.common_routes import rate_bp
from backend.routes.alert_routes import alert_bp

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
app_logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config) 

jwt = JWTManager(app)

# SocketIO
try:
    socketio.init_app(app, cors_allowed_origins="*")
    app_logger.info("Flask-SocketIO inicializado.")
except Exception as e:
    app_logger.error(f"Error al inicializar SocketIO: {e}")

# CORS - Configuración Robusta
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Scheduler
scheduler = APScheduler()
scheduler.init_app(app)
if not scheduler.running:
    scheduler.start()
    scheduler.add_job(
       id='verificar_alertas_estacionales',
       func=verificar_tendencia_y_alertar,
       trigger='cron',
       hour=0,
       minute=0
    )

# --- REGISTRO DE RUTAS (CORREGIDO) ---
# Quité los prefijos de los Blueprints internos para manejarlos aquí centralizados
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(customer_bp, url_prefix='/api/customers')
app.register_blueprint(product_bp, url_prefix='/api/products')
app.register_blueprint(sale_bp, url_prefix='/api/sales') # Centralizado aquí
app.register_blueprint(alert_bp, url_prefix='/api/alerts')
app.register_blueprint(rate_bp, url_prefix='/api/exchange-rate')
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(admin_bp, url_prefix='/api/admin')

@app.route('/')
def index():
    return jsonify({"status": "online", "message": "Sales API is running"}), 200

@app.errorhandler(404)
def not_found_error(error):
    app_logger.warning(f"404 Not Found: {request.path}") 
    return jsonify({"msg": "Resource not found", "path": request.path}), 404

@app.errorhandler(500)
def internal_error(error):
    app_logger.error(f"500 Error: {error}", exc_info=True)
    return jsonify({"msg": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)