"""Add required recruitment onboarding meetings.

Revision ID: pap59_onboarding_meetings
Revises: pap49_calendar
Create Date: 2026-07-02 16:30:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "pap59_onboarding_meetings"
down_revision: str | Sequence[str] | None = "pap49_calendar"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_MEETING_TYPES = ("CHARISM", "COMMUNITY", "ADMINISTRATION", "ACTIVITY")


def upgrade() -> None:
    op.create_table(
        "recruitment_onboarding_meetings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("submission_id", sa.Integer(), nullable=False),
        sa.Column("meeting_type", sa.String(length=30), nullable=False),
        sa.Column("attended_at", sa.DateTime(timezone=True), nullable=True),
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
            ["submission_id"],
            ["recruitment_submissions.id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "meeting_type IN ('CHARISM', 'COMMUNITY', 'ADMINISTRATION', 'ACTIVITY')",
            name="ck_recruitment_onboarding_meeting_type",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "submission_id",
            "meeting_type",
            name="uq_recruitment_onboarding_meeting_type",
        ),
    )
    op.create_index(
        "ix_recruitment_onboarding_meetings_submission_id",
        "recruitment_onboarding_meetings",
        ["submission_id"],
        unique=False,
    )

    submissions = sa.table(
        "recruitment_submissions",
        sa.column("id", sa.Integer()),
        sa.column("status", sa.String()),
    )
    meetings = sa.table(
        "recruitment_onboarding_meetings",
        sa.column("submission_id", sa.Integer()),
        sa.column("meeting_type", sa.String()),
    )
    connection = op.get_bind()
    onboarding_ids = connection.execute(
        sa.select(submissions.c.id).where(submissions.c.status == "ONBOARDING")
    ).scalars()
    rows = [
        {"submission_id": submission_id, "meeting_type": meeting_type}
        for submission_id in onboarding_ids
        for meeting_type in _MEETING_TYPES
    ]
    if rows:
        op.bulk_insert(meetings, rows)


def downgrade() -> None:
    op.drop_index(
        "ix_recruitment_onboarding_meetings_submission_id",
        table_name="recruitment_onboarding_meetings",
    )
    op.drop_table("recruitment_onboarding_meetings")
