import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.core.runner import SimulationRunner
from null_engine.db import async_session, get_db
from null_engine.models.schemas import (
    RecentMessageOut,
    SimulationControlOut,
    WorldCardOut,
    WorldCreate,
    WorldOut,
    WorldTagOut,
)
from null_engine.models.tables import Agent, Conversation, WikiPage, World, WorldTag

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


@router.get("/worlds/{world_id}/recent-messages", response_model=list[RecentMessageOut])
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


@router.post("/worlds/{world_id}/start", response_model=SimulationControlOut)
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


@router.post("/worlds/{world_id}/stop", response_model=SimulationControlOut)
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


# --- Seed Bomb ---
from pydantic import BaseModel


class SeedBombRequest(BaseModel):
    topic: str


@router.post("/worlds/{world_id}/seed-bomb")
async def seed_bomb(world_id: uuid.UUID, body: SeedBombRequest, db: AsyncSession = Depends(get_db)):
    """Inject a topic into the next conversation round."""
    result = await db.execute(select(World).where(World.id == world_id))
    world = result.scalar_one_or_none()
    if not world:
        raise HTTPException(404, "World not found")

    # Store injected topic in world config
    config = dict(world.config or {})
    injected = config.get("_injected_topics", [])
    injected.append(body.topic)
    config["_injected_topics"] = injected
    world.config = config
    await db.commit()

    from null_engine.ws.handler import broadcast
    from null_engine.models.schemas import WSEnvelope

    await broadcast(world_id, WSEnvelope(
        type="event.triggered",
        epoch=world.current_epoch,
        payload={
            "description": f"A new idea ripples through the world: '{body.topic}'",
            "text": f"Seed bomb: {body.topic}",
            "source": "divine_intervention",
            "tick": world.current_tick,
        },
    ))

    return {"status": "injected", "topic": body.topic}


# --- Catch Up ---
@router.get("/worlds/{world_id}/catch-up")
async def catch_up(world_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """LLM-generated summary of recent events."""
    result = await db.execute(select(World).where(World.id == world_id))
    world = result.scalar_one_or_none()
    if not world:
        raise HTTPException(404, "World not found")

    # Get recent conversations
    conv_result = await db.execute(
        select(Conversation)
        .where(Conversation.world_id == world_id)
        .order_by(Conversation.created_at.desc())
        .limit(5)
    )
    recent_convs = conv_result.scalars().all()

    if not recent_convs:
        return {"summary": "Nothing of note has occurred yet in this world."}

    context = "\n".join(
        f"- Topic: {c.topic}. Summary: {c.summary[:200]}"
        for c in recent_convs if c.summary
    )

    try:
        from null_engine.services.llm_router import llm_router

        prompt = f"""Summarize the recent events in this simulated world in 3-5 sentences.
Write in a dramatic, cosmic narrator style.

Recent events:
{context}

Summary:"""

        summary = await llm_router.generate_text(role="reaction_agent", prompt=prompt)
        return {"summary": summary.strip()}
    except Exception:
        summaries = [c.summary[:100] for c in recent_convs if c.summary]
        return {"summary": " ".join(summaries) if summaries else "The void stirs, but details are unclear."}


# --- Analytics: Faction Power ---
@router.get("/worlds/{world_id}/analytics/faction-power")
async def faction_power_analytics(world_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Faction power over epochs."""
    from null_engine.models.tables import Faction, Relationship
    from sqlalchemy import and_

    result = await db.execute(select(World).where(World.id == world_id))
    world = result.scalar_one_or_none()
    if not world:
        raise HTTPException(404, "World not found")

    # Get factions
    factions_result = await db.execute(select(Faction).where(Faction.world_id == world_id))
    factions = factions_result.scalars().all()

    # Simple: return current power per faction (agent count × avg relationship strength)
    data = []
    for f in factions:
        agent_count_result = await db.execute(
            select(func.count()).where(Agent.faction_id == f.id)
        )
        count = agent_count_result.scalar() or 0

        data.append({
            "faction_id": str(f.id),
            "faction_name": f.name,
            "color": f.color,
            "agent_count": count,
            "power": count,  # Simplified; could factor in relationships
        })

    return {"epoch": world.current_epoch, "factions": data}


# --- Analytics: Agent Influence ---
@router.get("/worlds/{world_id}/analytics/agent-influence")
async def agent_influence_analytics(
    world_id: uuid.UUID,
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Agent influence radar data."""
    from null_engine.models.tables import Relationship

    agent_result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = agent_result.scalar_one_or_none()
    if not agent:
        raise HTTPException(404, "Agent not found")

    # Get relationships
    rels_result = await db.execute(
        select(Relationship).where(
            Relationship.world_id == world_id,
            (Relationship.agent_a == agent_id) | (Relationship.agent_b == agent_id),
        )
    )
    rels = rels_result.scalars().all()

    # Get conversation count
    conv_count_result = await db.execute(
        select(func.count())
        .select_from(Conversation)
        .where(Conversation.world_id == world_id)
    )
    conv_count = conv_count_result.scalar() or 0

    avg_strength = sum(r.strength for r in rels) / len(rels) if rels else 0.5
    allies = sum(1 for r in rels if r.strength > 0.6)
    rivals = sum(1 for r in rels if r.strength < 0.3)

    return {
        "agent_id": str(agent_id),
        "agent_name": agent.name,
        "axes": [
            {"axis": "Relationships", "value": len(rels)},
            {"axis": "Avg Strength", "value": round(avg_strength * 10, 1)},
            {"axis": "Allies", "value": allies},
            {"axis": "Rivals", "value": rivals},
            {"axis": "Conversations", "value": min(conv_count, 10)},
        ],
    }
