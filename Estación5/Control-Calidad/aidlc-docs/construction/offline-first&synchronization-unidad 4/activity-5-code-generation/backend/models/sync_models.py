# backend/models/sync_models.py
# SQLAlchemy ORM models for offline sync queue and conflict management

from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON, Text, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
import uuid

Base = declarative_base()


class SyncStatus(str, Enum):
    PENDING = 'PENDING'
    SYNCING = 'SYNCING'
    SYNCED = 'SYNCED'
    CONFLICT = 'CONFLICT'
    FAILED = 'FAILED'
    RETRY_PENDING = 'RETRY_PENDING'
    DEAD_LETTER = 'DEAD_LETTER'


class OperationType(str, Enum):
    CREATE_INSPECTION = 'CREATE_INSPECTION'
    UPDATE_INSPECTION = 'UPDATE_INSPECTION'
    SUBMIT_INSPECTION = 'SUBMIT_INSPECTION'
    APPROVE_INSPECTION = 'APPROVE_INSPECTION'
    REJECT_INSPECTION = 'REJECT_INSPECTION'
    DELETE_INSPECTION = 'DELETE_INSPECTION'


class ConflictType(str, Enum):
    VERSION_MISMATCH = 'VERSION_MISMATCH'
    DELETED_REMOTE = 'DELETED_REMOTE'
    EDITED_BOTH = 'EDITED_BOTH'


class ResolutionStrategy(str, Enum):
    AUTO_MERGE = 'AUTO_MERGE'
    KEEP_LOCAL = 'KEEP_LOCAL'
    USE_SERVER = 'USE_SERVER'
    MANUAL_MERGE = 'MANUAL_MERGE'


class SyncQueueItem(Base):
    __tablename__ = 'sync_queue_items'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    operation_type = Column(SQLEnum(OperationType), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(36), nullable=False)
    payload = Column(JSON, nullable=False)

    status = Column(SQLEnum(SyncStatus), default=SyncStatus.PENDING, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_retry_at = Column(DateTime, nullable=True)
    next_retry_at = Column(DateTime, nullable=True)
    synced_at = Column(DateTime, nullable=True)

    user_id = Column(String(36), nullable=False)
    device_id = Column(String(36), nullable=True)

    __table_args__ = (
        Index('idx_sync_queue_status', 'status'),
        Index('idx_sync_queue_user_id', 'user_id'),
        Index('idx_sync_queue_next_retry', 'next_retry_at'),
        Index('idx_sync_queue_created', 'created_at'),
    )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'operation_type': self.operation_type.value,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'payload': self.payload,
            'status': self.status.value,
            'retry_count': self.retry_count,
            'last_error': self.last_error,
            'created_at': self.created_at.isoformat(),
            'last_retry_at': self.last_retry_at.isoformat() if self.last_retry_at else None,
            'next_retry_at': self.next_retry_at.isoformat() if self.next_retry_at else None,
            'synced_at': self.synced_at.isoformat() if self.synced_at else None,
        }


class ConflictRecord(Base):
    __tablename__ = 'conflict_records'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sync_queue_item_id = Column(String(36), ForeignKey('sync_queue_items.id'), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(36), nullable=False)

    conflict_type = Column(SQLEnum(ConflictType), nullable=False)
    our_version = Column(Integer, nullable=False)
    server_version = Column(Integer, nullable=False)

    our_data = Column(JSON, nullable=False)
    server_data = Column(JSON, nullable=False)
    base_data = Column(JSON, nullable=True)

    can_auto_merge = Column(Boolean, default=False, nullable=False)
    overlapping_fields = Column(JSON, default=list, nullable=False)

    resolution_strategy = Column(SQLEnum(ResolutionStrategy), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    user_id = Column(String(36), nullable=False)

    __table_args__ = (
        Index('idx_conflict_sync_queue_item', 'sync_queue_item_id'),
        Index('idx_conflict_user_id', 'user_id'),
        Index('idx_conflict_resolution', 'resolution_strategy'),
        Index('idx_conflict_expires', 'expires_at'),
    )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'sync_queue_item_id': self.sync_queue_item_id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'conflict_type': self.conflict_type.value,
            'our_version': self.our_version,
            'server_version': self.server_version,
            'our_data': self.our_data,
            'server_data': self.server_data,
            'base_data': self.base_data,
            'can_auto_merge': self.can_auto_merge,
            'overlapping_fields': self.overlapping_fields,
            'resolution_strategy': self.resolution_strategy.value if self.resolution_strategy else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
        }


class SyncMetadata(Base):
    __tablename__ = 'sync_metadata'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, unique=True)

    last_sync_timestamp = Column(DateTime, nullable=True)
    last_conflict_check = Column(DateTime, nullable=True)
    total_synced_items = Column(Integer, default=0, nullable=False)
    total_conflicts = Column(Integer, default=0, nullable=False)
    total_failed_items = Column(Integer, default=0, nullable=False)

    device_count = Column(Integer, default=1, nullable=False)
    network_quality = Column(String(20), default='GOOD', nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_sync_metadata_user', 'user_id'),
        Index('idx_sync_metadata_updated', 'updated_at'),
    )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'last_sync_timestamp': self.last_sync_timestamp.isoformat() if self.last_sync_timestamp else None,
            'last_conflict_check': self.last_conflict_check.isoformat() if self.last_conflict_check else None,
            'total_synced_items': self.total_synced_items,
            'total_conflicts': self.total_conflicts,
            'total_failed_items': self.total_failed_items,
            'device_count': self.device_count,
            'network_quality': self.network_quality,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
