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
    """Extrae el tenant_id del token JWT."""
    return get_jwt().get('tenant_id', 'default-tenant')

@product_bp.route('', methods=['GET', 'POST'])
@jwt_required()
def products_collection():
    current_user_id, user_role_id = get_user_and_role()
    tenant_id = get_current_tenant()
    
    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado"}), 401
    
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
            
            if price <= 0 or stock < 0:
                return jsonify({"msg": "Precio debe ser positivo y Stock no negativo"}), 400

            with get_db_cursor(commit=True) as cur:
                cur.execute(
                    """INSERT INTO products (name, price, stock, tenant_id) 
                       VALUES (%s, %s, %s, %s) 
                       RETURNING id, name, price, stock;""",
                    (name, price, stock, tenant_id)
                )
                new_product = cur.fetchone()
                
            return jsonify(dict(new_product)), 201

        except (ValueError, TypeError):
            return jsonify({"msg": "Formato de datos inválido"}), 400
        except Exception as e:
            app_logger.error(f"Error creando producto: {e}")
            return jsonify({"msg": "Error interno"}), 500

    # ------------------ GET (Listar Productos del Tenant) ------------------
    elif request.method == 'GET':
        try:
            with get_db_cursor() as cur:
                cur.execute(
                    "SELECT id, name, price, stock FROM products WHERE tenant_id = %s ORDER BY name;",
                    (tenant_id,)
                )
                return jsonify([dict(p) for p in cur.fetchall()]), 200
        except Exception as e:
            app_logger.error(f"Error listando productos: {e}")
            return jsonify({"msg": "Error al obtener productos"}), 500

@product_bp.route('/<string:product_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def product_single(product_id):
    current_user_id, user_role_id = get_user_and_role()
    tenant_id = get_current_tenant()

    if not current_user_id:
        return jsonify({"msg": "Usuario no encontrado"}), 401

    # ------------------ GET (Producto Único) ------------------
    if request.method == 'GET':
        try:
            with get_db_cursor() as cur:
                cur.execute(
                    "SELECT id, name, price, stock FROM products WHERE id = %s AND tenant_id = %s;",
                    (product_id, tenant_id)
                )
                product = cur.fetchone()
            return jsonify(dict(product)) if product else (jsonify({"msg": "Producto no encontrado"}), 404)
        except Exception as e:
            return jsonify({"msg": "Error"}), 500

    # ------------------ PUT (Actualizar Producto) ------------------
    elif request.method == 'PUT':
        if not check_product_manager_permission(user_role_id):
            return jsonify({"msg": "Acceso denegado"}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"msg": "No hay datos para actualizar"}), 400
        
        try:
            with get_db_cursor(commit=True) as cur:
                # Construcción dinámica de la consulta para actualizar solo lo enviado
                allowed_keys = {'name': str, 'price': float, 'stock': int}
                updates = []
                params = []
                
                for key, val in data.items():
                    if key in allowed_keys:
                        # Validaciones rápidas
                        clean_val = val.strip() if key == 'name' else allowed_keys[key](val)
                        if key == 'price' and clean_val <= 0: continue
                        if key == 'stock' and clean_val < 0: continue
                        
                        updates.append(f"{key} = %s")
                        params.append(clean_val)
                
                if not updates:
                    return jsonify({"msg": "Nada que actualizar"}), 400
                
                params.extend([product_id, tenant_id])
                query = f"UPDATE products SET {', '.join(updates)} WHERE id = %s AND tenant_id = %s RETURNING id, name, price, stock;"
                
                cur.execute(query, tuple(params))
                updated = cur.fetchone()
                
                return jsonify(dict(updated)) if updated else (jsonify({"msg": "Producto no encontrado"}), 404)

        except Exception as e:
            app_logger.error(f"Error en PUT producto: {e}")
            return jsonify({"msg": "Error al actualizar"}), 500

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
                return jsonify({"msg": "Eliminado"}), 200 if cur.fetchone() else (jsonify({"msg": "No encontrado"}), 404)
        except Exception as e:
            return jsonify({"msg": "Error al eliminar"}), 500