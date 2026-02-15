"""SemanticIndexer — background service for embedding generation and neighbor discovery.

Periodically:
1. Ensures all entities have embeddings
2. Computes semantic_neighbors for intra-world entities
"""

import asyncio
import time

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.db import async_session
from null_engine.models.tables import (
    Agent,
    Conversation,
    SemanticNeighbor,
    WikiPage,
)

logger = structlog.get_logger()

INDEXER_INTERVAL = 60  # seconds
NEIGHBOR_THRESHOLD = 0.70
MAX_NEIGHBORS = 5


async def _get_embedding(text: str) -> list[float] | None:
    """Reuse convergence embedding helper."""
    from null_engine.services.convergence import _get_embedding as get_emb
    return await get_emb(text)


async def _ensure_agent_embeddings(db: AsyncSession):
    """Generate embeddings for agents without them."""
    result = await db.execute(
        select(Agent).where(Agent.embedding.is_(None)).limit(50)
    )
    agents = result.scalars().all()
    for agent in agents:
        text = f"{agent.name}\n{agent.persona.get('role', '')}\n{agent.persona.get('personality', '')}"
        emb = await _get_embedding(text)
        if emb:
            agent.embedding = emb
    if agents:
        await db.flush()
        logger.info("semantic_indexer.agent_embeddings", count=len(agents))


async def _ensure_conversation_embeddings(db: AsyncSession):
    """Generate embeddings for conversations without them."""
    result = await db.execute(
        select(Conversation).where(Conversation.embedding.is_(None)).limit(50)
    )
    convs = result.scalars().all()
    for conv in convs:
        text = f"{conv.topic}\n{conv.summary}"
        emb = await _get_embedding(text)
        if emb:
            conv.embedding = emb
    if convs:
        await db.flush()
        logger.info("semantic_indexer.conversation_embeddings", count=len(convs))


async def _update_neighbors(db: AsyncSession):
    """Find semantic neighbors among wiki pages within each world."""
    result = await db.execute(
        select(WikiPage)
        .where(WikiPage.embedding.isnot(None))
        .order_by(WikiPage.created_at.desc())
        .limit(200)
    )
    pages = result.scalars().all()
    if len(pages) < 2:
        return

    new_pairs = 0
    for page in pages:
        try:
            neighbor_result = await db.execute(
                select(WikiPage)
                .where(
                    WikiPage.id != page.id,
                    WikiPage.embedding.isnot(None),
                )
                .order_by(WikiPage.embedding.cosine_distance(page.embedding))
                .limit(MAX_NEIGHBORS)
            )
            neighbors = neighbor_result.scalars().all()

            for neighbor in neighbors:
                dist_result = await db.execute(
                    select(
                        WikiPage.embedding.cosine_distance(page.embedding)
                    ).where(WikiPage.id == neighbor.id)
                )
                distance = dist_result.scalar()
                if distance is None:
                    continue
                similarity = 1.0 - float(distance)
                if similarity < NEIGHBOR_THRESHOLD:
                    continue

                is_cross = "true" if page.world_id != neighbor.world_id else "false"

                # Check existing
                existing = await db.execute(
                    select(SemanticNeighbor).where(
                        SemanticNeighbor.entity_a_id == page.id,
                        SemanticNeighbor.entity_b_id == neighbor.id,
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                db.add(SemanticNeighbor(
                    entity_a_type="wiki_page",
                    entity_a_id=page.id,
                    entity_b_type="wiki_page",
                    entity_b_id=neighbor.id,
                    similarity=similarity,
                    is_cross_world=is_cross,
                ))
                new_pairs += 1
        except Exception:
            logger.exception("semantic_indexer.neighbor_error", page_id=str(page.id))

    if new_pairs:
        await db.flush()
        logger.info("semantic_indexer.neighbors_updated", new_pairs=new_pairs)


async def run_indexer_cycle():
    """Single indexer cycle."""
    cycle_started = time.monotonic()
    async with async_session() as db:
        try:
            await _ensure_agent_embeddings(db)
            await _ensure_conversation_embeddings(db)
            await _update_neighbors(db)
            await db.commit()
            logger.info(
                "semantic_indexer.cycle_complete",
                duration_ms=int((time.monotonic() - cycle_started) * 1000),
            )
        except Exception:
            await db.rollback()
            logger.exception(
                "semantic_indexer.cycle_failed",
                duration_ms=int((time.monotonic() - cycle_started) * 1000),
            )


async def semantic_indexer_loop():
    """Background loop."""
    logger.info("semantic_indexer.loop_started", interval=INDEXER_INTERVAL)
    while True:
        await asyncio.sleep(INDEXER_INTERVAL)
        try:
            await run_indexer_cycle()
        except Exception:
            logger.exception("semantic_indexer.loop_error")
