import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.db import get_db
from null_engine.models.schemas import StrataComparisonOut, StratumOut
from null_engine.models.tables import Stratum

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


def _normalize_str_list(values: list | None) -> list[str]:
    if not values:
        return []
    out: list[str] = []
    for value in values:
        text = str(value).strip()
        if text:
            out.append(text)
    return out


@router.get("/worlds/{world_id}/strata/compare", response_model=StrataComparisonOut)
async def compare_strata(
    world_id: uuid.UUID,
    from_epoch: int | None = Query(None, ge=0),
    to_epoch: int | None = Query(None, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Compare two strata snapshots. If omitted, compares the latest two epochs."""
    if (from_epoch is None) != (to_epoch is None):
        raise HTTPException(400, "Provide both from_epoch and to_epoch, or neither")

    if from_epoch is not None and to_epoch is not None:
        if from_epoch == to_epoch:
            raise HTTPException(400, "from_epoch and to_epoch must be different")
        if from_epoch > to_epoch:
            raise HTTPException(400, "from_epoch must be less than to_epoch")

        result = await db.execute(
            select(Stratum).where(
                Stratum.world_id == world_id,
                Stratum.epoch.in_([from_epoch, to_epoch]),
            )
        )
        rows = result.scalars().all()
        by_epoch = {row.epoch: row for row in rows}
        if from_epoch not in by_epoch or to_epoch not in by_epoch:
            raise HTTPException(404, "Stratum comparison target not found")
        older = by_epoch[from_epoch]
        newer = by_epoch[to_epoch]
    else:
        result = await db.execute(
            select(Stratum)
            .where(Stratum.world_id == world_id)
            .order_by(Stratum.epoch.desc())
            .limit(2)
        )
        rows = result.scalars().all()
        if len(rows) < 2:
            raise HTTPException(404, "Not enough strata to compare")
        newer, older = rows[0], rows[1]

    older_themes = set(_normalize_str_list(older.dominant_themes))
    newer_themes = set(_normalize_str_list(newer.dominant_themes))
    older_emerged = set(_normalize_str_list(older.emerged_concepts))
    newer_emerged = set(_normalize_str_list(newer.emerged_concepts))
    older_faded = set(_normalize_str_list(older.faded_concepts))
    newer_faded = set(_normalize_str_list(newer.faded_concepts))

    return {
        "world_id": world_id,
        "from_epoch": older.epoch,
        "to_epoch": newer.epoch,
        "from_summary": older.summary,
        "from_summary_ko": older.summary_ko,
        "to_summary": newer.summary,
        "to_summary_ko": newer.summary_ko,
        "added_themes": sorted(newer_themes - older_themes),
        "removed_themes": sorted(older_themes - newer_themes),
        "persisted_themes": sorted(newer_themes & older_themes),
        "newly_emerged_concepts": sorted(newer_emerged - older_emerged),
        "newly_faded_concepts": sorted(newer_faded - older_faded),
    }


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
