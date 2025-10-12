import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_super_secret_key_here' # ¡CAMBIA ESTO EN PRODUCCIÓN!
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt_super_secret_key_here' # ¡CAMBIA ESTO EN PRODUCCIÓN!
    
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    DB_NAME = os.environ.get('DB_NAME') or 'your_database_name' # <--- CAMBIA ESTO
    DB_USER = os.environ.get('DB_USER') or 'your_db_user'       # <--- CAMBIA ESTO
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'your_db_password' # <--- CAMBIA ESTO