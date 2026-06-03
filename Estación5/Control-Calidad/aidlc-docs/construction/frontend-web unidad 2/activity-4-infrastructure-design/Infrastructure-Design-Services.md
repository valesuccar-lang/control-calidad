# Infrastructure Design: Services & Configuration
## Activity 4 — Frontend Web Unit

**Date**: 2026-05-31  
**Status**: ACCEPTED  
**Context**: Based on Application Design (Inception) + NFR Requirements + ADRs  
**Scope**: Service definition, configuration, and cross-cutting concerns

---

## 📋 SYSTEM SERVICES MAP

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                              │
│                      (React PWA - Node.js)                         │
├─────────────────────────────────────────────────────────────────────┤
│ Services:                                                           │
│ ├─ Inspection Service (Form capture, offline sync)                │
│ ├─ Approval Service (Review workflow)                             │
│ ├─ Master Service (CRUD Defects, Machines, Fabrics)               │
│ ├─ Auth Service (JWT token, RBAC)                                 │
│ ├─ Error Tracking Service (Custom error collection)               │
│ ├─ Performance Monitoring Service (Core Web Vitals)               │
│ ├─ Analytics Service (Event tracking)                             │
│ └─ Offline Sync Service (IndexedDB + Service Worker)              │
└────────────────┬────────────────────────────────────────────────────┘
                 │ HTTP/REST (Bearer Token)
                 │
┌─────────────────────────────────────────────────────────────────────┐
│                        BACKEND LAYER                               │
│                    (Python FastAPI - Uvicorn)                      │
├─────────────────────────────────────────────────────────────────────┤
│ API Services:                                                       │
│ ├─ Inspection Service (POST, GET, sync)                           │
│ ├─ Approval Service (POST approval decisions)                     │
│ ├─ Master Service (CRUD masters)                                  │
│ ├─ User Service (CRUD users, roles)                               │
│ ├─ Auth Service (Login, refresh, logout)                          │
│ ├─ Health Service (/health check)                                 │
│ └─ Sync Service (Merge offline changes)                           │
│                                                                    │
│ Middleware:                                                         │
│ ├─ JWT Authentication                                             │
│ ├─ RBAC (Role-Based Access Control)                               │
│ ├─ Logging (All requests/errors)                                  │
│ ├─ Error Handling (Global exception handler)                      │
│ ├─ CORS (Allow same-origin)                                       │
│ └─ Rate Limiting (Optional)                                       │
└────────────────┬────────────────────────────────────────────────────┘
                 │ SQLAlchemy ORM
                 │
    ┌────────────┴──────────┬──────────────┐
    ↓                       ↓              ↓
┌─────────────┐  ┌──────────────────┐  ┌──────────────┐
│ PostgreSQL  │  │ File Storage     │  │ Redis Cache  │
│ (Database)  │  │ (/data/photos)   │  │ (Sessions)   │
├─────────────┤  ├──────────────────┤  ├──────────────┤
│ Users       │  │ Inspection photos│  │ Auth tokens  │
│ Inspections │  │ (JPEG, 500-1500KB)│ │ Masters      │
│ Approvals   │  │ Organized by lote│  │ cache       │
│ Masters     │  │                  │  │              │
│ Lotes       │  │                  │  │              │
└─────────────┘  └──────────────────┘  └──────────────┘
```

---

## 🔐 FRONTEND SERVICES DETAIL

### 1. Inspection Service

**Purpose**: Handle inspection creation, retrieval, offline draft management

**Location**: `src/services/inspectionService.ts`

**Interface**:
```typescript
export interface InspectionService {
  // Lote Management
  searchLote(loteId: string): Promise<Lote>
  
  // Inspection CRUD
  registerInspection(data: InspectionCreate): Promise<Inspection>
  getMyInspections(): Promise<Inspection[]>
  getInspectionDetail(id: string): Promise<Inspection>
  
  // Offline/Draft Management
  saveDraftOffline(data: InspectionCreate): Promise<void>
  getDraftInspections(): Promise<InspectionDraft[]>
  deleteDraft(draftId: string): Promise<void>
  
  // Photo Management
  addPhoto(inspectionId: string, photoBlob: Blob): Promise<PhotoMetadata>
  removePhoto(inspectionId: string, photoId: string): Promise<void>
  getPhotos(inspectionId: string): Promise<Photo[]>
  
  // Sync
  syncPendingInspections(): Promise<SyncResult>
}
```

**Configuration**:
```typescript
// config/inspectionService.ts
export const inspectionConfig = {
  photoMaxSize: 5 * 1024 * 1024, // 5MB
  photoCompressionQuality: 0.8,
  maxPhotosPerInspection: 10,
  commentMinLength: 10,
  commentMaxLength: 500,
  draftRetentionDays: 30,
  syncRetryAttempts: 5,
  syncRetryDelayMs: [5000, 10000, 30000, 60000, 60000],
  offlineCacheTTL: 7 * 24 * 60 * 60 * 1000, // 7 days
}
```

**Dependencies**:
- IndexedDB (photo storage)
- Service Worker (background sync)
- Error Tracking (error reporting)
- Performance Monitor (timing)
- Offline Store (sync status)

---

### 2. Approval Service

**Purpose**: Retrieve pending approvals, submit approval decisions

**Location**: `src/services/approvalService.ts`

**Interface**:
```typescript
export interface ApprovalService {
  // Retrieval
  getPendingApprovals(limit?: number, offset?: number): Promise<Approval[]>
  getApprovalDetail(inspectionId: string): Promise<ApprovalDetail>
  getMyApprovals(): Promise<Approval[]>
  
  // Decision
  approveInspection(inspectionId: string, comment?: string): Promise<ApprovalResult>
  rejectInspection(inspectionId: string, reason: string): Promise<ApprovalResult>
  
  // Statistics (Dashboard)
  getApprovalStats(): Promise<ApprovalStats>
}
```

**Configuration**:
```typescript
export const approvalConfig = {
  pageSize: 20,
  commentMaxLength: 500,
  rejectReasonRequired: true,
  rejectReasonMinLength: 20,
  notificationOnApproval: true,
  notificationOnRejection: true,
}
```

**Dependencies**:
- API client (axios)
- Error Tracking
- Analytics (track approvals)

---

### 3. Master Service

**Purpose**: CRUD operations for Defects, Machines, Fabrics (Admin only)

**Location**: `src/services/masterService.ts`

**Interface**:
```typescript
export interface MasterService {
  // Defects
  getDefects(): Promise<Defect[]>
  createDefect(data: DefectCreate): Promise<Defect>
  updateDefect(id: string, data: DefectUpdate): Promise<Defect>
  inactivateDefect(id: string): Promise<void>
  
  // Machines
  getMachines(): Promise<Machine[]>
  createMachine(data: MachineCreate): Promise<Machine>
  updateMachine(id: string, data: MachineUpdate): Promise<Machine>
  inactivateMachine(id: string): Promise<void>
  
  // Fabrics
  getFabrics(): Promise<Fabric[]>
  createFabric(data: FabricCreate): Promise<Fabric>
  updateFabric(id: string, data: FabricUpdate): Promise<Fabric>
  inactivateFabric(id: string): Promise<void>
  
  // Cache
  refreshCache(): Promise<void>
  getCacheStatus(): Promise<CacheStatus>
}
```

**Configuration**:
```typescript
export const masterConfig = {
  cacheTTL: 60 * 60 * 1000, // 1 hour
  pageSize: 50,
  
  defect: {
    idPattern: /^DEF-[A-Z0-9]{3,}$/,
    nameMaxLength: 100,
    descriptionMaxLength: 500,
  },
  
  machine: {
    idPattern: /^MAQ-[A-Z0-9-]+$/,
    nameMaxLength: 100,
  },
  
  fabric: {
    idPattern: /^[A-Z0-9]+$/,
    nameMaxLength: 100,
  },
}
```

**Dependencies**:
- Redis cache (optional, for shared cache)
- Error Tracking
- Analytics (track master changes)

---

### 4. Auth Service

**Purpose**: Login, token refresh, logout, role verification

**Location**: `src/services/authService.ts`

**Interface**:
```typescript
export interface AuthService {
  login(email: string, password: string): Promise<AuthResponse>
  logout(): Promise<void>
  refreshToken(): Promise<string>
  getCurrentUser(): Promise<User>
  verifyRole(requiredRoles: Role[]): boolean
  hasPermission(action: string): boolean
}
```

**Configuration**:
```typescript
export const authConfig = {
  accessTokenTTL: 8 * 60 * 60, // 8 hours (seconds)
  refreshTokenTTL: 30 * 24 * 60 * 60, // 30 days (seconds)
  tokenStorageKey: 'textile-qc-token',
  httpOnly: true,
  secure: true, // HTTPS only
  sameSite: 'Strict',
  
  passwordPolicy: {
    minLength: 12,
    requireUppercase: true,
    requireLowercase: true,
    requireNumbers: true,
    requireSpecialChars: true,
  },
  
  roles: {
    ANALISTA: ['create_inspection', 'view_own_inspections'],
    JEFE_QA: ['view_all_inspections', 'approve_inspection', 'create_masters'],
    GERENTE: ['view_dashboard', 'view_analytics'],
    ADMIN: ['*'], // All permissions
  },
}
```

**Dependencies**:
- Axios interceptors
- Zustand auth store
- Error Tracking

---

### 5. Error Tracking Service

**Purpose**: Capture errors, performance issues, and send to backend

**Location**: `src/services/errorTracking.ts` (from ADR-004)

**Key Methods**:
```typescript
export interface ErrorTrackingService {
  captureError(message: string, stack?: string, severity?: Severity, metadata?: any): void
  capturePerformance(metric: string, duration: number, threshold: number): void
  flushQueue(): Promise<void>
  setUser(userId: string, email: string): void
}
```

**Configuration**:
```typescript
export const errorTrackingConfig = {
  enabled: true,
  endpoint: 'https://api.company.local/api/errors',
  batchSize: 50,
  flushIntervalMs: 30000,
  
  severityLevels: {
    ERROR: { color: 'red', slack: true },
    WARNING: { color: 'yellow', slack: false },
    INFO: { color: 'blue', slack: false },
  },
  
  performanceThresholds: {
    LCP: 2500, // ms (Largest Contentful Paint)
    FID: 100, // ms (First Input Delay)
    CLS: 0.1, // Cumulative Layout Shift
    apiCall: 5000, // ms
    photoValidation: 500, // ms
  },
}
```

**Dependencies**:
- IndexedDB (queue storage)
- Service Worker (retry on reconnect)

---

### 6. Performance Monitoring Service

**Purpose**: Track Core Web Vitals and API response times

**Location**: `src/services/performanceMonitoring.ts` (from ADR-004)

**Key Methods**:
```typescript
export interface PerformanceMonitor {
  captureMetrics(): void
  captureNetworkTiming(endpoint: string, method: string, durationMs: number): void
  reportCoreWebVitals(): void
}
```

**Configuration**:
```typescript
export const performanceConfig = {
  enabled: true,
  
  metrics: {
    trackLCP: true,
    trackFID: true,
    trackCLS: true,
    trackDOMInteractive: true,
    trackFCP: true,
  },
  
  webVitalThresholds: {
    LCP: { good: 2500, poor: 4000 },
    FID: { good: 100, poor: 300 },
    CLS: { good: 0.1, poor: 0.25 },
  },
}
```

---

### 7. Analytics Service

**Purpose**: Track user events for insights (no session replay)

**Location**: `src/services/analytics.ts` (from ADR-004)

**Key Methods**:
```typescript
export interface AnalyticsService {
  trackEvent(eventName: string, properties?: Record<string, any>): void
  trackPageView(page: string): void
  trackTiming(category: string, variable: string, time: number): void
  flush(): Promise<void>
}
```

**Tracked Events**:
```
- INSPECTION_CREATED
- INSPECTION_SUBMITTED
- INSPECTION_SYNCED
- PHOTO_UPLOADED
- PHOTO_VALIDATION_FAILED
- SYNC_COMPLETED
- SYNC_FAILED
- APPROVAL_SUBMITTED
- LOGIN
- LOGOUT
- MASTER_CREATED
- MASTER_UPDATED
```

**Configuration**:
```typescript
export const analyticsConfig = {
  enabled: true,
  endpoint: 'https://api.company.local/api/analytics',
  batchSize: 50,
  flushIntervalMs: 60000,
}
```

---

### 8. Offline Sync Service

**Purpose**: Manage sync queue and background synchronization (from ADR-003)

**Location**: `src/services/offlineSync.ts`

**Key Methods**:
```typescript
export interface OfflineSyncService {
  enqueueOperation(operation: Operation): void
  syncPendingItems(): Promise<SyncResult>
  getQueueStatus(): QueueStatus
  retryFailed(): Promise<void>
}
```

**Configuration**:
```typescript
export const offlineSyncConfig = {
  enabled: true,
  
  // IndexedDB
  dbName: 'textile-qc-db',
  tables: {
    inspections: { keyPath: 'id', indexes: ['loteId', 'status'] },
    photos: { keyPath: 'id', indexes: ['inspectionId'] },
    syncQueue: { keyPath: 'id', indexes: ['status', 'enqueuedAt'] },
    masters: { keyPath: 'id', indexes: ['type', 'status'] },
  },
  
  // Service Worker
  workerScript: '/service-worker.js',
  
  // Sync strategy
  syncOnline: true,
  syncInterval: 30000, // 30 seconds
  retryDelays: [5000, 10000, 30000, 60000, 60000], // 5 attempts
  
  // Storage
  photosMaxSizePerInspection: 5 * 1024 * 1024, // 5MB
  inspectionRetentionDays: 90,
  photoCleanupDays: 7,
}
```

---

## 🔌 BACKEND SERVICES DETAIL

### 1. Inspection Service (Backend)

**Location**: `backend/app/services/inspection_service.py`

**Responsibility**: Business logic for inspection registration, retrieval, sync

**Methods**:
```python
class InspectionService:
    async def register_inspection(
        self,
        lote_id: str,
        defect_type_id: str,
        machine_id: str,
        comment: str,
        photo_data: bytes,
        user_id: str
    ) -> Inspection:
        """Register new inspection with photo"""
        
    async def get_pending_approvals(
        self,
        limit: int = 20,
        offset: int = 0
    ) -> List[Inspection]:
        """Get inspections awaiting approval"""
        
    async def sync_offline_inspections(
        self,
        inspections: List[InspectionData],
        photos: List[PhotoData]
    ) -> SyncResult:
        """Merge offline-captured inspections"""
        
    async def get_inspection_detail(self, id: str) -> Inspection:
        """Get single inspection with full details"""
```

**Dependencies**:
- PostgreSQL ORM (SQLAlchemy)
- File storage (local filesystem `/data/photos`)
- Logging
- Error handling

---

### 2. Approval Service (Backend)

**Location**: `backend/app/services/approval_service.py`

**Responsibility**: Approval workflow (create, retrieve, statistics)

**Methods**:
```python
class ApprovalService:
    async def approve_inspection(
        self,
        inspection_id: str,
        comment: str,
        user_id: str
    ) -> Approval:
        """Approve inspection"""
        
    async def reject_inspection(
        self,
        inspection_id: str,
        reason: str,
        user_id: str
    ) -> Approval:
        """Reject inspection with reason"""
        
    async def get_approval_stats(self) -> ApprovalStats:
        """Get dashboard stats"""
```

---

### 3. Master Service (Backend)

**Location**: `backend/app/services/master_service.py`

**Responsibility**: CRUD for Defects, Machines, Fabrics

**Methods**:
```python
class MasterService:
    async def get_all_defects(self) -> List[Defect]:
    async def create_defect(self, data: DefectCreate) -> Defect:
    async def update_defect(self, id: str, data: DefectUpdate) -> Defect:
    async def inactivate_defect(self, id: str) -> None:
    
    async def get_all_machines(self) -> List[Machine]:
    async def create_machine(self, data: MachineCreate) -> Machine:
    async def update_machine(self, id: str, data: MachineUpdate) -> Machine:
    
    async def get_all_fabrics(self) -> List[Fabric]:
    async def create_fabric(self, data: FabricCreate) -> Fabric:
    async def update_fabric(self, id: str, data: FabricUpdate) -> Fabric:
```

---

### 4. Auth Service (Backend)

**Location**: `backend/app/services/auth_service.py`

**Responsibility**: JWT generation, validation, password hashing

**Methods**:
```python
class AuthService:
    async def authenticate(self, email: str, password: str) -> AuthResponse:
        """Login: validate credentials, return tokens"""
        
    async def refresh_access_token(self, refresh_token: str) -> str:
        """Refresh expired access token"""
        
    async def logout(self, user_id: str) -> None:
        """Logout: blacklist tokens"""
        
    async def verify_token(self, token: str) -> TokenPayload:
        """Verify JWT validity"""
        
    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        
    def verify_password(self, password: str, hash: str) -> bool:
        """Verify password against hash"""
```

**Configuration**:
```python
# config/auth_config.py
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8
REFRESH_TOKEN_EXPIRE_DAYS = 30
BCRYPT_ROUNDS = 12
```

---

### 5. Sync Service (Backend)

**Location**: `backend/app/services/sync_service.py`

**Responsibility**: Merge offline-captured changes with server state

**Methods**:
```python
class SyncService:
    async def sync_offline_inspections(
        self,
        offline_data: List[InspectionData],
        photos: List[PhotoData]
    ) -> SyncResult:
        """Merge offline inspections, handle conflicts"""
        
    async def get_sync_status(self, user_id: str) -> SyncStatus:
        """Get pending sync count, last sync time"""
```

**Conflict Resolution**:
- Server always wins (inspection already approved = skip)
- Deleted items handled gracefully
- Timestamps compared for ordering

---

## 📊 CROSS-CUTTING CONCERNS

### 1. Logging

**Frontend**:
```typescript
// utils/logger.ts
export const logger = {
  info: (message: string, context?: any) => console.log(`[INFO]`, message, context),
  warn: (message: string, context?: any) => console.warn(`[WARN]`, message, context),
  error: (message: string, error?: Error, context?: any) => {
    console.error(`[ERROR]`, message, error, context)
    errorTracking.captureError(message, error?.stack, 'ERROR', context)
  }
}
```

**Backend**:
```python
# app/utils/logger.py
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)
```

---

### 2. Error Handling

**Frontend**:
```typescript
// utils/errorHandler.ts
export const handleError = (error: unknown) => {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status
    const message = error.response?.data?.detail || error.message
    
    if (status === 401) {
      // Token expired → redirect to login
    } else if (status === 403) {
      // No permission → show modal
    } else if (status === 404) {
      // Not found
    } else if (status === 500) {
      // Server error → alert + Slack notification
    }
  }
  
  // Always track
  errorTracking.captureError(
    `${error}`,
    undefined,
    'ERROR',
    { url: window.location.href }
  )
}
```

**Backend**:
```python
# app/middleware/error_handler.py
from fastapi import Request
from fastapi.responses import JSONResponse

async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", extra={
        "path": request.url.path,
        "method": request.method,
        "user_id": getattr(request.user, 'id', None)
    })
    
    # Send to error tracking (Slack)
    await slack_service.send_alert(f"🚨 Backend Error: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

---

### 3. CORS & Security Headers

**Backend**:
```python
# app/middleware/cors.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://qc.factory.local"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

---

### 4. Rate Limiting

**Backend** (Optional, for API protection):
```python
# app/middleware/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Apply per route
@app.post("/api/inspections")
@limiter.limit("100/minute")
async def create_inspection(request: Request, ...):
    ...
```

---

### 5. Database Connection Pooling

**Backend**:
```python
# app/database.py
from sqlalchemy.pool import QueuePool

DATABASE_URL = "postgresql://user:pass@localhost/textile_qc"
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
)
```

---

### 6. Caching Strategy

**Frontend** (Redis - optional, mostly browser cache):
```typescript
// Cache API responses in localStorage + memory
const cache = new Map<string, CacheEntry>()

export const cachedFetch = async (key: string, fetcher: () => Promise<any>, ttl = 3600000) => {
  const cached = cache.get(key)
  if (cached && Date.now() - cached.timestamp < ttl) {
    return cached.data
  }
  
  const data = await fetcher()
  cache.set(key, { data, timestamp: Date.now() })
  return data
}
```

**Backend** (Redis for masters cache):
```python
# app/services/cache.py
from redis import Redis

redis = Redis(host="localhost", port=6379, decode_responses=True)

async def get_defects_cached():
    cached = redis.get("defects:list")
    if cached:
        return json.loads(cached)
    
    defects = await master_service.get_all_defects()
    redis.setex("defects:list", 3600, json.dumps(defects))
    return defects
```

---

## ✅ SERVICE CHECKLIST

**Frontend Services**:
- [ ] Inspection Service (create, sync, draft)
- [ ] Approval Service (list, approve, reject)
- [ ] Master Service (CRUD)
- [ ] Auth Service (login, refresh, logout)
- [ ] Error Tracking Service
- [ ] Performance Monitor Service
- [ ] Analytics Service
- [ ] Offline Sync Service

**Backend Services**:
- [ ] Inspection Service (register, sync)
- [ ] Approval Service (approve, reject, stats)
- [ ] Master Service (CRUD)
- [ ] Auth Service (JWT, password hashing)
- [ ] Sync Service (merge offline data)

**Cross-Cutting**:
- [ ] Logging (structured, JSON format)
- [ ] Error Handling (global handlers)
- [ ] Security Headers (CORS, CSP, etc.)
- [ ] Rate Limiting (optional)
- [ ] Connection Pooling (database)
- [ ] Caching Strategy (Redis, localStorage)

---

**Status**: ✅ ACCEPTED  
**Next**: Deployment Architecture (Mermaid diagrams)
