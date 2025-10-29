# En backend/utils/bcv_api.py

import requests
import logging

# Configuración de logger (opcional, si no está en app.py)
api_logger = logging.getLogger('backend.utils.bcv_api')

# La URL de la API que proporcionaste
DOLAR_VZLA_API_URL = "https://api.dolarvzla.com/public/exchange-rate" 

def get_dolarvzla_rate():
    DEFAULT_RATE = 36.5 
    
    try:
        # Aumentamos el timeout a 10s para dar más margen.
        response = requests.get(DOLAR_VZLA_API_URL, timeout=10) 
        response.raise_for_status() # Lanza excepción para errores HTTP (4xx o 5xx)
        data = response.json()
        
        # 🚨 DIAGNÓSTICO CLAVE: Registra el JSON completo para verificar la llave
        api_logger.info(f"Respuesta JSON de DolarVzla: {data}") 
        
        # Usaremos 'exchangeRate' como esperas
        rate_str = data.get('exchangeRate')
        
        if rate_str:
            rate = float(rate_str)
            api_logger.info(f"Tasa de DolarVzla obtenida con éxito: {rate}")
            return rate
        else:
            # 🚨 DIAGNÓSTICO CLAVE: Registra las llaves si 'exchangeRate' no se encuentra
            api_logger.error(f"La API de DolarVzla no devolvió el campo 'exchangeRate'. Claves disponibles: {data.keys()}")
            return DEFAULT_RATE

    except requests.exceptions.RequestException as e:
        # Registra fallos de red (DNS, Timeout) o HTTP 4xx/5xx
        api_logger.error(f"Error de conexión/HTTP al obtener la tasa: {e}. Usando tasa predeterminada de {DEFAULT_RATE}.", exc_info=True)
        return DEFAULT_RATE
    
    except Exception as e:
        # Registra errores de JSON (si el content-type no es correcto o está malformado)
        api_logger.error(f"Error inesperado al procesar la respuesta JSON: {e}. Usando tasa predeterminada de {DEFAULT_RATE}.", exc_info=True)
        return DEFAULT_RATE