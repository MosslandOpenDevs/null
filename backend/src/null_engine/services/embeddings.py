"""Central embedding service.

Every embedding in the system flows through here so the model and the
vector dimension are controlled in exactly one place (``settings``).
Historically the Ollama path silently discarded every embedding because
the model emits 1024 dims while the DB columns were fixed at 1536.
"""

import httpx
import structlog

from null_engine.config import settings

logger = structlog.get_logger()

# Startup probe result, surfaced by /health/ready.
# status: "unknown" (not probed / provider unreachable), "ok",
#         "dimension_mismatch" (reachable but misconfigured — data-corrupting)
probe_state: dict[str, object] = {"status": "unknown", "actual_dim": None, "detail": ""}

_mismatch_logged = False


async def get_embedding(text: str) -> list[float] | None:
    """Return an ``settings.embedding_dim``-dim embedding, or None on failure."""
    global _mismatch_logged
    try:
        if settings.llm_provider == "ollama":
            emb = await _ollama_embedding(text)
        else:
            emb = await _openai_embedding(text)
        if emb is None:
            return None
        if len(emb) != settings.embedding_dim:
            if not _mismatch_logged:
                _mismatch_logged = True
                logger.error(
                    "embeddings.dimension_mismatch",
                    expected=settings.embedding_dim,
                    actual=len(emb),
                    model=settings.embedding_model,
                    hint="align EMBEDDING_DIM / EMBEDDING_MODEL and re-run the reindex",
                )
            probe_state.update(
                {"status": "dimension_mismatch", "actual_dim": len(emb)}
            )
            return None
        return emb
    except Exception:
        logger.exception("embeddings.error")
        return None


async def _ollama_embedding(text: str) -> list[float] | None:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{settings.ollama_base_url}/api/embed",
            json={"model": settings.embedding_model, "input": text[:2000]},
        )
        if resp.status_code != 200:
            logger.warning("embeddings.ollama_http_error", status=resp.status_code)
            return None
        data = resp.json()
        embeddings = data.get("embeddings") or []
        return embeddings[0] if embeddings else None


async def _openai_embedding(text: str) -> list[float] | None:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    resp = await client.embeddings.create(
        model=settings.openai_embedding_model,
        input=text[:8000],
        dimensions=settings.embedding_dim,
    )
    return resp.data[0].embedding


async def probe_embedding_dimension() -> None:
    """Startup check: verify the configured model's real output dimension.

    A reachable-but-wrong-dimension model fails readiness (it means every
    embedding would be discarded); an unreachable provider stays "unknown"
    so a missing local Ollama doesn't take the API down.
    """
    try:
        if settings.llm_provider == "ollama":
            emb = await _ollama_embedding("dimension probe")
        else:
            emb = await _openai_embedding("dimension probe")
    except Exception as exc:
        probe_state.update({"status": "unknown", "detail": f"probe failed: {type(exc).__name__}"})
        logger.warning("embeddings.probe_unreachable", error=str(exc))
        return

    if emb is None:
        probe_state.update({"status": "unknown", "detail": "provider returned no embedding"})
        logger.warning("embeddings.probe_empty")
        return

    if len(emb) != settings.embedding_dim:
        probe_state.update({"status": "dimension_mismatch", "actual_dim": len(emb)})
        logger.error(
            "embeddings.probe_dimension_mismatch",
            expected=settings.embedding_dim,
            actual=len(emb),
            model=settings.embedding_model,
        )
        return

    probe_state.update({"status": "ok", "actual_dim": len(emb), "detail": ""})
    logger.info("embeddings.probe_ok", dim=len(emb), model=settings.embedding_model)
