# Business Rules — Backend API Unit (Unit 1)
**Date**: 2026-05-28  
**Unit**: Backend API (Python FastAPI)  
**Purpose**: Document all business rules by bounded context  
**Status**: FUNCTIONAL DESIGN PHASE

---

## 📍 BOUNDED CONTEXT 1: INSPECTION DOMAIN

### Business Rules: Lote Aggregate

#### Rule I.1: Lote Identity Uniqueness
**Statement**: Cada Lote DEBE tener un `lote_id` único en el sistema.

**Why**: Evitar duplicados en catálogo de lotes; cada HDR-XXXXX es única en producción.

**Implementation**:
```python
class Lote:
    lote_id: str  # HDR-12847 (must be unique in DB)
    
    def __post_init__(self):
        if not self.lote_id:
            raise ValueError("lote_id cannot be empty")
        # DB: UNIQUE constraint on lote_id column
```

**Enforcement**:
- ✅ Dataclass validation (non-empty)
- ✅ PostgreSQL UNIQUE index on `lote_id`
- ✅ Application-level check before save

---

#### Rule I.2: Lote Quantity Validation
**Statement**: La cantidad de un lote DEBE ser > 0.

**Why**: Un lote sin cantidad no tiene sentido; es error de datos.

**Implementation**:
```python
class Lote:
    quantity: int
    
    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("quantity must be > 0")
```

**Enforcement**:
- ✅ Dataclass validation (>0)
- ✅ PostgreSQL NOT NULL + CHECK constraint
- ✅ Pydantic DTO validation on route

---

#### Rule I.3: Lote Status State Machine
**Statement**: Un Lote sigue esta máquina de estados:
```
PENDING → IN_PROCESS → INSPECTED → (APPROVED | REJECTED)
```

**Why**: Asegurar progresión lógica (no se puede rechazar sin inspeccionar).

**Implementation**:
```python
class LoteStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROCESS = "IN_PROCESS"
    INSPECTED = "INSPECTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class Lote:
    status: LoteStatus
    
    def mark_in_process(self) -> None:
        if self.status != LoteStatus.PENDING:
            raise ValueError(f"Cannot mark in process: current status is {self.status}")
        self.status = LoteStatus.IN_PROCESS
    
    def mark_inspected(self) -> None:
        if self.status != LoteStatus.IN_PROCESS:
            raise ValueError(f"Cannot mark inspected: current status is {self.status}")
        self.status = LoteStatus.INSPECTED
```

**Enforcement**:
- ✅ Dataclass validation (only valid transitions)
- ✅ Audit log (track status changes)

---

### Business Rules: Inspection Aggregate

#### Rule I.4: Inspection Mandatory Fields
**Statement**: Una Inspección DEBE tener TODOS estos campos:
- `defect` (tipo de defecto)
- `comment` (comentario ≥10 chars)
- `photograph` (foto válida)
- `machine_identified` (máquina responsable)

**Why**: Compleness de datos; sin foto, no hay evidencia del defecto.

**Implementation**:
```python
class Inspection:
    defect: 'DefectType'
    comment: 'Comment'
    photograph: 'Photograph'
    machine_identified: 'MachineId'
    
    def __post_init__(self):
        if not self.defect:
            raise ValueError("defect required")
        if not self.comment:
            raise ValueError("comment required")
        if not self.photograph:
            raise ValueError("photograph required")
        if not self.machine_identified:
            raise ValueError("machine_identified required")
```

**Enforcement**:
- ✅ Dataclass validation (non-null)
- ✅ Pydantic DTO (required fields)
- ✅ PostgreSQL NOT NULL constraints

---

#### Rule I.5: Inspection Timestamps from Server
**Statement**: Los timestamps (`check_in`, `check_out`) DEBEN generarse en el servidor, NO en el cliente.

**Why**: Prevenir manipulación de tiempos; garantizar que todos los registros usen hora confiable del servidor.

**Implementation**:
```python
class InspectionTime:
    check_in: datetime  # Set by server in InspectionService
    check_out: Optional[datetime] = None  # Set by server when inspection completed
    
    def __post_init__(self):
        if not self.check_in:
            raise ValueError("check_in timestamp required")
        # Immutable: no setters, only creation with server time

class InspectionService:
    def register_inspection(...) -> Inspection:
        inspection = Inspection(
            ...
            inspection_time=InspectionTime(check_in=datetime.utcnow())  # Server time
        )
        return inspection
```

**Enforcement**:
- ✅ Service method always uses `datetime.utcnow()` (not client-provided)
- ✅ API route never accepts `check_in`/`check_out` from request

---

#### Rule I.6: Inspection Uniqueness per Lote
**Statement**: No DEBE haber dos inspecciones idénticas para el mismo Lote (defect + photo).

**Why**: Evitar duplicados accidentales (misma foto cargada 2 veces).

**Implementation**:
```python
class InspectionService:
    def register_inspection(
        self,
        lote: Lote,
        defect: DefectType,
        photograph: Photograph,
        ...
    ) -> Inspection:
        # Check if same defect+photo already exists for this lote
        existing = self.inspection_repo.find_by_lote_defect_photo(
            lote_id=lote.lote_id,
            defect_id=defect.defect_id,
            photo_checksum=photograph.checksum  # Content-based identity
        )
        if existing:
            raise ValueError("Inspection already exists for this lote+defect+photo")
        
        # Create new inspection
        inspection = Inspection(...)
        return inspection
```

**Enforcement**:
- ✅ Repository query (check before save)
- ✅ Photo checksum (content-based duplicate detection)

---

### Business Rules: Value Objects (Inspection Domain)

#### Rule I.7: DefectType Must Exist in Masters
**Statement**: Un `DefectType` en una Inspección DEBE existir en el catálogo de Masters Domain.

**Why**: Integridad referencial; defect_id debe ser válido.

**Implementation**:
```python
class InspectionService:
    def register_inspection(
        self,
        lote: Lote,
        defect: DefectType,
        ...
    ) -> Inspection:
        # Rule: Validate defect exists
        if not self.defect_repo.find_by_id(defect.defect_id):
            raise ValueError(f"Defect {defect.defect_id} not found in Masters")
        
        inspection = Inspection(...)
        return inspection
```

**Enforcement**:
- ✅ Service validation before creation
- ✅ PostgreSQL FOREIGN KEY constraint (if implemented)

---

#### Rule I.8: Comment Length Validation
**Statement**: Un `Comment` DEBE tener:
- Mínimo: 10 caracteres
- Máximo: 500 caracteres

**Why**: Garantizar comentarios útiles (no vacíos); limitar size (1500 chars = 1.5KB × 100K inspections = 150MB).

**Implementation**:
```python
class Comment:
    text: str
    
    def __post_init__(self):
        if len(self.text) < 10:
            raise ValueError("comment must be at least 10 characters")
        if len(self.text) > 500:
            raise ValueError("comment must be at most 500 characters")
```

**Enforcement**:
- ✅ Value Object validation (frozen dataclass)
- ✅ Pydantic DTO validation
- ✅ PostgreSQL VARCHAR(500) constraint

---

#### Rule I.9: Photograph Size Limit
**Statement**: Una `Photograph` DEBE ser ≤ 500KB.

**Why**: Limitar almacenamiento (30GB/month × 60K/month); optimizar para almacenamiento IndexedDB (5-10MB límite).

**Implementation**:
```python
class Photograph:
    size_bytes: int
    
    def __post_init__(self):
        if self.size_bytes > 500 * 1024:  # 500KB
            raise ValueError("Photo size exceeds 500KB limit")
        # Client: Compress JPEG 80% quality before upload
```

**Enforcement**:
- ✅ Value Object validation
- ✅ Client-side compression (Service Worker)
- ✅ Server-side size check before save

---

#### Rule I.10: Photograph Integrity Check
**Statement**: Un `Photograph` debe incluir un `checksum` (SHA256) para verificar integridad.

**Why**: Detectar corrupción de archivo durante transferencia; deduplicación de fotos.

**Implementation**:
```python
class Photograph:
    checksum: str  # SHA256 hash
    
    def verify_checksum(self, file_bytes: bytes) -> bool:
        computed = hashlib.sha256(file_bytes).hexdigest()
        return computed == self.checksum

# In route:
@app.post("/api/inspections")
async def create_inspection(req: InspectionCreateDTO):
    photo_bytes = base64.b64decode(req.photo_base64)
    
    # Verify checksum
    computed_checksum = hashlib.sha256(photo_bytes).hexdigest()
    if computed_checksum != req.photo_checksum:
        raise ValueError("Photo checksum mismatch (file corrupted)")
    
    # Create photograph value object with verified checksum
    photograph = Photograph(
        checksum=computed_checksum,
        ...
    )
```

**Enforcement**:
- ✅ Client calculates SHA256, sends with request
- ✅ Server verifies checksum before save

---

#### Rule I.11: SyncStatus Immutable State
**Statement**: Un `SyncStatus` DEBE ser inmutable después de asignado.

**Why**: Evitar race conditions en offline sync (no modificar mientras se sincroniza).

**Implementation**:
```python
class SyncStatus(str, Enum):
    # Immutable enum; cannot change after assignment
    PENDING = "PENDING"
    SYNCED = "SYNCED"
    SYNC_FAILED = "SYNC_FAILED"

# Transition: Create new Inspection with updated SyncStatus
inspection.sync_status = SyncStatus.SYNCED  # In-memory
inspection_repo.save(inspection)  # Persist updated status
```

**Enforcement**:
- ✅ Enum-based (fixed set, no custom mutations)
- ✅ Repository handles state transitions atomically

---

### Business Rules: Domain Services (Inspection Domain)

#### Rule I.12: Defect & Machine Cross-Domain Validation
**Statement**: Antes de crear una Inspección, DEBE validarse que:
- El `defect_id` exista en Masters Domain
- El `machine_id` exista en Masters Domain

**Why**: Integridad referencial; evitar referencias a datos inexistentes.

**Implementation**: (Already shown in Rule I.7)

**Enforcement**:
- ✅ InspectionService validation (calls DefectRepository, MachineRepository)

---

#### Rule I.13: Offline Inspection Sync Idempotency
**Statement**: Si se intenta sincronizar la MISMA inspección dos veces, NO debe crear un duplicado.

**Why**: Network retry safety; analyst may click sync button multiple times.

**Implementation**:
```python
# Client sends: POST /api/inspections/sync with inspection_id
@app.post("/api/inspections/sync")
async def sync_inspection(req: SyncInspectionDTO):
    # Check if inspection_id already synced
    existing = inspection_repo.find_by_id(req.inspection_id)
    if existing and existing.sync_status == SyncStatus.SYNCED:
        # Already synced; return success (idempotent)
        return {"status": "SYNCED", "inspection_id": req.inspection_id}
    
    # Save or update inspection
    inspection_repo.save(inspection)
    return {"status": "SYNCED", "inspection_id": req.inspection_id}
```

**Enforcement**:
- ✅ API uses inspection_id as idempotency key
- ✅ Repository handles upsert (insert or update)

---

---

## 📍 BOUNDED CONTEXT 2: APPROVAL DOMAIN

### Business Rules: Approval Aggregate

#### Rule A.1: One Approval per Inspection
**Statement**: Una Inspección PUEDE tener máximo 1 Aprobación.

**Why**: Evitar múltiples decisiones sobre el mismo defecto; decisión es definitiva.

**Implementation**:
```python
class ApprovalService:
    def approve_inspection(
        self,
        inspection_id: UUID,
        jefe_qa_id: str
    ) -> Approval:
        # Check if approval already exists
        existing = self.approval_repo.find_by_inspection_id(inspection_id)
        if existing:
            raise ValueError(f"Inspection {inspection_id} already has an approval")
        
        approval = Approval(...)
        return approval
```

**Enforcement**:
- ✅ Repository query before creation
- ✅ PostgreSQL UNIQUE index on `inspection_id`

---

#### Rule A.2: Immutable Approval Decision
**Statement**: Una vez creada una Aprobación, su `decision` CANNOT cambiar.

**Why**: Audit trail; decisión es permanente, no se puede revertir.

**Implementation**:
```python
class Approval:
    decision: ApprovalDecision  # APPROVED or REJECTED
    
    # NO SETTER: decision is immutable
    # If need to change, must create NEW Approval and VOID the old one

# If analyst wants to "undo" approval, only option is to document in comment/audit
```

**Enforcement**:
- ✅ Dataclass (no setter for decision)
- ✅ API: No PATCH route to change decision (only POST to create new)

---

#### Rule A.3: Rejection Reason Mandatory if REJECTED
**Statement**: Si `decision` = REJECTED, entonces `rejection_reason` MUST ser no-null.

**Why**: Obligar analyst a documentar POR QUÉ rechazó; traceability.

**Implementation**:
```python
class Approval:
    decision: ApprovalDecision
    rejection_reason: Optional[RejectionReason] = None
    
    def __post_init__(self):
        if self.decision == ApprovalDecision.REJECTED and not self.rejection_reason:
            raise ValueError("rejection_reason required when decision=REJECTED")
```

**Enforcement**:
- ✅ Dataclass validation
- ✅ Pydantic DTO (rejection_reason required in request if decision=REJECTED)

---

### Business Rules: Value Objects (Approval Domain)

#### Rule A.4: Rejection Reason Length
**Statement**: Un `RejectionReason.reason` DEBE tener 10-500 caracteres.

**Why**: Same as Rule I.8 (completeness + audit trail).

**Implementation**:
```python
class RejectionReason:
    reason: str
    
    def __post_init__(self):
        if len(self.reason) < 10:
            raise ValueError("reason must be at least 10 characters")
        if len(self.reason) > 500:
            raise ValueError("reason must be at most 500 characters")
```

**Enforcement**:
- ✅ Value Object validation
- ✅ Pydantic DTO validation

---

#### Rule A.5: Valid Rejection Reason Codes
**Statement**: `RejectionReason.reason_code` MUST ser uno de:
- `PHOTO_BLURRY`
- `FALSE_ALARM`
- `NOT_CONFIRMED`
- `OTHER`

**Why**: Standardize rejection categories; enable analytics (% false alarms, % blurry photos).

**Implementation**:
```python
class RejectionReason:
    reason_code: str
    
    def __post_init__(self):
        valid_codes = ["PHOTO_BLURRY", "FALSE_ALARM", "NOT_CONFIRMED", "OTHER"]
        if self.reason_code not in valid_codes:
            raise ValueError(f"Invalid reason_code: {self.reason_code}")
```

**Enforcement**:
- ✅ Value Object validation
- ✅ Pydantic DTO (Enum or string matching)

---

---

## 📍 BOUNDED CONTEXT 3: MASTERS DOMAIN

### Business Rules: Master Aggregates

#### Rule M.1: Master Identity Uniqueness
**Statement**: Cada Master (Defect, Machine, Fabric) DEBE tener un ID único.

**Why**: Integridad referencial; each defect_id, machine_id, fabric_id must be unique.

**Implementation**:
```python
class Defect:
    defect_id: str  # e.g., DEF-TON
    
    def __post_init__(self):
        if not self.defect_id:
            raise ValueError("defect_id required")
        # DB: UNIQUE constraint on defect_id

class Machine:
    machine_id: str  # e.g., MAQ-AGO-80
    
    def __post_init__(self):
        if not self.machine_id:
            raise ValueError("machine_id required")
```

**Enforcement**:
- ✅ Dataclass validation
- ✅ PostgreSQL UNIQUE constraint

---

#### Rule M.2: Soft Delete (No Hard Delete)
**Statement**: Cuando un Master se "borra", se marca como INACTIVE (status=INACTIVE), NUNCA se borra de base de datos.

**Why**: Preservar histórico; inspecciones antiguas pueden referenciar el defect que fue inactivado.

**Implementation**:
```python
class MasterStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class Defect:
    status: MasterStatus = MasterStatus.ACTIVE
    
    def inactivate(self) -> None:
        if self.status == MasterStatus.INACTIVE:
            raise ValueError("Defect already inactive")
        self.status = MasterStatus.INACTIVE

# API:
@app.delete("/api/masters/defects/{defect_id}")
async def delete_defect(defect_id: str):
    defect = defect_repo.find_by_id(defect_id)
    if not defect:
        raise ValueError("Defect not found")
    
    defect.inactivate()  # Soft delete
    defect_repo.save(defect)
    
    return {"status": "INACTIVE"}
```

**Enforcement**:
- ✅ Service method (`inactivate()`) enforces transition
- ✅ No hard DELETE from API (only soft delete via status)

---

#### Rule M.3: Active Masters in Dropdowns
**Statement**: Cuando Analista abre form (defect selector), SOLO se muestran Masters con status=ACTIVE.

**Why**: UX: no mostrar opciones inactivas en dropdowns; pero historicamente existen.

**Implementation**:
```python
class DefectRepository(ABC):
    @abstractmethod
    def find_all_active(self) -> list[Defect]:
        """Get only ACTIVE defects (for dropdowns)"""
        pass

# In API:
@app.get("/api/masters/defects")
async def list_defects(include_inactive: bool = False):
    if include_inactive:
        # Only ADMIN can see inactive
        return defect_repo.find_all()
    else:
        # Analista sees only ACTIVE
        return defect_repo.find_all_active()
```

**Enforcement**:
- ✅ Repository method filtering
- ✅ RBAC: only ADMIN can request `include_inactive=true`

---

#### Rule M.4: Masters Read-Only from Other Domains
**Statement**: Inspection Domain y Approval Domain SOLO pueden LEER Masters; NUNCA pueden escribir.

**Why**: Separation of concerns; Masters es catálogo compartido, no puede ser modificado desde inspection flow.

**Implementation**:
```python
# ✅ ALLOWED:
inspection_service = InspectionService(
    ...,
    defect_repo=defect_repo  # Read-only access
)
defect = defect_repo.find_by_id(defect_id)  # READ OK

# ❌ NOT ALLOWED:
# inspection_service.create_defect(...) - NO! This method doesn't exist in InspectionService
# Only MastersService can create/update Masters
```

**Enforcement**:
- ✅ Code review (InspectionService ONLY calls `find_*` on DefectRepository, never `save`)
- ✅ No write routes in inspection API routes

---

#### Rule M.5: CSV Bulk Import Validation
**Statement**: Al importar Masters desde CSV:
- Los IDs duplicados se SKIP (no error)
- Los IDs nuevos se IMPORT
- Se retorna { imported: N, skipped: N, errors: N }

**Why**: Reusabilidad; CSV puede contener datos ya existentes (idempotent).

**Implementation**:
```python
class MastersService:
    def bulk_import_masters(self, csv_file_path: str) -> dict:
        counts = {'imported': 0, 'skipped': 0, 'errors': 0}
        
        for row in csv_rows:
            try:
                # Check if exists
                if defect_repo.find_by_id(row['id']):
                    counts['skipped'] += 1
                    continue
                
                # Create and save
                defect = Defect(...)
                defect_repo.save(defect)
                counts['imported'] += 1
            
            except Exception as e:
                counts['errors'] += 1
                # Log error, continue with next row
        
        return counts
```

**Enforcement**:
- ✅ Service method logic (skip existing, import new)
- ✅ Transaction per-row (error in 1 row doesn't block others)

---

---

## 🔄 CROSS-DOMAIN BUSINESS RULES

#### Rule X.1: No Circular Dependencies
**Statement**: Las dependencias entre Bounded Contexts DEBEN ser unidireccionales:
```
Inspection Domain → Masters Domain (read-only)
Approval Domain → Inspection Domain (read-only)
Events ← All Domains (loose coupling)
```

**Why**: Evitar circular dependencies (A depends on B, B depends on A); simplify testing.

**Implementation**:
- ✅ Code review: Check imports (Inspection NEVER imports Approval)
- ✅ Tests: Mock dependencies to prevent circular setup

---

#### Rule X.2: Domain Events for Inter-Domain Communication
**Statement**: Cuando ocurra un evento en un Bounded Context que afecta a otro:
1. Publicar Domain Event
2. Application Layer subscibe y actúa
3. Domains NO se conocen directamente

**Why**: Loose coupling; cambios en un domain no rompen otros.

**Example**:
```python
# In ApprovalService (Approval Domain):
approval = Approval(...)
self.event_bus.publish(InspectionApproved(...))
# ← Approval Domain NO sabe quién le escucha

# In Application Layer:
event_bus.subscribe(InspectionApproved, NotificationService.handle_approval)
# ← Application Layer escucha y envía notificación
```

**Enforcement**:
- ✅ Event Bus pattern (pub/sub)
- ✅ No direct service dependencies (Approval doesn't call Notification)

---

---

## 📊 BUSINESS RULES SUMMARY TABLE

| Rule | Context | Aggregate | Statement | Enforcement |
|------|---------|-----------|-----------|-------------|
| I.1 | Inspection | Lote | Lote.lote_id must be unique | DB UNIQUE + validation |
| I.2 | Inspection | Lote | Lote.quantity > 0 | Dataclass + DB CHECK |
| I.3 | Inspection | Lote | Status state machine | Method validation |
| I.4 | Inspection | Inspection | All fields mandatory | Dataclass + Pydantic |
| I.5 | Inspection | InspectionTime | Server-generated timestamps | Service method |
| I.6 | Inspection | Inspection | No duplicate (defect+photo) | Repository query |
| I.7 | Inspection | DefectType | Must exist in Masters | Service validation |
| I.8 | Inspection | Comment | 10-500 chars | Value Object validation |
| I.9 | Inspection | Photograph | ≤500KB | Value Object validation |
| I.10 | Inspection | Photograph | SHA256 checksum | Server verification |
| I.11 | Inspection | SyncStatus | Immutable enum | Enum-based |
| I.12 | Inspection | Service | Defect & Machine validation | Service method |
| I.13 | Inspection | Service | Sync idempotency | API + Repository |
| A.1 | Approval | Approval | One per Inspection | DB UNIQUE + validation |
| A.2 | Approval | Approval | Decision immutable | No setter + API design |
| A.3 | Approval | Approval | Rejection reason if REJECTED | Value Object validation |
| A.4 | Approval | RejectionReason | 10-500 chars | Value Object validation |
| A.5 | Approval | RejectionReason | Valid reason codes | Enum validation |
| M.1 | Masters | All | ID uniqueness | DB UNIQUE + validation |
| M.2 | Masters | All | Soft delete only | Status = INACTIVE |
| M.3 | Masters | All | Active-only dropdowns | Repository filtering |
| M.4 | Masters | All | Read-only from others | Code review + method design |
| M.5 | Masters | Service | CSV import idempotency | Skip existing, import new |
| X.1 | Cross | All | No circular dependencies | Code structure |
| X.2 | Cross | All | Domain Events for coupling | Event Bus pattern |

---

**Status**: ✅ BUSINESS RULES DOCUMENTED  
**Ready for**: Business Logic Model (workflows, process flows)
