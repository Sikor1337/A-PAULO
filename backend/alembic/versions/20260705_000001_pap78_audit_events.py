"""Add the append-only generic audit event store.

Revision ID: pap78_audit_events
Revises: pap29_departures
Create Date: 2026-07-05 00:00:01+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision: str = "pap78_audit_events"
down_revision: str | Sequence[str] | None = "pap29_departures"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == "postgresql"
    table_options = (
        {"postgresql_partition_by": "RANGE (created_at)"}
        if is_postgresql
        else {}
    )

    op.create_table(
        "audit_events",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("actor_id", sa.String(length=255), nullable=False),
        sa.Column("actor_display_name", sa.String(length=255), nullable=True),
        sa.Column("context_type", sa.String(length=100), nullable=True),
        sa.Column("context_id", sa.String(length=255), nullable=True),
        sa.Column(
            "changes",
            sa.JSON().with_variant(JSONB(), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", "created_at"),
        **table_options,
    )
    op.create_index(
        "idx_audit_entity",
        "audit_events",
        ["entity_type", "entity_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "idx_audit_context",
        "audit_events",
        ["context_type", "context_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "idx_audit_actor",
        "audit_events",
        ["actor_id", sa.text("created_at DESC")],
    )

    if not is_postgresql:
        return

    op.create_index(
        "idx_audit_changes_gin",
        "audit_events",
        ["changes"],
        postgresql_using="gin",
    )
    op.execute("CREATE TABLE audit_events_default PARTITION OF audit_events DEFAULT")
    op.execute(
        """
        CREATE FUNCTION prevent_audit_event_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'audit_events is append-only';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_events_append_only
        BEFORE UPDATE OR DELETE ON audit_events
        FOR EACH ROW EXECUTE FUNCTION prevent_audit_event_mutation()
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'fastapi_db_user') THEN
                REVOKE UPDATE, DELETE ON audit_events FROM fastapi_db_user;
            END IF;
        END
        $$
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS audit_events_append_only ON audit_events")
        op.execute("DROP FUNCTION IF EXISTS prevent_audit_event_mutation()")
    op.drop_table("audit_events")
