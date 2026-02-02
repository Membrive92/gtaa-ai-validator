"""
API test de ejemplo — NO debe generar ADAPTATION_IN_DEFINITION.

Este archivo simula un test de API típico que usa requests.
El clasificador debe detectarlo como "api" y saltar las reglas UI-only.
"""
import requests


def test_get_users():
    response = requests.get("http://localhost:8080/api/users")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_create_user():
    payload = {"name": "Test User", "email": "test@example.com"}
    response = requests.post("http://localhost:8080/api/users", json=payload)
    assert response.status_code == 201


def test_1():
    """Este test tiene POOR_TEST_NAMING — aplica también en API tests."""
    pass
