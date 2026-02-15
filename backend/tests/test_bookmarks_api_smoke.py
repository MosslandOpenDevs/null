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
    def __init__(self, data: Any):
        self._data = data

    def scalars(self) -> _ScalarResult:
        if isinstance(self._data, list):
            return _ScalarResult(self._data)
        if self._data is None:
            return _ScalarResult([])
        return _ScalarResult([self._data])

    def scalar_one_or_none(self) -> Any:
        if isinstance(self._data, list):
            return self._data[0] if self._data else None
        return self._data


class _QueueSession:
    def __init__(self, batches: list[Any] | None = None):
        self._batches = list(batches or [])
        self.deleted: list[Any] = []

    def add(self, obj: Any) -> None:
        if getattr(obj, "id", None) is None:
            obj.id = uuid4()
        if getattr(obj, "created_at", None) is None:
            obj.created_at = datetime.now(UTC)

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def refresh(self, _obj: Any) -> None:
        return None

    async def delete(self, obj: Any) -> None:
        self.deleted.append(obj)

    async def execute(self, _stmt: Any) -> _ExecuteResult:
        if not self._batches:
            raise AssertionError("Unexpected DB execute call")
        return _ExecuteResult(self._batches.pop(0))


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def override_db():
    def _install(*batches: Any) -> _QueueSession:
        session = _QueueSession(list(batches))

        async def _override():
            yield session

        app.dependency_overrides[get_db] = _override
        return session

    yield _install
    app.dependency_overrides.pop(get_db, None)


@pytest.mark.anyio
async def test_create_bookmark_smoke(override_db) -> None:
    session = override_db()
    world_id = uuid4()
    entity_id = uuid4()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/bookmarks",
            json={
                "user_session": "sess-1",
                "label": "Important page",
                "entity_type": "wiki_page",
                "entity_id": str(entity_id),
                "world_id": str(world_id),
                "note": "track this",
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["entity_id"] == str(entity_id)
    assert data["world_id"] == str(world_id)
    assert data["label"] == "Important page"
    assert session.deleted == []


@pytest.mark.anyio
async def test_list_bookmarks_smoke(override_db) -> None:
    world_id = uuid4()
    bookmark = SimpleNamespace(
        id=uuid4(),
        user_session="sess-2",
        label="Saved",
        entity_type="agent",
        entity_id=uuid4(),
        world_id=world_id,
        note="watch",
        created_at=datetime.now(UTC),
    )
    override_db([bookmark])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/bookmarks?session=sess-2")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["entity_type"] == "agent"


@pytest.mark.anyio
async def test_delete_bookmark_smoke(override_db) -> None:
    bookmark = SimpleNamespace(id=uuid4())
    session = override_db(bookmark)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.delete(f"/api/bookmarks/{bookmark.id}")

    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    assert session.deleted == [bookmark]


@pytest.mark.anyio
async def test_export_bookmarks_smoke(override_db) -> None:
    world_id = uuid4()
    page_id = uuid4()
    bookmark = SimpleNamespace(
        label="Wiki clip",
        entity_type="wiki_page",
        entity_id=page_id,
        world_id=world_id,
        note="for report",
    )
    page = SimpleNamespace(title="Neon Port", content="A strategic harbor city.")
    override_db([bookmark], page)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/bookmarks/export?session=sess-3")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["entity_type"] == "wiki_page"
    assert data[0]["title"] == "Neon Port"
