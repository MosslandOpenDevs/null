import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.db import get_db
from null_engine.models.tables import Stratum
from null_engine.models.schemas import StratumOut

router = APIRouter(tags=["strata"])


@router.get("/worlds/{world_id}/strata", response_model=list[StratumOut])
async def get_strata(
    world_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all temporal strata for a world."""
    result = await db.execute(
        select(Stratum)
        .where(Stratum.world_id == world_id)
        .order_by(Stratum.epoch.desc())
    )
    return result.scalars().all()


@router.get("/worlds/{world_id}/strata/{epoch}", response_model=StratumOut)
async def get_stratum(
    world_id: uuid.UUID,
    epoch: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific stratum by epoch."""
    result = await db.execute(
        select(Stratum).where(
            Stratum.world_id == world_id,
            Stratum.epoch == epoch,
        )
    )
    stratum = result.scalar_one_or_none()
    if not stratum:
        raise HTTPException(404, "Stratum not found")
    return stratum
