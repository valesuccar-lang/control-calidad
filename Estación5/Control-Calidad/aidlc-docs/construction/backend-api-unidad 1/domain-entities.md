# Domain Entities & DDD Design — Backend API Unit (Unit 1)
**Date**: 2026-05-28  
**Unit**: Backend API (Python FastAPI)  
**Purpose**: Document domain model, aggregates, value objects, and services for backend implementation  
**Status**: FUNCTIONAL DESIGN PHASE

---

## 🎯 OVERVIEW

This document consolidates the Domain-Driven Design (DDD) model for the **Backend API Unit (Unit 1)**, mapping abstract DDD concepts to concrete Python/FastAPI implementation patterns.

**3 Bounded Contexts**:
1. **Inspection Domain** — Register defects, photos, timestamps
2. **Approval Domain** — Approve/reject inspections  
3. **Masters Domain** — Manage catalogs (defects, machines, fabrics)

---

## 📍 BOUNDED CONTEXT 1: INSPECTION DOMAIN

### Purpose
Centralize defect capture logic: photos, defect types, comments, machines, timing.

### Aggregates

#### Aggregate 1: Lote (Aggregate Root)

**Role**: Container for all inspections of a production batch.

**Python Implementation**:
```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class LoteStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROCESS = "IN_PROCESS"
    INSPECTED = "INSPECTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

@dataclass
class Lote:
    """Aggregate Root: Production batch"""
    lote_id: str  # HDR-12847 (unique identity)
    fabric_id: str  # TEJ-001 (reference to Masters Domain)
    quantity: int
    status: LoteStatus
    created_at: datetime
    
    def __post_init__(self):
        # Invariant: lote_id must be non-empty
        if not self.lote_id:
            raise ValueError("lote_id cannot be empty")
        # Invariant: quantity must be positive
        if self.quantity <= 0:
            raise ValueError("quantity must be > 0")
    
    def mark_in_process(self) -> None:
        """Business rule: transition PENDING → IN_PROCESS"""
        if self.status != LoteStatus.PENDING:
            raise ValueError(f"Cannot mark in process: current status is {self.status}")
        self.status = LoteStatus.IN_PROCESS
    
    def mark_inspected(self) -> None:
        """Business rule: transition IN_PROCESS → INSPECTED"""
        if self.status != LoteStatus.IN_PROCESS:
            raise ValueError(f"Cannot mark inspected: current status is {self.status}")
        self.status = LoteStatus.INSPECTED
```

**Invariants**:
- `lote_id` is unique (identity)
- `quantity` > 0
- Status transitions follow state machine (PENDING → IN_PROCESS → INSPECTED → APPROVED/REJECTED)
- One Lote has many Inspections (1:M)

---

#### Aggregate 2: Inspection (Aggregate Root)

**Role**: Core entity capturing a single defect finding.

**Python Implementation**:
```python
from typing import Optional
from uuid import UUID, uuid4

@dataclass
class Inspection:
    """Aggregate Root: Single defect finding"""
    inspection_id: UUID  # Generated UUID
    lote_id: str  # Reference to Lote
    analista_id: str  # Reference to user/analyst
    defect: 'DefectType'  # Value Object
    comment: 'Comment'  # Value Object
    photograph: 'Photograph'  # Value Object
    machine_identified: 'MachineId'  # Value Object
    inspection_time: 'InspectionTime'  # Value Object
    sync_status: 'SyncStatus' = SyncStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        # Invariants: all required fields must be non-null
        if not self.lote_id:
            raise ValueError("lote_id required")
        if not self.defect:
            raise ValueError("defect required")
        if not self.comment:
            raise ValueError("comment required")
        if not self.photograph:
            raise ValueError("photograph required")
        if not self.machine_identified:
            raise ValueError("machine_identified required")
    
    def mark_synced(self) -> None:
        """Mark inspection as successfully synced to server"""
        self.sync_status = SyncStatus.SYNCED
    
    def mark_sync_failed(self) -> None:
        """Mark sync as failed, retry eligible"""
        self.sync_status = SyncStatus.SYNC_FAILED
    
    def complete_inspection(self) -> None:
        """Finalize inspection (set check_out timestamp)"""
        self.inspection_time.set_check_out(datetime.utcnow())
```

**Invariants**:
- `inspection_id` is unique (identity)
- All required fields: `defect`, `comment`, `photograph`, `machine_identified` must be non-null
- Only one Inspection per finding (no duplicates within same Lote)
- Timestamps from server, not client

---

### Value Objects (Inspection Domain)

#### DefectType
```python
@dataclass(frozen=True)  # Immutable
class DefectType:
    """Value Object: Type of defect found (reference to Masters Domain)"""
    defect_id: str  # DEF-TON
    defect_name: str  # TONODIFFERENTE
    description: str
    typical_machine: Optional['MachineId'] = None
    
    def __post_init__(self):
        # Invariant: defect_id must be non-empty
        if not self.defect_id:
            raise ValueError("defect_id cannot be empty")
    
    def __eq__(self, other) -> bool:
        """Equality by defect_id (value-based identity)"""
        if not isinstance(other, DefectType):
            return False
        return self.defect_id == other.defect_id
    
    def __hash__(self) -> int:
        return hash(self.defect_id)
```

**Rules**:
- Immutable (frozen dataclass)
- Equality by `defect_id` (not object reference)
- Must exist in Masters Domain before use
- Typical machine is optional hint for analyst

---

#### Comment
```python
@dataclass(frozen=True)
class Comment:
    """Value Object: Analyst comment on defect"""
    text: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        # Invariant: length 10-500 characters
        if len(self.text) < 10:
            raise ValueError("comment must be at least 10 characters")
        if len(self.text) > 500:
            raise ValueError("comment must be at most 500 characters")
        # Invariant: no special SQL characters (basic sanitization)
        if any(char in self.text for char in [';"', "';", "--"]):
            raise ValueError("comment contains invalid characters")
    
    def __eq__(self, other) -> bool:
        """Equality by content"""
        if not isinstance(other, Comment):
            return False
        return self.text == other.text
```

**Rules**:
- Immutable
- 10-500 characters (required for audit trail)
- Unicode + emoji allowed
- Timestamps immutable (set at creation)

---

#### Photograph
```python
@dataclass(frozen=True)
class Photograph:
    """Value Object: Defect photo (blob reference)"""
    photo_id: UUID = field(default_factory=uuid4)
    blob_path: str  # File system or S3 path
    mime_type: str = "image/jpeg"  # Default JPEG
    size_bytes: int  # Total size after compression
    checksum: str  # SHA256 for integrity check
    uploaded_at: datetime = field(default_factory=datetime.utcnow)
    synced: bool = False
    
    def __post_init__(self):
        # Invariant: size <= 500KB
        if self.size_bytes > 500 * 1024:
            raise ValueError("Photo size exceeds 500KB limit")
        # Invariant: mime_type must be valid image
        if not self.mime_type.startswith("image/"):
            raise ValueError("mime_type must be image/*")
    
    def __eq__(self, other) -> bool:
        """Equality by checksum (content-based identity)"""
        if not isinstance(other, Photograph):
            return False
        return self.checksum == other.checksum
    
    def __hash__(self) -> int:
        return hash(self.checksum)
```

**Rules**:
- Immutable (photo data cannot be modified)
- Max 500KB (compression: JPEG 80%)
- Checksum for integrity verification
- Synced flag: True after backend confirms receipt
- Storable in IndexedDB (frontend) or filesystem (backend)

---

#### InspectionTime
```python
@dataclass(frozen=True)
class InspectionTime:
    """Value Object: Immutable timestamps for inspection duration"""
    check_in: datetime
    check_out: Optional[datetime] = None
    elapsed_seconds: int = 0
    
    def __post_init__(self):
        # Invariant: check_in must not be None
        if not self.check_in:
            raise ValueError("check_in timestamp required")
        # Invariant: if check_out exists, must be after check_in
        if self.check_out and self.check_out < self.check_in:
            raise ValueError("check_out must be after check_in")
    
    def with_check_out(self, check_out: datetime) -> 'InspectionTime':
        """
        Create new InspectionTime with check_out (immutable pattern).
        
        Returns: New InspectionTime with elapsed_seconds calculated
        """
        elapsed = int((check_out - self.check_in).total_seconds())
        return InspectionTime(
            check_in=self.check_in,
            check_out=check_out,
            elapsed_seconds=elapsed
        )
    
    def is_complete(self) -> bool:
        """Check if inspection has been completed (check_out set)"""
        return self.check_out is not None
```

**Rules**:
- Immutable (no setters)
- `check_in`: Set automatically when Lote opened
- `check_out`: Set when inspection saved (immutable pattern: create new instance)
- `elapsed_seconds`: Calculated automatically
- Timestamps from server (not client) to prevent manipulation

---

#### SyncStatus
```python
from enum import Enum

class SyncStatus(str, Enum):
    """Value Object: Offline sync state"""
    PENDING = "PENDING"  # In IndexedDB, not yet synced
    SYNCED = "SYNCED"  # Sent to server, confirmed
    SYNC_FAILED = "SYNC_FAILED"  # Attempted sync but error
    RETRY = "RETRY"  # Queued for automatic retry
    
    def can_retry(self) -> bool:
        """Check if retry is eligible"""
        return self in [SyncStatus.SYNC_FAILED, SyncStatus.RETRY]
```

**Rules**:
- Enum-based (fixed set of states)
- Service Worker manages state transitions
- Retry uses exponential backoff
- No circular states (one-way progression)

---

#### MachineId
```python
@dataclass(frozen=True)
class MachineId:
    """Value Object: Reference to machine (Masters Domain)"""
    machine_id: str  # MAQ-AGO-80
    machine_name: str  # AGOTAMIENTO 80
    
    def __post_init__(self):
        if not self.machine_id:
            raise ValueError("machine_id cannot be empty")
    
    def __eq__(self, other) -> bool:
        """Equality by machine_id"""
        if not isinstance(other, MachineId):
            return False
        return self.machine_id == other.machine_id
```

---

### Domain Services (Inspection Domain)

**Purpose**: Encapsulate complex business logic that doesn't fit in Aggregates or Value Objects.

```python
class InspectionService:
    """Domain Service: Inspection business logic"""
    
    def __init__(self, inspection_repository: 'InspectionRepository',
                 defect_repository: 'DefectRepository',
                 machine_repository: 'MachineRepository'):
        self.inspection_repo = inspection_repository
        self.defect_repo = defect_repository
        self.machine_repo = machine_repository
        self.event_bus = EventBus()  # For publishing events
    
    def register_inspection(
        self,
        lote: Lote,
        defect: DefectType,
        comment: Comment,
        photograph: Photograph,
        machine: MachineId,
        analista_id: str
    ) -> Inspection:
        """
        Register new inspection with all validations.
        
        Business Rules:
        - Defect MUST exist in Masters Domain
        - Comment MUST be ≥10 chars (validated in Value Object)
        - Photograph MUST be valid (size, format, checksum)
        - Machine MUST exist in Masters Domain
        - Timestamps from server (not client)
        
        Returns: New Inspection aggregate
        
        Raises:
        - ValueError: If defect/machine not found or photo invalid
        """
        # Rule 1: Validate defect exists
        if not self.defect_repo.find_by_id(defect.defect_id):
            raise ValueError(f"Defect {defect.defect_id} not found in Masters")
        
        # Rule 2: Validate machine exists
        if not self.machine_repo.find_by_id(machine.machine_id):
            raise ValueError(f"Machine {machine.machine_id} not found in Masters")
        
        # Rule 3: Create inspection with server-side timestamps
        inspection = Inspection(
            inspection_id=uuid4(),
            lote_id=lote.lote_id,
            analista_id=analista_id,
            defect=defect,
            comment=comment,
            photograph=photograph,
            machine_identified=machine,
            inspection_time=InspectionTime(check_in=datetime.utcnow()),
            sync_status=SyncStatus.PENDING
        )
        
        # Rule 4: Persist inspection
        self.inspection_repo.save(inspection)
        
        return inspection
    
    def complete_inspection(self, inspection: Inspection) -> Inspection:
        """
        Finalize inspection (set check_out timestamp, calculate elapsed time).
        
        Returns: Updated inspection with complete timing
        """
        # Set check_out (creates new InspectionTime due to immutability)
        inspection.inspection_time = inspection.inspection_time.with_check_out(
            datetime.utcnow()
        )
        
        # Persist update
        self.inspection_repo.save(inspection)
        
        return inspection
    
    def sync_offline_inspection(self, inspection: Inspection) -> bool:
        """
        Sync offline inspection to server.
        
        Business Rules:
        - Handle network failures gracefully
        - Retry with exponential backoff
        - Update SyncStatus in repo
        - Publish SyncCompleted event on success
        
        Returns: True if sync successful, False if queued for retry
        
        Raises:
        - ValueError: If inspection not found locally
        """
        try:
            # Attempt to send to server
            # (Implementation: HTTP POST to /api/inspections/sync)
            inspection.mark_synced()
            self.inspection_repo.save(inspection)
            
            # Publish event
            self.event_bus.publish(InspectionSynced(
                inspection_id=inspection.inspection_id,
                lote_id=inspection.lote_id,
                synced_at=datetime.utcnow()
            ))
            
            return True
        
        except Exception as e:
            # Mark for retry
            inspection.mark_sync_failed()
            self.inspection_repo.save(inspection)
            
            # Queue for exponential backoff retry
            self.event_bus.publish(SyncFailed(
                inspection_id=inspection.inspection_id,
                error=str(e)
            ))
            
            return False
    
    def get_pending_sync_inspections(self) -> list[Inspection]:
        """Get all inspections pending sync (offline data)"""
        return self.inspection_repo.find_pending_sync()
```

---

### Repository Interface (Inspection Domain)

**Purpose**: Abstraction for persistence, enabling offline/online switching.

```python
from abc import ABC, abstractmethod

class InspectionRepository(ABC):
    """
    Repository pattern: Abstraction for Inspection persistence.
    
    Implementations:
    - IndexedDBRepository (frontend, offline)
    - PostgreSQLRepository (backend, server)
    """
    
    @abstractmethod
    def save(self, inspection: Inspection) -> None:
        """Save or update inspection"""
        pass
    
    @abstractmethod
    def find_by_id(self, inspection_id: UUID) -> Optional[Inspection]:
        """Retrieve inspection by ID"""
        pass
    
    @abstractmethod
    def find_pending_sync(self) -> list[Inspection]:
        """Find all inspections with SyncStatus=PENDING (offline queue)"""
        pass
    
    @abstractmethod
    def find_by_lote(self, lote_id: str) -> list[Inspection]:
        """Find all inspections for a Lote"""
        pass
    
    @abstractmethod
    def find_by_analista(self, analista_id: str) -> list[Inspection]:
        """Find all inspections by analyst (for history)"""
        pass
    
    @abstractmethod
    def delete(self, inspection_id: UUID) -> None:
        """Soft delete (mark inactive, preserve history)"""
        pass
```

---

---

## 📍 BOUNDED CONTEXT 2: APPROVAL DOMAIN

### Purpose
Validate and approve/reject inspections. Jefe QA reviews photo and issues decision.

### Aggregates

#### Aggregate: Approval (Aggregate Root)

**Python Implementation**:
```python
class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

@dataclass
class Approval:
    """Aggregate Root: QA approval decision"""
    approval_id: UUID = field(default_factory=uuid4)
    inspection_id: UUID  # Reference to Inspection Domain
    jefe_qa_id: str  # Reference to QA manager user
    decision: 'ApprovalDecision'  # Value Object
    rejection_reason: Optional['RejectionReason'] = None  # Value Object (optional)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status: ApprovalStatus = ApprovalStatus.PENDING
    
    def __post_init__(self):
        # Invariant: decision must be set
        if not self.decision:
            raise ValueError("decision required")
        # Invariant: if REJECTED, reason must be provided
        if self.decision == ApprovalDecision.REJECTED and not self.rejection_reason:
            raise ValueError("rejection_reason required when decision=REJECTED")
    
    def approve(self) -> None:
        """Business rule: Set decision to APPROVED"""
        if self.status != ApprovalStatus.PENDING:
            raise ValueError(f"Cannot approve: current status is {self.status}")
        self.decision = ApprovalDecision.APPROVED
        self.status = ApprovalStatus.APPROVED
    
    def reject(self, reason: 'RejectionReason') -> None:
        """Business rule: Set decision to REJECTED with reason"""
        if self.status != ApprovalStatus.PENDING:
            raise ValueError(f"Cannot reject: current status is {self.status}")
        self.decision = ApprovalDecision.REJECTED
        self.rejection_reason = reason
        self.status = ApprovalStatus.REJECTED
```

**Invariants**:
- `approval_id` is unique (identity)
- `decision` is immutable after creation
- If `REJECTED`, `rejection_reason` is required
- Only one Approval per Inspection (no duplicate decisions)

---

### Value Objects (Approval Domain)

#### ApprovalDecision
```python
class ApprovalDecision(str, Enum):
    """Value Object: Approval verdict"""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
```

**Rules**:
- Immutable enum
- Required on every Approval
- Cannot be changed after creation

---

#### RejectionReason
```python
@dataclass(frozen=True)
class RejectionReason:
    """Value Object: Reason for rejection with category"""
    reason: str  # "Foto borrosa", "Falsa alarma", etc.
    reason_code: str  # "PHOTO_BLURRY", "FALSE_ALARM", "NOT_CONFIRMED"
    
    def __post_init__(self):
        # Invariant: reason must be 10-500 chars (audit trail)
        if len(self.reason) < 10:
            raise ValueError("reason must be at least 10 characters")
        if len(self.reason) > 500:
            raise ValueError("reason must be at most 500 characters")
        # Invariant: reason_code must be valid
        valid_codes = ["PHOTO_BLURRY", "FALSE_ALARM", "NOT_CONFIRMED", "OTHER"]
        if self.reason_code not in valid_codes:
            raise ValueError(f"Invalid reason_code: {self.reason_code}")
    
    @staticmethod
    def suggested_reasons() -> dict[str, str]:
        """Return suggested reasons for dropdown UI"""
        return {
            "PHOTO_BLURRY": "Foto borrosa o de mala calidad",
            "FALSE_ALARM": "Falsa alarma (defecto no confirmado)",
            "NOT_CONFIRMED": "No se puede confirmar desde foto",
            "OTHER": "Otra razón"
        }
```

**Rules**:
- Immutable
- Reason text: 10-500 characters
- Reason code: fixed set (enum-like)
- Used only when decision=REJECTED

---

### Domain Services (Approval Domain)

```python
class ApprovalService:
    """Domain Service: Approval business logic"""
    
    def __init__(self, approval_repository: 'ApprovalRepository',
                 inspection_repository: 'InspectionRepository'):
        self.approval_repo = approval_repository
        self.inspection_repo = inspection_repository
        self.event_bus = EventBus()
    
    def approve_inspection(
        self,
        inspection_id: UUID,
        jefe_qa_id: str
    ) -> Approval:
        """
        Approve inspection (Jefe QA confirms defect finding).
        
        Business Rules:
        - Inspection must exist
        - Only one Approval per Inspection
        - Publishes InspectionApproved event for Gerente notification
        
        Returns: New Approval aggregate
        
        Raises:
        - ValueError: If inspection not found or already approved
        """
        # Rule 1: Verify inspection exists
        inspection = self.inspection_repo.find_by_id(inspection_id)
        if not inspection:
            raise ValueError(f"Inspection {inspection_id} not found")
        
        # Rule 2: Create approval
        approval = Approval(
            approval_id=uuid4(),
            inspection_id=inspection_id,
            jefe_qa_id=jefe_qa_id,
            decision=ApprovalDecision.APPROVED,
            status=ApprovalStatus.APPROVED
        )
        
        # Rule 3: Persist
        self.approval_repo.save(approval)
        
        # Rule 4: Publish event (loose coupling to notification system)
        self.event_bus.publish(InspectionApproved(
            approval_id=approval.approval_id,
            inspection_id=inspection_id,
            jefe_qa=jefe_qa_id,
            timestamp=datetime.utcnow()
        ))
        
        return approval
    
    def reject_inspection(
        self,
        inspection_id: UUID,
        jefe_qa_id: str,
        reason: RejectionReason
    ) -> Approval:
        """
        Reject inspection (Jefe QA flags defect finding as invalid).
        
        Business Rules:
        - Reason is mandatory
        - Publishes InspectionRejected event to notify Analista
        
        Returns: New Approval aggregate
        """
        # Rule 1: Verify inspection
        inspection = self.inspection_repo.find_by_id(inspection_id)
        if not inspection:
            raise ValueError(f"Inspection {inspection_id} not found")
        
        # Rule 2: Create rejection approval
        approval = Approval(
            approval_id=uuid4(),
            inspection_id=inspection_id,
            jefe_qa_id=jefe_qa_id,
            decision=ApprovalDecision.REJECTED,
            rejection_reason=reason,
            status=ApprovalStatus.REJECTED
        )
        
        # Rule 3: Persist
        self.approval_repo.save(approval)
        
        # Rule 4: Publish event (notify analyst to re-inspect)
        self.event_bus.publish(InspectionRejected(
            approval_id=approval.approval_id,
            inspection_id=inspection_id,
            reason=reason.reason,
            timestamp=datetime.utcnow()
        ))
        
        return approval
    
    def get_pending_approvals(self, jefe_qa_id: Optional[str] = None) -> list[Approval]:
        """
        Get all pending approvals for Jefe QA.
        
        Args:
            jefe_qa_id: If provided, filter by this QA manager
        
        Returns: List of pending Approvals
        """
        all_pending = self.approval_repo.find_pending()
        if jefe_qa_id:
            return [a for a in all_pending if a.jefe_qa_id == jefe_qa_id]
        return all_pending
```

---

### Repository Interface (Approval Domain)

```python
class ApprovalRepository(ABC):
    """Persistence abstraction for Approval aggregate"""
    
    @abstractmethod
    def save(self, approval: Approval) -> None:
        """Save approval"""
        pass
    
    @abstractmethod
    def find_by_id(self, approval_id: UUID) -> Optional[Approval]:
        """Find approval by ID"""
        pass
    
    @abstractmethod
    def find_pending(self) -> list[Approval]:
        """Find all pending approvals (status=PENDING)"""
        pass
    
    @abstractmethod
    def find_by_jefe_qa(self, jefe_qa_id: str) -> list[Approval]:
        """Find all approvals by QA manager (for history)"""
        pass
```

---

---

## 📍 BOUNDED CONTEXT 3: MASTERS DOMAIN

### Purpose
Maintain reference data: defect catalog, machine list, fabric properties. Read-only from other contexts.

### Aggregates

#### Aggregate 1: Defect (Aggregate Root)

```python
class MasterStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

@dataclass
class Defect:
    """Aggregate Root: Defect master (catalog item)"""
    defect_id: str  # DEF-TON (unique identity, not UUID)
    defect_name: str  # TONODIFFERENTE
    description: str
    typical_process: str  # TINTORERIA (process name)
    typical_machine: Optional['MachineId'] = None
    status: MasterStatus = MasterStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        # Invariant: defect_id must be unique (checked in repo)
        if not self.defect_id:
            raise ValueError("defect_id required")
        if not self.defect_name:
            raise ValueError("defect_name required")
    
    def inactivate(self) -> None:
        """Soft delete: mark INACTIVE (preserve historical data)"""
        if self.status == MasterStatus.INACTIVE:
            raise ValueError("Defect already inactive")
        self.status = MasterStatus.INACTIVE
        self.updated_at = datetime.utcnow()
    
    def reactivate(self) -> None:
        """Re-enable defect if needed"""
        if self.status == MasterStatus.ACTIVE:
            raise ValueError("Defect already active")
        self.status = MasterStatus.ACTIVE
        self.updated_at = datetime.utcnow()
```

**Invariants**:
- `defect_id` is unique (identity)
- Soft delete: status → INACTIVE (never hard delete to preserve history)
- Cannot inactivate twice

---

#### Aggregate 2: Machine (Aggregate Root)

```python
@dataclass
class Machine:
    """Aggregate Root: Production machine master"""
    machine_id: str  # MAQ-AGO-80 (unique identity)
    machine_name: str  # AGOTAMIENTO 80
    process: str  # TINTORERIA
    status: MasterStatus = MasterStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.machine_id or not self.machine_name:
            raise ValueError("machine_id and machine_name required")
    
    def inactivate(self) -> None:
        """Soft delete: mark INACTIVE"""
        if self.status == MasterStatus.INACTIVE:
            raise ValueError("Machine already inactive")
        self.status = MasterStatus.INACTIVE
        self.updated_at = datetime.utcnow()
```

---

#### Aggregate 3: Fabric (Aggregate Root)

```python
@dataclass
class Fabric:
    """Aggregate Root: Raw material master"""
    fabric_id: str  # TEJ-001 (unique identity)
    fabric_name: str  # NOVAKREPEL
    composition: str  # 100% algodón
    width: float  # cm
    weight: float  # gsm (grams per square meter)
    status: MasterStatus = MasterStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.fabric_id or not self.fabric_name:
            raise ValueError("fabric_id and fabric_name required")
        if self.width <= 0 or self.weight <= 0:
            raise ValueError("width and weight must be positive")
    
    def inactivate(self) -> None:
        """Soft delete: mark INACTIVE"""
        if self.status == MasterStatus.INACTIVE:
            raise ValueError("Fabric already inactive")
        self.status = MasterStatus.INACTIVE
        self.updated_at = datetime.utcnow()
```

---

### Domain Services (Masters Domain)

```python
class MastersService:
    """Domain Service: Master data management"""
    
    def __init__(self, defect_repo: 'DefectRepository',
                 machine_repo: 'MachineRepository',
                 fabric_repo: 'FabricRepository'):
        self.defect_repo = defect_repo
        self.machine_repo = machine_repo
        self.fabric_repo = fabric_repo
        self.event_bus = EventBus()
    
    def create_defect(
        self,
        defect_id: str,
        defect_name: str,
        description: str,
        typical_process: str,
        typical_machine: Optional[MachineId] = None
    ) -> Defect:
        """
        Create new defect in catalog.
        
        Business Rules:
        - defect_id must be unique (not already exist)
        - typical_machine (if provided) must exist
        
        Returns: New Defect aggregate
        
        Raises:
        - ValueError: If defect_id already exists or machine not found
        """
        # Rule 1: Check uniqueness
        if self.defect_repo.find_by_id(defect_id):
            raise ValueError(f"Defect {defect_id} already exists")
        
        # Rule 2: Validate machine if provided
        if typical_machine and not self.machine_repo.find_by_id(typical_machine.machine_id):
            raise ValueError(f"Machine {typical_machine.machine_id} not found")
        
        # Rule 3: Create aggregate
        defect = Defect(
            defect_id=defect_id,
            defect_name=defect_name,
            description=description,
            typical_process=typical_process,
            typical_machine=typical_machine,
            status=MasterStatus.ACTIVE
        )
        
        # Rule 4: Persist
        self.defect_repo.save(defect)
        
        # Rule 5: Publish event
        self.event_bus.publish(DefectCreated(
            defect_id=defect_id,
            defect_name=defect_name,
            timestamp=datetime.utcnow()
        ))
        
        return defect
    
    def inactivate_defect(self, defect_id: str) -> Defect:
        """Soft delete: mark defect as inactive (preserve history)"""
        defect = self.defect_repo.find_by_id(defect_id)
        if not defect:
            raise ValueError(f"Defect {defect_id} not found")
        
        defect.inactivate()
        self.defect_repo.save(defect)
        
        return defect
    
    def bulk_import_masters(
        self,
        csv_file_path: str
    ) -> dict[str, int]:
        """
        Import defects, machines, and fabrics from CSV.
        
        CSV Format:
        - Row 1: Header (type, id, name, ...)
        - type: DEFECT, MACHINE, or FABRIC
        
        Business Rules:
        - Skip duplicates (if ID exists, skip row)
        - Validate references (machine/fabric must exist)
        - Count successes and failures
        
        Returns: { 'imported': N, 'skipped': N, 'errors': N }
        """
        import csv
        
        counts = {'imported': 0, 'skipped': 0, 'errors': 0}
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        row_type = row.get('type', '').upper()
                        
                        if row_type == 'DEFECT':
                            # Check if exists
                            if self.defect_repo.find_by_id(row['id']):
                                counts['skipped'] += 1
                                continue
                            
                            defect = Defect(
                                defect_id=row['id'],
                                defect_name=row['name'],
                                description=row.get('description', ''),
                                typical_process=row.get('process', ''),
                                status=MasterStatus.ACTIVE
                            )
                            self.defect_repo.save(defect)
                            counts['imported'] += 1
                        
                        elif row_type == 'MACHINE':
                            if self.machine_repo.find_by_id(row['id']):
                                counts['skipped'] += 1
                                continue
                            
                            machine = Machine(
                                machine_id=row['id'],
                                machine_name=row['name'],
                                process=row.get('process', ''),
                                status=MasterStatus.ACTIVE
                            )
                            self.machine_repo.save(machine)
                            counts['imported'] += 1
                        
                        elif row_type == 'FABRIC':
                            if self.fabric_repo.find_by_id(row['id']):
                                counts['skipped'] += 1
                                continue
                            
                            fabric = Fabric(
                                fabric_id=row['id'],
                                fabric_name=row['name'],
                                composition=row.get('composition', ''),
                                width=float(row.get('width', 0)),
                                weight=float(row.get('weight', 0)),
                                status=MasterStatus.ACTIVE
                            )
                            self.fabric_repo.save(fabric)
                            counts['imported'] += 1
                    
                    except Exception as e:
                        counts['errors'] += 1
                        # Log error but continue with next row
                        print(f"Row error: {e}")
        
        except Exception as e:
            raise ValueError(f"Failed to import CSV: {e}")
        
        return counts
```

---

### Repository Interfaces (Masters Domain)

```python
class DefectRepository(ABC):
    @abstractmethod
    def save(self, defect: Defect) -> None:
        pass
    
    @abstractmethod
    def find_by_id(self, defect_id: str) -> Optional[Defect]:
        pass
    
    @abstractmethod
    def find_all_active(self) -> list[Defect]:
        """Get only ACTIVE defects (for dropdowns)"""
        pass
    
    @abstractmethod
    def find_all(self) -> list[Defect]:
        """Get all defects including INACTIVE (for admin)"""
        pass

class MachineRepository(ABC):
    @abstractmethod
    def save(self, machine: Machine) -> None:
        pass
    
    @abstractmethod
    def find_by_id(self, machine_id: str) -> Optional[Machine]:
        pass
    
    @abstractmethod
    def find_all_active(self) -> list[Machine]:
        pass

class FabricRepository(ABC):
    @abstractmethod
    def save(self, fabric: Fabric) -> None:
        pass
    
    @abstractmethod
    def find_by_id(self, fabric_id: str) -> Optional[Fabric]:
        pass
    
    @abstractmethod
    def find_all_active(self) -> list[Fabric]:
        pass
```

---

---

## 🔄 CROSS-DOMAIN INTERACTIONS

### Interaction 1: Inspection Domain → Masters Domain (Read-Only)

**Pattern**: Inspection Service validates against Masters catalog.

```python
# In InspectionService.register_inspection():
if not self.defect_repo.find_by_id(defect.defect_id):
    raise ValueError(f"Defect {defect.defect_id} not found in Masters")

if not self.machine_repo.find_by_id(machine.machine_id):
    raise ValueError(f"Machine {machine.machine_id} not found in Masters")
```

**Rule**: Masters Domain is READ-ONLY from Inspection Domain. No writes or cascading deletes.

---

### Interaction 2: Approval Domain → Inspection Domain (Reference)

**Pattern**: Approval references Inspection, not vice versa (unidirectional).

```python
# In ApprovalService.approve_inspection():
inspection = self.inspection_repo.find_by_id(inspection_id)
if not inspection:
    raise ValueError(f"Inspection {inspection_id} not found")

# No circular dependency: Inspection never references Approval
```

**Rule**: One-way dependency prevents circular references and simplifies state management.

---

### Interaction 3: Events for Cross-Context Communication

**Pattern**: Domain Events decouple contexts.

```python
# Approval Domain publishes event (Approval Service)
self.event_bus.publish(InspectionApproved(
    approval_id=approval.approval_id,
    inspection_id=inspection_id,
    jefe_qa=jefe_qa_id,
    timestamp=datetime.utcnow()
))

# Application Layer subscribes and sends notification
# (Loose coupling: Approval doesn't know about notification system)
```

---

---

## 🏗️ LAYERED ARCHITECTURE FOR BACKEND API UNIT

```
┌──────────────────────────────────────────────────────────┐
│           PRESENTATION LAYER (Routes)                    │
│  (FastAPI routes, request/response marshaling)           │
│  - routes/inspections.py                                 │
│  - routes/approvals.py                                   │
│  - routes/masters.py                                     │
│  - routes/auth.py                                        │
└─────────────────────────┬────────────────────────────────┘
                          │ DTOs (Request/Response)
┌──────────────────────────────────────────────────────────┐
│      APPLICATION LAYER (Use Cases / Services)            │
│  (DTO → Domain → DTO mapping, orchestration)             │
│  - application/inspection_use_cases.py                   │
│  - application/approval_use_cases.py                     │
│  - application/masters_use_cases.py                      │
│  - application/dtos.py                                   │
└─────────────────────────┬────────────────────────────────┘
                          │ Domain Objects
┌──────────────────────────────────────────────────────────┐
│     DOMAIN LAYER (Business Logic - DDD Core)             │
│  - domain/inspection/ (Aggregates, Value Objects, Service)
│  - domain/approval/ (Aggregates, Value Objects, Service) │
│  - domain/masters/ (Aggregates, Value Objects, Service)  │
│  - Domain Events, Ubiquitous Language                    │
└─────────────────────────┬────────────────────────────────┘
                          │ Repository Interfaces
┌──────────────────────────────────────────────────────────┐
│  INFRASTRUCTURE LAYER (Persistence, Event Bus)           │
│  - repositories/ (PostgreSQL implementations)            │
│  - database.py (SQLAlchemy ORM models)                   │
│  - event_bus.py (Event pub/sub)                          │
│  - config.py (Database connection, secrets)              │
└──────────────────────────────────────────────────────────┘
```

---

## 📋 DOMAIN EVENTS

### Event 1: InspectionApproved
```python
@dataclass
class InspectionApproved:
    """Published when Jefe QA approves inspection"""
    approval_id: UUID
    inspection_id: UUID
    jefe_qa_id: str
    timestamp: datetime
    
    # Handler in Application Layer: NotificationService
    # → Sends notification to Gerente (dashboard, email)
```

### Event 2: InspectionRejected
```python
@dataclass
class InspectionRejected:
    """Published when Jefe QA rejects inspection"""
    approval_id: UUID
    inspection_id: UUID
    reason: str
    timestamp: datetime
    
    # Handler in Application Layer: NotificationService
    # → Notifies Analista to re-inspect
```

### Event 3: InspectionSynced
```python
@dataclass
class InspectionSynced:
    """Published when offline inspection syncs to server"""
    inspection_id: UUID
    lote_id: str
    synced_at: datetime
    
    # Handler: Update UI, clear local cache if needed
```

### Event 4: SyncFailed
```python
@dataclass
class SyncFailed:
    """Published when sync fails (queued for retry)"""
    inspection_id: UUID
    error: str
    
    # Handler: Log retry attempt, schedule exponential backoff
```

---

## ✅ DESIGN VALIDATION CHECKLIST

- [ ] **Aggregates**: Each has clear root entity with invariants
- [ ] **Value Objects**: All immutable (frozen dataclasses)
- [ ] **Domain Services**: Business logic encapsulated, not anemic
- [ ] **Repositories**: Persistence abstraction defined (ABC)
- [ ] **Domain Events**: Cross-context communication via events
- [ ] **No Circular Dependencies**: Masters read-only, Approval → Inspection (one-way)
- [ ] **Immutability**: InspectionTime, Photograph, Comment, ApprovalDecision frozen
- [ ] **Invariants**: All business rules enforced in __post_init__
- [ ] **Python Patterns**: Dataclasses, Enums, ABC (match FastAPI style)
- [ ] **Error Handling**: ValueError for invariant violations, explicit messages

---

## 🚀 NEXT STEPS

1. ✅ **Functional Design** — COMPLETED (this document)
2. ➡️ **NFR Requirements** — Assess performance, security, scalability needs
3. ➡️ **NFR Design** — Apply NFR patterns (caching, validation, logging)
4. ➡️ **Infrastructure Design** — Map to PostgreSQL, repositories
5. ➡️ **Code Generation** — Generate FastAPI routes, SQLAlchemy models, tests

---

**Status**: ✅ FUNCTIONAL DESIGN COMPLETE  
**Ready for**: NFR Requirements Assessment & Code Generation  
**Unit**: Backend API (Python FastAPI)
