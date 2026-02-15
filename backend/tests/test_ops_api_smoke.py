from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from null_engine.api.routes import worlds as worlds_route
from null_engine.db import get_db
from null_engine.main import app


class _ExecuteResult:
    def __init__(self, *, rows: list[Any] | None = None, scalar_value: Any = None):
        self._rows = rows or []
        self._scalar_value = scalar_value

    def all(self) -> list[Any]:
        return self._rows

    def scalar(self) -> Any:
        return self._scalar_value


class _QueueSession:
    def __init__(self, results: list[_ExecuteResult]):
        self._results = list(results)

    async def execute(self, _stmt: Any) -> _ExecuteResult:
        if not self._results:
            raise AssertionError("Unexpected DB execute call")
        return self._results.pop(0)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def override_db():
    def _install(*results: _ExecuteResult):
        session = _QueueSession(list(results))

        async def _override():
            yield session

        app.dependency_overrides[get_db] = _override

    yield _install
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def patch_runtime(monkeypatch):
    from null_engine.api.routes import ops as ops_route

    monkeypatch.setattr(
        ops_route,
        "get_loop_metrics_snapshot",
        lambda: [
            {
                "name": "convergence",
                "status": "running",
                "restart_count": 1,
                "last_started_at": datetime.now(UTC),
                "last_error_at": None,
                "last_error": None,
            }
        ],
    )
    world_id = uuid4()
    monkeypatch.setattr(
        ops_route,
        "get_runner_metrics_snapshot",
        lambda: [
            {
                "world_id": world_id,
                "status": "running",
                "ticks_total": 12,
                "tick_failures": 0,
                "success_rate": 1.0,
                "last_duration_ms": 120,
                "avg_duration_ms": 110.0,
                "last_tick_delay_ms": 12,
                "last_seen_at": datetime.now(UTC),
            }
        ],
    )
    worlds_route._runners = {world_id: SimpleNamespace(running=True)}
    yield world_id
    worlds_route._runners.clear()


@pytest.mark.anyio
async def test_ops_metrics_smoke(override_db, patch_runtime) -> None:
    override_db(
        _ExecuteResult(rows=[("running", 2), ("paused", 1)]),
        _ExecuteResult(scalar_value=1),  # generating worlds
        _ExecuteResult(scalar_value=3),  # pending conversations
        _ExecuteResult(scalar_value=2),  # pending wiki
        _ExecuteResult(scalar_value=1),  # pending strata
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/ops/metrics")

    assert resp.status_code == 200
    body = resp.json()
    assert body["active_runners"] == 1
    assert len(body["worlds"]) == 2
    assert body["queues"]["translator_pending_conversations"] == 3
    assert body["loops"][0]["name"] == "convergence"
    assert body["runners"][0]["world_id"] == str(patch_runtime)
    assert body["alerts"] == []


@pytest.mark.anyio
async def test_ops_alerts_smoke(override_db, monkeypatch) -> None:
    from null_engine.api.routes import ops as ops_route

    world_id = uuid4()
    monkeypatch.setattr(
        ops_route,
        "get_loop_metrics_snapshot",
        lambda: [
            {
                "name": "taxonomy_builder",
                "status": "error",
                "restart_count": 4,
                "last_started_at": datetime.now(UTC),
                "last_error_at": datetime.now(UTC),
                "last_error": "timeout",
            }
        ],
    )
    monkeypatch.setattr(
        ops_route,
        "get_runner_metrics_snapshot",
        lambda: [
            {
                "world_id": world_id,
                "status": "degraded",
                "ticks_total": 15,
                "tick_failures": 5,
                "success_rate": 0.66,
                "last_duration_ms": 800,
                "avg_duration_ms": 600.0,
                "last_tick_delay_ms": 100,
                "last_seen_at": datetime.now(UTC),
            }
        ],
    )
    worlds_route._runners = {}

    override_db(
        _ExecuteResult(rows=[("running", 3)]),
        _ExecuteResult(scalar_value=6),   # generating worlds
        _ExecuteResult(scalar_value=30),  # pending conversations
        _ExecuteResult(scalar_value=20),  # pending wiki
        _ExecuteResult(scalar_value=15),  # pending strata
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/ops/alerts")

    worlds_route._runners.clear()

    assert resp.status_code == 200
    alerts = resp.json()
    codes = {alert["code"] for alert in alerts}
    assert "loop_error" in codes
    assert "runner_degraded" in codes
    assert "translator_backlog" in codes
    assert "genesis_backlog" in codes
    assert "runner_mismatch" in codes
