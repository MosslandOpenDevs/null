"""StratumDetector — generates temporal strata summaries at epoch boundaries.

When an epoch ends, summarizes what concepts emerged, faded, and dominated.
"""

import uuid

import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.models.tables import (
    Conversation, WikiPage, KnowledgeEdge, Stratum,
)
from null_engine.services.llm_router import llm_router

logger = structlog.get_logger()


async def detect_stratum(
    db: AsyncSession,
    world_id: uuid.UUID,
    epoch: int,
):
    """Generate a stratum summary for the completed epoch."""
    # Check if stratum already exists
    existing = await db.execute(
        select(Stratum).where(
            Stratum.world_id == world_id,
            Stratum.epoch == epoch,
        )
    )
    if existing.scalar_one_or_none():
        return

    # Gather epoch data
    convs = (await db.execute(
        select(Conversation).where(
            Conversation.world_id == world_id,
            Conversation.epoch == epoch,
        )
    )).scalars().all()

    # Gather wiki pages updated during this epoch (approximate by recent)
    wiki_pages = (await db.execute(
        select(WikiPage).where(WikiPage.world_id == world_id)
    )).scalars().all()

    # Gather knowledge edges
    edges = (await db.execute(
        select(KnowledgeEdge).where(KnowledgeEdge.world_id == world_id)
    )).scalars().all()

    # Build context for LLM
    conv_summaries = [c.summary for c in convs if c.summary][:10]
    wiki_titles = [p.title for p in wiki_pages][:20]
    edge_triples = [f"{e.subject} -> {e.predicate} -> {e.object}" for e in edges][:20]

    # Get previous stratum for comparison
    prev_stratum = None
    if epoch > 0:
        prev_result = await db.execute(
            select(Stratum).where(
                Stratum.world_id == world_id,
                Stratum.epoch == epoch - 1,
            )
        )
        prev_stratum = prev_result.scalar_one_or_none()

    prev_context = ""
    if prev_stratum:
        prev_context = f"""
Previous epoch themes: {prev_stratum.dominant_themes}
Previous emerged concepts: {prev_stratum.emerged_concepts}
"""

    prompt = f"""Analyze this epoch (epoch {epoch}) of a simulated world.

Conversations this epoch:
{chr(10).join(f'- {s}' for s in conv_summaries)}

Wiki pages in this world:
{chr(10).join(f'- {t}' for t in wiki_titles)}

Knowledge graph edges:
{chr(10).join(f'- {e}' for e in edge_triples)}

{prev_context}

Generate a JSON summary:
{{
  "summary": "1-2 sentence summary of this epoch",
  "emerged_concepts": ["new concepts/themes that appeared"],
  "faded_concepts": ["concepts that became less prominent"],
  "dominant_themes": ["top 3-5 dominant themes"]
}}"""

    try:
        result = await llm_router.generate_json(
            role="reaction_agent",
            prompt=prompt,
            max_tokens=512,
        )
        if not isinstance(result, dict):
            result = {}

        # Get embedding for the summary
        from null_engine.services.convergence import _get_embedding
        summary_text = result.get("summary", f"Epoch {epoch} summary")
        embedding = await _get_embedding(summary_text)

        stratum = Stratum(
            world_id=world_id,
            epoch=epoch,
            summary=str(result.get("summary", "")),
            emerged_concepts=result.get("emerged_concepts", []),
            faded_concepts=result.get("faded_concepts", []),
            dominant_themes=result.get("dominant_themes", []),
            embedding=embedding,
        )
        db.add(stratum)
        await db.flush()
        logger.info("stratum_detector.created", world_id=str(world_id), epoch=epoch)

    except Exception:
        logger.exception("stratum_detector.failed", world_id=str(world_id), epoch=epoch)
