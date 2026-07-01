"""Add flexible user groups and permissions.

Revision ID: pap58_permissions
Revises: pap59_static_recruitment
Create Date: 2026-06-30 17:30:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "pap58_permissions"
down_revision: str | Sequence[str] | None = "pap59_static_recruitment"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSIONS = (
    ("CAN_VIEW_USERS", "Podgląd użytkowników", "Użytkownicy"),
    ("CAN_MANAGE_USERS", "Zarządzanie użytkownikami", "Użytkownicy"),
    ("CAN_VIEW_VOLUNTEERS", "Podgląd wolontariuszy", "Wolontariusze"),
    ("CAN_MANAGE_VOLUNTEERS", "Zarządzanie wolontariuszami", "Wolontariusze"),
    ("CAN_VIEW_BENEFICIARIES", "Podgląd podopiecznych", "Podopieczni"),
    ("CAN_MANAGE_BENEFICIARIES", "Zarządzanie podopiecznymi", "Podopieczni"),
    ("CAN_VIEW_PI_GROUPS", "Podgląd grup A-PAULO", "Grupy A-PAULO"),
    ("CAN_MANAGE_PI_GROUPS", "Zarządzanie grupami A-PAULO", "Grupy A-PAULO"),
    ("CAN_VIEW_FUNCTIONS", "Podgląd funkcji", "Funkcje"),
    ("CAN_MANAGE_FUNCTIONS", "Zarządzanie funkcjami", "Funkcje"),
    ("CAN_VIEW_ATTACHMENTS", "Podgląd załączników i kart BO", "Załączniki"),
    ("CAN_MANAGE_ATTACHMENTS", "Zarządzanie załącznikami i kartami BO", "Załączniki"),
    ("CAN_VIEW_RECRUITMENT", "Podgląd rekrutacji", "Rekrutacja"),
    ("CAN_MANAGE_RECRUITMENT", "Zarządzanie rekrutacją", "Rekrutacja"),
    ("CAN_VIEW_EVENTS", "Podgląd wydarzeń", "Wydarzenia"),
    ("CAN_MANAGE_EVENTS", "Zarządzanie wydarzeniami", "Wydarzenia"),
    ("CAN_VIEW_SECURITY", "Podgląd grup użytkowników", "Bezpieczeństwo"),
    ("CAN_MANAGE_SECURITY", "Zarządzanie grupami i uprawnieniami", "Bezpieczeństwo"),
)

STAFF_EXCLUDED = {
    "CAN_VIEW_USERS",
    "CAN_MANAGE_USERS",
    "CAN_VIEW_SECURITY",
    "CAN_MANAGE_SECURITY",
}


def upgrade() -> None:
    op.create_table(
        "security_permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        schema="public",
    )
    op.create_index(
        "ix_security_permissions_code",
        "security_permissions",
        ["code"],
        unique=True,
        schema="public",
    )
    op.create_index(
        "ix_security_permissions_category",
        "security_permissions",
        ["category"],
        schema="public",
    )

    op.create_table(
        "security_groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "description", sa.String(length=500), nullable=False, server_default=""
        ),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("system_key", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("system_key"),
        schema="public",
    )
    op.create_index(
        "ix_security_groups_name",
        "security_groups",
        ["name"],
        unique=True,
        schema="public",
    )
    op.create_index(
        "ix_security_groups_system_key",
        "security_groups",
        ["system_key"],
        unique=True,
        schema="public",
    )

    op.create_table(
        "security_group_permissions",
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"], ["public.security_groups.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"], ["public.security_permissions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("group_id", "permission_id"),
        schema="public",
    )
    op.create_table(
        "security_user_groups",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["public.users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["group_id"], ["public.security_groups.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("user_id", "group_id"),
        schema="public",
    )

    permission_table = sa.table(
        "security_permissions",
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("category", sa.String),
        schema="public",
    )
    op.bulk_insert(
        permission_table,
        [
            {"code": code, "name": name, "category": category}
            for code, name, category in PERMISSIONS
        ],
    )
    op.execute(
        """
        INSERT INTO public.security_groups
            (name, description, is_system, system_key)
        VALUES
            ('Admin', 'Pełny dostęp administracyjny', true, 'admin'),
            ('Staff', 'Domyślne uprawnienia pracownika', true, 'staff')
        """
    )
    op.execute(
        """
        INSERT INTO public.security_group_permissions (group_id, permission_id)
        SELECT security_group.id, permission.id
        FROM public.security_groups AS security_group
        CROSS JOIN public.security_permissions AS permission
        WHERE security_group.system_key = 'admin'
        """
    )
    staff_codes = ", ".join(
        f"'{code}'" for code, _, _ in PERMISSIONS if code not in STAFF_EXCLUDED
    )
    op.execute(
        f"""
        INSERT INTO public.security_group_permissions (group_id, permission_id)
        SELECT security_group.id, permission.id
        FROM public.security_groups AS security_group
        CROSS JOIN public.security_permissions AS permission
        WHERE security_group.system_key = 'staff'
          AND permission.code IN ({staff_codes})
        """
    )
    op.execute(
        """
        INSERT INTO public.security_user_groups (user_id, group_id)
        SELECT users.id, security_group.id
        FROM public.users AS users
        JOIN public.security_groups AS security_group
          ON security_group.system_key = CASE
              WHEN users.status = 'admin' THEN 'admin'
              WHEN users.status = 'regular' THEN 'staff'
          END
        WHERE users.status IN ('admin', 'regular')
        """
    )


def downgrade() -> None:
    op.drop_table("security_user_groups", schema="public")
    op.drop_table("security_group_permissions", schema="public")
    op.drop_table("security_groups", schema="public")
    op.drop_table("security_permissions", schema="public")
