"""Replace invitation tokens with account-bound recruitment forms.

Revision ID: pap59_static_recruitment
Revises: pap59_invitation_tokens
Create Date: 2026-06-30 13:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "pap59_static_recruitment"
down_revision: str | Sequence[str] | None = "pap59_invitation_tokens"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_UNUSABLE_PASSWORD = "!migration-unusable!"


def upgrade() -> None:
    op.add_column(
        "recruitment_submissions",
        sa.Column("user_id", sa.Integer(), nullable=True),
        schema="public",
    )
    op.add_column(
        "recruitment_submissions",
        sa.Column("decision_comment", sa.Text(), nullable=True),
        schema="public",
    )

    op.execute(
        f"""
        INSERT INTO public.users
            (username, email, first_name, last_name, hashed_password, status,
             is_active)
        SELECT
            'legacy_recruitment_' || submission.id::text || '_' ||
                substr(md5(submission.email), 1, 8),
            lower(submission.email),
            left(submission.full_name, 150),
            '',
            '{_UNUSABLE_PASSWORD}',
            CASE
                WHEN submission.status = 'ACCEPTED' THEN 'regular'
                ELSE 'new_volunteer'
            END,
            false
        FROM public.recruitment_submissions AS submission
        WHERE NOT EXISTS (
            SELECT 1
            FROM public.users AS existing_user
            WHERE lower(existing_user.email) = lower(submission.email)
        )
        """
    )
    op.execute(
        """
        UPDATE public.recruitment_submissions AS submission
        SET user_id = (
            SELECT min(existing_user.id)
            FROM public.users AS existing_user
            WHERE lower(existing_user.email) = lower(submission.email)
        )
        """
    )
    op.execute(
        """
        UPDATE public.users AS candidate
        SET status = 'regular'
        FROM public.recruitment_submissions AS submission
        WHERE submission.user_id = candidate.id
          AND submission.status = 'ACCEPTED'
          AND candidate.status = 'new_volunteer'
        """
    )
    op.alter_column(
        "recruitment_submissions", "user_id", nullable=False, schema="public"
    )
    op.create_foreign_key(
        "fk_recruitment_submissions_user_id",
        "recruitment_submissions",
        "users",
        ["user_id"],
        ["id"],
        source_schema="public",
        referent_schema="public",
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_public_recruitment_submissions_user_id",
        "recruitment_submissions",
        ["user_id"],
        unique=True,
        schema="public",
    )
    op.alter_column(
        "volunteers",
        "phone",
        existing_type=sa.String(length=20),
        type_=sa.String(length=30),
        schema="public",
    )

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


def downgrade() -> None:
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
            'restored-' || id::text || '-' || md5(random()::text),
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
        WHERE invitation.token LIKE 'restored-' || submission.id::text || '-%'
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

    op.drop_index(
        "ix_public_recruitment_submissions_user_id",
        table_name="recruitment_submissions",
        schema="public",
    )
    op.drop_constraint(
        "fk_recruitment_submissions_user_id",
        "recruitment_submissions",
        type_="foreignkey",
        schema="public",
    )
    op.drop_column("recruitment_submissions", "user_id", schema="public")
    op.drop_column("recruitment_submissions", "decision_comment", schema="public")
    op.execute(
        """
        UPDATE public.volunteers
        SET phone = left(phone, 20)
        WHERE length(phone) > 20
        """
    )
    op.alter_column(
        "volunteers",
        "phone",
        existing_type=sa.String(length=30),
        type_=sa.String(length=20),
        schema="public",
    )
    op.execute(
        f"""
        DELETE FROM public.users
        WHERE hashed_password = '{_UNUSABLE_PASSWORD}'
          AND is_active = false
        """
    )
