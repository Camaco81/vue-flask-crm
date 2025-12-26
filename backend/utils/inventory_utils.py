from backend.db import get_db_cursor
import uuid
from datetime import date
import logging
import time
import re 

ALMACENISTA_ROL = 'almacenista' 
inv_logger = logging.getLogger('backend.utils.inventory_utils')

def get_alert_stable_id(event_name: str, tipo: str) -> str:
    """Genera un ID único y estable para que el frontend sepa si ya la leyó."""
    safe_name = re.sub(r'[^\w\s-]', '', event_name).strip().lower()
    safe_name = re.sub(r'[-\s]+', '_', safe_name)
    return f"{ALMACENISTA_ROL}_{safe_name}_{tipo}"

def calculate_active_seasonality_alerts(rol_destino: str):
    """
    CONSULTA ÚNICA: Obtiene reglas de la DB y verifica productos.
    Se usa tanto para WebSockets como para la API REST.
    """
    current_month = date.today().month
    final_alerts = []
    
    try:
        with get_db_cursor() as cur: 
            # 1. Obtener reglas del mes actual desde la DB
            cur.execute("""
                SELECT event_name, alert_type, product_category, stock_threshold, message_template
                FROM seasonality_events
                WHERE active_month = %s;
            """, (current_month,))
            active_rules = cur.fetchall()

            # 2. Agrupar categorías por evento para no repetir mensajes
            events_map = {}

            for rule in active_rules:
                event = rule['event_name']
                if event not in events_map:
                    events_map[event] = {
                        **rule,
                        'products': [],
                        'categories': []
                    }
                
                # Buscar productos de esta regla que están bajo el umbral
                cur.execute("""
                    SELECT name, stock FROM products 
                    WHERE category = %s AND stock < %s
                """, (rule['product_category'], rule['stock_threshold']))
                
                prods = cur.fetchall()
                if prods:
                    events_map[event]['products'].extend(prods)
                
                if rule['product_category'] not in events_map[event]['categories']:
                    events_map[event]['categories'].append(rule['product_category'])

            # 3. Construir los objetos finales de alerta
            for event_name, data in events_map.items():
                # Si es promoción o si hay productos críticos, disparamos la alerta
                if data['products'] or data['alert_type'] == 'promocion_baja':
                    
                    cats_str = ", ".join(data['categories'])
                    msg = data['message_template'].format(
                        event=event_name,
                        categories_list=cats_str,
                        threshold=data['stock_threshold']
                    )

                    # Resumen de productos
                    if data['products']:
                        p_names = [f"{p['name']} ({p['stock']} ud)" for p in data['products']]
                        summary = f"Críticos: {', '.join(p_names[:2])}"
                        if len(p_names) > 2: summary += f" y {len(p_names)-2} más"
                    else:
                        summary = "Revisión sugerida por temporada."

                    final_alerts.append({
                        "id": get_alert_stable_id(event_name, data['alert_type']),
                        "message": msg,
                        "type": data['alert_type'],
                        "timestamp": time.time(),
                        "summary": summary,
                        "rol_destino": rol_destino
                    })

    except Exception as e:
        inv_logger.error(f"Error calculando alertas: {e}", exc_info=True)
    
    return final_alerts