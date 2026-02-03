import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.core.genesis import create_world
from null_engine.core.runner import SimulationRunner
from null_engine.db import get_db, async_session
from null_engine.models.tables import World, WorldTag, Agent, Conversation, WikiPage
from null_engine.models.schemas import WorldCreate, WorldOut, WorldTagOut, WorldWithTagsOut, WorldCardOut

router = APIRouter(tags=["worlds"])

_runners: dict[uuid.UUID, SimulationRunner] = {}
_genesis_tasks: dict[uuid.UUID, asyncio.Task] = {}


@router.get("/worlds", response_model=list[WorldCardOut])
async def list_worlds(
    tag: str | None = None,
    mature: bool | None = None,
    incubating: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(World).order_by(World.created_at.desc()).limit(50)

    if tag:
        world_ids_q = select(WorldTag.world_id).where(WorldTag.tag.ilike(f"%{tag}%"))
        query = query.where(World.id.in_(world_ids_q))

    result = await db.execute(query)
    worlds = result.scalars().all()

    if not worlds:
        return []

    world_ids = [w.id for w in worlds]

    # Batch count agents per world
    agent_counts_q = await db.execute(
        select(Agent.world_id, func.count()).where(Agent.world_id.in_(world_ids)).group_by(Agent.world_id)
    )
    agent_counts = dict(agent_counts_q.all())

    # Batch count conversations per world
    conv_counts_q = await db.execute(
        select(Conversation.world_id, func.count()).where(Conversation.world_id.in_(world_ids)).group_by(Conversation.world_id)
    )
    conv_counts = dict(conv_counts_q.all())

    # Batch count wiki pages per world
    wiki_counts_q = await db.execute(
        select(WikiPage.world_id, func.count()).where(WikiPage.world_id.in_(world_ids)).group_by(WikiPage.world_id)
    )
    wiki_counts = dict(wiki_counts_q.all())

    # Batch fetch latest conversation topic per world
    latest_conv_q = await db.execute(
        select(
            Conversation.world_id,
            Conversation.topic,
        )
        .distinct(Conversation.world_id)
        .where(Conversation.world_id.in_(world_ids))
        .order_by(Conversation.world_id, Conversation.created_at.desc())
    )
    latest_activity_map: dict[uuid.UUID, str] = {}
    for row in latest_conv_q.all():
        if row.world_id not in latest_activity_map:
            latest_activity_map[row.world_id] = row.topic

    # Batch fetch all tags
    tags_q = await db.execute(
        select(WorldTag).where(WorldTag.world_id.in_(world_ids))
    )
    all_tags = tags_q.scalars().all()
    tags_by_world: dict[uuid.UUID, list[WorldTagOut]] = {}
    for t in all_tags:
        tags_by_world.setdefault(t.world_id, []).append(WorldTagOut.model_validate(t))

    out = []
    for w in worlds:
        agent_count = agent_counts.get(w.id, 0)
        conversation_count = conv_counts.get(w.id, 0)
        wiki_page_count = wiki_counts.get(w.id, 0)

        # Apply maturity filters
        is_mature = conversation_count >= 5 and wiki_page_count >= 1
        if mature and not is_mature:
            continue
        if incubating and is_mature:
            continue

        card = WorldCardOut.model_validate(w)
        card.tags = tags_by_world.get(w.id, [])
        card.agent_count = agent_count
        card.conversation_count = conversation_count
        card.wiki_page_count = wiki_page_count
        card.epoch_count = w.current_epoch
        card.latest_activity = latest_activity_map.get(w.id)

        out.append(card)

    return out


@router.get("/worlds/{world_id}/recent-messages")
async def get_recent_messages(world_id: uuid.UUID, limit: int = 5, db: AsyncSession = Depends(get_db)):
    """Return recent conversation messages for the SystemPulse mini-feed."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.world_id == world_id)
        .order_by(Conversation.created_at.desc())
        .limit(limit)
    )
    conversations = result.scalars().all()

    messages = []
    for conv in reversed(conversations):
        msgs_ko = conv.messages_ko or []
        for idx, msg in enumerate((conv.messages or [])[-2:]):
            real_idx = len(conv.messages or []) - 2 + idx
            if real_idx < 0:
                real_idx = idx
            ko_msg = msgs_ko[real_idx] if real_idx < len(msgs_ko) else None
            entry = {
                "agent_id": msg.get("agent_id", ""),
                "agent_name": msg.get("agent_name", ""),
                "content": msg.get("content", ""),
                "epoch": conv.epoch,
                "topic": conv.topic,
            }
            if ko_msg:
                entry["content_ko"] = ko_msg.get("content", "")
            if conv.topic_ko:
                entry["topic_ko"] = conv.topic_ko
            messages.append(entry)

    return messages[-10:]


async def _background_genesis(world_id: uuid.UUID, seed_prompt: str, extra_config: dict):
    """Run full genesis in background after the world row is created."""
    import structlog
    logger = structlog.get_logger()
    try:
        async with async_session() as db:
            from null_engine.core.genesis import populate_world
            await populate_world(db, world_id, seed_prompt, extra_config)
        # Auto-start simulation after genesis completes
        from null_engine.core.runner import SimulationRunner
        runner = SimulationRunner(world_id)
        _runners[world_id] = runner
        runner.start()

        async with async_session() as db:
            result = await db.execute(select(World).where(World.id == world_id))
            world = result.scalar_one_or_none()
            if world:
                world.status = "running"
                await db.commit()
            logger.info("genesis.background_complete", world_id=str(world_id), status="running")
    except Exception:
        logger.exception("genesis.background_failed", world_id=str(world_id))
        try:
            async with async_session() as db:
                result = await db.execute(select(World).where(World.id == world_id))
                world = result.scalar_one_or_none()
                if world:
                    world.status = "error"
                    await db.commit()
        except Exception:
            pass
    finally:
        _genesis_tasks.pop(world_id, None)


@router.post("/worlds", response_model=WorldOut, status_code=201)
async def create_world_endpoint(body: WorldCreate, db: AsyncSession = Depends(get_db)):
    world = World(seed_prompt=body.seed_prompt, config=body.config or {}, status="generating")
    db.add(world)
    await db.flush()
    await db.commit()
    await db.refresh(world)

    task = asyncio.create_task(
        _background_genesis(world.id, body.seed_prompt, body.config or {})
    )
    _genesis_tasks[world.id] = task

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
