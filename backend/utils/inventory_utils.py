from backend.db import get_db_cursor
from datetime import date
import uuid
import logging
import time
import re

# Configuración de Logging
inv_logger = logging.getLogger('backend.utils.inventory_utils')

# Umbral por defecto para productos normales
STOCK_THRESHOLD = 10 

def create_notification(tenant_id, rol_destino, mensaje, tipo, referencia_id=None):
    """
    Inserta una nueva notificación en la base de datos vinculada a un tenant.
    """
    try:
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

def verificar_stock_y_alertar(product_id):
    """
    Verifica el stock de un producto individual. 
    Retorna el mensaje de alerta si el stock es bajo, de lo contrario None.
    """
    try:
        with get_db_cursor() as cur:
            cur.execute(
                "SELECT name, stock, tenant_id FROM products WHERE id = %s", 
                (product_id,)
            )
            product = cur.fetchone()
            
            if not product:
                return None 

            current_stock = product['stock']
            product_name = product['name']
            tenant_id = product['tenant_id']

            if current_stock <= STOCK_THRESHOLD:
                mensaje = (
                    f"ALERTA DE STOCK BAJO: El producto '{product_name}' "
                    f"tiene solo {current_stock} unidades restantes."
                )
                
                # Opcional: Crear la notificación persistente automáticamente
                create_notification(
                    tenant_id=tenant_id,
                    rol_destino='almacenista',
                    mensaje=mensaje,
                    tipo='stock_bajo',
                    referencia_id=product_id
                )
                
                return mensaje
            
            return None 
            
    except Exception as e:
        inv_logger.error(f"Error en verificar_stock_y_alertar (ID: {product_id}): {e}")
        return None

# Configuración de estacionalidad para ferreterías
ESTACIONALIDAD = [
    {
        'event': 'Navidad e Iluminación',
        'months': [11, 12],
        'categories': ['Iluminación Decorativa', 'Extensiones', 'Herramientas Eléctricas'],
        'stock_threshold': 50 
    },
    {
        'event': 'Reformas de Verano',
        'months': [7, 8],
        'categories': ['Pinturas', 'Brochas', 'Materiales Secos'],
        'stock_threshold': 80 
    },
    {
        'event': 'Mantenimiento de Jardín',
        'months': [4, 5],
        'categories': ['Mangueras', 'Herramientas de Jardinería', 'Bombas de Agua'],
        'stock_threshold': 40
    }
]

def verificar_tendencia_y_alertar(tenant_id=None):
    """
    Escanea el inventario buscando productos que deban reponerse según la temporada.
    Si se pasa tenant_id, filtra por esa empresa; si no, procesa todo (para tareas programadas).
    """
    current_month = date.today().month
    
    for season in ESTACIONALIDAD:
        if current_month in season['months']:
            for category in season['categories']:
                
                # Query optimizada: busca productos con stock bajo el umbral estacional
                query = """
                    SELECT id, name, stock, tenant_id
                    FROM products
                    WHERE category = %s AND stock < %s
                """
                params = [category, season['stock_threshold']]
                
                if tenant_id:
                    query += " AND tenant_id = %s"
                    params.append(tenant_id)
                
                try:
                    with get_db_cursor() as cur:
                        cur.execute(query, tuple(params))
                        productos_criticos = cur.fetchall()

                        for product in productos_criticos:
                            mensaje = (
                                f"🔔 Temporada ({season['event']}): '{product['name']}' "
                                f"tiene solo {product['stock']} unidades. "
                                f"Se recomienda subir a {season['stock_threshold']} por alta demanda."
                            )
                            
                            create_notification(
                                tenant_id=product['tenant_id'],
                                rol_destino='almacenista',
                                mensaje=mensaje,
                                tipo='tendencia_alta',
                                referencia_id=product['id']
                            )
                except Exception as e:
                    inv_logger.error(f"Error en tarea de tendencia: {e}")