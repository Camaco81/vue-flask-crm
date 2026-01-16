import uuid
import logging
from datetime import datetime, timedelta, timezone

# Configuración de logging
sec_logger = logging.getLogger('backend.utils.security_utils')

# El tiempo de vida (TTL) del código de seguridad en minutos
CODE_TTL_MINUTES = 5

def generate_security_code():
    """
    Genera un código numérico de 6 dígitos basado en un hash de UUID 
    para garantizar aleatoriedad y unicidad.
    """
    return str(uuid.uuid4().int)[:6].zfill(6)

def send_security_code(sale_id, contact_value, contact_method, cur):
    """
    Genera, registra y simula el envío de un código de seguridad para una venta específica.
    """
    code = generate_security_code()
    # Usamos timezone.utc para evitar conflictos de "offset-naive" vs "offset-aware"
    code_sent_at = datetime.now(timezone.utc)
    
    # Mensaje de simulación para consola (Ideal para desarrollo/ilustración del proceso)
    print(f"\n" + "="*40)
    print(f"🛡️  ALERTA DE SEGURIDAD: VERIFICACIÓN DE VENTA")
    print(f"ID VENTA: {sale_id}")
    print(f"CÓDIGO:    {code}")
    print(f"MÉTODO:    {contact_method} ({contact_value})")
    print(f"VALIDEZ:   {CODE_TTL_MINUTES} minutos")
    print("="*40 + "\n")

    try:
        # Actualizamos la venta con el código y el timestamp
        # Asegúrate de que tu tabla 'sales' tenga estas columnas
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
            "message": f"Código enviado a {contact_value}. Expira en {CODE_TTL_MINUTES} min.",
            "code_simulated": code # Lo devolvemos para facilitar pruebas en el frontend
        }
    except Exception as e:
        sec_logger.error(f"Error al guardar código de seguridad (Venta: {sale_id}): {e}")
        return {"success": False, "message": "No se pudo generar el código de validación."}

def validate_security_code(sale_id, code_provided, cur):
    """
    Valida el código proporcionado contra la base de datos, 
    verificando que no haya expirado.
    """
    try:
        # Buscamos el código y el tiempo de envío
        cur.execute(
            "SELECT confirmation_code, code_sent_at FROM sales WHERE id = %s;",
            (sale_id,)
        )
        result = cur.fetchone()

        if not result or not result.get('confirmation_code'):
            return {"valid": False, "message": "No hay un proceso de verificación activo para esta venta."}

        # 1. Validar expiración (Manejo de fechas consciente de la zona horaria)
        code_sent_at = result['code_sent_at']
        
        # Si la fecha viene de la DB como naive (sin zona), la localizamos a UTC
        if code_sent_at.tzinfo is None:
            code_sent_at = code_sent_at.replace(tzinfo=timezone.utc)
            
        now = datetime.now(timezone.utc)
        expiry_time = code_sent_at + timedelta(minutes=CODE_TTL_MINUTES)
        
        if now > expiry_time:
            # Limpiamos el código expirado para obligar a generar uno nuevo
            cur.execute("UPDATE sales SET confirmation_code = NULL, code_sent_at = NULL WHERE id = %s;", (sale_id,))
            return {"valid": False, "message": "El código ha expirado. Solicite uno nuevo."}

        # 2. Validar coincidencia del código
        if str(code_provided).strip() == str(result['confirmation_code']).strip():
            # Limpieza inmediata tras uso exitoso (Seguridad: One-time use)
            cur.execute(
                "UPDATE sales SET confirmation_code = NULL, code_sent_at = NULL WHERE id = %s;",
                (sale_id,)
            )
            return {"valid": True, "message": "Verificación exitosa."}
        else:
            return {"valid": False, "message": "El código ingresado es incorrecto."}

    except Exception as e:
        sec_logger.error(f"Error en validación de seguridad (Venta: {sale_id}): {e}")
        return {"valid": False, "message": "Error interno en el servidor de seguridad."}