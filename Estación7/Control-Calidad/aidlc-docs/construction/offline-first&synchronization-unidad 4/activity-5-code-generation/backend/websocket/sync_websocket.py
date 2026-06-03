# backend/websocket/sync_websocket.py
# WebSocket handler for real-time sync status updates

from fastapi import WebSocket, WebSocketDisconnect, status
from datetime import datetime
from typing import Set, Dict, Optional
import json
import structlog

from app.models.sync_models import SyncStatus
from app.repositories.sync_repositories import SyncQueueRepository, ConflictRepository
from app.database import SessionLocal

logger = structlog.get_logger(__name__)


class SyncWebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_sync_state: Dict[str, dict] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Register user WebSocket connection"""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)
        logger.info('websocket_connected', user_id=user_id)

        # Send initial status
        await self.send_status_update(user_id)

    async def disconnect(self, websocket: WebSocket, user_id: str):
        """Unregister user WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)

            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        logger.info('websocket_disconnected', user_id=user_id)

    async def broadcast_sync_started(self, user_id: str):
        """Notify user(s) that sync has started"""
        await self.broadcast_to_user(
            user_id,
            {
                'type': 'SYNC_STARTED',
                'timestamp': datetime.utcnow().isoformat(),
            },
        )

    async def broadcast_sync_item_progress(
        self,
        user_id: str,
        item_id: str,
        status: str,
        synced_at: Optional[str] = None,
    ):
        """Notify user(s) of sync item progress"""
        await self.broadcast_to_user(
            user_id,
            {
                'type': 'SYNC_ITEM_PROGRESS',
                'item_id': item_id,
                'status': status,
                'synced_at': synced_at,
                'timestamp': datetime.utcnow().isoformat(),
            },
        )

    async def broadcast_conflict_detected(
        self,
        user_id: str,
        conflict_id: str,
        entity_type: str,
        entity_id: str,
    ):
        """Notify user(s) of detected conflict"""
        await self.broadcast_to_user(
            user_id,
            {
                'type': 'CONFLICT_DETECTED',
                'conflict_id': conflict_id,
                'entity_type': entity_type,
                'entity_id': entity_id,
                'timestamp': datetime.utcnow().isoformat(),
            },
        )

    async def broadcast_sync_completed(
        self,
        user_id: str,
        synced_count: int,
        conflict_count: int,
        failed_count: int,
    ):
        """Notify user(s) that sync has completed"""
        await self.broadcast_to_user(
            user_id,
            {
                'type': 'SYNC_COMPLETED',
                'synced_count': synced_count,
                'conflict_count': conflict_count,
                'failed_count': failed_count,
                'timestamp': datetime.utcnow().isoformat(),
            },
        )

    async def broadcast_sync_failed(
        self,
        user_id: str,
        error: str,
    ):
        """Notify user(s) that sync has failed"""
        await self.broadcast_to_user(
            user_id,
            {
                'type': 'SYNC_FAILED',
                'error': error,
                'timestamp': datetime.utcnow().isoformat(),
            },
        )

    async def send_status_update(self, user_id: str):
        """Send current sync status to user"""
        db = SessionLocal()
        try:
            queue_repo = SyncQueueRepository(db)
            conflict_repo = ConflictRepository(db)

            queue_stats = queue_repo.get_queue_stats(user_id)
            conflict_stats = conflict_repo.get_conflict_stats(user_id)

            await self.broadcast_to_user(
                user_id,
                {
                    'type': 'STATUS_UPDATE',
                    'queue_status': queue_stats,
                    'conflict_status': conflict_stats,
                    'timestamp': datetime.utcnow().isoformat(),
                },
            )
        finally:
            db.close()

    async def broadcast_to_user(self, user_id: str, message: dict):
        """Broadcast message to all user connections"""
        if user_id not in self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(
                    'websocket_send_error',
                    user_id=user_id,
                    error=str(e),
                )
                disconnected.append(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            await self.disconnect(connection, user_id)

    def is_user_connected(self, user_id: str) -> bool:
        """Check if user has active connections"""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0


# Global WebSocket manager
sync_ws_manager = SyncWebSocketManager()


async def sync_websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time sync updates.
    Usage: ws://server/api/v1/ws/sync/{user_id}
    """
    await sync_ws_manager.connect(websocket, user_id)

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({'error': 'Invalid JSON'})
                continue

            message_type = message.get('type')

            # Handle ping/pong for connection keep-alive
            if message_type == 'PING':
                await websocket.send_json({'type': 'PONG'})
                continue

            # Handle request for status update
            if message_type == 'REQUEST_STATUS':
                await sync_ws_manager.send_status_update(user_id)
                continue

            # Handle manual sync trigger
            if message_type == 'TRIGGER_SYNC':
                await sync_ws_manager.broadcast_sync_started(user_id)
                continue

            # Unknown message type
            await websocket.send_json({
                'error': f'Unknown message type: {message_type}'
            })

    except WebSocketDisconnect:
        await sync_ws_manager.disconnect(websocket, user_id)
        logger.info('websocket_disconnected_normally', user_id=user_id)

    except Exception as e:
        logger.error(
            'websocket_error',
            user_id=user_id,
            error=str(e),
        )
        await sync_ws_manager.disconnect(websocket, user_id)


class SyncEventBroadcaster:
    """Helper class for broadcasting sync events from background tasks"""

    @staticmethod
    async def on_sync_started(user_id: str):
        """Event: Sync operation started"""
        await sync_ws_manager.broadcast_sync_started(user_id)

    @staticmethod
    async def on_item_synced(user_id: str, item_id: str, synced_at: datetime):
        """Event: Individual sync item completed successfully"""
        await sync_ws_manager.broadcast_sync_item_progress(
            user_id,
            item_id,
            'SYNCED',
            synced_at.isoformat(),
        )

    @staticmethod
    async def on_item_failed(user_id: str, item_id: str):
        """Event: Sync item failed"""
        await sync_ws_manager.broadcast_sync_item_progress(
            user_id,
            item_id,
            'FAILED',
        )

    @staticmethod
    async def on_conflict_detected(
        user_id: str,
        conflict_id: str,
        entity_type: str,
        entity_id: str,
    ):
        """Event: Conflict detected during sync"""
        await sync_ws_manager.broadcast_conflict_detected(
            user_id,
            conflict_id,
            entity_type,
            entity_id,
        )

    @staticmethod
    async def on_sync_completed(
        user_id: str,
        synced_count: int,
        conflict_count: int,
        failed_count: int,
    ):
        """Event: Sync operation completed"""
        await sync_ws_manager.broadcast_sync_completed(
            user_id,
            synced_count,
            conflict_count,
            failed_count,
        )

    @staticmethod
    async def on_sync_failed(user_id: str, error: str):
        """Event: Sync operation failed"""
        await sync_ws_manager.broadcast_sync_failed(user_id, error)
