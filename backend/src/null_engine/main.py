from contextlib import asynccontextmanager
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio

    from null_engine.core.auto_genesis import auto_genesis_loop
    from null_engine.services.convergence import convergence_loop
    from null_engine.services.semantic_indexer import semantic_indexer_loop
    from null_engine.services.taxonomy_builder import taxonomy_builder_loop
    from null_engine.services.translator import translation_worker_loop

    logger.info("starting null-engine")
    await create_tables()

    # Start resilient background tasks with auto-restart on unexpected failure.
    background_tasks = [
        asyncio.create_task(_run_resilient_loop("auto_genesis", auto_genesis_loop)),
        asyncio.create_task(_run_resilient_loop("convergence", convergence_loop)),
        asyncio.create_task(_run_resilient_loop("semantic_indexer", semantic_indexer_loop)),
        asyncio.create_task(_run_resilient_loop("taxonomy_builder", taxonomy_builder_loop)),
        asyncio.create_task(_run_resilient_loop("translator", translation_worker_loop)),
    ]

    yield

    for task in background_tasks:
        task.cancel()
    await asyncio.gather(*background_tasks, return_exceptions=True)
    await engine.dispose()
    logger.info("null-engine stopped")


app = FastAPI(title="NULL Engine", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
    return {"status": "ok"}
