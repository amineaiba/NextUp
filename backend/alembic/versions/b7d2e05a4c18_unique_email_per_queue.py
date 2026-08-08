"""unique email per queue

Revision ID: b7d2e05a4c18
Revises: a1c4f7e29b30
Create Date: 2026-08-08 00:05:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b7d2e05a4c18'
down_revision: Union[str, None] = 'a1c4f7e29b30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CONSTRAINT_NAME = "uq_queue_entries_queue_email"


def upgrade() -> None:
    # One spot per email per line. The service turns the resulting
    # IntegrityError into a 409.
    op.create_unique_constraint(
        CONSTRAINT_NAME, "queue_entries", ["queue_id", "email"]
    )


def downgrade() -> None:
    op.drop_constraint(CONSTRAINT_NAME, "queue_entries", type_="unique")
