"""SQLAlchemy ORM models for all 8 tables"""
from sqlalchemy import (
    Column, String, Integer, Text, TIMESTAMP, ForeignKey,
    CheckConstraint, UniqueConstraint, Index, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from datetime import datetime
from uuid import uuid4
import enum

from app.models.base import BaseModel, Base


class UserRole(str, enum.Enum):
    """User roles for RBAC"""
    ANALISTA = "ANALISTA"
    JEFE_QA = "JEFE_QA"
    ADMIN = "ADMIN"
    GERENTE = "GERENTE"


class LoteStatus(str, enum.Enum):
    """Production batch status"""
    PENDING = "PENDING"
    IN_PROCESS = "IN_PROCESS"
    INSPECTED = "INSPECTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class SyncStatus(str, enum.Enum):
    """Synchronization status"""
    PENDING = "PENDING"
    SYNCED = "SYNCED"
    SYNC_FAILED = "SYNC_FAILED"


class ApprovalStatus(str, enum.Enum):
    """Approval decision status"""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# ==================== TABLE 1: USERS ====================
class User(BaseModel):
    """User accounts with RBAC"""
    __tablename__ = "users"

    id = Column(String(50), primary_key=True, default=lambda: str(uuid4()))
    email = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(200), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    roles = Column(ARRAY(String), nullable=False, default=["ANALISTA"])
    status = Column(String(20), default="ACTIVE", nullable=False)

    __table_args__ = (
        CheckConstraint("email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$'", name="valid_email"),
    )


# ==================== TABLE 2: FABRICS ====================
class Fabric(BaseModel):
    """Fabric types (masters data)"""
    __tablename__ = "fabrics"

    fabric_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    status = Column(String(20), default="ACTIVE", nullable=False, index=True)


# ==================== TABLE 3: LOTES ====================
class Lote(BaseModel):
    """Production batches (HDR-12847)"""
    __tablename__ = "lotes"

    lote_id = Column(String(50), primary_key=True)
    fabric_id = Column(String(50), ForeignKey("fabrics.fabric_id"), nullable=False)
    quantity = Column(Integer, nullable=False, index=True)
    status = Column(String(20), default="PENDING", nullable=False, index=True)

    __table_args__ = (
        CheckConstraint("quantity > 0", name="positive_quantity"),
        Index("idx_lotes_status", "status"),
        Index("idx_lotes_fabric_id", "fabric_id"),
    )

    fabric = relationship("Fabric")


# ==================== TABLE 4: MACHINES ====================
class Machine(BaseModel):
    """Production machines (masters data)"""
    __tablename__ = "machines"

    machine_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    model = Column(String(100))
    status = Column(String(20), default="ACTIVE", nullable=False, index=True)


# ==================== TABLE 5: DEFECTS ====================
class Defect(BaseModel):
    """Defect types (masters data)"""
    __tablename__ = "defects"

    defect_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), default="MEDIUM")
    status = Column(String(20), default="ACTIVE", nullable=False, index=True)


# ==================== TABLE 6: INSPECTIONS ====================
class Inspection(BaseModel):
    """Defect inspection records"""
    __tablename__ = "inspections"

    inspection_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, unique=True, index=True)
    lote_id = Column(String(50), ForeignKey("lotes.lote_id"), nullable=False, index=True)
    analista_id = Column(String(50), ForeignKey("users.id"), nullable=False, index=True)
    defect_id = Column(String(50), ForeignKey("defects.defect_id"), nullable=False)
    comment_text = Column(String(500), nullable=False)
    photo_path = Column(String(500), nullable=False)
    photo_checksum = Column(String(64), nullable=False)  # SHA256
    machine_id = Column(String(50), ForeignKey("machines.machine_id"), nullable=False)

    # Timestamps
    check_in = Column(TIMESTAMP, nullable=False)
    check_out = Column(TIMESTAMP)
    elapsed_seconds = Column(Integer)

    # Sync status
    sync_status = Column(SQLEnum(SyncStatus), default=SyncStatus.PENDING, nullable=False, index=True)
    sync_attempts = Column(Integer, default=0)
    last_sync_error = Column(String(500))

    __table_args__ = (
        CheckConstraint("char_length(comment_text) >= 10", name="min_comment_length"),
        Index("idx_inspections_lote_id", "lote_id"),
        Index("idx_inspections_analista_id_created", "analista_id", "created_at"),
        Index("idx_inspections_sync_status_pending", "sync_status", postgresql_where="sync_status = 'PENDING'"),
        UniqueConstraint("inspection_id", name="uq_inspection_id"),
    )

    lote = relationship("Lote")
    analista = relationship("User")
    defect = relationship("Defect")
    machine = relationship("Machine")


# ==================== TABLE 7: APPROVALS ====================
class Approval(BaseModel):
    """Inspection approval/rejection records"""
    __tablename__ = "approvals"

    approval_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, unique=True, index=True)
    inspection_id = Column(UUID(as_uuid=True), ForeignKey("inspections.inspection_id"), nullable=False, unique=True, index=True)
    jefe_qa_id = Column(String(50), ForeignKey("users.id"), nullable=False, index=True)

    decision = Column(SQLEnum(ApprovalStatus), nullable=False, index=True)
    rejection_reason = Column(String(500))
    notes = Column(Text)

    approved_at = Column(TIMESTAMP, nullable=False, default=func.now())

    __table_args__ = (
        CheckConstraint(
            "(decision = 'REJECTED' AND rejection_reason IS NOT NULL) OR decision = 'APPROVED'",
            name="rejection_reason_required"
        ),
        Index("idx_approvals_inspection_id", "inspection_id"),
        Index("idx_approvals_jefe_qa_id", "jefe_qa_id"),
        Index("idx_approvals_decision", "decision"),
    )

    inspection = relationship("Inspection")
    jefe_qa = relationship("User")


# ==================== TABLE 8: AUDIT_LOGS ====================
class AuditLog(BaseModel):
    """Structured audit events"""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String(50), ForeignKey("users.id"), index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(100), nullable=False, index=True)
    details = Column(Text)  # JSON string
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    status = Column(String(20), default="SUCCESS", nullable=False)
    error_message = Column(String(500))

    __table_args__ = (
        Index("idx_audit_logs_timestamp", "created_at"),
        Index("idx_audit_logs_user_action", "user_id", "action"),
        Index("idx_audit_logs_entity", "entity_type", "entity_id"),
    )

    user = relationship("User")


# Import func for timestamps
from sqlalchemy import func
