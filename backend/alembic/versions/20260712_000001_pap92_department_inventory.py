"""Add department inventory (PAP-92).

Revision ID: pap92_department_inventory
Revises: pap91_dept_membership
Create Date: 2026-07-12 00:00:01+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "pap92_department_inventory"
down_revision: str | Sequence[str] | None = "pap91_dept_membership"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "department_inventory_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("location", sa.String(length=300), nullable=False),
        sa.Column("borrowed_by_volunteer_id", sa.Integer(), nullable=True),
        sa.Column("borrowed_at", sa.Date(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["borrowed_by_volunteer_id"],
            ["volunteers.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["department_id"], ["departments.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_department_inventory_items_borrowed_by_volunteer_id"),
        "department_inventory_items",
        ["borrowed_by_volunteer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_department_inventory_items_department_id"),
        "department_inventory_items",
        ["department_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_department_inventory_items_name"),
        "department_inventory_items",
        ["name"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_department_inventory_items_name"),
        table_name="department_inventory_items",
    )
    op.drop_index(
        op.f("ix_department_inventory_items_department_id"),
        table_name="department_inventory_items",
    )
    op.drop_index(
        op.f("ix_department_inventory_items_borrowed_by_volunteer_id"),
        table_name="department_inventory_items",
    )
    op.drop_table("department_inventory_items")
