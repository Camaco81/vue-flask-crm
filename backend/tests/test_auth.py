import requests
import os
import json
import pytest
import time
global ACCESS_TOKEN
# URL base de tu API
BASE_URL = "http://localhost:5000"

# Datos de prueba para el registro y login
user_data = {
    "email": "test@example.com",
    "password": "password123"
}

# Variable global para almacenar el token de acceso
ACCESS_TOKEN = None

@pytest.fixture(scope="module")
def setup_api_server():
    # Asume que tu servidor Flask ya está corriendo en localhost:5000
    # En un entorno de CI/CD, esto se haría con un comando de arranque.
    yield
@pytest.fixture(scope="module", autouse=True)
def cleanup_user():
    """Limpia el usuario de prueba de la base de datos antes y después de las pruebas."""
    # Esperar un poco para que el servidor inicie
    time.sleep(1)
    
    # Limpiar antes de las pruebas
    delete_user()
    
    yield # Aquí se ejecutan las pruebas
    
    # Limpiar después de las pruebas
    delete_user()

def delete_user():
    """Función auxiliar para eliminar el usuario de prueba."""
    try:
        requests.post(f"{BASE_URL}/delete_user", json={"email": user_data["email"]})
    except requests.exceptions.ConnectionError as e:
        print(f"Error al intentar limpiar el usuario: {e}")

def test_1_register_user_success(setup_api_server):
    """Prueba que un nuevo usuario se pueda registrar exitosamente."""
    response = requests.post(f"{BASE_URL}/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert "Usuario registrado con éxito" in data["msg"]
    assert "user_id" in data

def test_2_register_existing_user_failure():
    """Prueba que el registro de un email ya existente falle."""
    response = requests.post(f"{BASE_URL}/register", json=user_data)
    assert response.status_code == 409
    data = response.json()
    assert "Este email ya está registrado" in data["msg"]

def test_3_login_user_success():
    """Prueba que un usuario se pueda loguear y obtenga un token."""
    global ACCESS_TOKEN
    response = requests.post(f"{BASE_URL}/login", json=user_data)
    assert response.status_code == 200

    # Extrae el token de la respuesta JSON y lo guarda en la variable global
    data = response.json()
    assert "access_token" in data
    ACCESS_TOKEN = data["access_token"]

def test_4_login_with_incorrect_password_failure():
    """Prueba que el login falle con una contraseña incorrecta."""
    incorrect_data = {
        "email": user_data["email"],
        "password": "wrongpassword"
    }
    response = requests.post(f"{BASE_URL}/login", json=incorrect_data)
    assert response.status_code == 401
    data = response.json()
    assert "Credenciales incorrectas" in data["msg"]

def test_5_access_protected_route_success():
    """Prueba que se pueda acceder a una ruta protegida con un token válido."""
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    response = requests.get(f"{BASE_URL}/protected", headers=headers)
    assert response.status_code == 200

def test_6_access_protected_route_failure():
    """Prueba que no se pueda acceder a una ruta protegida sin un token."""
    response = requests.get(f"{BASE_URL}/protected")
    assert response.status_code == 401
    data = response.json()
    assert "Missing Authorization Header" in data["msg"]