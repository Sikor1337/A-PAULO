"""Data access for user groups and permissions."""

from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from app.modules.security.models import (
    Permission,
    UserGroup,
    security_user_groups,
)


class PermissionRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_permissions(self) -> list[Permission]:
        return (
            self.session.query(Permission)
            .order_by(Permission.category, Permission.name)
            .all()
        )

    def get_permissions_by_codes(self, codes: set[str]) -> list[Permission]:
        if not codes:
            return []
        return self.session.query(Permission).filter(Permission.code.in_(codes)).all()

    def list_groups(self) -> list[UserGroup]:
        return (
            self.session.query(UserGroup)
            .order_by(UserGroup.is_system.desc(), UserGroup.name)
            .all()
        )

    def get_group(self, group_id: int) -> UserGroup | None:
        return self.session.query(UserGroup).filter_by(id=group_id).first()

    def get_group_by_system_key(self, system_key: str) -> UserGroup | None:
        return self.session.query(UserGroup).filter_by(system_key=system_key).first()

    def create_group(self, **values) -> UserGroup:
        group = UserGroup(**values)
        self.session.add(group)
        return group

    def delete_group(self, group: UserGroup) -> None:
        self.session.delete(group)

    def permission_codes_for_user(self, user_id: int) -> set[str]:
        statement = (
            select(Permission.code)
            .join(UserGroup.permissions)
            .join(security_user_groups, security_user_groups.c.group_id == UserGroup.id)
            .where(security_user_groups.c.user_id == user_id)
        )
        return set(self.session.execute(statement).scalars().all())

    def group_ids_for_user(self, user_id: int) -> list[int]:
        statement = select(security_user_groups.c.group_id).where(
            security_user_groups.c.user_id == user_id
        )
        return list(self.session.execute(statement).scalars().all())

    def user_ids_for_group(self, group_id: int) -> list[int]:
        statement = select(security_user_groups.c.user_id).where(
            security_user_groups.c.group_id == group_id
        )
        return list(self.session.execute(statement).scalars().all())

    def replace_user_groups(self, user_id: int, group_ids: set[int]) -> None:
        self.session.execute(
            delete(security_user_groups).where(
                security_user_groups.c.user_id == user_id
            )
        )
        if group_ids:
            self.session.execute(
                insert(security_user_groups),
                [{"user_id": user_id, "group_id": group_id} for group_id in group_ids],
            )

    def replace_group_users(self, group_id: int, user_ids: set[int]) -> None:
        self.session.execute(
            delete(security_user_groups).where(
                security_user_groups.c.group_id == group_id
            )
        )
        if user_ids:
            self.session.execute(
                insert(security_user_groups),
                [{"user_id": user_id, "group_id": group_id} for user_id in user_ids],
            )
