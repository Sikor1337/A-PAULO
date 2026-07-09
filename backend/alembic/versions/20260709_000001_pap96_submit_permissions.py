"""Add submit permissions for bug reports and the departure survey.

Lets admins disable the "Zgłoś błąd" and "Ankieta odejścia" self-service
windows per group (PAP-96). Both codes are granted to the admin and staff
groups so existing users keep their current access.

Revision ID: pap96_submit_permissions
Revises: pap89_tasks
Create Date: 2026-07-09 00:00:01+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "pap96_submit_permissions"
down_revision: str | Sequence[str] | None = "pap89_tasks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSIONS = (
    ("CAN_SUBMIT_BUG_REPORTS", "Zgłaszanie błędów", "Zgłoszenia błędów"),
    (
        "CAN_SUBMIT_DEPARTURE_SURVEY",
        "Wypełnianie ankiety odejścia",
        "Ankieta odejścia",
    ),
)


def upgrade() -> None:
    permission_table = sa.table(
        "security_permissions",
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("category", sa.String),
    )
    op.bulk_insert(
        permission_table,
        [
            {"code": code, "name": name, "category": category}
            for code, name, category in PERMISSIONS
        ],
    )

    codes = ", ".join(f"'{code}'" for code, _, _ in PERMISSIONS)
    op.execute(
        f"""
        INSERT INTO security_group_permissions (group_id, permission_id)
        SELECT security_group.id, permission.id
        FROM security_groups AS security_group
        CROSS JOIN security_permissions AS permission
        WHERE security_group.system_key IN ('admin', 'staff')
          AND permission.code IN ({codes})
        """
    )


def downgrade() -> None:
    codes = ", ".join(f"'{code}'" for code, _, _ in PERMISSIONS)
    op.execute(
        f"""
        DELETE FROM security_group_permissions
        WHERE permission_id IN (
            SELECT id FROM security_permissions WHERE code IN ({codes})
        )
        """
    )
    op.execute(f"DELETE FROM security_permissions WHERE code IN ({codes})")
