import time
from flask import request
from flask_socketio import SocketIO, emit, join_room
from flask_jwt_extended import decode_token
from .inventory_utils import calculate_active_seasonality_alerts, ALMACENISTA_ROL, save_read_alert

# Configuración de SocketIO
socketio = SocketIO(cors_allowed_origins="*", async_mode='gevent') 

@socketio.on('join_dashboard')
def on_join(data):
    token = data.get('token')
    if not token: return
    
    try:
        decoded = decode_token(token)
        user_id = decoded['sub'] # ID/Cédula
        # Asumimos que el rol viene en los claims del token
        role_id = decoded.get('role_id', ALMACENISTA_ROL) 
        
        room = f'user_dashboard_{user_id}' 
        join_room(room)
        
        # Enviamos alertas iniciales
        unread_alerts = calculate_active_seasonality_alerts(user_id, role_id)
        emit('new_alerts', {'alerts': unread_alerts}, room=room)
        
    except Exception as e:
        print(f"Error en join_dashboard: {e}")

@socketio.on('mark_as_read')
def handle_mark_as_read(data):
    token = data.get('token')
    alert_ids = data.get('alert_ids', [])
    
    try:
        decoded = decode_token(token)
        user_id = decoded['sub']

        for aid in alert_ids:
            save_read_alert(user_id, aid)
            
        print(f"DEBUG: Alertas leídas por {user_id}")
    except Exception as e:
        print(f"Error en mark_as_read: {e}")

def send_seasonality_alerts(user_id, role_id):
    """Función para emitir alertas manualmente (ej: tras una venta)"""
    try:
        unread_alerts = calculate_active_seasonality_alerts(user_id, role_id)
        room = f'user_dashboard_{user_id}'
        socketio.emit('new_alerts', {'alerts': unread_alerts}, room=room)
    except Exception as e:
        print(f"Error emitiendo alertas: {e}")