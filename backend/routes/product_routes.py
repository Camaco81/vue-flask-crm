from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from backend.db import get_db_cursor
from backend.utils.helpers import (
    get_user_and_role, 
    check_product_manager_permission, 
    validate_required_fields
)
import logging

product_bp = Blueprint('product', __name__, url_prefix='/api/products')
app_logger = logging.getLogger('backend.routes.product_routes')

def get_current_tenant():
    """Extrae el tenant_id del token JWT. En tu caso es el nombre del negocio."""
    return get_jwt().get('tenant_id', 'default-tenant')

@product_bp.route('', methods=['GET', 'POST'])
@jwt_required()
def products_collection():
    # Manejo de desempaquetado robusto para evitar el ValueError anterior
    result = get_user_and_role()
    if not isinstance(result, (list, tuple)) or len(result) < 2:
        app_logger.error(f"Error en helper get_user_and_role: se recibió {result}")
        return jsonify({"msg": "Error de sesión"}), 401
    
    current_user_id = result[0]
    user_role_id = result[1]
    tenant_id = get_current_tenant()
    
    # ------------------ POST (Crear Producto) ------------------
    if request.method == 'POST':
        if not check_product_manager_permission(user_role_id):
            return jsonify({"msg": "Acceso denegado: permisos insuficientes"}), 403
        
        data = request.get_json()
        if error := validate_required_fields(data, ['name', 'price', 'stock']):
            return jsonify({"msg": f"Campos faltantes: {error}"}), 400

        try:
            name = data['name'].strip()
            price = float(data['price'])
            stock = int(data['stock'])
            
            with get_db_cursor(commit=True) as cur:
                # Eliminado ::uuid porque el tenant es un string ("Maye")
                cur.execute(
                    """INSERT INTO products (name, price, stock, tenant_id) 
                       VALUES (%s, %s, %s, %s) """,
                    (name, price, stock, tenant_id)
                )
                new_product = cur.fetchone()
                
            return jsonify(dict(new_product)), 201
        except Exception as e:
            app_logger.error(f"Error creando producto: {e}")
            return jsonify({"msg": "Error interno al crear"}), 500

    # ------------------ GET (Listar Productos) ------------------
    elif request.method == 'GET':
        try:
            with get_db_cursor() as cur:
                # Comparamos como string normal. 
                # Si en la DB la columna fuera UUID real, esto daría error, 
                # pero si el tenant es "Maye", la columna debe ser VARCHAR/TEXT.
                cur.execute(
                    """SELECT id, name, price AS price_usd, stock 
                       FROM products 
                       WHERE tenant_id = %s 
                       ORDER BY name;""",
                    (tenant_id,)
                )
                rows = cur.fetchall()
                return jsonify([dict(p) for p in rows]), 200
        except Exception as e:
            app_logger.error(f"Error listando productos: {e}")
            return jsonify({"msg": "Error al obtener productos"}), 500

@product_bp.route('/<string:product_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def product_single(product_id):
    result = get_user_and_role()
    current_user_id, user_role_id = result[0], result[1]
    tenant_id = get_current_tenant()

    # ------------------ GET (Producto Único) ------------------
    if request.method == 'GET':
        try:
            with get_db_cursor() as cur:
                cur.execute(
                    "SELECT id, name, price AS price_usd, stock FROM products WHERE id = %s AND tenant_id = %s;",
                    (product_id, tenant_id)
                )
                product = cur.fetchone()
            return jsonify(dict(product)) if product else (jsonify({"msg": "Producto no encontrado"}), 404)
        except Exception as e:
            return jsonify({"msg": "Error servidor"}), 500

    # ------------------ PUT (Actualizar Producto) ------------------
    elif request.method == 'PUT':
        if not check_product_manager_permission(user_role_id):
            return jsonify({"msg": "Acceso denegado"}), 403
        
        data = request.get_json()
        try:
            with get_db_cursor(commit=True) as cur:
                allowed_keys = {'name': str, 'price': float, 'stock': int}
                updates = []
                params = []
                
                for key, val in data.items():
                    # Mapeo de price_usd del front a price de la DB
                    actual_key = 'price' if key == 'price_usd' else key
                    if actual_key in allowed_keys:
                        updates.append(f"{actual_key} = %s")
                        params.append(val)
                
                if not updates:
                    return jsonify({"msg": "No hay datos válidos"}), 400
                
                params.extend([product_id, tenant_id])
                query = f"UPDATE products SET {', '.join(updates)} WHERE id = %s AND tenant_id = %s RETURNING id, name, price AS price_usd, stock;"
                
                cur.execute(query, tuple(params))
                updated = cur.fetchone()
                return jsonify(dict(updated)) if updated else (jsonify({"msg": "No encontrado"}), 404)
        except Exception as e:
            app_logger.error(f"Error en PUT: {e}")
            return jsonify({"msg": "Error al actualizar"}), 500

    # ------------------ DELETE (Eliminar) ------------------
    elif request.method == 'DELETE':
        if not check_product_manager_permission(user_role_id):
            return jsonify({"msg": "Acceso denegado"}), 403
        try:
            with get_db_cursor(commit=True) as cur:
                cur.execute(
                    "DELETE FROM products WHERE id = %s AND tenant_id = %s RETURNING id;",
                    (product_id, tenant_id)
                )
                return jsonify({"msg": "Eliminado"}), 200 if cur.fetchone() else (jsonify({"msg": "No encontrado"}), 404)
        except Exception as e:
            return jsonify({"msg": "Error al eliminar"}), 500