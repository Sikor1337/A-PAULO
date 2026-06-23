"""Move volunteer functions to a catalog.

Revision ID: pap64_functions_catalog
Revises: pap64_volunteer_function
Create Date: 2026-06-21 00:00:02.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "pap64_functions_catalog"
down_revision: Union[str, Sequence[str], None] = "pap64_volunteer_function"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "functions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_index(op.f("ix_public_functions_name"), "functions", ["name"], unique=True, schema="public")

    op.create_table(
        "volunteer_function",
        sa.Column("volunteer_id", sa.Integer(), nullable=False),
        sa.Column("function_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["function_id"], ["public.functions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["volunteer_id"], ["public.volunteers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("volunteer_id", "function_id"),
        schema="public",
    )

    op.execute(
        """
        INSERT INTO public.functions (name, is_system, is_active)
        VALUES
            ('Przewodnik', true, true),
            ('Lider Podopiecznego', true, true)
        ON CONFLICT (name) DO UPDATE
        SET is_system = EXCLUDED.is_system,
            is_active = true
        """
    )
    op.execute(
        """
        INSERT INTO public.functions (name, is_system, is_active)
        SELECT DISTINCT trim("function"), false, true
        FROM public.volunteers
        WHERE "function" IS NOT NULL AND trim("function") <> ''
        ON CONFLICT (name) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO public.volunteer_function (volunteer_id, function_id)
        SELECT v.id, f.id
        FROM public.volunteers v
        JOIN public.functions f ON f.name = trim(v."function")
        WHERE v."function" IS NOT NULL AND trim(v."function") <> ''
        ON CONFLICT DO NOTHING
        """
    )
    op.drop_column("volunteers", "function", schema="public")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column("volunteers", sa.Column("function", sa.String(length=200), nullable=True), schema="public")
    op.execute(
        """
        UPDATE public.volunteers v
        SET function = manual_functions.function_names
        FROM (
            SELECT vf.volunteer_id, string_agg(f.name, ', ' ORDER BY f.name) AS function_names
            FROM public.volunteer_function vf
            JOIN public.functions f ON f.id = vf.function_id
            WHERE f.is_system = false
            GROUP BY vf.volunteer_id
        ) manual_functions
        WHERE manual_functions.volunteer_id = v.id
        """
    )
    op.drop_table("volunteer_function", schema="public")
    op.drop_index(op.f("ix_public_functions_name"), table_name="functions", schema="public")
    op.drop_table("functions", schema="public")
