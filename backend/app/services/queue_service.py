import uuid

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AlreadyInQueue,
    EntryNotCallable,
    NoOneWaiting,
    QueueNotOpen,
)
from app.models import Queue, QueueEntry
from app.models.enums import EntryStatus, QueueStatus


async def join_queue(db: AsyncSession, queue_id: uuid.UUID, email: str) -> QueueEntry:
    # One statement, no read-then-write: two clients joining the same second
    # can never be handed the same position.
    stmt = (
        update(Queue)
        .where(Queue.id == queue_id, Queue.status == QueueStatus.OPEN)
        .values(next_position=Queue.next_position + 1)
        .returning(Queue.next_position)
        .execution_options(synchronize_session=False)
    )
    position = (await db.execute(stmt)).scalar_one_or_none()
    if position is None:
        raise QueueNotOpen

    entry = QueueEntry(
        queue_id=queue_id,
        email=email,
        position=position,
        status=EntryStatus.WAITING,
    )
    db.add(entry)
    try:
        await db.commit()
    except IntegrityError as exc:
        # Rolling back also undoes the position bump above, so a rejected join
        # does not burn a number in the line.
        await db.rollback()
        raise AlreadyInQueue from exc
    return entry


async def call_next(
    db: AsyncSession, queue_id: uuid.UUID, counter_id: uuid.UUID
) -> QueueEntry:
    # Guarded queue-pop: lock the oldest waiting row, skip rows already locked
    # by a concurrent call-next on another counter, then update it in the same
    # statement. Two staff at two counters can never grab the same person.
    next_entry_id = (
        select(QueueEntry.id)
        .where(
            QueueEntry.queue_id == queue_id, QueueEntry.status == EntryStatus.WAITING
        )
        .order_by(QueueEntry.position)
        .limit(1)
        .with_for_update(skip_locked=True)
        .scalar_subquery()
    )
    stmt = (
        update(QueueEntry)
        .where(QueueEntry.id == next_entry_id)
        .values(status=EntryStatus.CALLED, counter_id=counter_id, called_at=func.now())
        .returning(QueueEntry)
        .execution_options(synchronize_session=False)
    )
    entry = (await db.execute(stmt)).scalar_one_or_none()
    if entry is None:
        raise NoOneWaiting
    await db.commit()
    return entry


async def mark_done(db: AsyncSession, entry_id: uuid.UUID) -> QueueEntry:
    stmt = (
        update(QueueEntry)
        .where(
            QueueEntry.id == entry_id,
            QueueEntry.status.in_([EntryStatus.CALLED, EntryStatus.SERVING]),
        )
        .values(status=EntryStatus.DONE, done_at=func.now())
        .returning(QueueEntry)
        .execution_options(synchronize_session=False)
    )
    entry = (await db.execute(stmt)).scalar_one_or_none()
    if entry is None:
        raise EntryNotCallable
    await db.commit()
    return entry
