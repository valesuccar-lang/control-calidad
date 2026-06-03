# Domain-Driven Design (DDD) — Control de Calidad Textil
**Date**: 2026-05-27 | **Approach**: Bottom-Up DDD | **Bounded Contexts**: 3 principales

---

## 🎯 DDD OVERVIEW

Domain-Driven Design enfoca diseño en el DOMINIO del negocio (no en tecnología).

**3 Bounded Contexts principales**:
1. **Inspection Domain**: Captura de defectos, fotos, timestamps
2. **Approval Domain**: Validación y aprobación de inspecciones
3. **Masters Domain**: Catálogos (defectos, máquinas, telas)

---

## 📍 BOUNDED CONTEXT 1: INSPECTION DOMAIN

### Purpose
Registrar defectos encontrados en tela (foto, tipo, máquina, tiempo inspección).

### Aggregates

#### Aggregate 1: Lote (Lote Aggregate Root)
```
Lote (Aggregate Root)
├── loteId: String (HDR-12847)  [Identity]
├── fabricId: String (TEJ-001)
├── quantity: int
├── status: LoteStatus enum
└── createdAt: DateTime

Attributes:
- Cada Lote es ÚNICO por loteId
- Status: PENDING → IN_PROCESS → INSPECTED → APPROVED/REJECTED
- Relations: Inspections (1:M)
```

#### Aggregate 2: Inspection (Inspection Aggregate Root)
```
Inspection (Aggregate Root)
├── inspectionId: UUID [Identity]
├── lote: Lote (Reference)
├── analista: Analista (Reference)
├── defect: DefectType (Value Object)
├── comment: Comment (Value Object)
├── photograph: Photograph (Value Object)
├── machineIdentified: MachineId (Value Object)
├── inspectionTime: InspectionTime (Value Object)
├── syncStatus: SyncStatus enum
└── createdAt: DateTime

Relations:
- Cada Inspection pertenece a 1 Lote
- Inspection.defect = Value Object (no entity)
```

### Value Objects (Inspection Domain)

#### DefectType
```
DefectType (Value Object - Immutable)
├── defectId: String (DEF-TON)
├── defectName: String (TONODIFFERENTE)
├── description: String
├── typicalMachine: Machine (Reference, optional)

Rules:
- NO puede ser NULL
- MUST exist en Masters Domain
- Equality: por defectId
```

#### Comment
```
Comment (Value Object - Immutable)
├── text: String
├── createdAt: DateTime

Rules:
- Mínimo 10 caracteres
- Máximo 500 caracteres
- Acentos + emojis permitidos
```

#### Photograph
```
Photograph (Value Object - Immutable)
├── photoId: UUID
├── blobData: Bytes (IndexedDB en frontend)
├── mimeType: String (image/jpeg)
├── size: long (bytes)
├── checksum: String (SHA256)
├── uploadedAt: DateTime
├── synced: Boolean

Rules:
- Obligatorio (NO NULL)
- Max 500KB (compresión JPEG 80%)
- Storageable en IndexedDB (frontend) y filesystem (backend)
```

#### InspectionTime
```
InspectionTime (Value Object - Immutable)
├── checkIn: DateTime
├── checkOut: DateTime
├── elapsedSeconds: int

Rules:
- checkIn: Automático al abrir Lote
- checkOut: Automático al guardar
- NO editable manualmente
- Timestamps del servidor (no cliente)
```

#### SyncStatus
```
SyncStatus (Value Object - Enum)
- PENDING: En IndexedDB, aún no sincronizado
- SYNCED: Enviado a servidor, confirmado
- SYNC_FAILED: Intentó sincronizar pero falló
- RETRY: En cola de reintento

Rules:
- Service Worker maneja transiciones
- Retry con exponential backoff
```

### Domain Services (Inspection Domain)

```python
class InspectionService:
    def register_inspection(
        lote: Lote,
        defect: DefectType,
        comment: Comment,
        photograph: Photograph,
        machine: MachineId
    ) -> Inspection:
        """
        Dominio: Crear inspección válida con todos los campos obligatorios.
        
        Rules:
        - Defect MUST exist en Masters
        - Comment MUST be ≥10 chars
        - Photograph MUST be valid
        - Machine MUST exist en Masters
        - Timestamps automáticos (servidor)
        """
        inspection = Inspection(
            loteId=lote.id,
            defectType=defect,
            comment=comment,
            photograph=photograph,
            machineIdentified=machine,
            inspectionTime=InspectionTime(checkIn=now())
        )
        return inspection

    def complete_inspection(
        inspection: Inspection
    ) -> CompletedInspection:
        """
        Marcar inspección como completada (check-out automático).
        
        Returns: Inspection con checkOut timestamp + elapsedTime
        """
        inspection.inspectionTime.set_check_out(now())
        return inspection

    def sync_offline_inspection(
        inspection: Inspection
    ) -> SyncResult:
        """
        Sincronizar inspección offline a servidor.
        
        Dominio: Maneja lógica de retry, conflicto resolution, cero pérdida.
        """
        pass
```

### Repository (Inspection Domain)

```python
class InspectionRepository:
    """Persistence abstraction for Inspection Aggregate"""
    
    def save(inspection: Inspection) -> None:
        """Save inspection (local IndexedDB or server DB)"""
        
    def find_by_id(inspection_id: UUID) -> Inspection | None:
        """Retrieve inspection"""
        
    def find_pending_sync() -> List[Inspection]:
        """Find all inspections with SyncStatus=PENDING"""
        
    def find_by_lote(lote_id: String) -> List[Inspection]:
        """Find all inspections for a Lote"""
        
    def find_by_analista(analista_id: String) -> List[Inspection]:
        """Find all inspections by Analista"""
```

---

## 📍 BOUNDED CONTEXT 2: APPROVAL DOMAIN

### Purpose
Validar y aprobar/rechazar inspecciones registradas.

### Aggregates

#### Aggregate 1: Approval (Approval Aggregate Root)
```
Approval (Aggregate Root)
├── approvalId: UUID [Identity]
├── inspection: Inspection (Reference to Inspection Domain)
├── jefeQA: JefeQA (Reference)
├── decision: ApprovalDecision (Value Object)
├── rejectionReason: RejectionReason | NULL (Value Object)
├── timestamp: DateTime
└── status: ApprovalStatus enum

Status:
- PENDING: Awaiting Jefe QA review
- APPROVED: Inspection válida, reproceso necesario
- REJECTED: Inspection inválida, re-inspect
```

### Value Objects (Approval Domain)

#### ApprovalDecision
```
ApprovalDecision (Value Object - Enum)
- APPROVED
- REJECTED

Rules:
- Cada Approval MUST have decision
- Decision is immutable (no se puede cambiar después)
```

#### RejectionReason
```
RejectionReason (Value Object - Immutable)
├── reason: String
├── reasonCode: String (PHOTO_BLURRY, FALSE_ALARM, etc.)

Rules:
- Obligatorio si decision = REJECTED
- Mínimo 10 caracteres
- Razones sugeridas: "Foto borrosa", "Falsa alarma", "Defecto no confirmado"
```

### Domain Services (Approval Domain)

```python
class ApprovalService:
    def approve_inspection(
        inspection: Inspection,
        jefe_qa: JefeQA
    ) -> Approval:
        """Aprobar inspección."""
        approval = Approval(
            inspection=inspection,
            jefeQA=jefe_qa,
            decision=ApprovalDecision.APPROVED,
            timestamp=now()
        )
        # Publish event: InspectionApproved (para notificar Gerente)
        return approval

    def reject_inspection(
        inspection: Inspection,
        jefe_qa: JefeQA,
        reason: RejectionReason
    ) -> Approval:
        """Rechazar inspección con motivo."""
        approval = Approval(
            inspection=inspection,
            jefeQA=jefe_qa,
            decision=ApprovalDecision.REJECTED,
            rejectionReason=reason,
            timestamp=now()
        )
        # Publish event: InspectionRejected
        return approval
```

### Repository (Approval Domain)

```python
class ApprovalRepository:
    def save(approval: Approval) -> None:
        pass
        
    def find_pending() -> List[Approval]:
        """Find all pending approvals"""
```

### Domain Events (Approval Domain)

```
InspectionApproved(
    approvalId: UUID,
    inspectionId: UUID,
    jefe_qa: String,
    timestamp: DateTime
)
→ Publicado para que Gerente sea notificado en tiempo real

InspectionRejected(
    approvalId: UUID,
    inspectionId: UUID,
    reason: String,
    timestamp: DateTime
)
→ Publicado para notificar al Analista
```

---

## 📍 BOUNDED CONTEXT 3: MASTERS DOMAIN

### Purpose
Mantener catálogos (defectos, máquinas, telas) que son referencias en otros dominios.

### Aggregates

#### Aggregate 1: Defect (Defect Aggregate Root)
```
Defect (Aggregate Root - Master)
├── defectId: String (DEF-TON) [Identity]
├── defectName: String (TONODIFFERENTE)
├── description: String
├── typicalProcess: String (TINTORERIA)
├── typicalMachine: Machine (Reference)
└── status: MasterStatus enum (ACTIVE, INACTIVE)

Rules:
- Unique per defectId
- 25+ defectos cargar en setup
```

#### Aggregate 2: Machine (Machine Aggregate Root)
```
Machine (Aggregate Root - Master)
├── machineId: String (MAQ-AGO-80) [Identity]
├── machineName: String (AGOTAMIENTO 80)
├── process: String (TINTORERIA)
└── status: MasterStatus enum
```

#### Aggregate 3: Fabric (Fabric Aggregate Root)
```
Fabric (Aggregate Root - Master)
├── fabricId: String (TEJ-001) [Identity]
├── fabricName: String (NOVAKREPEL)
├── composition: String (100% algodón)
├── width: float (cm)
├── weight: float (gsm)
└── status: MasterStatus enum
```

### Domain Services (Masters Domain)

```python
class MastersService:
    def create_defect(defect_data: DefectInput) -> Defect:
        """Create new defect in catalog"""
        defect = Defect(
            defectId=defect_data.id,
            defectName=defect_data.name,
            ...
        )
        return defect

    def inactivate_defect(defect_id: String) -> Defect:
        """Soft delete: marca inactivo, no borra histórico"""
        defect = defectRepository.find(defect_id)
        defect.status = MasterStatus.INACTIVE
        return defect

    def bulk_import_masters(csv_file) -> BulkImportResult:
        """Import CSV: 25 defects, 15 machines, 20 fabrics"""
        # Validate duplicates
        # Import with progress
        # Return: # imported, # errors
```

### Repository (Masters Domain)

```python
class DefectRepository:
    def save(defect: Defect) -> None:
        pass
        
    def find_by_id(defect_id: String) -> Defect | None:
        pass
        
    def find_all_active() -> List[Defect]:
        pass
```

---

## 🔄 CROSS-DOMAIN INTERACTIONS

### Interaction 1: Inspection Domain → Masters Domain
```
InspectionService.register_inspection(defectType=DefectType):
  1. Validate defectType exists in DefectRepository (Masters Domain)
  2. Get typicalMachine from Defect
  3. Create Inspection with those references
  
Rule: Masters Domain is READ-ONLY from Inspection Domain
```

### Interaction 2: Approval Domain → Inspection Domain
```
ApprovalService.approve_inspection(inspection: Inspection):
  1. Read Inspection (reference)
  2. Create Approval
  3. Publish InspectionApproved event
  
Rule: Approval references Inspection, not vice versa (no circular dependency)
```

### Interaction 3: Events & Notifications
```
InspectionApproved event (Approval Domain)
  ↓
Event Bus (Infrastructure Layer)
  ↓
NotificationService (Application Service)
  ↓
Notify Gerente (UI, email, etc.)
  
Rule: Loose coupling via events
```

---

## 📊 AGGREGATES SUMMARY

| Aggregate | Bounded Context | Root | Value Objects | Key Rules |
|-----------|---|---|---|---|
| Lote | Inspection | Lote | - | Unique per HDR, has many Inspections |
| Inspection | Inspection | Inspection | DefectType, Comment, Photograph, InspectionTime | Obligatorio: defect, comment, photo, machine |
| Approval | Approval | Approval | ApprovalDecision, RejectionReason | Immutable after creation |
| Defect | Masters | Defect | - | Read-only from other domains |
| Machine | Masters | Machine | - | Read-only from other domains |
| Fabric | Masters | Fabric | - | Read-only from other domains |

---

## 🏗️ LAYERED ARCHITECTURE (DDD Style)

```
┌─────────────────────────────────────────────────────┐
│            PRESENTATION LAYER                       │
│      (React Components, Pages, Forms)               │
└────────────────────┬────────────────────────────────┘
                     │
┌─────────────────────────────────────────────────────┐
│          APPLICATION LAYER                          │
│   (Use Cases, DTOs, Request/Response Mapping)       │
│   - InspectionApplicationService                    │
│   - ApprovalApplicationService                      │
│   - MastersApplicationService                       │
│   - AuthenticationService                           │
└────────────────────┬────────────────────────────────┘
                     │
┌─────────────────────────────────────────────────────┐
│          DOMAIN LAYER (DDD Core)                    │
│   Bounded Contexts:                                 │
│   - Inspection Domain (Aggregates, Value Objects)   │
│   - Approval Domain (Aggregates, Value Objects)     │
│   - Masters Domain (Aggregates, Value Objects)      │
│   Domain Services, Domain Events                    │
└────────────────────┬────────────────────────────────┘
                     │
┌─────────────────────────────────────────────────────┐
│       INFRASTRUCTURE LAYER                          │
│   - Repositories (ORM: SQLAlchemy)                  │
│   - Event Bus                                       │
│   - Service Worker (offline sync)                   │
│   - Database (PostgreSQL)                           │
│   - File Storage (IndexedDB, filesystem)            │
└─────────────────────────────────────────────────────┘
```

---

## 🎯 DDD PRINCIPLES APPLIED

| Principle | How Applied | Benefit |
|-----------|-------------|---------|
| **Ubiquitous Language** | Defect, Inspection, Approval, etc. | Devs + domain experts speak same language |
| **Bounded Contexts** | 3 contexts (Inspection, Approval, Masters) | Clear separation of concerns |
| **Aggregates** | Inspection, Approval, etc. (roots) | Transaction boundaries, consistency |
| **Value Objects** | DefectType, Comment, Photograph, etc. | Immutable, equals by value |
| **Domain Services** | InspectionService, ApprovalService | Business logic in domain, not application |
| **Domain Events** | InspectionApproved, InspectionRejected | Loose coupling, async communication |
| **Repositories** | InspectionRepository, ApprovalRepository | Persistence abstraction |

---

## ✅ DDD DESIGN VALIDATION

- [ ] Bounded Contexts separados (Inspection, Approval, Masters)
- [ ] Aggregates with clear roots (Lote, Inspection, Approval)
- [ ] Value Objects immutable (DefectType, Comment, Photograph)
- [ ] Domain Services with business logic (not anemic)
- [ ] Repositories for persistence abstraction
- [ ] Domain Events for cross-context communication
- [ ] No circular dependencies between contexts
- [ ] Masters domain is read-only from other contexts

---

## 🚀 PRÓXIMOS PASOS

1. ✅ DDD Design completado
2. ➡️ **CODE GENERATION** (Backend FastAPI + Frontend React)
   - Application Services (DTOs, use cases)
   - Controllers/Routes (HTTP endpoints)
   - Repository implementations
   - React Components

---

**Status**: ✅ DDD DESIGN COMPLETADO - LISTO PARA CODE GENERATION

