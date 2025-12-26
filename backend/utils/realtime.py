import time
from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_jwt_extended import decode_token
from backend.db import get_db_cursor 
# Importamos las funciones actualizadas
from .inventory_utils import calculate_active_seasonality_alerts, ALMACENISTA_ROL, save_read_alert

# Configuración de SocketIO
socketio = SocketIO(cors_allowed_origins="*", async_mode='gevent') 

# =========================================================
# Helpers de Identidad
# =========================================================

def get_user_id_from_socket():
    """Extrae el identity del JWT."""
    try:
        token = request.get_json().get('token') if request.get_json() else None
        if not token:
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token:
            decoded = decode_token(token)
            return decoded['sub']
    except Exception as e:
        print(f"DEBUG: No se pudo decodificar token: {e}")
    return None

# =========================================================
# Eventos de WebSockets
# =========================================================

@socketio.on('join_dashboard')
def on_join(data):
    """
    El cliente se une y recibe sus alertas pendientes de la tabla notifications.
    """
    token = data.get('token')
    try:
        decoded = decode_token(token)
        user_id = decoded['sub'] # Cédula del usuario
        
        room = f'user_dashboard_{user_id}' 
        join_room(room)
        
        print(f"DEBUG: Almacenista {user_id} se unió a su sala privada.")
        
        # Llamamos a la nueva lógica unificada
        send_seasonality_alerts(user_id)
        
    except Exception as e:
        print(f"Error de autenticación en join_dashboard: {e}")

@socketio.on('mark_as_read')
def handle_mark_as_read(data):
    """
    Procesa el marcado de lectura. 
    Ahora guarda la relación en la tabla read_alerts vinculada a notifications.
    """
    token = data.get('token')
    alert_ids = data.get('alert_ids', [])
    
    try:
        decoded = decode_token(token)
        user_id = decoded['sub']

        for aid in alert_ids:
            # Usamos la función de utilidad para marcar como leída
            save_read_alert(user_id, aid)
            
        print(f"DEBUG: Alertas {alert_ids} marcadas como leídas por {user_id}")
            
    except Exception as e:
        print(f"Error en mark_as_read: {e}")

# =========================================================
# Emisión de Alertas
# =========================================================

def send_seasonality_alerts(user_id: str):
    """
    Usa la lógica de inventory_utils para traer alertas de la DB
    que este usuario específico aún no ha leído.
    """
    try:
        # CORRECCIÓN: Pasamos user_id y ALMACENISTA_ROL (los 2 argumentos requeridos)
        unread_alerts = calculate_active_seasonality_alerts(user_id, ALMACENISTA_ROL)

        room = f'user_dashboard_{user_id}'
        # Emitimos el resultado al frontend
        socketio.emit('new_alerts', {'alerts': unread_alerts}, room=room)
        
        print(f"DEBUG: Enviadas {len(unread_alerts)} alertas a la sala {room}")
        
    except Exception as e:
        # Aquí es donde salía el error de "missing 1 required positional argument"
        print(f"ERROR al enviar alertas: {e}")