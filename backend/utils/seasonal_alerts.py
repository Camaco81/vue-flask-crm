# =========================================================
# ARCHIVO: backend/utils/seasonal_alerts.py 
# =========================================================

from datetime import date
from typing import List, Dict, Any

# 💡 Arreglo de Alertas Estacionales
# NOTA: Usar 'stock_critico_estacional' y 'tendencia_alta' como tipos

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


def get_active_seasonal_alerts() -> List[Dict[str, Any]]:
    """
    Verifica la fecha actual y devuelve una lista de alertas de temporada activas.
    """
    current_month = date.today().month
    active_alerts = []
    
    for season in ESTACIONALIDAD:
        if current_month in season['months']:
            
            categories_list = ", ".join(season['categories'])
            
            # Formatear el mensaje usando la plantilla
            mensaje = season['message_template'].format(
                event=season['event'],
                categories_list=categories_list,
                threshold=season['stock_threshold']
            )
            
            alert_data = {
                # Usamos el nombre del evento como ID temporal ya que no hay DB
                'id': season['event'].replace(' ', '_'), 
                'mensaje': mensaje,
                'tipo': season['tipo'],
                # Usamos la fecha actual como created_at
                'created_at': date.today().isoformat() 
            }
            active_alerts.append(alert_data)
             
    return active_alerts