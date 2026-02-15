import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.db import get_db
from null_engine.models.schemas import (
    ClusterDetailOut,
    ClusterMemberOut,
    ClusterOut,
    GlobalSearchResult,
    ResonanceLinkOut,
    WorldNeighborOut,
    WorldsSimilarityMapOut,
)
from null_engine.models.tables import (
    Agent,
    ConceptCluster,
    ConceptMembership,
    ResonanceLink,
    WikiPage,
    World,
)

router = APIRouter(prefix="/multiverse", tags=["multiverse"])


def _unordered_pair(a: uuid.UUID, b: uuid.UUID) -> tuple[uuid.UUID, uuid.UUID]:
    """Normalize a world pair key so A-B and B-A are aggregated together."""
    first, second = sorted((a, b), key=lambda item: str(item))
    return first, second


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


@router.get("/worlds/map", response_model=WorldsSimilarityMapOut)
async def worlds_similarity_map(
    min_strength: float = Query(0.0, ge=0.0, le=1.0),
    min_count: int = Query(1, ge=1, le=1000),
    link_limit: int = Query(200, ge=1, le=1000),
    world_limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Return deduplicated world pairs with resonance strength for visualization."""
    result = await db.execute(
        select(
            ResonanceLink.world_a,
            ResonanceLink.world_b,
            ResonanceLink.strength,
        )
        .where(ResonanceLink.strength >= min_strength)
        .order_by(ResonanceLink.strength.desc())
        .limit(5000)
    )
    rows = result.all()

    pair_metrics: dict[tuple[uuid.UUID, uuid.UUID], dict[str, float | int]] = {}
    for row in rows:
        pair_key = _unordered_pair(row.world_a, row.world_b)
        if pair_key not in pair_metrics:
            pair_metrics[pair_key] = {"strength_sum": 0.0, "count": 0}
        pair_metrics[pair_key]["strength_sum"] = float(pair_metrics[pair_key]["strength_sum"]) + float(row.strength)
        pair_metrics[pair_key]["count"] = int(pair_metrics[pair_key]["count"]) + 1

    links = []
    for (world_a, world_b), metrics in pair_metrics.items():
        count = int(metrics["count"])
        avg_strength = float(metrics["strength_sum"]) / count
        if count < min_count or avg_strength < min_strength:
            continue
        links.append(
            {
                "world_a": str(world_a),
                "world_b": str(world_b),
                "strength": avg_strength,
                "count": count,
            }
        )

    links.sort(key=lambda item: (item["strength"], item["count"]), reverse=True)
    links = links[:link_limit]

    linked_world_ids = {
        uuid.UUID(link["world_a"]) for link in links
    } | {
        uuid.UUID(link["world_b"]) for link in links
    }

    if linked_world_ids:
        worlds_result = await db.execute(
            select(World)
            .where(World.id.in_(linked_world_ids))
            .order_by(World.created_at.desc())
            .limit(world_limit)
        )
    else:
        worlds_result = await db.execute(select(World).order_by(World.created_at.desc()).limit(world_limit))

    worlds = [
        {
            "id": str(w.id),
            "seed_prompt": w.seed_prompt[:80],
            "status": w.status,
            "description": (w.config or {}).get("description", "")[:100],
        }
        for w in worlds_result.scalars().all()
    ]

    return {"worlds": worlds, "links": links}


@router.get("/worlds/{world_id}/neighbors", response_model=list[WorldNeighborOut])
async def world_neighbors(
    world_id: uuid.UUID,
    limit: int = Query(10, ge=1, le=100),
    min_strength: float = Query(0.0, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
):
    """Return top neighboring worlds by aggregated resonance strength."""
    result = await db.execute(
        select(
            ResonanceLink.world_a,
            ResonanceLink.world_b,
            ResonanceLink.strength,
        )
        .where(
            or_(
                ResonanceLink.world_a == world_id,
                ResonanceLink.world_b == world_id,
            )
        )
        .order_by(ResonanceLink.strength.desc())
        .limit(5000)
    )
    rows = result.all()

    neighbor_metrics: dict[uuid.UUID, dict[str, float | int]] = {}
    for row in rows:
        neighbor_id = row.world_b if row.world_a == world_id else row.world_a
        if neighbor_id not in neighbor_metrics:
            neighbor_metrics[neighbor_id] = {"strength_sum": 0.0, "count": 0}
        neighbor_metrics[neighbor_id]["strength_sum"] = (
            float(neighbor_metrics[neighbor_id]["strength_sum"]) + float(row.strength)
        )
        neighbor_metrics[neighbor_id]["count"] = int(neighbor_metrics[neighbor_id]["count"]) + 1

    ranked: list[tuple[uuid.UUID, float, int]] = []
    for neighbor_id, metrics in neighbor_metrics.items():
        count = int(metrics["count"])
        avg_strength = float(metrics["strength_sum"]) / count
        if avg_strength < min_strength:
            continue
        ranked.append((neighbor_id, avg_strength, count))

    if not ranked:
        return []

    ranked.sort(key=lambda item: (item[1], item[2]), reverse=True)
    ranked = ranked[:limit]

    neighbor_ids = [neighbor_id for neighbor_id, _avg, _count in ranked]
    worlds_result = await db.execute(select(World).where(World.id.in_(neighbor_ids)))
    worlds_by_id = {world.id: world for world in worlds_result.scalars().all()}

    out: list[WorldNeighborOut] = []
    for neighbor_id, avg_strength, count in ranked:
        world = worlds_by_id.get(neighbor_id)
        if not world:
            continue
        out.append(
            WorldNeighborOut(
                world_id=neighbor_id,
                seed_prompt=world.seed_prompt,
                status=world.status,
                strength=avg_strength,
                resonance_count=count,
            )
        )
    return out
