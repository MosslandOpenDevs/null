"""Convergence Detector — background service for cross-world intelligence.

Periodically:
1. Ensures WikiPage embeddings exist
2. Finds cross-world nearest neighbors via pgvector
3. Clusters similar content into ConceptClusters
4. Creates ResonanceLinks between worlds
5. Labels clusters via LLM
"""

import asyncio
import time

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.db import async_session
from null_engine.models.tables import (
    ConceptCluster,
    ConceptMembership,
    ResonanceLink,
    WikiPage,
)
from null_engine.services.llm_router import llm_router

logger = structlog.get_logger()

SIMILARITY_THRESHOLD = 0.78
CLUSTER_MIN_MEMBERS = 2
CONVERGENCE_INTERVAL = 120  # seconds


async def _ensure_embeddings(db: AsyncSession):
    """Generate embeddings for wiki pages that don't have them."""
    result = await db.execute(
        select(WikiPage).where(WikiPage.embedding.is_(None)).limit(50)
    )
    pages = result.scalars().all()
    if not pages:
        return

    for page in pages:
        try:
            embed_text = f"{page.title}\n{page.content[:2000]}"
            embedding = await _get_embedding(embed_text)
            if embedding:
                page.embedding = embedding
        except Exception:
            logger.exception("convergence.embed_failed", page_id=str(page.id))

    await db.flush()
    logger.info("convergence.embeddings_generated", count=len(pages))


async def _get_embedding(text: str) -> list[float] | None:
    """Get embedding via OpenAI or return None if unavailable."""
    try:
        from null_engine.config import settings
        if settings.llm_provider == "ollama":
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{settings.ollama_base_url}/api/embeddings",
                    json={"model": "nomic-embed-text", "prompt": text[:2000]},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    emb = data.get("embedding")
                    if emb and len(emb) == 1536:
                        return emb
            return None

        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        resp = await client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000],
        )
        return resp.data[0].embedding
    except Exception:
        logger.exception("convergence.embedding_error")
        return None


async def _find_cross_world_neighbors(db: AsyncSession):
    """Use pgvector to find similar wiki pages across different worlds."""
    # Get all pages with embeddings
    result = await db.execute(
        select(WikiPage)
        .where(WikiPage.embedding.isnot(None))
        .order_by(WikiPage.created_at.desc())
        .limit(500)
    )
    pages = result.scalars().all()
    if len(pages) < 2:
        return []

    pairs = []
    # For each page, find nearest neighbors in OTHER worlds
    for page in pages:
        try:
            neighbor_result = await db.execute(
                select(WikiPage)
                .where(
                    WikiPage.world_id != page.world_id,
                    WikiPage.embedding.isnot(None),
                )
                .order_by(WikiPage.embedding.cosine_distance(page.embedding))
                .limit(3)
            )
            neighbors = neighbor_result.scalars().all()
            for neighbor in neighbors:
                # Calculate similarity (1 - distance)
                dist_result = await db.execute(
                    select(
                        WikiPage.embedding.cosine_distance(page.embedding)
                    ).where(WikiPage.id == neighbor.id)
                )
                distance = dist_result.scalar()
                if distance is not None:
                    similarity = 1.0 - float(distance)
                    if similarity >= SIMILARITY_THRESHOLD:
                        pairs.append((page, neighbor, similarity))
        except Exception:
            logger.exception("convergence.neighbor_search_failed", page_id=str(page.id))

    return pairs


async def _update_clusters(db: AsyncSession, pairs: list):
    """Group similar pairs into concept clusters."""
    if not pairs:
        return

    # Simple approach: create/update clusters from pairs
    for page_a, page_b, similarity in pairs:
        # Check if either page is already in a cluster
        existing = await db.execute(
            select(ConceptMembership).where(
                ConceptMembership.entity_id.in_([page_a.id, page_b.id])
            )
        )
        memberships = existing.scalars().all()

        if memberships:
            cluster_id = memberships[0].cluster_id
        else:
            # Create new cluster
            label = f"{page_a.title} / {page_b.title}"
            cluster = ConceptCluster(
                label=label[:200],
                description="",
                member_count=0,
            )
            db.add(cluster)
            await db.flush()
            cluster_id = cluster.id

        # Add memberships if not existing
        for page in [page_a, page_b]:
            check = await db.execute(
                select(ConceptMembership).where(
                    ConceptMembership.cluster_id == cluster_id,
                    ConceptMembership.entity_id == page.id,
                )
            )
            if not check.scalar_one_or_none():
                db.add(ConceptMembership(
                    cluster_id=cluster_id,
                    world_id=page.world_id,
                    entity_type="wiki_page",
                    entity_id=page.id,
                    similarity=similarity,
                ))

        # Create resonance link
        if page_a.world_id != page_b.world_id:
            check = await db.execute(
                select(ResonanceLink).where(
                    ResonanceLink.entity_a == page_a.id,
                    ResonanceLink.entity_b == page_b.id,
                )
            )
            if not check.scalar_one_or_none():
                db.add(ResonanceLink(
                    cluster_id=cluster_id,
                    world_a=page_a.world_id,
                    world_b=page_b.world_id,
                    entity_a=page_a.id,
                    entity_b=page_b.id,
                    entity_type="wiki_page",
                    strength=similarity,
                ))

    # Update member counts
    clusters_result = await db.execute(select(ConceptCluster))
    for cluster in clusters_result.scalars().all():
        count_result = await db.execute(
            select(func.count())
            .select_from(ConceptMembership)
            .where(ConceptMembership.cluster_id == cluster.id)
        )
        cluster.member_count = count_result.scalar() or 0

    await db.flush()


async def _label_clusters(db: AsyncSession):
    """Use LLM to generate better labels for unlabeled clusters."""
    result = await db.execute(
        select(ConceptCluster).where(ConceptCluster.description == "").limit(5)
    )
    clusters = result.scalars().all()

    for cluster in clusters:
        members_result = await db.execute(
            select(ConceptMembership)
            .where(ConceptMembership.cluster_id == cluster.id)
            .limit(10)
        )
        members = members_result.scalars().all()

        # Gather entity titles
        titles = []
        for m in members:
            if m.entity_type == "wiki_page":
                page_result = await db.execute(
                    select(WikiPage.title, WikiPage.content)
                    .where(WikiPage.id == m.entity_id)
                )
                row = page_result.first()
                if row:
                    titles.append(f"{row.title}: {row.content[:100]}")

        if not titles:
            continue

        try:
            result_json = await llm_router.generate_json(
                role="reaction_agent",
                prompt=f"""These wiki pages from different worlds share similar concepts:
{chr(10).join(f'- {t}' for t in titles)}

Generate a short label (3-5 words) and 1-sentence description for this concept cluster.
Return JSON: {{"label": "...", "description": "..."}}""",
                max_tokens=256,
            )
            if isinstance(result_json, dict):
                cluster.label = str(result_json.get("label", cluster.label))[:200]
                cluster.description = str(result_json.get("description", ""))
        except Exception:
            logger.exception("convergence.label_failed", cluster_id=str(cluster.id))


async def run_convergence_cycle():
    """Single convergence detection cycle."""
    cycle_started = time.monotonic()
    async with async_session() as db:
        try:
            await _ensure_embeddings(db)
            pairs = await _find_cross_world_neighbors(db)
            await _update_clusters(db, pairs)
            await _label_clusters(db)
            await db.commit()
            logger.info(
                "convergence.cycle_complete",
                pairs=len(pairs),
                duration_ms=int((time.monotonic() - cycle_started) * 1000),
            )
        except Exception:
            await db.rollback()
            logger.exception(
                "convergence.cycle_failed",
                duration_ms=int((time.monotonic() - cycle_started) * 1000),
            )


async def convergence_loop():
    """Background loop that runs convergence detection periodically."""
    logger.info("convergence.loop_started", interval=CONVERGENCE_INTERVAL)
    while True:
        await asyncio.sleep(CONVERGENCE_INTERVAL)
        try:
            await run_convergence_cycle()
        except Exception:
            logger.exception("convergence.loop_error")
