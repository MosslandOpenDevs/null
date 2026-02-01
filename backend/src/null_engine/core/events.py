import random
import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.models.tables import World
from null_engine.models.schemas import EventCreate, EventOut, WSEnvelope
from null_engine.ws.handler import broadcast

logger = structlog.get_logger()

RANDOM_EVENTS = [
    "A mysterious plague spreads through the region",
    "A rare resource deposit is discovered",
    "A prophet emerges with dire warnings",
    "Trade routes are disrupted by natural disaster",
    "An ancient artifact is unearthed",
    "A solar eclipse triggers superstitious panic",
    "A foreign delegation arrives seeking alliance",
    "Underground resistance movement forms",
    "A great fire devastates a major settlement",
    "Unusual weather patterns affect harvests",
]

# Probability of random event per tick
EVENT_PROBABILITY = 0.15


async def check_random_events(db: AsyncSession, world: World, tick: int) -> list[EventOut]:
    events: list[EventOut] = []
    if random.random() < EVENT_PROBABILITY:
        description = random.choice(RANDOM_EVENTS)
        event = EventOut(
            type="random",
            description=description,
            epoch=world.current_epoch,
            tick=tick,
        )
        events.append(event)
        logger.info("event.random", desc=description, epoch=world.current_epoch, tick=tick)

        await broadcast(world.id, WSEnvelope(
            type="event.triggered",
            epoch=world.current_epoch,
            payload={"event_type": "random", "description": description, "tick": tick},
        ))

    return events


async def inject_event(db: AsyncSession, world: World, event_data: EventCreate) -> dict:
    logger.info("event.injected", type=event_data.type, desc=event_data.description[:80])

    await broadcast(world.id, WSEnvelope(
        type="event.triggered",
        epoch=world.current_epoch,
        payload={
            "event_type": event_data.type,
            "description": event_data.description,
            "targets": [str(t) for t in event_data.target_agents],
            "tick": world.current_tick,
        },
    ))

    return {
        "status": "injected",
        "type": event_data.type,
        "description": event_data.description,
        "epoch": world.current_epoch,
        "tick": world.current_tick,
    }
