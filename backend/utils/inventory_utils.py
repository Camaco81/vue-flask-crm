from backend.db import get_db_cursor
import uuid
from datetime import date
import logging

STOCK_THRESHOLD = 10 

# Configura tu logger si es necesario
inv_logger = logging.getLogger('backend.utils.inventory_utils')

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


# Configura tu logger si es necesario
inv_logger = logging.getLogger('backend.utils.inventory_utils')

def verificar_stock_y_alertar(product_id):
    """Verifica el stock de un producto contra el umbral de alerta."""
    
    try:
        with get_db_cursor() as cur:
            # Consulta corregida para usar 'stock'
            cur.execute(
                "SELECT name, stock FROM products WHERE id = %s", 
                (product_id,)
            )
            product = cur.fetchone()
            
            if not product:
                return None 

            current_stock = product['stock']
            product_name = product['name']

            if current_stock <= STOCK_THRESHOLD:
                return (
                    f"ALERTA DE STOCK BAJO: El producto '{product_name}' "
                    f"tiene solo {current_stock} unidades restantes (Umbral: {STOCK_THRESHOLD})."
                )
            
            return None 
            
    except Exception as e:
        inv_logger.error(f"Error en verificar_stock_y_alertar (product_id: {product_id}): {e}", exc_info=True)
        return None

ESTACIONALIDAD = [
    # ------------------ EVENTOS DE ALTA DEMANDA (Tendencia Alta) ------------------
    {
        'event': 'Navidad e Iluminación',
        'months': [11, 12], # Noviembre y Diciembre
        'categories': ['Iluminación Decorativa', 'Extensiones', 'Herramientas Eléctricas', 'Seguridad'],
        'stock_threshold': 50, # Alto umbral
        'message_template': (
            "🔔 Temporada Alta: **{event}**. Aumentar el stock de: {categories_list}. "
            "El umbral sugerido es **{threshold}** unidades. ¡Anticípate a la Navidad!"
        ),
        'tipo': 'tendencia_alta'
    },
    {
        'event': 'Reformas de Verano (Pico)',
        'months': [7, 8], # Julio y Agosto
        'categories': ['Pinturas', 'Brochas', 'Materiales Secos', 'Cerraduras'],
        'stock_threshold': 80, 
        'message_template': (
            "⚠️ Previsión de Verano: **{event}**. Revisar el inventario de {categories_list}. "
            "Se espera alta demanda con un umbral de **{threshold}**."
        ),
        'tipo': 'tendencia_alta'
    },
    {
        'event': 'Mantenimiento de Jardín y Lluvias',
        'months': [4, 5], # Abril y Mayo (Inicio de temporada de lluvias)
        'categories': ['Mangueras', 'Herramientas de Jardinería', 'Bombas de Agua', 'Siliconas'],
        'stock_threshold': 40,
        'message_template': (
            "🌱 Temporada de Jardín: **{event}**. Asegurar stock superior a **{threshold}** unidades "
            "en: {categories_list} para atender la demanda."
        ),
        'tipo': 'tendencia_alta'
    },
    
    # ------------------ EVENTOS TEMÁTICOS Y ESTACIONALES ------------------
    {
        'event': 'Pintura y Reparaciones de Fin de Año',
        'months': [9, 10], # Septiembre y Octubre (Preparativos para el fin de año)
        'categories': ['Pinturas', 'Rodillos', 'Materiales de Limpieza', 'Andamios'],
        'stock_threshold': 35,
        'message_template': (
            "🛠️ Preparación: **{event}**. Revisar stock de {categories_list}. "
            "Momento ideal para que los clientes renueven espacios."
        ),
        'tipo': 'tendencia_media'
    },
    {
        'event': 'Amor y Amistad / Pequeños Proyectos',
        'months': [2, 3], # Febrero y Marzo (Febrero es temático, Marzo es preparatorio)
        'categories': ['Adhesivos', 'Kits de Herramientas Básicas', 'Artículos de Decoración Pequeños'],
        'stock_threshold': 20,
        'message_template': (
            "❤️ Febrero/Marzo: **{event}**. Promocionar kits pequeños o regalos en {categories_list}. "
            "El stock sugerido es **{threshold}**."
        ),
        'tipo': 'tendencia_media'
    },
    {
        'event': 'Inicio de Clases y Oficina',
        'months': [6], # Junio (Cierre de semestre/Vacaciones/Inicio de otros proyectos)
        'categories': ['Cables de Red', 'Material de Oficina (Herramientas)', 'Sillas de Taller/Mesa'],
        'stock_threshold': 25,
        'message_template': (
            "🎓 Junio: **{event}**. Revisar inventario de {categories_list}. "
            "A menudo se requiere equipamiento para estudios u oficinas."
        ),
        'tipo': 'tendencia_media'
    },
    
    # ------------------ EVENTOS DE BAJA DEMANDA (Promoción/Descuentos) ------------------
    {
        'event': 'Cuesta de Enero y Descuentos Post-Navidad',
        'months': [1], # Enero
        'categories': ['Productos con Poco Movimiento', 'Inventario Excedente'],
        'stock_threshold': 50, # Umbral de stock para liquidar (no para reponer)
        'message_template': (
            "📉 Enero (Baja Demanda): **{event}**. Enfocarse en promociones/liquidación en {categories_list}. "
            "Usar el stock excedente para generar flujo de caja."
        ),
        'tipo': 'promocion_baja'
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

def get_alert_stable_id(event_name: str, tipo: str) -> str:
    """
    Genera un ID único y estable basado en el evento y tipo de alerta. 
    Esto garantiza que el estado 'leído' persista en la DB.
    """
    # Limpia y normaliza el nombre del evento
    safe_name = re.sub(r'[^\w\s-]', '', event_name).strip().lower()
    safe_name = re.sub(r'[-\s]+', '_', safe_name)
    return f"{safe_name}_{tipo}"


def calculate_active_seasonality_alerts(cur, rol_destino: str) -> list:
    """
    Calcula las alertas de estacionalidad basándose en el mes actual y el stock.
    Devuelve la lista de objetos de alerta con su ID estable, sin guardarlas en la DB.
    """
    current_month = date.today().month
    active_alerts = []
    
    # Iterar sobre las temporadas
    for season in ESTACIONALIDAD:
        if current_month in season['months']:
            
            # Generar el ID estable para este evento de temporada
            stable_id = get_alert_stable_id(season['event'], season['tipo'])
            
            # Recolectar productos críticos para este evento
            productos_criticos_info = []
            is_triggered = False

            # Consulta SQL: Busca productos de las categorías activas con stock bajo el umbral de temporada
            for category in season['categories']:
                query = """
                SELECT id, name, stock_actual, category
                FROM products
                WHERE category = %s AND stock_actual < %s
                """
                
                try:
                    cur.execute(query, (category, season['stock_threshold']))
                    productos_criticos = cur.fetchall()

                    for product in productos_criticos:
                        is_triggered = True
                        productos_criticos_info.append(
                            f"'{product['name']}' ({product['stock_actual']} uds)"
                        )
                except Exception as e:
                    # Manejo de error de DB
                    logging.error(f"Error SQL al revisar estacionalidad: {e}")
                    
            # 5. Si la alerta se disparó (stock bajo o es una alerta de promoción que siempre aplica)
            if is_triggered or season['tipo'] == 'promocion_baja':
                
                # Resumen para el mensaje final
                if productos_criticos_info:
                    alert_summary = f"Productos críticos: {', '.join(productos_criticos_info[:3])}"
                    if len(productos_criticos_info) > 3:
                        alert_summary += f" y {len(productos_criticos_info) - 3} más."
                else:
                    alert_summary = "Revisa las categorías sugeridas para anticiparte."
                
                # Construcción del mensaje principal basado en la plantilla
                categories_list_str = ", ".join(season['categories'])
                final_message = season['message_template'].format(
                    event=season['event'],
                    categories_list=categories_list_str,
                    threshold=season['stock_threshold']
                )

                # Creamos el objeto de alerta que enviaremos por WebSocket
                active_alerts.append({
                    "id": stable_id, # EL ID ESTABLE es la clave
                    "message": final_message,
                    "type": season['tipo'],
                    "timestamp": time.time(),
                    "summary": alert_summary,
                    "rol_destino": rol_destino
                })
                
    return active_alerts