# backend/repositories/sync_repositories.py
# Repository pattern implementation for sync queue and conflict management

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime, timedelta
from typing import List, Optional
import structlog

from app.models.sync_models import (
    SyncQueueItem,
    ConflictRecord,
    SyncMetadata,
    SyncStatus,
    ConflictType,
    ResolutionStrategy,
)

logger = structlog.get_logger(__name__)


class SyncQueueRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        operation_type: str,
        entity_type: str,
        entity_id: str,
        payload: dict,
        user_id: str,
        device_id: Optional[str] = None,
    ) -> SyncQueueItem:
        item = SyncQueueItem(
            operation_type=operation_type,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            user_id=user_id,
            device_id=device_id,
            status=SyncStatus.PENDING,
        )
        self.db.add(item)
        self.db.commit()
        logger.info(
            'sync_queue_item_created',
            item_id=item.id,
            operation_type=operation_type,
            entity_type=entity_type,
            user_id=user_id,
        )
        return item

    def get_by_id(self, item_id: str) -> Optional[SyncQueueItem]:
        return self.db.query(SyncQueueItem).filter(SyncQueueItem.id == item_id).first()

    def get_by_status(self, status: SyncStatus, user_id: Optional[str] = None) -> List[SyncQueueItem]:
        query = self.db.query(SyncQueueItem).filter(SyncQueueItem.status == status)
        if user_id:
            query = query.filter(SyncQueueItem.user_id == user_id)
        return query.order_by(SyncQueueItem.created_at).all()

    def get_pending_and_retry(self, user_id: Optional[str] = None) -> List[SyncQueueItem]:
        query = self.db.query(SyncQueueItem).filter(
            or_(
                SyncQueueItem.status == SyncStatus.PENDING,
                SyncQueueItem.status == SyncStatus.RETRY_PENDING,
            )
        )
        if user_id:
            query = query.filter(SyncQueueItem.user_id == user_id)
        return query.order_by(SyncQueueItem.created_at).all()

    def get_ready_for_retry(self) -> List[SyncQueueItem]:
        now = datetime.utcnow()
        return (
            self.db.query(SyncQueueItem)
            .filter(
                and_(
                    SyncQueueItem.status == SyncStatus.RETRY_PENDING,
                    SyncQueueItem.next_retry_at <= now,
                )
            )
            .order_by(SyncQueueItem.next_retry_at)
            .all()
        )

    def update_status(
        self,
        item_id: str,
        status: SyncStatus,
        last_error: Optional[str] = None,
        synced_at: Optional[datetime] = None,
    ) -> Optional[SyncQueueItem]:
        item = self.get_by_id(item_id)
        if not item:
            return None

        item.status = status
        if last_error:
            item.last_error = last_error
        if synced_at:
            item.synced_at = synced_at

        self.db.commit()
        return item

    def schedule_retry(self, item_id: str, retry_count: int, next_retry_at: datetime) -> Optional[SyncQueueItem]:
        item = self.get_by_id(item_id)
        if not item:
            return None

        item.status = SyncStatus.RETRY_PENDING
        item.retry_count = retry_count
        item.last_retry_at = datetime.utcnow()
        item.next_retry_at = next_retry_at

        self.db.commit()
        logger.info(
            'sync_item_scheduled_for_retry',
            item_id=item_id,
            retry_count=retry_count,
            next_retry_at=next_retry_at.isoformat(),
        )
        return item

    def mark_dead_letter(self, item_id: str, error: str) -> Optional[SyncQueueItem]:
        item = self.get_by_id(item_id)
        if not item:
            return None

        item.status = SyncStatus.DEAD_LETTER
        item.last_error = error

        self.db.commit()
        logger.warn(
            'sync_item_moved_to_dead_letter',
            item_id=item_id,
            error=error,
        )
        return item

    def delete(self, item_id: str) -> bool:
        item = self.get_by_id(item_id)
        if not item:
            return False

        self.db.delete(item)
        self.db.commit()
        return True

    def delete_by_status(self, status: SyncStatus, older_than_days: int = 7) -> int:
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        deleted = (
            self.db.query(SyncQueueItem)
            .filter(
                and_(
                    SyncQueueItem.status == status,
                    SyncQueueItem.created_at < cutoff_date,
                )
            )
            .delete()
        )
        self.db.commit()
        return deleted

    def get_queue_stats(self, user_id: Optional[str] = None) -> dict:
        query = self.db.query(SyncQueueItem)
        if user_id:
            query = query.filter(SyncQueueItem.user_id == user_id)

        total = query.count()
        pending = query.filter(SyncQueueItem.status == SyncStatus.PENDING).count()
        syncing = query.filter(SyncQueueItem.status == SyncStatus.SYNCING).count()
        synced = query.filter(SyncQueueItem.status == SyncStatus.SYNCED).count()
        conflicts = query.filter(SyncQueueItem.status == SyncStatus.CONFLICT).count()
        failed = query.filter(SyncQueueItem.status == SyncStatus.FAILED).count()
        dead_letter = query.filter(SyncQueueItem.status == SyncStatus.DEAD_LETTER).count()

        return {
            'total': total,
            'pending': pending,
            'syncing': syncing,
            'synced': synced,
            'conflicts': conflicts,
            'failed': failed,
            'dead_letter': dead_letter,
        }


class ConflictRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        sync_queue_item_id: str,
        entity_type: str,
        entity_id: str,
        conflict_type: ConflictType,
        our_version: int,
        server_version: int,
        our_data: dict,
        server_data: dict,
        user_id: str,
        base_data: Optional[dict] = None,
        can_auto_merge: bool = False,
        overlapping_fields: Optional[List[str]] = None,
    ) -> ConflictRecord:
        conflict = ConflictRecord(
            sync_queue_item_id=sync_queue_item_id,
            entity_type=entity_type,
            entity_id=entity_id,
            conflict_type=conflict_type,
            our_version=our_version,
            server_version=server_version,
            our_data=our_data,
            server_data=server_data,
            base_data=base_data,
            can_auto_merge=can_auto_merge,
            overlapping_fields=overlapping_fields or [],
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )
        self.db.add(conflict)
        self.db.commit()
        logger.info(
            'conflict_record_created',
            conflict_id=conflict.id,
            sync_queue_item_id=sync_queue_item_id,
            conflict_type=conflict_type.value,
        )
        return conflict

    def get_by_id(self, conflict_id: str) -> Optional[ConflictRecord]:
        return self.db.query(ConflictRecord).filter(ConflictRecord.id == conflict_id).first()

    def get_by_sync_queue_item_id(self, item_id: str) -> Optional[ConflictRecord]:
        return self.db.query(ConflictRecord).filter(ConflictRecord.sync_queue_item_id == item_id).first()

    def get_unresolved(self, user_id: Optional[str] = None) -> List[ConflictRecord]:
        query = self.db.query(ConflictRecord).filter(ConflictRecord.resolution_strategy.is_(None))
        if user_id:
            query = query.filter(ConflictRecord.user_id == user_id)
        return query.order_by(ConflictRecord.created_at).all()

    def get_expired(self) -> List[ConflictRecord]:
        now = datetime.utcnow()
        return self.db.query(ConflictRecord).filter(ConflictRecord.expires_at <= now).all()

    def resolve(
        self,
        conflict_id: str,
        resolution_strategy: ResolutionStrategy,
        resolved_data: Optional[dict] = None,
    ) -> Optional[ConflictRecord]:
        conflict = self.get_by_id(conflict_id)
        if not conflict:
            return None

        conflict.resolution_strategy = resolution_strategy
        conflict.resolved_at = datetime.utcnow()
        if resolved_data:
            conflict.resolved_data = resolved_data

        self.db.commit()
        logger.info(
            'conflict_resolved',
            conflict_id=conflict_id,
            resolution_strategy=resolution_strategy.value,
        )
        return conflict

    def delete(self, conflict_id: str) -> bool:
        conflict = self.get_by_id(conflict_id)
        if not conflict:
            return False

        self.db.delete(conflict)
        self.db.commit()
        return True

    def delete_expired(self) -> int:
        expired = self.get_expired()
        deleted_count = len(expired)
        for conflict in expired:
            self.db.delete(conflict)
        self.db.commit()
        logger.info('expired_conflicts_deleted', count=deleted_count)
        return deleted_count

    def get_conflict_stats(self, user_id: Optional[str] = None) -> dict:
        query = self.db.query(ConflictRecord)
        if user_id:
            query = query.filter(ConflictRecord.user_id == user_id)

        total = query.count()
        unresolved = query.filter(ConflictRecord.resolution_strategy.is_(None)).count()
        auto_merged = query.filter(ConflictRecord.resolution_strategy == ResolutionStrategy.AUTO_MERGE).count()
        manual = query.filter(ConflictRecord.resolution_strategy == ResolutionStrategy.MANUAL_MERGE).count()

        return {
            'total': total,
            'unresolved': unresolved,
            'auto_merged': auto_merged,
            'manual': manual,
        }
