import psycopg2
import psycopg2.extras
from contextlib import contextmanager
# Importación absoluta del archivo de configuración
from backend.config import Config 

# --- CONEXIÓN DE LA BASE DE DATOS ---

@contextmanager
def get_db_connection():
    conn = None
    
    # Lógica para usar DATABASE_URL de Neon o variables locales
    if Config.DATABASE_URL:
        # Usa la URL de conexión (dsn)
        conn_params = {'dsn': Config.DATABASE_URL}
    else:
        # Usa variables separadas (para desarrollo local)
        conn_params = {
            'host': Config.DB_HOST,
            'database': Config.DB_NAME,
            'user': Config.DB_USER,
            'password': Config.DB_PASSWORD
        }

    try:
        # Intento de conexión
        conn = psycopg2.connect(**conn_params)
        yield conn
    except psycopg2.Error as e:
        # La excepción se captura e imprime, luego se relanza para que el caller la maneje
        print(f"Database connection error: {e}")
        raise # Vuelve a lanzar la excepción
    finally:
        if conn:
            conn.close()

# --- CURSOR DE LA BASE DE DATOS ---

@contextmanager
def get_db_cursor(commit=False):
    # ¡Esta función es necesaria para resolver tu ImportError!
    with get_db_connection() as conn:
        # Usa DictCursor para obtener resultados como diccionarios
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            yield cur
            if commit:
                conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Database operation error: {e}")
            raise
        finally:
            cur.close()