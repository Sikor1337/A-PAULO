"""E-mail verification and password reset (PAP-87).

Adds users.email_verified_at (existing accounts are grandfathered as
verified) and the email_tokens table for one-time verification/reset
tokens (only SHA-256 hashes are stored).

Revision ID: pap87_email_verification
Revises: pap89_tasks
Create Date: 2026-07-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "pap87_email_verification"
down_revision: str | Sequence[str] | None = "pap89_tasks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Existing accounts predate verification; treat them as verified so
    # nobody is locked out by the new login gate.
    op.execute("UPDATE users SET email_verified_at = NOW()")

    op.create_table(
        "email_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.String(length=20), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_email_tokens_user_id", "email_tokens", ["user_id"])
    op.create_index("ix_email_tokens_purpose", "email_tokens", ["purpose"])


def downgrade() -> None:
    op.drop_index("ix_email_tokens_purpose", table_name="email_tokens")
    op.drop_index("ix_email_tokens_user_id", table_name="email_tokens")
    op.drop_table("email_tokens")
    op.drop_column("users", "email_verified_at")
