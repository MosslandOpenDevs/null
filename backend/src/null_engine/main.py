from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from null_engine.api.routes import worlds, agents, events, wiki, seeds, factions, export, multiverse
from null_engine.db import engine, create_tables
from null_engine.ws.handler import router as ws_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio
    from null_engine.core.auto_genesis import auto_genesis_loop
    from null_engine.services.convergence import convergence_loop

    logger.info("starting null-engine")
    await create_tables()

    # Start background tasks
    auto_task = asyncio.create_task(auto_genesis_loop())
    convergence_task = asyncio.create_task(convergence_loop())

    yield

    auto_task.cancel()
    convergence_task.cancel()
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
app.include_router(ws_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
