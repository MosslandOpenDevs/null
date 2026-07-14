"""Runner state machine and per-world lease behavior."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from null_engine.core.runner_manager import runner_manager
from null_engine.db import get_db
from null_engine.main import app


class _Result:
    def __init__(self, world: Any):
        self._world = world

    def scalar_one_or_none(self) -> Any:
        return self._world


class _Session:
    def __init__(self, world: Any):
        self.world = world

    async def execute(self, _stmt: Any) -> _Result:
        return _Result(self.world)

    async def commit(self) -> None:
        return None


class _DummyRunner:
    def __init__(self, world_id):
        self.world_id = world_id
        self.running = False

    def start(self):
        self.running = True

    def stop(self):
        self.running = False


def _world(status: str):
    return type(
        "WorldStub",
        (),
        {
            "id": uuid4(),
            "status": status,
            "current_epoch": 0,
            "current_tick": 0,
            "created_at": datetime.now(UTC),
        },
    )()


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def manager(monkeypatch):
    monkeypatch.setattr(runner_manager, "runner_factory", _DummyRunner)

    async def _lease_ok(_world_id):
        return True

    async def _release(_world_id):
        return None

    monkeypatch.setattr(runner_manager, "try_acquire_lease", _lease_ok)
    monkeypatch.setattr(runner_manager, "release_lease", _release)
    runner_manager._runners.clear()
    yield runner_manager
    runner_manager._runners.clear()


def _client_for(world):
    session = _Session(world)

    async def _override():
        yield session

    app.dependency_overrides[get_db] = _override
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.anyio
async def test_start_rejected_while_generating(manager) -> None:
    world = _world("generating")
    try:
        async with _client_for(world) as client:
            resp = await client.post(f"/api/worlds/{world.id}/start")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 409
    assert "generating" in resp.json()["detail"]
    assert not manager.is_running(world.id)


@pytest.mark.anyio
async def test_double_start_conflicts(manager) -> None:
    world = _world("ready")
    try:
        async with _client_for(world) as client:
            first = await client.post(f"/api/worlds/{world.id}/start")
            second = await client.post(f"/api/worlds/{world.id}/start")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert first.status_code == 200
    assert second.status_code == 409
    assert manager.is_running(world.id)


@pytest.mark.anyio
async def test_start_rejected_when_lease_held_elsewhere(manager, monkeypatch) -> None:
    async def _lease_denied(_world_id):
        return False

    monkeypatch.setattr(runner_manager, "try_acquire_lease", _lease_denied)
    world = _world("ready")
    try:
        async with _client_for(world) as client:
            resp = await client.post(f"/api/worlds/{world.id}/start")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 409
    assert not manager.is_running(world.id)


@pytest.mark.anyio
async def test_stop_releases_and_allows_restart(manager) -> None:
    world = _world("paused")
    try:
        async with _client_for(world) as client:
            start1 = await client.post(f"/api/worlds/{world.id}/start")
            stop = await client.post(f"/api/worlds/{world.id}/stop")
            start2 = await client.post(f"/api/worlds/{world.id}/start")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert start1.status_code == 200
    assert stop.status_code == 200
    assert start2.status_code == 200
