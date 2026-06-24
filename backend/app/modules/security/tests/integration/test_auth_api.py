from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.errors import register_error_handlers
from app.modules.security.api import router


@pytest.fixture
def auth_client(db_session: Session) -> Generator[TestClient, None, None]:
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(router)

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


def test_register_login_refresh_and_current_user(auth_client: TestClient) -> None:
    register_response = auth_client.post(
        "/auth/register",
        json={
            "username": "NewUser",
            "email": "NewUser@example.com",
            "password": "StrongPass123",
            "first_name": "Jan",
            "last_name": "Kowalski",
        },
    )
    assert register_response.status_code == 200
    assert register_response.json()["username"] == "newuser"
    assert register_response.json()["email"] == "newuser@example.com"

    login_response = auth_client.post(
        "/auth/token",
        json={
            "username": "newuser@example.com",
            "password": "StrongPass123",
        },
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert tokens["access"]
    assert tokens["refresh"]

    refresh_response = auth_client.post(
        "/auth/token/refresh",
        json={"refresh": tokens["refresh"]},
    )
    assert refresh_response.status_code == 200
    assert refresh_response.json()["access"]

    current_user_response = auth_client.get(
        "/auth/user",
        headers={"Authorization": f"Bearer {tokens['access']}"},
    )
    assert current_user_response.status_code == 200
    assert current_user_response.json()["email"] == "newuser@example.com"


def test_register_rejects_duplicate_username(auth_client: TestClient) -> None:
    payload = {
        "username": "duplicate",
        "email": "first@example.com",
        "password": "StrongPass123",
    }
    assert auth_client.post("/auth/register", json=payload).status_code == 200

    response = auth_client.post(
        "/auth/register",
        json={**payload, "email": "second@example.com"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Username 'duplicate' already exists"


def test_login_rejects_wrong_password(auth_client: TestClient) -> None:
    auth_client.post(
        "/auth/register",
        json={
            "username": "login-user",
            "email": "login@example.com",
            "password": "StrongPass123",
        },
    )

    response = auth_client.post(
        "/auth/token",
        json={"username": "login@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
