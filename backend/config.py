import os

class Config:
    # ... (Tus claves SECRET_KEY y JWT_SECRET_KEY)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_super_secret_key_here'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt_super_secret_key_here'
    
    # 🌟 NUEVA VARIABLE CLAVE: La URL completa de la base de datos de Neon
    # Usamos DB_URL como el nombre de la variable de entorno
    # Nota: No hay valor por defecto porque NECESITAS la URL de Neon.
    DATABASE_URL = os.environ.get('DATABASE_URL') 
    SECURITY_PASSWORD_HASH = os.environ.get('SECURITY_PASSWORD_HASH', 'pbkdf2:sha256') 
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT', 'fallback_salt_de_emergencia_largo') 
    # Mantenemos las variables antiguas, pero solo si no se usa DATABASE_URL
    # (Esto es opcional, pero puede ser útil si tu código necesita estos atributos por separado)
    DB_HOST = os.environ.get('DB_HOST') or 'localhost' 
    DB_NAME = os.environ.get('DB_NAME') or 'your_database_name'
    DB_USER = os.environ.get('DB_USER') or 'your_db_user'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'your_db_password'