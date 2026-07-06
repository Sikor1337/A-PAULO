"""Add departments module: tables, permissions, and the 12 initial departments.

Revision ID: pap84_departments
Revises: pap78_audit_events
Create Date: 2026-07-06 00:00:01+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "pap84_departments"
down_revision: str | Sequence[str] | None = "pap78_audit_events"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSIONS = (
    ("CAN_VIEW_DEPARTMENTS", "Podgląd działów", "Działy"),
    ("CAN_MANAGE_DEPARTMENTS", "Zarządzanie działami", "Działy"),
)

DEPARTMENTS = (
    ("Pomoc indywidualna", "🤝"),
    ("Remonty", "🔨"),
    ("Grupa porządkowa", "🧹"),
    ("Fizjoterapia", "💪"),
    ("Księgowość", "💰"),
    ("Festyn Seniora", "🎉"),
    ("Szkolenia", "📚"),
    ("Media", "📱"),
    ("Klub seniora", "🏠"),
    ("Muzyczni", "🎵"),
    ("Gastronomia", "🍽️"),
    ("Zbieranie funduszy", "💵"),
)


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("icon", sa.String(length=16), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("is_archived", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_departments_name"), "departments", ["name"], unique=True
    )

    op.create_table(
        "department_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("volunteer_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["department_id"], ["departments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["volunteer_id"], ["volunteers.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "department_id", "volunteer_id", name="uq_department_volunteer"
        ),
    )
    op.create_index(
        op.f("ix_department_members_department_id"),
        "department_members",
        ["department_id"],
    )
    op.create_index(
        op.f("ix_department_members_volunteer_id"),
        "department_members",
        ["volunteer_id"],
    )

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

    department_table = sa.table(
        "departments",
        sa.column("name", sa.String),
        sa.column("icon", sa.String),
        sa.column("description", sa.String),
        sa.column("is_archived", sa.Boolean),
    )
    op.bulk_insert(
        department_table,
        [
            {"name": name, "icon": icon, "description": "", "is_archived": False}
            for name, icon in DEPARTMENTS
        ],
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
    op.drop_index(
        op.f("ix_department_members_volunteer_id"), table_name="department_members"
    )
    op.drop_index(
        op.f("ix_department_members_department_id"), table_name="department_members"
    )
    op.drop_table("department_members")
    op.drop_index(op.f("ix_departments_name"), table_name="departments")
    op.drop_table("departments")
