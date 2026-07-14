"""Write-endpoint protection (X-API-Key) behavior."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from null_engine.config import settings
from null_engine.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.anyio
async def test_writes_rejected_when_locked_down() -> None:
    settings.api_write_token = ""
    settings.allow_anonymous_writes = False
    async with _client() as client:
        resp = await client.post("/api/worlds", json={"seed_prompt": "A world of glass"})
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "forbidden"


@pytest.mark.anyio
async def test_wrong_token_rejected() -> None:
    settings.api_write_token = "secret-token"
    settings.allow_anonymous_writes = False
    async with _client() as client:
        resp = await client.post(
            f"/api/worlds/{uuid4()}/start",
            headers={"X-API-Key": "wrong"},
        )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_correct_token_passes_auth_layer() -> None:
    settings.api_write_token = "secret-token"
    settings.allow_anonymous_writes = False
    async with _client() as client:
        # Missing body -> 422 proves the request got past the 403 auth gate.
        resp = await client.post(
            "/api/worlds",
            json={"config": {}},
            headers={"X-API-Key": "secret-token"},
        )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_reads_stay_public_when_locked_down() -> None:
    settings.api_write_token = "secret-token"
    settings.allow_anonymous_writes = False
    async with _client() as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
