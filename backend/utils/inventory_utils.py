from backend.db import get_db_cursor
import uuid
from datetime import date
def create_notification(rol_destino: str, mensaje: str, tipo: str, referencia_id: str = None):
    """Inserta una nueva notificación en la base de datos."""
    try:
        new_id = str(uuid.uuid4())
        with get_db_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO notifications (id, rol_destino, mensaje, tipo, referencia_id, is_read)
                VALUES (%s, %s, %s, %s, %s, FALSE)
                """,
                (new_id, rol_destino, mensaje, tipo, referencia_id)
            )
        print(f"Notificación creada: {mensaje}")
    except Exception as e:
        print(f"Error al crear notificación: {e}")

# =========================================================
# ARCHIVO: backend/utils/inventory_utils.py
# =========================================================

from backend.db import get_db_cursor
import logging
# ⚠️ IMPORTANTE: Importar la constante definida en el archivo de rutas
from backend.routes.sale_routes import STOCK_THRESHOLD 

# Configura tu logger si es necesario
inv_logger = logging.getLogger('backend.utils.inventory_utils')

def verificar_stock_y_alertar(product_id):
    """Verifica el stock de un producto contra el umbral de alerta."""
    
    try:
        with get_db_cursor() as cur:
            # 🟢 CORRECCIÓN DEL UNDEFINED COLUMN: Usar 'stock' en lugar de 'stock_actual'.
            # Usaremos el STOCK_THRESHOLD como un valor para comparar si no tienes una columna 'stock_minimo'.
            cur.execute(
                "SELECT name, stock FROM products WHERE id = %s", 
                (product_id,)
            )
            product = cur.fetchone()
            
            if not product:
                return None # Producto no encontrado

            current_stock = product['stock']
            product_name = product['name']

            if current_stock <= STOCK_THRESHOLD:
                return (
                    f"ALERTA DE STOCK BAJO: El producto '{product_name}' "
                    f"tiene solo {current_stock} unidades restantes (Umbral: {STOCK_THRESHOLD})."
                )
            
            return None # No se requiere alerta
            
    except Exception as e:
        # Registra el error para evitar el fallo de la transacción principal
        inv_logger.error(f"Error en verificar_stock_y_alertar (product_id: {product_id}): {e}", exc_info=True)
        # ❌ NO se retorna el error en el mensaje de alerta.
        return None
# Ejemplo de uso:
# verificar_stock_y_alertar('id-del-producto-vendido')

ESTACIONALIDAD = [
    {
        'event': 'Navidad e Iluminación',
        'months': [11, 12], # Noviembre y Diciembre
        'categories': ['Iluminación Decorativa', 'Extensiones', 'Herramientas Eléctricas'],
        'stock_threshold': 50 # Umbral de stock MÁS ALTO para temporada
    },
    {
        'event': 'Reformas de Verano',
        'months': [7, 8], # Julio y Agosto
        'categories': ['Pinturas', 'Brochas', 'Materiales Secos'],
        'stock_threshold': 80 
    },
    {
        'event': 'Mantenimiento de Jardín',
        'months': [4, 5], # Abril y Mayo (Inicio de temporada de lluvias)
        'categories': ['Mangueras', 'Herramientas de Jardinería', 'Bombas de Agua'],
        'stock_threshold': 40
    }
]

def verificar_tendencia_y_alertar():
    """
    Verifica los productos en tendencia por temporada y genera una alerta si 
    el stock está por debajo del umbral estacional para esas categorías.
    """
    current_month = date.today().month
    
    # 1. Iterar sobre las temporadas
    for season in ESTACIONALIDAD:
        if current_month in season['months']:
            
            # 2. Iterar sobre las categorías de la temporada activa
            for category in season['categories']:
                
                # 3. Consulta SQL: Busca productos de la categoría activa con stock bajo el umbral de temporada
                query = """
                SELECT id, name, stock_actual
                FROM products
                WHERE category = %s AND stock_actual < %s
                """
                
                try:
                    with get_db_cursor() as cur:
                        cur.execute(query, (category, season['stock_threshold']))
                        productos_criticos = cur.fetchall()

                        # 4. Generar alertas para cada producto encontrado
                        for product in productos_criticos:
                            
                            mensaje = (
                                f"🔔 Aviso de Temporada ({season['event']}): El producto "
                                f"'{product['name']}' (Cat: {category}) tiene stock bajo "
                                f"({product['stock_actual']} unidades) para la demanda proyectada. ¡Reponer!"
                            )
                            
                            create_notification(
                                rol_destino='almacenista',
                                mensaje=mensaje,
                                tipo='tendencia_alta',
                                referencia_id=product['id']
                            )
                            print(f"Alerta de Tendencia generada para: {product['name']}")

                except Exception as e:
                    print(f"Error en verificar_tendencia_y_alertar (SQL): {e}")