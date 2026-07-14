from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from null_engine.api.routes import (
    agents,
    bookmarks,
    conversations,
    entities,
    events,
    export,
    factions,
    multiverse,
    ops,
    seeds,
    strata,
    taxonomy,
    wiki,
    worlds,
)
from null_engine.config import settings
from null_engine.db import create_tables, engine
from null_engine.services.runtime_metrics import (
    note_loop_cancelled,
    note_loop_error,
    note_loop_exited,
    note_loop_started,
)
from null_engine.ws.handler import router as ws_router

logger = structlog.get_logger()


async def _run_resilient_loop(
    name: str,
    loop_fn: Callable[[], Awaitable[None]],
    restart_delay_seconds: float = 2.0,
) -> None:
    import asyncio

    while True:
        try:
            note_loop_started(name)
            logger.info("background.loop.start", loop=name)
            await loop_fn()
            note_loop_exited(name)
            logger.warning("background.loop.exited", loop=name)
            await asyncio.sleep(restart_delay_seconds)
        except asyncio.CancelledError:
            note_loop_cancelled(name)
            logger.info("background.loop.cancelled", loop=name)
            raise
        except Exception as exc:
            note_loop_error(name, str(exc))
            logger.exception("background.loop.error", loop=name)
            await asyncio.sleep(restart_delay_seconds)


def _error_code_for_status(status_code: int) -> str:
    if status_code == 401:
        return "unauthorized"
    if status_code == 403:
        return "forbidden"
    if status_code == 404:
        return "not_found"
    if status_code == 422:
        return "validation_error"
    if status_code >= 500:
        return "server_error"
    return "http_error"


def _build_error_payload(
    *,
    path: str,
    status_code: int,
    detail: Any,
    message: str,
    code: str | None = None,
) -> dict[str, Any]:
    return {
        "detail": detail,
        "error": {
            "code": code or _error_code_for_status(status_code),
            "message": message,
            "status_code": status_code,
            "path": path,
        },
    }


async def _recover_running_worlds() -> None:
    """Re-create SimulationRunners for worlds left in 'running' status.

    Goes through the runner manager, so with multiple workers each world
    is picked up by exactly one process (lease-guarded).
    """
    from sqlalchemy import select

    from null_engine.core.runner_manager import runner_manager
    from null_engine.db import async_session
    from null_engine.models.tables import World

    async with async_session() as db:
        result = await db.execute(select(World).where(World.status == "running"))
        running_worlds = result.scalars().all()

    recovered = 0
    for world in running_worlds:
        if await runner_manager.start(world.id):
            recovered += 1
            logger.info("runner.recovered", world_id=str(world.id), epoch=world.current_epoch)

    if running_worlds:
        logger.info("runner.recovery_complete", count=recovered, candidates=len(running_worlds))


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio

    from null_engine.core.auto_genesis import auto_genesis_loop
    from null_engine.services.convergence import convergence_loop
    from null_engine.services.embeddings import probe_embedding_dimension
    from null_engine.services.semantic_indexer import semantic_indexer_loop
    from null_engine.services.taxonomy_builder import taxonomy_builder_loop
    from null_engine.services.translator import translation_worker_loop

    logger.info("starting null-engine")
    await create_tables()

    # Verify the embedding model's real output dimension; a mismatch means
    # every embedding would be silently discarded (fails /health/ready).
    await probe_embedding_dimension()

    # Recover runners for worlds that were "running" before restart.
    await _recover_running_worlds()

    # Start resilient background tasks with auto-restart on unexpected failure.
    background_tasks = [
        asyncio.create_task(_run_resilient_loop("convergence", convergence_loop)),
        asyncio.create_task(_run_resilient_loop("semantic_indexer", semantic_indexer_loop)),
        asyncio.create_task(_run_resilient_loop("taxonomy_builder", taxonomy_builder_loop)),
        asyncio.create_task(_run_resilient_loop("translator", translation_worker_loop)),
    ]
    if settings.auto_genesis_enabled:
        background_tasks.append(
            asyncio.create_task(_run_resilient_loop("auto_genesis", auto_genesis_loop))
        )
    else:
        logger.info("auto_genesis.disabled", hint="set AUTO_GENESIS_ENABLED=true to enable")

    yield

    for task in background_tasks:
        task.cancel()
    await asyncio.gather(*background_tasks, return_exceptions=True)
    await engine.dispose()
    logger.info("null-engine stopped")


app = FastAPI(title="NULL Engine", version="0.1.0", lifespan=lifespan)

_cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins or ["*"],
    # Credentialed wildcard CORS makes Starlette echo any Origin — never
    # combine the two. No cookie-based auth exists, so credentials stay off
    # for the wildcard default.
    allow_credentials="*" not in (_cors_origins or ["*"]),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(worlds.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(wiki.router, prefix="/api")
app.include_router(seeds.router, prefix="/api")
app.include_router(factions.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(multiverse.router, prefix="/api")
app.include_router(ops.router, prefix="/api")
app.include_router(taxonomy.router, prefix="/api")
app.include_router(entities.router, prefix="/api")
app.include_router(strata.router, prefix="/api")
app.include_router(bookmarks.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
app.include_router(ws_router)


@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    message = detail if isinstance(detail, str) else "Request failed"
    return JSONResponse(
        status_code=exc.status_code,
        content=_build_error_payload(
            path=request.url.path,
            status_code=exc.status_code,
            detail=detail,
            message=message,
        ),
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_exception(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=_build_error_payload(
            path=request.url.path,
            status_code=422,
            detail=exc.errors(),
            message="Request validation failed",
            code="validation_error",
        ),
    )


@app.exception_handler(Exception)
async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("api.unhandled_exception", path=request.url.path)
    return JSONResponse(
        status_code=500,
        content=_build_error_payload(
            path=request.url.path,
            status_code=500,
            detail="Internal server error",
            message="Internal server error",
            code="internal_error",
        ),
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "NULL Engine",
        "version": app.version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health/live")
async def health_live():
    return {
        "status": "ok",
        "service": "NULL Engine",
        "version": app.version,
        "mode": "live",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health/ready")
async def health_ready():
    """Readiness: verifies the database actually answers, unlike /health/live."""
    from sqlalchemy import text

    from null_engine.db import async_session
    from null_engine.services.embeddings import probe_state

    checks: dict[str, str] = {}
    healthy = True
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        healthy = False
        checks["database"] = f"error: {type(exc).__name__}"

    embedding_status = str(probe_state["status"])
    checks["embeddings"] = embedding_status
    if embedding_status == "dimension_mismatch":
        # Reachable but misconfigured: every embedding would be discarded.
        healthy = False
        checks["embeddings"] = (
            f"dimension_mismatch: model emits {probe_state['actual_dim']}, "
            f"expected {settings.embedding_dim}"
        )

    payload = {
        "status": "ok" if healthy else "degraded",
        "service": "NULL Engine",
        "version": app.version,
        "mode": "ready",
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if not healthy:
        return JSONResponse(status_code=503, content=payload)
    return payload


@app.get("/ping")
async def ping():
    return {
        "ok": True,
        "service": "NULL Engine",
        "version": app.version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
