# backend/app/repositories.py
# Repository pattern for data access abstraction

from typing import List, Optional, Type, TypeVar
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from app.models import Defect, Machine, Fabric, StatusEnum, AuditLog

T = TypeVar('T')


class BaseRepository:
    """Generic repository for CRUD operations"""

    def __init__(self, db: Session, model_class: Type[T]):
        self.db = db
        self.model_class = model_class

    def save(self, entity: T) -> T:
        """Save entity (insert or merge)"""
        self.db.add(entity)
        self.db.flush()
        return entity

    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by primary key"""
        return self.db.query(self.model_class).filter(
            self.model_class.id == entity_id
        ).first()

    def exists_by_id(self, entity_id: str) -> bool:
        """Check if entity exists"""
        return self.db.query(self.model_class).filter(
            self.model_class.id == entity_id
        ).first() is not None

    def exists_by_name(self, name: str, exclude_id: Optional[str] = None) -> bool:
        """Check if entity with name exists (case-insensitive)"""
        query = self.db.query(self.model_class).filter(
            func.lower(self.model_class.name) == name.lower()
        )
        if exclude_id:
            query = query.filter(self.model_class.id != exclude_id)
        return query.first() is not None

    def get_all_active(self, skip: int = 0, limit: int = 100) -> tuple[List[T], int]:
        """Get all active entities (paginated)"""
        query = self.db.query(self.model_class).filter(
            self.model_class.status == StatusEnum.ACTIVE,
            self.model_class.is_system == False
        ).order_by(self.model_class.name)

        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def get_all(self, skip: int = 0, limit: int = 100, include_archived: bool = False) -> tuple[List[T], int]:
        """Get all entities (paginated)"""
        query = self.db.query(self.model_class)

        if not include_archived:
            query = query.filter(self.model_class.status == StatusEnum.ACTIVE)

        query = query.order_by(self.model_class.name)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def search_by_name(self, search_term: str, skip: int = 0, limit: int = 20) -> tuple[List[T], int]:
        """Search entities by name (case-insensitive)"""
        query = self.db.query(self.model_class).filter(
            func.lower(self.model_class.name).contains(search_term.lower()),
            self.model_class.status == StatusEnum.ACTIVE
        ).order_by(self.model_class.name)

        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def count_by_status(self, status: StatusEnum) -> int:
        """Count entities by status"""
        return self.db.query(self.model_class).filter(
            self.model_class.status == status
        ).count()

    def delete_by_id(self, entity_id: str) -> bool:
        """Hard delete (use with caution - prefer soft delete)"""
        entity = self.get_by_id(entity_id)
        if entity:
            self.db.delete(entity)
            self.db.flush()
            return True
        return False


class DefectRepository(BaseRepository):
    """Defect-specific repository"""

    def __init__(self, db: Session):
        super().__init__(db, Defect)

    def get_by_name(self, name: str) -> Optional[Defect]:
        """Get defect by name"""
        return self.db.query(Defect).filter(
            func.lower(Defect.name) == name.lower()
        ).first()

    def get_by_process(self, process: str, skip: int = 0, limit: int = 20) -> tuple[List[Defect], int]:
        """Get defects by typical process"""
        query = self.db.query(Defect).filter(
            Defect.typical_process == process,
            Defect.status == StatusEnum.ACTIVE
        ).order_by(Defect.name)

        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def count_recent_usage(self, defect_id: str, days: int = 7) -> int:
        """Count inspections using this defect in last N days"""
        cutoff = datetime.utcnow() - timedelta(days=days)

        # In real implementation, would join with inspections table
        # For now, returning 0 as placeholder
        # This would be implemented when inspections table is available
        return 0

    def get_system_defects(self) -> List[Defect]:
        """Get all system defects"""
        return self.db.query(Defect).filter(
            Defect.is_system == True
        ).order_by(Defect.name).all()


class MachineRepository(BaseRepository):
    """Machine-specific repository"""

    def __init__(self, db: Session):
        super().__init__(db, Machine)

    def get_by_name(self, name: str) -> Optional[Machine]:
        """Get machine by name"""
        return self.db.query(Machine).filter(
            func.lower(Machine.name) == name.lower()
        ).first()

    def get_by_process(self, process: str, skip: int = 0, limit: int = 20) -> tuple[List[Machine], int]:
        """Get machines by process type"""
        query = self.db.query(Machine).filter(
            Machine.process == process,
            Machine.status == StatusEnum.ACTIVE
        ).order_by(Machine.name)

        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def count_recent_usage(self, machine_id: str, days: int = 7) -> int:
        """Count inspections using this machine in last N days"""
        cutoff = datetime.utcnow() - timedelta(days=days)

        # In real implementation, would join with inspections table
        return 0

    def get_system_machines(self) -> List[Machine]:
        """Get all system machines"""
        return self.db.query(Machine).filter(
            Machine.is_system == True
        ).order_by(Machine.name).all()


class FabricRepository(BaseRepository):
    """Fabric-specific repository"""

    def __init__(self, db: Session):
        super().__init__(db, Fabric)

    def get_by_name(self, name: str) -> Optional[Fabric]:
        """Get fabric by name"""
        return self.db.query(Fabric).filter(
            func.lower(Fabric.name) == name.lower()
        ).first()

    def get_by_width_range(self, min_width: float, max_width: float,
                           skip: int = 0, limit: int = 20) -> tuple[List[Fabric], int]:
        """Get fabrics by width range"""
        query = self.db.query(Fabric).filter(
            Fabric.width_cm >= min_width,
            Fabric.width_cm <= max_width,
            Fabric.status == StatusEnum.ACTIVE
        ).order_by(Fabric.name)

        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def get_by_weight_range(self, min_weight: float, max_weight: float,
                            skip: int = 0, limit: int = 20) -> tuple[List[Fabric], int]:
        """Get fabrics by weight range"""
        query = self.db.query(Fabric).filter(
            Fabric.weight_gsm >= min_weight,
            Fabric.weight_gsm <= max_weight,
            Fabric.status == StatusEnum.ACTIVE
        ).order_by(Fabric.name)

        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def count_recent_usage(self, fabric_id: str, days: int = 7) -> int:
        """Count lotes using this fabric in last N days"""
        cutoff = datetime.utcnow() - timedelta(days=days)

        # In real implementation, would join with lotes table
        return 0

    def get_system_fabrics(self) -> List[Fabric]:
        """Get all system fabrics"""
        return self.db.query(Fabric).filter(
            Fabric.is_system == True
        ).order_by(Fabric.name).all()


class AuditLogRepository:
    """Repository for audit trail queries"""

    def __init__(self, db: Session):
        self.db = db

    def save(self, entity_type: str, entity_id: str, operation: str,
             old_values: Optional[str], new_values: Optional[str],
             user_id: str, trace_id: Optional[str] = None) -> AuditLog:
        """Save audit log entry"""
        entry = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            operation=operation,
            old_values=old_values,
            new_values=new_values,
            user_id=user_id,
            trace_id=trace_id
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    def get_by_entity_id(self, entity_id: str, skip: int = 0, limit: int = 50) -> tuple[List[AuditLog], int]:
        """Get audit history for entity"""
        query = self.db.query(AuditLog).filter(
            AuditLog.entity_id == entity_id
        ).order_by(desc(AuditLog.timestamp))

        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def get_by_user_id(self, user_id: str, skip: int = 0, limit: int = 100) -> tuple[List[AuditLog], int]:
        """Get audit entries by user"""
        query = self.db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(desc(AuditLog.timestamp))

        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def get_recent(self, hours: int = 24, skip: int = 0, limit: int = 100) -> tuple[List[AuditLog], int]:
        """Get recent audit entries"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        query = self.db.query(AuditLog).filter(
            AuditLog.timestamp >= cutoff
        ).order_by(desc(AuditLog.timestamp))

        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def get_by_operation(self, operation: str, skip: int = 0, limit: int = 100) -> tuple[List[AuditLog], int]:
        """Get audit entries by operation type"""
        query = self.db.query(AuditLog).filter(
            AuditLog.operation == operation
        ).order_by(desc(AuditLog.timestamp))

        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total
