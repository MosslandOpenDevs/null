import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.config import settings
from null_engine.models.schemas import WSEnvelope
from null_engine.models.tables import Agent, World
from null_engine.ws.handler import broadcast

logger = structlog.get_logger()


class TimeDilation:
    def __init__(self, ticks_per_epoch: int | None = None):
        self.ticks_per_epoch = ticks_per_epoch or settings.ticks_per_epoch

    async def advance_tick(self, db: AsyncSession, world: World) -> bool:
        """Advance one tick. Returns True if epoch transitioned."""
        world.current_tick += 1

        if world.current_tick >= self.ticks_per_epoch:
            world.current_tick = 0
            world.current_epoch += 1
            await self._epoch_transition(db, world)
            await db.commit()
            return True

        await db.commit()
        return False

    async def _epoch_transition(self, db: AsyncSession, world: World):
        logger.info("epoch.transition", world_id=str(world.id), epoch=world.current_epoch)

        # Belief drift: slightly modify agent beliefs over time
        result = await db.execute(select(Agent).where(Agent.world_id == world.id))
        agents = result.scalars().all()

        for agent in agents:
            if agent.beliefs:
                # Simple drift: beliefs persist but may shift
                pass  # Detailed drift handled by conversation outcomes

        await broadcast(world.id, WSEnvelope(
            type="epoch.transition",
            epoch=world.current_epoch,
            payload={
                "new_epoch": world.current_epoch,
                "total_agents": len(agents),
            },
        ))


time_dilation = TimeDilation()
