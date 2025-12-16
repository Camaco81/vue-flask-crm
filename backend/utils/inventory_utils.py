from backend.db import get_db_cursor, get_dict_cursor # 💡 ASUMO QUE TIENES UN get_dict_cursor
import uuid
from datetime import date
import logging
import time
import re # 💡 CORRECCIÓN 1: Se añade la importación de 're'

# Importar SocketIO si vas a emitir desde aquí (actualmente no lo haces)
# from .realtime import socketio 

STOCK_THRESHOLD = 10 
ALMACENISTA_ROL = 'almacenista' # Definir el rol aquí para evitar circular references

# Configura tu logger si es necesario
inv_logger = logging.getLogger('backend.utils.inventory_utils')

def create_notification(rol_destino: str, mensaje: str, tipo: str, referencia_id: str = None):
    """Inserta una nueva notificación en la base de datos."""
    # NOTA: La emisión en tiempo real debe hacerse AQUI después de cur.execute()
    # Pero por ahora, solo insertaremos.
    try:
        new_id = str(uuid.uuid4())
        # Usamos el cursor normal, pero debe poder recibir dicts si tu DB lo soporta
        with get_db_cursor(commit=True) as cur: 
            cur.execute(
                """
                INSERT INTO notifications (id, rol_destino, mensaje, tipo, referencia_id, is_read, fecha_creacion)
                VALUES (%s, %s, %s, %s, %s, FALSE, NOW())
                """,
                (new_id, rol_destino, mensaje, tipo, referencia_id)
            )
        print(f"Notificación estática creada: {mensaje}")
        # 💡 LÓGICA DE EMISIÓN DEBE IR AQUÍ:
        # from .realtime import broadcast_new_alert 
        # broadcast_new_alert(new_id, rol_destino, mensaje, tipo, time.time())
    except Exception as e:
        print(f"Error al crear notificación: {e}")
        inv_logger.error(f"Error al crear notificación: {e}", exc_info=True)


# Función auxiliar para generar IDs estables (necesaria para `read_alerts`)
def get_alert_stable_id(event_name: str, tipo: str) -> str:
    """
    Genera un ID único y estable basado en el evento y tipo de alerta. 
    Esto garantiza que el estado 'leído' persista en la DB.
    """
    safe_name = re.sub(r'[^\w\s-]', '', event_name).strip().lower()
    safe_name = re.sub(r'[-\s]+', '_', safe_name)
    return f"{ALMACENISTA_ROL}_{safe_name}_{tipo}"


def verificar_tendencia_y_alertar():
    """
    VERSIÓN SCHEDULER: Se ejecuta diariamente. Consulta la tabla seasonality_events.
    Genera y persiste notificaciones estáticas (notifications).
    """
    current_month = date.today().month
    
    # 1. Obtener todas las reglas de estacionalidad activas para el mes actual
    try:
        # 💡 CORRECCIÓN 2: Usar get_dict_cursor para acceder por nombre de columna
        with get_dict_cursor() as cur: 
            # Consulta la tabla de estacionalidad que creaste
            cur.execute("""
                SELECT 
                    event_name, alert_type, product_category, stock_threshold, message_template
                FROM seasonality_events
                WHERE active_month = %s;
            """, (current_month,))
            
            active_rules = cur.fetchall()
            
    except Exception as e:
        inv_logger.error(f"Error al consultar reglas de estacionalidad: {e}", exc_info=True)
        return

    # 2. Verificar los productos contra cada regla activa
    for rule in active_rules:
        
        # 3. Consulta SQL: Busca productos de la categoría activa con stock bajo el umbral de temporada
        # Usamos el cursor de la primera consulta ya que es un DictCursor
        query = """
        SELECT id, name, stock_actual, category
        FROM products
        WHERE category = %s AND stock_actual < %s
        """
        
        try:
            with get_dict_cursor() as cur: 
                cur.execute(query, (rule['product_category'], rule['stock_threshold']))
                productos_criticos = cur.fetchall()

                # 4. Generar una alerta por cada producto encontrado
                for product in productos_criticos:
                    mensaje = (
                        f"🔔 Aviso de Temporada ({rule['event_name']}): El producto "
                        f"'{product['name']}' (Cat: {rule['product_category']}) tiene stock bajo "
                        f"({product['stock_actual']} uds) para la demanda proyectada. ¡Reponer!"
                    )
                    
                    # Persistir la alerta en la tabla 'notifications' (Alerta Estática)
                    create_notification(
                        rol_destino=ALMACENISTA_ROL,
                        mensaje=mensaje,
                        tipo=rule['alert_type'],
                        referencia_id=product['id']
                    )
                    inv_logger.info(f"Alerta de Tendencia generada para: {product['name']}")

        except Exception as e:
            inv_logger.error(f"Error en verificación de productos (SQL): {e}", exc_info=True)

# =========================================================
# Lógica para SocketIO (Carga Inicial)
# =========================================================

def calculate_active_seasonality_alerts(rol_destino: str) -> list:
    """
    VERSIÓN SOCKETIO: Consulta la tabla seasonality_events.
    Devuelve la lista de objetos de alerta con su ID estable (para read_alerts),
    SIN guardarlas en la DB, ya que son alertas recurrentes por mes.
    """
    current_month = date.today().month
    active_alerts = []
    
    # 1. Obtener todas las reglas de estacionalidad activas para el mes actual
    try:
        # 💡 CORRECCIÓN 3: Usar get_dict_cursor para esta consulta también
        with get_dict_cursor() as cur: 
            cur.execute("""
                SELECT 
                    event_name, alert_type, product_category, stock_threshold, message_template
                FROM seasonality_events
                WHERE active_month = %s;
            """, (current_month,))
            
            active_rules = cur.fetchall()
            
    except Exception as e:
        inv_logger.error(f"Error al consultar reglas de estacionalidad para SocketIO: {e}", exc_info=True)
        return []

    # Mapeo de eventos para agrupar categorías
    events_map = {} # {'Navidad e Iluminación': {'rules': [], 'productos_criticos': []}}

    # 2. Procesar las reglas y buscar productos críticos
    for rule in active_rules:
        event_name = rule['event_name']
        
        # Inicializar el mapa para el evento si no existe
        if event_name not in events_map:
             events_map[event_name] = {
                'event_name': event_name,
                'tipo': rule['alert_type'],
                'stock_threshold': rule['stock_threshold'],
                'message_template': rule['message_template'],
                'categories': [],
                'productos_criticos_info': [],
                'is_triggered': False
            }
        
        # 2a. Recolectar productos críticos para esta regla de categoría
        query = """
        SELECT name, stock_actual
        FROM products
        WHERE category = %s AND stock_actual < %s
        """
        
        try:
            with get_dict_cursor() as cur:
                cur.execute(query, (rule['product_category'], rule['stock_threshold']))
                productos_criticos = cur.fetchall()

                if productos_criticos:
                    events_map[event_name]['is_triggered'] = True
                    for product in productos_criticos:
                        info = f"'{product['name']}' ({product['stock_actual']} uds)"
                        events_map[event_name]['productos_criticos_info'].append(info)
        except Exception as e:
             inv_logger.error(f"Error SQL en calculate_active_seasonality_alerts: {e}", exc_info=True)

        events_map[event_name]['categories'].append(rule['product_category'])


    # 3. Generar el objeto de alerta final
    for event_data in events_map.values():
        
        # 5. Si la alerta se disparó (stock bajo) o es de promoción (siempre aplica)
        if event_data['is_triggered'] or event_data['tipo'] == 'promocion_baja':
            
            # Generar el ID estable para este evento de temporada (Para el sistema read_alerts)
            stable_id = get_alert_stable_id(event_data['event_name'], event_data['tipo'])

            # Resumen para el mensaje final
            if event_data['productos_criticos_info']:
                unique_products = list(set(event_data['productos_criticos_info'])) # Evitar duplicados si una regla tiene varias categorías
                alert_summary = f"Productos críticos: {', '.join(unique_products[:3])}"
                if len(unique_products) > 3:
                    alert_summary += f" y {len(unique_products) - 3} más."
            else:
                alert_summary = "Revisa las categorías sugeridas para anticiparte."
            
            # Construcción del mensaje principal basado en la plantilla
            categories_list_str = ", ".join(event_data['categories'])
            final_message = event_data['message_template'].format(
                event=event_data['event_name'],
                categories_list=categories_list_str,
                threshold=event_data['stock_threshold']
            )

            # Creamos el objeto de alerta que enviaremos por WebSocket
            active_alerts.append({
                "id": stable_id, # EL ID ESTABLE es la clave para la tabla read_alerts
                "message": final_message,
                "type": event_data['tipo'],
                "timestamp": time.time(), # Usar NOW() de la DB si fuera una tabla
                "summary": alert_summary,
                "rol_destino": rol_destino
            })
            
    return active_alerts