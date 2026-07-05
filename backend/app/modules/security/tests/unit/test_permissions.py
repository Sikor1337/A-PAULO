from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.core_data.models import User
from app.modules.core_data.repositories import UserRepository
from app.modules.security.models import Permission, UserGroup
from app.modules.security.repositories import PermissionRepository
from app.modules.security.services.permissions import PermissionService


def _service(session: Session) -> PermissionService:
    return PermissionService(
        PermissionRepository(session), UserRepository(session), MagicMock()
    )


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

    service = _service(db_session)
    service.replace_user_groups(user.id, [first.id, second.id], actor=user)

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
        _service(db_session).update_group(group.id, actor=group, name="Changed")

    assert error.value.status_code == 400


def test_system_group_permission_matrix_cannot_be_modified(
    db_session: Session,
) -> None:
    group = UserGroup(
        name="Admin",
        description="Protected",
        is_system=True,
        system_key="admin",
    )
    db_session.add(group)
    db_session.commit()

    with pytest.raises(HTTPException) as error:
        _service(db_session).replace_group_permissions(group.id, [], actor=group)

    assert error.value.status_code == 400


def test_admin_status_without_group_does_not_grant_permissions(
    db_session: Session,
) -> None:
    admin = _user(db_session, "admin-without-group", status="admin")
    db_session.commit()

    permissions = _service(db_session).permissions_for_user(admin)

    assert permissions == set()


def test_default_group_assignment_preserves_explicit_memberships(
    db_session: Session,
) -> None:
    admin_group = UserGroup(
        name="Admin",
        is_system=True,
        system_key="admin",
    )
    staff_group = UserGroup(
        name="Staff",
        is_system=True,
        system_key="staff",
    )
    user = _user(db_session, "regular-with-admin", status="regular")
    db_session.add_all([admin_group, staff_group])
    db_session.flush()
    service = _service(db_session)
    service.replace_user_groups(user.id, [admin_group.id], actor=user)

    service.assign_default_group(user)

    assert service.group_ids_for_user(user.id) == sorted(
        [admin_group.id, staff_group.id]
    )

    service.remove_system_group(user, "staff")

    assert service.group_ids_for_user(user.id) == [admin_group.id]
