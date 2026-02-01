import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.core.genesis import create_world
from null_engine.core.runner import SimulationRunner
from null_engine.db import get_db
from null_engine.models.tables import World, WorldTag
from null_engine.models.schemas import WorldCreate, WorldOut, WorldTagOut, WorldWithTagsOut

router = APIRouter(tags=["worlds"])

_runners: dict[uuid.UUID, SimulationRunner] = {}


@router.get("/worlds", response_model=list[WorldWithTagsOut])
async def list_worlds(
    tag: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(World).order_by(World.created_at.desc()).limit(50)

    if tag:
        # Filter worlds that have this tag
        world_ids_q = select(WorldTag.world_id).where(WorldTag.tag.ilike(f"%{tag}%"))
        query = query.where(World.id.in_(world_ids_q))

    result = await db.execute(query)
    worlds = result.scalars().all()

    # Attach tags to each world
    out = []
    for w in worlds:
        tags_result = await db.execute(
            select(WorldTag).where(WorldTag.world_id == w.id)
        )
        tags = [WorldTagOut.model_validate(t) for t in tags_result.scalars().all()]
        world_dict = WorldWithTagsOut.model_validate(w)
        world_dict.tags = tags
        out.append(world_dict)

    return out


@router.post("/worlds", response_model=WorldOut, status_code=201)
async def create_world_endpoint(body: WorldCreate, db: AsyncSession = Depends(get_db)):
    world = await create_world(db, body.seed_prompt, body.config)
    return world


@router.get("/worlds/{world_id}", response_model=WorldOut)
async def get_world(world_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(World).where(World.id == world_id))
    world = result.scalar_one_or_none()
    if not world:
        raise HTTPException(404, "World not found")
    return world


@router.post("/worlds/{world_id}/start")
async def start_simulation(world_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(World).where(World.id == world_id))
    world = result.scalar_one_or_none()
    if not world:
        raise HTTPException(404, "World not found")

    if world_id in _runners and _runners[world_id].running:
        raise HTTPException(409, "Simulation already running")

    runner = SimulationRunner(world_id)
    _runners[world_id] = runner
    runner.start()

    world.status = "running"
    await db.commit()
    return {"status": "started", "world_id": str(world_id)}


@router.post("/worlds/{world_id}/stop")
async def stop_simulation(world_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    runner = _runners.get(world_id)
    if not runner or not runner.running:
        raise HTTPException(409, "Simulation not running")

    runner.stop()

    result = await db.execute(select(World).where(World.id == world_id))
    world = result.scalar_one_or_none()
    if world:
        world.status = "paused"
        await db.commit()
    return {"status": "stopped", "world_id": str(world_id)}
