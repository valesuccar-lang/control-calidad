"""
SQLAlchemy Models — Control de Calidad Textil
Base ORM models for PostgreSQL persistence
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Float, DateTime, Enum, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from enum import Enum as PyEnum
import uuid

Base = declarative_base()


# ============================================================================
# ENUMS
# ============================================================================

class RoleEnum(str, PyEnum):
    OPERARIO = "OPERARIO"
    SUPERVISOR = "SUPERVISOR"
    JEFE_QA = "JEFE_QA"
    GERENTE = "GERENTE"
    ADMIN = "ADMIN"


class InspectionStatusEnum(str, PyEnum):
    DRAFT = "DRAFT"
    REGISTERED = "REGISTERED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ApprovalStatusEnum(str, PyEnum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class LoteStatusEnum(str, PyEnum):
    PENDING = "PENDING"
    IN_PROCESS = "IN_PROCESS"
    REPROCESSED = "REPROCESSED"
    APPROVED = "APPROVED"


# ============================================================================
# USER MODEL
# ============================================================================

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.OPERARIO, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    inspections = relationship("Inspection", back_populates="analista", foreign_keys="Inspection.analista_id")
    approvals = relationship("Approval", back_populates="jefe_qa", foreign_keys="Approval.jefe_qa_id")

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


# ============================================================================
# MASTER DATA MODELS
# ============================================================================

class Defect(Base):
    __tablename__ = "defects"

    id = Column(String(50), primary_key=True)  # DEF-TON
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    typical_process = Column(String(100), nullable=True)  # TINTORERIA, TEÑIDO, etc.
    typical_machine_id = Column(String(50), ForeignKey("machines.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    inspections = relationship("Inspection", back_populates="defect_type")
    typical_machine = relationship("Machine", back_populates="typical_defects")

    def __repr__(self):
        return f"<Defect {self.id}: {self.name}>"


class Machine(Base):
    __tablename__ = "machines"

    id = Column(String(50), primary_key=True)  # MAQ-AGO-80
    name = Column(String(255), unique=True, nullable=False, index=True)
    process = Column(String(100), nullable=True)  # AGOTAMIENTO, TINTORERIA, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    inspections = relationship("Inspection", back_populates="machine_culpable")
    typical_defects = relationship("Defect", back_populates="typical_machine")

    def __repr__(self):
        return f"<Machine {self.id}: {self.name}>"


class Fabric(Base):
    __tablename__ = "fabrics"

    id = Column(String(50), primary_key=True)  # NOVAKREPEL
    name = Column(String(255), unique=True, nullable=False, index=True)
    composition = Column(String(255), nullable=True)  # 100% Poliéster, Algodón, etc.
    width_cm = Column(Float, nullable=True)
    weight_gsm = Column(Float, nullable=True)  # grams per square meter
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lotes = relationship("Lote", back_populates="fabric")

    def __repr__(self):
        return f"<Fabric {self.id}: {self.name}>"


# ============================================================================
# CORE DOMAIN MODELS
# ============================================================================

class Lote(Base):
    __tablename__ = "lotes"

    id = Column(String(50), primary_key=True)  # HDR-12847
    fabric_id = Column(String(50), ForeignKey("fabrics.id"), nullable=False, index=True)
    quantity_meters = Column(Float, nullable=False)
    status = Column(Enum(LoteStatusEnum), default=LoteStatusEnum.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    fabric = relationship("Fabric", back_populates="lotes")
    inspections = relationship("Inspection", back_populates="lote", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Lote {self.id} ({self.status})>"


class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lote_id = Column(String(50), ForeignKey("lotes.id"), nullable=False, index=True)
    analista_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    defect_type_id = Column(String(50), ForeignKey("defects.id"), nullable=False)
    machine_culpable_id = Column(String(50), ForeignKey("machines.id"), nullable=True)
    comment = Column(Text, nullable=False)
    photo_path = Column(String(500), nullable=True)  # Local file path or URL
    status = Column(Enum(InspectionStatusEnum), default=InspectionStatusEnum.REGISTERED)
    synced = Column(Boolean, default=True)  # Was this created offline and synced?
    check_in = Column(DateTime, default=datetime.utcnow, nullable=False)
    check_out = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lote = relationship("Lote", back_populates="inspections")
    analista = relationship("User", back_populates="inspections", foreign_keys=[analista_id])
    defect_type = relationship("Defect", back_populates="inspections")
    machine_culpable = relationship("Machine", back_populates="inspections")
    approval = relationship("Approval", back_populates="inspection", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Inspection {str(self.id)[:8]} ({self.status})>"


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inspection_id = Column(UUID(as_uuid=True), ForeignKey("inspections.id"), nullable=False, unique=True, index=True)
    jefe_qa_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(Enum(ApprovalStatusEnum), nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    inspection = relationship("Inspection", back_populates="approval")
    jefe_qa = relationship("User", back_populates="approvals", foreign_keys=[jefe_qa_id])

    def __repr__(self):
        return f"<Approval {str(self.id)[:8]} ({self.status})>"


# ============================================================================
# INDEXES FOR PERFORMANCE
# ============================================================================

# Created in SQLAlchemy via the models above
# Additional indexes can be added with:
# CREATE INDEX idx_inspections_synced ON inspections(synced) WHERE synced = FALSE;
# CREATE INDEX idx_approvals_status ON approvals(status);
