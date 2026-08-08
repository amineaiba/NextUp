import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.exceptions import AppError

logger = logging.getLogger(__name__)

# pool_pre_ping: a connection that died while idle gets replaced instead of
# raising on the next request that picks it up.
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        except AppError:
            # Expected outcome (empty queue, wrong state). Roll back, stay quiet:
            # logging these at ERROR would bury the real failures.
            await session.rollback()
            raise
        except Exception:
            # Closing the session already rolls back. The explicit call is here
            # for the log line: a silent rollback is a bug nobody can find.
            await session.rollback()
            logger.exception("db session rolled back")
            raise
