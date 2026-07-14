"""Permission resolution and user-group management rules."""

from app.core.audit import AuditEntry, AuditPort, EntityType, calculate_delta
from app.core.errors import (
    BadRequestError,
    ConflictError,
    NotFoundError,
    ValidationException,
)
from app.modules.core_data.models import User
from app.modules.core_data.repositories.users import UserRepository
from app.modules.security.audit_state import security_group_audit_state
from app.modules.security.models import UserGroup
from app.modules.security.models.constants import (
    ADMIN_GROUP_KEY,
    STAFF_GROUP_KEY,
)
from app.modules.security.repositories import PermissionRepository
from app.modules.security.schemas.permissions import (
    UserGroupCreateRequest,
    UserGroupSaveRequest,
    UserGroupUpdateRequest,
)


class PermissionService:
    def __init__(
        self,
        repo: PermissionRepository,
        users: UserRepository,
        audit: AuditPort,
    ):
        self.repo = repo
        self.users = users
        self.audit = audit

    def _group_state(self, group: UserGroup) -> dict:
        return security_group_audit_state(group, self.repo.user_ids_for_group(group.id))

    def _record_group(
        self,
        action: str,
        group: UserGroup,
        actor: User,
        old_state: dict,
        new_state: dict,
    ) -> None:
        self.audit.record(
            AuditEntry(
                entity_type=EntityType.SECURITY_USER_GROUP.value,
                entity_id=str(group.id),
                action=action,
                actor_id=str(actor.id),
                actor_display_name=actor.email,
                changes=calculate_delta(old_state, new_state),
            )
        )

    def _record_user_groups(
        self,
        user: User,
        actor: User,
        old_group_ids: list[int],
        new_group_ids: list[int],
    ) -> None:
        self.audit.record(
            AuditEntry(
                entity_type=EntityType.CORE_DATA_USER.value,
                entity_id=str(user.id),
                action="SECURITY_GROUPS_UPDATE",
                actor_id=str(actor.id),
                actor_display_name=actor.email,
                changes=calculate_delta(
                    {"security_group_ids": sorted(old_group_ids)},
                    {"security_group_ids": sorted(new_group_ids)},
                ),
            )
        )

    def _capture_user_groups(self, user_ids: set[int]) -> dict[int, list[int]]:
        return {
            user_id: sorted(self.repo.group_ids_for_user(user_id))
            for user_id in user_ids
        }

    def _record_membership_changes(
        self,
        before: dict[int, list[int]],
        actor: User,
    ) -> None:
        for user_id, old_group_ids in before.items():
            new_group_ids = sorted(self.repo.group_ids_for_user(user_id))
            if old_group_ids == new_group_ids:
                continue
            user = self.users.get_by_id(user_id)
            if user:
                self._record_user_groups(user, actor, old_group_ids, new_group_ids)

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
        request: UserGroupCreateRequest,
        *,
        actor: User,
    ) -> dict:
        try:
            if any(
                group.name.casefold() == request.name.casefold()
                for group in self.repo.list_groups()
            ):
                raise ConflictError("Grupa o tej nazwie już istnieje")
            group = self.repo.create_group(
                name=request.name,
                description=request.description,
            )
            group.permissions = self._resolve_permissions(request.permission_codes)
            self.repo.flush()
            self.repo.refresh(group)
            self._record_group("CREATE", group, actor, {}, self._group_state(group))
            self.repo.commit()
            return self._serialize_group(group)
        except Exception:
            self.repo.rollback()
            raise

    def update_group(
        self,
        group_id: int,
        request: UserGroupUpdateRequest,
        actor: User,
    ) -> dict:
        try:
            group = self.get_group(group_id)
            old_state = self._group_state(group)
            self._ensure_custom_group(group)
            if request.name is not None:
                duplicate = any(
                    candidate.id != group.id
                    and candidate.name.casefold() == request.name.casefold()
                    for candidate in self.repo.list_groups()
                )
                if duplicate:
                    raise ConflictError("Grupa o tej nazwie już istnieje")
            if request.name is not None:
                group.name = request.name
            if request.description is not None:
                group.description = request.description
            self.repo.flush()
            self.repo.refresh(group)
            new_state = self._group_state(group)
            if not calculate_delta(old_state, new_state):
                # Genuine no-op: persist (nothing changed) without an audit entry.
                self.repo.commit(skip_audit=True)
                return self._serialize_group(group)
            self._record_group("UPDATE", group, actor, old_state, new_state)
            self.repo.commit()
            return self._serialize_group(group)
        except Exception:
            self.repo.rollback()
            raise

    def replace_group_permissions(
        self, group_id: int, codes: list[str], actor: User
    ) -> dict:
        try:
            group = self.get_group(group_id)
            old_state = self._group_state(group)
            self._ensure_permissions_editable(group)
            group.permissions = self._resolve_permissions(codes)
            self.repo.flush()
            self.repo.refresh(group)
            new_state = self._group_state(group)
            if not calculate_delta(old_state, new_state):
                # Genuine no-op: persist (nothing changed) without an audit entry.
                self.repo.commit(skip_audit=True)
                return self._serialize_group(group)
            self._record_group("PERMISSIONS_UPDATE", group, actor, old_state, new_state)
            self.repo.commit()
            return self._serialize_group(group)
        except Exception:
            self.repo.rollback()
            raise

    def save_group(
        self,
        group_id: int,
        request: UserGroupSaveRequest,
        *,
        actor: User,
    ) -> dict:
        """Save metadata, permissions and members atomically."""

        try:
            group = self.get_group(group_id)
            old_state = self._group_state(group)
            member_ids = set(request.user_ids)
            changed_user_ids = set(old_state["user_ids"]) ^ member_ids
            user_groups_before = self._capture_user_groups(changed_user_ids)
            self._validate_users(member_ids)
            self._protect_last_admin(group, member_ids)

            if group.is_system:
                if (
                    request.name != group.name
                    or request.description != group.description
                ):
                    raise BadRequestError(
                        "Nazwy i opisu grupy systemowej nie można zmieniać"
                    )
                current_codes = {permission.code for permission in group.permissions}
                if set(request.permission_codes) != current_codes:
                    self._ensure_permissions_editable(group)
                    group.permissions = self._resolve_permissions(
                        request.permission_codes
                    )
            else:
                duplicate = any(
                    candidate.id != group.id
                    and candidate.name.casefold() == request.name.casefold()
                    for candidate in self.repo.list_groups()
                )
                if duplicate:
                    raise ConflictError("Grupa o tej nazwie już istnieje")
                group.name = request.name
                group.description = request.description
                group.permissions = self._resolve_permissions(request.permission_codes)

            self.repo.replace_group_users(group.id, member_ids)
            self.repo.flush()
            self.repo.refresh(group)
            new_state = self._group_state(group)
            if not calculate_delta(old_state, new_state):
                # Genuine no-op: persist (nothing changed) without an audit entry.
                self.repo.commit(skip_audit=True)
                return self._serialize_group(group)
            self._record_group("UPDATE", group, actor, old_state, new_state)
            self._record_membership_changes(user_groups_before, actor)
            self.repo.commit()
            return self._serialize_group(group)
        except Exception:
            self.repo.rollback()
            raise

    def replace_group_users(
        self, group_id: int, user_ids: list[int], actor: User
    ) -> dict:
        try:
            group = self.get_group(group_id)
            old_state = self._group_state(group)
            ids = set(user_ids)
            changed_user_ids = set(old_state["user_ids"]) ^ ids
            user_groups_before = self._capture_user_groups(changed_user_ids)
            self._validate_users(ids)
            self._protect_last_admin(group, ids)
            self.repo.replace_group_users(group_id, ids)
            self.repo.flush()
            new_state = self._group_state(group)
            if not calculate_delta(old_state, new_state):
                # Genuine no-op: persist (nothing changed) without an audit entry.
                self.repo.commit(skip_audit=True)
                return self._serialize_group(group)
            self._record_group("MEMBERS_UPDATE", group, actor, old_state, new_state)
            self._record_membership_changes(user_groups_before, actor)
            self.repo.commit()
            return self._serialize_group(group)
        except Exception:
            self.repo.rollback()
            raise

    def replace_user_groups(
        self, user_id: int, group_ids: list[int], actor: User
    ) -> list[int]:
        try:
            user = self.users.get_by_id(user_id)
            if not user:
                raise NotFoundError("Użytkownik nie istnieje")
            ids = set(group_ids)
            old_ids = sorted(self.repo.group_ids_for_user(user_id))
            changed_group_ids = set(old_ids) ^ ids
            group_states_before = {
                group_id: self._group_state(self.get_group(group_id))
                for group_id in changed_group_ids
            }
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
                    raise BadRequestError(
                        "Nie można usunąć ostatniego użytkownika z grupy Admin"
                    )
            self.repo.replace_user_groups(user_id, ids)
            self.repo.flush()
            new_ids = sorted(ids)
            if old_ids == new_ids:
                # Genuine no-op: persist (nothing changed) without an audit entry.
                self.repo.commit(skip_audit=True)
                return old_ids
            self._record_user_groups(user, actor, old_ids, new_ids)
            for group_id, old_state in group_states_before.items():
                group = self.get_group(group_id)
                self._record_group(
                    "MEMBERS_UPDATE",
                    group,
                    actor,
                    old_state,
                    self._group_state(group),
                )
            self.repo.commit()
            return sorted(ids)
        except Exception:
            self.repo.rollback()
            raise

    def assign_default_group(self, user: User, actor: User | None = None) -> None:
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
            old_state = self._group_state(selected) if actor else None
            current.add(selected.id)
            self.repo.replace_user_groups(user.id, current)
            if actor and old_state:
                self.repo.flush()
                self._record_group(
                    "MEMBERS_UPDATE",
                    selected,
                    actor,
                    old_state,
                    self._group_state(selected),
                )

    def remove_system_group(
        self, user: User, system_key: str, actor: User | None = None
    ) -> None:
        """Remove one lifecycle group while preserving all other memberships."""
        group = self.repo.get_group_by_system_key(system_key)
        if group is None:
            return
        current = set(self.repo.group_ids_for_user(user.id))
        if group.id in current:
            old_state = self._group_state(group) if actor else None
            current.remove(group.id)
            self.repo.replace_user_groups(user.id, current)
            if actor and old_state:
                self.repo.flush()
                self._record_group(
                    "MEMBERS_UPDATE",
                    group,
                    actor,
                    old_state,
                    self._group_state(group),
                )

    def delete_group(self, group_id: int, actor: User) -> None:
        try:
            group = self.get_group(group_id)
            old_state = self._group_state(group)
            affected_user_ids = set(old_state["user_ids"])
            user_groups_before = self._capture_user_groups(affected_user_ids)
            self._ensure_custom_group(group)
            self.repo.delete_group(group)
            self.repo.flush()
            self._record_group("DELETE", group, actor, old_state, {})
            self._record_membership_changes(user_groups_before, actor)
            self.repo.commit()
        except Exception:
            self.repo.rollback()
            raise

    def group_ids_for_user(self, user_id: int) -> list[int]:
        if not self.users.get_by_id(user_id):
            raise NotFoundError("Użytkownik nie istnieje")
        return sorted(self.repo.group_ids_for_user(user_id))

    def _resolve_permissions(self, codes: list[str]):
        unique_codes = set(codes)
        permissions = self.repo.get_permissions_by_codes(unique_codes)
        found_codes = {permission.code for permission in permissions}
        unknown = unique_codes - found_codes
        if unknown:
            raise ValidationException(
                f"Nieznane uprawnienia: {', '.join(sorted(unknown))}"
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
            raise BadRequestError(
                "Grupa Admin musi mieć co najmniej jednego użytkownika"
            )

    @staticmethod
    def _ensure_custom_group(group: UserGroup) -> None:
        if group.is_system:
            raise BadRequestError("Grupy systemowej nie można modyfikować")

    @staticmethod
    def _ensure_permissions_editable(group: UserGroup) -> None:
        """STAFF permissions are admin-tunable (PAP-95); other system groups
        stay locked — Admin especially, so administrators cannot cut off
        their own access."""
        if group.is_system and group.system_key != STAFF_GROUP_KEY:
            raise BadRequestError(
                "Uprawnień tej grupy systemowej nie można modyfikować"
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
