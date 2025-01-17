import pytest
import requests

BASE_URL = "http://127.0.0.1:5000"

def test_home():
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    assert response.json()["message"] == "Welcome to the Business Solver API!"

def test_register():
    response = requests.post(f"{BASE_URL}/register", json={
        "email": "testuser@example.com",
        "password": "Test1234"
    })
    assert response.status_code == 201
    assert response.json()["message"] == "User registered successfully!"

def test_login():
    response = requests.post(f"{BASE_URL}/login", json={
        "email": "testuser@example.com",
        "password": "Test1234"
    })
    assert response.status_code == 200
    assert "token" in response.json()

def test_secured_route():
    login_response = requests.post(f"{BASE_URL}/login", json={
        "email": "testuser@example.com",
        "password": "Test1234"
    })
    token = login_response.json()["token"]
    response = requests.get(f"{BASE_URL}/test", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    assert response.json()["message"] == "Connection successful!"
