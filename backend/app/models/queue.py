import uuid
from datetime import date as date_

from sqlalchemy import ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import QueueStatus, db_enum


class Queue(Base):
    __tablename__ = "queues"
    __table_args__ = (
        UniqueConstraint("service_id", "date", name="uq_queues_service_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    date: Mapped[date_]
    status: Mapped[QueueStatus] = mapped_column(db_enum(QueueStatus, "queue_status"))
    next_position: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE")
    )
