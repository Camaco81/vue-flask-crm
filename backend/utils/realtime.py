import time
from flask_socketio import SocketIO, emit, join_room, leave_room
from backend.db import get_db_cursor # Asumo que get_db_cursor devuelve un cursor estándar (tuplas)
from .inventory_utils import calculate_active_seasonality_alerts 

# Configuración básica de SocketIO
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
        with get_db_cursor(commit=True) as cur: 
            for alert_id in alert_ids:
                query = """
                INSERT INTO read_alerts (user_id, tenant_id, alert_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, alert_id) DO NOTHING;
                """
                cur.execute(query, (user_id, DEFAULT_TENANT_ID, alert_id))
            print(f"DEBUG: Alertas estacionales persistidas para {user_id}: {alert_ids}")

    except Exception as e:
        print(f"Error al guardar alertas leídas: {e}")

# 💡 NUEVA FUNCIÓN NECESARIA para marcar notificaciones estáticas como leídas
def mark_static_alerts_as_read(alert_uuids: list):
    """Marca las notificaciones estáticas (UUIDs) como leídas en la tabla 'notifications'."""
    if not alert_uuids:
        return
    
    try:
        with get_db_cursor(commit=True) as cur:
            # Marcamos is_read = TRUE donde el ID esté en la lista de UUIDs
            # Asegúrate de que tu tabla notifications tiene el campo `is_read`
            query = """
            UPDATE notifications 
            SET is_read = TRUE, read_at = NOW() 
            WHERE id IN %s; 
            """
            # El %s debe ser una tupla de valores para la cláusula IN
            cur.execute(query, (tuple(alert_uuids),))
            print(f"DEBUG: {cur.rowcount} notificaciones estáticas marcadas como leídas: {alert_uuids}")
            
    except Exception as e:
        print(f"Error al marcar notificaciones estáticas como leídas: {e}")


def get_read_alert_ids(user_id: str) -> set:
    """Obtiene todos los IDs de alertas estacionales que el usuario ya marcó como leídas."""
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
    """El usuario se une a una sala y se le envían sus notificaciones iniciales."""
    user_id = DEFAULT_USER_ID 
    
    # 💡 Nomenclatura de sala más clara
    room = f'user_dashboard_{user_id}' 
    join_room(room)
    print(f"DEBUG: Cliente unido al dashboard: {room}")
    
    # 1. Envía las alertas estacionales INICIALES
    send_initial_seasonality_alerts(user_id)
    
    # 2. Envía las notificaciones ESTÁTICAS que aún no ha leído
    send_initial_static_alerts(user_id)


@socketio.on('mark_as_read')
def handle_mark_as_read(data):
    """Recibe el evento de marcar como leídas y actualiza la base de datos."""
    user_id = DEFAULT_USER_ID
    alert_ids = data.get('alert_ids', []) # Lista de IDs estables o UUIDs estáticos

    # Separar IDs estacionales (estables, ejemplo: contienen el rol) y UUIDs (estáticos)
    stable_ids = [aid for aid in alert_ids if ALMACENISTA_ROL in str(aid)]
    static_uuids = [aid for aid in alert_ids if ALMACENISTA_ROL not in str(aid)] 

    if stable_ids:
        persist_read_alerts(user_id, stable_ids)
    
    if static_uuids:
        mark_static_alerts_as_read(static_uuids)


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
        room = f'user_dashboard_{user_id}'
        socketio.emit('new_alerts', {'alerts': unread_alerts}, room=room)
        print(f"DEBUG: Enviadas {len(unread_alerts)} alertas estacionales no leídas a {user_id}")
        
    except Exception as e:
        print(f"ERROR: Fallo al enviar alertas estacionales: {e}")
        
# 🚀 CORRECCIÓN APLICADA AQUÍ: Se accede a los resultados por índice numérico
def send_initial_static_alerts(user_id: str):
    """Envía las notificaciones estáticas (DB) no leídas."""
    try:
        with get_db_cursor() as cur:
            # 💡 NOTA IMPORTANTE: El orden de las columnas debe coincidir con el acceso por índice [0], [1], [2], [3]
            cur.execute("""
                SELECT id, mensaje, tipo, fecha_creacion
                FROM notifications 
                WHERE rol_destino = %s AND is_read = FALSE
                ORDER BY fecha_creacion DESC; 
            """, (ALMACENISTA_ROL,)) 
            
            static_alerts_tuples = cur.fetchall()
            
            # Formatear la tupla a diccionario para el frontend
            formatted_alerts = [{
                'id': alert[0],             # ID (UUID estático)
                'message': alert[1],        # Mensaje
                'type': alert[2],           # Tipo (stock_bajo, stock_critico)
                'timestamp': alert[3].timestamp() if alert[3] else time.time(), # Fecha de creación (convertir a timestamp)
                'rol_destino': ALMACENISTA_ROL
            } for alert in static_alerts_tuples]

        room = f'user_dashboard_{user_id}'
        socketio.emit('new_alerts', {'alerts': formatted_alerts}, room=room)
        print(f"DEBUG: Enviadas {len(formatted_alerts)} notificaciones estáticas no leídas.")
        
    except Exception as e:
        print(f"ERROR: Fallo al enviar notificaciones estáticas: {e}")