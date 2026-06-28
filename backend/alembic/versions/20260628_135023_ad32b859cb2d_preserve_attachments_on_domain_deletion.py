"""preserve attachments on domain deletion

Revision ID: ad32b859cb2d
Revises: pap53_attachments
Create Date: 2026-06-28 13:50:23.064242+00:00

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ad32b859cb2d"
down_revision: Union[str, Sequence[str], None] = "pap53_attachments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    _replace_attachment_foreign_keys(ondelete="SET NULL")


def downgrade() -> None:
    """Downgrade schema."""
    _replace_attachment_foreign_keys(ondelete="CASCADE")


def _replace_attachment_foreign_keys(*, ondelete: str) -> None:
    foreign_keys = {
        "beneficiary_id": "beneficiaries",
        "group_id": "groups",
        "volunteer_id": "volunteers",
    }
    for column_name, referenced_table in foreign_keys.items():
        constraint_name = f"attachments_{column_name}_fkey"
        op.drop_constraint(
            constraint_name,
            "attachments",
            type_="foreignkey",
            schema="public",
        )
        op.create_foreign_key(
            constraint_name,
            "attachments",
            referenced_table,
            [column_name],
            ["id"],
            source_schema="public",
            referent_schema="public",
            ondelete=ondelete,
        )
