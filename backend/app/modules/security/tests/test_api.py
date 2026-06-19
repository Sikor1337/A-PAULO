from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.security.api import router
from app.modules.security.dependencies import get_auth_service


def build_client(
    auth_service: MagicMock,
) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    return TestClient(app)


def test_login_endpoint_supports_username_or_email() -> None:
    """Test that login endpoint accepts username or email."""
    auth_service = MagicMock()
    auth_service.login.return_value = SimpleNamespace(
        access="access-token",
        refresh="refresh-token",
    )
    client = build_client(auth_service)

    # Test with email
    response = client.post(
        "/auth/token",
        json={"username": "user@example.com", "password": "StrongPass123"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "access": "access-token",
        "refresh": "refresh-token",
    }
    auth_service.login.assert_called_once()
    assert auth_service.login.call_args.args[0].username == "user@example.com"


def test_register_endpoint() -> None:
    """Test user registration endpoint."""
    auth_service = MagicMock()
    auth_service.register.return_value = SimpleNamespace(
        id=1,
        username="newuser",
        email="newuser@example.com",
        first_name="John",
        last_name="Doe",
        status="regular",
    )
    client = build_client(auth_service)

    response = client.post(
        "/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "StrongPass123",
            "first_name": "John",
            "last_name": "Doe",
        },
    )

    assert response.status_code == 200
    assert response.json()["username"] == "newuser"
    auth_service.register.assert_called_once()


def test_refresh_token_endpoint() -> None:
    """Test token refresh endpoint."""
    auth_service = MagicMock()
    auth_service.refresh.return_value = SimpleNamespace(
        access="new-access-token",
        refresh="new-refresh-token",
    )
    client = build_client(auth_service)

    response = client.post(
        "/auth/token/refresh",
        json={"refresh": "old-refresh-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "access": "new-access-token",
        "refresh": "new-refresh-token",
    }
    auth_service.refresh.assert_called_once()
