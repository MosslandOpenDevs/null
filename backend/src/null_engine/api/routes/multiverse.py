import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.db import get_db
from null_engine.models.tables import (
    ConceptCluster, ConceptMembership, ResonanceLink,
    WikiPage, Agent, World,
)
from null_engine.models.schemas import (
    ClusterOut, ClusterDetailOut, ClusterMemberOut,
    ResonanceLinkOut, GlobalSearchResult,
)

router = APIRouter(prefix="/multiverse", tags=["multiverse"])


@router.get("/clusters", response_model=list[ClusterOut])
async def list_clusters(
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ConceptCluster)
        .order_by(ConceptCluster.member_count.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/clusters/{cluster_id}", response_model=ClusterDetailOut)
async def get_cluster(cluster_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ConceptCluster).where(ConceptCluster.id == cluster_id)
    )
    cluster = result.scalar_one_or_none()
    if not cluster:
        from fastapi import HTTPException
        raise HTTPException(404, "Cluster not found")

    members_result = await db.execute(
        select(ConceptMembership)
        .where(ConceptMembership.cluster_id == cluster_id)
        .order_by(ConceptMembership.similarity.desc())
        .limit(100)
    )
    members = members_result.scalars().all()

    return ClusterDetailOut(
        cluster=ClusterOut.model_validate(cluster),
        members=[ClusterMemberOut.model_validate(m) for m in members],
    )


@router.get("/resonance", response_model=list[ResonanceLinkOut])
async def get_resonance(
    world_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ResonanceLink).where(
            or_(
                ResonanceLink.world_a == world_id,
                ResonanceLink.world_b == world_id,
            )
        ).order_by(ResonanceLink.strength.desc()).limit(50)
    )
    return result.scalars().all()


@router.get("/search", response_model=list[GlobalSearchResult])
async def global_search(
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    """Search across all worlds by text matching. Vector search when embeddings available."""
    pattern = f"%{q}%"
    results: list[GlobalSearchResult] = []

    # Search wiki pages
    wiki_result = await db.execute(
        select(WikiPage)
        .where(or_(WikiPage.title.ilike(pattern), WikiPage.content.ilike(pattern)))
        .limit(10)
    )
    for p in wiki_result.scalars().all():
        title_match = q.lower() in p.title.lower()
        results.append(GlobalSearchResult(
            entity_type="wiki_page",
            entity_id=p.id,
            world_id=p.world_id,
            title=p.title,
            snippet=p.content[:150],
            score=1.0 if title_match else 0.5,
        ))

    # Search agents
    agent_result = await db.execute(
        select(Agent).where(Agent.name.ilike(pattern)).limit(10)
    )
    for a in agent_result.scalars().all():
        results.append(GlobalSearchResult(
            entity_type="agent",
            entity_id=a.id,
            world_id=a.world_id,
            title=a.name,
            snippet=str(a.persona.get("role", "")),
            score=0.8,
        ))

    results.sort(key=lambda r: r.score, reverse=True)
    return results[:20]


@router.get("/worlds/map")
async def worlds_similarity_map(db: AsyncSession = Depends(get_db)):
    """Return world pairs with resonance strength for visualization."""
    result = await db.execute(
        select(
            ResonanceLink.world_a,
            ResonanceLink.world_b,
            func.avg(ResonanceLink.strength).label("avg_strength"),
            func.count().label("link_count"),
        )
        .group_by(ResonanceLink.world_a, ResonanceLink.world_b)
    )
    rows = result.all()

    # Also return all worlds for the map
    worlds_result = await db.execute(select(World).order_by(World.created_at.desc()).limit(50))
    worlds = [
        {
            "id": str(w.id),
            "seed_prompt": w.seed_prompt[:80],
            "status": w.status,
            "description": (w.config or {}).get("description", "")[:100],
        }
        for w in worlds_result.scalars().all()
    ]

    links = [
        {
            "world_a": str(r.world_a),
            "world_b": str(r.world_b),
            "strength": float(r.avg_strength),
            "count": r.link_count,
        }
        for r in rows
    ]

    return {"worlds": worlds, "links": links}
