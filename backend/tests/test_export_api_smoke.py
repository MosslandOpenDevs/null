import json
import uuid
from types import SimpleNamespace
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from null_engine.db import get_db
from null_engine.main import app


class _FakeScalarResult:
    def __init__(self, items: list[Any]):
        self._items = items

    def all(self) -> list[Any]:
        return self._items


class _FakeExecuteResult:
    def __init__(self, items: list[Any]):
        self._items = items

    def scalars(self) -> _FakeScalarResult:
        return _FakeScalarResult(self._items)


class _QueueSession:
    def __init__(self, batches: list[list[Any]]):
        self._batches = list(batches)

    async def execute(self, _stmt: Any) -> _FakeExecuteResult:
        if not self._batches:
            raise AssertionError("Unexpected DB execute call")
        return _FakeExecuteResult(self._batches.pop(0))


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
async def test_export_wiki_markdown_smoke(override_db) -> None:
    world_id = uuid.uuid4()
    override_db(
        [
            SimpleNamespace(
                id=uuid.uuid4(),
                title="Neon Joseon",
                content="A steam-powered Joseon kingdom.",
                status="canon",
                version=1,
                created_at=None,
            )
        ]
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/worlds/{world_id}/export/wiki?format=md")

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/markdown")
    assert "# Neon Joseon" in resp.text


@pytest.mark.anyio
async def test_export_training_jsonl_smoke(override_db) -> None:
    world_id = uuid.uuid4()
    override_db(
        [
            SimpleNamespace(
                topic="Faction diplomacy",
                summary="A temporary pact was accepted.",
                messages=[
                    {"agent_id": "A1", "content": "Let's pause the conflict."},
                    {"agent_id": "B2", "content": "We accept under conditions."},
                ],
            )
        ],
        [
            SimpleNamespace(title="Treaty of Dawn", content="A pact between rivals.")
        ],
        [
            SimpleNamespace(subject="A1", predicate="allies_with", object="B2"),
        ],
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/worlds/{world_id}/export/training?format=chatml")

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/jsonl")
    lines = [line for line in resp.text.splitlines() if line.strip()]
    assert len(lines) == 3
    first = json.loads(lines[0])
    assert first["messages"][0]["content"] == "Topic: Faction diplomacy"


@pytest.mark.anyio
async def test_export_knowledge_graph_csv_smoke(override_db) -> None:
    world_id = uuid.uuid4()
    override_db(
        [
            SimpleNamespace(
                subject="Guild",
                predicate="controls",
                object="Harbor",
                confidence=0.91,
            )
        ]
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/worlds/{world_id}/export/knowledge-graph?format=csv")

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "subject,predicate,object,confidence" in resp.text
    assert '"Guild","controls","Harbor",0.91' in resp.text


@pytest.mark.anyio
async def test_export_agents_json_schema_smoke(override_db) -> None:
    world_id = uuid.uuid4()
    override_db(
        [
            SimpleNamespace(
                id=uuid.uuid4(),
                world_id=world_id,
                faction_id=None,
                name="Archivist-7",
                persona={"role": "scribe"},
                beliefs=["order"],
                status="idle",
            )
        ]
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/worlds/{world_id}/export/agents")

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data[0]["name"] == "Archivist-7"
    assert data[0]["world_id"] == str(world_id)
