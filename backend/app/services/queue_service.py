import uuid
from dataclasses import dataclass

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AlreadyInQueue,
    EntryNotCallable,
    EntryNotFound,
    NoOneWaiting,
    QueueNotOpen,
)
from app.models import Queue, QueueEntry
from app.models.enums import EntryStatus, QueueStatus


@dataclass(frozen=True)
class EntryPosition:
    """What a waiting client sees when they poll: their ticket number, their
    state, and how many people are still in front of them."""

    id: uuid.UUID
    position: int
    status: EntryStatus
    people_ahead: int


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


async def get_position(db: AsyncSession, entry_id: uuid.UUID) -> EntryPosition:
    # populate_existing: always read the row from the database, never from
    # what this session already remembers. A poll must show the state right
    # now, even if this same session called or finished the entry earlier.
    entry = await db.get(QueueEntry, entry_id, populate_existing=True)
    if entry is None:
        raise EntryNotFound

    # Only someone still waiting has people ahead. Once called, done, or
    # skipped, the number in front of them is meaningless, so report 0.
    people_ahead = 0
    if entry.status == EntryStatus.WAITING:
        # Two reads, not one locked transaction: this is position *display*,
        # which may lag a moment (the L8 rule). The index on
        # (queue_id, status, position) covers this count exactly.
        count_stmt = (
            select(func.count())
            .select_from(QueueEntry)
            .where(
                QueueEntry.queue_id == entry.queue_id,
                QueueEntry.status == EntryStatus.WAITING,
                QueueEntry.position < entry.position,
            )
        )
        people_ahead = (await db.execute(count_stmt)).scalar_one()

    return EntryPosition(
        id=entry.id,
        position=entry.position,
        status=entry.status,
        people_ahead=people_ahead,
    )
