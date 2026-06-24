from collections.abc import Generator
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.errors import register_error_handlers
from app.modules.core_data.api.users import router as users_router
from app.modules.core_data.repositories.users import UserRepository
from app.modules.security.dependencies import get_current_user


def test_user_repository_filters_and_counts_users(db_session: Session) -> None:
    repo = UserRepository(db_session)
    repo.create(
        username="anna",
        email="anna@example.com",
        hashed_password="hash",
        first_name="Anna",
        last_name="Nowak",
        status="admin",
        is_active=True,
    )
    repo.create(
        username="jan",
        email="jan@example.com",
        hashed_password="hash",
        first_name="Jan",
        last_name="Kowalski",
        status="regular",
        is_active=False,
    )
    db_session.commit()

    active_admins = repo.list_all(search="anna", status="admin", is_active=True)
    inactive_count = repo.count(is_active=False)

    assert [user.username for user in active_admins] == ["anna"]
    assert inactive_count == 1
    assert repo.exists(email="jan@example.com") is True
    assert repo.exists(username="missing") is False


def test_users_api_supports_admin_crud_flow(api_client) -> None:
    create_response = api_client.post(
        "/api/v1/users",
        json={
            "username": "PanelUser",
            "email": "panel@example.com",
            "password": "StrongPass123",
            "first_name": "Panel",
            "last_name": "User",
            "status": "regular",
            "is_active": True,
        },
    )
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["username"] == "paneluser"

    list_response = api_client.get("/api/v1/users", params={"search": "panel"})
    assert list_response.status_code == 200
    assert [user["email"] for user in list_response.json()] == ["panel@example.com"]

    update_response = api_client.patch(
        f"/api/v1/users/{created['id']}",
        json={"email": "updated@example.com", "status": "admin"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["email"] == "updated@example.com"
    assert update_response.json()["status"] == "admin"

    delete_response = api_client.delete(f"/api/v1/users/{created['id']}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": "User deleted successfully"}

    missing_response = api_client.get(f"/api/v1/users/{created['id']}")
    assert missing_response.status_code == 404


def test_users_api_rejects_non_admin_user(db_session: Session) -> None:
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(users_router, prefix="/api/v1")

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=7,
        status="regular",
    )

    with TestClient(app) as client:
        response = client.get("/api/v1/users")

    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"
