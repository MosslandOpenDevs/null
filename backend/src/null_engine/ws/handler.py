import json
import uuid
from collections import defaultdict

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from null_engine.models.schemas import WSEnvelope

logger = structlog.get_logger()
router = APIRouter()

# world_id -> set of connected websockets
_connections: dict[uuid.UUID, set[WebSocket]] = defaultdict(set)


@router.websocket("/ws/{world_id}")
async def websocket_endpoint(websocket: WebSocket, world_id: uuid.UUID):
    await websocket.accept()
    _connections[world_id].add(websocket)
    logger.info("ws.connected", world_id=str(world_id))

    try:
        while True:
            data = await websocket.receive_text()
            logger.debug("ws.received", world_id=str(world_id), data=data[:100])

            # Parse client messages for divine intervention
            try:
                msg = json.loads(data)
                msg_type = msg.get("type", "")

                if msg_type == "divine.whisper":
                    agent_id = msg.get("agent_id")
                    message = msg.get("message", "")
                    if agent_id and message:
                        await broadcast(world_id, WSEnvelope(
                            type="event.triggered",
                            payload={
                                "description": f"A divine whisper reaches an agent: '{message[:100]}'",
                                "source": "divine_intervention",
                                "target_agent": agent_id,
                            },
                        ))

                elif msg_type == "divine.event":
                    event_type = msg.get("event_type", "general")
                    description = msg.get("description", "A divine event occurs")
                    await broadcast(world_id, WSEnvelope(
                        type="event.triggered",
                        payload={
                            "description": description,
                            "source": "divine_intervention",
                            "event_type": event_type,
                        },
                    ))

                elif msg_type == "divine.seed_bomb":
                    topic = msg.get("topic", "")
                    if topic:
                        await broadcast(world_id, WSEnvelope(
                            type="event.triggered",
                            payload={
                                "description": f"A new idea ripples through the world: '{topic}'",
                                "source": "divine_intervention",
                                "topic": topic,
                            },
                        ))

            except (json.JSONDecodeError, Exception):
                pass  # Ignore malformed client messages

    except WebSocketDisconnect:
        _connections[world_id].discard(websocket)
        logger.info("ws.disconnected", world_id=str(world_id))


async def broadcast(world_id: uuid.UUID, envelope: WSEnvelope):
    """Broadcast an event to all connected WebSocket clients for a world."""
    connections = _connections.get(world_id, set())
    if not connections:
        return

    payload = envelope.model_dump_json()
    dead: list[WebSocket] = []
    for ws in connections:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws)

    for ws in dead:
        connections.discard(ws)
