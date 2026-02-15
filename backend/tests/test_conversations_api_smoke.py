from datetime import UTC, datetime
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

    def all(self) -> list[Any]:
        return self._items


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
async def test_list_conversations_smoke(override_db) -> None:
    world_id = uuid4()
    agent_id = uuid4()
    faction_id = uuid4()
    conversation = SimpleNamespace(
        id=uuid4(),
        epoch=3,
        tick=5,
        topic="Treaty talks",
        topic_ko=None,
        participants=[agent_id],
        messages=[{"content": "We propose a ceasefire."}],
        messages_ko=None,
        summary="The factions open negotiations.",
        summary_ko=None,
        created_at=datetime.now(UTC),
    )

    override_db(
        [conversation],
        [SimpleNamespace(id=agent_id, name="Diplomat-1", faction_id=faction_id)],
        [SimpleNamespace(id=faction_id, color="#00ffcc")],
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/worlds/{world_id}/conversations")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["topic"] == "Treaty talks"
    assert data[0]["participants"][0]["name"] == "Diplomat-1"
    assert data[0]["participants"][0]["faction_color"] == "#00ffcc"


@pytest.mark.anyio
async def test_feed_smoke(override_db) -> None:
    world_id = uuid4()
    conversation = SimpleNamespace(
        id=uuid4(),
        topic="Supply crisis",
        topic_ko=None,
        participants=[],
        messages=[{"content": "Food reserves are critical."}],
        created_at=datetime.now(UTC),
    )
    wiki_page = SimpleNamespace(
        id=uuid4(),
        title="Granary Network",
        title_ko=None,
        created_by_agent=None,
        status="canon",
        version=2,
        created_at=datetime.now(UTC),
    )
    stratum = SimpleNamespace(
        id=uuid4(),
        epoch=4,
        summary="Scarcity reshaped alliances.",
        summary_ko=None,
        dominant_themes=["scarcity", "trade"],
    )

    override_db(
        [conversation],
        [wiki_page],
        [stratum],
        [],
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/worlds/{world_id}/feed")

    assert resp.status_code == 200
    types = [item["type"] for item in resp.json()]
    assert "conversation" in types
    assert "wiki_edit" in types
    assert "epoch" in types
