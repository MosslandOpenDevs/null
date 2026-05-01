import pytest
from httpx import ASGITransport, AsyncClient

from null_engine.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    body = resp.json()
    assert resp.status_code == 200
    assert body["status"] == "ok"
    assert body["service"] == "NULL Engine"
    assert isinstance(body.get("timestamp"), str)
