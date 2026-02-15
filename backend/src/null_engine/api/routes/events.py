import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.core.events import inject_event
from null_engine.db import get_db
from null_engine.models.schemas import EventCreate, InjectedEventOut
from null_engine.models.tables import World

router = APIRouter(tags=["events"])


@router.post("/worlds/{world_id}/events", response_model=InjectedEventOut)
async def create_event(world_id: uuid.UUID, body: EventCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(World).where(World.id == world_id))
    world = result.scalar_one_or_none()
    if not world:
        raise HTTPException(404, "World not found")

    event = await inject_event(db, world, body)
    return event
