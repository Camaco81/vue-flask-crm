import requests
import logging

api_logger = logging.getLogger('backend.utils.bcv_api')
DOLAR_VZLA_API_URL = "https://api.dolarvzla.com/public/exchange-rate" 
DEFAULT_RATE = 36.5 # Tasa de respaldo

def get_dolarvzla_rate():
    try:
        response = requests.get(DOLAR_VZLA_API_URL, timeout=10) 
        response.raise_for_status()
        data = response.json()
        
        # 🚨 CORRECCIÓN CLAVE: Buscar la tasa en la nueva estructura JSON
        # La tasa está en data['current']['usd'] y es float, no string.
        rate_float = data.get('current', {}).get('usd') # Usamos .get({}, {}) para manejo seguro

        # 🚨 Log de diagnóstico (Mantenemos el log por si cambia de nuevo)
        api_logger.info(f"Respuesta JSON de DolarVzla: {data}")
        
        if rate_float and isinstance(rate_float, (int, float)):
            rate = float(rate_float)
            api_logger.info(f"Tasa de DolarVzla obtenida con éxito: {rate}")
            return rate
        else:
            api_logger.error(f"La API de DolarVzla no devolvió el campo 'current.usd'. Usando tasa predeterminada.")
            return DEFAULT_RATE

    except requests.exceptions.RequestException as e:
        api_logger.error(f"Error de conexión/HTTP al obtener la tasa: {e}. Usando tasa predeterminada de {DEFAULT_RATE}.", exc_info=True)
        return DEFAULT_RATE
    
    except Exception as e:
        api_logger.error(f"Error inesperado al procesar la respuesta: {e}. Usando tasa predeterminada de {DEFAULT_RATE}.", exc_info=True)
        return DEFAULT_RATE