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

def verificar_stock_y_alertar(product_id: str):
    """
    Verifica el stock de un producto contra su umbral mínimo y genera una alerta 
    si es necesario. Se llama después de una transacción de inventario.
    """
    try:
        with get_db_cursor() as cur:
            # 1. Obtener datos del producto con los nuevos campos
            cur.execute(
                "SELECT name, stock_actual, stock_minimo FROM products WHERE id = %s",
                (product_id,)
            )
            product = cur.fetchone()
        
        if not product:
            return

        stock_actual = product['stock_actual']
        stock_minimo = product['stock_minimo']
        product_name = product['name']

        # 2. Aplicar la Regla de Alerta
        if stock_actual <= stock_minimo:
            mensaje = (
                f"🚨 Stock Crítico: El producto '{product_name}' tiene solo "
                f"{stock_actual} unidades (Mínimo: {stock_minimo}). Reponer pronto."
            )
            
            # 3. Generar Notificación (dirigida al almacenista)
            create_notification(
                rol_destino='almacenista',
                mensaje=mensaje,
                tipo='stock_critico',
                referencia_id=product_id
            )

    except Exception as e:
        print(f"Error en verificar_stock_y_alertar: {e}")

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