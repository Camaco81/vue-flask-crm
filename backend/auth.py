from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from backend.db import get_db_cursor
from backend.config import Config # <-- Nuevo

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS': # Manejar la petición preflight explícitamente
        # Flask-CORS normalmente se encarga de esto,
        # pero para mayor seguridad o si hay interacciones inusuales,
        # devolver un 200 OK vacío es la respuesta estándar para preflight.
        # Los encabezados CORS serán añadidos por Flask-CORS.
        return '', 200

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    role_id = data.get('role_id', 4) # Default role_id, e.g., customer or basic user

    if not email or not password:
        return jsonify({"msg": "Email and password are required"}), 400

    hashed_password = generate_password_hash(password)

    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute("INSERT INTO users (email, password, role_id) VALUES (%s, %s, %s) RETURNING id;",
                        (email, hashed_password, role_id))
            new_user_id = cur.fetchone()[0]
        return jsonify({"msg": "User registered successfully", "user_id": new_user_id}), 201
    except Exception as e:
        if "duplicate key value violates unique constraint" in str(e):
            return jsonify({"msg": "Email already registered"}), 409
        return jsonify({"msg": "Error registering user", "error": str(e)}), 500

@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"msg": "Email and password are required"}), 400

    try:
        with get_db_cursor() as cur:
            # Asegúrate de seleccionar todos los campos que el frontend pueda necesitar
            cur.execute("SELECT id, email, password, role_id FROM users WHERE email = %s", (email,)) 
            user = cur.fetchone()

        if user and check_password_hash(user['password'], password):
            access_token = create_access_token(identity=str(user['id']))
            
            # 🌟 CORRECCIÓN CRÍTICA: ESTRUCTURA LA RESPUESTA PARA EL FRONTEND 🌟
            # El frontend espera { access_token, user: { role_id, email, ... } }
            user_data = {
                'id': user['id'],
                'email': user['email'],
                'role_id': user['role_id'],
                # 'image_url': user['image_url'] if 'image_url' in user else None # Asume que tienes este campo
            }
            
            return jsonify(
                access_token=access_token,
                user=user_data # <-- AHORA ENVÍA EL OBJETO 'user' ESPERADO
            ), 200
        else:
            return jsonify({"msg": "Bad username or password"}), 401
    except Exception as e:
        print(f"Error during login: {e}") 
        return jsonify({"msg": "Error during login", "error": str(e)}), 500