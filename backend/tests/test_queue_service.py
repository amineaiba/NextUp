import asyncio
import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.db import engine
from app.core.exceptions import EntryNotFound
from app.models import Queue, QueueEntry
from app.models.enums import EntryStatus
from app.services import queue_service

CONCURRENT_JOINS = 20


async def _join_with_own_session(queue_id, email: str) -> QueueEntry:
    # Each concurrent request gets its own session, same as get_db does per
    # real request. Sharing one session across concurrent tasks is not safe.
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as db:
        return await queue_service.join_queue(db, queue_id, email)


async def test_concurrent_joins_never_collide_on_position(
    session: AsyncSession, open_queue: Queue
):
    """The L8 lesson: UPDATE ... RETURNING must give every joiner a distinct
    position, even when they all arrive at once."""
    entries = await asyncio.gather(
        *(
            _join_with_own_session(open_queue.id, f"racer{i}@test.dev")
            for i in range(CONCURRENT_JOINS)
        )
    )

    positions = sorted(entry.position for entry in entries)
    assert positions == list(range(1, CONCURRENT_JOINS + 1))

    rows = (
        await session.execute(
            select(QueueEntry.position)
            .where(QueueEntry.queue_id == open_queue.id)
            .group_by(QueueEntry.position)
            .having(func.count() > 1)
        )
    ).all()
    assert rows == []


async def test_position_counts_people_waiting_ahead(
    session: AsyncSession, open_queue: Queue
):
    await queue_service.join_queue(session, open_queue.id, "first@test.dev")
    await queue_service.join_queue(session, open_queue.id, "second@test.dev")
    third = await queue_service.join_queue(session, open_queue.id, "third@test.dev")

    info = await queue_service.get_position(session, third.id)

    assert info.position == 3
    assert info.status == EntryStatus.WAITING
    assert info.people_ahead == 2


async def test_called_person_stops_counting_as_ahead(
    session: AsyncSession, open_queue: Queue, counter_id: uuid.UUID
):
    first = await queue_service.join_queue(session, open_queue.id, "first@test.dev")
    await queue_service.join_queue(session, open_queue.id, "second@test.dev")
    third = await queue_service.join_queue(session, open_queue.id, "third@test.dev")

    await queue_service.call_next(session, open_queue.id, counter_id)

    assert (await queue_service.get_position(session, third.id)).people_ahead == 1
    called = await queue_service.get_position(session, first.id)
    assert called.status == EntryStatus.CALLED
    assert called.people_ahead == 0


async def test_get_position_unknown_entry_raises(session: AsyncSession):
    with pytest.raises(EntryNotFound):
        await queue_service.get_position(session, uuid.uuid4())
