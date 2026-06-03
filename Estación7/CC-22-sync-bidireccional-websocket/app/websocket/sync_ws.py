"""WebSocket endpoint for bidirectional sync"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from loguru import logger
import json

from app.auth.security import security_service

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, user_id: str, ws: WebSocket):
        await ws.accept()
        self._connections[user_id] = ws
        logger.info("WebSocket connected", user_id=user_id)

    def disconnect(self, user_id: str):
        self._connections.pop(user_id, None)

    async def broadcast(self, event: dict, exclude: str = None):
        for uid, ws in list(self._connections.items()):
            if uid != exclude:
                try:
                    await ws.send_json(event)
                except Exception:
                    self.disconnect(uid)


manager = ConnectionManager()


@router.websocket("/ws/sync")
async def sync_websocket(websocket: WebSocket, token: str):
    """
    Bidirectional sync WebSocket.
    Client sends: {"type": "push", "inspections": [...]}
    Server sends: {"type": "ack", "ids": [...]} or {"type": "new_approval", ...}
    """
    payload = security_service.verify_token(token, token_type="access")
    if not payload:
        await websocket.close(code=4001)
        return

    user_id = payload.get("sub")
    await manager.connect(user_id, websocket)

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type")

            if msg_type == "push":
                inspections = msg.get("inspections", [])
                ids = [i.get("inspection_id") for i in inspections]
                await websocket.send_json({"type": "ack", "ids": ids})
                await manager.broadcast(
                    {"type": "new_inspections", "count": len(ids), "by": user_id},
                    exclude=user_id,
                )

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info("WebSocket disconnected", user_id=user_id)
