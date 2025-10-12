import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from config import Config

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
        yield conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        raise # Re-raise the exception to be caught by the caller
    finally:
        if conn:
            conn.close()

@contextmanager
def get_db_cursor(commit=False):
    with get_db_connection() as conn:
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