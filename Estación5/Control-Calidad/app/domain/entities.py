"""Domain entities - pure business logic aggregates"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class DefectType(Enum):
    """Defect type value object"""
    TEAR = "TEAR"
    STAIN = "STAIN"
    COLOR_VARIATION = "COLOR_VARIATION"
    WEAVING_ERROR = "WEAVING_ERROR"
    SHRINKAGE = "SHRINKAGE"


class SyncStatus(Enum):
    """Synchronization status"""
    PENDING = "PENDING"
    SYNCED = "SYNCED"
    SYNC_FAILED = "SYNC_FAILED"


@dataclass(frozen=True)
class Comment:
    """Comment value object - immutable"""
    text: str

    def __post_init__(self):
        if not (10 <= len(self.text) <= 500):
            raise ValueError("Comment must be between 10 and 500 characters")


@dataclass(frozen=True)
class Photograph:
    """Photo value object - immutable"""
    file_path: str
    checksum: str
    size_kb: int
    synced: bool = False

    def __post_init__(self):
        if self.size_kb > 500:
            raise ValueError("Photo size must not exceed 500 KB")
        if len(self.checksum) != 64:
            raise ValueError("Checksum must be SHA256 (64 hex chars)")


@dataclass(frozen=True)
class InspectionTime:
    """Inspection timing value object - immutable"""
    check_in: datetime
    check_out: Optional[datetime] = None

    @property
    def elapsed_seconds(self) -> int:
        if self.check_out is None:
            return 0
        return int((self.check_out - self.check_in).total_seconds())


@dataclass
class Inspection:
    """Inspection aggregate root"""
    inspection_id: UUID
    lote_id: str
    analista_id: str
    defect_id: str
    comment: Comment
    photograph: Photograph
    machine_id: str
    inspection_time: InspectionTime
    sync_status: SyncStatus = SyncStatus.PENDING
    created_at: Optional[datetime] = None

    def mark_synced(self):
        """Mark inspection as successfully synced"""
        self.sync_status = SyncStatus.SYNCED

    def mark_sync_failed(self):
        """Mark inspection sync as failed"""
        self.sync_status = SyncStatus.SYNC_FAILED

    def to_dict(self):
        return {
            "inspection_id": str(self.inspection_id),
            "lote_id": self.lote_id,
            "analista_id": self.analista_id,
            "defect_id": self.defect_id,
            "comment": self.comment.text,
            "photo_path": self.photograph.file_path,
            "photo_checksum": self.photograph.checksum,
            "machine_id": self.machine_id,
            "check_in": self.inspection_time.check_in.isoformat(),
            "check_out": self.inspection_time.check_out.isoformat() if self.inspection_time.check_out else None,
            "elapsed_seconds": self.inspection_time.elapsed_seconds,
            "sync_status": self.sync_status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class Approval:
    """Approval aggregate root"""
    approval_id: UUID
    inspection_id: UUID
    jefe_qa_id: str
    decision: str  # "APPROVED" or "REJECTED"
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None
    approved_at: Optional[datetime] = None

    def validate(self):
        """Validate business rules"""
        if self.decision not in ("APPROVED", "REJECTED"):
            raise ValueError("Decision must be APPROVED or REJECTED")

        if self.decision == "REJECTED" and not self.rejection_reason:
            raise ValueError("Rejection reason is required when rejecting")

    def to_dict(self):
        return {
            "approval_id": str(self.approval_id),
            "inspection_id": str(self.inspection_id),
            "jefe_qa_id": self.jefe_qa_id,
            "decision": self.decision,
            "rejection_reason": self.rejection_reason,
            "notes": self.notes,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
        }


@dataclass
class Lote:
    """Production batch aggregate root"""
    lote_id: str
    fabric_id: str
    quantity: int
    status: str = "PENDING"
    created_at: Optional[datetime] = None

    def validate(self):
        """Validate business rules"""
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")

        if self.status not in ("PENDING", "IN_PROCESS", "INSPECTED", "APPROVED", "REJECTED"):
            raise ValueError("Invalid status")

    def to_dict(self):
        return {
            "lote_id": self.lote_id,
            "fabric_id": self.fabric_id,
            "quantity": self.quantity,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
