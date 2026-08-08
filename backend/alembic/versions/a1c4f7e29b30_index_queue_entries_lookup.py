"""index queue_entries lookup

Revision ID: a1c4f7e29b30
Revises: 243b5cc81c67
Create Date: 2026-08-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1c4f7e29b30'
down_revision: Union[str, None] = '243b5cc81c67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEX_NAME = "ix_queue_entries_queue_status_position"


def upgrade() -> None:
    # Matches the call_next lookup: filter queue_id + status, order by position.
    op.create_index(
        INDEX_NAME,
        "queue_entries",
        ["queue_id", "status", "position"],
    )


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name="queue_entries")
