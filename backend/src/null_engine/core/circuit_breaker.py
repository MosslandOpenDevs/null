"""Circuit breaker for simulation quality.

Detects and intervenes when the simulation falls into:
- Repetitive patterns (same topics/claims)
- Echo chambers (single faction dominance)
- Deadlocks (all relationships converging to neutral)
"""

import uuid
from collections import Counter

import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.models.tables import Conversation, Relationship, Claim
from null_engine.models.schemas import WSEnvelope
from null_engine.ws.handler import broadcast

logger = structlog.get_logger()

# Thresholds
SIMILARITY_THRESHOLD = 0.8  # Topic repetition detection
ECHO_CHAMBER_THRESHOLD = 0.7  # Faction dominance ratio
DEADLOCK_STRENGTH_RANGE = (0.4, 0.6)  # Neutral convergence range
MIN_CONVERSATIONS_FOR_ANALYSIS = 5


class CircuitBreaker:
    """Monitors simulation health and triggers interventions."""

    async def analyze(self, db: AsyncSession, world_id: uuid.UUID, epoch: int) -> list[dict]:
        """Run all analyses. Returns list of intervention triggers."""
        interventions: list[dict] = []

        try:
            repetition = await self._detect_repetition(db, world_id)
            if repetition:
                interventions.append(repetition)

            echo = await self._detect_echo_chamber(db, world_id)
            if echo:
                interventions.append(echo)

            deadlock = await self._detect_deadlock(db, world_id)
            if deadlock:
                interventions.append(deadlock)
        except Exception:
            logger.exception("circuit_breaker.analysis_failed", world_id=str(world_id))

        # Broadcast interventions
        for intervention in interventions:
            await broadcast(world_id, WSEnvelope(
                type="event.triggered",
                epoch=epoch,
                payload={
                    "description": intervention["description"],
                    "text": intervention["description"],
                    "source": "circuit_breaker",
                    "intervention_type": intervention["type"],
                },
            ))

        return interventions

    async def _detect_repetition(self, db: AsyncSession, world_id: uuid.UUID) -> dict | None:
        """Detect if recent conversations are too similar in topic."""
        result = await db.execute(
            select(Conversation.topic)
            .where(Conversation.world_id == world_id)
            .order_by(Conversation.created_at.desc())
            .limit(10)
        )
        topics = [row[0] for row in result.all()]

        if len(topics) < MIN_CONVERSATIONS_FOR_ANALYSIS:
            return None

        # Simple: check if any topic appears more than 50% of the time
        counter = Counter(topics)
        most_common_topic, count = counter.most_common(1)[0]
        if count / len(topics) > 0.5:
            logger.warning(
                "circuit_breaker.repetition_detected",
                topic=most_common_topic,
                frequency=count / len(topics),
            )
            return {
                "type": "repetition",
                "description": f"A sudden disruption forces new perspectives—the cycle of '{most_common_topic}' is broken by unexpected events.",
                "topic": most_common_topic,
            }

        return None

    async def _detect_echo_chamber(self, db: AsyncSession, world_id: uuid.UUID) -> dict | None:
        """Detect if one faction dominates all claims."""
        result = await db.execute(
            select(Claim.faction_id, func.count(Claim.id))
            .where(
                Claim.world_id == world_id,
                Claim.status == "proposed",
            )
            .group_by(Claim.faction_id)
        )
        faction_counts = dict(result.all())

        if not faction_counts:
            return None

        total = sum(faction_counts.values())
        if total < 3:
            return None

        max_faction = max(faction_counts, key=faction_counts.get)  # type: ignore[arg-type]
        ratio = faction_counts[max_faction] / total

        if ratio >= ECHO_CHAMBER_THRESHOLD:
            logger.warning(
                "circuit_breaker.echo_chamber_detected",
                dominant_faction=str(max_faction),
                ratio=ratio,
            )
            return {
                "type": "echo_chamber",
                "description": "A dissident voice emerges from the margins, challenging the dominant narrative with counter-evidence.",
                "dominant_faction": str(max_faction),
            }

        return None

    async def _detect_deadlock(self, db: AsyncSession, world_id: uuid.UUID) -> dict | None:
        """Detect if all relationships converge to neutral (~0.5)."""
        result = await db.execute(
            select(Relationship.strength)
            .where(Relationship.world_id == world_id)
        )
        strengths = [row[0] for row in result.all()]

        if len(strengths) < 3:
            return None

        # Check if most strengths are in the neutral range
        neutral_count = sum(
            1 for s in strengths
            if DEADLOCK_STRENGTH_RANGE[0] <= s <= DEADLOCK_STRENGTH_RANGE[1]
        )
        ratio = neutral_count / len(strengths)

        if ratio >= 0.8:
            logger.warning(
                "circuit_breaker.deadlock_detected",
                neutral_ratio=ratio,
            )
            return {
                "type": "deadlock",
                "description": "A provocative discovery polarizes the factions, forcing agents to take strong positions.",
            }

        return None


circuit_breaker = CircuitBreaker()
