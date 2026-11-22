import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.db import engine
from app.core.exceptions import AppError
from app.core.logging import setup_logging
from app.routers import queues

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield
    await engine.dispose()


app = FastAPI(title="Virtual Queue", lifespan=lifespan)
app.include_router(queues.router)


@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(IntegrityError)
async def handle_integrity_error(request: Request, exc: IntegrityError) -> JSONResponse:
    logger.warning("constraint violated on %s", request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=409, content={"detail": "Conflict with existing data"}
    )


@app.exception_handler(SQLAlchemyError)
async def handle_db_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    # The traceback goes to the log, never to the client: an error body must
    # not leak SQL or table names.
    logger.exception("database error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Database unavailable"})


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
