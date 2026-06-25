from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.core.errors import ConflictError, NotFoundError
from app.modules.core_data.services.users import UserService


@pytest.fixture
def session() -> MagicMock:
    return MagicMock()


@pytest.fixture
def repo() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(session: MagicMock, repo: MagicMock) -> UserService:
    service = UserService.__new__(UserService)
    service.session = session
    service.user_repo = repo
    service.settings = SimpleNamespace(
        secret_key="test-secret",
        algorithm="HS256",
        access_token_expire_minutes=120,
    )
    return service


def test_create_user_normalizes_credentials_hashes_password_and_commits(
    service: UserService,
    repo: MagicMock,
    session: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_user = SimpleNamespace(id=1)
    repo.get_by_username.return_value = None
    repo.get_by_email.return_value = None
    repo.create.return_value = created_user
    monkeypatch.setattr(
        "app.modules.core_data.services.users.hash_password",
        lambda password: f"hashed:{password}",
    )

    result = service.create_user(
        username="  AdminUser  ",
        email="  ADMIN@EXAMPLE.COM ",
        password="StrongPass123",
        first_name="Ala",
        last_name="Admin",
        status="admin",
        is_active=False,
    )

    assert result is created_user
    repo.get_by_username.assert_called_once_with("adminuser")
    repo.get_by_email.assert_called_once_with("admin@example.com")
    repo.create.assert_called_once_with(
        username="adminuser",
        email="admin@example.com",
        hashed_password="hashed:StrongPass123",
        first_name="Ala",
        last_name="Admin",
        status="admin",
        is_active=False,
    )
    session.flush.assert_called_once()
    session.refresh.assert_called_once_with(created_user)
    session.commit.assert_called_once()


def test_create_user_rolls_back_on_duplicate_email(
    service: UserService,
    repo: MagicMock,
    session: MagicMock,
) -> None:
    repo.get_by_username.return_value = None
    repo.get_by_email.return_value = SimpleNamespace(id=2)

    with pytest.raises(ConflictError):
        service.create_user(
            username="new-user",
            email="taken@example.com",
            password="StrongPass123",
        )

    repo.create.assert_not_called()
    session.rollback.assert_called_once()


def test_update_user_normalizes_unique_fields_and_hashes_password(
    service: UserService,
    repo: MagicMock,
    session: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = SimpleNamespace(id=1, username="old", email="old@example.com")
    repo.get_by_id.return_value = user
    repo.get_by_username.return_value = None
    repo.get_by_email.return_value = None
    repo.update.return_value = user
    monkeypatch.setattr(
        "app.modules.core_data.services.users.hash_password",
        lambda password: f"hashed:{password}",
    )

    result = service.update_user(
        1,
        username=" NewName ",
        email=" New@Example.com ",
        password="NewStrongPass123",
    )

    assert result is user
    repo.update.assert_called_once_with(
        user,
        username="newname",
        email="new@example.com",
        hashed_password="hashed:NewStrongPass123",
    )
    session.commit.assert_called_once()


def test_update_user_rejects_duplicate_username(
    service: UserService,
    repo: MagicMock,
    session: MagicMock,
) -> None:
    user = SimpleNamespace(id=1, username="old")
    repo.get_by_id.return_value = user
    repo.get_by_username.return_value = SimpleNamespace(id=2)

    with pytest.raises(ConflictError):
        service.update_user(1, username="taken")

    repo.update.assert_not_called()
    session.rollback.assert_called_once()


def test_delete_user_rejects_self_delete(
    service: UserService,
    repo: MagicMock,
    session: MagicMock,
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        service.delete_user(7, current_user_id=7)

    assert exc_info.value.status_code == 400
    repo.delete.assert_not_called()
    session.rollback.assert_not_called()


def test_get_user_by_id_raises_not_found_when_missing(
    service: UserService,
    repo: MagicMock,
) -> None:
    repo.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.get_user_by_id(404)
