# En backend/utils/bcv_api.py

import requests
import logging

# La URL de la API que proporcionaste
DOLAR_VZLA_API_URL = "https://api.dolarvzla.com/public/exchange-rate" 

def get_dolarvzla_rate():
    """
    Obtiene la tasa de cambio del dólar a Bolívares (VES) desde la API de DolarVzla.
    Retorna la tasa como un float.
    """
    # Tasa de respaldo CRÍTICA si la API falla o está fuera de servicio
    DEFAULT_RATE = 36.5 
    
    try:
        # Petición GET a la API con un tiempo de espera prudente
        response = requests.get(DOLAR_VZLA_API_URL, timeout=5)
        response.raise_for_status() # Lanza excepción para errores HTTP (4xx o 5xx)
        data = response.json()
        
        # La API de DolarVzla usa la llave 'exchangeRate' para la tasa de cambio.
        # Asegúrate de que el valor sea float o conviértelo.
        rate_str = data.get('exchangeRate')
        
        if rate_str:
            rate = float(rate_str)
            logging.info(f"Tasa de DolarVzla obtenida con éxito: {rate}")
            return rate
        else:
            logging.error("La API de DolarVzla no devolvió el campo 'exchangeRate'.")
            return DEFAULT_RATE

    except requests.exceptions.RequestException as e:
        # Captura errores de conexión, timeout, o HTTP
        logging.error(f"Error al obtener la tasa de DolarVzla: {e}. Usando tasa predeterminada de {DEFAULT_RATE}.", exc_info=True)
        return DEFAULT_RATE
    except Exception as e:
        # Captura otros errores (ej. JSON malformado)
        logging.error(f"Error inesperado al procesar la respuesta de DolarVzla: {e}. Usando tasa predeterminada de {DEFAULT_RATE}.", exc_info=True)
        return DEFAULT_RATE

# 🚨 IMPORTANTE: En sale_routes.py, cambia la importación si la tenías como get_bcv_rate
# De: from backend.utils.bcv_api import get_bcv_rate
# A: from backend.utils.bcv_api import get_dolarvzla_rate