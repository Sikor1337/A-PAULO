"""Add calendar events, private feed tokens and audit trail.

Revision ID: pap49_calendar
Revises: pap58_permissions
Create Date: 2026-06-30 17:20:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "pap49_calendar"
down_revision: str | Sequence[str] | None = "pap58_permissions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "calendar_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uid", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "timezone",
            sa.String(length=64),
            nullable=False,
            server_default="Europe/Warsaw",
        ),
        sa.Column(
            "is_all_day", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("location", sa.String(length=300), nullable=False, server_default=""),
        sa.Column("recurrence_rule", sa.String(length=500), nullable=True),
        sa.Column(
            "status", sa.String(length=30), nullable=False, server_default="published"
        ),
        sa.Column(
            "visibility",
            sa.String(length=30),
            nullable=False,
            server_default="organization",
        ),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'published', 'cancelled')",
            name="ck_calendar_event_status",
        ),
        sa.CheckConstraint(
            "visibility IN ('organization', 'admins')",
            name="ck_calendar_event_visibility",
        ),
        sa.CheckConstraint("ends_at >= starts_at", name="ck_calendar_event_dates"),
        sa.ForeignKeyConstraint(
            ["author_id"], ["public.users.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uid"),
        schema="public",
    )
    op.create_index(
        "ix_calendar_events_title", "calendar_events", ["title"], schema="public"
    )
    op.create_index(
        "ix_calendar_events_status", "calendar_events", ["status"], schema="public"
    )
    op.create_index(
        "ix_calendar_events_visibility",
        "calendar_events",
        ["visibility"],
        schema="public",
    )
    op.create_index(
        "ix_calendar_events_author_id",
        "calendar_events",
        ["author_id"],
        schema="public",
    )

    op.create_table(
        "calendar_feed_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["public.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
        sa.UniqueConstraint("user_id"),
        schema="public",
    )
    op.create_table(
        "calendar_audit",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("event_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=30), nullable=False),
        sa.Column("entity_type", sa.String(length=30), nullable=False),
        sa.Column("changes", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["public.users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["event_id"], ["public.calendar_events.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_index(
        "ix_calendar_audit_actor_id", "calendar_audit", ["actor_id"], schema="public"
    )
    op.create_index(
        "ix_calendar_audit_event_id", "calendar_audit", ["event_id"], schema="public"
    )
    op.create_index(
        "ix_calendar_audit_action", "calendar_audit", ["action"], schema="public"
    )


def downgrade() -> None:
    op.drop_table("calendar_audit", schema="public")
    op.drop_table("calendar_feed_tokens", schema="public")
    op.drop_table("calendar_events", schema="public")
