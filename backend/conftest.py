"""Shared pytest fixtures for backend tests."""

import os
from collections.abc import Generator
from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ALGORITHM"] = "HS256"

from app.core.dependencies import get_db  # noqa: E402
from app.core.errors import register_error_handlers  # noqa: E402
from app.infrastructure.sql.base import Base  # noqa: E402
from app.infrastructure.sql import models_registry  # noqa: F401, E402
from app.modules.attachments.api import router as attachments_router  # noqa: E402
from app.modules.calendar.api import router as calendar_router  # noqa: E402
from app.modules.core_data.api.users import router as users_router  # noqa: E402
from app.modules.core_data.models import User  # noqa: E402
from app.modules.departments.api import router as departments_router  # noqa: E402
from app.modules.pi.api.beneficiaries import router as beneficiaries_router  # noqa: E402
from app.modules.pi.api.functions import router as functions_router  # noqa: E402
from app.modules.pi.api.groups import router as groups_router  # noqa: E402
from app.modules.pi.api.volunteers import router as volunteers_router  # noqa: E402
from app.modules.recruitment.api import router as recruitment_router  # noqa: E402
from app.modules.security.api import router as security_router  # noqa: E402
from app.modules.security.dependencies import (  # noqa: E402
    get_current_user,
    require_admin,
)
from app.modules.security.models import (  # noqa: E402
    Permission,
    UserGroup,
    security_user_groups,
)
from app.modules.security.models.constants import PERMISSION_CATALOG  # noqa: E402


@pytest.fixture
def db_engine() -> Generator[Engine, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def db_session(db_engine: Engine) -> Generator[Session, None, None]:
    session_factory = sessionmaker(bind=db_engine, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def admin_user(db_session: Session) -> User:
    user = User(
        id=999,
        username="admin",
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        hashed_password="not-used",
        status="admin",
        is_active=True,
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 1, 1),
    )
    permissions = [
        Permission(code=code, name=name, category=category)
        for code, name, category in PERMISSION_CATALOG
    ]
    admin_group = UserGroup(
        name="Admin",
        description="System test administrator group",
        is_system=True,
        system_key="admin",
        permissions=permissions,
    )
    db_session.add_all([user, admin_group])
    db_session.flush()
    db_session.execute(
        security_user_groups.insert(),
        {"user_id": user.id, "group_id": admin_group.id},
    )
    db_session.commit()
    return user


@pytest.fixture
def api_client(
    db_session: Session,
    admin_user: User,
) -> Generator[TestClient, None, None]:
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(security_router)
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(volunteers_router, prefix="/api/v1")
    app.include_router(functions_router, prefix="/api/v1")
    app.include_router(beneficiaries_router, prefix="/api/v1")
    app.include_router(groups_router, prefix="/api/v1")
    app.include_router(attachments_router, prefix="/api/v1")
    app.include_router(departments_router, prefix="/api/v1")
    app.include_router(recruitment_router, prefix="/api/v1")
    app.include_router(calendar_router, prefix="/api/v1")

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
