from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.utils.inventory_utils import calculate_active_seasonality_alerts, ALMACENISTA_ROL

alert_bp = Blueprint('alert', __name__, url_prefix='/api/alerts')

@alert_bp.route('/seasonal', methods=['GET'])
@jwt_required()
def get_seasonal_alerts():
    """Endpoint REST que usa la misma lógica que los WebSockets."""
    try:
        # Usamos la función unificada
        alerts = calculate_active_seasonality_alerts(ALMACENISTA_ROL)
        return jsonify(alerts), 200
    except Exception as e:
        return jsonify({"msg": "Error", "error": str(e)}), 500