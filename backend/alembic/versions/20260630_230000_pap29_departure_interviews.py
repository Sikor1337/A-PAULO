"""Add configurable volunteer departure interviews.

Revision ID: pap29_departures
Revises: cd317ee086f0
Create Date: 2026-06-30 23:00:00+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "pap29_departures"
down_revision: str | Sequence[str] | None = "cd317ee086f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "departure_fields",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("label", sa.String(length=250), nullable=False),
        sa.Column("field_type", sa.String(length=30), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.Column("placeholder", sa.String(length=250), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False),
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
    op.create_index("ix_departure_fields_key", "departure_fields", ["key"], unique=True)
    op.create_index(
        "ix_departure_fields_position", "departure_fields", ["position"], unique=False
    )
    op.create_table(
        "departure_interviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("volunteer_id", sa.Integer(), nullable=False),
        sa.Column("departure_date", sa.Date(), nullable=False),
        sa.Column("departure_reason", sa.Text(), nullable=False),
        sa.Column("stay_in_contact", sa.Boolean(), nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("completed_by_id", sa.Integer(), nullable=True),
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
            ["volunteer_id"], ["volunteers.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["completed_by_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_departure_interviews_departure_date",
        "departure_interviews",
        ["departure_date"],
        unique=False,
    )
    op.create_index(
        "ix_departure_interviews_volunteer_id",
        "departure_interviews",
        ["volunteer_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_departure_interviews_volunteer_id", table_name="departure_interviews"
    )
    op.drop_index(
        "ix_departure_interviews_departure_date", table_name="departure_interviews"
    )
    op.drop_table("departure_interviews")
    op.drop_index("ix_departure_fields_position", table_name="departure_fields")
    op.drop_index("ix_departure_fields_key", table_name="departure_fields")
    op.drop_table("departure_fields")
