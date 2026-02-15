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
async def test_compare_latest_strata_smoke(override_db) -> None:
    world_id = uuid4()
    newer = SimpleNamespace(
        world_id=world_id,
        epoch=4,
        summary="Trade pacts stabilized.",
        summary_ko=None,
        dominant_themes=["trade", "stability"],
        emerged_concepts=["pact"],
        faded_concepts=["panic"],
    )
    older = SimpleNamespace(
        world_id=world_id,
        epoch=3,
        summary="Markets were unstable.",
        summary_ko=None,
        dominant_themes=["trade", "panic"],
        emerged_concepts=["panic"],
        faded_concepts=[],
    )
    override_db([newer, older])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/worlds/{world_id}/strata/compare")

    assert resp.status_code == 200
    body = resp.json()
    assert body["from_epoch"] == 3
    assert body["to_epoch"] == 4
    assert body["added_themes"] == ["stability"]
    assert body["removed_themes"] == ["panic"]
    assert body["persisted_themes"] == ["trade"]
    assert body["newly_emerged_concepts"] == ["pact"]
    assert body["newly_faded_concepts"] == ["panic"]


@pytest.mark.anyio
async def test_compare_specific_epochs_not_found_smoke(override_db) -> None:
    world_id = uuid4()
    override_db(
        [
            SimpleNamespace(
                world_id=world_id,
                epoch=2,
                summary="Only one stratum exists.",
                summary_ko=None,
                dominant_themes=[],
                emerged_concepts=[],
                faded_concepts=[],
            )
        ]
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/worlds/{world_id}/strata/compare?from_epoch=2&to_epoch=3")

    assert resp.status_code == 404
    body = resp.json()
    assert body["detail"] == "Stratum comparison target not found"
    assert body["error"]["code"] == "not_found"


@pytest.mark.anyio
async def test_compare_strata_invalid_query_smoke() -> None:
    world_id = uuid4()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/worlds/{world_id}/strata/compare?from_epoch=2")

    assert resp.status_code == 400
    body = resp.json()
    assert body["detail"] == "Provide both from_epoch and to_epoch, or neither"
    assert body["error"]["code"] == "http_error"
