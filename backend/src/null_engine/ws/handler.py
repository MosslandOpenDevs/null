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
            # Keep connection alive; handle incoming messages if needed
            data = await websocket.receive_text()
            # Client messages can be used for divine intervention in the future
            logger.debug("ws.received", world_id=str(world_id), data=data[:100])
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
