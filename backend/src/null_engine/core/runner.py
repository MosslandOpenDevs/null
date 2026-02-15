import asyncio
import time
import uuid

import structlog

from null_engine.agents.memory import MemoryManager
from null_engine.core.consensus import consensus_engine
from null_engine.core.conversation import run_conversation
from null_engine.core.events import check_random_events
from null_engine.core.herald import herald
from null_engine.core.posts import generate_agent_posts
from null_engine.core.time_dilation import time_dilation
from null_engine.core.wiki import wiki_engine
from null_engine.db import async_session
from null_engine.models.tables import World
from null_engine.services.runtime_metrics import note_runner_status, note_runner_tick

logger = structlog.get_logger()
RUNNER_TICK_INTERVAL_SECONDS = 5


class SimulationRunner:
    def __init__(self, world_id: uuid.UUID):
        self.world_id = world_id
        self.running = False
        self._task: asyncio.Task | None = None
        self._memory = MemoryManager()
        self._conversation_summaries: list[str] = []
        self._last_tick_started_at: float | None = None
        self._ticks_total = 0
        self._tick_failures = 0

    def start(self):
        self.running = True
        note_runner_status(self.world_id, "starting")
        self._task = asyncio.create_task(self._run_loop())

    def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()
        note_runner_status(self.world_id, "stopping")

    async def _run_loop(self):
        logger.info("runner.start", world_id=str(self.world_id))
        note_runner_status(self.world_id, "running")

        try:
            while self.running:
                loop_now = time.monotonic()
                tick_delay_ms = 0
                if self._last_tick_started_at is not None:
                    expected_next_tick = self._last_tick_started_at + RUNNER_TICK_INTERVAL_SECONDS
                    tick_delay_ms = max(0, int((loop_now - expected_next_tick) * 1000))
                self._last_tick_started_at = loop_now

                async with async_session() as db:
                    from sqlalchemy import select

                    result = await db.execute(select(World).where(World.id == self.world_id))
                    world = result.scalar_one_or_none()
                    if not world:
                        logger.error("runner.world_not_found", world_id=str(self.world_id))
                        note_runner_status(self.world_id, "missing_world")
                        break

                    epoch = world.current_epoch
                    tick = world.current_tick
                    tick_started = time.monotonic()
                    tick_metrics: dict[str, int | bool] = {}
                    tick_ok = False

                    try:
                        tick_metrics = await self._tick(db, world)
                        tick_ok = True
                    except Exception:
                        self._tick_failures += 1
                        await db.rollback()
                        logger.exception("runner.tick_failed", world_id=str(self.world_id), epoch=epoch, tick=tick)
                    finally:
                        self._ticks_total += 1
                        duration_ms = int((time.monotonic() - tick_started) * 1000)
                        success_rate = (
                            (self._ticks_total - self._tick_failures) / self._ticks_total
                            if self._ticks_total
                            else 0.0
                        )
                        logger.info(
                            "runner.tick_metrics",
                            world_id=str(self.world_id),
                            epoch=epoch,
                            tick=tick,
                            duration_ms=duration_ms,
                            tick_delay_ms=tick_delay_ms,
                            tick_ok=tick_ok,
                            success_rate=round(success_rate, 3),
                            **tick_metrics,
                        )
                        note_runner_tick(
                            world_id=self.world_id,
                            tick_ok=tick_ok,
                            ticks_total=self._ticks_total,
                            tick_failures=self._tick_failures,
                            success_rate=success_rate,
                            duration_ms=duration_ms,
                            tick_delay_ms=tick_delay_ms,
                        )

                # Delay between ticks
                await asyncio.sleep(RUNNER_TICK_INTERVAL_SECONDS)

        except asyncio.CancelledError:
            logger.info("runner.cancelled", world_id=str(self.world_id))
            note_runner_status(self.world_id, "cancelled")
        except Exception:
            logger.exception("runner.error", world_id=str(self.world_id))
            note_runner_status(self.world_id, "error")
        finally:
            self.running = False
            note_runner_status(self.world_id, "stopped")

    async def _tick(self, db, world: World) -> dict[str, int | bool]:
        tick = world.current_tick
        epoch = world.current_epoch
        claims_count = 0
        wiki_topics_generated = 0

        logger.info("tick", world_id=str(self.world_id), epoch=epoch, tick=tick)

        # 1. Run conversation
        turn = await run_conversation(db, self.world_id, epoch, tick, self._memory)
        if turn.messages:
            summary = f"[E{epoch}T{tick}] {turn.topic}: {len(turn.messages)} messages"
            self._conversation_summaries.append(summary)

            # Extract claims for consensus
            text = "\n".join(f"{m.content}" for m in turn.messages)
            claims = await consensus_engine.extract_claims(text)
            claims_count = len(claims)
            for claim in claims:
                if turn.participants:
                    await consensus_engine.propose_claim(
                        self.world_id, claim, turn.participants[0], turn.participants[0]
                    )

        # 2. Check random events
        events = await check_random_events(db, world, tick)
        for ev in events:
            herald.buffer_event(self.world_id, {"description": ev.description, "type": ev.type})

        # 3. Generate agent posts
        posts = await generate_agent_posts(db, self.world_id, epoch, tick)

        # 4. Check consensus
        await consensus_engine.check_consensus(db, self.world_id)

        # 5. Advance time
        epoch_changed = await time_dilation.advance_tick(db, world)

        if epoch_changed:
            # Herald announcement
            await herald.announce(self.world_id, world.current_epoch)

            # Generate stratum for the completed epoch
            try:
                from null_engine.services.stratum_detector import detect_stratum
                await detect_stratum(db, self.world_id, epoch)
            except Exception:
                logger.exception("runner.stratum_failed", epoch=epoch)

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
                    wiki_topics_generated += 1

                self._conversation_summaries = []

        return {
            "participants": len(turn.participants),
            "conversation_messages": len(turn.messages),
            "claims_proposed": claims_count,
            "events_triggered": len(events),
            "posts_created": len(posts),
            "epoch_changed": epoch_changed,
            "wiki_topics_generated": wiki_topics_generated,
        }
