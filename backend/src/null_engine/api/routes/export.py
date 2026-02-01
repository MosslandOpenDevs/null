import json
import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.db import get_db
from null_engine.models.tables import (
    Agent, Conversation, KnowledgeEdge, WikiPage, World,
)

router = APIRouter(tags=["export"])


@router.get("/worlds/{world_id}/export/wiki")
async def export_wiki(
    world_id: uuid.UUID,
    format: str = Query("md", regex="^(md|json)$"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(WikiPage).where(WikiPage.world_id == world_id))
    pages = result.scalars().all()

    if format == "md":
        lines = []
        for p in pages:
            lines.append(f"# {p.title}\n")
            lines.append(f"*Status: {p.status} | Version: {p.version}*\n")
            lines.append(f"{p.content}\n")
            lines.append("---\n")
        return PlainTextResponse("\n".join(lines), media_type="text/markdown")

    data = [
        {
            "id": str(p.id),
            "title": p.title,
            "content": p.content,
            "status": p.status,
            "version": p.version,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in pages
    ]
    return JSONResponse(data)


@router.get("/worlds/{world_id}/export/conversations")
async def export_conversations(
    world_id: uuid.UUID,
    format: str = Query("jsonl", regex="^(jsonl|json)$"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.world_id == world_id)
        .order_by(Conversation.created_at)
    )
    convs = result.scalars().all()

    if format == "jsonl":
        lines = []
        for c in convs:
            obj = {
                "type": "conversation",
                "epoch": c.epoch,
                "tick": c.tick,
                "topic": c.topic,
                "participants": c.participants,
                "messages": c.messages,
                "summary": c.summary,
            }
            lines.append(json.dumps(obj, ensure_ascii=False))
        return PlainTextResponse("\n".join(lines), media_type="application/jsonl")

    data = [
        {
            "id": str(c.id),
            "epoch": c.epoch,
            "tick": c.tick,
            "topic": c.topic,
            "participants": c.participants,
            "messages": c.messages,
            "summary": c.summary,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in convs
    ]
    return JSONResponse(data)


@router.get("/worlds/{world_id}/export/knowledge-graph")
async def export_knowledge_graph(
    world_id: uuid.UUID,
    format: str = Query("json", regex="^(csv|json)$"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(KnowledgeEdge).where(KnowledgeEdge.world_id == world_id)
    )
    edges = result.scalars().all()

    if format == "csv":
        lines = ["subject,predicate,object,confidence"]
        for e in edges:
            subj = e.subject.replace('"', '""')
            pred = e.predicate.replace('"', '""')
            obj = e.object.replace('"', '""')
            lines.append(f'"{subj}","{pred}","{obj}",{e.confidence}')
        return PlainTextResponse("\n".join(lines), media_type="text/csv")

    data = [
        {
            "subject": e.subject,
            "predicate": e.predicate,
            "object": e.object,
            "confidence": e.confidence,
        }
        for e in edges
    ]
    return JSONResponse(data)


@router.get("/worlds/{world_id}/export/agents")
async def export_agents(
    world_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Agent).where(Agent.world_id == world_id))
    agents = result.scalars().all()
    data = [
        {
            "id": str(a.id),
            "name": a.name,
            "faction_id": str(a.faction_id) if a.faction_id else None,
            "persona": a.persona,
            "beliefs": a.beliefs,
            "status": a.status,
        }
        for a in agents
    ]
    return JSONResponse(data)


@router.get("/worlds/{world_id}/export/all")
async def export_all(
    world_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Export everything as JSONL."""
    lines = []

    # World
    result = await db.execute(select(World).where(World.id == world_id))
    world = result.scalar_one_or_none()
    if world:
        lines.append(json.dumps({
            "type": "world",
            "id": str(world.id),
            "seed_prompt": world.seed_prompt,
            "config": world.config,
            "status": world.status,
        }, ensure_ascii=False))

    # Agents
    result = await db.execute(select(Agent).where(Agent.world_id == world_id))
    for a in result.scalars().all():
        lines.append(json.dumps({
            "type": "agent",
            "id": str(a.id),
            "name": a.name,
            "persona": a.persona,
            "beliefs": a.beliefs,
        }, ensure_ascii=False))

    # Wiki
    result = await db.execute(select(WikiPage).where(WikiPage.world_id == world_id))
    for p in result.scalars().all():
        lines.append(json.dumps({
            "type": "wiki_page",
            "id": str(p.id),
            "title": p.title,
            "content": p.content,
            "status": p.status,
        }, ensure_ascii=False))

    # Conversations
    result = await db.execute(select(Conversation).where(Conversation.world_id == world_id))
    for c in result.scalars().all():
        lines.append(json.dumps({
            "type": "conversation",
            "epoch": c.epoch,
            "topic": c.topic,
            "messages": c.messages,
            "summary": c.summary,
        }, ensure_ascii=False))

    # Knowledge graph
    result = await db.execute(select(KnowledgeEdge).where(KnowledgeEdge.world_id == world_id))
    for e in result.scalars().all():
        lines.append(json.dumps({
            "type": "knowledge_edge",
            "subject": e.subject,
            "predicate": e.predicate,
            "object": e.object,
            "confidence": e.confidence,
        }, ensure_ascii=False))

    return PlainTextResponse("\n".join(lines), media_type="application/jsonl")
