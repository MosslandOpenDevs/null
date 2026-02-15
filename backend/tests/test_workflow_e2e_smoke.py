from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from null_engine.api.routes import worlds as worlds_route
from null_engine.db import get_db
from null_engine.main import app


class _ScalarCollection:
    def __init__(self, items: list[Any]):
        self._items = items

    def all(self) -> list[Any]:
        return self._items


class _ExecuteResult:
    def __init__(
        self,
        *,
        scalar_one_or_none: Any = None,
        scalars: list[Any] | None = None,
        rows: list[Any] | None = None,
    ):
        self._scalar_one_or_none = scalar_one_or_none
        self._scalars = scalars or []
        self._rows = rows or []

    def scalar_one_or_none(self) -> Any:
        return self._scalar_one_or_none

    def scalars(self) -> _ScalarCollection:
        return _ScalarCollection(self._scalars)

    def all(self) -> list[Any]:
        return self._rows


class _WorkflowSession:
    def __init__(self, execute_results: list[_ExecuteResult] | None = None):
        self._execute_results = list(execute_results or [])
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

    async def execute(self, _stmt: Any) -> _ExecuteResult:
        if not self._execute_results:
            raise AssertionError("Unexpected DB execute call in workflow scenario")
        return self._execute_results.pop(0)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def override_db(monkeypatch):
    def _set_session(session: _WorkflowSession) -> None:
        async def _override():
            yield session

        app.dependency_overrides[get_db] = _override

    async def _no_background_genesis(_world_id, _seed_prompt, _extra_config):
        return None

    class _DummyRunner:
        def __init__(self, world_id):
            self.world_id = world_id
            self.running = False

        def start(self):
            self.running = True

        def stop(self):
            self.running = False

    monkeypatch.setattr(worlds_route, "_background_genesis", _no_background_genesis)
    monkeypatch.setattr(worlds_route, "SimulationRunner", _DummyRunner)
    yield _set_session
    app.dependency_overrides.pop(get_db, None)
    for task in list(worlds_route._genesis_tasks.values()):
        task.cancel()
    worlds_route._genesis_tasks.clear()
    worlds_route._runners.clear()


@pytest.mark.anyio
async def test_world_to_strata_and_resonance_workflow_smoke(override_db) -> None:
    transport = ASGITransport(app=app)

    # 1) Create world
    create_session = _WorkflowSession()
    override_db(create_session)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/api/worlds",
            json={"seed_prompt": "Workflow Seed", "config": {"era": "future"}},
        )
    assert create_resp.status_code == 201
    world_id = create_resp.json()["id"]

    # 2) Start world simulation
    world_stub = SimpleNamespace(
        id=uuid4(),
        status="paused",
        current_epoch=2,
        current_tick=4,
    )
    start_session = _WorkflowSession(
        execute_results=[_ExecuteResult(scalar_one_or_none=world_stub)]
    )
    override_db(start_session)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        start_resp = await client.post(f"/api/worlds/{world_id}/start")
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "started"

    # 3) Compare latest strata (epoch shift)
    newer = SimpleNamespace(
        world_id=world_id,
        epoch=5,
        summary="Trade becomes stable.",
        summary_ko=None,
        dominant_themes=["trade", "stability"],
        emerged_concepts=["dawn pact"],
        faded_concepts=["panic"],
    )
    older = SimpleNamespace(
        world_id=world_id,
        epoch=4,
        summary="Trade panic phase.",
        summary_ko=None,
        dominant_themes=["trade", "panic"],
        emerged_concepts=["panic"],
        faded_concepts=[],
    )
    strata_session = _WorkflowSession(
        execute_results=[_ExecuteResult(scalars=[newer, older])]
    )
    override_db(strata_session)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        compare_resp = await client.get(f"/api/worlds/{world_id}/strata/compare")
    assert compare_resp.status_code == 200
    compare_body = compare_resp.json()
    assert compare_body["from_epoch"] == 4
    assert compare_body["to_epoch"] == 5
    assert compare_body["added_themes"] == ["stability"]
    assert compare_body["persisted_themes"] == ["trade"]

    # 4) Fetch world resonance neighbors
    base_world = uuid4()
    neighbor_world = uuid4()
    neighbors_session = _WorkflowSession(
        execute_results=[
            _ExecuteResult(
                rows=[
                    SimpleNamespace(world_a=base_world, world_b=neighbor_world, strength=0.9),
                    SimpleNamespace(world_a=neighbor_world, world_b=base_world, strength=0.5),
                ]
            ),
            _ExecuteResult(
                scalars=[
                    SimpleNamespace(
                        id=neighbor_world,
                        seed_prompt="Neighbor Workflow World",
                        status="running",
                    )
                ]
            ),
        ]
    )
    override_db(neighbors_session)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        neighbors_resp = await client.get(
            f"/api/multiverse/worlds/{base_world}/neighbors?min_strength=0.5"
        )
    assert neighbors_resp.status_code == 200
    neighbors_body = neighbors_resp.json()
    assert len(neighbors_body) == 1
    assert neighbors_body[0]["world_id"] == str(neighbor_world)
    assert neighbors_body[0]["resonance_count"] == 2
