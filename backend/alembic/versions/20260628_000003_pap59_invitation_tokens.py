"""Add single-use recruitment invitation tokens.

Revision ID: pap59_invitation_tokens
Revises: pap59_recruitment
Create Date: 2026-06-28 22:45:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "pap59_invitation_tokens"
down_revision: str | Sequence[str] | None = "pap59_recruitment"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "recruitment_invitations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=128), nullable=False),
        sa.Column("recipient_name", sa.String(length=200), nullable=True),
        sa.Column("recipient_email", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
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
        "ix_public_recruitment_invitations_token",
        "recruitment_invitations",
        ["token"],
        unique=True,
        schema="public",
    )
    op.create_index(
        "ix_public_recruitment_invitations_recipient_email",
        "recruitment_invitations",
        ["recipient_email"],
        unique=False,
        schema="public",
    )
    op.create_index(
        "ix_public_recruitment_invitations_is_active",
        "recruitment_invitations",
        ["is_active"],
        unique=False,
        schema="public",
    )

    op.add_column(
        "recruitment_submissions",
        sa.Column("invitation_id", sa.Integer(), nullable=True),
        schema="public",
    )
    op.execute(
        """
        INSERT INTO public.recruitment_invitations
            (token, recipient_name, recipient_email, is_active)
        SELECT
            'migrated-' || id::text || '-' ||
                md5(random()::text || clock_timestamp()::text),
            full_name,
            email,
            false
        FROM public.recruitment_submissions
        """
    )
    op.execute(
        """
        UPDATE public.recruitment_submissions AS submission
        SET invitation_id = invitation.id
        FROM public.recruitment_invitations AS invitation
        WHERE invitation.token LIKE 'migrated-' || submission.id::text || '-%'
        """
    )
    op.alter_column(
        "recruitment_submissions",
        "invitation_id",
        nullable=False,
        schema="public",
    )
    op.create_foreign_key(
        "fk_recruitment_submissions_invitation_id",
        "recruitment_submissions",
        "recruitment_invitations",
        ["invitation_id"],
        ["id"],
        source_schema="public",
        referent_schema="public",
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_public_recruitment_submissions_invitation_id",
        "recruitment_submissions",
        ["invitation_id"],
        unique=True,
        schema="public",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_public_recruitment_submissions_invitation_id",
        table_name="recruitment_submissions",
        schema="public",
    )
    op.drop_constraint(
        "fk_recruitment_submissions_invitation_id",
        "recruitment_submissions",
        type_="foreignkey",
        schema="public",
    )
    op.drop_column("recruitment_submissions", "invitation_id", schema="public")
    op.drop_index(
        "ix_public_recruitment_invitations_is_active",
        table_name="recruitment_invitations",
        schema="public",
    )
    op.drop_index(
        "ix_public_recruitment_invitations_recipient_email",
        table_name="recruitment_invitations",
        schema="public",
    )
    op.drop_index(
        "ix_public_recruitment_invitations_token",
        table_name="recruitment_invitations",
        schema="public",
    )
    op.drop_table("recruitment_invitations", schema="public")
