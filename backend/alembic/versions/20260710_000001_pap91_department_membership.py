"""Add membership status to department members (PAP-91).

Introduces the PENDING/ACTIVE lifecycle so volunteers can request to join a
department and someone with permission approves them. Existing memberships are
backfilled to ACTIVE.

Revision ID: pap91_dept_membership
Revises: pap89_tasks
Create Date: 2026-07-10 00:00:01+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "pap91_dept_membership"
down_revision: str | Sequence[str] | None = "pap96_submit_permissions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "department_members",
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="ACTIVE",
        ),
    )


def downgrade() -> None:
    op.drop_column("department_members", "status")
