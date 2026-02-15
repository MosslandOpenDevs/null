from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.api.routes import worlds as worlds_route
from null_engine.config import settings
from null_engine.db import get_db
from null_engine.models.schemas import (
    OpsAlertOut,
    OpsLoopOut,
    OpsMetricsOut,
    OpsQueueOut,
    OpsRunnerOut,
    OpsWorldStatusOut,
)
from null_engine.models.tables import Conversation, Stratum, WikiPage, World
from null_engine.services.runtime_metrics import (
    get_loop_metrics_snapshot,
    get_runner_metrics_snapshot,
    merge_metric_defaults,
)

router = APIRouter(prefix="/ops", tags=["ops"])


def _build_alerts(
    *,
    world_status_counts: dict[str, int],
    loops: list[dict[str, Any]],
    runners: list[dict[str, Any]],
    queue_data: dict[str, int],
    active_runners: int,
) -> list[OpsAlertOut]:
    alerts: list[OpsAlertOut] = []

    for loop in loops:
        if loop["status"] == "error":
            alerts.append(
                OpsAlertOut(
                    code="loop_error",
                    severity="critical",
                    message=f"Background loop `{loop['name']}` is in error state",
                    context={
                        "loop": loop["name"],
                        "restart_count": loop["restart_count"],
                        "last_error": loop.get("last_error"),
                    },
                )
            )
        elif loop["status"] == "exited":
            alerts.append(
                OpsAlertOut(
                    code="loop_exited",
                    severity="warning",
                    message=f"Background loop `{loop['name']}` exited and is restarting",
                    context={"loop": loop["name"], "restart_count": loop["restart_count"]},
                )
            )

    for runner in runners:
        if (
            runner["ticks_total"] >= settings.ops_runner_ticks_min_for_alert
            and runner["success_rate"] < settings.ops_runner_success_rate_threshold
        ):
            alerts.append(
                OpsAlertOut(
                    code="runner_degraded",
                    severity="warning",
                    message=f"Runner {str(runner['world_id'])[:8]} has low tick success rate",
                    context={
                        "world_id": str(runner["world_id"]),
                        "success_rate": runner["success_rate"],
                        "tick_failures": runner["tick_failures"],
                        "ticks_total": runner["ticks_total"],
                    },
                )
            )

    pending_total = (
        queue_data["translator_pending_conversations"]
        + queue_data["translator_pending_wiki_pages"]
        + queue_data["translator_pending_strata"]
    )
    if pending_total >= settings.ops_translator_backlog_threshold:
        alerts.append(
            OpsAlertOut(
                code="translator_backlog",
                severity="warning",
                message="Translation queue backlog is high",
                context={"pending_total": pending_total, **queue_data},
            )
        )

    if queue_data["generating_worlds"] >= settings.ops_generating_worlds_threshold:
        alerts.append(
            OpsAlertOut(
                code="genesis_backlog",
                severity="warning",
                message="Too many worlds are stuck in `generating` state",
                context={"generating_worlds": queue_data["generating_worlds"]},
            )
        )

    running_worlds = world_status_counts.get("running", 0)
    if running_worlds > 0 and active_runners == 0:
        alerts.append(
            OpsAlertOut(
                code="runner_mismatch",
                severity="warning",
                message="Running worlds exist but no active in-memory runners were found",
                context={"running_worlds": running_worlds, "active_runners": active_runners},
            )
        )

    return alerts


async def _build_ops_snapshot(db: AsyncSession) -> OpsMetricsOut:
    status_result = await db.execute(
        select(World.status, func.count()).group_by(World.status)
    )
    world_status_rows = status_result.all()
    world_statuses = [OpsWorldStatusOut(status=row[0], count=row[1]) for row in world_status_rows]
    world_status_counts = {row[0]: int(row[1]) for row in world_status_rows}

    generating_worlds_result = await db.execute(
        select(func.count()).select_from(World).where(World.status == "generating")
    )
    pending_conversations_result = await db.execute(
        select(func.count())
        .select_from(Conversation)
        .where(Conversation.topic_ko.is_(None))
        .where(Conversation.topic != "")
    )
    pending_wiki_result = await db.execute(
        select(func.count())
        .select_from(WikiPage)
        .where(WikiPage.title_ko.is_(None))
        .where(WikiPage.title != "")
    )
    pending_strata_result = await db.execute(
        select(func.count())
        .select_from(Stratum)
        .where(Stratum.summary_ko.is_(None))
        .where(Stratum.summary != "")
    )

    queue_data = {
        "translator_pending_conversations": int(pending_conversations_result.scalar() or 0),
        "translator_pending_wiki_pages": int(pending_wiki_result.scalar() or 0),
        "translator_pending_strata": int(pending_strata_result.scalar() or 0),
        "generating_worlds": int(generating_worlds_result.scalar() or 0),
    }

    loop_defaults = {
        "status": "unknown",
        "restart_count": 0,
        "last_started_at": None,
        "last_error_at": None,
        "last_error": None,
    }
    loops = [
        OpsLoopOut.model_validate(merge_metric_defaults(loop, loop_defaults))
        for loop in get_loop_metrics_snapshot()
    ]
    loops.sort(key=lambda loop: loop.name)

    runner_defaults = {
        "status": "unknown",
        "ticks_total": 0,
        "tick_failures": 0,
        "success_rate": 1.0,
        "last_duration_ms": None,
        "avg_duration_ms": None,
        "last_tick_delay_ms": None,
        "last_seen_at": None,
    }
    runners = [
        OpsRunnerOut.model_validate(merge_metric_defaults(runner, runner_defaults))
        for runner in get_runner_metrics_snapshot()
    ]
    runners.sort(key=lambda runner: runner.world_id.hex)

    active_runners = sum(1 for runner in worlds_route._runners.values() if runner.running)

    alerts = _build_alerts(
        world_status_counts=world_status_counts,
        loops=[loop.model_dump() for loop in loops],
        runners=[runner.model_dump() for runner in runners],
        queue_data=queue_data,
        active_runners=active_runners,
    )

    return OpsMetricsOut(
        generated_at=datetime.now(UTC),
        worlds=world_statuses,
        active_runners=active_runners,
        loops=loops,
        runners=runners,
        queues=OpsQueueOut(**queue_data),
        alerts=alerts,
    )


@router.get("/metrics", response_model=OpsMetricsOut)
async def get_ops_metrics(db: AsyncSession = Depends(get_db)):
    return await _build_ops_snapshot(db)


@router.get("/alerts", response_model=list[OpsAlertOut])
async def get_ops_alerts(db: AsyncSession = Depends(get_db)):
    metrics = await _build_ops_snapshot(db)
    return metrics.alerts
