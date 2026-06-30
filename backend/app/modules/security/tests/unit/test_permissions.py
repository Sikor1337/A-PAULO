from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.core_data.models import User
from app.modules.security.models import Permission, UserGroup
from app.modules.security.services.permissions import PermissionService


def _user(session: Session, username: str, status: str = "new_volunteer") -> User:
    user = User(
        username=username,
        email=f"{username}@example.org",
        hashed_password="unused",
        status=status,
    )
    session.add(user)
    session.flush()
    return user


def test_user_inherits_union_of_permissions_from_multiple_groups(
    db_session: Session,
) -> None:
    view = Permission(code="CAN_VIEW_USERS", name="View", category="Users")
    manage = Permission(code="CAN_MANAGE_USERS", name="Manage", category="Users")
    first = UserGroup(name="Data provider", permissions=[view])
    second = UserGroup(name="Reviewer", permissions=[manage])
    user = _user(db_session, "ala")
    db_session.add_all([first, second])
    db_session.flush()

    service = PermissionService(db_session)
    service.replace_user_groups(user.id, [first.id, second.id])

    assert service.permissions_for_user(user) == {
        "CAN_VIEW_USERS",
        "CAN_MANAGE_USERS",
    }


def test_system_group_definition_cannot_be_modified(db_session: Session) -> None:
    group = UserGroup(
        name="Admin",
        description="Protected",
        is_system=True,
        system_key="admin",
    )
    db_session.add(group)
    db_session.commit()

    with pytest.raises(HTTPException) as error:
        PermissionService(db_session).update_group(group.id, name="Changed")

    assert error.value.status_code == 400


def test_admin_status_is_a_lockout_safe_fallback(db_session: Session) -> None:
    admin = SimpleNamespace(id=999, status="admin")

    permissions = PermissionService(db_session).permissions_for_user(admin)

    assert "CAN_MANAGE_SECURITY" in permissions
    assert "CAN_MANAGE_USERS" in permissions
