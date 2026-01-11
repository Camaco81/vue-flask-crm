import uuid
from datetime import datetime, timedelta
import logging

sec_logger = logging.getLogger('backend.utils.security_utils')

# El tiempo de vida (TTL) del código de seguridad en minutos
CODE_TTL_MINUTES = 5

def generate_security_code():
    """Genera un código numérico de 6 dígitos."""
    # Usamos un UUID para asegurar unicidad, pero lo truncamos a 6 dígitos
    return str(uuid.uuid4().int)[:6].zfill(6)

def send_security_code(sale_id, contact_value, contact_method, cur):
    """
    Simula el envío de un código de seguridad y actualiza la venta.

    En una aplicación real, aquí se integraría Twilio, SendGrid, etc.
    Aquí solo se registra el código en la base de datos y se imprime un mensaje.
    """
    code = generate_security_code()
    code_sent_at = datetime.now()
    ttl_expiry = code_sent_at + timedelta(minutes=CODE_TTL_MINUTES)
    
    # Mensaje de simulación
    print(f"\n--- ALERTA DE SEGURIDAD SIMULADA ---")
    print(f"VENTA ID: {sale_id}")
    print(f"CÓDIGO GENERADO: {code}")
    print(f"CONTACTO: {contact_value} via {contact_method}. Válido hasta: {ttl_expiry.strftime('%H:%M:%S')}")
    print(f"------------------------------------\n")

    try:
        cur.execute(
            """
            UPDATE sales SET 
                confirmation_code = %s,
                code_sent_at = %s,
                code_contact_method = %s
            WHERE id = %s;
            """,
            (code, code_sent_at, contact_method, sale_id)
        )
        return {
            "success": True, 
            "message": f"Código de seguridad enviado a {contact_value} por {contact_method}. Válido por {CODE_TTL_MINUTES} minutos."
        }
    except Exception as e:
        sec_logger.error(f"Error al guardar código de seguridad para venta {sale_id}: {e}")
        return {"success": False, "message": "Error interno al generar el código de seguridad."}


def validate_security_code(sale_id, code_provided, cur):
    """Valida si el código proporcionado es correcto y aún está vigente."""
    try:
        cur.execute(
            "SELECT confirmation_code, code_sent_at FROM sales WHERE id = %s;",
            (sale_id,)
        )
        result = cur.fetchone()

        if not result or not result['confirmation_code']:
            return {"valid": False, "message": "No se encontró un código de confirmación activo para esta venta."}

        # 1. Validar expiración
        code_sent_at = result['code_sent_at'].replace(tzinfo=None) # Ajustar la zona horaria si es necesario
        expiry_time = code_sent_at + timedelta(minutes=CODE_TTL_MINUTES)
        
        if datetime.now() > expiry_time:
            return {"valid": False, "message": "El código de seguridad ha expirado. Por favor, solicite uno nuevo."}

        # 2. Validar código
        if code_provided == result['confirmation_code']:
            # Limpiar el código después de un uso exitoso
            cur.execute(
                "UPDATE sales SET confirmation_code = NULL, code_sent_at = NULL WHERE id = %s;",
                (sale_id,)
            )
            return {"valid": True, "message": "Código de seguridad validado exitosamente."}
        else:
            return {"valid": False, "message": "Código de seguridad incorrecto."}

    except Exception as e:
        sec_logger.error(f"Error al validar código de seguridad para venta {sale_id}: {e}")
        return {"valid": False, "message": "Error interno durante la validación del código."}