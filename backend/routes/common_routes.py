from flask import Blueprint, jsonify
from backend.utils.bcv_api import get_dolarvzla_rate
from flask_cors import cross_origin
import time

# Definimos el blueprint
rate_bp = Blueprint('rate_bp', __name__)

@rate_bp.route('', methods=['GET']) # 💡 CORRECCIÓN: Se deja vacío porque el prefijo ya tiene '/api/exchange-rate'
@cross_origin()
def get_current_exchange_rate():
    """Devuelve la tasa de cambio actual USD a VES obtenida de la utilidad bcv_api."""
    try:
        # Llamamos a la utilidad que ya corregimos con la estructura {'current': {'usd': ...}}
        rate = get_dolarvzla_rate()
        
        # Si por alguna razón la utilidad devolviera None (aunque pusimos DEFAULT_RATE)
        if rate is None:
            raise ValueError("No se pudo obtener una tasa válida")

        return jsonify({
            "rate": rate,
            "source": "DolarVzla (BCV)",
            "timestamp": int(time.time()), # Timestamp real de la consulta
            "status": "success"
        }), 200

    except Exception as e:
        # Log interno para el desarrollador
        # app_logger.error(f"Error crítico en endpoint de tasa: {e}")
        
        # En caso de error crítico, devolvemos una tasa de emergencia (puedes ajustarla a la realidad actual)
        # 220 parece una tasa muy vieja comparada con el 341.74 del JSON que enviaste
        return jsonify({
            "msg": "Error al obtener la tasa. Usando tasa de respaldo del servidor.", 
            "rate": 340.0, # Tasa de emergencia cercana a la realidad
            "status": "fallback",
            "error": str(e)
        }), 500