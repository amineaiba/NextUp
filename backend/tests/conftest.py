import uuid
from collections.abc import AsyncGenerator
from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.db import engine
from app.models import Business, Counter, Queue, Service
from app.models.enums import QueueStatus


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """One session per test, matching how a request gets its own session."""
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as db:
        yield db
    # Each test runs in its own event loop, and an asyncpg connection only
    # works on the loop that opened it. Drop the pool here, or the next test
    # gets handed a connection from a loop that no longer exists.
    await engine.dispose()


@pytest_asyncio.fixture
async def open_queue(session: AsyncSession) -> AsyncGenerator[Queue, None]:
    """A business -> service -> open queue, torn down after the test.

    Own UUIDs, not the dev_seed.sql ones: tests never touch seed data. No
    relationship() on the models (deliberate, see queue_service.py), so the
    foreign keys are set by hand instead of by assigning related objects.
    """
    business_id = uuid.uuid4()
    service_id = uuid.uuid4()
    queue_id = uuid.uuid4()

    # No relationship() on the models, so the session does not know these rows
    # depend on each other. Commit in FK order by hand instead of one add_all.
    session.add(Business(id=business_id, name="Test Clinic", email="test@clinic.dev"))
    await session.commit()

    session.add(Service(id=service_id, name="General Checkup", business_id=business_id))
    await session.commit()

    queue = Queue(
        id=queue_id, status=QueueStatus.OPEN, date=date.today(), service_id=service_id
    )
    session.add(queue)
    session.add(Counter(label="Counter A", service_id=service_id))
    await session.commit()
    await session.refresh(queue)

    yield queue

    # queue_entries.counter_id has no ON DELETE rule, so entries must be gone
    # before the counters are. Deleting the queue cascades to its entries;
    # the business then cascades to service, counter, and the empty queue
    # (the CASCADE rules live in the migrations, not in the ORM).
    await session.delete(queue)
    await session.commit()
    business = await session.get(Business, business_id)
    await session.delete(business)
    await session.commit()


@pytest_asyncio.fixture
async def counter_id(session: AsyncSession, open_queue: Queue) -> uuid.UUID:
    """The one counter open_queue created, for tests that need to call_next."""
    return (
        await session.execute(
            select(Counter.id).where(Counter.service_id == open_queue.service_id)
        )
    ).scalar_one()


@pytest.fixture
def unique_email() -> str:
    return f"{uuid.uuid4()}@test.dev"
