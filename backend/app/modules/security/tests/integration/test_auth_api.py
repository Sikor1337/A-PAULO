import re
from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.errors import register_error_handlers
from app.infrastructure.email.port import EmailMessage
from app.modules.core_data.repositories import UserRepository
from app.modules.recruitment.access import get_recruitment_access_token
from app.modules.security.api import router
from app.modules.security.dependencies import get_email_backend
from app.modules.security.models import UserGroup
from app.modules.security.repositories import PermissionRepository
from app.modules.security.services.permissions import PermissionService


def permission_service(session: Session) -> PermissionService:
    return PermissionService(
        PermissionRepository(session), UserRepository(session), MagicMock()
    )


class CapturingEmailBackend:
    """Records sent messages so tests can read tokens from the links."""

    def __init__(self) -> None:
        self.messages: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> None:
        self.messages.append(message)

    def last_token(self) -> str:
        match = re.search(r"token=([\w\-]+)", self.messages[-1].html)
        assert match, "no token link in the last e-mail"
        return match.group(1)


@pytest.fixture
def emails() -> CapturingEmailBackend:
    return CapturingEmailBackend()


@pytest.fixture
def auth_client(
    db_session: Session, emails: CapturingEmailBackend
) -> Generator[TestClient, None, None]:
    db_session.add(
        UserGroup(
            name="Staff",
            description="Default application access",
            is_system=True,
            system_key="staff",
        )
    )
    db_session.commit()
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(router)

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_email_backend] = lambda: emails
    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


def _verify(auth_client: TestClient, emails: CapturingEmailBackend) -> None:
    response = auth_client.post(
        "/auth/verify-email", json={"token": emails.last_token()}
    )
    assert response.status_code == 204


def test_register_login_refresh_and_current_user(
    auth_client: TestClient,
    emails: CapturingEmailBackend,
    db_session: Session,
) -> None:
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
    assert register_response.json()["status"] == "regular"
    registered_id = register_response.json()["id"]
    assert len(permission_service(db_session).group_ids_for_user(registered_id)) == 1

    # Login is blocked until the e-mail address is confirmed.
    blocked = auth_client.post(
        "/auth/token",
        json={"username": "newuser@example.com", "password": "StrongPass123"},
    )
    assert blocked.status_code == 403

    _verify(auth_client, emails)

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


def test_register_from_recruitment_link_creates_candidate(
    auth_client: TestClient,
    db_session: Session,
) -> None:
    response = auth_client.post(
        "/auth/register",
        json={
            "username": "candidate",
            "email": "candidate@example.com",
            "password": "StrongPass123",
            "recruitment_token": get_recruitment_access_token(),
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "new_volunteer"
    assert (
        permission_service(db_session).group_ids_for_user(response.json()["id"]) == []
    )


def test_register_rejects_invalid_recruitment_link(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/auth/register",
        json={
            "username": "candidate",
            "email": "candidate@example.com",
            "password": "StrongPass123",
            "recruitment_token": "a" * 64,
        },
    )

    assert response.status_code == 422


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


def test_verify_email_rejects_unknown_token(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/auth/verify-email", json={"token": "x" * 40}
    )
    assert response.status_code == 422


def test_password_reset_flow(
    auth_client: TestClient, emails: CapturingEmailBackend
) -> None:
    auth_client.post(
        "/auth/register",
        json={
            "username": "reset-user",
            "email": "reset@example.com",
            "password": "OldPass123",
        },
    )
    _verify(auth_client, emails)

    requested = auth_client.post(
        "/auth/password-reset/request", json={"email": "reset@example.com"}
    )
    assert requested.status_code == 202
    reset_token = emails.last_token()

    confirmed = auth_client.post(
        "/auth/password-reset/confirm",
        json={"token": reset_token, "new_password": "BrandNew123"},
    )
    assert confirmed.status_code == 204

    # Old password no longer works; the new one does.
    assert (
        auth_client.post(
            "/auth/token",
            json={"username": "reset@example.com", "password": "OldPass123"},
        ).status_code
        == 401
    )
    assert (
        auth_client.post(
            "/auth/token",
            json={"username": "reset@example.com", "password": "BrandNew123"},
        ).status_code
        == 200
    )

    # The reset token is single-use.
    reused = auth_client.post(
        "/auth/password-reset/confirm",
        json={"token": reset_token, "new_password": "Another123"},
    )
    assert reused.status_code == 422


def test_password_reset_request_unknown_email_is_silent(
    auth_client: TestClient, emails: CapturingEmailBackend
) -> None:
    response = auth_client.post(
        "/auth/password-reset/request", json={"email": "ghost@example.com"}
    )
    assert response.status_code == 202
    assert emails.messages == []
