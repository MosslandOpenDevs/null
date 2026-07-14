"""Single owner of SimulationRunner lifecycles.

Every place that used to construct a runner directly (/start, background
genesis, auto-genesis, startup recovery) goes through this manager, which
enforces:

- at most one runner per world **in this process** (asyncio lock + registry)
- at most one runner per world **across processes/workers** via a DB lease
  on the worlds row (lease_owner / lease_expires_at, renewed every tick by
  the runner loop and expiring automatically if a holder dies)
"""

import asyncio
import uuid
from datetime import datetime, timedelta

import structlog
from sqlalchemy import update

from null_engine.core.runner import SimulationRunner
from null_engine.db import async_session
from null_engine.models.tables import World

logger = structlog.get_logger()

#: Identifies this process as a lease holder.
INSTANCE_ID = uuid.uuid4().hex
LEASE_SECONDS = 90


class RunnerManager:
    def __init__(self):
        self._runners: dict[uuid.UUID, SimulationRunner] = {}
        self._lock = asyncio.Lock()
        # Injection point for tests.
        self.runner_factory = SimulationRunner

    def get(self, world_id: uuid.UUID):
        return self._runners.get(world_id)

    def is_running(self, world_id: uuid.UUID) -> bool:
        runner = self._runners.get(world_id)
        return bool(runner and runner.running)

    def running_world_ids(self) -> list[uuid.UUID]:
        return [wid for wid, r in self._runners.items() if r.running]

    async def try_acquire_lease(self, world_id: uuid.UUID) -> bool:
        """Atomically claim the world if unleased, expired, or already ours."""
        now = datetime.utcnow()
        async with async_session() as db:
            result = await db.execute(
                update(World)
                .where(World.id == world_id)
                .where(
                    (World.lease_owner.is_(None))
                    | (World.lease_owner == INSTANCE_ID)
                    | (World.lease_expires_at < now)
                )
                .values(
                    lease_owner=INSTANCE_ID,
                    lease_expires_at=now + timedelta(seconds=LEASE_SECONDS),
                )
            )
            await db.commit()
            return bool(result.rowcount)

    async def renew_lease(self, world_id: uuid.UUID) -> bool:
        now = datetime.utcnow()
        async with async_session() as db:
            result = await db.execute(
                update(World)
                .where(World.id == world_id, World.lease_owner == INSTANCE_ID)
                .values(lease_expires_at=now + timedelta(seconds=LEASE_SECONDS))
            )
            await db.commit()
            return bool(result.rowcount)

    async def release_lease(self, world_id: uuid.UUID) -> None:
        async with async_session() as db:
            await db.execute(
                update(World)
                .where(World.id == world_id, World.lease_owner == INSTANCE_ID)
                .values(lease_owner=None, lease_expires_at=None)
            )
            await db.commit()

    async def start(self, world_id: uuid.UUID) -> bool:
        """Start exactly one runner for the world; False if it can't be ours."""
        async with self._lock:
            existing = self._runners.get(world_id)
            if existing and existing.running:
                logger.info("runner_manager.already_running", world_id=str(world_id))
                return False

            if not await self.try_acquire_lease(world_id):
                logger.warning(
                    "runner_manager.lease_unavailable",
                    world_id=str(world_id),
                    instance=INSTANCE_ID,
                )
                return False

            if existing:
                await self._shutdown_runner(existing)

            runner = self.runner_factory(world_id)
            self._runners[world_id] = runner
            runner.start()
            logger.info("runner_manager.started", world_id=str(world_id))
            return True

    async def stop(self, world_id: uuid.UUID) -> bool:
        async with self._lock:
            runner = self._runners.get(world_id)
            if not runner or not runner.running:
                return False
            await self._shutdown_runner(runner)
            await self.release_lease(world_id)
            logger.info("runner_manager.stopped", world_id=str(world_id))
            return True

    async def shutdown_all(self) -> None:
        """Stop every runner and release its lease (process shutdown).

        Without this, a restart leaves lease rows owned by a dead
        INSTANCE_ID and no process can restart those worlds until the
        lease TTL expires.
        """
        async with self._lock:
            for world_id, runner in list(self._runners.items()):
                try:
                    await self._shutdown_runner(runner)
                except Exception:
                    logger.exception("runner_manager.shutdown_failed", world_id=str(world_id))
                try:
                    await self.release_lease(world_id)
                except Exception:
                    logger.exception("runner_manager.release_failed", world_id=str(world_id))
            self._runners.clear()
        logger.info("runner_manager.shutdown_complete")

    async def _shutdown_runner(self, runner) -> None:
        shutdown = getattr(runner, "shutdown", None)
        if shutdown is not None:
            await shutdown()
        else:  # test doubles may only implement stop()
            runner.stop()


runner_manager = RunnerManager()
