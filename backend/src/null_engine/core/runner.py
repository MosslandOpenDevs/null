import asyncio
import time
import uuid

import structlog
from sqlalchemy import select

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
RUNNER_TICK_INTERVAL_SECONDS = 10


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

    async def shutdown(self):
        """Stop and wait for the loop task, so no orphan loop keeps ticking."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        note_runner_status(self.world_id, "stopped")

    async def _lease_heartbeat(self):
        """Renew the world lease independently of tick duration.

        A long tick (LLM calls can take minutes) must not let the lease
        lapse mid-tick, or another worker could start a second runner.
        Transient DB errors are tolerated; three consecutive failures or
        a definitive renewal refusal stop the runner.
        """
        from null_engine.core.runner_manager import LEASE_SECONDS, runner_manager

        consecutive_failures = 0
        while self.running:
            await asyncio.sleep(LEASE_SECONDS / 3)
            if not self.running:
                return
            try:
                renewed = await runner_manager.renew_lease(self.world_id)
                consecutive_failures = 0
            except Exception:
                consecutive_failures += 1
                logger.exception(
                    "runner.lease_renew_error",
                    world_id=str(self.world_id),
                    consecutive=consecutive_failures,
                )
                if consecutive_failures >= 3:
                    logger.error("runner.lease_renew_giving_up", world_id=str(self.world_id))
                    self.running = False
                    note_runner_status(self.world_id, "lease_lost")
                    return
                continue
            if not renewed:
                logger.warning("runner.lease_lost", world_id=str(self.world_id))
                self.running = False
                note_runner_status(self.world_id, "lease_lost")
                return

    async def _run_loop(self):
        from null_engine.core.runner_manager import runner_manager

        logger.info("runner.start", world_id=str(self.world_id))
        note_runner_status(self.world_id, "running")

        # Restore persisted state so a restart doesn't wipe agent memory
        # or in-flight consensus.
        try:
            async with async_session() as db:
                from null_engine.models.tables import Agent

                agents_result = await db.execute(
                    select(Agent.id).where(Agent.world_id == self.world_id)
                )
                for (agent_id,) in agents_result.all():
                    await self._memory.load_from_db(agent_id, db)
                await consensus_engine.load_from_db(db, self.world_id)
        except Exception:
            logger.exception("runner.state_restore_failed", world_id=str(self.world_id))

        heartbeat = asyncio.create_task(self._lease_heartbeat())
        consecutive_loop_errors = 0
        try:
            while self.running:
                loop_now = time.monotonic()
                tick_delay_ms = 0
                if self._last_tick_started_at is not None:
                    expected_next_tick = self._last_tick_started_at + RUNNER_TICK_INTERVAL_SECONDS
                    tick_delay_ms = max(0, int((loop_now - expected_next_tick) * 1000))
                self._last_tick_started_at = loop_now

                try:
                    async with async_session() as db:
                        result = await db.execute(select(World).where(World.id == self.world_id))
                        world = result.scalar_one_or_none()
                    consecutive_loop_errors = 0
                except Exception:
                    # Transient DB outage must not kill the runner while the
                    # world row still says "running".
                    consecutive_loop_errors += 1
                    logger.exception(
                        "runner.world_fetch_failed",
                        world_id=str(self.world_id),
                        consecutive=consecutive_loop_errors,
                    )
                    if consecutive_loop_errors >= 6:
                        note_runner_status(self.world_id, "db_unreachable")
                        break
                    await asyncio.sleep(RUNNER_TICK_INTERVAL_SECONDS)
                    continue

                if not world:
                    logger.error("runner.world_not_found", world_id=str(self.world_id))
                    note_runner_status(self.world_id, "missing_world")
                    break

                if world.status == "paused":
                    # Cross-worker stop: another process set the world to
                    # paused; honor it even though it can't reach this runner.
                    logger.info("runner.stopped_via_status", world_id=str(self.world_id))
                    note_runner_status(self.world_id, "stopped_via_status")
                    break

                async with async_session() as db:
                    result = await db.execute(select(World).where(World.id == self.world_id))
                    world = result.scalar_one_or_none()
                    if not world:
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
                        # The rollback may have erased rows that the consensus
                        # cache already references; resync so later votes
                        # don't hit dead claim ids.
                        try:
                            await consensus_engine.load_from_db(db, self.world_id)
                        except Exception:
                            logger.exception("runner.consensus_resync_failed", world_id=str(self.world_id))
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
            heartbeat.cancel()
            # Best-effort lease release (scoped to our INSTANCE_ID, so this
            # is a no-op if another worker already took over).
            try:
                await asyncio.shield(runner_manager.release_lease(self.world_id))
            except Exception:
                logger.warning("runner.lease_release_failed", world_id=str(self.world_id))
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
            # Carry real utterances into the summary so downstream wiki
            # generation is grounded in what agents actually said, not just
            # a topic name and a message count.
            excerpt = " / ".join(
                m.content[:150].replace("\n", " ") for m in turn.messages[:3]
            )
            summary = f"[E{epoch}T{tick}] {turn.topic} ({len(turn.messages)} messages): {excerpt}"
            self._conversation_summaries.append(summary)

            # Extract claims for consensus
            text = "\n".join(f"{m.content}" for m in turn.messages)
            claims = await consensus_engine.extract_claims(text)
            claims_count = len(claims)
            if claims and turn.participants:
                # Look up the proposer agent's faction_id
                from null_engine.models.tables import Agent
                proposer_id = turn.participants[0]
                agent_result = await db.execute(
                    select(Agent).where(Agent.id == proposer_id)
                )
                proposer_agent = agent_result.scalar_one_or_none()
                faction_id = proposer_agent.faction_id if proposer_agent else None

                for claim in claims:
                    if faction_id:
                        await consensus_engine.propose_claim(
                            db, self.world_id, claim, proposer_id, faction_id
                        )

        # 1b. Peer voting on open claims, so consensus (3+ votes from 2+
        # factions) is actually reachable — previously only the proposer's
        # own vote ever existed.
        votes_cast = await self._vote_on_claims(db)

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
            "votes_cast": votes_cast,
            "events_triggered": len(events),
            "posts_created": len(posts),
            "epoch_changed": epoch_changed,
            "wiki_topics_generated": wiki_topics_generated,
        }

    async def _vote_on_claims(self, db) -> int:
        """Deterministic-heuristic peer voting (no LLM cost per vote).

        A few random agents evaluate each open claim; same-faction agents
        and high-confidence claims are more likely to attract votes.
        """
        import random

        from null_engine.models.tables import Agent

        open_claims = consensus_engine.open_claims(self.world_id)[:3]
        if not open_claims:
            return 0

        result = await db.execute(select(Agent).where(Agent.world_id == self.world_id))
        agents = list(result.scalars().all())
        if not agents:
            return 0

        votes_cast = 0
        for claim in open_claims:
            already_voted = {v["agent"] for v in claim["votes"]}
            candidates = [a for a in agents if str(a.id) not in already_voted]
            for voter in random.sample(candidates, min(3, len(candidates))):
                same_faction = str(voter.faction_id) == claim.get("faction")
                confidence = float(claim.get("confidence", 0.5) or 0.5)
                p_vote = 0.25 + (0.3 if same_faction else 0.0) + 0.3 * confidence
                if random.random() >= p_vote:
                    continue
                outcome = await consensus_engine.vote(
                    db,
                    self.world_id,
                    claim.get("claim", ""),
                    voter.id,
                    voter.faction_id,
                )
                if outcome:
                    votes_cast += 1
                if outcome == "canon":
                    break
        return votes_cast
