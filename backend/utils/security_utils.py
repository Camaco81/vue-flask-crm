import hashlib
import logging
import uuid
from datetime import datetime, timezone

sec_logger = logging.getLogger('backend.utils.security_utils')

def generate_daily_admin_code(tenant_id, secret_seed):
    """
    Genera un código de 6 dígitos que cambia cada día.
    Es determinista: mientras sea el mismo día y el mismo tenant, el código será igual.
    """
    try:
        # Usamos la fecha actual en formato YYYY-MM-DD
        today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        
        # Combinamos fecha, tenant y la semilla secreta del servidor
        combined_payload = f"{today_str}-{tenant_id}-{secret_seed}"
        
        # Creamos un hash SHA256
        hash_digest = hashlib.sha256(combined_payload.encode()).hexdigest()
        
        # Convertimos una parte del hash a un número de 6 dígitos
        # Tomamos los últimos 6 dígitos del entero resultante
        code = str(int(hash_digest[:10], 16))[-6:].zfill(6)
        
        return code, today_str
    except Exception as e:
        sec_logger.error(f"Error generando código diario: {e}")
        return None, None

def verify_admin_auth_code(provided_code, tenant_id, secret_seed):
    """
    Verifica si el código entregado por el vendedor coincide con el código 
    maestro generado para el día de hoy.
    """
    expected_code, _ = generate_daily_admin_code(tenant_id, secret_seed)
    if not expected_code or not provided_code:
        return False
        
    return str(provided_code).strip() == expected_code