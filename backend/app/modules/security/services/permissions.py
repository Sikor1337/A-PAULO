"""Permission resolution and user-group management rules."""

from fastapi import HTTPException, status

from app.core.errors import ConflictError, NotFoundError
from app.modules.core_data.models import User
from app.modules.core_data.repositories.users import UserRepository
from app.modules.security.models import UserGroup
from app.modules.security.models.constants import (
    ADMIN_GROUP_KEY,
    ALL_PERMISSION_CODES,
    STAFF_GROUP_KEY,
)
from app.modules.security.repositories import PermissionRepository


class PermissionService:
    def __init__(self, repo: PermissionRepository, users: UserRepository):
        self.repo = repo
        self.users = users

    def permissions_for_user(self, user: User) -> set[str]:
        return self.repo.permission_codes_for_user(user.id)

    def has_permission(self, user: User, permission_code: str) -> bool:
        return permission_code in self.permissions_for_user(user)

    def list_permissions(self):
        return self.repo.list_permissions()

    def list_groups(self) -> list[dict]:
        return [self._serialize_group(group) for group in self.repo.list_groups()]

    def get_group(self, group_id: int) -> UserGroup:
        group = self.repo.get_group(group_id)
        if not group:
            raise NotFoundError("Grupa użytkowników nie istnieje")
        return group

    def create_group(
        self,
        *,
        name: str,
        description: str,
        permission_codes: list[str],
    ) -> dict:
        try:
            if any(
                group.name.casefold() == name.casefold()
                for group in self.repo.list_groups()
            ):
                raise ConflictError("Grupa o tej nazwie już istnieje")
            group = self.repo.create_group(name=name, description=description)
            group.permissions = self._resolve_permissions(permission_codes)
            self.repo.commit(skip_audit=True)
            self.repo.refresh(group)
            return self._serialize_group(group)
        except Exception:
            self.repo.rollback()
            raise

    def update_group(self, group_id: int, **values) -> dict:
        try:
            group = self.get_group(group_id)
            self._ensure_custom_group(group)
            if "name" in values:
                duplicate = any(
                    candidate.id != group.id
                    and candidate.name.casefold() == values["name"].casefold()
                    for candidate in self.repo.list_groups()
                )
                if duplicate:
                    raise ConflictError("Grupa o tej nazwie już istnieje")
            for key, value in values.items():
                if value is not None:
                    setattr(group, key, value)
            self.repo.commit(skip_audit=True)
            self.repo.refresh(group)
            return self._serialize_group(group)
        except Exception:
            self.repo.rollback()
            raise

    def replace_group_permissions(self, group_id: int, codes: list[str]) -> dict:
        try:
            group = self.get_group(group_id)
            self._ensure_custom_group(group)
            group.permissions = self._resolve_permissions(codes)
            self.repo.commit(skip_audit=True)
            self.repo.refresh(group)
            return self._serialize_group(group)
        except Exception:
            self.repo.rollback()
            raise

    def save_group(
        self,
        group_id: int,
        *,
        name: str,
        description: str,
        permission_codes: list[str],
        user_ids: list[int],
    ) -> dict:
        """Save metadata, permissions and members atomically."""

        try:
            group = self.get_group(group_id)
            member_ids = set(user_ids)
            self._validate_users(member_ids)
            self._protect_last_admin(group, member_ids)

            if group.is_system:
                current_codes = {permission.code for permission in group.permissions}
                if (
                    name != group.name
                    or description != group.description
                    or set(permission_codes) != current_codes
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Grupy systemowej nie można dowolnie modyfikować",
                    )
            else:
                duplicate = any(
                    candidate.id != group.id
                    and candidate.name.casefold() == name.casefold()
                    for candidate in self.repo.list_groups()
                )
                if duplicate:
                    raise ConflictError("Grupa o tej nazwie już istnieje")
                group.name = name
                group.description = description
                group.permissions = self._resolve_permissions(permission_codes)

            self.repo.replace_group_users(group.id, member_ids)
            self.repo.commit(skip_audit=True)
            self.repo.refresh(group)
            return self._serialize_group(group)
        except Exception:
            self.repo.rollback()
            raise

    def replace_group_users(self, group_id: int, user_ids: list[int]) -> dict:
        try:
            group = self.get_group(group_id)
            ids = set(user_ids)
            self._validate_users(ids)
            self._protect_last_admin(group, ids)
            self.repo.replace_group_users(group_id, ids)
            self.repo.commit(skip_audit=True)
            return self._serialize_group(group)
        except Exception:
            self.repo.rollback()
            raise

    def replace_user_groups(self, user_id: int, group_ids: list[int]) -> list[int]:
        try:
            user = self.users.get_by_id(user_id)
            if not user:
                raise NotFoundError("Użytkownik nie istnieje")
            ids = set(group_ids)
            for group_id in ids:
                self.get_group(group_id)
            admin_group = self.repo.get_group_by_system_key(ADMIN_GROUP_KEY)
            if admin_group:
                existing_admins = set(self.repo.user_ids_for_group(admin_group.id))
                if (
                    user_id in existing_admins
                    and admin_group.id not in ids
                    and len(existing_admins) == 1
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Nie można usunąć ostatniego użytkownika z grupy Admin",
                    )
            self.repo.replace_user_groups(user_id, ids)
            self.repo.commit(skip_audit=True)
            return sorted(ids)
        except Exception:
            self.repo.rollback()
            raise

    def assign_default_group(self, user: User) -> None:
        """Add the default system group without replacing explicit memberships."""
        user_status = getattr(user, "status", None)
        if user_status is None:
            return
        admin_group = self.repo.get_group_by_system_key(ADMIN_GROUP_KEY)
        staff_group = self.repo.get_group_by_system_key(STAFF_GROUP_KEY)
        selected = admin_group if user_status == "admin" else staff_group
        if user_status not in {"admin", "regular"} or selected is None:
            return
        current = set(self.repo.group_ids_for_user(user.id))
        if selected.id not in current:
            current.add(selected.id)
            self.repo.replace_user_groups(user.id, current)

    def remove_system_group(self, user: User, system_key: str) -> None:
        """Remove one lifecycle group while preserving all other memberships."""
        group = self.repo.get_group_by_system_key(system_key)
        if group is None:
            return
        current = set(self.repo.group_ids_for_user(user.id))
        if group.id in current:
            current.remove(group.id)
            self.repo.replace_user_groups(user.id, current)

    def delete_group(self, group_id: int) -> None:
        try:
            group = self.get_group(group_id)
            self._ensure_custom_group(group)
            self.repo.delete_group(group)
            self.repo.commit(skip_audit=True)
        except Exception:
            self.repo.rollback()
            raise

    def group_ids_for_user(self, user_id: int) -> list[int]:
        if not self.users.get_by_id(user_id):
            raise NotFoundError("Użytkownik nie istnieje")
        return sorted(self.repo.group_ids_for_user(user_id))

    def _resolve_permissions(self, codes: list[str]):
        unique_codes = set(codes)
        unknown = unique_codes - ALL_PERMISSION_CODES
        if unknown:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Nieznane uprawnienia: {', '.join(sorted(unknown))}",
            )
        permissions = self.repo.get_permissions_by_codes(unique_codes)
        if len(permissions) != len(unique_codes):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Katalog uprawnień nie jest zsynchronizowany z bazą",
            )
        return permissions

    def _validate_users(self, user_ids: set[int]) -> None:
        missing = [user_id for user_id in user_ids if not self.users.get_by_id(user_id)]
        if missing:
            raise NotFoundError(f"Nie istnieją użytkownicy: {missing}")

    def _protect_last_admin(self, group: UserGroup, new_user_ids: set[int]) -> None:
        if group.system_key != ADMIN_GROUP_KEY:
            return
        if not new_user_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Grupa Admin musi mieć co najmniej jednego użytkownika",
            )

    @staticmethod
    def _ensure_custom_group(group: UserGroup) -> None:
        if group.is_system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Grupy systemowej nie można modyfikować",
            )

    def _serialize_group(self, group: UserGroup) -> dict:
        return {
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "is_system": group.is_system,
            "system_key": group.system_key,
            "permissions": sorted(
                group.permissions, key=lambda item: (item.category, item.name)
            ),
            "user_ids": sorted(self.repo.user_ids_for_group(group.id)),
            "created_at": group.created_at,
            "updated_at": group.updated_at,
        }
