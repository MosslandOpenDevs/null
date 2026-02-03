import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.db import get_db
from null_engine.models.tables import Conversation, WikiPage, Stratum, Agent, Faction

router = APIRouter(tags=["conversations"])


@router.get("/worlds/{world_id}/conversations")
async def list_conversations(
    world_id: uuid.UUID,
    limit: int = Query(20, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.world_id == world_id)
        .order_by(Conversation.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    conversations = result.scalars().all()

    if not conversations:
        return []

    # Collect all participant agent IDs
    all_agent_ids: set[uuid.UUID] = set()
    for conv in conversations:
        for pid in (conv.participants or []):
            try:
                all_agent_ids.add(uuid.UUID(str(pid)))
            except (ValueError, AttributeError):
                pass

    # Batch fetch agents + faction colors
    agent_map: dict[str, dict] = {}
    if all_agent_ids:
        agents_result = await db.execute(
            select(Agent.id, Agent.name, Agent.faction_id)
            .where(Agent.id.in_(list(all_agent_ids)))
        )
        agents_rows = agents_result.all()
        faction_ids = {r.faction_id for r in agents_rows if r.faction_id}

        faction_color_map: dict[uuid.UUID, str] = {}
        if faction_ids:
            factions_result = await db.execute(
                select(Faction.id, Faction.color).where(Faction.id.in_(list(faction_ids)))
            )
            faction_color_map = {r.id: r.color for r in factions_result.all()}

        for r in agents_rows:
            agent_map[str(r.id)] = {
                "id": str(r.id),
                "name": r.name,
                "faction_color": faction_color_map.get(r.faction_id, "#6366f1") if r.faction_id else "#6366f1",
            }

    out = []
    for conv in conversations:
        participants = []
        for pid in (conv.participants or []):
            pid_str = str(pid)
            if pid_str in agent_map:
                participants.append(agent_map[pid_str])
            else:
                participants.append({"id": pid_str, "name": "Unknown", "faction_color": "#6366f1"})

        out.append({
            "id": str(conv.id),
            "epoch": conv.epoch,
            "tick": conv.tick,
            "topic": conv.topic,
            "topic_ko": conv.topic_ko,
            "participants": participants,
            "messages": conv.messages or [],
            "messages_ko": conv.messages_ko,
            "summary": conv.summary or "",
            "summary_ko": conv.summary_ko,
            "created_at": conv.created_at.isoformat() if conv.created_at else None,
        })

    return out


@router.get("/worlds/{world_id}/feed")
async def get_feed(
    world_id: uuid.UUID,
    limit: int = Query(20, le=50),
    before: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    before_dt = datetime.fromisoformat(before) if before else datetime.utcnow()

    # Fetch conversations
    conv_result = await db.execute(
        select(Conversation)
        .where(Conversation.world_id == world_id, Conversation.created_at < before_dt)
        .order_by(Conversation.created_at.desc())
        .limit(limit)
    )
    conversations = conv_result.scalars().all()

    # Collect agent info for conversations
    all_agent_ids: set[uuid.UUID] = set()
    for conv in conversations:
        for pid in (conv.participants or []):
            try:
                all_agent_ids.add(uuid.UUID(str(pid)))
            except (ValueError, AttributeError):
                pass

    agent_name_map: dict[str, str] = {}
    if all_agent_ids:
        agents_result = await db.execute(
            select(Agent.id, Agent.name).where(Agent.id.in_(list(all_agent_ids)))
        )
        agent_name_map = {str(r.id): r.name for r in agents_result.all()}

    # Fetch recent wiki edits
    wiki_result = await db.execute(
        select(WikiPage)
        .where(WikiPage.world_id == world_id, WikiPage.created_at < before_dt)
        .order_by(WikiPage.created_at.desc())
        .limit(limit)
    )
    wiki_pages = wiki_result.scalars().all()

    # Fetch wiki agent names
    wiki_agent_ids = {wp.created_by_agent for wp in wiki_pages if wp.created_by_agent}
    wiki_agent_names: dict[str, str] = {}
    if wiki_agent_ids:
        wa_result = await db.execute(
            select(Agent.id, Agent.name).where(Agent.id.in_(list(wiki_agent_ids)))
        )
        wiki_agent_names = {str(r.id): r.name for r in wa_result.all()}

    # Fetch strata
    strata_result = await db.execute(
        select(Stratum)
        .where(Stratum.world_id == world_id)
        .order_by(Stratum.epoch.desc())
        .limit(limit)
    )
    strata = strata_result.scalars().all()

    # Merge into feed items
    items = []

    for conv in conversations:
        participant_names = []
        for pid in (conv.participants or []):
            participant_names.append(agent_name_map.get(str(pid), "Unknown"))

        first_msg = ""
        msgs = conv.messages or []
        if msgs:
            first_msg = (msgs[0].get("content", "") or "")[:120]

        items.append({
            "type": "conversation",
            "data": {
                "id": str(conv.id),
                "topic": conv.topic,
                "topic_ko": conv.topic_ko,
                "participant_names": participant_names,
                "message_count": len(msgs),
                "first_message_preview": first_msg,
            },
            "created_at": conv.created_at.isoformat() if conv.created_at else None,
        })

    for wp in wiki_pages:
        items.append({
            "type": "wiki_edit",
            "data": {
                "id": str(wp.id),
                "title": wp.title,
                "title_ko": wp.title_ko,
                "agent_name": wiki_agent_names.get(str(wp.created_by_agent), "Unknown") if wp.created_by_agent else None,
                "status": wp.status.value if hasattr(wp.status, "value") else str(wp.status),
                "version": wp.version,
            },
            "created_at": wp.created_at.isoformat() if wp.created_at else None,
        })

    for s in strata:
        items.append({
            "type": "epoch",
            "data": {
                "id": str(s.id),
                "epoch": s.epoch,
                "summary": s.summary,
                "summary_ko": s.summary_ko,
                "theme_count": len(s.dominant_themes or []),
            },
            "created_at": None,  # strata don't have created_at, sort by epoch
        })

    # Sort by created_at descending, None items at end
    items.sort(key=lambda x: x["created_at"] or "0000", reverse=True)

    return items[:limit]
