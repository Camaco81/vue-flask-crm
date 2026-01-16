import requests
import logging

# Configuración de logging para diagnóstico
api_logger = logging.getLogger('backend.utils.bcv_api')

# URL de la API proporcionada por el usuario
DOLAR_VZLA_API_URL = "https://api.dolarvzla.com/public/exchange-rate" 

# Tasa de respaldo en caso de caída total de la API
DEFAULT_RATE = 36.5 

def get_dolarvzla_rate():
    """
    Obtiene la tasa de cambio actual desde DolarVzla API.
    Estructura esperada: {"current": {"usd": 341.74, ...}, ...}
    """
    try:
        # Realizamos la petición con un timeout prudencial (10 segundos)
        response = requests.get(DOLAR_VZLA_API_URL, timeout=10)
        
        # Lanza una excepción si el status code no es 2xx
        response.raise_for_status()
        
        data = response.json()
        
        # Log para depuración: Ver qué está llegando exactamente al servidor
        api_logger.info(f"Estructura recibida de la API: {data}")

        # Extracción segura: Accedemos a data['current']['usd']
        current_data = data.get('current')
        
        if current_data and 'usd' in current_data:
            rate_val = current_data.get('usd')
            
            # Verificamos que el valor sea numérico
            if isinstance(rate_val, (int, float)):
                rate = float(rate_val)
                api_logger.info(f"Tasa extraída con éxito: {rate}")
                return rate
            else:
                api_logger.error(f"El campo 'usd' no es un número: {rate_val} (tipo: {type(rate_val)})")
        else:
            api_logger.error("No se encontró la clave 'current' o 'usd' en la respuesta de la API.")

    except requests.exceptions.Timeout:
        api_logger.error("Timeout al conectar con la API de DolarVzla.")
    except requests.exceptions.RequestException as e:
        api_logger.error(f"Error de red o HTTP: {e}")
    except Exception as e:
        api_logger.error(f"Error inesperado al procesar la tasa: {e}", exc_info=True)

    # Si llegamos aquí, algo falló. Retornamos la tasa por defecto.
    api_logger.warning(f"Se utilizará la tasa por defecto: {DEFAULT_RATE}")
    return DEFAULT_RATE