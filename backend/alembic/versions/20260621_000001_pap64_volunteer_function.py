"""Replace volunteer roles with function field.

Revision ID: pap64_volunteer_function
Revises: 3a853d2d6c75
Create Date: 2026-06-21 00:00:01.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "pap64_volunteer_function"
down_revision: Union[str, Sequence[str], None] = "3a853d2d6c75"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "volunteers",
        sa.Column("function", sa.String(length=200), nullable=True),
        schema="public",
    )
    op.execute("ALTER TABLE public.volunteers DROP CONSTRAINT IF EXISTS volunteers_role_id_fkey")
    op.drop_column("volunteers", "role_id", schema="public")
    op.execute("DROP INDEX IF EXISTS public.ix_public_roles_name")
    op.drop_table("roles", schema="public")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_index(op.f("ix_public_roles_name"), "roles", ["name"], unique=True, schema="public")
    op.add_column("volunteers", sa.Column("role_id", sa.Integer(), nullable=True), schema="public")
    op.create_foreign_key(
        "volunteers_role_id_fkey",
        "volunteers",
        "roles",
        ["role_id"],
        ["id"],
        source_schema="public",
        referent_schema="public",
        ondelete="SET NULL",
    )
    op.drop_column("volunteers", "function", schema="public")
