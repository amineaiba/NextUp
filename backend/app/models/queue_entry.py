import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import EntryStatus, db_enum


class QueueEntry(Base):
    __tablename__ = "queue_entries"
    __table_args__ = (
        # call_next filters on queue_id + status and sorts by position.
        # Without this index that lookup scans the whole table.
        Index(
            "ix_queue_entries_queue_status_position",
            "queue_id",
            "status",
            "position",
        ),
        UniqueConstraint("queue_id", "email", name="uq_queue_entries_queue_email"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str]
    position: Mapped[int]
    status: Mapped[EntryStatus] = mapped_column(db_enum(EntryStatus, "entry_status"))
    push_subscription: Mapped[str | None]
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    called_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    done_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    queue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("queues.id", ondelete="CASCADE")
    )
    counter_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("counters.id"), default=None
    )
