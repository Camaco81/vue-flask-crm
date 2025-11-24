# =========================================================
# ARCHIVO: backend/routes/alert_routes.py 
# =========================================================

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
# Importar la función que creamos en el archivo de utilidades
from backend.utils.seasonal_alerts import get_active_seasonal_alerts 

alert_bp = Blueprint('alert', __name__, url_prefix='/api/alerts')

@alert_bp.route('/seasonal', methods=['GET'])
@jwt_required()
def get_seasonal_alerts():
    """
    Endpoint para obtener alertas de stock bajo basadas SÓLO en la temporada actual.
    """
    try:
        active_alerts = get_active_seasonal_alerts()
        # Devolver la lista de alertas activas
        return jsonify(active_alerts), 200
        
    except Exception as e:
        # Devolver una lista vacía en caso de error
        return jsonify({"msg": "Error al obtener alertas estacionales", "error": str(e)}), 500

# ⚠️ ¡IMPORTANTE! No olvides registrar este Blueprint en tu archivo principal de Flask (e.g., app.py):
# app.register_blueprint(alert_bp)