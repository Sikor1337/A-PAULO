"""Add attachments metadata.

Revision ID: pap53_attachments
Revises: pap64_functions_catalog
Create Date: 2026-06-26 00:00:01.000000+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "pap53_attachments"
down_revision: Union[str, Sequence[str], None] = "pap64_functions_catalog"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("context", sa.String(length=50), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=True),
        sa.Column("beneficiary_id", sa.Integer(), nullable=True),
        sa.Column("volunteer_id", sa.Integer(), nullable=True),
        sa.Column("period", sa.String(length=7), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_backend", sa.String(length=50), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("content_type", sa.String(length=127), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_by_username", sa.String(length=150), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_username", sa.String(length=150), nullable=True),
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
            ["beneficiary_id"], ["public.beneficiaries.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["group_id"], ["public.groups.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["volunteer_id"], ["public.volunteers.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_index(
        "ix_attachments_bo_card_lookup",
        "attachments",
        ["context", "group_id", "beneficiary_id", "volunteer_id", "period"],
        unique=False,
        schema="public",
    )
    op.create_index(
        op.f("ix_public_attachments_beneficiary_id"),
        "attachments",
        ["beneficiary_id"],
        unique=False,
        schema="public",
    )
    op.create_index(
        op.f("ix_public_attachments_context"),
        "attachments",
        ["context"],
        unique=False,
        schema="public",
    )
    op.create_index(
        op.f("ix_public_attachments_group_id"),
        "attachments",
        ["group_id"],
        unique=False,
        schema="public",
    )
    op.create_index(
        op.f("ix_public_attachments_period"),
        "attachments",
        ["period"],
        unique=False,
        schema="public",
    )
    op.create_index(
        op.f("ix_public_attachments_storage_key"),
        "attachments",
        ["storage_key"],
        unique=True,
        schema="public",
    )
    op.create_index(
        op.f("ix_public_attachments_volunteer_id"),
        "attachments",
        ["volunteer_id"],
        unique=False,
        schema="public",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_public_attachments_volunteer_id"),
        table_name="attachments",
        schema="public",
    )
    op.drop_index(
        op.f("ix_public_attachments_storage_key"),
        table_name="attachments",
        schema="public",
    )
    op.drop_index(
        op.f("ix_public_attachments_period"), table_name="attachments", schema="public"
    )
    op.drop_index(
        op.f("ix_public_attachments_group_id"),
        table_name="attachments",
        schema="public",
    )
    op.drop_index(
        op.f("ix_public_attachments_context"), table_name="attachments", schema="public"
    )
    op.drop_index(
        op.f("ix_public_attachments_beneficiary_id"),
        table_name="attachments",
        schema="public",
    )
    op.drop_index(
        "ix_attachments_bo_card_lookup", table_name="attachments", schema="public"
    )
    op.drop_table("attachments", schema="public")
