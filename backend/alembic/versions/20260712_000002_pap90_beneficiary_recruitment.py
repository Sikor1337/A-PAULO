"""Add public beneficiary recruitment workflow (PAP-90).

Revision ID: pap90_beneficiary_recruitment
Revises: pap92_department_inventory
Create Date: 2026-07-12 00:00:02+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "pap90_beneficiary_recruitment"
down_revision: str | Sequence[str] | None = "pap92_department_inventory"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "beneficiary_recruitment_fields",
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
    op.create_index(
        op.f("ix_beneficiary_recruitment_fields_key"),
        "beneficiary_recruitment_fields",
        ["key"],
        unique=True,
    )
    op.create_index(
        op.f("ix_beneficiary_recruitment_fields_position"),
        "beneficiary_recruitment_fields",
        ["position"],
        unique=False,
    )

    op.create_table(
        "beneficiary_recruitment_submissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("address", sa.String(length=500), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("reporter_name", sa.String(length=200), nullable=False),
        sa.Column("reporter_phone", sa.String(length=20), nullable=False),
        sa.Column("help_needed", sa.Text(), nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("decision_comment", sa.Text(), nullable=True),
        sa.Column("beneficiary_id", sa.Integer(), nullable=True),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["beneficiary_id"], ["beneficiaries.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("beneficiary_id"),
    )
    op.create_index(
        op.f("ix_beneficiary_recruitment_submissions_full_name"),
        "beneficiary_recruitment_submissions",
        ["full_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_beneficiary_recruitment_submissions_status"),
        "beneficiary_recruitment_submissions",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_beneficiary_recruitment_submissions_status"),
        table_name="beneficiary_recruitment_submissions",
    )
    op.drop_index(
        op.f("ix_beneficiary_recruitment_submissions_full_name"),
        table_name="beneficiary_recruitment_submissions",
    )
    op.drop_table("beneficiary_recruitment_submissions")
    op.drop_index(
        op.f("ix_beneficiary_recruitment_fields_position"),
        table_name="beneficiary_recruitment_fields",
    )
    op.drop_index(
        op.f("ix_beneficiary_recruitment_fields_key"),
        table_name="beneficiary_recruitment_fields",
    )
    op.drop_table("beneficiary_recruitment_fields")
