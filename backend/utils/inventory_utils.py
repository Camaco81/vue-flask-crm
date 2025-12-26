from backend.db import get_db_cursor
import uuid
from datetime import date
import logging
import time
import re 

# Constantes requeridas por otros módulos (como sale_routes)
STOCK_THRESHOLD = 10 
ALMACENISTA_ROL = 'almacenista' 

inv_logger = logging.getLogger('backend.utils.inventory_utils')

def get_alert_stable_id(event_name: str, tipo: str) -> str:
    """Genera un ID único y estable basado en el evento."""
    safe_name = re.sub(r'[^\w\s-]', '', event_name).strip().lower()
    safe_name = re.sub(r'[-\s]+', '_', safe_name)
    return f"{ALMACENISTA_ROL}_{safe_name}_{tipo}"

def create_notification(rol_destino: str, mensaje: str, tipo: str, referencia_id: str = None):
    """Inserta notificación con manejo de error si la tabla no existe."""
    try:
        new_id = str(uuid.uuid4())
        with get_db_cursor(commit=True) as cur: 
            cur.execute("""
                INSERT INTO notifications (id, rol_destino, mensaje, tipo, referencia_id, is_read, fecha_creacion)
                VALUES (%s, %s, %s, %s, %s, FALSE, NOW())
            """, (new_id, rol_destino, mensaje, tipo, referencia_id))
    except Exception as e:
        # Si la tabla no existe, solo lo logeamos para que la App no muera
        inv_logger.warning(f"No se pudo guardar notificación (¿Falta tabla notifications?): {e}")

def verificar_stock_y_alertar():
    """Lógica para el worker/background."""
    current_month = date.today().month
    try:
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT event_name, alert_type, product_category, stock_threshold 
                FROM seasonality_events WHERE active_month = %s
            """, (current_month,))
            rules = cur.fetchall()
            
            for rule in rules:
                cur.execute("SELECT id, name, stock FROM products WHERE category = %s AND stock < %s", 
                           (rule['product_category'], rule['stock_threshold']))
                products = cur.fetchall()
                
                for p in products:
                    msg = f"🔔 {rule['event_name']}: {p['name']} tiene stock bajo ({p['stock']})."
                    create_notification(ALMACENISTA_ROL, msg, rule['alert_type'], p['id'])
    except Exception as e:
        inv_logger.error(f"Error en verificar_stock_y_alertar: {e}")

def calculate_active_seasonality_alerts(rol_destino: str):
    """Lógica para WebSockets/API - Uso de 'stock' en lugar de 'stock_actual'."""
    current_month = date.today().month
    final_alerts = []
    try:
        with get_db_cursor() as cur: 
            cur.execute("SELECT * FROM seasonality_events WHERE active_month = %s", (current_month,))
            rules = cur.fetchall()

            events_map = {}
            for rule in rules:
                event = rule['event_name']
                if event not in events_map:
                    events_map[event] = {**rule, 'products': [], 'categories': []}
                
                # CORRECCIÓN: Aseguramos que la columna sea 'stock'
                cur.execute("SELECT name, stock FROM products WHERE category = %s AND stock < %s", 
                           (rule['product_category'], rule['stock_threshold']))
                prods = cur.fetchall()
                if prods: events_map[event]['products'].extend(prods)
                if rule['product_category'] not in events_map[event]['categories']:
                    events_map[event]['categories'].append(rule['product_category'])

            for event_name, data in events_map.items():
                if data['products'] or data['alert_type'] == 'promocion_baja':
                    msg = data['message_template'].format(
                        event=event_name, 
                        categories_list=", ".join(data['categories']), 
                        threshold=data['stock_threshold']
                    )
                    
                    # Usamos 'stock' que es el nombre real en tu tabla products
                    p_names = [f"{p['name']} ({p['stock']} ud)" for p in data['products']]
                    summary = f"Críticos: {', '.join(p_names[:2])}" if p_names else "Revisión de temporada."

                    final_alerts.append({
                        "id": get_alert_stable_id(event_name, data['alert_type']),
                        "message": msg,
                        "type": data['alert_type'],
                        "timestamp": time.time(),
                        "summary": summary,
                        "rol_destino": rol_destino
                    })
    except Exception as e:
        inv_logger.error(f"Error en calculate_active_seasonality_alerts: {e}")
    return final_alerts