from backend.db import get_db_cursor
import uuid
from datetime import date
import logging
import time
import re 

ALMACENISTA_ROL = 'almacenista' 
inv_logger = logging.getLogger('backend.utils.inventory_utils')

# --- HELPERS ---
def get_alert_stable_id(event_name: str, tipo: str) -> str:
    safe_name = re.sub(r'[^\w\s-]', '', event_name).strip().lower()
    safe_name = re.sub(r'[-\s]+', '_', safe_name)
    return f"{ALMACENISTA_ROL}_{safe_name}_{tipo}"

def create_notification(rol_destino: str, mensaje: str, tipo: str, referencia_id: str = None):
    """Inserta una notificación física en la tabla 'notifications'."""
    try:
        new_id = str(uuid.uuid4())
        with get_db_cursor(commit=True) as cur: 
            cur.execute("""
                INSERT INTO notifications (id, rol_destino, mensaje, tipo, referencia_id, is_read, fecha_creacion)
                VALUES (%s, %s, %s, %s, %s, FALSE, NOW())
            """, (new_id, rol_destino, mensaje, tipo, referencia_id))
    except Exception as e:
        inv_logger.error(f"Error al crear notificación: {e}")

# --- FUNCIÓN QUE BUSCA APP.PY (EL FIX) ---
def verificar_stock_y_alertar():
    """
    Esta es la función que llama tu app.py o tu scheduler.
    Busca productos críticos y los guarda en la base de datos.
    """
    current_month = date.today().month
    try:
        with get_db_cursor() as cur:
            # 1. Traer reglas del mes
            cur.execute("SELECT * FROM seasonality_events WHERE active_month = %s", (current_month,))
            rules = cur.fetchall()
            
            for rule in rules:
                # 2. Buscar productos bajo el umbral
                cur.execute("SELECT id, name, stock FROM products WHERE category = %s AND stock < %s", 
                           (rule['product_category'], rule['stock_threshold']))
                products = cur.fetchall()
                
                for p in products:
                    msg = f"⚠️ STOCK BAJO: El producto {p['name']} está bajo el umbral de {rule['event_name']}."
                    create_notification(ALMACENISTA_ROL, msg, rule['alert_type'], p['id'])
    except Exception as e:
        inv_logger.error(f"Error en el worker de stock: {e}")

# --- FUNCIÓN PARA SOCKETS Y API ---
def calculate_active_seasonality_alerts(rol_destino: str):
    """Calcula alertas al vuelo para WebSockets sin guardarlas duplicadas."""
    current_month = date.today().month
    final_alerts = []
    try:
        with get_db_cursor() as cur: 
            cur.execute("""
                SELECT event_name, alert_type, product_category, stock_threshold, message_template
                FROM seasonality_events WHERE active_month = %s;
            """, (current_month,))
            active_rules = cur.fetchall()

            events_map = {}
            for rule in active_rules:
                event = rule['event_name']
                if event not in events_map:
                    events_map[event] = {**rule, 'products': [], 'categories': []}
                
                cur.execute("SELECT name, stock FROM products WHERE category = %s AND stock < %s", 
                           (rule['product_category'], rule['stock_threshold']))
                prods = cur.fetchall()
                if prods: events_map[event]['products'].extend(prods)
                if rule['product_category'] not in events_map[event]['categories']:
                    events_map[event]['categories'].append(rule['product_category'])

            for event_name, data in events_map.items():
                if data['products'] or data['alert_type'] == 'promocion_baja':
                    cats_str = ", ".join(data['categories'])
                    msg = data['message_template'].format(event=event_name, categories_list=cats_str, threshold=data['stock_threshold'])
                    
                    p_names = [f"{p['name']} ({p['stock']} ud)" for p in data['products']]
                    summary = f"Críticos: {', '.join(p_names[:2])}" if p_names else "Revisión sugerida."

                    final_alerts.append({
                        "id": get_alert_stable_id(event_name, data['alert_type']),
                        "message": msg,
                        "type": data['alert_type'],
                        "timestamp": time.time(),
                        "summary": summary,
                        "rol_destino": rol_destino
                    })
    except Exception as e:
        inv_logger.error(f"Error calculando alertas: {e}")
    return final_alerts