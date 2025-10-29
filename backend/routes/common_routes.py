# En backend/routes/common_routes.py

from flask import Blueprint, jsonify
from backend.utils.bcv_api import get_dolarvzla_rate
from flask_cors import cross_origin

rate_bp = Blueprint('rate_bp', __name__, url_prefix='/api')

@rate_bp.route('/exchange-rate', methods=['GET'])
@cross_origin() # Si usas CORS, asegúrate de permitir esta ruta
def get_current_exchange_rate():
    """Devuelve la tasa de cambio actual USD a VES."""
    try:
        rate = get_dolarvzla_rate()
        return jsonify({
            "rate": rate,
            "source": "DolarVzla",
            "timestamp": int(rate) # En un sistema real usarías time.time()
        }), 200
    except Exception as e:
        # En caso de error crítico en el servidor, devuelve una tasa de respaldo con error
        return jsonify({"msg": "Error al obtener la tasa. Usando tasa de respaldo.", "rate": 220}), 500

# 🚨 Asegúrate de registrar este Blueprint en tu archivo app.py:
# app.register_blueprint(rate_bp)