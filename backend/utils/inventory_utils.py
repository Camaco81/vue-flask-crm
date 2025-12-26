from backend.db import get_db_cursor
import uuid
from datetime import date
import logging
import time
import re

# Constantes para lógica de negocio
STOCK_THRESHOLD = 10 
ALMACENISTA_ROL = 'almacenista' 

inv_logger = logging.getLogger('backend.utils.inventory_utils')

def get_alert_stable_id(event_name: str, category: str) -> str:
    """
    Genera un ID único para una combinación de evento y categoría.
    Esto permite que 'Navidad - Iluminación' y 'Navidad - Decoración' sean distintas.
    """
    safe_event = re.sub(r'[^\w]', '', event_name).lower()
    safe_cat = re.sub(r'[^\w]', '', category).lower()
    return f"alert_{safe_event}_{safe_cat}_{date.today().strftime('%Y%m%d')}"

def create_notification(rol_destino: str, mensaje: str, tipo: str, referencia_id: str = None):
    """
    Inserta una notificación física en la base de datos para persistencia.
    """
    new_id = str(uuid.uuid4())
    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO notifications (id, rol_destino, mensaje, tipo, referencia_id, is_read, fecha_creacion)
                VALUES (%s, %s, %s, %s, %s, FALSE, NOW())
            """, (new_id, rol_destino, mensaje, tipo, referencia_id))
            return new_id
    except Exception as e:
        inv_logger.error(f"Error persistiendo notificación: {e}")
        return None

def verificar_stock_y_alertar():
    """
    Worker que llena la tabla 'notifications'. 
    Crea una notificación separada por cada categoría que esté baja de stock.
    """
    current_month = date.today().month
    try:
        with get_db_cursor() as cur:
            # 1. Obtenemos las reglas del JSON/Tabla seasonality_events
            cur.execute("""
                SELECT event_name, alert_type, product_category, stock_threshold, message_template 
                FROM seasonality_events WHERE active_month = %s
            """, (current_month,))
            rules = cur.fetchall()

            for rule in rules:
                # 2. Buscamos productos para esta categoría específica
                cur.execute("""
                    SELECT name, stock FROM products 
                    WHERE category = %s AND stock < %s
                """, (rule['product_category'], rule['stock_threshold']))
                products = cur.fetchall()

                if products:
                    # Generamos un mensaje específico para esta categoría
                    p_names = ", ".join([p['name'] for p in products])
                    mensaje = rule['message_template'].format(
                        event=rule['event_name'],
                        categories_list=rule['product_category'],
                        threshold=rule['stock_threshold']
                    )
                    full_msg = f"{mensaje} | Items: {p_names}"
                    
                    # Referencia única para no duplicar hoy
                    ref_id = get_alert_stable_id(rule['event_name'], rule['product_category'])
                    
                    # Evitar duplicados en la tabla notifications para el mismo día
                    cur.execute("SELECT id FROM notifications WHERE referencia_id = %s", (ref_id,))
                    if not cur.fetchone():
                        create_notification(ALMACENISTA_ROL, full_msg, rule['alert_type'], ref_id)
                        inv_logger.info(f"Notificación creada para: {rule['product_category']}")
    except Exception as e:
        inv_logger.error(f"Error en verificar_stock_y_alertar: {e}")

def calculate_active_seasonality_alerts(user_id: str, rol_destino: str):
    """
    Lee las notificaciones físicas y filtra las que el usuario ya leyó.
    """
    final_alerts = []
    try:
        # IMPORTANTE: Primero corremos la verificación para asegurar que la tabla no esté vacía
        verificar_stock_y_alertar()

        with get_db_cursor() as cur:
            # JOIN entre notifications (N) y read_alerts (R)
            # Solo traemos las que NO tengan registro en read_alerts para este usuario
            cur.execute("""
                SELECT n.id, n.mensaje, n.tipo, n.fecha_creacion, n.referencia_id
                FROM notifications n
                LEFT JOIN read_alerts r ON n.id::text = r.alert_id AND r.user_id = %s
                WHERE n.rol_destino = %s AND r.alert_id IS NULL
                ORDER BY n.fecha_creacion DESC
            """, (str(user_id), rol_destino))
            
            rows = cur.fetchall()
            for row in rows:
                final_alerts.append({
                    "id": str(row['id']), # ID de la tabla notifications
                    "message": row['mensaje'],
                    "type": row['tipo'],
                    "timestamp": row['fecha_creacion'].timestamp(),
                    "summary": f"Alerta: {row['tipo']}"
                })
    except Exception as e:
        inv_logger.error(f"Error consultando alertas: {e}")
    
    return final_alerts

def save_read_alert(user_id: str, alert_id: str):
    """
    Marca una notificación como leída insertando en read_alerts.
    """
    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO read_alerts (user_id, alert_id, tenant_id, fecha_lectura)
                VALUES (%s, %s, 'default', NOW())
                ON CONFLICT DO NOTHING
            """, (str(user_id), str(alert_id)))
            return True
    except Exception as e:
        inv_logger.error(f"Error al guardar lectura: {e}")
        return False