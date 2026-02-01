import uuid

import structlog

from null_engine.models.schemas import WSEnvelope
from null_engine.services.llm_router import llm_router
from null_engine.ws.handler import broadcast

logger = structlog.get_logger()

HERALD_PROMPT = """You are the Herald, a dramatic narrator for a world simulation.

Recent events:
{events}

Write a brief, dramatic 1-2 sentence announcement about the most significant event.
Use archaic or dramatic language. Be concise."""


class Herald:
    def __init__(self):
        self._event_buffer: dict[uuid.UUID, list[dict]] = {}

    def buffer_event(self, world_id: uuid.UUID, event: dict):
        if world_id not in self._event_buffer:
            self._event_buffer[world_id] = []
        self._event_buffer[world_id].append(event)

    async def announce(self, world_id: uuid.UUID, epoch: int):
        events = self._event_buffer.get(world_id, [])
        if not events:
            return

        events_text = "\n".join(
            f"- {e.get('description', e.get('type', 'unknown event'))}" for e in events[-5:]
        )

        announcement = await llm_router.generate_text(
            role="reaction_agent",
            prompt=HERALD_PROMPT.format(events=events_text),
        )

        await broadcast(world_id, WSEnvelope(
            type="herald.announcement",
            epoch=epoch,
            payload={"text": announcement, "event_count": len(events)},
        ))

        self._event_buffer[world_id] = []
        logger.info("herald.announced", world_id=str(world_id))


herald = Herald()
