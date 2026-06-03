# Units de Construcción × DDD Mapping
**Date**: 2026-05-27 | **Purpose**: Alinear 4 Units de construcción con 3 DDD Bounded Contexts

---

## 📍 QUICK MAPPING

```
DDD Contexts         Unit 1 (Backend API)    Unit 2 (Frontend)       Unit 3 (Masters)   Unit 4 (Offline)
────────────────────────────────────────────────────────────────────────────────────────────────────
Inspection Domain    ✅ routes/inspections   ✅ Inspection Page      ✅ APIoutils      ✅ Service Worker
                     ✅ services/inspection  ✅ CameraCapture        (CRUD initial)     ✅ IndexedDB
                     ✅ models/inspection    ✅ DefectSelector

Approval Domain      ✅ routes/approvals     ✅ Approval Page        -                  ✅ Sync queue
                     ✅ services/approval    ✅ PendingLotsTable
                     ✅ models/approval      ✅ ApprovalModal

Masters Domain       ✅ routes/masters       ✅ Config Page          ✅ MastersCRUD     -
                     ✅ services/masters     ✅ MastersTable         Form
                     ✅ models/defect,       ✅ ImportCSV Modal
                        machine, fabric
```

---

## 🏗️ UNIT 1: BACKEND API (Python FastAPI) — 10 días

### Scope
Implementar API REST que expone las 3 DDD Bounded Contexts.

### Code Structure
```
backend/
├── app/
│   ├── routes/
│   │   ├── inspections.py          # Inspection Context API
│   │   ├── approvals.py            # Approval Context API
│   │   ├── masters.py              # Masters Context API
│   │   └── auth.py                 # Auth (cross-context)
│   │
│   ├── domain/                     # DDD Core
│   │   ├── inspection/
│   │   │   ├── inspection.py       # Inspection Aggregate
│   │   │   ├── defect_type.py      # DefectType Value Object
│   │   │   ├── comment.py          # Comment Value Object
│   │   │   ├── photograph.py       # Photograph Value Object
│   │   │   ├── inspection_time.py  # InspectionTime Value Object
│   │   │   ├── services.py         # InspectionService (domain logic)
│   │   │   └── events.py           # Domain events
│   │   │
│   │   ├── approval/
│   │   │   ├── approval.py         # Approval Aggregate
│   │   │   ├── decision.py         # ApprovalDecision Value Object
│   │   │   ├── rejection_reason.py # RejectionReason Value Object
│   │   │   ├── services.py         # ApprovalService
│   │   │   └── events.py           # Domain events
│   │   │
│   │   ├── masters/
│   │   │   ├── defect.py           # Defect Aggregate
│   │   │   ├── machine.py          # Machine Aggregate
│   │   │   ├── fabric.py           # Fabric Aggregate
│   │   │   ├── services.py         # MastersService
│   │   │   └── master_status.py    # Enum
│   │   │
│   │   └── lote.py                 # Lote (shared across contexts)
│   │
│   ├── application/                # Application Layer
│   │   ├── inspection_use_cases.py # DTO + business orchestration
│   │   ├── approval_use_cases.py
│   │   ├── masters_use_cases.py
│   │   └── dtos.py                 # Request/response DTOs
│   │
│   ├── repositories/               # Infrastructure (Persistence)
│   │   ├── inspection_repository.py
│   │   ├── approval_repository.py
│   │   ├── defect_repository.py
│   │   ├── machine_repository.py
│   │   └── fabric_repository.py
│   │
│   ├── database.py                 # SQLAlchemy ORM models
│   └── main.py                     # FastAPI app entry
```

### Key Routes (API Contracts)

#### Inspection Context
```python
POST /api/inspections                    # Create inspection
  Request: { lote_id, defect_id, comment, photo_base64, machine_id }
  Response: { id, status, check_in, synced }

GET /api/inspections/pending-sync        # Get offline inspections (for sync)
  Response: List[Inspection]

GET /api/inspections/{id}                # Get details
GET /api/inspections/by-lote/{lote_id}   # Get by lote
GET /api/inspections/by-analista/{analista_id}  # Get my inspections
```

#### Approval Context
```python
GET /api/approvals/pending               # List pending for Jefe QA
  Response: List[PendingApproval]

POST /api/approvals                      # Create approval
  Request: { inspection_id, decision, rejection_reason? }
  Response: { id, inspection_id, status }

GET /api/approvals/{id}                  # Get approval details
```

#### Masters Context
```python
GET /api/masters/defects                 # List all defects
POST /api/masters/defects                # Create defect
PUT /api/masters/defects/{id}            # Edit defect
DELETE /api/masters/defects/{id}         # Inactivate defect

GET /api/masters/machines                # List machines
POST /api/masters/machines               # Create machine

GET /api/masters/fabrics                 # List fabrics
POST /api/masters/fabrics                # Create fabric

POST /api/masters/bulk-import            # Import CSV (defects, machines, fabrics)
```

### Testing Strategy (Unit 1)
- Unit tests: Services + Value Objects (pytest)
- Integration tests: API endpoints (FastAPI TestClient)
- Example:
```python
def test_create_inspection_valid():
    # Arrange: defect exists, machine exists
    # Act: POST /api/inspections
    # Assert: inspection created, timestamps set, photo stored
    
def test_create_inspection_missing_photo():
    # Arrange: photo is NULL
    # Act: POST /api/inspections
    # Assert: 400 Bad Request, message: "Photo is required"
```

---

## 🎨 UNIT 2: FRONTEND WEB (React + TypeScript) — 12 días

### Scope
Implementar UI para 3 Bounded Contexts (Inspection, Approval, Masters).

### Code Structure
```
frontend/
├── src/
│   ├── pages/
│   │   ├── Inspection/               # Inspection Context UI
│   │   │   ├── InspectionPage.tsx
│   │   │   ├── components/
│   │   │   │   ├── LoteSearchBar.tsx
│   │   │   │   ├── CameraCapture.tsx
│   │   │   │   ├── DefectSelector.tsx
│   │   │   │   ├── CommentInput.tsx
│   │   │   │   ├── MachineSelector.tsx
│   │   │   │   ├── OfflineIndicator.tsx
│   │   │   │   └── InspectionHistory.tsx
│   │   │   └── hooks/
│   │   │       └── useInspection.ts   # Custom hook (Inspection logic)
│   │   │
│   │   ├── Approval/                 # Approval Context UI
│   │   │   ├── ApprovalPage.tsx
│   │   │   ├── components/
│   │   │   │   ├── PendingLotsTable.tsx
│   │   │   │   ├── LoteDetailModal.tsx
│   │   │   │   ├── ApprovalDecision.tsx
│   │   │   │   └── ApprovalHistory.tsx
│   │   │   └── hooks/
│   │   │       └── useApproval.ts
│   │   │
│   │   ├── Config/                   # Masters Context UI
│   │   │   ├── ConfigPage.tsx
│   │   │   ├── components/
│   │   │   │   ├── MastersTab.tsx
│   │   │   │   ├── MastersCRUDForm.tsx
│   │   │   │   ├── MastersTable.tsx
│   │   │   │   ├── ImportCSVModal.tsx
│   │   │   │   └── UsersManagement.tsx
│   │   │   └── hooks/
│   │   │       └── useMasters.ts
│   │   │
│   │   ├── Auth/
│   │   │   ├── LoginPage.tsx
│   │   │   └── LogoutPage.tsx
│   │   │
│   │   └── Dashboard/
│   │       └── DashboardPage.tsx     # Basic KPI (no advanced analysis in MVP)
│   │
│   ├── components/
│   │   ├── Layout/
│   │   │   ├── Navbar.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Footer.tsx
│   │   ├── common/
│   │   │   ├── Button.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Table.tsx
│   │   │   └── Form.tsx
│   │   └── Auth/
│   │       ├── PrivateRoute.tsx      # RBAC guard
│   │       └── RoleGuard.tsx
│   │
│   ├── services/                     # API client
│   │   ├── api.ts                    # Axios + interceptors
│   │   ├── inspectionService.ts
│   │   ├── approvalService.ts
│   │   ├── mastersService.ts
│   │   └── authService.ts
│   │
│   ├── store/ (Zustand State Management)
│   │   ├── authStore.ts              # User, token, roles
│   │   ├── inspectionStore.ts        # Inspection state
│   │   ├── approvalStore.ts          # Approval state
│   │   ├── mastersStore.ts           # Masters state
│   │   └── offlineStore.ts           # Offline queue + sync status
│   │
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useFetch.ts
│   │   ├── useOfflineSync.ts         # Service Worker integration
│   │   └── useNotification.ts
│   │
│   ├── utils/
│   │   ├── validation.ts             # Validation logic
│   │   ├── formatters.ts             # Date, string formatting
│   │   ├── errorHandling.ts
│   │   └── offlineSync.ts            # Service Worker communication
│   │
│   ├── types/
│   │   ├── index.ts                  # TypeScript interfaces
│   │   └── api.ts                    # API response types
│   │
│   ├── App.tsx
│   └── index.tsx
│
├── public/
│   ├── index.html
│   ├── sw.js                         # Service Worker (offline-first)
│   └── manifest.json                 # PWA manifest
│
└── tests/
    ├── pages/                        # Component tests
    ├── services/                     # API client tests
    └── stores/                       # Zustand tests
```

### Key Components (by DDD Context)

#### Inspection Context Components
- `InspectionPage`: Container
- `LoteSearchBar`: Search/scan lote
- `CameraCapture`: Photo capture (offline)
- `DefectSelector`: Dropdown 25+ defects
- `CommentInput`: Comment input validation
- `MachineSelector`: Machine pre-filled + editable
- `InspectionHistory`: Table my inspections

#### Approval Context Components
- `ApprovalPage`: Container
- `PendingLotsTable`: List pending approvals
- `LoteDetailModal`: Photo + details
- `ApprovalDecision`: Buttons approve/reject

#### Masters Context Components
- `ConfigPage`: Container
- `MastersCRUDForm`: Generic form (defects, machines, fabrics)
- `MastersTable`: Table CRUD
- `ImportCSVModal`: CSV import

### Testing Strategy (Unit 2)
- Component tests: React Testing Library
- E2E tests: Cypress (critical flows)
- Example:
```typescript
test("Inspection: Capture photo successfully", async () => {
    // Arrange
    const { getByRole } = render(<InspectionPage />)
    
    // Act
    await userEvent.click(getByRole("button", { name: /Capturar Foto/i }))
    // (mock camera, select file)
    
    // Assert
    expect(getByAltText("preview")).toBeInTheDocument()
    expect(getByRole("button", { name: /Guardar/ })).not.toBeDisabled()
})
```

---

## 🗄️ UNIT 3: MAESTROS Y CONFIGURACIÓN (Backend) — 4 días

### Scope
CRUD maestros + initial setup (defects, machines, fabrics).

### Responsibilities
- `/api/masters/*` endpoints (defects, machines, fabrics)
- `/api/config/setup` (initial configuration wizard)
- `/api/users` (user + role management)
- CSV bulk import logic
- Database seeding with initial data

### Key Files (Unit 3)
```
backend/
├── domain/masters/
│   ├── defect.py
│   ├── machine.py
│   ├── fabric.py
│   └── services.py
├── routes/
│   ├── masters.py    # All /api/masters/* endpoints
│   ├── config.py     # /api/config/* endpoints
│   └── users.py      # /api/users endpoints
└── application/
    └── masters_use_cases.py  # Import logic, validation
```

### Testing (Unit 3)
- API endpoint tests (e.g., POST /api/masters/defects)
- CSV import validation (duplicate detection, error handling)
- Example:
```python
def test_import_csv_defects():
    # Arrange: CSV with 25 defects
    # Act: POST /api/masters/bulk-import
    # Assert: 25 defects created, 0 errors
    
def test_import_csv_duplicate_id():
    # Arrange: CSV has DEF-TON twice
    # Act: POST /api/masters/bulk-import
    # Assert: 400 Bad Request, message: "Duplicate ID: DEF-TON"
```

---

## 📡 UNIT 4: OFFLINE-FIRST & SYNCHRONIZATION (Backend) — 4 días

### Scope
Offline-first architecture: Service Worker + IndexedDB (frontend), sync queue (backend).

### Responsibilities

#### Frontend (Service Worker)
- Intercept POST/PUT requests
- Store in IndexedDB if offline
- Retry when online (background sync)
- Handle photo binary (blob storage)

#### Backend (Sync Endpoint)
- `/api/sync/upload-pending` endpoint
- Receive bulk offline inspections
- Validation + conflict resolution (server wins)
- Return: # synced, # errors

### Key Files (Unit 4)
```
backend/
├── routes/
│   └── sync.py                   # POST /api/sync/upload-pending
└── application/
    └── sync_use_cases.py         # Sync logic, validation

frontend/
├── public/
│   └── sw.js                     # Service Worker
└── utils/
    └── offlineSync.ts            # IndexedDB management
```

### Key Logic
```
Frontend Offline Flow:
1. Network goes down (navigator.onLine = false)
2. User captures photo + inspection
3. Presiona "Guardar"
4. Service Worker intercepts POST
5. Stores in IndexedDB: {inspection, photo_blob, synced: false}
6. Returns optimistic success to UI
7. UI shows "✓ Guardado localmente. Sincronizará..."
8. Network vuelve (navigator.onLine = true)
9. Service Worker detects online
10. Reads all {synced: false} from IndexedDB
11. POST /api/sync/upload-pending {inspections: [...], photos: [...]}
12. Backend validates + persists
13. Backend returns: {synced: 5, errors: 0}
14. Service Worker marks synced: true in IndexedDB
15. UI shows "✓ 5 registros sincronizados"
```

### Testing (Unit 4)
- Service Worker tests (chrome extensions)
- Offline sync integration tests
- Example:
```typescript
test("Offline inspection sync on network restore", async () => {
    // Arrange: offline, create inspection
    // Act: go online, trigger sync
    // Assert: POST /api/sync/upload-pending called
    // Assert: UI shows "✓ Sincronizado"
})
```

---

## 📋 UNITS SUMMARY

| Unit | Duration | Dev | DDD Mapping | Key Files |
|------|----------|-----|-------------|-----------|
| **1: Backend API** | 10 días | Backend | All 3 contexts | routes/, domain/, application/, repositories/ |
| **2: Frontend Web** | 12 días | Frontend (tú) | All 3 contexts | pages/, components/, services/, store/ |
| **3: Masters + Config** | 4 días | Backend | Masters Domain + Config | routes/masters.py, routes/config.py |
| **4: Offline Sync** | 4 días | Backend + Frontend | Infrastructure | sw.js, /api/sync/upload-pending |
| **Build & Test** | 2 días | Both | All | pytest, React Testing Library, Cypress |

**Total**: ~30 días (4 semanas) ✅ MVP

---

## ✅ DDD × Units VALIDATION

- [ ] Unit 1 implements 3 DDD contexts (routes, services, models)
- [ ] Unit 2 consumes Unit 1 via API (typed DTOs)
- [ ] Unit 3 & 4 are specialized (masters, offline)
- [ ] No business logic in Unit 2 (it's in domain services)
- [ ] Each context has clear API boundaries
- [ ] Domain events published for cross-context communication
- [ ] Offline sync respects domain invariants (cero pérdida de datos)

---

**Status**: ✅ UNITS + DDD MAPPING COMPLETADO

**Next**: CODE GENERATION Phase

