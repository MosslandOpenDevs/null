from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from null_engine.api.routes import worlds as worlds_route
from null_engine.db import get_db
from null_engine.main import app


class _WorldExecuteResult:
    def __init__(self, world: Any):
        self._world = world

    def scalar_one_or_none(self) -> Any:
        return self._world


class _FakeWorldSession:
    def __init__(self):
        self.world = None

    def add(self, obj: Any) -> None:
        if getattr(obj, "id", None) is None:
            obj.id = uuid4()
        if getattr(obj, "created_at", None) is None:
            obj.created_at = datetime.now(UTC)
        if getattr(obj, "current_epoch", None) is None:
            obj.current_epoch = 0
        if getattr(obj, "current_tick", None) is None:
            obj.current_tick = 0
        self.world = obj

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def refresh(self, _obj: Any) -> None:
        return None

    async def execute(self, _stmt: Any) -> _WorldExecuteResult:
        return _WorldExecuteResult(self.world)


class _NotFoundSession:
    async def execute(self, _stmt: Any) -> _WorldExecuteResult:
        return _WorldExecuteResult(None)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def world_db(monkeypatch):
    session = _FakeWorldSession()

    async def _override():
        yield session

    async def _no_background_genesis(_world_id, _seed_prompt, _extra_config):
        return None

    app.dependency_overrides[get_db] = _override
    monkeypatch.setattr(worlds_route, "_background_genesis", _no_background_genesis)
    yield session
    app.dependency_overrides.pop(get_db, None)
    for task in list(worlds_route._genesis_tasks.values()):
        task.cancel()
    worlds_route._genesis_tasks.clear()
    worlds_route._runners.clear()


@pytest.mark.anyio
async def test_create_world_smoke(world_db) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/worlds",
            json={"seed_prompt": "Neon Joseon", "config": {"era": "alt-1700s"}},
        )

    assert resp.status_code == 201
    body = resp.json()
    assert body["seed_prompt"] == "Neon Joseon"
    assert body["status"] == "generating"
    assert "id" in body
    assert world_db.world is not None


@pytest.mark.anyio
async def test_get_world_smoke(world_db) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/api/worlds",
            json={"seed_prompt": "Archive City", "config": {}},
        )
        world_id = create_resp.json()["id"]
        get_resp = await client.get(f"/api/worlds/{world_id}")

    assert create_resp.status_code == 201
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == world_id


@pytest.mark.anyio
async def test_get_world_not_found_smoke() -> None:
    session = _NotFoundSession()

    async def _override():
        yield session

    app.dependency_overrides[get_db] = _override
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/api/worlds/{uuid4()}")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 404
    body = resp.json()
    assert body["detail"] == "World not found"
    assert body["error"]["code"] == "not_found"
    assert body["error"]["status_code"] == 404


@pytest.mark.anyio
async def test_create_world_validation_error_shape() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/worlds", json={"config": {}})

    assert resp.status_code == 422
    body = resp.json()
    assert isinstance(body["detail"], list)
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["status_code"] == 422


@pytest.mark.anyio
async def test_start_stop_world_smoke(world_db, monkeypatch) -> None:
    class _DummyRunner:
        def __init__(self, world_id):
            self.world_id = world_id
            self.running = False

        def start(self):
            self.running = True

        def stop(self):
            self.running = False

    monkeypatch.setattr(worlds_route, "SimulationRunner", _DummyRunner)
    worlds_route._runners.clear()
    world_db.world = type(
        "WorldStub",
        (),
        {"id": uuid4(), "status": "paused", "current_epoch": 0, "current_tick": 0},
    )()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        start_resp = await client.post(f"/api/worlds/{world_db.world.id}/start")
        stop_resp = await client.post(f"/api/worlds/{world_db.world.id}/stop")

    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "started"
    assert stop_resp.status_code == 200
    assert stop_resp.json()["status"] == "stopped"
