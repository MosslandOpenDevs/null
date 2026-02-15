"""TaxonomyBuilder — automatic bottom-up taxonomy generation.

Periodically clusters world content into a hierarchical taxonomy tree
using embeddings and LLM-based labeling.
"""

import asyncio
import time
import uuid
from collections import defaultdict

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.db import async_session
from null_engine.models.tables import (
    TaxonomyMembership,
    TaxonomyNode,
    WikiPage,
)
from null_engine.services.llm_router import llm_router

logger = structlog.get_logger()

TAXONOMY_INTERVAL = 300  # seconds
CLUSTER_THRESHOLD = 0.72


async def _build_leaf_nodes(db: AsyncSession):
    """Create/update leaf taxonomy nodes from world content clusters."""
    # Get all worlds with wiki pages that have embeddings
    result = await db.execute(
        select(WikiPage)
        .where(WikiPage.embedding.isnot(None))
        .order_by(WikiPage.created_at.desc())
        .limit(500)
    )
    pages = result.scalars().all()
    if not pages:
        return

    # Group pages by world
    by_world: dict[uuid.UUID, list] = defaultdict(list)
    for p in pages:
        by_world[p.world_id].append(p)

    for world_id, world_pages in by_world.items():
        if len(world_pages) < 2:
            continue

        # For each page, check if it already has a taxonomy membership
        for page in world_pages:
            existing = await db.execute(
                select(TaxonomyMembership).where(
                    TaxonomyMembership.entity_id == page.id,
                    TaxonomyMembership.entity_type == "wiki_page",
                )
            )
            if existing.scalar_one_or_none():
                continue

            # Find best matching taxonomy node by similarity
            best_node = None
            best_sim = 0.0

            nodes_result = await db.execute(
                select(TaxonomyNode)
                .where(TaxonomyNode.centroid.isnot(None))
                .order_by(TaxonomyNode.centroid.cosine_distance(page.embedding))
                .limit(1)
            )
            closest_node = nodes_result.scalar_one_or_none()

            if closest_node:
                dist_result = await db.execute(
                    select(
                        TaxonomyNode.centroid.cosine_distance(page.embedding)
                    ).where(TaxonomyNode.id == closest_node.id)
                )
                distance = dist_result.scalar()
                if distance is not None:
                    sim = 1.0 - float(distance)
                    if sim >= CLUSTER_THRESHOLD:
                        best_node = closest_node
                        best_sim = sim

            if best_node:
                db.add(TaxonomyMembership(
                    node_id=best_node.id,
                    world_id=world_id,
                    entity_type="wiki_page",
                    entity_id=page.id,
                    similarity=best_sim,
                ))
                best_node.member_count = (best_node.member_count or 0) + 1
            else:
                # Create a new leaf node
                node = TaxonomyNode(
                    label=page.title[:200],
                    description="",
                    depth=0,
                    path="",
                    centroid=page.embedding,
                    member_count=1,
                )
                db.add(node)
                await db.flush()
                node.path = str(node.id)

                db.add(TaxonomyMembership(
                    node_id=node.id,
                    world_id=world_id,
                    entity_type="wiki_page",
                    entity_id=page.id,
                    similarity=1.0,
                ))

    await db.flush()


async def _merge_similar_nodes(db: AsyncSession):
    """Merge taxonomy nodes that are very similar into parent nodes."""
    result = await db.execute(
        select(TaxonomyNode)
        .where(TaxonomyNode.parent_id.is_(None), TaxonomyNode.centroid.isnot(None))
        .limit(100)
    )
    root_nodes = result.scalars().all()
    if len(root_nodes) < 2:
        return

    merged = set()
    for i, node_a in enumerate(root_nodes):
        if node_a.id in merged:
            continue
        for node_b in root_nodes[i + 1:]:
            if node_b.id in merged:
                continue
            try:
                dist_result = await db.execute(
                    select(
                        TaxonomyNode.centroid.cosine_distance(node_a.centroid)
                    ).where(TaxonomyNode.id == node_b.id)
                )
                distance = dist_result.scalar()
                if distance is not None and (1.0 - float(distance)) >= CLUSTER_THRESHOLD:
                    # Create parent node
                    parent = TaxonomyNode(
                        label=f"{node_a.label} / {node_b.label}"[:200],
                        description="",
                        depth=0,
                        path="",
                        centroid=node_a.centroid,  # Use first node's centroid
                        member_count=(node_a.member_count or 0) + (node_b.member_count or 0),
                    )
                    db.add(parent)
                    await db.flush()
                    parent.path = str(parent.id)

                    node_a.parent_id = parent.id
                    node_a.depth = 1
                    node_a.path = f"{parent.id}/{node_a.id}"

                    node_b.parent_id = parent.id
                    node_b.depth = 1
                    node_b.path = f"{parent.id}/{node_b.id}"

                    merged.add(node_a.id)
                    merged.add(node_b.id)
                    break
            except Exception:
                logger.exception("taxonomy.merge_error")

    await db.flush()


async def _label_nodes(db: AsyncSession):
    """Use LLM to generate labels for unlabeled taxonomy nodes."""
    result = await db.execute(
        select(TaxonomyNode).where(TaxonomyNode.description == "").limit(5)
    )
    nodes = result.scalars().all()

    for node in nodes:
        members_result = await db.execute(
            select(TaxonomyMembership)
            .where(TaxonomyMembership.node_id == node.id)
            .limit(10)
        )
        members = members_result.scalars().all()

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
                prompt=f"""These wiki pages belong to the same category:
{chr(10).join(f'- {t}' for t in titles)}

Generate a short label (3-5 words) and 1-sentence description for this category.
Return JSON: {{"label": "...", "description": "..."}}""",
                max_tokens=256,
            )
            if isinstance(result_json, dict):
                node.label = str(result_json.get("label", node.label))[:200]
                node.description = str(result_json.get("description", ""))
        except Exception:
            logger.exception("taxonomy.label_failed", node_id=str(node.id))


async def run_taxonomy_cycle():
    """Single taxonomy building cycle."""
    cycle_started = time.monotonic()
    async with async_session() as db:
        try:
            await _build_leaf_nodes(db)
            await _merge_similar_nodes(db)
            await _label_nodes(db)
            await db.commit()
            logger.info(
                "taxonomy_builder.cycle_complete",
                duration_ms=int((time.monotonic() - cycle_started) * 1000),
            )
        except Exception:
            await db.rollback()
            logger.exception(
                "taxonomy_builder.cycle_failed",
                duration_ms=int((time.monotonic() - cycle_started) * 1000),
            )


async def taxonomy_builder_loop():
    """Background loop."""
    logger.info("taxonomy_builder.loop_started", interval=TAXONOMY_INTERVAL)
    while True:
        await asyncio.sleep(TAXONOMY_INTERVAL)
        try:
            await run_taxonomy_cycle()
        except Exception:
            logger.exception("taxonomy_builder.loop_error")
