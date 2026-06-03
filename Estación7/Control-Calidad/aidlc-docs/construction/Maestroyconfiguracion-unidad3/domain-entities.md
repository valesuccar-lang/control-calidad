# Domain Entities — Unit 3: Maestros y Configuración
## Activity 1: Functional Design

**Date**: 2026-06-01  
**Status**: DESIGN PHASE  
**Bounded Context**: Masters Domain  
**Decision Makers**: Backend + DDD Team

---

## 🏗️ BOUNDED CONTEXT: MASTERS DOMAIN

### Purpose
Gestión de datos maestros (defects, machines, fabrics) que son catálogos de referencia para las inspecciones. Este dominio es principalmente CRUD con validaciones de unicidad y configuración inicial de la fábrica.

### Scope
- Crear, actualizar, listar, inactivar (soft delete) defects, machines, fabrics
- CSV bulk import con validación y manejo de errores
- Configuración inicial (setup wizard)
- Gestión de usuarios y roles

### Ubicación en la Arquitectura
```
┌─────────────────────────────────────────┐
│     INSPECTION DOMAIN (Unit 1)          │
│  (Crear inspecciones, capturar fotos)   │
└────────────┬────────────────────────────┘
             │ references
             ↓
┌─────────────────────────────────────────┐
│     MASTERS DOMAIN (Unit 3) ← HERE      │
│  (Defects, Machines, Fabrics)           │
└────────────┬────────────────────────────┘
             │ references
             ↓
┌─────────────────────────────────────────┐
│      APPROVAL DOMAIN (Unit 1)           │
│  (Aprobar inspecciones)                 │
└─────────────────────────────────────────┘
```

---

## 📦 AGGREGATES & ENTITIES

### 1. DEFECT AGGREGATE

**Root Entity**: Defect

```python
# Domain Model
class Defect:
    """Aggregate Root: Tipo de defecto encontrado en telas"""
    
    # Identity
    id: DefectId  # DEF-TON, DEF-MAY, etc. (Unique, immutable)
    
    # Core Properties
    name: DefectName           # TONODIFFERENTE, MAYADO, etc. (Unique)
    description: Optional[Description]
    typical_process: Optional[Process]  # TINTORERIA, TEÑIDO, ACABADO, etc.
    typical_machine_id: Optional[MachineId]
    
    # Lifecycle
    status: DefectStatus       # ACTIVE, ARCHIVED
    created_at: DateTime
    created_by: UserId
    updated_at: DateTime
    updated_by: UserId
    
    # Metadata
    usage_count: Int           # Number of inspections using this defect
    is_system: Bool            # True = built-in, cannot delete
```

#### Defect Value Objects

```python
class DefectId(ValueObject):
    """Unique identifier for defect"""
    id: str  # Format: DEF-[A-Z0-9]{3,}
    
    def __init__(self, id: str):
        if not self._is_valid(id):
            raise InvalidDefectIdError(f"Invalid format: {id}")
        self.id = id
    
    @staticmethod
    def _is_valid(id: str) -> bool:
        return re.match(r'^DEF-[A-Z0-9]{3,}$', id) is not None
    
    def __eq__(self, other):
        return self.id == other.id
    
    def __hash__(self):
        return hash(self.id)


class DefectName(ValueObject):
    """Name of defect"""
    name: str
    
    def __init__(self, name: str):
        if len(name) < 3 or len(name) > 100:
            raise InvalidDefectNameError("Name must be 3-100 chars")
        if not name.strip():
            raise InvalidDefectNameError("Name cannot be blank")
        self.name = name.strip().upper()
    
    def __eq__(self, other):
        return self.name == other.name


class Description(ValueObject):
    """Description of defect"""
    text: str
    max_length: ClassVar[int] = 500
    
    def __init__(self, text: Optional[str]):
        if text is None:
            self.text = None
            return
        if len(text) > self.max_length:
            raise InvalidDescriptionError(f"Max {self.max_length} chars")
        self.text = text.strip()


class Process(ValueObject):
    """Manufacturing process where defect typically occurs"""
    process: str
    valid_processes = [
        "TINTORERIA", "TEÑIDO", "ACABADO", "TEJIDO", 
        "CARDADO", "PEINADO", "RETORCIMIENTO"
    ]
    
    def __init__(self, process: str):
        if process not in self.valid_processes:
            raise InvalidProcessError(f"Unknown process: {process}")
        self.process = process


class DefectStatus(Enum):
    """Lifecycle status"""
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
```

#### Defect Aggregate Invariants

```python
class DefectInvariants:
    """Business rules that must always be true"""
    
    @staticmethod
    def validate_on_creation(id: DefectId, name: DefectName) -> None:
        """Validate before creating new defect"""
        # Rule 1: ID must be unique (checked in repository)
        # Rule 2: Name must be unique (checked in repository)
        # Rule 3: System defects cannot be deleted
        pass
    
    @staticmethod
    def validate_on_update(defect: Defect, updated_name: DefectName) -> None:
        """Validate before updating"""
        # Rule 1: Cannot change system defect
        if defect.is_system:
            raise CannotModifySystemDefectError()
        
        # Rule 2: New name must be unique
        # (checked in repository before persistence)
        pass
    
    @staticmethod
    def validate_on_archive(defect: Defect, usage_count: Int) -> None:
        """Validate before archiving"""
        # Rule 1: Can only archive if no recent usages
        # (inspections from last 30 days)
        if usage_count > 0:
            raise CannotArchiveActiveDefectError(
                f"Defect in use: {usage_count} recent inspections"
            )
        
        # Rule 2: System defects cannot be archived
        if defect.is_system:
            raise CannotArchiveSystemDefectError()
```

---

### 2. MACHINE AGGREGATE

**Root Entity**: Machine

```python
class Machine:
    """Aggregate Root: Máquina que produce defectos"""
    
    # Identity
    id: MachineId            # MAQ-AGO-80, MAQ-TIN-120, etc.
    
    # Core Properties
    name: MachineName        # AGOTAMIENTO 80, TINTORERIA 120, etc.
    process: Optional[Process]
    manufacturer: Optional[str]
    model: Optional[str]
    installation_date: Optional[Date]
    
    # Status & Lifecycle
    status: MachineStatus    # ACTIVE, MAINTENANCE, DECOMMISSIONED
    created_at: DateTime
    updated_at: DateTime
    
    # Metadata
    is_system: Bool          # True = built-in
    defect_count: Int        # # of defects linked to this machine
```

#### Machine Value Objects

```python
class MachineId(ValueObject):
    id: str  # MAQ-[A-Z]{3}-[0-9]{1,3}
    
    def __init__(self, id: str):
        if not re.match(r'^MAQ-[A-Z]{3}-[0-9]{1,3}$', id):
            raise InvalidMachineIdError(f"Invalid format: {id}")
        self.id = id


class MachineName(ValueObject):
    name: str
    
    def __init__(self, name: str):
        if len(name) < 3 or len(name) > 150:
            raise InvalidMachineNameError("Name must be 3-150 chars")
        self.name = name.strip().upper()


class MachineStatus(Enum):
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    DECOMMISSIONED = "DECOMMISSIONED"
```

---

### 3. FABRIC AGGREGATE

**Root Entity**: Fabric

```python
class Fabric:
    """Aggregate Root: Tela/composición de referencia"""
    
    # Identity
    id: FabricId            # NOVAKREPEL, PERCHERON, etc.
    
    # Core Properties
    name: FabricName        # nombre comercial
    composition: Optional[Composition]  # 100% Poliéster, 80% Algodón+20% Pol., etc.
    width_cm: Optional[Decimal]
    weight_gsm: Optional[Decimal]  # grams per square meter
    
    # Status & Lifecycle
    status: FabricStatus    # ACTIVE, ARCHIVED
    created_at: DateTime
    updated_at: DateTime
    
    # Metadata
    is_system: Bool
    lote_count: Int         # # of lotes using this fabric
```

#### Fabric Value Objects

```python
class FabricId(ValueObject):
    id: str  # NOVAKREPEL, PERCHERON, etc. (uppercase, alphanumeric)
    
    def __init__(self, id: str):
        normalized = id.strip().upper()
        if not re.match(r'^[A-Z0-9]{3,30}$', normalized):
            raise InvalidFabricIdError(f"Invalid format: {id}")
        self.id = normalized


class FabricName(ValueObject):
    name: str
    
    def __init__(self, name: str):
        if len(name) < 3 or len(name) > 150:
            raise InvalidFabricNameError("Name must be 3-150 chars")
        self.name = name.strip()


class Composition(ValueObject):
    """Fiber composition, e.g., '100% Polyester' or '80% Cotton + 20% Polyester'"""
    composition: str
    
    def __init__(self, composition: str):
        if len(composition) > 200:
            raise InvalidCompositionError("Max 200 chars")
        # Could add validation for known fibers, percentages, etc.
        self.composition = composition.strip()


class FabricStatus(Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
```

---

## 🎯 DOMAIN SERVICES

### MastersService

```python
class MastersService:
    """Domain service for Masters domain operations"""
    
    def __init__(self, 
                 defect_repository: DefectRepository,
                 machine_repository: MachineRepository,
                 fabric_repository: FabricRepository,
                 event_bus: EventBus):
        self.defects = defect_repository
        self.machines = machine_repository
        self.fabrics = fabric_repository
        self.events = event_bus
    
    # ========== DEFECT OPERATIONS ==========
    
    def create_defect(self, 
                     id: DefectId,
                     name: DefectName,
                     description: Optional[Description],
                     typical_process: Optional[Process],
                     typical_machine_id: Optional[MachineId],
                     created_by: UserId) -> Defect:
        """Create new defect with validation"""
        
        # Rule 1: Validate aggregate invariants
        DefectInvariants.validate_on_creation(id, name)
        
        # Rule 2: Check uniqueness (in repository)
        if self.defects.exists_by_id(id):
            raise DuplicateDefectIdError(f"Defect ID already exists: {id}")
        
        if self.defects.exists_by_name(name):
            raise DuplicateDefectNameError(f"Defect name already exists: {name}")
        
        # Rule 3: Validate machine exists if provided
        if typical_machine_id:
            if not self.machines.exists(typical_machine_id):
                raise MachineNotFoundError(f"Machine not found: {typical_machine_id}")
        
        # Create aggregate
        defect = Defect(
            id=id,
            name=name,
            description=description,
            typical_process=typical_process,
            typical_machine_id=typical_machine_id,
            status=DefectStatus.ACTIVE,
            created_by=created_by,
            created_at=datetime.utcnow(),
            is_system=False
        )
        
        # Persist
        self.defects.save(defect)
        
        # Publish domain event
        self.events.publish(DefectCreatedEvent(
            defect_id=id,
            name=name,
            timestamp=datetime.utcnow()
        ))
        
        return defect
    
    
    def update_defect(self,
                     id: DefectId,
                     name: Optional[DefectName],
                     description: Optional[Description],
                     typical_process: Optional[Process],
                     typical_machine_id: Optional[MachineId],
                     updated_by: UserId) -> Defect:
        """Update defect with validation"""
        
        defect = self.defects.get_by_id(id)
        if not defect:
            raise DefectNotFoundError(f"Defect not found: {id}")
        
        # Rule 1: Cannot modify system defects
        if defect.is_system:
            raise CannotModifySystemDefectError()
        
        # Rule 2: Validate new name uniqueness
        if name and name != defect.name:
            if self.defects.exists_by_name(name):
                raise DuplicateDefectNameError(f"Name already exists: {name}")
        
        # Rule 3: Validate machine exists
        if typical_machine_id and typical_machine_id != defect.typical_machine_id:
            if not self.machines.exists(typical_machine_id):
                raise MachineNotFoundError(f"Machine not found: {typical_machine_id}")
        
        # Update
        if name:
            defect.name = name
        if description is not None:
            defect.description = description
        if typical_process:
            defect.typical_process = typical_process
        if typical_machine_id:
            defect.typical_machine_id = typical_machine_id
        
        defect.updated_at = datetime.utcnow()
        defect.updated_by = updated_by
        
        # Persist
        self.defects.save(defect)
        
        # Publish event
        self.events.publish(DefectUpdatedEvent(
            defect_id=id,
            timestamp=datetime.utcnow()
        ))
        
        return defect
    
    
    def archive_defect(self, 
                      id: DefectId,
                      updated_by: UserId) -> None:
        """Archive (soft delete) defect"""
        
        defect = self.defects.get_by_id(id)
        if not defect:
            raise DefectNotFoundError(f"Defect not found: {id}")
        
        # Rule 1: Cannot archive system defects
        if defect.is_system:
            raise CannotArchiveSystemDefectError()
        
        # Rule 2: Check no recent usage
        recent_usage_count = self.defects.count_recent_usages(id, days=30)
        DefectInvariants.validate_on_archive(defect, recent_usage_count)
        
        # Archive
        defect.status = DefectStatus.ARCHIVED
        defect.updated_at = datetime.utcnow()
        defect.updated_by = updated_by
        
        self.defects.save(defect)
        
        self.events.publish(DefectArchivedEvent(
            defect_id=id,
            timestamp=datetime.utcnow()
        ))
    
    
    # ========== MACHINE OPERATIONS ==========
    
    def create_machine(self,
                      id: MachineId,
                      name: MachineName,
                      process: Optional[Process],
                      manufacturer: Optional[str],
                      model: Optional[str],
                      installation_date: Optional[Date],
                      created_by: UserId) -> Machine:
        """Create new machine"""
        
        # Validate uniqueness
        if self.machines.exists_by_id(id):
            raise DuplicateMachineIdError(f"Machine ID already exists: {id}")
        
        if self.machines.exists_by_name(name):
            raise DuplicateMachineNameError(f"Machine name already exists: {name}")
        
        machine = Machine(
            id=id,
            name=name,
            process=process,
            manufacturer=manufacturer,
            model=model,
            installation_date=installation_date,
            status=MachineStatus.ACTIVE,
            created_at=datetime.utcnow(),
            is_system=False
        )
        
        self.machines.save(machine)
        
        self.events.publish(MachineCreatedEvent(
            machine_id=id,
            name=name,
            timestamp=datetime.utcnow()
        ))
        
        return machine
    
    
    # ========== FABRIC OPERATIONS ==========
    
    def create_fabric(self,
                     id: FabricId,
                     name: FabricName,
                     composition: Optional[Composition],
                     width_cm: Optional[Decimal],
                     weight_gsm: Optional[Decimal],
                     created_by: UserId) -> Fabric:
        """Create new fabric"""
        
        # Validate uniqueness
        if self.fabrics.exists_by_id(id):
            raise DuplicateFabricIdError(f"Fabric ID already exists: {id}")
        
        if self.fabrics.exists_by_name(name):
            raise DuplicateFabricNameError(f"Fabric name already exists: {name}")
        
        fabric = Fabric(
            id=id,
            name=name,
            composition=composition,
            width_cm=width_cm,
            weight_gsm=weight_gsm,
            status=FabricStatus.ACTIVE,
            created_at=datetime.utcnow(),
            is_system=False
        )
        
        self.fabrics.save(fabric)
        
        self.events.publish(FabricCreatedEvent(
            fabric_id=id,
            name=name,
            timestamp=datetime.utcnow()
        ))
        
        return fabric
```

---

## 📤 DOMAIN EVENTS

```python
class DefectCreatedEvent(DomainEvent):
    """Published when defect created"""
    defect_id: DefectId
    name: DefectName
    timestamp: DateTime


class DefectUpdatedEvent(DomainEvent):
    """Published when defect updated"""
    defect_id: DefectId
    timestamp: DateTime


class DefectArchivedEvent(DomainEvent):
    """Published when defect archived (soft delete)"""
    defect_id: DefectId
    timestamp: DateTime


class MachineCreatedEvent(DomainEvent):
    machine_id: MachineId
    name: MachineName
    timestamp: DateTime


class MachineUpdatedEvent(DomainEvent):
    machine_id: MachineId
    timestamp: DateTime


class FabricCreatedEvent(DomainEvent):
    fabric_id: FabricId
    name: FabricName
    timestamp: DateTime


class FabricUpdatedEvent(DomainEvent):
    fabric_id: FabricId
    timestamp: DateTime


class CsvImportStartedEvent(DomainEvent):
    """Bulk import initiated"""
    filename: str
    record_count: Int
    timestamp: DateTime


class CsvImportCompletedEvent(DomainEvent):
    """Bulk import finished"""
    successful: Int
    failed: Int
    timestamp: DateTime
```

---

## 📊 REPOSITORY CONTRACTS

```python
class DefectRepository(ABC):
    """Persistence contract for Defect aggregate"""
    
    @abstractmethod
    def save(self, defect: Defect) -> None:
        """Persist defect (create or update)"""
        pass
    
    @abstractmethod
    def get_by_id(self, id: DefectId) -> Optional[Defect]:
        pass
    
    @abstractmethod
    def exists_by_id(self, id: DefectId) -> bool:
        pass
    
    @abstractmethod
    def exists_by_name(self, name: DefectName) -> bool:
        pass
    
    @abstractmethod
    def get_all(self, status: Optional[DefectStatus] = None) -> List[Defect]:
        """Get all defects, optionally filtered by status"""
        pass
    
    @abstractmethod
    def count_recent_usages(self, defect_id: DefectId, days: int) -> Int:
        """Count inspections using this defect in last N days"""
        pass
    
    @abstractmethod
    def delete(self, id: DefectId) -> None:
        """Hard delete (only for system data cleanup)"""
        pass


class MachineRepository(ABC):
    """Persistence contract for Machine aggregate"""
    
    @abstractmethod
    def save(self, machine: Machine) -> None:
        pass
    
    @abstractmethod
    def get_by_id(self, id: MachineId) -> Optional[Machine]:
        pass
    
    @abstractmethod
    def exists(self, id: MachineId) -> bool:
        pass
    
    @abstractmethod
    def exists_by_name(self, name: MachineName) -> bool:
        pass
    
    @abstractmethod
    def get_all(self, status: Optional[MachineStatus] = None) -> List[Machine]:
        pass


class FabricRepository(ABC):
    """Persistence contract for Fabric aggregate"""
    
    @abstractmethod
    def save(self, fabric: Fabric) -> None:
        pass
    
    @abstractmethod
    def get_by_id(self, id: FabricId) -> Optional[Fabric]:
        pass
    
    @abstractmethod
    def exists_by_id(self, id: FabricId) -> bool:
        pass
    
    @abstractmethod
    def exists_by_name(self, name: FabricName) -> bool:
        pass
    
    @abstractmethod
    def get_all(self, status: Optional[FabricStatus] = None) -> List[Fabric]:
        pass
```

---

## 🔄 CSV IMPORT USE CASE

```python
class ImportMastersUseCase:
    """Application service for CSV bulk import"""
    
    def __init__(self, 
                 masters_service: MastersService,
                 event_bus: EventBus):
        self.masters = masters_service
        self.events = event_bus
    
    def import_defects_from_csv(self, 
                               csv_file: BinaryIO,
                               imported_by: UserId) -> ImportResult:
        """
        Import defects from CSV
        Expected format:
        ID, NAME, DESCRIPTION, TYPICAL_PROCESS, TYPICAL_MACHINE_ID
        DEF-TON, TONODIFFERENTE, Variación de tono, TINTORERIA, MAQ-TIN-120
        """
        
        result = ImportResult(successful=0, failed=0, errors=[])
        
        self.events.publish(CsvImportStartedEvent(
            filename=csv_file.name,
            record_count=0,  # Will update
            timestamp=datetime.utcnow()
        ))
        
        try:
            rows = self._parse_csv(csv_file)
            
            for row_num, row in enumerate(rows, start=2):  # Skip header
                try:
                    # Parse
                    defect_id = DefectId(row.get('ID'))
                    defect_name = DefectName(row.get('NAME'))
                    description = Description(row.get('DESCRIPTION'))
                    typical_process = Process(row.get('TYPICAL_PROCESS')) if row.get('TYPICAL_PROCESS') else None
                    typical_machine_id = MachineId(row.get('TYPICAL_MACHINE_ID')) if row.get('TYPICAL_MACHINE_ID') else None
                    
                    # Create
                    self.masters.create_defect(
                        id=defect_id,
                        name=defect_name,
                        description=description,
                        typical_process=typical_process,
                        typical_machine_id=typical_machine_id,
                        created_by=imported_by
                    )
                    
                    result.successful += 1
                    
                except (ValueError, DomainException) as e:
                    result.failed += 1
                    result.errors.append(ImportError(
                        row_number=row_num,
                        message=str(e)
                    ))
        
        except Exception as e:
            result.errors.append(ImportError(
                row_number=0,
                message=f"File read error: {str(e)}"
            ))
        
        self.events.publish(CsvImportCompletedEvent(
            successful=result.successful,
            failed=result.failed,
            timestamp=datetime.utcnow()
        ))
        
        return result
    
    @staticmethod
    def _parse_csv(csv_file: BinaryIO) -> List[Dict[str, str]]:
        """Parse CSV file into dictionaries"""
        import csv
        reader = csv.DictReader(csv_file)
        return list(reader)
```

---

## ✅ AGGREGATE CHECKLIST

- [x] Defect Aggregate (root entity, value objects, invariants)
- [x] Machine Aggregate (root entity, value objects)
- [x] Fabric Aggregate (root entity, value objects)
- [x] MastersService (business logic, domain rules)
- [x] Domain Events (DefectCreated, MachineCreated, etc.)
- [x] Repository Contracts (Defect, Machine, Fabric)
- [x] CSV Import Use Case (with validation & error handling)
- [x] Business Invariants (documented in code)
- [x] Domain Exceptions (duplicates, not found, cannot modify, etc.)

---

**Status**: ✅ DOMAIN DESIGN COMPLETADO  
**Next**: Activity 2 (NFR Requirements) para Unit 3  
**Estimated Effort**: 4 días para implementación (backend CRUD)

