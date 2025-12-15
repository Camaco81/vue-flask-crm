import time
from flask_socketio import SocketIO, emit, join_room
from backend.db import get_db_cursor
from .inventory_utils import calculate_active_seasonality_alerts 

# Configuración básica de SocketIO
# Debes integrar esto en tu __init__.py de Flask
socketio = SocketIO(cors_allowed_origins="*", async_mode='gevent') 

# IDs Fijos para la demo (Single Tenant)
DEFAULT_USER_ID = 'almacenista_unico_cliente_12345' 
DEFAULT_TENANT_ID = 'default_tenant_001' 
ALMACENISTA_ROL = 'almacenista'

# =========================================================
# Lógica de Persistencia (Marcar como Leído)
# =========================================================

def persist_read_alerts(user_id: str, alert_ids: list):
    """Guarda los IDs de alertas estacionales marcadas como leídas en la DB."""
    if not alert_ids:
        return
        
    try:
        # Usamos el tenant_id por defecto para el cursor
        with get_db_cursor(commit=True) as cur: 
            for alert_id in alert_ids:
                query = """
                INSERT INTO read_alerts (user_id, tenant_id, alert_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, alert_id) DO NOTHING;
                """
                # Asumo que el tenant_id es accesible desde la sesión o es fijo (como aquí)
                cur.execute(query, (user_id, DEFAULT_TENANT_ID, alert_id))
            print(f"DEBUG: Alertas persistidas para {user_id}: {alert_ids}")

    except Exception as e:
        print(f"Error al guardar alertas leídas: {e}")


def get_read_alert_ids(user_id: str) -> set:
    """Obtiene todos los IDs de alertas que el usuario ya marcó como leídas."""
    try:
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT alert_id FROM read_alerts 
                WHERE user_id = %s AND tenant_id = %s;
            """, (user_id, DEFAULT_TENANT_ID))
            
            return {row[0] for row in cur.fetchall()}
    except Exception as e:
        print(f"Error al obtener alertas leídas: {e}")
        return set()

# =========================================================
# WebSockets Events
# =========================================================

@socketio.on('join_dashboard')
def on_join(data):
    """El usuario se une a una sala para recibir sus notificaciones."""
    user_id = DEFAULT_USER_ID 
    
    room = f'user_{user_id}' 
    join_room(room)
    print(f"DEBUG: Usuario {user_id} unido a la sala: {room}")
    
    # 1. Envía las alertas estacionales INICIALES
    send_initial_seasonality_alerts(user_id)
    
    # 2. Envía las notificaciones ESTÁTICAS que aún no ha leído
    send_initial_static_alerts(user_id)


@socketio.on('mark_as_read')
def handle_mark_as_read(data):
    """Recibe el evento de marcar como leídas y actualiza la base de datos."""
    user_id = DEFAULT_USER_ID
    alert_ids = data.get('alert_ids', []) # Lista de IDs estables o UUIDs

    # Solo persistimos las alertas estacionales (IDs estables)
    stable_ids = [aid for aid in alert_ids if ALMACENISTA_ROL in aid] # Filtro simple por ahora
    
    if stable_ids:
        persist_read_alerts(user_id, stable_ids)
    
    # NOTA: Si también quieres marcar las notificaciones estáticas como leídas:
    # Debes implementar la lógica SQL aquí para actualizar la columna `is_read`
    # en la tabla `notifications` usando los UUIDs proporcionados.


# =========================================================
# Lógica de Emisión de Alertas
# =========================================================

def send_initial_seasonality_alerts(user_id: str):
    """Envía las alertas estacionales no leídas."""
    try:
        with get_db_cursor() as cur:
            # 1. Calcular todas las alertas que APLICAN ESTE MES
            all_alerts = calculate_active_seasonality_alerts(cur, ALMACENISTA_ROL)
            
        # 2. Obtener los IDs de las alertas que ya leyó el usuario
        read_alert_ids = get_read_alert_ids(user_id)
        
        # 3. Filtrar las alertas para determinar cuáles NO han sido leídas
        unread_alerts = [
            alert for alert in all_alerts 
            if alert['id'] not in read_alert_ids
        ]

        # 4. Enviar solo las no leídas
        room = f'user_{user_id}'
        socketio.emit('new_alerts', {'alerts': unread_alerts}, room=room)
        print(f"DEBUG: Enviadas {len(unread_alerts)} alertas estacionales no leídas a {user_id}")
        
    except Exception as e:
        print(f"ERROR: Fallo al enviar alertas estacionales: {e}")
        

def send_initial_static_alerts(user_id: str):
    """Envía las notificaciones estáticas (DB) no leídas."""
    try:
        with get_db_cursor() as cur:
            # Asumo que tienes una forma de obtener las notificaciones no leídas
            # Aquí podrías consultar la tabla `notifications` por `rol_destino` y `is_read = FALSE`
            cur.execute("""
                SELECT id, mensaje, tipo, referencia_id 
                FROM notifications 
                WHERE rol_destino = %s AND is_read = FALSE;
            """, (ALMACENISTA_ROL,)) 
            
            static_alerts = cur.fetchall()
            
            # Formatear a la estructura de alerta si es necesario, y emitir:
            formatted_alerts = [{
                'id': alert['id'], # UUID de la tabla notifications
                'message': alert['mensaje'],
                'type': alert['tipo'],
                'timestamp': time.time(), # Usar la fecha de creación si está disponible
                'rol_destino': ALMACENISTA_ROL
            } for alert in static_alerts]

        room = f'user_{user_id}'
        socketio.emit('new_alerts', {'alerts': formatted_alerts}, room=room)
        print(f"DEBUG: Enviadas {len(formatted_alerts)} notificaciones estáticas no leídas.")
        
    except Exception as e:
        print(f"ERROR: Fallo al enviar notificaciones estáticas: {e}")

# NOTA: Deberías modificar tu función `create_notification` para llamar 
# a `broadcast_new_alert` cada vez que se cree una nueva notificación estática 
# (ej. stock bajo) para enviarla en tiempo real.