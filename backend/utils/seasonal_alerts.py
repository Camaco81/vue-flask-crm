# =========================================================
# ARCHIVO: backend/utils/seasonal_alerts.py 
# =========================================================

from datetime import date
from typing import List, Dict, Any

# 💡 Arreglo de Alertas Estacionales
# NOTA: Usar 'stock_critico_estacional' y 'tendencia_alta' como tipos
ESTACIONALIDAD = [
    {
        'event': 'Navidad e Iluminación',
        'months': [11, 12], # Noviembre y Diciembre
        'categories': ['Iluminación Decorativa', 'Extensiones', 'Herramientas Eléctricas'],
        'stock_threshold': 50, # Umbral de stock MÁS ALTO para temporada
        'message_template': (
            "🔔 Temporada Alta: **{event}**. Aumentar el stock de las categorías: {categories_list}. "
            "El umbral sugerido es **{threshold}** unidades. ¡Anticípate a la Navidad!"
        ),
        'tipo': 'tendencia_alta'
    },
    {
        'event': 'Reformas de Verano',
        'months': [7, 8], # Julio y Agosto
        'categories': ['Pinturas', 'Brochas', 'Materiales Secos'],
        'stock_threshold': 80, 
        'message_template': (
            "⚠️ Previsión de Verano: **{event}**. Revisar el inventario de {categories_list}. "
            "Se espera alta demanda con un umbral de **{threshold}**."
        ),
        'tipo': 'stock_critico_estacional'
    },
    {
        'event': 'Mantenimiento de Jardín',
        'months': [4, 5], # Abril y Mayo (Inicio de temporada de lluvias)
        'categories': ['Mangueras', 'Herramientas de Jardinería', 'Bombas de Agua'],
        'stock_threshold': 40,
        'message_template': (
            "🌱 Temporada de Jardín: **{event}**. Asegurar stock superior a **{threshold}** unidades "
            "en: {categories_list} para atender la demanda."
        ),
        'tipo': 'tendencia_alta'
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