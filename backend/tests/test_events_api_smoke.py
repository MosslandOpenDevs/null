from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from null_engine.api.routes import events as events_route
from null_engine.db import get_db
from null_engine.main import app


class _WorldResult:
    def __init__(self, world: Any):
        self._world = world

    def scalar_one_or_none(self) -> Any:
        return self._world


class _EventSession:
    def __init__(self, world: Any):
        self.world = world

    async def execute(self, _stmt: Any) -> _WorldResult:
        return _WorldResult(self.world)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_create_event_smoke(monkeypatch) -> None:
    world = type(
        "WorldStub",
        (),
        {"id": uuid4(), "current_epoch": 2, "current_tick": 7, "created_at": datetime.now(UTC)},
    )()
    session = _EventSession(world)

    async def _override():
        yield session

    async def _fake_inject_event(_db, _world, body):
        return {
            "status": "injected",
            "type": body.type,
            "description": body.description,
            "epoch": 2,
            "tick": 7,
        }

    app.dependency_overrides[get_db] = _override
    monkeypatch.setattr(events_route, "inject_event", _fake_inject_event)
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                f"/api/worlds/{world.id}/events",
                json={"type": "divine_intervention", "description": "A comet appears"},
            )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200
    assert resp.json()["status"] == "injected"
    assert resp.json()["epoch"] == 2


@pytest.mark.anyio
async def test_create_event_world_not_found_smoke() -> None:
    session = _EventSession(None)

    async def _override():
        yield session

    app.dependency_overrides[get_db] = _override
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                f"/api/worlds/{uuid4()}/events",
                json={"type": "divine_intervention", "description": "No world"},
            )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 404
    body = resp.json()
    assert body["detail"] == "World not found"
    assert body["error"]["code"] == "not_found"
    assert body["error"]["status_code"] == 404
