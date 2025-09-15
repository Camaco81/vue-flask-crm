import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    create_access_token,
    JWTManager,
    jwt_required,
    get_jwt_identity,
)
import cloudinary
import cloudinary.uploader
from passlib.hash import pbkdf2_sha256
from database import get_db_connection
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from datetime import timedelta

# Carga las variables de entorno del archivo .env
load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)

app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=30)
jwt = JWTManager(app)

cloudinary_url = os.environ.get('CLOUDINARY_URL')
if cloudinary_url:
    cloudinary.config(secure=True)
    print("Cloudinary configurado exitosamente.")
else:
    print("Advertencia: La variable de entorno CLOUDINARY_URL no está configurada.")
    print("La subida de imágenes a Cloudinary no funcionará.")


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"msg": "Email y contraseña son requeridos"}), 400

    hashed_password = pbkdf2_sha256.hash(password)
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM roles WHERE name = 'consultor';")
        role_id = cur.fetchone()[0]

        cur.execute(
            "INSERT INTO users (email, password, role_id) VALUES (%s, %s, %s);",
            (email, hashed_password, role_id)
        )
        conn.commit()
        return jsonify({"msg": "Usuario registrado exitosamente"}), 201

    except psycopg2.IntegrityError:
        if conn:
            conn.rollback()
        return jsonify({"msg": "El email ya está registrado"}), 409
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error en el registro: {e}")
        return jsonify({"msg": "Error al registrar usuario"}), 500
    finally:
        if conn:
            cur.close()
            conn.close()


@app.route("/login", methods=["POST"])
def login():
    """Endpoint para iniciar sesión y generar un token JWT."""
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"msg": "Email y contraseña son requeridos"}), 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT u.id, u.password, r.name, u.profile_image_url FROM users u JOIN roles r ON u.role_id = r.id WHERE u.email = %s;",
            (email,)
        )
        user = cur.fetchone()

        if user and pbkdf2_sha256.verify(password, user[1]):
            # Manejo de valor nulo
            profile_image_url = user[3] if user[3] else None
            
            user_data = {
                "id": str(user[0]),
                "email": email,
                "role": user[2],
                "profile_image_url": profile_image_url
            }
            access_token = create_access_token(identity=json.dumps(user_data))
            return jsonify(access_token=access_token, msg="Inicio de sesión exitoso"), 200
        else:
            return jsonify({"msg": "Credenciales incorrectas"}), 401

    except Exception as e:
        print(f"Error inesperado en login: {e}")
        return jsonify({"msg": "Error al iniciar sesión", "error": str(e)}), 500
    finally:
        if conn:
            cur.close()
            conn.close()


@app.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    try:
        current_user_data = json.loads(get_jwt_identity())
        return jsonify(logged_in_as=current_user_data), 200
    except Exception as e:
        print(f"Error al obtener datos del usuario: {e}")
        return jsonify({"msg": "No se pudo cargar la información del usuario"}), 500


@app.route("/api/customers", methods=["GET", "POST"])
@jwt_required()
def customers_management():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        if request.method == "GET":
            cur.execute("SELECT * FROM customers;")
            customers = cur.fetchall()
            return jsonify([dict(row) for row in customers]), 200

        elif request.method == "POST":
            data = request.get_json()

            if not data or 'name' not in data or 'email' not in data:
                return jsonify({"msg": "El nombre y el email del cliente son requeridos"}), 400

            name = data.get("name")
            email = data.get("email")
            phone = data.get("phone")
            address = data.get("address")

            cur.execute(
                "INSERT INTO customers (name, email, phone, address) VALUES (%s, %s, %s, %s) RETURNING *;",
                (name, email, phone, address)
            )
            new_customer = cur.fetchone()
            conn.commit()
            return jsonify(dict(new_customer)), 201

    except psycopg2.IntegrityError as e:
        if conn:
            conn.rollback()
        if 'email' in str(e):
            return jsonify({"msg": "Este email ya está registrado"}), 409
        return jsonify({"msg": "Error de integridad en la base de datos"}), 400

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error en la gestión de clientes: {e}")
        return jsonify({"msg": "Error al agregar cliente", "error": str(e)}), 500

    finally:
        if conn:
            cur.close()
            conn.close()


@app.route("/api/products", methods=["GET", "POST"])
@jwt_required()
def products_management():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        if request.method == "GET":
            cur.execute("SELECT * FROM products;")
            products = cur.fetchall()
            return jsonify([dict(row) for row in products]), 200

        elif request.method == "POST":
            data = request.get_json()

            if not data or 'name' not in data or 'price' not in data:
                return jsonify({"msg": "El nombre y el precio del producto son requeridos"}), 400

            name = data.get("name")
            price = data.get("price")

            cur.execute(
                "INSERT INTO products (name, price) VALUES (%s, %s) RETURNING *;",
                (name, price)
            )
            new_product = cur.fetchone()
            conn.commit()
            return jsonify(dict(new_product)), 201

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error en la gestión de productos: {e}")
        return jsonify({"msg": "Error al procesar la solicitud de productos", "error": str(e)}), 500

    finally:
        if conn:
            cur.close()
            conn.close()


@app.route("/api/upload_image", methods=["POST"])
@jwt_required()
def upload_image():
    conn = None
    try:
        if 'file' not in request.files:
            return jsonify({"msg": "No se encontró el archivo"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"msg": "No se seleccionó ningún archivo"}), 400

        current_user_data = json.loads(get_jwt_identity())
        user_id = current_user_data['id']

        upload_result = cloudinary.uploader.upload(file, folder="user_profiles")
        image_url = upload_result['secure_url']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET profile_image_url = %s WHERE id = %s RETURNING profile_image_url;",
            (image_url, user_id)
        )
        conn.commit()

        # Generar un nuevo token con la URL de la imagen actualizada
        current_user_data['profile_image_url'] = image_url
        new_access_token = create_access_token(identity=json.dumps(current_user_data))

        return jsonify({
            "url": image_url,
            "msg": "Imagen subida y guardada exitosamente.",
            "access_token": new_access_token  # Enviar el nuevo token al frontend
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error al subir o guardar la imagen: {e}")
        return jsonify({"msg": "Error al procesar la subida de la imagen.", "error": str(e)}), 500
    finally:
        if conn:
            cur.close()
            conn.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)