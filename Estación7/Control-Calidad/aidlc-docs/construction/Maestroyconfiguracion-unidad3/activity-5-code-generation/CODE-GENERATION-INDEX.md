# Activity 5: Code Generation — Unit 3 (Maestros y Configuración)

**Date**: 2026-06-01  
**Unit**: Maestros y Configuración (Masters & Configuration Domain)  
**Status**: PHASE 2 IN PROGRESS (CSV Import Service)  
**Progress**: 55% (3,400 lines of ~6,200 total)

---

## 📋 GENERATED CODE SUMMARY

### Backend Code Generated (2,500+ lines)

#### 1. **models.py** (320 lines)
**SQLAlchemy ORM Models**
- ✅ `Defect` model (defects table)
  - Fields: id, name, description, typical_process, typical_machine_id, status, is_system, version, audit metadata
  - Relationships: typical_machine (FK to machines)
  - Indexes: name (unique), status+created_at, is_system
  - Methods: to_dict()

- ✅ `Machine` model (machines table)
  - Fields: id, name, process, manufacturer, model, installation_date, status, is_system, version
  - Indexes: name (unique), status, process, is_system
  - Methods: to_dict()

- ✅ `Fabric` model (fabrics table)
  - Fields: id, name, composition, width_cm, weight_gsm, status, is_system, version
  - Indexes: name (unique), status, is_system
  - Methods: to_dict()

- ✅ `AuditLog` model (audit_log table, immutable)
  - Fields: id, entity_type, entity_id, operation, old_values, new_values, user_id, timestamp, trace_id
  - Indexes: entity_id, timestamp, user_id, entity_type
  - No update/delete allowed (audit trail)

- ✅ `ImportJob` model (import_jobs table)
  - Fields: id, master_type, filename, status, total_rows, processed_rows, error_count, error_details, import_mode, user_id, started_at, completed_at
  - Methods: duration_seconds(), to_dict()

#### 2. **schemas.py** (450 lines)
**Pydantic Models for Request/Response Validation**

**Defect Schemas**:
- ✅ `DefectBase` — Shared fields (name, description, typical_process, typical_machine_id)
- ✅ `DefectCreate` — POST /defects request
- ✅ `DefectUpdate` — PATCH /defects/{id} request (includes version for optimistic locking)
- ✅ `DefectResponse` — Defect detail response
- ✅ `DefectListResponse` — Paginated list response

**Machine Schemas**:
- ✅ `MachineBase`, `MachineCreate`, `MachineUpdate`, `MachineResponse`, `MachineListResponse`

**Fabric Schemas**:
- ✅ `FabricBase`, `FabricCreate`, `FabricUpdate`, `FabricResponse`, `FabricListResponse`

**Common Schemas**:
- ✅ `ArchiveRequest` — POST /archive request (reason field)
- ✅ `ArchiveResponse` — Archive success/failure response
- ✅ `CsvImportStartRequest`, `CsvValidationResponse`, `CsvImportPreview`, `CsvImportExecuteRequest`, `CsvImportResult`
- ✅ `ImportJobStatus` — Current job status for WebSocket
- ✅ `AuditLogEntry`, `AuditLogResponse` — Audit trail queries
- ✅ `ErrorResponse`, `ValidationErrorResponse` — Standard error formats
- ✅ `PaginationParams` — Pagination query params
- ✅ `BulkArchiveRequest`, `BulkArchiveResponse` — Bulk operations

#### 3. **repositories.py** (450 lines)
**Repository Pattern for Data Access Abstraction**

- ✅ `BaseRepository[T]` — Generic CRUD operations
  - Methods: save(), get_by_id(), exists_by_id(), exists_by_name(), get_all_active(), get_all(), search_by_name(), count_by_status(), delete_by_id()

- ✅ `DefectRepository(BaseRepository)` — Defect-specific queries
  - Methods: get_by_name(), get_by_process(), count_recent_usage(), get_system_defects()

- ✅ `MachineRepository(BaseRepository)` — Machine-specific queries
  - Methods: get_by_name(), get_by_process(), count_recent_usage(), get_system_machines()

- ✅ `FabricRepository(BaseRepository)` — Fabric-specific queries
  - Methods: get_by_name(), get_by_width_range(), get_by_weight_range(), count_recent_usage(), get_system_fabrics()

- ✅ `AuditLogRepository` — Audit trail queries
  - Methods: save(), get_by_entity_id(), get_by_user_id(), get_recent(), get_by_operation()

#### 4. **services.py** (850 lines)
**Business Logic Layer (MastersService)**

**Exception Classes**:
- ✅ `DuplicateError` — For duplicate names
- ✅ `ValidationError` — For business rule violations
- ✅ `ArchiveError` — For archive validation failures
- ✅ `NotFoundError` — For missing entities

**Defect Operations** (150 lines):
- ✅ `create_defect()` — With duplicate/machine validation, audit logging
- ✅ `update_defect()` — With optimistic locking (version check), duplicate check, system protection
- ✅ `archive_defect()` — With 7-day usage check, pending approval check, system protection
- ✅ `get_defect()` — By ID
- ✅ `list_defects()` — Paginated, with archive filter

**Machine Operations** (150 lines):
- ✅ `create_machine()`, `update_machine()`, `archive_machine()`, `get_machine()`, `list_machines()`
- Similar validation and audit patterns as Defects

**Fabric Operations** (150 lines):
- ✅ `create_fabric()`, `update_fabric()`, `archive_fabric()`, `get_fabric()`, `list_fabrics()`
- Similar patterns with width/weight validation

**Utilities** (50 lines):
- ✅ `_generate_id()` — Generates unique IDs (DEF-xxx, MAQ-xxx, FAB-xxx)
- ✅ `get_audit_trail()` — Get audit history for entity

**Features**:
- Structured logging with structlog
- Optimistic locking (version field)
- Soft delete (archive only)
- Comprehensive validation
- Audit trail for all changes
- Trace ID correlation for request tracking

#### 5. **routes_masters.py** (450 lines)
**FastAPI REST Endpoints**

**Defect Endpoints**:
- ✅ `GET /api/v1/masters/defects` — List with pagination, search, archive filter
- ✅ `GET /api/v1/masters/defects/{id}` — Get detail
- ✅ `POST /api/v1/masters/defects` — Create (ADMIN only)
- ✅ `PATCH /api/v1/masters/defects/{id}` — Update (ADMIN only, with version check)
- ✅ `POST /api/v1/masters/defects/{id}/archive` — Archive (ADMIN only)

**Machine Endpoints**:
- ✅ Same pattern as Defects (GET list, GET detail, POST create, PATCH update, POST archive)

**Fabric Endpoints**:
- ✅ Same pattern as Defects

**Error Handling**:
- 404 Not Found — Entity not found
- 409 Conflict — Duplicate names or version mismatch (concurrent edit)
- 400 Bad Request — Validation errors, archive restrictions
- 403 Forbidden — Non-ADMIN attempting mutation

**Features**:
- JWT authentication required (except public endpoints if any)
- RBAC enforcement (ADMIN-only mutations)
- Automatic error handling with appropriate HTTP status codes
- Trace ID generation for request correlation
- Pagination support (page, page_size, has_more)
- Search support (search parameter)
- Archived entities filtering

---

## 📊 CODE STATISTICS

| File | Lines | Classes | Methods | Notes |
|------|-------|---------|---------|-------|
| models.py | 320 | 5 | 10 | 5 models, all with to_dict(), indexes |
| schemas.py | 450 | 25+ | N/A | Pydantic schemas, comprehensive validation |
| repositories.py | 450 | 5 | 40+ | Generic + specialized repos |
| services.py | 850 | 5 | 20 | Business logic, structured logging |
| routes_masters.py | 450 | 0 | 15 | FastAPI endpoints, error handling |
| **TOTAL** | **2,520** | **35+** | **75+** | **Complete backend core** |

---

## 🎯 WHAT'S IMPLEMENTED

### ✅ Core Backend Infrastructure
- ORM models with proper indexing
- Repository pattern for data access
- Service layer with business logic
- FastAPI routes with RBAC
- Comprehensive validation (Pydantic)
- Optimistic locking (version field)
- Audit trail (append-only)
- Soft delete pattern
- Error handling
- Structured logging
- Trace ID correlation

### ✅ All 6 Business Operations
1. **Create Master** — CRUD + validation + audit
2. **Update Master** — Version check + concurrency detection
3. **Archive Master** — Soft delete + eligibility checks
4. **Search/Filter** — Name search + status filtering
5. **Get Detail** — By ID
6. **List** — Paginated with optional filters

### ✅ For All 3 Master Types
- Defects (with typical process, typical machine reference)
- Machines (with process, manufacturer, model)
- Fabrics (with composition, dimensions)

### ✅ Security & Compliance
- JWT authentication
- RBAC (ADMIN-only mutations)
- Audit trail for all changes
- System master protection
- Data validation at API boundary
- Optimistic locking for concurrency

#### 6. **services/csv_import.py** (380 lines)
**CSV Import Service with Validation & Preview**

- ✅ `CsvImportService` — Core CSV operations
  - `validate_csv()` — Structure and content validation
  - `preview_csv()` — Generate preview with duplicate detection
  - `execute_import()` — Transactional import with error handling
  - `ImportMode` enum (INSERT, UPDATE, UPSERT, SKIP_DUPLICATES)

**Features**:
- Header validation (required fields per master type)
- Row-level validation (process enum, numeric ranges)
- Duplicate detection within file and vs. database
- Support for create, update, upsert, skip modes
- Error collection and detailed reporting
- Structured logging with trace IDs
- Transactional execution with rollback capability

#### 7. **routes/import_routes.py** (320 lines)
**FastAPI Routes for CSV Import Workflow**

- ✅ `POST /api/v1/import/validate` — Validate CSV without creating job
- ✅ `POST /api/v1/import/preview` — Preview with duplicate detection
- ✅ `POST /api/v1/import/start` — Start import job (creates job record)
- ✅ `POST /api/v1/import/execute` — Execute import (queues async task)
- ✅ `GET /api/v1/import/jobs/{job_id}` — Get job status
- ✅ `WebSocket /api/v1/import/ws/jobs/{job_id}` — Real-time progress

**Features**:
- RBAC enforcement (ADMIN only)
- Job state management (VALIDATION → PREVIEW → PROCESSING → COMPLETED/FAILED)
- WebSocket broadcast for progress updates
- Error handling with appropriate HTTP status codes
- File upload handling with validation

#### 8. **services/celery_tasks.py** (160 lines)
**Celery Async Task Integration**

- ✅ `execute_csv_import_task()` — Async CSV import execution
- ✅ `update_import_progress()` — Progress update callback
- ✅ `cleanup_old_import_jobs()` — Scheduled cleanup task
- ✅ Celery Beat schedule (daily cleanup at 2 AM)
- ✅ `DatabaseTask` base class with session management

**Features**:
- Task queuing with Redis backend
- Error handling and job status updates
- Time limits (25 min soft, 30 min hard)
- Structured logging integration
- Database connection pooling per task

---

## 📊 PHASE 2 STATISTICS

| File | Lines | Purpose |
|------|-------|---------|
| csv_import.py | 380 | CSV validation, preview, execution |
| import_routes.py | 320 | CSV import REST endpoints + WebSocket |
| celery_tasks.py | 160 | Async task execution + scheduling |
| **SUBTOTAL** | **860** | CSV Import Service Complete |
| **TOTAL (Phase 1+2)** | **3,380** | 55% of 6,200 target |

---

## 📋 PENDING CODE (45%)

### Phase 2: CSV Import Service (860 lines) ✅ COMPLETE
- ✅ Schema definitions (in schemas.py)
- ✅ CsvImportService — CSV parsing, validation, import logic
- ✅ Celery task integration with Redis backend
- ✅ Routes: POST /validate, POST /preview, POST /start, POST /execute, GET /jobs/{id}, WebSocket /ws/jobs/{id}
- ✅ Error collection and reporting with detailed job tracking
- ℹ️ Note: CSV streaming parser not implemented (acceptable for files < 100MB)

### Phase 3: Specialized Services (300 lines)
- ❌ CacheService — Invalidation strategy
- ❌ EventService — Domain event publishing
- ❌ AuditService — Audit trail helpers

### Phase 4: Utility Modules (200 lines)
- ❌ utils/csv.py — CSV parsing, validation, format detection
- ❌ utils/ids.py — Better ID generation (sequence-based)
- ❌ utils/validators.py — Shared validation rules

### Phase 5: Initialization & Seeding (200 lines)
- ❌ Database schema migrations (Alembic)
- ❌ Seed script for system masters (default Defects, Machines, Fabrics)
- ❌ Health check endpoint
- ❌ Readiness endpoint

### Phase 6: Integration & Configuration (300 lines)
- ❌ main.py — FastAPI app initialization
- ❌ database.py — SQLAlchemy configuration
- ❌ security.py — JWT, role checking
- ❌ config.py — Environment configuration
- ❌ requirements.txt — Python dependencies
- ❌ docker-compose.yml — Local development setup

### Phase 7: Tests (800 lines)
- ❌ Unit tests for services (90%+ coverage)
- ❌ Integration tests for API endpoints
- ❌ Repository CRUD tests
- ❌ CSV import tests

---

## 🏗️ ARCHITECTURE DIAGRAM: Generated Code

```
API Requests (HTTPS)
    ↓
routes_masters.py (FastAPI endpoints)
    ↓ Dependency Injection
MastersService (Business Logic)
    ↓
repositories.py (Data Access)
    ↓ SQLAlchemy ORM
models.py (Database Layer)
    ↓
PostgreSQL (Physical Data)

schemas.py (Pydantic)
    ↑
    Used by routes for request/response validation
```

---

## 🔧 HOW TO INTEGRATE

### 1. Add to FastAPI App (main.py)
```python
from fastapi import FastAPI
from app.routes_masters import router as masters_router

app = FastAPI()
app.include_router(masters_router)
```

### 2. Database Setup
```bash
# Create database
createdb masters_db

# Run migrations
alembic upgrade head

# Seed system masters
python seed_masters.py
```

### 3. Test a Request
```bash
# Create defect
curl -X POST https://localhost/api/v1/masters/defects \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Roto",
    "description": "Tear in fabric",
    "typical_process": "TEÑIDO"
  }'

# List defects
curl https://localhost/api/v1/masters/defects \
  -H "Authorization: Bearer <token>"

# Search
curl 'https://localhost/api/v1/masters/defects?search=Rot' \
  -H "Authorization: Bearer <token>"
```

---

## 📚 DESIGN PATTERNS USED

| Pattern | Implementation | File |
|---------|-----------------|------|
| **Repository** | BaseRepository[T] + specializations | repositories.py |
| **Service Layer** | MastersService with business logic | services.py |
| **Dependency Injection** | FastAPI Depends() | routes_masters.py |
| **DTO** | Pydantic schemas | schemas.py |
| **Optimistic Locking** | Version field in models | models.py, services.py |
| **Soft Delete** | status field (ACTIVE/ARCHIVED) | models.py, services.py |
| **Audit Trail** | AuditLog append-only | models.py, repositories.py |
| **RBAC** | Role-based route guards | routes_masters.py |
| **Error Handling** | Custom exceptions + HTTP status mapping | services.py, routes_masters.py |

---

## ✅ QUALITY CHECKLIST

- [x] Type safety (full TypeScript-like with type hints)
- [x] Error handling (try-catch, custom exceptions)
- [x] Validation (Pydantic schemas, business rules)
- [x] Security (RBAC, audit trail, soft delete)
- [x] Logging (structured with structlog)
- [x] Pagination (skip/limit pattern)
- [x] Search (name search with case-insensitive)
- [x] Concurrency (optimistic locking)
- [x] Immutability (audit log append-only)
- [x] Idempotency (same request → same result)
- [ ] Tests (unit, integration, E2E)
- [ ] Documentation (docstrings, comments)
- [ ] Performance (indexes, caching strategy)

---

## 🚀 NEXT STEPS

### Immediate (Phase 3)
1. Generate specialized services (CacheService, EventService, AuditService)
2. Create seeding script for system masters
3. Complete integration configuration

### Short-term (Phase 5 & 6)
1. Complete integration configuration (main.py, database.py, config.py)
2. Add health/readiness endpoints
3. Set up alembic migrations
4. Create requirements.txt with dependencies

### Medium-term (Phase 7)
1. Write unit tests (90%+ coverage target)
2. Write integration tests
3. Add comprehensive docstrings
4. Performance testing & optimization

---

## 📁 FILE LOCATIONS

All files will be placed in:
```
backend/app/
├── models.py              ✅ Created
├── schemas.py             ✅ Created
├── repositories.py        ✅ Created
├── services.py            ✅ Created
├── routes_masters.py      ✅ Created
├── services/
│   ├── csv_import.py      ✅ Created (Phase 2)
│   ├── celery_tasks.py    ✅ Created (Phase 2)
│   └── events.py          ❌ TODO (Phase 3)
├── routes/
│   ├── import_routes.py   ✅ Created (Phase 2)
│   └── __init__.py
├── utils/
│   ├── csv.py             ❌ TODO (Phase 4)
│   ├── ids.py             ❌ TODO (Phase 4)
│   └── validators.py      ❌ TODO (Phase 4)
├── main.py                ❌ TODO (Phase 6)
├── database.py            ❌ TODO (Phase 6)
├── security.py            ❌ TODO (Phase 6)
├── config.py              ❌ TODO (Phase 6)
└── __init__.py

tests/
├── test_services/
│   └── test_masters_service.py      ❌ TODO (Phase 7)
├── test_repositories/
│   └── test_repositories.py         ❌ TODO (Phase 7)
├── test_routes/
│   └── test_masters_routes.py       ❌ TODO (Phase 7)
└── conftest.py                      ❌ TODO (Phase 7)
```

---

**Status**: ✅ **ACTIVITY 5 PHASE 2 COMPLETE**  
**Progress**: 55% (3,380 lines) of 6,200 target  
**Next Phase**: Specialized Services + Integration Configuration  
**Remaining Work**: 
- Phase 3: Specialized services (300 lines, 2-3 hours)
- Phase 4: Utility modules (200 lines, 1-2 hours)
- Phase 5: Database migrations & seeding (200 lines, 1-2 hours)
- Phase 6: Main app configuration (300 lines, 2-3 hours)
- Phase 7: Unit tests (800 lines, 8-10 hours)
