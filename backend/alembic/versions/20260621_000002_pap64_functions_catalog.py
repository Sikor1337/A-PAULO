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
    op.execute("""
        CREATE TABLE IF NOT EXISTS public.functions (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            is_system BOOLEAN NOT NULL DEFAULT false,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_public_functions_name
        ON public.functions (name)
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS public.volunteer_function (
            volunteer_id INTEGER NOT NULL,
            function_id INTEGER NOT NULL,
            PRIMARY KEY (volunteer_id, function_id),
            CONSTRAINT volunteer_function_volunteer_id_fkey
                FOREIGN KEY (volunteer_id)
                REFERENCES public.volunteers(id)
                ON DELETE CASCADE,
            CONSTRAINT volunteer_function_function_id_fkey
                FOREIGN KEY (function_id)
                REFERENCES public.functions(id)
                ON DELETE CASCADE
        )
    """)

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
