import psycopg2
import os

def get_db_connection():
    """Establece y retorna una conexión a la base de datos de Neon."""
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    return conn