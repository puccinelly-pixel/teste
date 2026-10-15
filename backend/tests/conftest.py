"""Fixtures dos testes: banco SQLite em memória isolado por teste."""

import os

os.environ.setdefault("SECRET_KEY", "chave-somente-para-testes-" + "x" * 40)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.security import login_limiter  # noqa: E402


@pytest.fixture()
def client():
    """Cliente HTTP com um banco novo em memória para cada teste."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    login_limiter.reset()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


def register(client, email="ana@example.com", senha="senha123", nome="Ana"):
    """Cadastra um usuário e retorna o header de autorização."""
    response = client.post(
        "/auth/register",
        json={"nome": nome, "email": email, "senha": senha},
    )
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def auth_headers(client):
    """Headers de um usuário já cadastrado."""
    return register(client)
