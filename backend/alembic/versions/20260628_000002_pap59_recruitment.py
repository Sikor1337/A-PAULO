"""Add configurable volunteer recruitment workflow.

Revision ID: pap59_recruitment
Revises: ad32b859cb2d
Create Date: 2026-06-28 18:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "pap59_recruitment"
down_revision: str | Sequence[str] | None = "ad32b859cb2d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "recruitment_fields",
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
        schema="public",
    )
    op.create_index(
        "ix_public_recruitment_fields_key",
        "recruitment_fields",
        ["key"],
        unique=True,
        schema="public",
    )
    op.create_index(
        "ix_public_recruitment_fields_position",
        "recruitment_fields",
        ["position"],
        unique=False,
        schema="public",
    )

    op.create_table(
        "recruitment_submissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("social_link", sa.String(length=500), nullable=False),
        sa.Column("availability", sa.Text(), nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("return_reason", sa.Text(), nullable=True),
        sa.Column("volunteer_id", sa.Integer(), nullable=True),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "status_changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
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
            ["volunteer_id"], ["public.volunteers.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("volunteer_id"),
        schema="public",
    )
    op.create_index(
        "ix_public_recruitment_submissions_email",
        "recruitment_submissions",
        ["email"],
        unique=True,
        schema="public",
    )
    op.create_index(
        "ix_public_recruitment_submissions_full_name",
        "recruitment_submissions",
        ["full_name"],
        unique=False,
        schema="public",
    )
    op.create_index(
        "ix_public_recruitment_submissions_status",
        "recruitment_submissions",
        ["status"],
        unique=False,
        schema="public",
    )

    fields = sa.table(
        "recruitment_fields",
        sa.column("key", sa.String),
        sa.column("label", sa.String),
        sa.column("field_type", sa.String),
        sa.column("required", sa.Boolean),
        sa.column("placeholder", sa.String),
        sa.column("options", sa.JSON),
        sa.column("position", sa.Integer),
        sa.column("is_active", sa.Boolean),
        sa.column("is_system", sa.Boolean),
        schema="public",
    )
    op.bulk_insert(
        fields,
        [
            {
                "key": "full_name",
                "label": "Imię i nazwisko",
                "field_type": "text",
                "required": True,
                "placeholder": "np. Jan Kowalski",
                "options": [],
                "position": 0,
                "is_active": True,
                "is_system": True,
            },
            {
                "key": "email",
                "label": "Adres e-mail",
                "field_type": "email",
                "required": True,
                "placeholder": "email@example.com",
                "options": [],
                "position": 1,
                "is_active": True,
                "is_system": True,
            },
            {
                "key": "phone",
                "label": "Telefon",
                "field_type": "tel",
                "required": True,
                "placeholder": "+48 123 456 789",
                "options": [],
                "position": 2,
                "is_active": True,
                "is_system": True,
            },
            {
                "key": "social_link",
                "label": "Link do profilu społecznościowego",
                "field_type": "text",
                "required": False,
                "placeholder": "https://...",
                "options": [],
                "position": 3,
                "is_active": True,
                "is_system": False,
            },
            {
                "key": "availability",
                "label": "Dyspozycyjność",
                "field_type": "textarea",
                "required": False,
                "placeholder": "Napisz, w jakie dni i godziny jesteś dostępny/a",
                "options": [],
                "position": 4,
                "is_active": True,
                "is_system": False,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_public_recruitment_submissions_status",
        table_name="recruitment_submissions",
        schema="public",
    )
    op.drop_index(
        "ix_public_recruitment_submissions_full_name",
        table_name="recruitment_submissions",
        schema="public",
    )
    op.drop_index(
        "ix_public_recruitment_submissions_email",
        table_name="recruitment_submissions",
        schema="public",
    )
    op.drop_table("recruitment_submissions", schema="public")
    op.drop_index(
        "ix_public_recruitment_fields_position",
        table_name="recruitment_fields",
        schema="public",
    )
    op.drop_index(
        "ix_public_recruitment_fields_key",
        table_name="recruitment_fields",
        schema="public",
    )
    op.drop_table("recruitment_fields", schema="public")
