from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from threading import Lock
from typing import Any

_lock = Lock()
_loop_metrics: dict[str, dict[str, Any]] = {}
_runner_metrics: dict[uuid.UUID, dict[str, Any]] = {}


def _now() -> datetime:
    return datetime.now(UTC)


def note_loop_started(name: str) -> None:
    with _lock:
        metric = _loop_metrics.setdefault(
            name,
            {
                "name": name,
                "status": "running",
                "restart_count": 0,
                "last_started_at": None,
                "last_error_at": None,
                "last_error": None,
            },
        )
        metric["status"] = "running"
        metric["last_started_at"] = _now()


def note_loop_exited(name: str) -> None:
    with _lock:
        metric = _loop_metrics.setdefault(
            name,
            {
                "name": name,
                "status": "exited",
                "restart_count": 0,
                "last_started_at": None,
                "last_error_at": None,
                "last_error": None,
            },
        )
        metric["status"] = "exited"
        metric["restart_count"] = int(metric["restart_count"]) + 1


def note_loop_cancelled(name: str) -> None:
    with _lock:
        metric = _loop_metrics.setdefault(
            name,
            {
                "name": name,
                "status": "cancelled",
                "restart_count": 0,
                "last_started_at": None,
                "last_error_at": None,
                "last_error": None,
            },
        )
        metric["status"] = "cancelled"


def note_loop_error(name: str, error: str) -> None:
    with _lock:
        metric = _loop_metrics.setdefault(
            name,
            {
                "name": name,
                "status": "error",
                "restart_count": 0,
                "last_started_at": None,
                "last_error_at": None,
                "last_error": None,
            },
        )
        metric["status"] = "error"
        metric["restart_count"] = int(metric["restart_count"]) + 1
        metric["last_error_at"] = _now()
        metric["last_error"] = error[:400]


def note_runner_status(world_id: uuid.UUID, status: str) -> None:
    with _lock:
        metric = _runner_metrics.setdefault(
            world_id,
            {
                "world_id": world_id,
                "status": status,
                "ticks_total": 0,
                "tick_failures": 0,
                "success_rate": 1.0,
                "last_duration_ms": None,
                "avg_duration_ms": None,
                "last_tick_delay_ms": None,
                "last_seen_at": None,
            },
        )
        metric["status"] = status
        metric["last_seen_at"] = _now()


def note_runner_tick(
    *,
    world_id: uuid.UUID,
    tick_ok: bool,
    ticks_total: int,
    tick_failures: int,
    success_rate: float,
    duration_ms: int,
    tick_delay_ms: int,
) -> None:
    with _lock:
        metric = _runner_metrics.setdefault(
            world_id,
            {
                "world_id": world_id,
                "status": "running",
                "ticks_total": 0,
                "tick_failures": 0,
                "success_rate": 1.0,
                "last_duration_ms": None,
                "avg_duration_ms": None,
                "last_tick_delay_ms": None,
                "last_seen_at": None,
            },
        )

        previous_total = int(metric["ticks_total"])
        previous_avg = metric["avg_duration_ms"]
        metric["status"] = "running" if tick_ok else "degraded"
        metric["ticks_total"] = ticks_total
        metric["tick_failures"] = tick_failures
        metric["success_rate"] = round(success_rate, 3)
        metric["last_duration_ms"] = duration_ms
        metric["last_tick_delay_ms"] = tick_delay_ms
        metric["last_seen_at"] = _now()

        if previous_total <= 0 or previous_avg is None:
            metric["avg_duration_ms"] = float(duration_ms)
        else:
            metric["avg_duration_ms"] = (
                (float(previous_avg) * previous_total + duration_ms) / (previous_total + 1)
            )


def get_loop_metrics_snapshot() -> list[dict[str, Any]]:
    with _lock:
        return [dict(metric) for metric in _loop_metrics.values()]


def get_runner_metrics_snapshot() -> list[dict[str, Any]]:
    with _lock:
        return [dict(metric) for metric in _runner_metrics.values()]


def clear_runtime_metrics() -> None:
    """Testing helper to reset in-memory runtime metrics."""
    with _lock:
        _loop_metrics.clear()
        _runner_metrics.clear()


def merge_metric_defaults(metric: Mapping[str, Any], defaults: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(defaults)
    out.update(dict(metric))
    return out
