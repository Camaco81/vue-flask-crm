from backend.db import get_db_cursor
from datetime import date
import uuid
import logging

inv_logger = logging.getLogger('backend.utils.inventory_utils')

# --- CONSTANTES ---
STOCK_THRESHOLD = 10 
ALMACENISTA_ROL = 3 

# Configuración de estacionalidad
ESTACIONALIDAD = [
    {'event': 'Navidad', 'months': [11, 12], 'categories': ['Iluminación Decorativa'], 'stock_threshold': 50},
    {'event': 'Verano', 'months': [7, 8], 'categories': ['Pinturas'], 'stock_threshold': 80},
    {'event': 'Jardín', 'months': [4, 5], 'categories': ['Mangueras'], 'stock_threshold': 40}
]

def create_notification(tenant_id, rol_destino, mensaje, tipo, referencia_id=None):
    try:
        new_id = str(uuid.uuid4())
        with get_db_cursor(commit=True) as cur:
            cur.execute(
                """INSERT INTO notifications (id, tenant_id, rol_destino, mensaje, tipo, referencia_id, is_read, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, FALSE, CURRENT_TIMESTAMP)""",
                (new_id, tenant_id, rol_destino, mensaje, tipo, referencia_id)
            )
    except Exception as e:
        inv_logger.error(f"Error al crear notificación: {e}")

def calculate_active_seasonality_alerts(user_id, rol_id):
    try:
        with get_db_cursor() as cur:
            rol_str = 'almacenista' if int(rol_id) == ALMACENISTA_ROL else 'admin'
            query = """
                SELECT n.* FROM notifications n
                WHERE n.rol_destino = %s
                AND n.id NOT IN (SELECT alert_id FROM read_alerts WHERE user_id = %s)
                ORDER BY n.created_at DESC
            """
            cur.execute(query, (rol_str, str(user_id)))
            return cur.fetchall()
    except Exception as e:
        inv_logger.error(f"Error en calculate_active_seasonality_alerts: {e}")
        return []

def save_read_alert(user_id, alert_id):
    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute("INSERT INTO read_alerts (user_id, alert_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (str(user_id), str(alert_id)))
        return True
    except Exception as e:
        inv_logger.error(f"Error en save_read_alert: {e}")
        return False

# --- ESTA ES LA FUNCIÓN QUE RENDER NO ENCONTRABA ---
def verificar_tendencia_y_alertar(tenant_id=None):
    current_month = date.today().month
    for season in ESTACIONALIDAD:
        if current_month in season['months']:
            for category in season['categories']:
                query = "SELECT id, name, stock, tenant_id FROM products WHERE category = %s AND stock < %s"
                params = [category, season['stock_threshold']]
                if tenant_id:
                    query += " AND tenant_id = %s"
                    params.append(tenant_id)
                try:
                    with get_db_cursor() as cur:
                        cur.execute(query, tuple(params))
                        for prod in cur.fetchall():
                            msg = f"🔔 Temporada {season['event']}: {prod['name']} bajo stock."
                            create_notification(prod['tenant_id'], 'almacenista', msg, 'tendencia_alta', prod['id'])
                except Exception as e:
                    inv_logger.error(f"Error en tendencia: {e}")

def verificar_stock_y_alertar(product_id):
    # Esta se usa manualmente tras ventas, requiere product_id
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT name, stock, tenant_id FROM products WHERE id = %s", (product_id,))
            p = cur.fetchone()
            if p and p['stock'] <= STOCK_THRESHOLD:
                create_notification(p['tenant_id'], 'almacenista', f"Stock bajo: {p['name']}", 'stock_bajo', product_id)
    except Exception as e:
        inv_logger.error(f"Error: {e}")