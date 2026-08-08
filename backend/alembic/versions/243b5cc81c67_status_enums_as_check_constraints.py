"""status enums as check constraints

Revision ID: 243b5cc81c67
Revises: d506f008f53b
Create Date: 2026-08-06 14:46:28.177612

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '243b5cc81c67'
down_revision: Union[str, None] = 'd506f008f53b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ENUMS = [
    ("queues", "status", "queue_status", ["open", "closed"]),
    (
        "queue_entries",
        "status",
        "entry_status",
        ["waiting", "called", "serving", "done", "no_show", "skipped"],
    ),
    (
        "queue_events",
        "event_type",
        "queue_event_type",
        ["joined", "called", "skipped", "no_show", "done"],
    ),
]


def upgrade() -> None:
    for table, column, name, values in ENUMS:
        op.alter_column(
            table,
            column,
            existing_type=sa.VARCHAR(),
            type_=sa.VARCHAR(length=max(len(v) for v in values)),
            existing_nullable=False,
        )
        op.create_check_constraint(name, table, sa.column(column).in_(values))


def downgrade() -> None:
    for table, column, name, values in ENUMS:
        op.drop_constraint(name, table, type_="check")
        op.alter_column(
            table,
            column,
            existing_type=sa.VARCHAR(length=max(len(v) for v in values)),
            type_=sa.VARCHAR(),
            existing_nullable=False,
        )
