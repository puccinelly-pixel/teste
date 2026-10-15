"""Testes de cadastro, login e proteção das rotas."""

from tests.conftest import register


def test_register_returns_token(client):
    response = client.post(
        "/auth/register",
        json={"nome": "Ana", "email": "Ana@Example.com", "senha": "senha123"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["usuario"]["email"] == "ana@example.com"
    assert "senha" not in body["usuario"]
    assert "senha_hash" not in body["usuario"]


def test_register_duplicate_email(client):
    register(client)
    response = client.post(
        "/auth/register",
        json={"nome": "Ana 2", "email": "ANA@example.com", "senha": "senha123"},
    )
    assert response.status_code == 409


def test_register_rejects_weak_password(client):
    response = client.post(
        "/auth/register",
        json={"nome": "Ana", "email": "ana@example.com", "senha": "abcdefgh"},
    )
    assert response.status_code == 422


def test_login_success(client):
    register(client)
    response = client.post(
        "/auth/login", json={"email": "ana@example.com", "senha": "senha123"}
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_wrong_password_and_unknown_email_same_message(client):
    register(client)
    wrong = client.post(
        "/auth/login", json={"email": "ana@example.com", "senha": "errada123"}
    )
    unknown = client.post(
        "/auth/login", json={"email": "x@example.com", "senha": "senha123"}
    )
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["detail"] == unknown.json()["detail"]


def test_login_rate_limit(client):
    register(client)
    payload = {"email": "ana@example.com", "senha": "errada123"}
    statuses = [client.post("/auth/login", json=payload).status_code
                for _ in range(6)]
    assert statuses[:5] == [401] * 5
    assert statuses[5] == 429


def test_me_requires_token(client, auth_headers):
    assert client.get("/auth/me").status_code == 401
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["nome"] == "Ana"


def test_invalid_token_rejected(client):
    headers = {"Authorization": "Bearer token.invalido.aqui"}
    assert client.get("/tasks", headers=headers).status_code == 401


def test_security_headers(client):
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
