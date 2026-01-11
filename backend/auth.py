from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from backend.db import get_db_cursor
import logging

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
auth_logger = logging.getLogger('backend.routes.auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    # En un sistema real, el tenant_id vendría del nombre de la empresa al registrarse
    tenant_id = data.get('company_name') or data.get('tenant_id')
    role_id = data.get('role_id', 2) # 2: Vendedor por defecto

    if not email or not password:
        return jsonify({"msg": "Email y contraseña requeridos"}), 400

    hashed_password = generate_password_hash(password)

    try:
        with get_db_cursor(commit=True) as cur:
            # Insertamos el usuario vinculado a su empresa (tenant)
            cur.execute(
                """INSERT INTO users (email, password, role_id, tenant_id) 
                   VALUES (%s, %s, %s, %s) RETURNING id;""",
                (email, hashed_password, role_id, tenant_id)
            )
            new_user_id = cur.fetchone()[0]
        return jsonify({"msg": "Registro exitoso", "user_id": new_user_id}), 201
    except Exception as e:
        if "unique constraint" in str(e).lower():
            return jsonify({"msg": "El email ya está registrado"}), 409
        return jsonify({"msg": "Error en el registro"}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"msg": "Email y contraseña requeridos"}), 400

    try:
        with get_db_cursor() as cur:
            # Buscamos el usuario y su tenant_id
            cur.execute("SELECT id, email, password, role_id, tenant_id FROM users WHERE email = %s", (email,)) 
            user = cur.fetchone()

        if user and check_password_hash(user['password'], password):
            # 🌟 CLAVE: Incluimos el tenant_id en los claims adicionales del token
            additional_claims = {"tenant_id": user['tenant_id']}
            access_token = create_access_token(
                identity=str(user['id']), 
                additional_claims=additional_claims
            )
            
            # Estructura de respuesta limpia para el Frontend
            return jsonify({
                "access_token": access_token,
                "user": {
                    "id": user['id'],
                    "email": user['email'],
                    "role_id": user['role_id'],
                    "tenant_id": user['tenant_id']
                }
            }), 200
        else:
            return jsonify({"msg": "Credenciales inválidas"}), 401
    except Exception as e:
        auth_logger.error(f"Error en login: {e}")
        return jsonify({"msg": "Error interno en el servidor"}), 500