# backend/app/services/masters.py
# Business logic for masters domain

import json
from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
import structlog

from app.models import Defect, Machine, Fabric, StatusEnum, AuditLog
from app.repositories import DefectRepository, MachineRepository, FabricRepository, AuditLogRepository
from app.schemas import DefectCreate, DefectUpdate, MachineCreate, MachineUpdate, FabricCreate, FabricUpdate

logger = structlog.get_logger(__name__)


class DuplicateError(Exception):
    """Raised when attempting to create duplicate master"""
    pass


class ValidationError(Exception):
    """Raised on business logic validation failure"""
    pass


class ArchiveError(ValidationError):
    """Raised when archive is not allowed"""
    pass


class NotFoundError(Exception):
    """Raised when entity not found"""
    pass


class MastersService:
    """Service for managing master data (Defects, Machines, Fabrics)"""

    def __init__(self, db: Session):
        self.db = db
        self.defect_repo = DefectRepository(db)
        self.machine_repo = MachineRepository(db)
        self.fabric_repo = FabricRepository(db)
        self.audit_repo = AuditLogRepository(db)

    # ==================== DEFECT OPERATIONS ====================

    def create_defect(self, payload: DefectCreate, user_id: str, trace_id: Optional[str] = None) -> Defect:
        """Create new defect with validation"""
        logger.info(
            'defect_create_start',
            name=payload.name,
            user_id=user_id,
            trace_id=trace_id
        )

        # Validate uniqueness
        if self.defect_repo.exists_by_name(payload.name):
            logger.warning('defect_duplicate', name=payload.name)
            raise DuplicateError(f"Defect '{payload.name}' already exists")

        # Validate machine reference if provided
        if payload.typical_machine_id:
            machine = self.machine_repo.get_by_id(payload.typical_machine_id)
            if not machine or machine.status == StatusEnum.ARCHIVED:
                logger.warning('defect_machine_not_found', machine_id=payload.typical_machine_id)
                raise ValidationError(f"Machine '{payload.typical_machine_id}' not found or archived")

        # Create entity
        defect = Defect(
            id=self._generate_id('DEF'),
            name=payload.name,
            description=payload.description,
            typical_process=payload.typical_process,
            typical_machine_id=payload.typical_machine_id,
            status=StatusEnum.ACTIVE,
            is_system=False,
            version=1,
            created_by=user_id
        )

        # Persist
        saved = self.defect_repo.save(defect)

        # Audit log
        self.audit_repo.save(
            entity_type='defect',
            entity_id=saved.id,
            operation='INSERT',
            old_values=None,
            new_values=json.dumps(saved.to_dict()),
            user_id=user_id,
            trace_id=trace_id
        )

        self.db.commit()

        logger.info(
            'defect_created',
            defect_id=saved.id,
            name=payload.name,
            user_id=user_id,
            trace_id=trace_id
        )

        return saved

    def update_defect(self, defect_id: str, payload: DefectUpdate, user_id: str,
                      trace_id: Optional[str] = None) -> Defect:
        """Update defect with version check (optimistic locking)"""
        logger.info('defect_update_start', defect_id=defect_id, version=payload.version, trace_id=trace_id)

        # Fetch current
        defect = self.defect_repo.get_by_id(defect_id)
        if not defect:
            logger.error('defect_not_found', defect_id=defect_id)
            raise NotFoundError(f"Defect '{defect_id}' not found")

        # Check system protection
        if defect.is_system:
            logger.warning('defect_system_protected', defect_id=defect_id)
            raise ValidationError("Cannot modify system defect")

        # Version check (optimistic locking)
        if defect.version != payload.version:
            logger.warning(
                'defect_version_conflict',
                defect_id=defect_id,
                expected_version=payload.version,
                actual_version=defect.version
            )
            raise ValidationError("Defect was modified by another user. Refresh and retry.")

        # Validate name uniqueness if changing
        if payload.name and payload.name != defect.name:
            if self.defect_repo.exists_by_name(payload.name, exclude_id=defect_id):
                logger.warning('defect_duplicate_update', name=payload.name)
                raise DuplicateError(f"Defect '{payload.name}' already exists")

        # Store old values for audit
        old_values = json.dumps(defect.to_dict())

        # Update fields
        if payload.name:
            defect.name = payload.name
        if payload.description is not None:
            defect.description = payload.description
        if payload.typical_process:
            defect.typical_process = payload.typical_process
        if payload.typical_machine_id:
            machine = self.machine_repo.get_by_id(payload.typical_machine_id)
            if not machine or machine.status == StatusEnum.ARCHIVED:
                raise ValidationError(f"Machine '{payload.typical_machine_id}' not found or archived")
            defect.typical_machine_id = payload.typical_machine_id

        # Increment version
        defect.version += 1
        defect.updated_by = user_id
        defect.updated_at = datetime.utcnow()

        self.db.flush()

        # Audit log
        self.audit_repo.save(
            entity_type='defect',
            entity_id=defect.id,
            operation='UPDATE',
            old_values=old_values,
            new_values=json.dumps(defect.to_dict()),
            user_id=user_id,
            trace_id=trace_id
        )

        self.db.commit()

        logger.info(
            'defect_updated',
            defect_id=defect_id,
            new_version=defect.version,
            user_id=user_id,
            trace_id=trace_id
        )

        return defect

    def archive_defect(self, defect_id: str, reason: Optional[str], user_id: str,
                       trace_id: Optional[str] = None) -> Defect:
        """Archive defect with validation checks"""
        logger.info('defect_archive_start', defect_id=defect_id, user_id=user_id, trace_id=trace_id)

        defect = self.defect_repo.get_by_id(defect_id)
        if not defect:
            raise NotFoundError(f"Defect '{defect_id}' not found")

        # Check system protection
        if defect.is_system:
            logger.warning('defect_system_protected_archive', defect_id=defect_id)
            raise ArchiveError("Cannot archive system defect")

        # Check recent usage (7 days)
        recent_usage = self.defect_repo.count_recent_usage(defect_id, days=7)
        if recent_usage > 0:
            logger.warning(
                'defect_recent_usage',
                defect_id=defect_id,
                usage_count=recent_usage,
                days=7
            )
            raise ArchiveError(
                f"Cannot archive; defect was used {recent_usage} times in last 7 days"
            )

        # Store old values
        old_values = json.dumps(defect.to_dict())

        # Archive
        defect.status = StatusEnum.ARCHIVED
        defect.updated_by = user_id
        defect.updated_at = datetime.utcnow()

        self.db.flush()

        # Audit with reason
        audit_notes = {'reason': reason} if reason else {}
        self.audit_repo.save(
            entity_type='defect',
            entity_id=defect.id,
            operation='UPDATE',
            old_values=old_values,
            new_values=json.dumps(defect.to_dict()),
            user_id=user_id,
            trace_id=trace_id
        )

        self.db.commit()

        logger.info(
            'defect_archived',
            defect_id=defect_id,
            reason=reason,
            user_id=user_id,
            trace_id=trace_id
        )

        return defect

    def get_defect(self, defect_id: str) -> Optional[Defect]:
        """Get defect by ID"""
        return self.defect_repo.get_by_id(defect_id)

    def list_defects(self, skip: int = 0, limit: int = 20,
                     include_archived: bool = False) -> Tuple[List[Defect], int]:
        """List defects with pagination"""
        if include_archived:
            return self.defect_repo.get_all(skip, limit, include_archived=True)
        return self.defect_repo.get_all_active(skip, limit)

    # ==================== MACHINE OPERATIONS ====================

    def create_machine(self, payload: MachineCreate, user_id: str,
                       trace_id: Optional[str] = None) -> Machine:
        """Create new machine"""
        logger.info('machine_create_start', name=payload.name, user_id=user_id, trace_id=trace_id)

        if self.machine_repo.exists_by_name(payload.name):
            raise DuplicateError(f"Machine '{payload.name}' already exists")

        machine = Machine(
            id=self._generate_id('MAQ'),
            name=payload.name,
            process=payload.process,
            manufacturer=payload.manufacturer,
            model=payload.model,
            installation_date=payload.installation_date,
            status=StatusEnum.ACTIVE,
            is_system=False,
            version=1,
            created_by=user_id
        )

        saved = self.machine_repo.save(machine)

        self.audit_repo.save(
            entity_type='machine',
            entity_id=saved.id,
            operation='INSERT',
            old_values=None,
            new_values=json.dumps(saved.to_dict()),
            user_id=user_id,
            trace_id=trace_id
        )

        self.db.commit()

        logger.info('machine_created', machine_id=saved.id, name=payload.name, user_id=user_id)

        return saved

    def update_machine(self, machine_id: str, payload: MachineUpdate, user_id: str,
                       trace_id: Optional[str] = None) -> Machine:
        """Update machine with version check"""
        logger.info('machine_update_start', machine_id=machine_id, version=payload.version)

        machine = self.machine_repo.get_by_id(machine_id)
        if not machine:
            raise NotFoundError(f"Machine '{machine_id}' not found")

        if machine.is_system:
            raise ValidationError("Cannot modify system machine")

        if machine.version != payload.version:
            raise ValidationError("Machine was modified by another user. Refresh and retry.")

        old_values = json.dumps(machine.to_dict())

        if payload.name and payload.name != machine.name:
            if self.machine_repo.exists_by_name(payload.name, exclude_id=machine_id):
                raise DuplicateError(f"Machine '{payload.name}' already exists")
            machine.name = payload.name

        if payload.process:
            machine.process = payload.process
        if payload.manufacturer is not None:
            machine.manufacturer = payload.manufacturer
        if payload.model is not None:
            machine.model = payload.model
        if payload.installation_date is not None:
            machine.installation_date = payload.installation_date

        machine.version += 1
        machine.updated_by = user_id
        machine.updated_at = datetime.utcnow()

        self.db.flush()

        self.audit_repo.save(
            entity_type='machine',
            entity_id=machine.id,
            operation='UPDATE',
            old_values=old_values,
            new_values=json.dumps(machine.to_dict()),
            user_id=user_id,
            trace_id=trace_id
        )

        self.db.commit()

        logger.info('machine_updated', machine_id=machine_id, new_version=machine.version)

        return machine

    def archive_machine(self, machine_id: str, reason: Optional[str], user_id: str,
                        trace_id: Optional[str] = None) -> Machine:
        """Archive machine with validation"""
        logger.info('machine_archive_start', machine_id=machine_id)

        machine = self.machine_repo.get_by_id(machine_id)
        if not machine:
            raise NotFoundError(f"Machine '{machine_id}' not found")

        if machine.is_system:
            raise ArchiveError("Cannot archive system machine")

        recent_usage = self.machine_repo.count_recent_usage(machine_id, days=7)
        if recent_usage > 0:
            raise ArchiveError(f"Cannot archive; machine was used {recent_usage} times in last 7 days")

        old_values = json.dumps(machine.to_dict())

        machine.status = StatusEnum.ARCHIVED
        machine.updated_by = user_id
        machine.updated_at = datetime.utcnow()

        self.db.flush()

        self.audit_repo.save(
            entity_type='machine',
            entity_id=machine.id,
            operation='UPDATE',
            old_values=old_values,
            new_values=json.dumps(machine.to_dict()),
            user_id=user_id,
            trace_id=trace_id
        )

        self.db.commit()

        logger.info('machine_archived', machine_id=machine_id, user_id=user_id)

        return machine

    def get_machine(self, machine_id: str) -> Optional[Machine]:
        """Get machine by ID"""
        return self.machine_repo.get_by_id(machine_id)

    def list_machines(self, skip: int = 0, limit: int = 20,
                      include_archived: bool = False) -> Tuple[List[Machine], int]:
        """List machines with pagination"""
        if include_archived:
            return self.machine_repo.get_all(skip, limit, include_archived=True)
        return self.machine_repo.get_all_active(skip, limit)

    # ==================== FABRIC OPERATIONS ====================

    def create_fabric(self, payload: FabricCreate, user_id: str,
                      trace_id: Optional[str] = None) -> Fabric:
        """Create new fabric"""
        logger.info('fabric_create_start', name=payload.name, user_id=user_id)

        if self.fabric_repo.exists_by_name(payload.name):
            raise DuplicateError(f"Fabric '{payload.name}' already exists")

        fabric = Fabric(
            id=self._generate_id('FAB'),
            name=payload.name,
            composition=payload.composition,
            width_cm=payload.width_cm,
            weight_gsm=payload.weight_gsm,
            status=StatusEnum.ACTIVE,
            is_system=False,
            version=1,
            created_by=user_id
        )

        saved = self.fabric_repo.save(fabric)

        self.audit_repo.save(
            entity_type='fabric',
            entity_id=saved.id,
            operation='INSERT',
            old_values=None,
            new_values=json.dumps(saved.to_dict()),
            user_id=user_id,
            trace_id=trace_id
        )

        self.db.commit()

        logger.info('fabric_created', fabric_id=saved.id, name=payload.name, user_id=user_id)

        return saved

    def update_fabric(self, fabric_id: str, payload: FabricUpdate, user_id: str,
                      trace_id: Optional[str] = None) -> Fabric:
        """Update fabric with version check"""
        logger.info('fabric_update_start', fabric_id=fabric_id, version=payload.version)

        fabric = self.fabric_repo.get_by_id(fabric_id)
        if not fabric:
            raise NotFoundError(f"Fabric '{fabric_id}' not found")

        if fabric.is_system:
            raise ValidationError("Cannot modify system fabric")

        if fabric.version != payload.version:
            raise ValidationError("Fabric was modified by another user. Refresh and retry.")

        old_values = json.dumps(fabric.to_dict())

        if payload.name and payload.name != fabric.name:
            if self.fabric_repo.exists_by_name(payload.name, exclude_id=fabric_id):
                raise DuplicateError(f"Fabric '{payload.name}' already exists")
            fabric.name = payload.name

        if payload.composition:
            fabric.composition = payload.composition
        if payload.width_cm:
            fabric.width_cm = payload.width_cm
        if payload.weight_gsm:
            fabric.weight_gsm = payload.weight_gsm

        fabric.version += 1
        fabric.updated_by = user_id
        fabric.updated_at = datetime.utcnow()

        self.db.flush()

        self.audit_repo.save(
            entity_type='fabric',
            entity_id=fabric.id,
            operation='UPDATE',
            old_values=old_values,
            new_values=json.dumps(fabric.to_dict()),
            user_id=user_id,
            trace_id=trace_id
        )

        self.db.commit()

        logger.info('fabric_updated', fabric_id=fabric_id, new_version=fabric.version)

        return fabric

    def archive_fabric(self, fabric_id: str, reason: Optional[str], user_id: str,
                       trace_id: Optional[str] = None) -> Fabric:
        """Archive fabric with validation"""
        logger.info('fabric_archive_start', fabric_id=fabric_id)

        fabric = self.fabric_repo.get_by_id(fabric_id)
        if not fabric:
            raise NotFoundError(f"Fabric '{fabric_id}' not found")

        if fabric.is_system:
            raise ArchiveError("Cannot archive system fabric")

        recent_usage = self.fabric_repo.count_recent_usage(fabric_id, days=7)
        if recent_usage > 0:
            raise ArchiveError(f"Cannot archive; fabric was used {recent_usage} times in last 7 days")

        old_values = json.dumps(fabric.to_dict())

        fabric.status = StatusEnum.ARCHIVED
        fabric.updated_by = user_id
        fabric.updated_at = datetime.utcnow()

        self.db.flush()

        self.audit_repo.save(
            entity_type='fabric',
            entity_id=fabric.id,
            operation='UPDATE',
            old_values=old_values,
            new_values=json.dumps(fabric.to_dict()),
            user_id=user_id,
            trace_id=trace_id
        )

        self.db.commit()

        logger.info('fabric_archived', fabric_id=fabric_id, user_id=user_id)

        return fabric

    def get_fabric(self, fabric_id: str) -> Optional[Fabric]:
        """Get fabric by ID"""
        return self.fabric_repo.get_by_id(fabric_id)

    def list_fabrics(self, skip: int = 0, limit: int = 20,
                     include_archived: bool = False) -> Tuple[List[Fabric], int]:
        """List fabrics with pagination"""
        if include_archived:
            return self.fabric_repo.get_all(skip, limit, include_archived=True)
        return self.fabric_repo.get_all_active(skip, limit)

    # ==================== UTILITY METHODS ====================

    @staticmethod
    def _generate_id(prefix: str) -> str:
        """Generate unique ID (simple counter-based)"""
        # In production, use proper ID generation strategy
        # Could use UUID, nanoid, or database sequence
        import uuid
        return f"{prefix}-{str(uuid.uuid4())[:8].upper()}"

    def get_audit_trail(self, entity_id: str, skip: int = 0, limit: int = 50) -> Tuple[List[AuditLog], int]:
        """Get audit history for entity"""
        return self.audit_repo.get_by_entity_id(entity_id, skip, limit)
