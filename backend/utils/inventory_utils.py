from backend.db import get_db_cursor
import uuid

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