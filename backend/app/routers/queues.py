import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.queue import (
    CalledEntryResponse,
    CallRequest,
    EntryResponse,
    JoinRequest,
)
from app.services import queue_service

router = APIRouter(tags=["queues"])


@router.post("/queues/{queue_id}/join", response_model=EntryResponse, status_code=201)
async def join_queue(
    queue_id: uuid.UUID, body: JoinRequest, db: AsyncSession = Depends(get_db)
):
    return await queue_service.join_queue(db, queue_id, body.email)


@router.post("/queues/{queue_id}/call-next", response_model=CalledEntryResponse)
async def call_next(
    queue_id: uuid.UUID, body: CallRequest, db: AsyncSession = Depends(get_db)
):
    return await queue_service.call_next(db, queue_id, body.counter_id)


@router.post("/entries/{entry_id}/done", response_model=EntryResponse)
async def mark_done(entry_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await queue_service.mark_done(db, entry_id)
