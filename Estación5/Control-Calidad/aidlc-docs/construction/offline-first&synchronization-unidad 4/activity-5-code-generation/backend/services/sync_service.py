# backend/services/sync_service.py
# Backend sync service for orchestration, validation, and conflict detection

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import structlog
import json

from app.models.sync_models import (
    SyncQueueItem,
    ConflictRecord,
    SyncMetadata,
    SyncStatus,
    OperationType,
    ConflictType,
    ResolutionStrategy,
)
from app.repositories.sync_repositories import SyncQueueRepository, ConflictRepository

logger = structlog.get_logger(__name__)

BACKOFF_INTERVALS_MS = [5000, 10000, 30000, 60000, 60000]
MAX_RETRIES = 5
CONFLICT_EXPIRATION_HOURS = 24


class SyncService:
    def __init__(self, db: Session):
        self.db = db
        self.queue_repo = SyncQueueRepository(db)
        self.conflict_repo = ConflictRepository(db)

    def process_sync_item(
        self, item: SyncQueueItem
    ) -> Tuple[str, Optional[ConflictRecord]]:
        """Process single sync queue item, returns (status, conflict_or_none)"""
        item.status = SyncStatus.SYNCING
        self.db.commit()

        logger.info(
            'sync_item_processing',
            item_id=item.id,
            operation_type=item.operation_type.value,
            entity_id=item.entity_id,
        )

        try:
            # Validate payload
            self.validate_payload(item)

            # Check for conflicts
            conflict = self.detect_conflict(item)
            if conflict:
                item.status = SyncStatus.CONFLICT
                self.db.commit()
                logger.info('conflict_detected', item_id=item.id, conflict_id=conflict.id)
                return 'CONFLICT', conflict

            # Apply changes to database
            self.apply_changes(item)

            # Update item status
            item.status = SyncStatus.SYNCED
            item.synced_at = datetime.utcnow()
            self.db.commit()

            logger.info('sync_item_completed', item_id=item.id)
            return 'SYNCED', None

        except Exception as e:
            logger.error(
                'sync_item_processing_failed',
                item_id=item.id,
                error=str(e),
            )
            raise

    def validate_payload(self, item: SyncQueueItem) -> None:
        """Validate sync item payload structure"""
        if not item.payload:
            raise ValueError('Payload is required')

        payload = item.payload
        if not isinstance(payload, dict):
            raise ValueError('Payload must be a dictionary')

        if 'version' not in payload:
            raise ValueError('Payload must contain version field')

        if not isinstance(payload['version'], int) or payload['version'] < 1:
            raise ValueError('Version must be a positive integer')

    def detect_conflict(self, item: SyncQueueItem) -> Optional[ConflictRecord]:
        """Detect conflicts by comparing versions"""
        # Get server version from domain
        server_item = self.get_server_item(item)
        if not server_item:
            return None

        our_version = item.payload.get('version', 1)
        server_version = server_item.get('version', 1)

        if our_version >= server_version:
            return None

        logger.info(
            'version_conflict_detected',
            item_id=item.id,
            our_version=our_version,
            server_version=server_version,
        )

        conflict = self.conflict_repo.create(
            sync_queue_item_id=item.id,
            entity_type=item.entity_type,
            entity_id=item.entity_id,
            conflict_type=ConflictType.VERSION_MISMATCH,
            our_version=our_version,
            server_version=server_version,
            our_data=item.payload,
            server_data=server_item,
            user_id=item.user_id,
            can_auto_merge=False,
            overlapping_fields=[],
        )

        return conflict

    def get_server_item(self, item: SyncQueueItem) -> Optional[Dict]:
        """Fetch server state for comparison"""
        # This would be implemented based on your domain models
        # For now, return None if item doesn't exist on server
        return None

    def apply_changes(self, item: SyncQueueItem) -> None:
        """Apply sync item changes to database"""
        operation = item.operation_type
        payload = item.payload

        if operation == OperationType.CREATE_INSPECTION:
            self.handle_create_inspection(item.entity_id, payload, item.user_id)
        elif operation == OperationType.UPDATE_INSPECTION:
            self.handle_update_inspection(item.entity_id, payload, item.user_id)
        elif operation == OperationType.SUBMIT_INSPECTION:
            self.handle_submit_inspection(item.entity_id, payload, item.user_id)
        elif operation == OperationType.APPROVE_INSPECTION:
            self.handle_approve_inspection(item.entity_id, payload, item.user_id)
        elif operation == OperationType.REJECT_INSPECTION:
            self.handle_reject_inspection(item.entity_id, payload, item.user_id)
        elif operation == OperationType.DELETE_INSPECTION:
            self.handle_delete_inspection(item.entity_id, payload, item.user_id)

    def handle_create_inspection(self, entity_id: str, payload: dict, user_id: str) -> None:
        """Handle CREATE_INSPECTION operation"""
        logger.info('creating_inspection', entity_id=entity_id, user_id=user_id)
        # Implementation would create inspection in domain

    def handle_update_inspection(self, entity_id: str, payload: dict, user_id: str) -> None:
        """Handle UPDATE_INSPECTION operation"""
        logger.info('updating_inspection', entity_id=entity_id, user_id=user_id)
        # Implementation would update inspection in domain

    def handle_submit_inspection(self, entity_id: str, payload: dict, user_id: str) -> None:
        """Handle SUBMIT_INSPECTION operation"""
        logger.info('submitting_inspection', entity_id=entity_id, user_id=user_id)
        # Implementation would submit inspection in domain

    def handle_approve_inspection(self, entity_id: str, payload: dict, user_id: str) -> None:
        """Handle APPROVE_INSPECTION operation"""
        logger.info('approving_inspection', entity_id=entity_id, user_id=user_id)
        # Implementation would approve inspection in domain

    def handle_reject_inspection(self, entity_id: str, payload: dict, user_id: str) -> None:
        """Handle REJECT_INSPECTION operation"""
        logger.info('rejecting_inspection', entity_id=entity_id, user_id=user_id)
        # Implementation would reject inspection in domain

    def handle_delete_inspection(self, entity_id: str, payload: dict, user_id: str) -> None:
        """Handle DELETE_INSPECTION operation"""
        logger.info('deleting_inspection', entity_id=entity_id, user_id=user_id)
        # Implementation would delete inspection in domain

    def schedule_retry(self, item_id: str, error: str, retry_count: int) -> None:
        """Schedule item for retry with exponential backoff"""
        if retry_count >= MAX_RETRIES:
            self.queue_repo.mark_dead_letter(item_id, f'Max retries exceeded: {error}')
            return

        backoff_ms = BACKOFF_INTERVALS_MS[retry_count]
        next_retry_at = datetime.utcnow() + timedelta(milliseconds=backoff_ms)

        self.queue_repo.schedule_retry(item_id, retry_count + 1, next_retry_at)

        logger.info(
            'sync_item_scheduled_for_retry',
            item_id=item_id,
            retry_count=retry_count + 1,
            backoff_ms=backoff_ms,
        )

    def get_queue_status(self, user_id: Optional[str] = None) -> dict:
        """Get current sync queue status"""
        stats = self.queue_repo.get_queue_stats(user_id)
        return {
            'total': stats['total'],
            'pending': stats['pending'],
            'syncing': stats['syncing'],
            'synced': stats['synced'],
            'conflicts': stats['conflicts'],
            'failed': stats['failed'],
            'dead_letter': stats['dead_letter'],
        }

    def get_conflict_status(self, user_id: Optional[str] = None) -> dict:
        """Get current conflict status"""
        stats = self.conflict_repo.get_conflict_stats(user_id)
        return {
            'total': stats['total'],
            'unresolved': stats['unresolved'],
            'auto_merged': stats['auto_merged'],
            'manual': stats['manual'],
        }

    def cleanup_expired_conflicts(self) -> int:
        """Remove expired conflicts (older than 24 hours)"""
        deleted = self.conflict_repo.delete_expired()
        logger.info('expired_conflicts_cleaned', count=deleted)
        return deleted

    def cleanup_old_items(self, days: int = 30) -> int:
        """Remove synced items older than specified days"""
        deleted = self.queue_repo.delete_by_status(SyncStatus.SYNCED, days)
        logger.info('old_sync_items_cleaned', deleted_count=deleted, days=days)
        return deleted

    def update_sync_metadata(self, user_id: str, synced_count: int = 0, conflicts_count: int = 0) -> None:
        """Update user sync metadata"""
        metadata = self.db.query(SyncMetadata).filter(SyncMetadata.user_id == user_id).first()

        if not metadata:
            metadata = SyncMetadata(user_id=user_id)
            self.db.add(metadata)

        metadata.last_sync_timestamp = datetime.utcnow()
        metadata.total_synced_items += synced_count
        metadata.total_conflicts += conflicts_count
        metadata.updated_at = datetime.utcnow()

        self.db.commit()
