# Domain Entities — Frontend Web (React + TypeScript)

**Date**: 2026-05-31  
**Unit**: Frontend Web (React + TypeScript)  
**Tech Stack**: React 18 + TypeScript + Zustand + Service Worker + IndexedDB  
**Status**: 🟢 DESIGN PHASE

---

## 🏛️ BOUNDED CONTEXTS

The Frontend Web unit is organized into 5 bounded contexts, each with independent responsibility:

### **1. Inspection Context**
**Responsibility**: Capture defect inspections (Analista workflow)
- Lote search and retrieval
- Photo capture and validation
- Defect type selection
- Comment input and validation
- Machine identification
- Local storage and sync queue

### **2. Approval Context**
**Responsibility**: Review and approve/reject inspections (Jefe QA workflow)
- Pending approvals list
- Inspection detail view (photo + metadata)
- Approval/rejection decision
- Rejection reason input
- Approval history

### **3. Masters Context**
**Responsibility**: Manage master data (Admin workflow)
- Defect types CRUD
- Machine CRUD
- Fabric types CRUD
- CSV import/export
- Data validation and deduplication

### **4. Auth Context**
**Responsibility**: User authentication and authorization
- Login/logout
- Token management (access + refresh)
- Role-based access control (ANALISTA, JEFE_QA, ADMIN, GERENTE)
- Session state

### **5. Offline Context**
**Responsibility**: Offline-first synchronization
- IndexedDB persistence
- Sync queue management
- Exponential backoff retry logic
- Network state detection
- Conflict resolution

---

## 📦 AGGREGATES (Zustand Stores)

Each aggregate is implemented as a Zustand store with immutable state updates.

### **Aggregate 1: InspectionAggregate**
**Root Entity**: `CurrentInspection`

```typescript
// Domain Model
type InspectionAggregate = {
  // Root entity
  inspection: {
    id: UUID
    loteId: string
    analista_id: string
    photo: Photo                    // Value Object
    defect: DefectSelection         // Value Object
    comment: Comment                // Value Object
    machine: MachineIdentification  // Value Object
    inspectionTime: InspectionTime  // Value Object
    syncStatus: SyncStatus          // Value Object
    createdAt: datetime
  }

  // Context state
  currentLote: Lote | null
  isCapturingPhoto: boolean
  validationErrors: ValidationError[]
  
  // Methods (business logic)
  selectLote(loteId: string): Promise<void>
  capturePhoto(file: File): Promise<Photo>
  selectDefect(defectId: string): void
  updateComment(text: string): void
  autoSelectMachine(defectId: string): void
  saveInspection(): Promise<UUID>
  markSyncPending(): void
  markSyncSuccessful(): void
  markSyncFailed(error: string): void
}

// Zustand Store
const useInspectionStore = create<InspectionAggregate>((set, get) => ({
  inspection: null,
  currentLote: null,
  isCapturingPhoto: false,
  validationErrors: [],
  
  selectLote: async (loteId) => { /* ... */ },
  capturePhoto: async (file) => { /* ... */ },
  selectDefect: (defectId) => { /* ... */ },
  updateComment: (text) => { /* ... */ },
  autoSelectMachine: (defectId) => { /* ... */ },
  saveInspection: async () => { /* ... */ },
  // ... other methods
}))
```

**Invariants** (Business Rules):
- BR-001: Inspection must have all mandatory fields (lote, defect, comment, photo, machine)
- BR-002: Comment must be 10-500 characters (validated in value object)
- BR-004: Photo max 500KB (validated in value object)
- BR-003: Photo must pass quality validation (Laplacian blur, brightness, contrast)
- BR-013: Sync idempotency (inspection_id prevents duplicates)

---

### **Aggregate 2: ApprovalAggregate**
**Root Entity**: `PendingApproval`

```typescript
type ApprovalAggregate = {
  // Root entity
  approval: {
    id: UUID
    inspectionId: UUID
    inspection: InspectionDetails   // Nested aggregate reference
    jefe_qa_id: string
    decision: ApprovalDecision      // Value Object: APPROVED | REJECTED
    rejectionReason?: RejectionReason // Value Object (if rejected)
    notes?: string
    approvedAt: datetime
  }

  // Context state
  pendingApprovals: PendingApproval[]
  selectedApproval: PendingApproval | null
  approvalHistory: ApprovalRecord[]
  isSubmittingApproval: boolean
  validationErrors: ValidationError[]

  // Methods
  loadPendingApprovals(): Promise<void>
  selectApproval(approvalId: UUID): void
  approveInspection(notes?: string): Promise<void>
  rejectInspection(rejectionReason: string, notes?: string): Promise<void>
  loadApprovalHistory(skip: number, limit: number): Promise<void>
}

const useApprovalStore = create<ApprovalAggregate>((set, get) => ({
  approval: null,
  pendingApprovals: [],
  selectedApproval: null,
  approvalHistory: [],
  isSubmittingApproval: false,
  validationErrors: [],
  
  loadPendingApprovals: async () => { /* ... */ },
  selectApproval: (approvalId) => { /* ... */ },
  approveInspection: async (notes) => { /* ... */ },
  rejectInspection: async (reason, notes) => { /* ... */ },
  loadApprovalHistory: async (skip, limit) => { /* ... */ },
}))
```

**Invariants** (Business Rules):
- BR-007: One approval per inspection (API enforces, frontend validates)
- BR-008: Approval is immutable (no edit, only read)
- BR-009: Rejection requires reason (validated in value object)

---

### **Aggregate 3: MastersAggregate**
**Root Entity**: `MasterDataCollection`

```typescript
type MastersAggregate = {
  // Root entities
  masters: {
    defects: Defect[]
    machines: Machine[]
    fabrics: Fabric[]
  }

  // Context state
  selectedMasterType: 'defects' | 'machines' | 'fabrics'
  editingMaster: MasterRecord | null
  isLoading: boolean
  isSaving: boolean
  validationErrors: ValidationError[]

  // Methods
  loadMasters(type: string): Promise<void>
  createMaster(type: string, data: object): Promise<void>
  updateMaster(type: string, id: string, data: object): Promise<void>
  inactivateMaster(type: string, id: string): Promise<void>
  importCsv(type: string, file: File): Promise<ImportResult>
  validateMasterData(data: object): ValidationError[]
}

const useMastersStore = create<MastersAggregate>((set, get) => ({
  masters: { defects: [], machines: [], fabrics: [] },
  selectedMasterType: 'defects',
  editingMaster: null,
  isLoading: false,
  isSaving: false,
  validationErrors: [],
  
  loadMasters: async (type) => { /* ... */ },
  createMaster: async (type, data) => { /* ... */ },
  // ... other methods
}))
```

**Invariants** (Business Rules):
- BR-010: Master ID uniqueness (API enforces, frontend validates)
- BR-011: Soft deletes only (status = "ACTIVE" or "INACTIVE")
- BR-012: Import idempotency (skip duplicates)

---

### **Aggregate 4: AuthAggregate**
**Root Entity**: `AuthenticatedUser`

```typescript
type AuthAggregate = {
  // Root entity
  user: {
    id: string
    email: EmailVO                  // Value Object
    roles: Role[]                   // Value Object[]
    accessToken: JWT                // Value Object
    refreshToken: JWT               // Value Object
    expiresAt: datetime
  }

  // Context state
  isAuthenticated: boolean
  isLoading: boolean
  loginError?: string
  lastAuthRefresh: datetime

  // Methods
  login(email: string, password: string): Promise<void>
  logout(): void
  refreshToken(): Promise<void>
  hasRole(role: Role): boolean
  canAccess(requiredRoles: Role[]): boolean
  updateProfile(data: object): Promise<void>
}

const useAuthStore = create<AuthAggregate>((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  loginError: undefined,
  lastAuthRefresh: null,
  
  login: async (email, password) => { /* ... */ },
  logout: () => { /* ... */ },
  refreshToken: async () => { /* ... */ },
  hasRole: (role) => { /* ... */ },
  canAccess: (roles) => { /* ... */ },
  updateProfile: async (data) => { /* ... */ },
}))
```

**Invariants** (Business Rules):
- ADR-003: JWT + Role Decorators (8h access token, 30d refresh)
- 4 roles: ANALISTA, JEFE_QA, ADMIN, GERENTE
- Tokens stored in memory (not localStorage for security)

---

### **Aggregate 5: OfflineAggregate**
**Root Entity**: `OfflineSyncQueue`

```typescript
type OfflineAggregate = {
  // Root entity
  syncQueue: {
    pending: PendingInspection[]
    failed: FailedInspection[]
    lastSyncTime: datetime
    syncStatus: SyncStatus         // Value Object
  }

  // Context state
  networkStatus: NetworkStatus    // Value Object: ONLINE | OFFLINE
  isSyncing: boolean
  syncProgress: number            // 0-100%
  syncErrors: SyncError[]
  retrySchedule: RetrySchedule[]  // [5s, 10s, 30s, 60s, 60s]

  // Methods
  initializeOfflineStorage(): Promise<void>
  queueInspectionForSync(inspection: Inspection): Promise<void>
  startAutoSync(): void
  pauseSync(): void
  retryFailedSync(): Promise<void>
  clearOfflineData(): Promise<void>
  getLocalInspections(): Promise<Inspection[]>
  getSyncStatus(): SyncStatusReport
}

const useOfflineStore = create<OfflineAggregate>((set, get) => ({
  syncQueue: { pending: [], failed: [], lastSyncTime: null, syncStatus: 'idle' },
  networkStatus: 'online',
  isSyncing: false,
  syncProgress: 0,
  syncErrors: [],
  retrySchedule: [5000, 10000, 30000, 60000, 60000],
  
  initializeOfflineStorage: async () => { /* ... */ },
  queueInspectionForSync: async (inspection) => { /* ... */ },
  startAutoSync: () => { /* ... */ },
  // ... other methods
}))
```

**Invariants** (Business Rules):
- ADR-001: Zero Data Loss (Multi-Layer Persistence)
  - Layer 1: IndexedDB (local storage before sync)
  - Layer 2: Idempotent API (inspection_id unique constraint)
  - Layer 3: Exponential backoff retry (5x attempts)
- Inspection UUID prevents duplicate submissions

---

## 🔷 VALUE OBJECTS

Value objects are immutable, validated, and focused on domain logic (not HTTP/storage).

### **Photo (Photo)**
```typescript
type Photo = {
  readonly id: UUID
  readonly filePath: string              // /storage/photos/YYYY/MM/DD/id.jpg
  readonly checksum: SHA256Hash          // 64-char hex
  readonly sizeKB: number                // 0-500
  readonly capturedAt: datetime
  readonly qualityScore: number          // 0-100 (Laplacian variance)
  readonly brightness: number            // 0-255
  readonly contrast: number              // std deviation
  
  isValid(): boolean
  getQualityFeedback(): string           // "Photo is blurry" | "Low brightness" | etc
  getFileDataUrl(): Promise<string>      // For preview
}

// Factory with validation
const createPhoto = (file: File): Result<Photo> => {
  if (file.size > 500 * 1024) {
    return Err("Photo exceeds 500KB")
  }
  if (!['image/jpeg', 'image/png'].includes(file.type)) {
    return Err("Only JPEG/PNG allowed")
  }
  return Ok(new Photo(...))
}
```

**Validation Rules** (ADR-002: Photo Quality Validation):
- Max 500KB size
- JPEG or PNG format
- Laplacian variance >50 (not blurry)
- Brightness 50-200
- Contrast >30
- Client-side validation before sync

---

### **Comment**
```typescript
type Comment = {
  readonly text: string
  readonly length: number
  readonly isValid: boolean
  
  validate(): ValidationError[]
}

// Factory
const createComment = (text: string): Result<Comment> => {
  if (text.length < 10 || text.length > 500) {
    return Err("Comment must be 10-500 characters")
  }
  return Ok(new Comment(text))
}
```

---

### **DefectSelection**
```typescript
type DefectSelection = {
  readonly defectId: string
  readonly defectName: string
  readonly category: string
  readonly severity: 'LOW' | 'MEDIUM' | 'HIGH'
  readonly machineId?: string            // Auto-filled from master data
  
  getMachineForDefect(): Promise<Machine>
}
```

---

### **SyncStatus**
```typescript
type SyncStatus = 
  | 'PENDING'        // Queued for sync
  | 'SYNCING'        // Currently syncing
  | 'SYNCED'         // Successfully synced
  | 'SYNC_FAILED'    // Sync failed, retrying
  | 'SYNC_ERROR'     // Unrecoverable error

type SyncStatusRecord = {
  readonly status: SyncStatus
  readonly retryCount: number
  readonly lastAttempt: datetime
  readonly errorMessage?: string
  readonly nextRetry?: datetime
}
```

---

### **NetworkStatus**
```typescript
type NetworkStatus = 'ONLINE' | 'OFFLINE' | 'SLOW'

type NetworkStatusEvent = {
  readonly status: NetworkStatus
  readonly timestamp: datetime
  readonly latency?: number             // ms
}
```

---

### **ApprovalDecision**
```typescript
type ApprovalDecision = {
  readonly decision: 'APPROVED' | 'REJECTED'
  readonly timestamp: datetime
  readonly submittedBy: string           // jefe_qa_id
}
```

---

### **RejectionReason**
```typescript
type RejectionReason = {
  readonly text: string
  
  validate(): ValidationError[]
}

// Factory
const createRejectionReason = (text: string): Result<RejectionReason> => {
  if (text.length < 10 || text.length > 500) {
    return Err("Reason must be 10-500 characters")
  }
  return Ok(new RejectionReason(text))
}
```

---

### **EmailVO**
```typescript
type EmailVO = {
  readonly value: string
  
  validate(): ValidationError[]
  getDomain(): string
}

// Factory with RFC validation
const createEmail = (text: string): Result<EmailVO> => {
  if (!isValidEmail(text)) {
    return Err("Invalid email format")
  }
  return Ok(new EmailVO(text))
}
```

---

## 🔗 DOMAIN SERVICES

Domain services encapsulate business logic that doesn't fit cleanly in an aggregate.

### **PhotoValidationService**
```typescript
interface PhotoValidationService {
  validatePhoto(file: File): Promise<ValidationResult>
  calculateQualityMetrics(imageData: ImageData): QualityMetrics
  getLaplacianVariance(pixels: Uint8Array): number      // Sharpness
  getBrightnessStats(pixels: Uint8Array): {avg, std}
  getContrastStats(pixels: Uint8Array): number
}
```

**Quality Metrics**:
- Blur (Laplacian variance): >50
- Brightness: 50-200
- Contrast: >30

---

### **OfflineSyncService**
```typescript
interface OfflineSyncService {
  initializeStorage(): Promise<void>
  saveToIndexedDB(inspection: Inspection): Promise<void>
  getFromIndexedDB(inspectionId: UUID): Promise<Inspection>
  getAllPendingFromIndexedDB(): Promise<Inspection[]>
  deleteFromIndexedDB(inspectionId: UUID): Promise<void>
  
  calculateBackoffDelay(retryCount: number): number  // [5, 10, 30, 60, 60]
  scheduleRetry(inspection: Inspection): Promise<void>
}
```

**Exponential Backoff** (ADR-001):
- Delays: 5s → 10s → 30s → 60s → 60s
- Max retries: 5
- Total window: ~165 seconds
- 100% data loss guarantee: Layer 1 (IndexedDB) + Layer 2 (API idempotency) + Layer 3 (retries)

---

### **RoleAuthorizationService**
```typescript
interface RoleAuthorizationService {
  canCreateInspection(user: User): boolean           // ANALISTA
  canApproveInspection(user: User): boolean          // JEFE_QA
  canManageMasters(user: User): boolean              // ADMIN
  canViewDashboard(user: User): boolean              // GERENTE
  canAccess(user: User, requiredRoles: Role[]): boolean
}
```

**Roles** (ADR-003):
- ANALISTA: Create inspections
- JEFE_QA: Approve/reject inspections
- ADMIN: Manage masters data
- GERENTE: View dashboard/reports

---

## 📊 LAYERED ARCHITECTURE (Frontend)

```
┌─────────────────────────────────────────┐
│        PRESENTATION LAYER               │
│  (Pages: Inspection, Approval, Config)  │
├─────────────────────────────────────────┤
│        COMPONENT LAYER                  │
│  (Forms, Tables, Modals, Layout)        │
├─────────────────────────────────────────┤
│       AGGREGATES LAYER (Zustand)        │
│  (InspectionAggregate, ApprovalAggregate)
├─────────────────────────────────────────┤
│      DOMAIN SERVICES LAYER              │
│  (PhotoValidation, OfflineSync, Auth)   │
├─────────────────────────────────────────┤
│        SERVICES LAYER (API)             │
│  (HTTP calls to FastAPI backend)        │
├─────────────────────────────────────────┤
│      PERSISTENCE LAYER                  │
│  (IndexedDB, localStorage, Session)     │
└─────────────────────────────────────────┘
```

---

## 🔐 CROSS-CUTTING CONCERNS

### **Error Handling**
- ValidationError (form validation)
- NetworkError (offline, timeout)
- AuthError (unauthorized, token expired)
- SyncError (sync failed, retry exhausted)
- ApiError (4xx, 5xx responses)

### **Logging**
- User actions (login, create inspection, approve)
- Sync events (started, progress, completed, failed)
- Validation errors (with user context)
- Network events (online/offline)

### **Performance**
- Memoization of selectors (Zustand)
- Lazy loading of images
- Virtual scrolling for long lists
- IndexedDB queries optimized

---

## 📋 SUMMARY TABLE

| Bounded Context | Root Aggregate | Key Invariants | Tech Implementation |
|---|---|---|---|
| **Inspection** | CurrentInspection | BR-001, BR-002, BR-004 | Zustand + IndexedDB |
| **Approval** | PendingApproval | BR-007, BR-008, BR-009 | Zustand + API |
| **Masters** | MasterDataCollection | BR-010, BR-011, BR-012 | Zustand + API |
| **Auth** | AuthenticatedUser | 4 roles, JWT tokens | Zustand + localStorage |
| **Offline** | OfflineSyncQueue | Zero data loss, idempotency | Service Worker + IndexedDB |

---

**Status**: ✅ DOMAIN ENTITIES DEFINED  
**Next**: Proceed to business-rules.md and business-logic-model.md for Frontend Web unit
