"""Add bug reports module: table and permissions.

Revision ID: pap83_bug_reports
Revises: pap84_departments
Create Date: 2026-07-07 00:00:01+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "pap83_bug_reports"
down_revision: str | Sequence[str] | None = "pap84_departments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSIONS = (
    ("CAN_VIEW_BUG_REPORTS", "Podgląd zgłoszeń błędów", "Zgłoszenia błędów"),
    ("CAN_MANAGE_BUG_REPORTS", "Rozwiązywanie zgłoszeń błędów", "Zgłoszenia błędów"),
)


def upgrade() -> None:
    op.create_table(
        "bug_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("resolution_comment", sa.String(), nullable=False),
        sa.Column("reporter_id", sa.Integer(), nullable=True),
        sa.Column("reporter_email", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("storage_backend", sa.String(length=50), nullable=True),
        sa.Column("storage_key", sa.String(length=500), nullable=True),
        sa.Column("content_type", sa.String(length=127), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
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
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_index(op.f("ix_bug_reports_status"), "bug_reports", ["status"])
    op.create_index(
        op.f("ix_bug_reports_reporter_id"), "bug_reports", ["reporter_id"]
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
    op.drop_index(op.f("ix_bug_reports_reporter_id"), table_name="bug_reports")
    op.drop_index(op.f("ix_bug_reports_status"), table_name="bug_reports")
    op.drop_table("bug_reports")
