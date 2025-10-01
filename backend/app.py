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

@app.route('/')
def index():
    return jsonify(message="API is running!"), 200

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

@app.before_request
def handle_options():
    if request.method == "OPTIONS":
        return "", 200

@app.route("/login", methods=["POST"])
def login():
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
            # Asegúrate de que los índices coincidan: user[0]=id, user[1]=password, user[2]=role_name, user[3]=profile_image_url, user[4]=role_id
            "SELECT u.id, u.password, r.name AS role_name, u.profile_image_url, r.id AS role_id FROM users u JOIN roles r ON u.role_id = r.id WHERE u.email = %s;",
            (email,)
        )
        user = cur.fetchone()

        if user and pbkdf2_sha256.verify(password, user[1]):
            user_id = user[0]
            user_role_name = user[2] # 'admin' o 'vendedor'
            user_profile_image_url = user[3] if user[3] else None
            user_role_id = user[4] # El ID numérico del rol (ej. 1, 2)

            # Opcional: Puedes incrustar más datos directamente en el token si lo deseas
            # Aunque para el rol, es más fácil devolverlo por separado y guardarlo en localStorage
            # identity_data = {
            #     "id": str(user_id),
            #     "email": email,
            #     "role_id": user_role_id,
            #     "role_name": user_role_name
            # }
            # access_token = create_access_token(identity=json.dumps(identity_data))

            # Si el token solo necesita el ID del usuario:
            access_token = create_access_token(identity=str(user_id)) # Solo el ID como identidad del token

            return jsonify(
                access_token=access_token,
                msg="Inicio de sesión exitoso",
                role_id=user_role_id,          # <--- ¡AÑADIDO! ID numérico del rol
                role_name=user_role_name,      # <--- ¡AÑADIDO! Nombre del rol ('admin', 'vendedor')
                profile_image_url=user_profile_image_url # <--- ¡AÑADIDO!
            ), 200
        else:
            return jsonify({"msg": "Credenciales incorrectas"}), 401

    except Exception as e:
        print(f"Error inesperado en login: {e}")
        return jsonify({"msg": "Error al iniciar sesión", "error": str(e)}), 500
    finally:
        if conn:
            cur.close()
            conn.close()
            
# Endpoint para actualizar datos del usuario (password, email)
@app.route("/api/users/<int:user_id>", methods=["PUT"])
@jwt_required()
def update_user(user_id):
    conn = None
    try:
        data = request.get_json()
        
        if not data or not any(key in data for key in ['password', 'email']):
            return jsonify({"msg": "Se requiere al menos un campo (email o password) para actualizar"}), 400

        conn = get_db_connection()
        cur = conn.cursor()
        
        if 'password' in data:
            hashed_password = pbkdf2_sha256.hash(data['password'])
            cur.execute("UPDATE users SET password = %s WHERE id = %s;", (hashed_password, user_id))
        
        if 'email' in data:
            cur.execute("UPDATE users SET email = %s WHERE id = %s;", (data['email'], user_id))

        conn.commit()
        return jsonify({"msg": "Usuario actualizado exitosamente"}), 200
    
    except psycopg2.IntegrityError:
        if conn:
            conn.rollback()
        return jsonify({"msg": "El nuevo email ya está en uso"}), 409
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error al actualizar usuario: {e}")
        return jsonify({"msg": "Error al actualizar usuario"}), 500
    finally:
        if conn:
            cur.close()
            conn.close()


@app.route("/api/roles", methods=["GET"])
@jwt_required()
def get_roles():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT id, name FROM roles;")
        roles = cur.fetchall()
        return jsonify([dict(row) for row in roles]), 200
    except Exception as e:
        print(f"Error al obtener roles: {e}")
        return jsonify({"msg": "Error al obtener roles"}), 500
    finally:
        if conn:
            cur.close()
            conn.close()


# ====================================================================
# === CLIENTS: COLLECTION ROUTE (GET all, POST new) ===
# ====================================================================

@app.route("/api/customers", methods=["GET", "POST"])
@jwt_required()
def customers_collection():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        if request.method == "GET":
            cur.execute("SELECT id, name, email, phone, address FROM customers;")
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
                "INSERT INTO customers (name, email, phone, address) VALUES (%s, %s, %s, %s) RETURNING id, name, email, phone, address;",
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
        return jsonify({"msg": f"Error al procesar la solicitud: {e}"}), 500
    finally:
        if conn:
            cur.close()
            conn.close()


# ====================================================================
# === CLIENTS: SINGLE ITEM ROUTE (GET, PUT, DELETE) ===
# ====================================================================

@app.route("/api/customers/<string:customer_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def customers_single(customer_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        if request.method == "GET":
            cur.execute("SELECT id, name, email, phone, address FROM customers WHERE id = %s;", (customer_id,))
            customer = cur.fetchone()
            if customer:
                return jsonify(dict(customer)), 200
            else:
                return jsonify({"msg": "Cliente no encontrado"}), 404

        elif request.method == "PUT":
            data = request.get_json()
            if not data or not any(key in data for key in ['name', 'email', 'phone', 'address']):
                return jsonify({"msg": "Se requiere al menos un campo para actualizar"}), 400

            fields = []
            values = []
            if 'name' in data:
                fields.append("name = %s")
                values.append(data["name"])
            if 'email' in data:
                fields.append("email = %s")
                values.append(data["email"])
            if 'phone' in data:
                fields.append("phone = %s")
                values.append(data["phone"])
            if 'address' in data:
                fields.append("address = %s")
                values.append(data["address"])

            values.append(customer_id)

            cur.execute(
                f"UPDATE customers SET {', '.join(fields)} WHERE id = %s RETURNING id, name, email, phone, address;",
                tuple(values)
            )
            updated_customer = cur.fetchone()
            conn.commit()

            if updated_customer:
                return jsonify(dict(updated_customer)), 200
            else:
                return jsonify({"msg": "Cliente no encontrado"}), 404
        
        elif request.method == "DELETE":
            cur.execute("DELETE FROM customers WHERE id = %s;", (customer_id,))
            deleted_rows = cur.rowcount
            conn.commit()

            if deleted_rows > 0:
                return jsonify({"msg": "Cliente eliminado exitosamente"}), 200
            else:
                return jsonify({"msg": "Cliente no encontrado"}), 404

    except psycopg2.IntegrityError as e:
        if conn:
            conn.rollback()
        if 'email' in str(e):
            return jsonify({"msg": "Este email ya está registrado"}), 409
        return jsonify({"msg": "Error de integridad en la base de datos"}), 400
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"msg": f"Error al procesar la solicitud: {e}"}), 500
    finally:
        if conn:
            cur.close()
            conn.close()


# ====================================================================
# === PRODUCTS: COLLECTION ROUTE (GET all, POST new) ===
# ====================================================================

@app.route("/api/products", methods=["GET", "POST"])
@jwt_required()
def products_collection():
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


# ====================================================================
# === PRODUCTS: SINGLE ITEM ROUTE (GET, PUT, DELETE) ===
# ====================================================================

@app.route("/api/products/<string:product_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def products_single(product_id):
    conn = None
    try:
        # Aquí no necesitas hacer nada, ya que la variable `product_id` ya es un string
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        if request.method == "PUT":
            data = request.get_json()
            if not data or not any(key in data for key in ['name', 'price']):
                return jsonify({"msg": "Se requiere al menos un campo para actualizar (name o price)"}), 400

            fields = []
            values = []
            if 'name' in data:
                fields.append("name = %s")
                values.append(data['name'])
            if 'price' in data:
                fields.append("price = %s")
                values.append(data['price'])

            values.append(product_id)

            cur.execute(
                f"UPDATE products SET {', '.join(fields)} WHERE id = %s RETURNING *;",
                tuple(values)
            )
            updated_product = cur.fetchone()
            conn.commit()
    

            if updated_product:
                return jsonify(dict(updated_product)), 200
            else:
                return jsonify({"msg": "Producto no encontrado"}), 404

        elif request.method == "DELETE":
            cur.execute("DELETE FROM products WHERE id = %s;", (product_id,))
            deleted_rows = cur.rowcount
            conn.commit()

            if deleted_rows > 0:
                return jsonify({"msg": "Producto eliminado exitosamente"}), 200
            else:
                return jsonify({"msg": "Producto no encontrado"}), 404

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

        current_user_data['profile_image_url'] = image_url
        new_access_token = create_access_token(identity=json.dumps(current_user_data))

        return jsonify({
            "url": image_url,
            "msg": "Imagen subida y guardada exitosamente.",
            "access_token": new_access_token
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


# ====================================================================
# === ORDERS: COLLECTION ROUTE (GET all, POST new) ===
# ====================================================================

@app.route("/api/orders", methods=["GET", "POST"])
@jwt_required()
def orders_collection():
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        if request.method == "POST":
            data = request.get_json()
            customer_id = data.get("customer_id")
            items = data.get("items")

            if not customer_id or not items:
                return jsonify({"msg": "Missing customer_id or items"}), 400

            total_amount = 0
            product_prices = {}
            for item in items:
                cur.execute("SELECT price FROM products WHERE id = %s", (item['product_id'],))
                price_row = cur.fetchone()
                if price_row:
                    product_prices[item['product_id']] = price_row[0]
                    total_amount += price_row[0] * item['quantity']
                else:
                    return jsonify({"msg": f"Product with ID {item['product_id']} not found"}), 404

            cur.execute(
                "INSERT INTO orders (customer_id, total_amount) VALUES (%s, %s) RETURNING id;",
                (customer_id, total_amount)
            )
            new_order_id = cur.fetchone()[0]

            for item in items:
                cur.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s);",
                    (new_order_id, item['product_id'], item['quantity'], product_prices[item['product_id']])
                )
            
            conn.commit()
            return jsonify({"msg": "Order created successfully", "order_id": str(new_order_id)}), 201
        
        elif request.method == "GET":
            cur.execute("""
                SELECT o.id, c.name as customer_name, o.order_date, o.status, o.total_amount,
                        json_agg(json_build_object(
                            'product_name', p.name,
                            'quantity', oi.quantity,
                            'price', oi.price
                        )) AS items
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                JOIN order_items oi ON o.id = oi.order_id
                JOIN products p ON oi.product_id = p.id
                GROUP BY o.id, c.name
                ORDER BY o.order_date DESC
            """)
            orders = cur.fetchall()
            orders_list = [dict(order) for order in orders]
            return jsonify(orders_list), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"msg": "Error en la gestión de pedidos", "error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# ====================================================================
# === ORDERS: SINGLE ITEM ROUTE (GET, DELETE) ===
# ====================================================================

@app.route("/api/orders/<int:order_id>", methods=["GET", "DELETE"])
@jwt_required()
def orders_single(order_id):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        if request.method == "GET":
            cur.execute("""
                SELECT o.id, c.name as customer_name, o.order_date, o.status, o.total_amount,
                        json_agg(json_build_object(
                            'product_name', p.name,
                            'quantity', oi.quantity,
                            'price', oi.price
                        )) AS items
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                JOIN order_items oi ON o.id = oi.order_id
                JOIN products p ON oi.product_id = p.id
                WHERE o.id = %s
                GROUP BY o.id, c.name
            """, (order_id,))
            order = cur.fetchone()
            if order:
                return jsonify(dict(order)), 200
            else:
                return jsonify({"msg": "Order not found"}), 404

        elif request.method == "DELETE":
            cur.execute("DELETE FROM order_items WHERE order_id = %s;", (order_id,))
            cur.execute("DELETE FROM orders WHERE id = %s;", (order_id,))
            deleted_rows = cur.rowcount
            conn.commit()

            if deleted_rows > 0:
                return jsonify({"msg": "Pedido y sus items eliminados exitosamente"}), 200
            else:
                return jsonify({"msg": "Pedido no encontrado"}), 404

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"msg": "Error en la gestión de pedidos", "error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route("/api/analytics", methods=["GET"])
@jwt_required()
def get_analytics():
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("SELECT COUNT(*) AS total_customers FROM customers;")
        total_customers = cur.fetchone()['total_customers']

        cur.execute("SELECT COUNT(*) AS total_products FROM products;")
        total_products = cur.fetchone()['total_products']

        cur.execute("""
            SELECT COUNT(*) AS total_today_orders
            FROM orders
            WHERE order_date >= current_date;
        """)
        total_today_orders = cur.fetchone()['total_today_orders']

        cur.execute("SELECT COALESCE(SUM(total_amount), 0) AS total_revenue FROM orders;")
        total_revenue = cur.fetchone()['total_revenue']

        return jsonify({
            "total_customers": total_customers,
            "total_products": total_products,
            "total_today_orders": total_today_orders,
            "total_revenue": float(total_revenue)
        }), 200

    except Exception as e:
        return jsonify({"msg": "Error al obtener analíticas", "error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)