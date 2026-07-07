"""Add tasks module: tasks, checklist items, assignees, permissions.

Revision ID: pap89_tasks
Revises: pap83_bug_reports
Create Date: 2026-07-07 00:00:02+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "pap89_tasks"
down_revision: str | Sequence[str] | None = "pap83_bug_reports"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSIONS = (
    ("CAN_VIEW_TASKS", "Podgląd zadań", "Zadania"),
    ("CAN_MANAGE_TASKS", "Zarządzanie zadaniami", "Zadania"),
)


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "status_is_manual",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
            ["department_id"], ["departments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["event_id"], ["calendar_events.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tasks_status"), "tasks", ["status"])
    op.create_index(op.f("ix_tasks_department_id"), "tasks", ["department_id"])
    op.create_index(op.f("ix_tasks_event_id"), "tasks", ["event_id"])

    op.create_table(
        "task_checklist_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=300), nullable=False),
        sa.Column("is_done", sa.Boolean(), nullable=False),
        sa.Column("done_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_task_checklist_items_task_id"), "task_checklist_items", ["task_id"]
    )

    op.create_table(
        "task_assignees",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("volunteer_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["volunteer_id"], ["volunteers.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id", "volunteer_id", name="uq_task_volunteer"),
    )
    op.create_index(op.f("ix_task_assignees_task_id"), "task_assignees", ["task_id"])
    op.create_index(
        op.f("ix_task_assignees_volunteer_id"), "task_assignees", ["volunteer_id"]
    )

    permission_table = sa.table(
        "security_permissions",
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("category", sa.String),
    )
    op.bulk_insert(
        permission_table,
        [
            {"code": code, "name": name, "category": category}
            for code, name, category in PERMISSIONS
        ],
    )

    codes = ", ".join(f"'{code}'" for code, _, _ in PERMISSIONS)
    op.execute(
        f"""
        INSERT INTO security_group_permissions (group_id, permission_id)
        SELECT security_group.id, permission.id
        FROM security_groups AS security_group
        CROSS JOIN security_permissions AS permission
        WHERE security_group.system_key IN ('admin', 'staff')
          AND permission.code IN ({codes})
        """
    )


def downgrade() -> None:
    codes = ", ".join(f"'{code}'" for code, _, _ in PERMISSIONS)
    op.execute(
        f"""
        DELETE FROM security_group_permissions
        WHERE permission_id IN (
            SELECT id FROM security_permissions WHERE code IN ({codes})
        )
        """
    )
    op.execute(f"DELETE FROM security_permissions WHERE code IN ({codes})")
    op.drop_index(op.f("ix_task_assignees_volunteer_id"), table_name="task_assignees")
    op.drop_index(op.f("ix_task_assignees_task_id"), table_name="task_assignees")
    op.drop_table("task_assignees")
    op.drop_index(
        op.f("ix_task_checklist_items_task_id"), table_name="task_checklist_items"
    )
    op.drop_table("task_checklist_items")
    op.drop_index(op.f("ix_tasks_event_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_department_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_status"), table_name="tasks")
    op.drop_table("tasks")
