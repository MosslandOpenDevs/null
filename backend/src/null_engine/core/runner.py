import asyncio
import uuid

import structlog

from null_engine.agents.memory import MemoryManager
from null_engine.core.consensus import consensus_engine
from null_engine.core.conversation import run_conversation
from null_engine.core.events import check_random_events
from null_engine.core.herald import herald
from null_engine.core.time_dilation import time_dilation
from null_engine.core.wiki import wiki_engine
from null_engine.db import async_session
from null_engine.models.tables import World

logger = structlog.get_logger()


class SimulationRunner:
    def __init__(self, world_id: uuid.UUID):
        self.world_id = world_id
        self.running = False
        self._task: asyncio.Task | None = None
        self._memory = MemoryManager()
        self._conversation_summaries: list[str] = []

    def start(self):
        self.running = True
        self._task = asyncio.create_task(self._run_loop())

    def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()

    async def _run_loop(self):
        logger.info("runner.start", world_id=str(self.world_id))

        try:
            while self.running:
                async with async_session() as db:
                    from sqlalchemy import select

                    result = await db.execute(select(World).where(World.id == self.world_id))
                    world = result.scalar_one_or_none()
                    if not world:
                        logger.error("runner.world_not_found", world_id=str(self.world_id))
                        break

                    await self._tick(db, world)

                # Delay between ticks
                await asyncio.sleep(5)

        except asyncio.CancelledError:
            logger.info("runner.cancelled", world_id=str(self.world_id))
        except Exception:
            logger.exception("runner.error", world_id=str(self.world_id))
        finally:
            self.running = False

    async def _tick(self, db, world: World):
        tick = world.current_tick
        epoch = world.current_epoch

        logger.info("tick", world_id=str(self.world_id), epoch=epoch, tick=tick)

        # 1. Run conversation
        turn = await run_conversation(db, self.world_id, epoch, tick, self._memory)
        if turn.messages:
            summary = f"[E{epoch}T{tick}] {turn.topic}: {len(turn.messages)} messages"
            self._conversation_summaries.append(summary)

            # Extract claims for consensus
            text = "\n".join(f"{m.content}" for m in turn.messages)
            claims = await consensus_engine.extract_claims(text)
            for claim in claims:
                if turn.participants:
                    await consensus_engine.propose_claim(
                        self.world_id, claim, turn.participants[0], turn.participants[0]
                    )

        # 2. Check random events
        events = await check_random_events(db, world, tick)
        for ev in events:
            herald.buffer_event(self.world_id, {"description": ev.description, "type": ev.type})

        # 3. Check consensus
        canon = await consensus_engine.check_consensus(db, self.world_id)

        # 4. Advance time
        epoch_changed = await time_dilation.advance_tick(db, world)

        if epoch_changed:
            # Herald announcement
            await herald.announce(self.world_id, world.current_epoch)

            # Wiki generation every epoch
            if self._conversation_summaries:
                topics = set()
                for s in self._conversation_summaries[-10:]:
                    # Extract topic from summary
                    if "] " in s:
                        topic = s.split("] ", 1)[1].split(":")[0]
                        topics.add(topic)

                for topic in list(topics)[:3]:
                    await wiki_engine.generate_or_update_page(
                        db, self.world_id, topic, self._conversation_summaries[-5:]
                    )

                self._conversation_summaries = []
