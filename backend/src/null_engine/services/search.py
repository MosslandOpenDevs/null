import httpx
import structlog

from null_engine.config import settings

logger = structlog.get_logger()

TAVILY_URL = "https://api.tavily.com/search"


async def search_external(query: str, max_results: int = 5) -> list[dict]:
    """Search external sources via Tavily API for reality injection."""
    if not settings.tavily_api_key:
        logger.warning("tavily.no_key")
        return []

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                TAVILY_URL,
                json={
                    "api_key": settings.tavily_api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "basic",
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return [
                {"title": r.get("title", ""), "content": r.get("content", ""), "url": r.get("url", "")}
                for r in data.get("results", [])
            ]
    except Exception:
        logger.exception("tavily.error")
        return []
