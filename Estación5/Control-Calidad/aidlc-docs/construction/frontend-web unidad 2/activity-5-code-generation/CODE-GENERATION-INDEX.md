# Activity 5: Code Generation — Complete Implementation
## Frontend Web Unit

**Date**: 2026-05-31  
**Status**: IN PROGRESS  
**Scope**: React components, Zustand stores, TypeScript services, Python FastAPI endpoints, tests

---

## 📋 GENERATION ROADMAP

### Phase 1: Core Infrastructure
- [ ] TypeScript Types & Interfaces
- [ ] Zustand Stores (5 stores)
- [ ] Axios Configuration
- [ ] Environment Setup

### Phase 2: Frontend Services
- [ ] Auth Service
- [ ] Inspection Service
- [ ] Approval Service
- [ ] Master Service
- [ ] Error Tracking Service
- [ ] Performance Monitoring Service
- [ ] Analytics Service
- [ ] Offline Sync Service

### Phase 3: Frontend Components
- [ ] Auth Pages (Login)
- [ ] Inspection Page (Analista)
- [ ] Approval Page (Jefe QA)
- [ ] Config/Masters Page (Admin)
- [ ] Dashboard Page (Basic)
- [ ] Reusable Components (Forms, Tables, Modals)
- [ ] Layout Components

### Phase 4: Backend Core
- [ ] SQLAlchemy Models (8 tables)
- [ ] Pydantic Schemas
- [ ] Database Configuration
- [ ] Middleware (Auth, RBAC, Logging)

### Phase 5: Backend Services
- [ ] Auth Service
- [ ] Inspection Service
- [ ] Approval Service
- [ ] Master Service
- [ ] Sync Service

### Phase 6: Backend API Routes
- [ ] POST /auth/login
- [ ] POST /auth/refresh
- [ ] POST /auth/logout
- [ ] POST /inspections
- [ ] GET /inspections/{id}
- [ ] GET /inspections/pending-approval
- [ ] POST /inspections/sync
- [ ] POST /approvals
- [ ] GET /approvals/stats
- [ ] CRUD /masters/defects
- [ ] CRUD /masters/machines
- [ ] CRUD /masters/fabrics
- [ ] GET /health

### Phase 7: Tests
- [ ] Frontend: Component tests (Jest)
- [ ] Frontend: Store tests
- [ ] Frontend: Service tests
- [ ] Backend: API tests (pytest)
- [ ] Backend: Service tests
- [ ] Integration tests

---

## 🗂️ FILES TO BE GENERATED

### Frontend (React + TypeScript)

#### Types & Config
```
frontend/src/
├── types/
│   ├── index.ts          # All TypeScript interfaces
│   ├── api.ts            # API response types
│   └── domain.ts         # Domain models
├── config/
│   ├── env.ts            # Environment variables
│   ├── api.config.ts     # API configuration
│   └── app.config.ts     # App settings
└── utils/
    ├── logger.ts         # Logging utility
    ├── validators.ts     # Form validators
    └── formatters.ts     # Date/string formatting
```

#### Zustand Stores
```
frontend/src/stores/
├── authStore.ts          # User, tokens, roles
├── inspectionStore.ts    # Lotes, drafts, sync
├── approvalStore.ts      # Pending approvals
├── masterStore.ts        # Defects, machines, fabrics
└── offlineStore.ts       # Sync queue, network status
```

#### Services
```
frontend/src/services/
├── api.ts                # Axios instance + interceptors
├── authService.ts        # Login, refresh, logout
├── inspectionService.ts  # Register, sync, drafts
├── approvalService.ts    # Get pending, approve, reject
├── masterService.ts      # CRUD masters
├── errorTracking.ts      # Error collection + Slack alerts
├── performanceMonitoring.ts # Core Web Vitals
├── analytics.ts          # Event tracking
└── offlineSync.ts        # IndexedDB + Service Worker
```

#### Pages
```
frontend/src/pages/
├── Login/
│   ├── LoginPage.tsx     # Email/password form
│   └── LoginForm.tsx     # Reusable form
├── Inspection/
│   ├── InspectionPage.tsx    # Main page (Analista)
│   ├── LoteSearch.tsx        # Search bar
│   ├── CameraCapture.tsx     # Photo upload
│   ├── DefectForm.tsx        # Defect selection + comment
│   └── InspectionHistory.tsx # My inspections table
├── Approval/
│   ├── ApprovalPage.tsx      # Main page (Jefe QA)
│   ├── PendingLotsTable.tsx  # Pending inspections
│   ├── InspectionModal.tsx   # Detail + decision
│   └── ApprovalHistory.tsx   # Past approvals
├── Config/
│   ├── ConfigPage.tsx        # Admin page
│   ├── DefectsTab.tsx        # CRUD defects
│   ├── MachinesTab.tsx       # CRUD machines
│   ├── FabricsTab.tsx        # CRUD fabrics
│   ├── UsersTab.tsx          # CRUD users (future)
│   └── MasterForm.tsx        # Generic CRUD form
└── Dashboard/
    ├── DashboardPage.tsx     # KPIs
    ├── KPICards.tsx          # Stats cards
    └── RecentInspections.tsx # Last 10
```

#### Components
```
frontend/src/components/
├── Auth/
│   ├── PrivateRoute.tsx      # Route guard
│   └── RoleGuard.tsx         # Role-based render
├── Forms/
│   ├── FormInput.tsx         # Reusable input
│   ├── FormSelect.tsx        # Reusable select
│   ├── FormTextarea.tsx      # Reusable textarea
│   └── FormSubmit.tsx        # Reusable submit button
├── Tables/
│   ├── DataTable.tsx         # Generic table
│   ├── PaginationControls.tsx # Pagination
│   └── TableSearch.tsx       # Search/filter
├── Modals/
│   ├── ConfirmationModal.tsx # Yes/no dialog
│   ├── ErrorModal.tsx        # Error display
│   └── LoadingModal.tsx      # Loading spinner
├── Layout/
│   ├── Navbar.tsx            # Top navigation
│   ├── Sidebar.tsx           # Left sidebar
│   ├── Layout.tsx            # Main layout
│   └── SyncIndicator.tsx     # Offline/sync status
└── Common/
    ├── Button.tsx            # Reusable button
    ├── Card.tsx              # Reusable card
    ├── Badge.tsx             # Status badge
    └── Toast.tsx             # Notifications
```

#### Hooks
```
frontend/src/hooks/
├── useAuth.ts               # Auth state + methods
├── useInspection.ts         # Inspection state + methods
├── useApproval.ts           # Approval state + methods
├── useMaster.ts             # Masters cache
├── useOfflineSync.ts        # Sync status
├── useFetch.ts              # Data fetching
└── useForm.ts               # Form management
```

#### Tests
```
frontend/tests/
├── stores/
│   ├── authStore.test.ts
│   ├── inspectionStore.test.ts
│   └── offlineStore.test.ts
├── services/
│   ├── authService.test.ts
│   ├── inspectionService.test.ts
│   └── errorTracking.test.ts
└── components/
    ├── LoginPage.test.tsx
    ├── InspectionPage.test.tsx
    └── ApprovalPage.test.tsx
```

---

### Backend (Python FastAPI)

#### Models (SQLAlchemy)
```
backend/app/models/
├── __init__.py
├── base.py               # Base model class
├── user.py               # User model
├── lote.py               # Lote (HDR) model
├── inspection.py         # Inspection model
├── approval.py           # Approval model
├── defect.py             # Defect type master
├── machine.py            # Machine master
└── fabric.py             # Fabric master
```

#### Schemas (Pydantic)
```
backend/app/schemas/
├── __init__.py
├── user.py               # UserCreate, UserResponse
├── auth.py               # LoginRequest, AuthResponse
├── lote.py               # LoteResponse
├── inspection.py         # InspectionCreate, InspectionResponse, SyncRequest
├── approval.py           # ApprovalCreate, ApprovalResponse
├── master.py             # DefectCreate, MachineCreate, FabricCreate, etc.
└── common.py             # Pagination, Error responses
```

#### Services (Business Logic)
```
backend/app/services/
├── __init__.py
├── auth_service.py       # JWT, password hashing, validation
├── inspection_service.py # Register, retrieve, sync
├── approval_service.py   # Approve, reject, stats
├── master_service.py     # CRUD, cache
├── sync_service.py       # Merge offline data
└── email_service.py      # Email notifications (optional)
```

#### Routes (Endpoints)
```
backend/app/routes/
├── __init__.py
├── auth.py               # /auth/* endpoints
├── inspections.py        # /inspections/* endpoints
├── approvals.py          # /approvals/* endpoints
├── masters.py            # /masters/* endpoints
├── health.py             # /health endpoint
└── errors.py             # /api/errors endpoint (error logging)
```

#### Middleware
```
backend/app/middleware/
├── __init__.py
├── auth.py               # JWT verification
├── rbac.py               # Role-based access control
├── logging.py            # Request/response logging
└── error_handler.py      # Global exception handling
```

#### Utils & Config
```
backend/app/
├── main.py               # FastAPI app initialization
├── config.py             # Environment config
├── database.py           # SQLAlchemy setup
├── dependencies.py       # FastAPI Depends()
└── utils/
    ├── __init__.py
    ├── validators.py     # Input validation
    ├── exceptions.py     # Custom exceptions
    ├── logger.py         # Logging setup
    └── jwt_utils.py      # JWT helpers
```

#### Tests
```
backend/tests/
├── __init__.py
├── conftest.py           # Pytest fixtures
├── test_auth.py          # Auth endpoints
├── test_inspections.py   # Inspection endpoints
├── test_approvals.py     # Approval endpoints
├── test_masters.py       # Master endpoints
└── services/
    ├── test_auth_service.py
    ├── test_inspection_service.py
    └── test_sync_service.py
```

---

## 📊 GENERATION STRATEGY

**File Order** (Dependencies first):

1. **Types & Config** (no dependencies)
2. **Backend Models** (depend on config)
3. **Backend Schemas** (depend on models)
4. **Backend Middleware** (depend on config)
5. **Backend Services** (depend on models, schemas)
6. **Backend Routes** (depend on services, middleware)
7. **Frontend Types** (depend on backend schemas)
8. **Frontend Services** (depend on types)
9. **Frontend Stores** (depend on services, types)
10. **Frontend Components** (depend on stores, services)
11. **Tests** (depend on all)

---

## ✅ GENERATION CHECKLIST

**Core Files** (Must-have):
- [ ] TypeScript types
- [ ] Auth service + store
- [ ] Inspection service + store
- [ ] Approval service + store
- [ ] Master service + store
- [ ] Offline sync service + store
- [ ] SQLAlchemy models
- [ ] FastAPI routes
- [ ] Jest + pytest tests

**UI Components** (MVP):
- [ ] Login page
- [ ] Inspection page
- [ ] Approval page
- [ ] Config page
- [ ] Dashboard page
- [ ] Reusable components

**Integration**:
- [ ] Service Worker implementation
- [ ] IndexedDB setup
- [ ] Error tracking integration
- [ ] Performance monitoring integration

---

## 🚀 EXECUTION PLAN

**This session**: Generate core infrastructure + critical components
- TypeScript types
- Zustand stores (all 5)
- Frontend services (critical ones)
- Backend models + schemas
- Backend routes (auth, inspections)
- Main pages (Login, Inspection, Approval)

**Next session**: Generate remaining + tests
- Backend services (full)
- Remaining components
- Tests (frontend + backend)
- Integration setup

---

**Status**: 🚀 READY TO START  
**Priority**: Auth → Inspection → Approval → Masters  
**Focus**: Correctness > Completeness (generate robust code for critical paths)

