import time
from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_jwt_extended import decode_token
from backend.db import get_db_cursor 
from .inventory_utils import calculate_active_seasonality_alerts, ALMACENISTA_ROL 

# Configuración de SocketIO
socketio = SocketIO(cors_allowed_origins="*", async_mode='gevent') 

# =========================================================
# Helpers de Identidad
# =========================================================

def get_user_id_from_socket():
    """
    Extrae el identity del JWT enviado en la conexión del Socket.
    Se espera que el cliente envíe el token en el objeto 'auth'.
    """
    try:
        # En el frontend: socket = io({ auth: { token: "..." } })
        token = request.get_json().get('token') if request.get_json() else None
        if not token:
            # Intento alternativo por headers si no viene en body
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            
        if token:
            decoded = decode_token(token)
            return decoded['sub']  # Aquí vendrá la 'cedula' o ID del usuario
    except Exception as e:
        print(f"DEBUG: No se pudo decodificar token en socket: {e}")
    return None

# =========================================================
# Lógica de Persistencia Dinámica
# =========================================================

def persist_read_alerts(user_id: str, alert_ids: list):
    if not alert_ids: return
    try:
        with get_db_cursor(commit=True) as cur: 
            for alert_id in alert_ids:
                # Usamos la cédula (user_id) para la persistencia individual
                query = """
                INSERT INTO read_alerts (user_id, alert_id)
                VALUES (%s, %s)
                ON CONFLICT (user_id, alert_id) DO NOTHING;
                """
                cur.execute(query, (user_id, alert_id))
    except Exception as e:
        print(f"Error al guardar alertas leídas: {e}")

def mark_static_alerts_as_read(alert_uuids: list):
    """Marca notificaciones en la tabla general."""
    if not alert_uuids: return
    try:
        with get_db_cursor(commit=True) as cur:
            query = "UPDATE notifications SET is_read = TRUE, read_at = NOW() WHERE id IN %s;"
            cur.execute(query, (tuple(alert_uuids),))
    except Exception as e:
        print(f"Error al marcar notificaciones estáticas: {e}")

def get_read_alert_ids(user_id: str) -> set:
    """Obtiene alertas leídas específicas para este usuario."""
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT alert_id FROM read_alerts WHERE user_id = %s;", (user_id,))
            return {row['alert_id'] for row in cur.fetchall()}
    except Exception as e:
        print(f"Error al obtener alertas leídas: {e}")
        return set()

# =========================================================
# Eventos de WebSockets
# =========================================================

@socketio.on('join_dashboard')
def on_join(data):
    """
    El cliente se une usando su token. 
    Se crea una sala privada 'user_dashboard_{cedula}'
    """
    # Intentamos obtener el user_id del token enviado en data o auth
    token = data.get('token')
    try:
        decoded = decode_token(token)
        user_id = decoded['sub'] # ID/Cédula real del usuario
        
        room = f'user_dashboard_{user_id}' 
        join_room(room)
        
        print(f"DEBUG: Almacenista {user_id} se unió a su sala privada.")
        
        # Enviar alertas personalizadas para este usuario específico
        send_initial_seasonality_alerts(user_id)
        send_initial_static_alerts(user_id)
        
    except Exception as e:
        print(f"Error de autenticación en join_dashboard: {e}")

@socketio.on('mark_as_read')
def handle_mark_as_read(data):
    """Procesa el marcado de lectura usando el ID dinámico."""
    token = data.get('token')
    try:
        decoded = decode_token(token)
        user_id = decoded['sub']
        alert_ids = data.get('alert_ids', [])

        # Separar estacionales de estáticas
        stable_ids = [aid for aid in alert_ids if ALMACENISTA_ROL in str(aid)]
        static_uuids = [aid for aid in alert_ids if ALMACENISTA_ROL not in str(aid)] 

        if stable_ids:
            persist_read_alerts(user_id, stable_ids)
        if static_uuids:
            mark_static_alerts_as_read(static_uuids)
            
    except Exception as e:
        print(f"Error en mark_as_read: {e}")

# =========================================================
# Emisión de Alertas
# =========================================================

def send_initial_seasonality_alerts(user_id: str):
    """Calcula alertas según el rol pero filtra por el historial del usuario."""
    try:
        all_alerts = calculate_active_seasonality_alerts(ALMACENISTA_ROL)
        read_alert_ids = get_read_alert_ids(user_id)
        
        # Filtrar: Solo lo que este usuario específico no ha leído
        unread_alerts = [a for a in all_alerts if a['id'] not in read_alert_ids]

        room = f'user_dashboard_{user_id}'
        socketio.emit('new_alerts', {'alerts': unread_alerts}, room=room)
        
    except Exception as e:
        print(f"ERROR Estacionales: {e}")
        
def send_initial_static_alerts(user_id: str):
    """Notificaciones de la DB dirigidas al rol Almacenista."""
    try:
        with get_db_cursor() as cur:
            # Filtramos por rol_destino para que todos los almacenistas las vean, 
            # pero el estado is_read debería ser gestionado con cuidado si es compartido.
            cur.execute("""
                SELECT id, mensaje, tipo, fecha_creacion
                FROM notifications 
                WHERE rol_destino = %s AND is_read = FALSE
                ORDER BY fecha_creacion DESC; 
            """, (ALMACENISTA_ROL,)) 
            
            static_alerts = cur.fetchall()
            formatted_alerts = [{
                'id': alert['id'], 
                'message': alert['mensaje'], 
                'type': alert['tipo'],
                'timestamp': alert['fecha_creacion'].timestamp() if alert['fecha_creacion'] else time.time()
            } for alert in static_alerts]

        room = f'user_dashboard_{user_id}'
        socketio.emit('new_alerts', {'alerts': formatted_alerts}, room=room)
        
    except Exception as e:
        print(f"ERROR Estáticas: {e}")