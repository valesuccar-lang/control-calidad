# backend/app/models.py
# SQLAlchemy ORM Models for Masters & Configuration Domain

from datetime import datetime
from typing import Optional
from enum import Enum
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime,
    Text, Numeric, Date, ForeignKey, Index, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class StatusEnum(str, Enum):
    """Status values for all master entities"""
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class ProcessEnum(str, Enum):
    """Valid manufacturing processes"""
    TEÑIDO = "TEÑIDO"
    ESTAMPADO = "ESTAMPADO"
    ACABADO = "ACABADO"
    OTRA = "OTRA"


class Defect(Base):
    """
    Defect Master Entity
    Represents a type of defect found in fabric inspections
    """
    __tablename__ = "defects"

    id = Column(String(100), primary_key=True)  # e.g., "DEF-00001"
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    typical_process = Column(SQLEnum(ProcessEnum), nullable=False, default=ProcessEnum.OTRA)
    typical_machine_id = Column(String(100), ForeignKey("machines.id"), nullable=True)

    status = Column(SQLEnum(StatusEnum), nullable=False, default=StatusEnum.ACTIVE)
    is_system = Column(Boolean, nullable=False, default=False)
    version = Column(Integer, nullable=False, default=1)

    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_by = Column(String(100), nullable=True)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    # Relationships
    typical_machine = relationship("Machine", foreign_keys=[typical_machine_id], lazy="joined")

    # Indexes
    __table_args__ = (
        Index("idx_defects_name", "name"),
        Index("idx_defects_name_lower", "name", postgresql_using="btree",
              postgresql_where="is_system = false"),
        Index("idx_defects_status_created", "status", "created_at"),
        Index("idx_defects_is_system", "is_system"),
    )

    def to_dict(self):
        """Convert to dictionary for JSON response"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "typical_process": self.typical_process.value if self.typical_process else None,
            "typical_machine_id": self.typical_machine_id,
            "typical_machine_name": self.typical_machine.name if self.typical_machine else None,
            "status": self.status.value,
            "is_system": self.is_system,
            "version": self.version,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_by": self.updated_by,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Defect(id={self.id}, name={self.name}, status={self.status})>"


class Machine(Base):
    """
    Machine Master Entity
    Represents a manufacturing machine/equipment
    """
    __tablename__ = "machines"

    id = Column(String(100), primary_key=True)  # e.g., "MAQ-TINT-01"
    name = Column(String(100), nullable=False, unique=True)
    process = Column(SQLEnum(ProcessEnum), nullable=False)
    manufacturer = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    installation_date = Column(Date, nullable=True)

    status = Column(SQLEnum(StatusEnum), nullable=False, default=StatusEnum.ACTIVE)
    is_system = Column(Boolean, nullable=False, default=False)
    version = Column(Integer, nullable=False, default=1)

    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_by = Column(String(100), nullable=True)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_machines_name", "name"),
        Index("idx_machines_name_lower", "name", postgresql_using="btree",
              postgresql_where="is_system = false"),
        Index("idx_machines_status", "status"),
        Index("idx_machines_process", "process"),
        Index("idx_machines_is_system", "is_system"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "process": self.process.value if self.process else None,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "installation_date": self.installation_date.isoformat() if self.installation_date else None,
            "status": self.status.value,
            "is_system": self.is_system,
            "version": self.version,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_by": self.updated_by,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Machine(id={self.id}, name={self.name}, process={self.process})>"


class Fabric(Base):
    """
    Fabric Master Entity
    Represents a type of fabric with composition and specifications
    """
    __tablename__ = "fabrics"

    id = Column(String(100), primary_key=True)  # e.g., "FAB-00001"
    name = Column(String(100), nullable=False, unique=True)
    composition = Column(String(200), nullable=False)  # e.g., "Cotton 50%, Polyester 50%"
    width_cm = Column(Numeric(5, 2), nullable=False)  # Range: 10-300 cm
    weight_gsm = Column(Numeric(6, 2), nullable=False)  # Range: 50-1000 g/m²

    status = Column(SQLEnum(StatusEnum), nullable=False, default=StatusEnum.ACTIVE)
    is_system = Column(Boolean, nullable=False, default=False)
    version = Column(Integer, nullable=False, default=1)

    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_by = Column(String(100), nullable=True)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_fabrics_name", "name"),
        Index("idx_fabrics_name_lower", "name", postgresql_using="btree",
              postgresql_where="is_system = false"),
        Index("idx_fabrics_status", "status"),
        Index("idx_fabrics_is_system", "is_system"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "composition": self.composition,
            "width_cm": float(self.width_cm),
            "weight_gsm": float(self.weight_gsm),
            "status": self.status.value,
            "is_system": self.is_system,
            "version": self.version,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_by": self.updated_by,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Fabric(id={self.id}, name={self.name}, composition={self.composition})>"


class AuditLog(Base):
    """
    Immutable audit trail for all changes to master entities
    """
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)  # 'defect', 'machine', 'fabric'
    entity_id = Column(String(100), nullable=False)
    operation = Column(String(20), nullable=False)  # 'INSERT', 'UPDATE', 'DELETE'
    old_values = Column(Text, nullable=True)  # JSON string
    new_values = Column(Text, nullable=True)  # JSON string
    user_id = Column(String(100), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    trace_id = Column(String(100), nullable=True)  # For request correlation

    # Indexes for audit queries
    __table_args__ = (
        Index("idx_audit_entity", "entity_id"),
        Index("idx_audit_timestamp", "timestamp"),
        Index("idx_audit_user_timestamp", "user_id", "timestamp"),
        Index("idx_audit_entity_type", "entity_type"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "operation": self.operation,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "trace_id": self.trace_id,
        }

    def __repr__(self):
        return f"<AuditLog(id={self.id}, entity={self.entity_type}:{self.entity_id}, op={self.operation})>"


class ImportJob(Base):
    """
    Tracks CSV import job state for progress tracking
    """
    __tablename__ = "import_jobs"

    id = Column(String(100), primary_key=True)  # Job ID from Celery
    master_type = Column(String(50), nullable=False)  # 'defect', 'machine', 'fabric'
    filename = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)  # 'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'
    total_rows = Column(Integer, nullable=False)
    processed_rows = Column(Integer, nullable=False, default=0)
    error_count = Column(Integer, nullable=False, default=0)
    error_details = Column(Text, nullable=True)  # JSON array of errors

    import_mode = Column(String(50), nullable=False)  # 'skip_duplicates', 'upsert'
    user_id = Column(String(100), nullable=False)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    def duration_seconds(self) -> Optional[float]:
        """Calculate import duration in seconds"""
        if self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds()
        return None

    def to_dict(self):
        return {
            "id": self.id,
            "master_type": self.master_type,
            "filename": self.filename,
            "status": self.status,
            "total_rows": self.total_rows,
            "processed_rows": self.processed_rows,
            "error_count": self.error_count,
            "import_mode": self.import_mode,
            "user_id": self.user_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds(),
        }

    def __repr__(self):
        return f"<ImportJob(id={self.id}, status={self.status}, progress={self.processed_rows}/{self.total_rows})>"
