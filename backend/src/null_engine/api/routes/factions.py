import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.db import get_db
from null_engine.models.tables import Faction, Agent, Relationship
from null_engine.models.schemas import FactionOut

router = APIRouter(tags=["factions"])


@router.get("/worlds/{world_id}/factions")
async def list_factions(world_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Faction).where(Faction.world_id == world_id)
    )
    factions = result.scalars().all()

    out = []
    for f in factions:
        count_result = await db.execute(
            select(func.count(Agent.id)).where(Agent.faction_id == f.id)
        )
        agent_count = count_result.scalar() or 0
        out.append({
            "id": str(f.id),
            "world_id": str(f.world_id),
            "name": f.name,
            "description": f.description,
            "color": f.color,
            "agent_count": agent_count,
        })
    return out


@router.get("/worlds/{world_id}/relationships")
async def list_relationships(world_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Relationship).where(Relationship.world_id == world_id)
    )
    rels = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "agent_a": str(r.agent_a),
            "agent_b": str(r.agent_b),
            "type": r.type,
            "strength": r.strength,
        }
        for r in rels
    ]
