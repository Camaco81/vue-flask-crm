from backend.db import get_db_cursor
from datetime import date
import uuid
import logging

# Configuración de Logging
inv_logger = logging.getLogger('backend.utils.inventory_utils')

# --- CONSTANTES ---
STOCK_THRESHOLD = 10 
ALMACENISTA_ROL = 3  # <--- Agregado para que realtime.py lo encuentre

def create_notification(tenant_id, rol_destino, mensaje, tipo, referencia_id=None):
    """Inserta una nueva notificación en la base de datos."""
    try:
        new_id = str(uuid.uuid4()) # Generamos el ID que faltaba
        with get_db_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO notifications (id, tenant_id, rol_destino, mensaje, tipo, referencia_id, is_read, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, FALSE, CURRENT_TIMESTAMP)
                """,
                (new_id, tenant_id, rol_destino, mensaje, tipo, referencia_id)
            )
        inv_logger.info(f"Notificación creada para tenant {tenant_id}: {tipo}")
    except Exception as e:
        inv_logger.error(f"Error al crear notificación: {e}")

# --- ESTAS SON LAS FUNCIONES QUE FALTABAN Y CAUSABAN EL ERROR EN RENDER ---

def calculate_active_seasonality_alerts(user_id, rol_id):
    """
    Trae las notificaciones de la DB que el usuario no ha marcado como leídas.
    """
    try:
        with get_db_cursor() as cur:
            # Buscamos notificaciones que correspondan al rol y que NO estén en la tabla de leídas para este usuario
            query = """
                SELECT n.* FROM notifications n
                WHERE n.rol_destino = %s
                AND n.id NOT IN (
                    SELECT alert_id FROM read_alerts WHERE user_id = %s
                )
                ORDER BY n.created_at DESC
            """
            # Mapeo de rol ID a string si es necesario
            rol_str = 'almacenista' if int(rol_id) == ALMACENISTA_ROL else 'admin'
            
            cur.execute(query, (rol_str, str(user_id)))
            return cur.fetchall()
    except Exception as e:
        inv_logger.error(f"Error en calculate_active_seasonality_alerts: {e}")
        return []

def save_read_alert(user_id, alert_id):
    """Registra que un usuario leyó una alerta específica."""
    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO read_alerts (user_id, alert_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (str(user_id), str(alert_id))
            )
        return True
    except Exception as e:
        inv_logger.error(f"Error en save_read_alert: {e}")
        return False

# --- Lógica de verificación existente ---

def verificar_stock_y_alertar(product_id):
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT name, stock, tenant_id FROM products WHERE id = %s", (product_id,))
            product = cur.fetchone()
            if not product: return None 

            if product['stock'] <= STOCK_THRESHOLD:
                mensaje = f"ALERTA: '{product['name']}' tiene solo {product['stock']} unidades."
                create_notification(product['tenant_id'], 'almacenista', mensaje, 'stock_bajo', product_id)
                return mensaje
        return None 
    except Exception as e:
        inv_logger.error(f"Error en stock_alert: {e}")
        return None