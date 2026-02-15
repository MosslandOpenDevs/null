import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.db import get_db
from null_engine.models.schemas import (
    EntityGraphEdge,
    EntityGraphNode,
    EntityGraphOut,
    EntityMentionOut,
    SemanticNeighborOut,
)
from null_engine.models.tables import (
    Agent,
    EntityMention,
    KnowledgeEdge,
    SemanticNeighbor,
    WikiPage,
)

router = APIRouter(tags=["entities"])


@router.get(
    "/worlds/{world_id}/entities/{entity_type}/{entity_id}/mentions",
    response_model=list[EntityMentionOut],
)
async def get_entity_mentions(
    world_id: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all mentions of this entity (places that reference it)."""
    result = await db.execute(
        select(EntityMention).where(
            EntityMention.world_id == world_id,
            EntityMention.target_type == entity_type,
            EntityMention.target_id == entity_id,
        ).order_by(EntityMention.created_at.desc())
    )
    return result.scalars().all()


@router.get(
    "/worlds/{world_id}/entities/{entity_type}/{entity_id}/neighbors",
    response_model=list[SemanticNeighborOut],
)
async def get_entity_neighbors(
    world_id: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get semantic neighbors of this entity."""
    result = await db.execute(
        select(SemanticNeighbor).where(
            or_(
                (SemanticNeighbor.entity_a_id == entity_id),
                (SemanticNeighbor.entity_b_id == entity_id),
            )
        ).order_by(SemanticNeighbor.similarity.desc()).limit(20)
    )
    return result.scalars().all()


@router.get(
    "/worlds/{world_id}/entity-graph",
    response_model=EntityGraphOut,
)
async def get_entity_graph(
    world_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get the full entity graph for a world (agents + wiki + mentions + knowledge edges)."""
    nodes: list[EntityGraphNode] = []
    edges: list[EntityGraphEdge] = []
    seen_nodes: set[str] = set()

    # Add agents as nodes
    agents_result = await db.execute(
        select(Agent).where(Agent.world_id == world_id)
    )
    for agent in agents_result.scalars().all():
        key = str(agent.id)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(EntityGraphNode(id=agent.id, type="agent", label=agent.name))

    # Add wiki pages as nodes
    wiki_result = await db.execute(
        select(WikiPage).where(WikiPage.world_id == world_id)
    )
    for page in wiki_result.scalars().all():
        key = str(page.id)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(EntityGraphNode(id=page.id, type="wiki_page", label=page.title))

    # Add mention-based edges
    mentions_result = await db.execute(
        select(EntityMention).where(EntityMention.world_id == world_id)
    )
    for mention in mentions_result.scalars().all():
        edges.append(EntityGraphEdge(
            source_id=mention.source_id,
            target_id=mention.target_id,
            type="mention",
            weight=mention.confidence,
        ))

    # Add knowledge edges
    kg_result = await db.execute(
        select(KnowledgeEdge).where(KnowledgeEdge.world_id == world_id)
    )
    for edge in kg_result.scalars().all():
        # Knowledge edges use string subjects, so we map them to wiki page IDs if possible
        # For now, skip — they're already in the graph tab via knowledgeEdges
        pass

    return EntityGraphOut(nodes=nodes, edges=edges)
