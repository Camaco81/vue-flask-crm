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
    """
    Extrae el tenant_id del token JWT.
    """
    return get_jwt().get('tenant_id', 'default-tenant')

@product_bp.route('', methods=['GET', 'POST'])
@jwt_required()
def products_collection():
    result = get_user_and_role()
    if not isinstance(result, (list, tuple)) or len(result) < 2:
        app_logger.error(f"Error en helper get_user_and_role: se recibió {result}")
        return jsonify({"msg": "Error de sesión"}), 401
    
    user_role_id = result[1]
    tenant_id = get_current_tenant()
    
    # ------------------ POST (Crear Producto) ------------------
    if request.method == 'POST':
        if not check_product_manager_permission(user_role_id):
            return jsonify({"msg": "Acceso denegado: permisos insuficientes"}), 403
        
        data = request.get_json()
        # Validamos que 'category' esté presente
        if error := validate_required_fields(data, ['name', 'price', 'stock', 'category']):
            return jsonify({"msg": f"Campos faltantes: {error}"}), 400

        try:
            name = data['name'].strip()
            category = data['category'].strip()
            price = float(data['price'])
            stock = int(data['stock'])
            
            with get_db_cursor(commit=True) as cur:
                # Corregido: Se agregaron los placeholders y la columna category
                cur.execute(
                    """INSERT INTO products (name, price, stock, category, tenant_id) 
                       VALUES (%s, %s, %s, %s, %s) 
                       RETURNING id, name, price, stock, category;""",
                    (name, price, stock, category, tenant_id)
                )
                new_product = cur.fetchone()
                
            return jsonify(dict(new_product)), 201
        except Exception as e:
            app_logger.error(f"Error creando producto: {e}")
            return jsonify({"msg": "Error interno al crear producto"}), 500

    # ------------------ GET (Listar Productos) ------------------
    elif request.method == 'GET':
        try:
            with get_db_cursor() as cur:
                cur.execute(
                    """SELECT id, name, price, stock, category
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
    if not isinstance(result, (list, tuple)) or len(result) < 2:
        return jsonify({"msg": "Error de sesión"}), 401

    user_role_id = result[1]
    tenant_id = get_current_tenant()

    # ------------------ GET (Producto Único) ------------------
    if request.method == 'GET':
        try:
            with get_db_cursor() as cur:
                # Corregido: faltaba coma entre category y stock
                cur.execute(
                    "SELECT id, name, price, category, stock FROM products WHERE id = %s AND tenant_id = %s;",
                    (product_id, tenant_id)
                )
                product = cur.fetchone()
            
            if not product:
                return jsonify({"msg": "Producto no encontrado"}), 404
                
            return jsonify(dict(product)), 200
        except Exception as e:
            app_logger.error(f"Error obteniendo producto: {e}")
            return jsonify({"msg": "Error del servidor"}), 500

    # ------------------ PUT (Actualizar Producto) ------------------
    elif request.method == 'PUT':
        if not check_product_manager_permission(user_role_id):
            return jsonify({"msg": "Acceso denegado"}), 403
        
        data = request.get_json()
        try:
            with get_db_cursor(commit=True) as cur:
                # Agregamos 'category' a los campos permitidos para actualizar
                allowed_keys = {'name': str, 'price': float, 'stock': int, 'category': str}
                updates = []
                params = []
                
                for key, val in data.items():
                    actual_key = 'price' if key == 'price_usd' else key
                    
                    if actual_key in allowed_keys:
                        updates.append(f"{actual_key} = %s")
                        params.append(allowed_keys[actual_key](val))
                
                if not updates:
                    return jsonify({"msg": "No hay datos válidos para actualizar"}), 400
                
                params.extend([product_id, tenant_id])
                
                query = f"""
                    UPDATE products 
                    SET {', '.join(updates)} 
                    WHERE id = %s AND tenant_id = %s 
                    RETURNING id, name, price, stock, category;
                """
                
                cur.execute(query, tuple(params))
                updated = cur.fetchone()
                
                if not updated:
                    return jsonify({"msg": "Producto no encontrado o no pertenece a su negocio"}), 404
                    
                return jsonify(dict(updated)), 200
        except Exception as e:
            app_logger.error(f"Error en actualización (PUT): {e}")
            return jsonify({"msg": "Error al actualizar el producto"}), 500

    # ------------------ DELETE (Eliminar Producto) ------------------
    elif request.method == 'DELETE':
        if not check_product_manager_permission(user_role_id):
            return jsonify({"msg": "Acceso denegado"}), 403
        try:
            with get_db_cursor(commit=True) as cur:
                cur.execute(
                    "DELETE FROM products WHERE id = %s AND tenant_id = %s RETURNING id;",
                    (product_id, tenant_id)
                )
                deleted = cur.fetchone()
                
                if not deleted:
                    return jsonify({"msg": "Producto no encontrado"}), 404
                    
                return jsonify({"msg": "Producto eliminado exitosamente"}), 200
        except Exception as e:
            app_logger.error(f"Error eliminando producto: {e}")
            return jsonify({"msg": "Error al intentar eliminar el producto"}), 500