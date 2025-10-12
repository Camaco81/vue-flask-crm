import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from backend.config import Config

@contextmanager
def get_db_connection():
    conn = None
    
    # 💡 Lógica para usar DATABASE_URL si existe
    if Config.DATABASE_URL:
        # Usa la URL completa si está configurada (esto incluye host, user, password, etc.)
        conn_params = {'dsn': Config.DATABASE_URL}
    else:
        # Si DATABASE_URL NO está configurada, usa las variables separadas (para desarrollo local)
        conn_params = {
            'host': Config.DB_HOST,
            'database': Config.DB_NAME,
            'user': Config.DB_USER,
            'password': Config.DB_PASSWORD
        }

    try:
        conn = psycopg2.connect(**conn_params) # Pasa los parámetros al conector
        yield conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        # El error "Connection refused" que tenías antes ocurriría aquí si el host es incorrecto
        raise 
    finally:
        if conn:
            conn.close()