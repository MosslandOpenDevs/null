import json
import uuid
from typing import Any, Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.db import get_db
from null_engine.models.schemas import AgentExportOut
from null_engine.models.tables import (
    Agent,
    Conversation,
    KnowledgeEdge,
    WikiPage,
    World,
)

router = APIRouter(tags=["export"])
TrainingFormat = Literal["chatml", "alpaca", "sharegpt"]


def _parse_include(include: str) -> set[str]:
    return {token.strip() for token in include.split(",") if token.strip()}


def _conversation_training_sample(conversation: Any, fmt: TrainingFormat) -> dict[str, Any] | None:
    messages: list[dict[str, Any]] = conversation.messages or []
    if not messages:
        return None

    if fmt == "chatml":
        chatml_messages = [{"role": "system", "content": f"Topic: {conversation.topic}"}]
        for message in messages:
            agent_id = message.get("agent_id", "unknown")
            content = message.get("content", "")
            chatml_messages.append(
                {"role": "user", "content": f"[{agent_id}]: {content}"}
            )
        if conversation.summary:
            chatml_messages.append({"role": "assistant", "content": conversation.summary})
        return {"messages": chatml_messages}

    if fmt == "alpaca":
        instruction = f"Continue the conversation about '{conversation.topic}'"
        input_text = "\n".join(
            f"{message.get('agent_id', '')}: {message.get('content', '')}"
            for message in messages[:2]
        )
        output_text = "\n".join(
            f"{message.get('agent_id', '')}: {message.get('content', '')}"
            for message in messages[2:]
        )
        return {
            "instruction": instruction,
            "input": input_text,
            "output": output_text or conversation.summary,
        }

    sharegpt_conversations = [
        {"from": "human", "value": message.get("content", "")}
        for message in messages
    ]
    if conversation.summary:
        sharegpt_conversations.append({"from": "gpt", "value": conversation.summary})
    return {"conversations": sharegpt_conversations}


def _wiki_training_sample(page: Any, fmt: TrainingFormat) -> dict[str, Any]:
    if fmt == "chatml":
        return {
            "messages": [
                {"role": "system", "content": "You are a world-building wiki author."},
                {"role": "user", "content": f"Write a wiki article about: {page.title}"},
                {"role": "assistant", "content": page.content},
            ]
        }
    if fmt == "alpaca":
        return {
            "instruction": f"Write a wiki article about: {page.title}",
            "input": "",
            "output": page.content,
        }
    return {
        "conversations": [
            {"from": "human", "value": f"Write about {page.title}"},
            {"from": "gpt", "value": page.content},
        ]
    }


def _knowledge_graph_training_sample(
    edges: list[Any], fmt: TrainingFormat
) -> dict[str, Any] | None:
    if not edges:
        return None

    triples = [f"{edge.subject} {edge.predicate} {edge.object}" for edge in edges]
    triple_text = "\n".join(triples)

    if fmt == "chatml":
        return {
            "messages": [
                {"role": "system", "content": "Extract knowledge triples."},
                {"role": "assistant", "content": triple_text},
            ]
        }
    if fmt == "alpaca":
        return {
            "instruction": "List knowledge graph triples.",
            "input": "",
            "output": triple_text,
        }
    return {
        "conversations": [
            {"from": "human", "value": "What are the key relationships?"},
            {"from": "gpt", "value": triple_text},
        ]
    }


@router.get("/worlds/{world_id}/export/wiki", response_model=list[dict[str, Any]])
async def export_wiki(
    world_id: uuid.UUID,
    format: str = Query("md", pattern="^(md|json)$"),
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


@router.get(
    "/worlds/{world_id}/export/conversations",
    response_model=list[dict[str, Any]],
)
async def export_conversations(
    world_id: uuid.UUID,
    format: str = Query("jsonl", pattern="^(jsonl|json)$"),
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


@router.get("/worlds/{world_id}/export/training", response_model=list[dict[str, Any]])
async def export_training_data(
    world_id: uuid.UUID,
    format: TrainingFormat = Query("chatml", pattern="^(chatml|alpaca|sharegpt)$"),
    include: str = Query("conversations,wiki,kg"),
    db: AsyncSession = Depends(get_db),
):
    """Export world data in LLM training formats."""
    include_set = _parse_include(include)
    samples: list[dict] = []

    if "conversations" in include_set:
        result = await db.execute(
            select(Conversation)
            .where(Conversation.world_id == world_id)
            .order_by(Conversation.created_at)
        )
        for c in result.scalars().all():
            sample = _conversation_training_sample(c, format)
            if sample:
                samples.append(sample)

    if "wiki" in include_set:
        result = await db.execute(
            select(WikiPage).where(WikiPage.world_id == world_id)
        )
        for p in result.scalars().all():
            samples.append(_wiki_training_sample(p, format))

    if "kg" in include_set:
        result = await db.execute(
            select(KnowledgeEdge).where(KnowledgeEdge.world_id == world_id)
        )
        edges = result.scalars().all()
        kg_sample = _knowledge_graph_training_sample(edges, format)
        if kg_sample:
            samples.append(kg_sample)

    lines = [json.dumps(s, ensure_ascii=False) for s in samples]
    return PlainTextResponse("\n".join(lines), media_type="application/jsonl")


@router.get(
    "/worlds/{world_id}/export/knowledge-graph",
    response_model=list[dict[str, Any]],
)
async def export_knowledge_graph(
    world_id: uuid.UUID,
    format: str = Query("json", pattern="^(csv|json)$"),
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


@router.get("/worlds/{world_id}/export/agents", response_model=list[AgentExportOut])
async def export_agents(
    world_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Agent).where(Agent.world_id == world_id))
    agents = result.scalars().all()
    data = [
        {
            "id": str(a.id),
            "world_id": str(a.world_id),
            "name": a.name,
            "faction_id": str(a.faction_id) if a.faction_id else None,
            "persona": a.persona,
            "beliefs": a.beliefs,
            "status": a.status,
        }
        for a in agents
    ]
    return JSONResponse(data)


@router.get("/worlds/{world_id}/export/all", response_model=list[dict[str, Any]])
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
