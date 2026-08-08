import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Business(Base):
    """Tenant root. Owns services, which own counters and queues."""

    __tablename__ = "businesses"

    # UUID instead of int: safe to expose in URLs, no cross-tenant guessing.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str]
    email: Mapped[str]
    # server_default: DB writes the timestamp, so it is right even on raw SQL inserts.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
