# Application Design — Control de Calidad Textil
**Date**: 2026-05-26 | **Personas**: 4 (Analista, Jefe QA, Gerente, Admin) | **Tech Stack**: Python FastAPI + React + PostgreSQL | **Status**: INCEPTION PHASE

---

## 🏗️ VISIÓN GENERAL DE ARQUITECTURA

```
┌─────────────────────────────────────────────────────────┐
│              FRONTEND LAYER (React PWA)                │
├─────────────────────────────────────────────────────────┤
│ • Pages: Inspección, Aprobación, Análisis (básico), Config
│ • Components: Form, Table, Modal, Chart, AuthGuard
│ • State: Zustand (simple, escalable)
│ • Offline: Service Worker + IndexedDB (fotos)
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/REST
        ┌────────────┴────────────┐
        ↓                         ↓
   ┌─────────────────────────────────────────────────────────┐
   │        BACKEND LAYER (Python FastAPI)                  │
   ├─────────────────────────────────────────────────────────┤
   │ • API Routes: /inspections, /approvals, /masters, /config
   │ • Services: InspectionService, ApprovalService, etc.
   │ • Auth: JWT + RBAC
   │ • Middleware: Logging, Error handling, CORS
   └────────────────────┬────────────────────────────────────┘
                        │ SQLAlchemy ORM
        ┌───────────────┴────────────────┐
        ↓                                ↓
   ┌──────────────────┐         ┌─────────────────────┐
   │  POSTGRESQL DB   │         │  File Storage       │
   │  (Relational)    │         │  (Fotos locales)    │
   ├──────────────────┤         ├─────────────────────┤
   │ • Inspecciones   │         │ • Defect photos     │
   │ • Aprobaciones   │         │ (Stored locally)    │
   │ • Maestros       │         │                     │
   │ • Usuarios       │         │                     │
   └──────────────────┘         └─────────────────────┘
```

---

## 📦 FRONTEND ARCHITECTURE (React + TypeScript)

### Directory Structure

```
src/
├── pages/
│   ├── Inspection/          # Analista: capturar defectos
│   ├── Approval/            # Jefe QA: aprobar lotes
│   ├── Config/              # Admin: maestros + settings
│   └── Dashboard/           # Básico (sin análisis avanzado en MVP)
├── components/
│   ├── Forms/
│   │   ├── LoteSearchForm
│   │   ├── DefectForm
│   │   ├── ApprovalForm
│   │   └── MasterCRUDForm
│   ├── Tables/
│   │   ├── PendingLotsTable
│   │   ├── InspectionHistoryTable
│   │   └── MastersTable
│   ├── Modals/
│   │   ├── PhotoModal
│   │   ├── ConfirmationModal
│   │   └── ErrorModal
│   ├── Auth/
│   │   ├── LoginForm
│   │   ├── PrivateRoute
│   │   └── RoleGuard
│   └── Layout/
│       ├── Navbar
│       ├── Sidebar
│       └── Footer
├── services/
│   ├── api.ts              # Axios instance + interceptors
│   ├── inspectionService.ts
│   ├── approvalService.ts
│   ├── masterService.ts
│   └── authService.ts
├── store/
│   ├── authStore.ts        # Zustand: user, roles, token
│   ├── inspectionStore.ts  # Zustand: lotes, defectos
│   ├── approvalStore.ts    # Zustand: pending approvals
│   └── offlineStore.ts     # Zustand: offline queue
├── utils/
│   ├── validation.ts
│   ├── formatters.ts
│   ├── offlineSync.ts      # Service Worker comunicación
│   └── errorHandling.ts
├── types/
│   ├── index.ts            # TypeScript interfaces
│   └── api.ts              # API response types
├── hooks/
│   ├── useAuth.ts
│   ├── useInspection.ts
│   ├── useOfflineSync.ts
│   └── useFetch.ts
└── App.tsx
```

### Page Components (4 páginas MVP)

#### Page 1: Inspection (Analista)

**Purpose**: Capturar defecto (foto + tipo + comentario)

**Components**:
- `InspectionPage.tsx`: Container
  - `LoteSearchBar`: Escanear/buscar código HDR
  - `CameraCapture`: Capturar foto
  - `DefectTypeSelector`: Dropdown 25+ defectos
  - `CommentInput`: Campo comentario (≥10 chars)
  - `MachineSelector`: Máquina culpable (pre-filled, editable)
  - `OfflineIndicator`: Muestra 📡 ONLINE/OFFLINE
  - `InspectionHistory`: Tabla mis últimos registros

**State** (Zustand):
```typescript
inspectionStore {
  currentLote: Lote | null
  currentDefect: DefectInput
  isOnline: boolean
  pendingRegistrations: DefectInput[]
}
```

**Data Flow**:
1. Analista busca lote
2. Sistema carga lote de API (o caché offline)
3. Analista captura foto → guardada en IndexedDB
4. Selecciona tipo defecto → máquina se pre-rellena
5. Escribe comentario
6. Presiona "Guardar" → guardado localmente + cola offline
7. Cuando hay wifi → sincroniza automáticamente

---

#### Page 2: Approval (Jefe QA)

**Purpose**: Revisar y aprobar/rechazar defectos

**Components**:
- `ApprovalPage.tsx`: Container
  - `PendingLotsTable`: Lista lotes pendientes
  - `LoteDetailModal`: Foto grande + detalles
  - `ApprovalDecision`: Botones Aprobar/Rechazar
  - `ApprovalHistory`: Mis aprobaciones pasadas

**State** (Zustand):
```typescript
approvalStore {
  pendingApprovals: Approval[]
  selectedApproval: Approval | null
  approvalHistory: Approval[]
}
```

**Data Flow**:
1. Jefe ve tabla pendiente (API query)
2. Selecciona lote → muestra foto + detalles modal
3. Presiona Aprobar/Rechazar
4. Sistema envía a API
5. Registro actualizado en BD

---

#### Page 3: Config (Admin)

**Purpose**: CRUD maestros + settings

**Components**:
- `ConfigPage.tsx`: Container
  - `MastersTab`: Telas, Máquinas, Defectos
  - `UsersTab`: CRUD usuarios + roles
  - `SettingsTab`: Empresa, integración ACATEX (future)
  - `MasterCRUDForm`: Formulario dinámico (create/edit/inactivate)
  - `MastersTable`: Tabla datos

**State** (Zustand):
```typescript
configStore {
  masters: {
    defects: Defect[]
    machines: Machine[]
    fabrics: Fabric[]
  }
  users: User[]
  settings: Settings
}
```

**Data Flow**:
1. Admin ve tabla maestro (ej: defectos)
2. Presiona "Crear" → abre formulario
3. Completa campos → presiona guardar
4. API POST /api/masters/defects
5. Actualiza tabla

---

#### Page 4: Dashboard (Admin/Jefe QA) — Básico MVP

**Purpose**: Números principales (sin gráficos avanzados en v1)

**Components**:
- `DashboardPage.tsx`: Container
  - `KPICards`: Total reprocesos hoy
  - `RecentInspections`: Últimas 10 inspecciones
  - `ApprovalStatus`: # pendientes vs. aprobados

**Note**: Análisis avanzado (gráficos) es v1.1

---

### State Management (Zustand)

**Why Zustand?** Simple, TypeScript-friendly, menos boilerplate que Redux

```typescript
// stores/authStore.ts
export const useAuthStore = create((set) => ({
  user: null,
  token: null,
  roles: [],
  login: async (email, password) => { /* API call */ },
  logout: () => { /* clear state */ },
}))

// stores/inspectionStore.ts
export const useInspectionStore = create((set) => ({
  currentLote: null,
  currentDefect: {},
  pendingRegistrations: [],
  addPendingRegistration: (reg) => { /* add to queue */ },
  syncOfflineData: async () => { /* sync all pending */ },
}))

// stores/offlineStore.ts
export const useOfflineStore = create((set) => ({
  isOnline: navigator.onLine,
  syncQueue: [],
  // Service Worker integration
}))
```

---

### Offline-First Implementation

**Service Worker**:
```typescript
// public/sw.js
self.addEventListener('install', (event) => {
  // Cache static assets
})

self.addEventListener('fetch', (event) => {
  if (event.request.method === 'GET') {
    // Cache first for assets, network first for APIs
  } else {
    // POST/PUT: queue for sync, return optimistic response
  }
})

self.addEventListener('sync', (event) => {
  // Background sync: retry failed requests when online
})
```

**IndexedDB** (Foto storage):
```typescript
// utils/indexedDB.ts
export async function saveDefectPhoto(loteId: string, photoBlob: Blob) {
  const db = await openDB()
  const tx = db.transaction('photos', 'readwrite')
  await tx.objectStore('photos').add({
    loteId,
    photo: photoBlob,
    timestamp: Date.now(),
    synced: false
  })
}
```

---

## 🖥️ BACKEND ARCHITECTURE (Python FastAPI)

### Directory Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app entry
│   ├── config.py                # Config (DB, secrets, etc.)
│   ├── database.py              # SQLAlchemy setup
│   ├── models/                  # ORM models
│   │   ├── __init__.py
│   │   ├── lote.py              # Lote (HDR) model
│   │   ├── inspection.py        # Inspection model
│   │   ├── defect.py            # Defect type (master)
│   │   ├── approval.py          # Approval model
│   │   ├── user.py              # User model
│   │   ├── machine.py           # Machine model (master)
│   │   └── fabric.py            # Fabric model (master)
│   ├── schemas/                 # Pydantic request/response
│   │   ├── inspection.py        # InspectionCreate, InspectionResponse
│   │   ├── approval.py          # ApprovalCreate, ApprovalResponse
│   │   ├── master.py            # DefectCreate, MachineCreate, etc.
│   │   └── user.py              # UserCreate, UserResponse
│   ├── routes/                  # API endpoints
│   │   ├── __init__.py
│   │   ├── inspections.py       # POST /inspections, GET, etc.
│   │   ├── approvals.py         # POST /approvals, GET, etc.
│   │   ├── masters.py           # CRUD /masters/defects, /machines, /fabrics
│   │   ├── users.py             # CRUD /users, /roles
│   │   ├── auth.py              # POST /auth/login, /auth/logout
│   │   └── health.py            # GET /health (ping)
│   ├── services/                # Business logic
│   │   ├── inspection_service.py
│   │   ├── approval_service.py
│   │   ├── master_service.py
│   │   └── sync_service.py      # Offline sync logic
│   ├── middleware/
│   │   ├── auth.py              # JWT verification
│   │   ├── rbac.py              # Role-based access control
│   │   └── error_handler.py     # Global error handling
│   ├── utils/
│   │   ├── validators.py
│   │   ├── logger.py
│   │   └── exceptions.py
│   └── dependencies.py          # FastAPI Depends()
├── tests/
│   ├── test_inspections.py
│   ├── test_approvals.py
│   └── test_masters.py
├── requirements.txt
└── .env.example
```

### Core Models (SQLAlchemy ORM)

```python
# models/lote.py
from sqlalchemy import Column, String, DateTime, Enum
from datetime import datetime

class Lote(Base):
    __tablename__ = "lotes"
    
    id = Column(String, primary_key=True)  # HDR-12847
    fabric_id = Column(String, ForeignKey("fabrics.id"))
    quantity_meters = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(LoteStatus), default=LoteStatus.PENDING)
    
    # Relations
    inspections = relationship("Inspection", back_populates="lote")

# models/inspection.py
class Inspection(Base):
    __tablename__ = "inspections"
    
    id = Column(String, primary_key=True, default=uuid4)
    lote_id = Column(String, ForeignKey("lotes.id"))
    analista_id = Column(String, ForeignKey("users.id"))
    defect_type_id = Column(String, ForeignKey("defects.id"))
    machine_culpable_id = Column(String, ForeignKey("machines.id"))
    comment = Column(String, nullable=False)
    photo_path = Column(String)  # Path en filesystem o URL
    check_in = Column(DateTime, default=datetime.utcnow)
    check_out = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    synced = Column(Boolean, default=False)  # Offline flag
    
    # Relations
    lote = relationship("Lote", back_populates="inspections")
    analista = relationship("User")
    defect_type = relationship("Defect")
    machine = relationship("Machine")

# models/approval.py
class Approval(Base):
    __tablename__ = "approvals"
    
    id = Column(String, primary_key=True, default=uuid4)
    inspection_id = Column(String, ForeignKey("inspections.id"))
    jefe_qa_id = Column(String, ForeignKey("users.id"))
    status = Column(Enum(ApprovalStatus))  # APPROVED, REJECTED
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    inspection = relationship("Inspection")
    jefe_qa = relationship("User")

# models/defect.py
class Defect(Base):
    __tablename__ = "defects"
    
    id = Column(String, primary_key=True)  # DEF-TON
    name = Column(String, unique=True)  # TONODIFFERENTE
    description = Column(String)
    typical_process = Column(String)  # TINTORERIA
    typical_machine_id = Column(String, ForeignKey("machines.id"), nullable=True)

# models/user.py
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(Enum(Role))  # ANALISTA, JEFE_QA, GERENTE, ADMIN
    created_at = Column(DateTime, default=datetime.utcnow)
```

### API Routes & Contracts

#### Route 1: POST /inspections (Crear inspección)

**Request**:
```json
{
  "lote_id": "HDR-12847",
  "defect_type_id": "DEF-TON",
  "machine_culpable_id": "MAQ-AGO-80",
  "comment": "Variación de tono entre 200-250m...",
  "photo_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

**Response (201)**:
```json
{
  "id": "insp-001",
  "lote_id": "HDR-12847",
  "status": "REGISTERED",
  "check_in": "2026-05-26T14:32:15Z",
  "synced": true
}
```

---

#### Route 2: GET /inspections/pending-approval (Listar lotes pendientes)

**Query Params**: `?limit=20&offset=0`

**Response (200)**:
```json
[
  {
    "id": "insp-001",
    "lote_id": "HDR-12847",
    "fabric_name": "NOVAKREPEL",
    "analista_name": "María López",
    "defect_type": "TONODIFFERENTE",
    "comment": "Variación de tono...",
    "photo_url": "/photos/insp-001.jpg",
    "created_at": "2026-05-26T14:35:37Z"
  }
]
```

---

#### Route 3: POST /approvals (Aprobar/rechazar)

**Request**:
```json
{
  "inspection_id": "insp-001",
  "status": "APPROVED",
  "comment": "Acción correctiva: revisar máquina"
}
```

**Response (201)**:
```json
{
  "id": "appr-001",
  "inspection_id": "insp-001",
  "status": "APPROVED",
  "created_at": "2026-05-26T14:40:00Z"
}
```

---

#### Route 4: CRUD /masters/defects (Maestro defectos)

**GET** `/masters/defects` → Lista todos
```json
[
  {
    "id": "DEF-TON",
    "name": "TONODIFFERENTE",
    "description": "Variación de tono en tela",
    "typical_process": "TINTORERIA",
    "typical_machine": "AGOTAMIENTO 80"
  }
]
```

**POST** `/masters/defects` → Crear
```json
{
  "id": "DEF-NEW",
  "name": "DEFECTO NUEVO",
  "description": "..."
}
```

**PUT** `/masters/defects/{id}` → Editar  
**DELETE** `/masters/defects/{id}` → Inactivar

---

#### Route 5: Auth Routes

**POST** `/auth/login` → Login
```json
{
  "email": "analista@eliot.com",
  "password": "***"
}
→ Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "...",
  "user": {
    "id": "user-001",
    "email": "analista@eliot.com",
    "role": "ANALISTA"
  }
}
```

**POST** `/auth/logout` → Logout
```json
{
  "message": "Logged out successfully"
}
```

---

### Middleware & Authentication

```python
# middleware/auth.py
from fastapi import HTTPException, Depends
from jose import JWTError, jwt

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return User.get_by_id(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate token")

# middleware/rbac.py
def require_role(*roles: Role):
    def decorator(func):
        async def wrapper(current_user: User = Depends(get_current_user)):
            if current_user.role not in roles:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return await func(current_user=current_user)
        return wrapper
    return decorator

# Usage:
@app.post("/approvals")
@require_role(Role.JEFE_QA)
async def create_approval(data: ApprovalCreate, current_user: User = Depends()):
    ...
```

---

## 💾 DATABASE SCHEMA (PostgreSQL)

```sql
-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  full_name VARCHAR(255),
  role VARCHAR(50),  -- ANALISTA, JEFE_QA, GERENTE, ADMIN
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Defects master (local)
CREATE TABLE defects (
  id VARCHAR(50) PRIMARY KEY,  -- DEF-TON
  name VARCHAR(255) UNIQUE NOT NULL,
  description TEXT,
  typical_process VARCHAR(100),
  typical_machine_id VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Machines master (optional ACATEX sync)
CREATE TABLE machines (
  id VARCHAR(50) PRIMARY KEY,  -- MAQ-AGO-80
  name VARCHAR(255) UNIQUE NOT NULL,
  process VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Fabrics master (optional ACATEX sync)
CREATE TABLE fabrics (
  id VARCHAR(50) PRIMARY KEY,  -- NOVAKREPEL
  name VARCHAR(255) UNIQUE NOT NULL,
  composition VARCHAR(255),
  width_cm DECIMAL(5,2),
  weight_gsm DECIMAL(5,2),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Lotes (HDR)
CREATE TABLE lotes (
  id VARCHAR(50) PRIMARY KEY,  -- HDR-12847
  fabric_id VARCHAR(50) NOT NULL REFERENCES fabrics(id),
  quantity_meters DECIMAL(10,2),
  status VARCHAR(50),  -- PENDING, IN_PROCESS, REPROCESSED, APPROVED
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Inspections
CREATE TABLE inspections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lote_id VARCHAR(50) NOT NULL REFERENCES lotes(id),
  analista_id UUID NOT NULL REFERENCES users(id),
  defect_type_id VARCHAR(50) NOT NULL REFERENCES defects(id),
  machine_culpable_id VARCHAR(50) REFERENCES machines(id),
  comment TEXT NOT NULL,
  photo_path VARCHAR(500),
  check_in TIMESTAMP DEFAULT NOW(),
  check_out TIMESTAMP,
  synced BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Approvals
CREATE TABLE approvals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  inspection_id UUID NOT NULL REFERENCES inspections(id),
  jefe_qa_id UUID NOT NULL REFERENCES users(id),
  status VARCHAR(50),  -- APPROVED, REJECTED
  comment TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes para performance
CREATE INDEX idx_inspections_lote_id ON inspections(lote_id);
CREATE INDEX idx_inspections_analista_id ON inspections(analista_id);
CREATE INDEX idx_inspections_synced ON inspections(synced) WHERE synced = FALSE;
CREATE INDEX idx_approvals_inspection_id ON approvals(inspection_id);
```

---

## 🔄 DATA FLOW & DEPENDENCIES

### Flow 1: Inspection Registration (Happy Path)

```
Analista abre app
  ↓
[Offline] Busca lote HDR-12847
  ↓ (cacheado o API call)
Sistema carga: fabric=NOVAKREPEL, típicas máquinas tintorería
  ↓
[Offline] Captura foto → guardada IndexedDB
  ↓
[Offline] Selecciona defect=TONODIFFERENTE → máquina=AGOTAMIENTO 80 (pre-filled)
  ↓
[Offline] Escribe comentario
  ↓
[Offline] Presiona "Guardar"
  ↓
Sistema guarda en IndexedDB + agrega a syncQueue
  ↓
[Online?]
  Sí → sincroniza: POST /api/inspections con blob foto
       BD actualizada, inspection.synced=true
  No  → muestra "Guardado. Sincronizará cuando haya wifi"
```

---

### Flow 2: Approval (Happy Path)

```
Jefe QA abre app
  ↓
GET /api/inspections/pending-approval
  ↓
Tabla muestra 10 lotes pendientes
  ↓
Selecciona uno → modal muestra foto + detalles
  ↓
Presiona "Aprobar"
  ↓
POST /api/approvals { inspection_id, status=APPROVED }
  ↓
BD actualizado: approval creado, inspection.status=APPROVED
```

---

## 📋 COMPONENTES Y SERVICIOS

### Frontend Services (TypeScript)

```typescript
// services/inspectionService.ts
export const inspectionService = {
  async searchLote(loteId: string): Promise<Lote> {
    // GET /lotes/{loteId}
  },
  
  async registerInspection(data: InspectionCreate): Promise<Inspection> {
    // POST /inspections (con foto FormData)
  },
  
  async getMyInspections(): Promise<Inspection[]> {
    // GET /inspections/me
  },
  
  async saveDraftOffline(data: InspectionCreate): Promise<void> {
    // Guardar en IndexedDB
  },
  
  async syncPendingInspections(): Promise<void> {
    // Enviar cola offline a server
  }
}

// services/approvalService.ts
export const approvalService = {
  async getPendingApprovals(): Promise<Approval[]> {
    // GET /inspections/pending-approval
  },
  
  async approveInspection(inspectionId: string, comment?: string): Promise<void> {
    // POST /approvals
  },
  
  async rejectInspection(inspectionId: string, comment?: string): Promise<void> {
    // POST /approvals
  }
}

// services/masterService.ts
export const masterService = {
  async getDefects(): Promise<Defect[]> {
    // GET /masters/defects
  },
  
  async createDefect(data: DefectCreate): Promise<Defect> {
    // POST /masters/defects
  },
  
  async updateDefect(id: string, data: DefectUpdate): Promise<Defect> {
    // PUT /masters/defects/{id}
  },
  
  async inactivateDefect(id: string): Promise<void> {
    // DELETE /masters/defects/{id}
  }
}
```

---

## ✅ COMPONENTES CRÍTICOS A VALIDAR

### Critical Component 1: Offline-First Sync

**Responsabilidad**: Garantizar cero pérdida de fotos/datos

**Implementation**:
- Service Worker + IndexedDB
- Retry logic con exponential backoff
- Conflict resolution (server wins)

**Test cases**:
- Capturar foto sin wifi → guardar en IndexedDB
- Wifi vuelve 5 min después → sincronizar automáticamente
- Foto grande (10MB) → compresión antes guardar
- Sincronización falla → reintentar con backoff

---

### Critical Component 2: Photo Storage

**Responsabilidad**: Almacenar y recuperar fotos

**Options**:
- IndexedDB en frontend (ideal para MVP on-premise)
- Filesystem local backend (después)

**MVP**: IndexedDB + compresión JPEG 80%

---

### Critical Component 3: Role-Based Access Control (RBAC)

**Responsabilidad**: Autorizar por rol

**Roles**:
- `ANALISTA`: Solo crear inspecciones, ver mis históricos
- `JEFE_QA`: Ver + aprobar/rechazar, crear maestros
- `GERENTE`: Ver dashboards (v1.1)
- `ADMIN`: Todo

**Enforcement**: Middleware JWT + @require_role en cada route

---

## 🎯 ARCHITECTURE SUMMARY

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Frontend** | React 18 + TypeScript + Zustand | Moderno, escalable, TypeScript type safety |
| **Backend** | Python FastAPI | Rápido desarrollo, async, buena documentación |
| **Database** | PostgreSQL | Relacional, full-text search, JSON support |
| **Photo Storage** | IndexedDB (frontend) | Offline-first, no servidor necesario para MVP |
| **Auth** | JWT + RBAC | Stateless, seguro, escalable |
| **Offline** | Service Worker + IndexedDB | Estándar PWA, funciona offline |
| **State Mgmt** | Zustand | Ligero, TypeScript, fácil testing |
| **API Style** | RESTful + JSON | Estándar, Swagger auto-docs en FastAPI |

---

## ✅ APPROVAL CHECKLIST

- [ ] Componentes React (4 pages + 15 components) ✅ Listados
- [ ] Servicios backend (3 servicios principales) ✅ Definidos
- [ ] DB schema (8 tables + indexes) ✅ Normalizado
- [ ] API routes (10+ endpoints) ✅ Especificados
- [ ] Offline-first architecture ✅ Diseñado
- [ ] RBAC + Auth ✅ Definido

---

**Status**: ✅ READY FOR APPROVAL

**Next Step**: CODE GENERATION (Backend + Frontend)

