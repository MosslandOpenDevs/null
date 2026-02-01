import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.db import get_db
from null_engine.models.tables import TaxonomyNode, TaxonomyMembership, World
from null_engine.models.schemas import TaxonomyNodeOut, TaxonomyNodeDetail, TaxonomyMembershipOut

router = APIRouter(tags=["taxonomy"])


@router.get("/taxonomy/tree", response_model=list[TaxonomyNodeOut])
async def get_taxonomy_tree(db: AsyncSession = Depends(get_db)):
    """Get all root-level taxonomy nodes."""
    result = await db.execute(
        select(TaxonomyNode)
        .where(TaxonomyNode.parent_id.is_(None))
        .order_by(TaxonomyNode.member_count.desc())
    )
    return result.scalars().all()


@router.get("/taxonomy/tree/{node_id}", response_model=TaxonomyNodeDetail)
async def get_taxonomy_subtree(
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a taxonomy node with its children and members."""
    result = await db.execute(
        select(TaxonomyNode).where(TaxonomyNode.id == node_id)
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(404, "Taxonomy node not found")

    children_result = await db.execute(
        select(TaxonomyNode)
        .where(TaxonomyNode.parent_id == node_id)
        .order_by(TaxonomyNode.member_count.desc())
    )
    children = children_result.scalars().all()

    members_result = await db.execute(
        select(TaxonomyMembership)
        .where(TaxonomyMembership.node_id == node_id)
        .order_by(TaxonomyMembership.similarity.desc())
        .limit(50)
    )
    members = members_result.scalars().all()

    return TaxonomyNodeDetail(
        node=TaxonomyNodeOut.model_validate(node),
        children=[TaxonomyNodeOut.model_validate(c) for c in children],
        members=[TaxonomyMembershipOut.model_validate(m) for m in members],
    )


@router.get("/taxonomy/tree/{node_id}/worlds")
async def get_taxonomy_worlds(
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get worlds that have entities in this taxonomy node."""
    members_result = await db.execute(
        select(TaxonomyMembership.world_id)
        .where(TaxonomyMembership.node_id == node_id)
        .distinct()
    )
    world_ids = [row[0] for row in members_result.all()]

    if not world_ids:
        return []

    worlds_result = await db.execute(
        select(World).where(World.id.in_(world_ids))
    )
    worlds = worlds_result.scalars().all()
    return [
        {
            "id": str(w.id),
            "seed_prompt": w.seed_prompt,
            "status": w.status,
            "current_epoch": w.current_epoch,
        }
        for w in worlds
    ]
