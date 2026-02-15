from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from null_engine.db import get_db
from null_engine.main import app


class _ScalarResult:
    def __init__(self, items: list[Any]):
        self._items = items

    def all(self) -> list[Any]:
        return self._items


class _ExecuteResult:
    def __init__(self, items: list[Any]):
        self._items = items

    def all(self) -> list[Any]:
        return self._items

    def scalars(self) -> _ScalarResult:
        return _ScalarResult(self._items)


class _QueueSession:
    def __init__(self, batches: list[list[Any]]):
        self._batches = list(batches)

    async def execute(self, _stmt: Any) -> _ExecuteResult:
        if not self._batches:
            raise AssertionError("Unexpected DB execute call")
        return _ExecuteResult(self._batches.pop(0))


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def override_db():
    def _install(*batches: list[Any]) -> None:
        session = _QueueSession(list(batches))

        async def _override():
            yield session

        app.dependency_overrides[get_db] = _override

    yield _install
    app.dependency_overrides.pop(get_db, None)


@pytest.mark.anyio
async def test_worlds_map_deduplicates_bidirectional_links(override_db) -> None:
    world_a = uuid4()
    world_b = uuid4()
    world_c = uuid4()

    override_db(
        [
            SimpleNamespace(world_a=world_a, world_b=world_b, strength=0.9),
            SimpleNamespace(world_a=world_b, world_b=world_a, strength=0.5),
            SimpleNamespace(world_a=world_a, world_b=world_c, strength=0.2),
        ],
        [
            SimpleNamespace(
                id=world_a,
                seed_prompt="World A",
                status="running",
                config={"description": "A world"},
            ),
            SimpleNamespace(
                id=world_b,
                seed_prompt="World B",
                status="running",
                config={"description": "B world"},
            ),
        ],
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/multiverse/worlds/map?min_strength=0.3")

    assert resp.status_code == 200
    body = resp.json()
    assert len(body["links"]) == 1
    link = body["links"][0]
    assert {link["world_a"], link["world_b"]} == {str(world_a), str(world_b)}
    assert link["count"] == 2
    assert abs(link["strength"] - 0.7) < 1e-6


@pytest.mark.anyio
async def test_world_neighbors_aggregates_resonance(override_db) -> None:
    base_world = uuid4()
    neighbor_world = uuid4()
    low_neighbor_world = uuid4()

    override_db(
        [
            SimpleNamespace(world_a=base_world, world_b=neighbor_world, strength=0.8),
            SimpleNamespace(world_a=neighbor_world, world_b=base_world, strength=0.6),
            SimpleNamespace(world_a=base_world, world_b=low_neighbor_world, strength=0.4),
        ],
        [
            SimpleNamespace(id=neighbor_world, seed_prompt="Neighbor", status="running"),
            SimpleNamespace(id=low_neighbor_world, seed_prompt="Low Neighbor", status="paused"),
        ],
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/multiverse/worlds/{base_world}/neighbors?min_strength=0.5")

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["world_id"] == str(neighbor_world)
    assert body[0]["resonance_count"] == 2
    assert abs(body[0]["strength"] - 0.7) < 1e-6
