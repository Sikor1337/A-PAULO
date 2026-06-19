"""Seed the predefined volunteer roles (pap-30).

Roles are plain labels assignable to a Volunteer — for now NOT tied to any
permissions (every role has the same access). The set is editable afterwards
via the roles CRUD / "Zarządzaj rolami" UI; this script only guarantees the
three defaults exist.

Idempotent: re-running only adds roles that are missing.

Usage (from backend/, venv active):
    python -m app.seed_roles
"""
from app.core.dependencies import _sql_session_factory
from app.modules.core_data.services.roles import RoleService

PREDEFINED_ROLES = ["Administrator", "Przewodnik", "Wolontariusz"]


def seed_roles() -> None:
    session = _sql_session_factory()
    try:
        service = RoleService(session)
        for name in PREDEFINED_ROLES:
            if service.get_role_by_name(name):
                print(f"= '{name}' already exists - skipping")
                continue
            service.create_role(name=name)
            print(f"+ created role '{name}'")
    finally:
        session.close()


if __name__ == "__main__":
    seed_roles()
