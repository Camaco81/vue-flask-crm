from backend.db import get_db_cursor
import uuid
from datetime import date
import logging
import time
import re

# Constantes de negocio
STOCK_THRESHOLD = 10 
ALMACENISTA_ROL = 'almacenista' 

inv_logger = logging.getLogger('backend.utils.inventory_utils')

def create_notification(rol_destino: str, mensaje: str, tipo: str, referencia_id: str = None):
    """
    Inserta una notificación física en la base de datos.
    Retorna el ID generado para poder rastrearlo.
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
        inv_logger.error(f"Error al persistir notificación en tabla: {e}")
        return None

def verificar_stock_y_alertar():
    """
    Worker que escanea stock y crea notificaciones INDEPENDIENTES.
    Si hay 2 categorías críticas, crea 2 notificaciones separadas.
    """
    current_month = date.today().month
    try:
        with get_db_cursor() as cur:
            # 1. Traer reglas de temporada
            cur.execute("""
                SELECT event_name, alert_type, product_category, stock_threshold, message_template
                FROM seasonality_events WHERE active_month = %s
            """, (current_month,))
            rules = cur.fetchall()
            
            for rule in rules:
                # 2. Buscar productos críticos por cada categoría (Iluminación, Decoración, etc.)
                cur.execute("""
                    SELECT id, name, stock 
                    FROM products 
                    WHERE category = %s AND stock < %s
                """, (rule['product_category'], rule['stock_threshold']))
                products = cur.fetchall()
                
                if products:
                    # Agrupamos productos de la misma categoría en una sola notificación clara
                    p_list = ", ".join([p['name'] for p in products])
                    msg = rule['message_template'].format(
                        event=rule['event_name'],
                        categories_list=rule['product_category'],
                        threshold=rule['stock_threshold']
                    )
                    full_message = f"{msg} | Productos: {p_list}"
                    
                    # Creamos la notificación en la tabla 'notifications'
                    # Usamos el product_category como parte de la referencia para unicidad
                    create_notification(
                        ALMACENISTA_ROL, 
                        full_message, 
                        rule['alert_type'], 
                        f"stock_bajo_{rule['product_category']}_{date.today()}"
                    )
    except Exception as e:
        inv_logger.error(f"Error en worker de stock: {e}")

def calculate_active_seasonality_alerts(user_cedula: str, rol_destino: str):
    """
    Lógica para WebSockets: Consulta 'notifications' y filtra las ya leídas por el usuario.
    """
    final_alerts = []
    try:
        with get_db_cursor() as cur:
            # Seleccionamos notificaciones que el usuario NO ha leído (usando LEFT JOIN)
            # Filtramos por el campo 'cedula' que es tu identificador de usuario
            cur.execute("""
                SELECT n.id, n.mensaje, n.tipo, n.fecha_creacion, n.referencia_id
                FROM notifications n
                LEFT JOIN read_alerts r ON n.id::text = r.alert_id AND r.user_id = %s
                WHERE n.rol_destino = %s 
                  AND r.alert_id IS NULL
                ORDER BY n.fecha_creacion DESC
            """, (str(user_cedula), rol_destino))
            
            rows = cur.fetchall()
            for row in rows:
                final_alerts.append({
                    "id": str(row['id']),
                    "message": row['mensaje'],
                    "type": row['tipo'],
                    "timestamp": row['fecha_creacion'].timestamp(),
                    "summary": f"Alerta de {row['tipo']}",
                    "referencia": row['referencia_id']
                })
    except Exception as e:
        inv_logger.error(f"Error al calcular alertas desde tabla notifications: {e}")
    
    return final_alerts

def mark_notification_as_read(user_id: str, alert_id: str):
    """
    Registra que un usuario específico leyó una notificación específica.
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
        inv_logger.error(f"Error al marcar como leída: {e}")
        return False