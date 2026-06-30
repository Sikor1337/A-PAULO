from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.modules.security.schemas import LoginRequest, ProfileUpdateRequest
from app.modules.security.services.auth import AuthService


@pytest.fixture
def session() -> MagicMock:
    return MagicMock()


@pytest.fixture
def repo(session: MagicMock) -> MagicMock:
    repository = MagicMock()
    repository.session = session
    return repository


@pytest.fixture
def token_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(
    repo: MagicMock,
    token_service: MagicMock,
    session: MagicMock,
) -> AuthService:
    return AuthService(repo, token_service, session)


def test_register_normalizes_fields_hashes_password_and_commits(
    service: AuthService,
    repo: MagicMock,
    session: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = SimpleNamespace(id=1)
    repo.get_by_username.return_value = None
    repo.get_by_email.return_value = None
    repo.create.return_value = user
    monkeypatch.setattr(
        "app.modules.security.services.auth.hash_password",
        lambda password: f"hashed:{password}",
    )

    result = service.register(
        username="  NewUser  ",
        email="  USER@EXAMPLE.COM  ",
        password="StrongPass123",
        first_name="Jan",
        last_name="Kowalski",
    )

    assert result is user
    repo.get_by_username.assert_called_once_with("newuser")
    repo.get_by_email.assert_called_once_with("user@example.com")
    repo.create.assert_called_once_with(
        username="newuser",
        email="user@example.com",
        hashed_password="hashed:StrongPass123",
        first_name="Jan",
        last_name="Kowalski",
        status="new_volunteer",
    )
    session.flush.assert_called_once()
    session.refresh.assert_called_once_with(user)
    session.commit.assert_called_once()
    session.rollback.assert_not_called()


def test_register_rolls_back_when_username_exists(
    service: AuthService,
    repo: MagicMock,
    session: MagicMock,
) -> None:
    repo.get_by_username.return_value = SimpleNamespace(id=1)

    with pytest.raises(HTTPException) as exc_info:
        service.register(
            username="existing",
            email="new@example.com",
            password="StrongPass123",
        )

    assert exc_info.value.status_code == 409
    repo.create.assert_not_called()
    session.commit.assert_not_called()
    session.rollback.assert_called_once()


def test_register_claims_a_migrated_recruitment_account(
    service: AuthService,
    repo: MagicMock,
    session: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    migrated_user = SimpleNamespace(
        id=5,
        username="legacy_recruitment_5_deadbeef",
        email="candidate@example.com",
        first_name="Candidate",
        last_name="",
        is_active=False,
        status="regular",
        hashed_password="!migration-unusable!",
    )
    repo.get_by_username.return_value = None
    repo.get_by_email.return_value = migrated_user
    repo.update.return_value = migrated_user
    monkeypatch.setattr(
        "app.modules.security.services.auth.hash_password",
        lambda password: f"hashed:{password}",
    )

    result = service.register(
        username="candidate",
        email="candidate@example.com",
        password="StrongPass123",
        first_name="Anna",
        last_name="Nowak",
    )

    assert result is migrated_user
    repo.create.assert_not_called()
    repo.update.assert_called_once_with(
        migrated_user,
        username="candidate",
        hashed_password="hashed:StrongPass123",
        first_name="Anna",
        last_name="Nowak",
        status="regular",
        is_active=True,
    )
    session.commit.assert_called_once()


def test_login_uses_username_then_email_and_issues_tokens(
    service: AuthService,
    repo: MagicMock,
    token_service: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = SimpleNamespace(id=42, is_active=True, hashed_password="stored-hash")
    repo.get_by_username.return_value = None
    repo.get_by_email.return_value = user
    token_service.create_access_token.return_value = "access-token"
    token_service.create_refresh_token.return_value = "refresh-token"
    monkeypatch.setattr(
        "app.modules.security.services.auth.verify_password",
        lambda plain, hashed: plain == "StrongPass123" and hashed == "stored-hash",
    )

    token = service.login(
        LoginRequest(username=" USER@EXAMPLE.COM ", password="StrongPass123")
    )

    assert token.access == "access-token"
    assert token.refresh == "refresh-token"
    repo.get_by_username.assert_called_once_with("user@example.com")
    repo.get_by_email.assert_called_once_with("user@example.com")
    token_service.create_access_token.assert_called_once_with({"sub": "42"})
    token_service.create_refresh_token.assert_called_once_with({"sub": "42"})


def test_login_rejects_invalid_credentials(
    service: AuthService,
    repo: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo.get_by_username.return_value = None
    repo.get_by_email.return_value = None
    monkeypatch.setattr(
        "app.modules.security.services.auth.verify_password",
        lambda plain, hashed: True,
    )

    with pytest.raises(HTTPException) as exc_info:
        service.login(LoginRequest(username="user@example.com", password="bad"))

    assert exc_info.value.status_code == 401


def test_update_profile_requires_current_password_for_password_change(
    service: AuthService,
    session: MagicMock,
) -> None:
    user = SimpleNamespace(
        id=1,
        email="user@example.com",
        hashed_password="stored-hash",
    )

    with pytest.raises(HTTPException) as exc_info:
        service.update_profile(
            user,
            ProfileUpdateRequest(new_password="NewStrongPass123"),
        )

    assert exc_info.value.status_code == 400
    session.rollback.assert_called_once()


def test_refresh_rejects_non_refresh_token(
    service: AuthService,
    token_service: MagicMock,
) -> None:
    token_service.decode_token.return_value = {"sub": "42", "type": "access"}

    with pytest.raises(HTTPException) as exc_info:
        service.refresh("access-token")

    assert exc_info.value.status_code == 401
