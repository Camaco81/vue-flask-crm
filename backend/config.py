import os
from datetime import timedelta

class Config:
    # --- Seguridad Básica ---
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_super_secret_key_here'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt_super_secret_key_here'
    
    # --- Configuración de Base de Datos (Neon/PostgreSQL) ---
    DATABASE_URL = os.environ.get('DATABASE_URL') 
    
    # --- Seguridad de Contraseñas ---
    SECURITY_PASSWORD_HASH = os.environ.get('SECURITY_PASSWORD_HASH', 'pbkdf2:sha256') 
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT', 'fallback_salt_de_emergencia_largo') 

    # 🌟 MANEJO DE SESIÓN Y TIEMPO DE CONEXIÓN 🌟
    
    # Define cuánto tiempo dura el token antes de expirar (1 día)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
    
    
    # Esto asegura que el frontend no tenga problemas con zonas horarias
    JWT_TIMEZONE_LOOKUP = False 

    # --- Variables heredadas (Compatibilidad) ---
    DB_HOST = os.environ.get('DB_HOST') or 'localhost' 
    DB_NAME = os.environ.get('DB_NAME') or 'your_database_name'
    DB_USER = os.environ.get('DB_USER') or 'your_db_user'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'your_db_password'