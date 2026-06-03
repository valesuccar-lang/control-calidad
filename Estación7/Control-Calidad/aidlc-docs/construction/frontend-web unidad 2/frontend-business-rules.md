# Business Rules — Frontend Web (React + TypeScript)

**Date**: 2026-05-31  
**Unit**: Frontend Web (React + TypeScript)  
**Total Rules**: 28 rules organized by bounded context  
**Status**: ✅ DESIGN PHASE

---

## 📋 RULE INDEX

| # | Context | Rule | Category |
|---|---------|------|----------|
| **FR-001** | Inspection | Mandatory inspection fields | Form Validation |
| **FR-002** | Inspection | Photo size must not exceed 500KB | Photo Validation |
| **FR-003** | Inspection | Photo quality validation (blur, brightness, contrast) | Photo Quality |
| **FR-004** | Inspection | Comment must be 10-500 characters | Text Validation |
| **FR-005** | Inspection | Lote must exist and be in PENDING status | Business Logic |
| **FR-006** | Inspection | Machine auto-filled from defect mapping | UI Logic |
| **FR-007** | Inspection | Photo must be JPEG or PNG only | File Validation |
| **FR-008** | Inspection | Cannot create inspection without online connection or offline queue | Sync Dependency |
| **FR-009** | Inspection | Inspection history shows only user's own inspections | Privacy/RBAC |
| **FR-010** | Inspection | Inspection save disabled until all validations pass | UX/State |
| **FR-011** | Approval | Can only see pending approvals for own role (JEFE_QA) | RBAC |
| **FR-012** | Approval | Approval requires decision (APPROVED or REJECTED) | Form Validation |
| **FR-013** | Approval | Rejection requires reason (10-500 characters) | Conditional Validation |
| **FR-014** | Approval | Cannot approve already-approved inspection | Business Logic |
| **FR-015** | Approval | Approval photo preview must load from backend | Image Handling |
| **FR-016** | Approval | Approval history is read-only (no edit) | Immutability |
| **FR-017** | Masters | Only ADMIN can create/edit/inactivate masters | RBAC |
| **FR-018** | Masters | Master data must be cached locally for offline access | Offline Support |
| **FR-019** | Masters | CSV import validates all rows before committing | Batch Validation |
| **FR-020** | Masters | Duplicate master IDs in import are skipped (idempotency) | Idempotency |
| **FR-021** | Masters | Inactive masters hidden from dropdowns (status = ACTIVE only) | Data Filtering |
| **FR-022** | Auth | Must login before accessing any protected page | Authentication Gate |
| **FR-023** | Auth | Access token expires after 8 hours, must refresh | Token Expiration |
| **FR-024** | Auth | Invalid login shows generic error (no user enumeration) | Security |
| **FR-025** | Offline | Pending inspections queued in IndexedDB before sync | Persistence |
| **FR-026** | Offline | Sync with exponential backoff: 5s → 10s → 30s → 60s → 60s | Retry Logic |
| **FR-027** | Offline | Sync fails after 5 attempts, manual retry available | Exhaustion Handling |
| **FR-028** | Offline | Network status indicator visible in header (online/offline/syncing) | UX Feedback |

---

## 🔍 DETAILED RULES BY CONTEXT

---

## **INSPECTION CONTEXT** (9 rules)

### **FR-001: Mandatory Inspection Fields**

**Rule ID**: FR-001  
**Context**: Inspection  
**Statement**: An inspection form cannot be submitted without all mandatory fields populated:
- Lote ID (scanned or selected)
- Defect type (from dropdown)
- Comment (≥10 characters)
- Photo (captured and validated)
- Machine (auto-filled or manually selected)

**Rationale**: Ensures data quality and completeness in sync with backend BR-001. All fields are required by business process.

**Enforcement Mechanism**:
- Submit button disabled until all fields valid
- Visual indicators (red border, error message) for missing/invalid fields
- Real-time validation as user types

**Validation Approach**:
```typescript
const canSubmitInspection = (state) => {
  return state.loteId && 
         state.defectId && 
         state.comment.length >= 10 &&
         state.photo !== null &&
         state.machineId
}
```

---

### **FR-002: Photo Size Limit**

**Rule ID**: FR-002  
**Context**: Inspection  
**Statement**: Photo file size must not exceed 500KB before upload.

**Rationale**: Sync performance and backend storage limits. Large photos cause longer sync times.

**Enforcement Mechanism**:
- Client-side validation before IndexedDB storage
- Error message: "Photo exceeds 500KB limit (max: 500KB)"
- User must retake or select different photo

**Validation Approach**:
```typescript
const validatePhotoSize = (file: File): ValidationError[] => {
  const sizeKB = file.size / 1024
  if (sizeKB > 500) {
    return [{ field: 'photo', message: `Photo is ${Math.round(sizeKB)}KB (max: 500KB)` }]
  }
  return []
}
```

---

### **FR-003: Photo Quality Validation** (ADR-002)

**Rule ID**: FR-003  
**Context**: Inspection  
**Statement**: Photo must pass quality metrics before acceptance:
- **Blur Check**: Laplacian variance > 50 (not blurry)
- **Brightness Check**: 50-200 range (well-lit, not washed)
- **Contrast Check**: Std deviation > 30 (distinguishable features)

**Rationale**: Prevents low-quality photos that can't be analyzed. Improves visual inspection accuracy.

**Enforcement Mechanism**:
- Real-time feedback after photo capture
- Quality score displayed (0-100%)
- Disable "Save" button if quality < threshold
- Offer "Retake" button for poor quality photos

**Feedback Messages**:
- "Photo is too blurry (sharpness: 35/50)" — Suggest steadier hand
- "Photo is too dark (brightness: 40/50-200)" — Suggest better lighting
- "Photo lacks contrast (contrast: 20/30)" — Suggest different angle

**Validation Approach** (Canvas-based):
```typescript
const calculatePhotoQuality = async (file: File) => {
  const imageData = await getImageData(file)
  const laplacian = calculateLaplacian(imageData)
  const brightness = calculateBrightness(imageData)
  const contrast = calculateContrast(imageData)
  
  return {
    blur: laplacian > 50 ? 'pass' : 'fail',
    brightness: brightness >= 50 && brightness <= 200 ? 'pass' : 'fail',
    contrast: contrast > 30 ? 'pass' : 'fail',
    isValid: [blur, brightness, contrast].every(x => x === 'pass')
  }
}
```

**Consequence**: ~200 lines of image processing code (Canvas API). May reject some valid photos (false negatives ~5%).

---

### **FR-004: Comment Length Validation**

**Rule ID**: FR-004  
**Context**: Inspection  
**Statement**: Comment field must contain 10-500 characters.

**Rationale**: Enforces meaningful comments (not "ok" or "good"), aligns with backend BR-002.

**Enforcement Mechanism**:
- Real-time character count display
- Error message: "Comment must be 10-500 characters (current: X)"
- Submit button disabled if invalid length

**Validation Approach**:
```typescript
const isCommentValid = (text: string): boolean => {
  return text.length >= 10 && text.length <= 500
}
```

---

### **FR-005: Lote Must Exist and Be PENDING**

**Rule ID**: FR-005  
**Context**: Inspection  
**Statement**: Selected lote must exist in backend database and have status = "PENDING".

**Rationale**: Prevents inspecting finished or non-existent lotes. Maintains data integrity.

**Enforcement Mechanism**:
- Lote search queries backend API
- Display "Lote not found" or "Lote already inspected"
- Only allow selection of PENDING lotes
- Lote info cached locally for offline access

**Validation Approach**:
```typescript
const validateLote = async (loteId: string) => {
  const lote = await inspectionService.searchLote(loteId)
  if (!lote) return { error: "Lote not found" }
  if (lote.status !== "PENDING") return { error: "Lote is not pending" }
  return { success: true, lote }
}
```

---

### **FR-006: Machine Auto-Fill from Defect Mapping**

**Rule ID**: FR-006  
**Context**: Inspection  
**Statement**: When defect is selected, machine field is automatically populated from master data mapping.

**Rationale**: Reduces user input, improves speed, reduces errors. Most defects are machine-specific.

**Enforcement Mechanism**:
- Defect dropdown change triggers machine auto-fill
- Auto-filled value is editable (user can override)
- If no mapping exists, field remains empty but editable

**Logic**:
```typescript
const handleDefectChange = (defectId: string) => {
  const machineMapping = getMachineForDefect(defectId)
  setMachineId(machineMapping?.machineId || null)
}
```

---

### **FR-007: Photo Format Validation**

**Rule ID**: FR-007  
**Context**: Inspection  
**Statement**: Photo file must be JPEG (image/jpeg) or PNG (image/png) format only.

**Rationale**: Ensures compatibility with backend storage and processing. Prevents unsupported formats (BMP, GIF, WebP).

**Enforcement Mechanism**:
- File input accept attribute: `accept=".jpg,.jpeg,.png"`
- Validate MIME type after file selection
- Error message: "Only JPEG and PNG photos allowed"

**Validation Approach**:
```typescript
const validatePhotoFormat = (file: File): boolean => {
  return ['image/jpeg', 'image/png'].includes(file.type)
}
```

---

### **FR-008: Offline Queue Required for Save**

**Rule ID**: FR-008  
**Context**: Inspection  
**Statement**: Inspection can be saved if:
- Online connection available (can sync immediately), OR
- Offline mode enabled (save to IndexedDB, sync later)

**Rationale**: Prevents confusion between online/offline states. Guarantees data is stored locally.

**Enforcement Mechanism**:
- Check network status before save
- If offline: Save to IndexedDB, show "Saved locally" message
- If online: Save to IndexedDB AND POST to API immediately
- If neither: Show error "Unable to save (offline storage not initialized)"

**Logic**:
```typescript
const handleSaveInspection = async () => {
  const isSaved = await offlineStore.queueInspectionForSync(inspection)
  if (isOnline) {
    await syncService.syncNow()
  }
}
```

---

### **FR-009: Inspection History Shows Only User's Inspections**

**Rule ID**: FR-009  
**Context**: Inspection  
**Statement**: Inspection history table displays only inspections created by the current user (ANALISTA).

**Rationale**: Privacy and role-based access control. Users see their own work only.

**Enforcement Mechanism**:
- Query API with user_id filter: `/api/inspections?analista_id={currentUserId}`
- Load history on page load
- Refresh button available
- No admin override to see all users' inspections

**Validation Approach**:
```typescript
const loadMyInspections = async (skip: number = 0, limit: number = 50) => {
  const userId = useAuthStore((s) => s.user.id)
  const inspections = await inspectionService.getInspectionsByAnalista(userId, skip, limit)
  setInspectionHistory(inspections)
}
```

---

### **FR-010: Save Button Disabled Until All Validations Pass**

**Rule ID**: FR-010  
**Context**: Inspection  
**Statement**: "Save" button is disabled (greyed out, non-clickable) until all form validations pass.

**Rationale**: Prevents submission of incomplete or invalid inspections. Improves UX by providing clear feedback.

**Enforcement Mechanism**:
- Button state computed from form validity
- CSS class: `disabled` → opacity 0.5, cursor not-allowed
- Hover tooltip: "Please fix errors before saving"

**React Implementation**:
```typescript
<button 
  onClick={handleSave}
  disabled={!canSubmitInspection(formState)}
  className={canSubmitInspection(formState) ? 'btn-primary' : 'btn-disabled'}
>
  Save Inspection
</button>
```

---

## **APPROVAL CONTEXT** (6 rules)

### **FR-011: Can Only See Pending Approvals for Own Role**

**Rule ID**: FR-011  
**Context**: Approval  
**Statement**: User with JEFE_QA role sees only pending approvals assigned to them. ADMIN and GERENTE see all.

**Rationale**: RBAC enforcement. Different roles have different approval queues.

**Enforcement Mechanism**:
- API endpoint respects role: `/api/approvals/pending` filters by jefe_qa_id
- Frontend enforces role check: `<PrivateRoute requiredRole="JEFE_QA" />`
- Unauthorized users see error page or redirect

**Validation Approach**:
```typescript
const canViewApprovals = (user: User): boolean => {
  return ['JEFE_QA', 'ADMIN', 'GERENTE'].includes(user.role)
}

const loadPendingApprovals = async () => {
  if (userRole === 'JEFE_QA') {
    return api.get('/api/approvals/pending?jefe_qa_id=' + userId)
  } else {
    return api.get('/api/approvals/pending')  // All
  }
}
```

---

### **FR-012: Approval Requires Decision**

**Rule ID**: FR-012  
**Context**: Approval  
**Statement**: Approval form submission requires selecting a decision: "APPROVED" or "REJECTED".

**Rationale**: Cannot submit approval without explicit decision. Prevents accidental clicks.

**Enforcement Mechanism**:
- Two radio buttons (APPROVED, REJECTED) required
- Submit button disabled until decision selected
- Visual indication of selected decision

**Validation**:
```typescript
const isDecisionSelected = (state) => state.decision !== null
```

---

### **FR-013: Rejection Requires Reason**

**Rule ID**: FR-013  
**Context**: Approval  
**Statement**: If "REJECTED" is selected, rejection reason field must be populated with 10-500 characters.

**Rationale**: Rejects must have documented reasons for traceability. Supports BR-009 (rejection reason requirement).

**Enforcement Mechanism**:
- Rejection reason field appears only when REJECTED selected
- Required field validation if REJECTED
- Same character count rules as inspection comment
- Error: "Rejection reason required (10-500 characters)"

**Conditional Validation**:
```typescript
const validateApprovalForm = (state) => {
  if (state.decision === 'REJECTED' && (!state.rejectionReason || state.rejectionReason.length < 10)) {
    return [{ field: 'rejectionReason', message: 'Reason required (10+ chars)' }]
  }
  return []
}
```

---

### **FR-014: Cannot Approve Already-Approved Inspection**

**Rule ID**: FR-014  
**Context**: Approval  
**Statement**: If inspection already has approval record (from another JEFE_QA or offline conflict), show error message and prevent duplicate approval.

**Rationale**: Enforces BR-007 (one approval per inspection) at frontend level. Provides immediate feedback.

**Enforcement Mechanism**:
- Before showing approval form, check if approval already exists
- If exists: Display message "This inspection was already approved by [name] on [date]"
- Hide approval form, show read-only approval details

**Validation Approach**:
```typescript
const checkApprovalExists = async (inspectionId: UUID) => {
  const approval = await approvalService.getApprovalByInspection(inspectionId)
  if (approval) {
    return { exists: true, approval }
  }
  return { exists: false }
}
```

---

### **FR-015: Approval Photo Preview Must Load from Backend**

**Rule ID**: FR-015  
**Context**: Approval  
**Statement**: Photo displayed in approval detail modal is loaded from backend file storage (/storage/photos/...), not cached.

**Rationale**: Ensures latest photo is shown. Prevents stale/incorrect photos if backend photo changed.

**Enforcement Mechanism**:
- Photo URL constructed from backend storage path
- No caching headers (Cache-Control: no-cache)
- Image load error shown if photo not found
- Loading spinner while photo fetches

**Image Handling**:
```typescript
const getPhotoUrl = (photoPath: string) => {
  // photoPath: /storage/photos/2026/05/31/inspection_id.jpg
  return `${API_BASE_URL}/photos/${photoPath}?t=${Date.now()}`  // Bust cache
}

<img 
  src={getPhotoUrl(approval.photo_path)} 
  alt="Inspection photo"
  onError={() => setPhotoError("Photo not found")}
/>
```

---

### **FR-016: Approval History is Read-Only**

**Rule ID**: FR-016  
**Context**: Approval  
**Statement**: Approval history table shows past approvals but cannot be edited or deleted. All fields are read-only.

**Rationale**: Immutability enforcement (BR-008). Audit trail cannot be modified.

**Enforcement Mechanism**:
- Table shows inspection_id, decision, rejection_reason, approver, timestamp
- No edit/delete buttons visible
- Click on row shows detail modal (read-only, no buttons)
- No inline editing

**React Implementation**:
```typescript
<ApprovalHistoryTable 
  approvals={history} 
  readOnly={true}
  onRowClick={(approval) => showDetailModal(approval)}
/>
```

---

## **MASTERS CONTEXT** (5 rules)

### **FR-017: Only ADMIN Can Manage Masters**

**Rule ID**: FR-017  
**Context**: Masters  
**Statement**: Only users with ADMIN role can create, edit, or inactivate master data (defects, machines, fabrics).

**Rationale**: Data integrity. Prevents accidental modifications by unauthorized users.

**Enforcement Mechanism**:
- Config page requires ADMIN role: `<PrivateRoute requiredRole="ADMIN" />`
- All CRUD buttons hidden for non-ADMIN users
- API enforces same check (defense in depth)
- Error message for unauthorized access

**Validation**:
```typescript
const canEditMasters = (user: User): boolean => {
  return user.roles.includes('ADMIN')
}
```

---

### **FR-018: Master Data Cached Locally for Offline Access**

**Rule ID**: FR-018  
**Context**: Masters  
**Statement**: Master data (defects, machines, fabrics) is cached in IndexedDB for offline access. Dropdowns populate from cache first.

**Rationale**: Offline-first UX. Users can still select defects/machines without internet.

**Enforcement Mechanism**:
- Load masters on app startup (if online)
- Store in IndexedDB
- Dropdowns query IndexedDB first (fast)
- If online, background sync updates cache
- If offline, use stale cache without error

**Caching Logic**:
```typescript
const getMastersFromCache = async () => {
  const cached = await offlineService.getFromIndexedDB('masters')
  return cached || []
}

const refreshMastersIfOnline = async () => {
  if (isOnline) {
    const fresh = await mastersService.getMasters()
    await offlineService.saveToIndexedDB('masters', fresh)
  }
}
```

---

### **FR-019: CSV Import Validates All Rows Before Committing**

**Rule ID**: FR-019  
**Context**: Masters  
**Statement**: When importing CSV file with master data:
1. Parse all rows
2. Validate each row (required fields, format, data type)
3. If any row invalid: Show error summary, don't import anything (all-or-nothing)
4. If all valid: Import and show success count

**Rationale**: Prevents partial imports. User sees all errors before committing.

**Enforcement Mechanism**:
- CSV parser with validation rules per field
- Error table shows row number, field, error message
- "Import" button disabled if errors exist
- Success modal shows count: "Imported 42 defects (2 skipped as duplicates)"

**Validation Approach**:
```typescript
const validateCsvImport = (rows: object[]) => {
  const errors = []
  rows.forEach((row, idx) => {
    if (!row.defect_id) errors.push({ row: idx + 1, field: 'defect_id', error: 'Required' })
    if (!row.name) errors.push({ row: idx + 1, field: 'name', error: 'Required' })
    if (row.severity && !['LOW', 'MEDIUM', 'HIGH'].includes(row.severity)) {
      errors.push({ row: idx + 1, field: 'severity', error: 'Invalid value' })
    }
  })
  return errors
}
```

---

### **FR-020: Duplicate Master IDs Skipped in Import** (Idempotency)

**Rule ID**: FR-020  
**Context**: Masters  
**Statement**: If CSV import contains duplicate master IDs (within same import or already in system), those rows are skipped with status "duplicate".

**Rationale**: Idempotency (BR-012). Allows retry of imports without side effects.

**Enforcement Mechanism**:
- Track imported IDs during import loop
- Check if ID already exists: `if (existingIds.has(id)) { skip() }`
- Return count: "Imported 40, Skipped 2 (duplicates)"
- Show skipped IDs in summary

**Logic**:
```typescript
const importWithIdempotency = async (rows: object[]) => {
  const existingIds = new Set(masters.map(m => m.id))
  const imported = []
  const skipped = []
  
  for (const row of rows) {
    if (existingIds.has(row.id)) {
      skipped.push(row.id)
    } else {
      imported.push(row)
      existingIds.add(row.id)
    }
  }
  
  return { imported, skipped }
}
```

---

### **FR-021: Inactive Masters Hidden from Dropdowns**

**Rule ID**: FR-021  
**Context**: Masters  
**Statement**: Master data with status = "INACTIVE" should not appear in dropdowns (defect type, machine, fabric selectors).

**Rationale**: UX clarity. Users only see active, usable options. Soft-deleted data still in system (auditable).

**Enforcement Mechanism**:
- Filter dropdowns: `masters.filter(m => m.status === 'ACTIVE')`
- Cache refreshes when masters updated
- Admin sees "INACTIVE" badge in management table

**React Implementation**:
```typescript
const getActiveDefects = () => {
  return defects.filter(d => d.status === 'ACTIVE')
}

<select value={defectId} onChange={handleDefectChange}>
  {getActiveDefects().map(d => <option key={d.id}>{d.name}</option>)}
</select>
```

---

## **AUTH CONTEXT** (4 rules)

### **FR-022: Must Login Before Accessing Protected Pages**

**Rule ID**: FR-022  
**Context**: Auth  
**Statement**: Any page except /login requires valid authentication. Unauthenticated users are redirected to login page.

**Rationale**: Security. Protects sensitive data (inspections, approvals) from unauthorized access.

**Enforcement Mechanism**:
- PrivateRoute HOC checks authentication
- If not authenticated: Redirect to /login
- Token checked on app startup
- Expired token triggers token refresh or re-login

**Implementation**:
```typescript
const PrivateRoute = ({ children, requiredRoles }) => {
  const { isAuthenticated, user } = useAuthStore()
  
  if (!isAuthenticated) {
    return <Navigate to="/login" />
  }
  
  if (requiredRoles && !requiredRoles.includes(user.role)) {
    return <Unauthorized />
  }
  
  return children
}
```

---

### **FR-023: Access Token Expires After 8 Hours**

**Rule ID**: FR-023  
**Context**: Auth  
**Statement**: Access token is valid for 8 hours from login. After expiration, user must refresh or re-login.

**Rationale**: ADR-003 compliance. Time-limited tokens reduce risk if token is compromised.

**Enforcement Mechanism**:
- Token decoded to extract `exp` claim
- Before API call: Check if `exp < Date.now()`
- If expired: Attempt refresh using refresh token
- If refresh fails: Redirect to login

**Token Refresh Logic**:
```typescript
const refreshAccessTokenIfNeeded = async () => {
  const { accessToken, refreshToken } = useAuthStore()
  const decoded = jwt_decode(accessToken)
  
  if (decoded.exp < Date.now() / 1000) {
    try {
      const newToken = await authService.refreshToken(refreshToken)
      useAuthStore.setState({ accessToken: newToken })
    } catch {
      // Redirect to login
      navigate('/login')
    }
  }
}
```

---

### **FR-024: Invalid Login Shows Generic Error**

**Rule ID**: FR-024  
**Context**: Auth  
**Statement**: If login fails (invalid email or password), show generic error message "Invalid credentials" instead of revealing whether email exists.

**Rationale**: Security (username enumeration prevention). Prevents attackers from discovering valid emails.

**Enforcement Mechanism**:
- Same error message for both "user not found" and "password incorrect"
- Error message: "Invalid email or password"
- No differentiation in UI or API response

**Error Handling**:
```typescript
const handleLogin = async (email, password) => {
  try {
    await authService.login(email, password)
  } catch (error) {
    // Don't show specific error
    setLoginError("Invalid email or password")
  }
}
```

---

### **FR-025 (moved to Offline): Pending Inspections Queued in IndexedDB**

---

## **OFFLINE CONTEXT** (4 rules)

### **FR-025: Pending Inspections Queued in IndexedDB Before Sync**

**Rule ID**: FR-025  
**Context**: Offline  
**Statement**: When inspection is saved and offline (or online but before sync), it is stored in IndexedDB with sync_status = "PENDING".

**Rationale**: ADR-001 Zero Data Loss. Guarantees inspection survives app crash/browser close.

**Enforcement Mechanism**:
- Before API POST: `await offlineService.saveToIndexedDB(inspection)`
- IndexedDB transaction is synchronous/blocking
- Only after confirmed write: Set sync_status = PENDING
- Service Worker monitors IndexedDB for pending items

**Storage Logic**:
```typescript
const queueInspectionForSync = async (inspection: Inspection) => {
  const db = await openIndexedDB('textile-qc')
  const tx = db.transaction('inspections', 'readwrite')
  const store = tx.objectStore('inspections')
  
  inspection.sync_status = 'PENDING'
  await store.put(inspection)
  
  return new Promise((resolve, reject) => {
    tx.oncomplete = () => resolve(inspection)
    tx.onerror = () => reject(tx.error)
  })
}
```

---

### **FR-026: Sync with Exponential Backoff**

**Rule ID**: FR-026  
**Context**: Offline  
**Statement**: When syncing pending inspections with API:
- First attempt: 5 second delay
- Second attempt: 10 second delay
- Third attempt: 30 second delay
- Fourth attempt: 60 second delay
- Fifth attempt: 60 second delay (capped)

**Rationale**: ADR-001 + ADR-005. Graceful retry for transient network failures. Respects server load.

**Enforcement Mechanism**:
- Service Worker implements retry loop
- Delays stored in config: `[5000, 10000, 30000, 60000, 60000]`
- Each failed sync increments retry_count
- User sees sync progress (icon, percentage)

**Retry Logic**:
```typescript
const syncWithExponentialBackoff = async (inspection: Inspection) => {
  const delays = [5000, 10000, 30000, 60000, 60000]
  
  for (let attempt = 0; attempt < delays.length; attempt++) {
    try {
      await syncService.syncInspection(inspection)
      return { success: true }
    } catch (error) {
      if (attempt < delays.length - 1) {
        await sleep(delays[attempt])
      } else {
        return { success: false, error }
      }
    }
  }
}
```

---

### **FR-027: Sync Fails After 5 Attempts, Manual Retry Available**

**Rule ID**: FR-027  
**Context**: Offline  
**Statement**: After 5 failed sync attempts (exhausting exponential backoff), inspection sync is marked SYNC_FAILED. User sees error and can manually retry.

**Rationale**: Prevents infinite retry loop. Alerts user to unrecoverable error.

**Enforcement Mechanism**:
- Sync status changes to SYNC_FAILED after 5 attempts
- User sees failed items in sync status panel
- Manual "Retry Now" button triggers immediate retry
- Error message shows last error (e.g., "Network timeout")

**UI State**:
```typescript
// Sync status panel
{syncQueue.failed.length > 0 && (
  <div className="sync-error">
    <p>{syncQueue.failed.length} inspection(s) failed to sync</p>
    <p>Last error: {syncQueue.failed[0].errorMessage}</p>
    <button onClick={() => syncService.retryFailed()}>Retry Now</button>
  </div>
)}
```

---

### **FR-028: Network Status Indicator Visible**

**Rule ID**: FR-028  
**Context**: Offline  
**Statement**: Header displays current network status:
- 📡 **ONLINE** (green) — Connected, can sync
- 🔴 **OFFLINE** (red) — No connection, queuing locally
- 🔄 **SYNCING** (yellow) — In progress, don't close app

**Rationale**: User awareness. Clear feedback about offline-first status and sync progress.

**Enforcement Mechanism**:
- Network status updated via Service Worker
- Icon + text in header always visible
- Tooltip shows "Last synced: 2 minutes ago"
- Sync progress bar while syncing

**Component**:
```typescript
<div className="network-status">
  {networkStatus === 'ONLINE' && <span className="online">📡 Online</span>}
  {networkStatus === 'OFFLINE' && <span className="offline">🔴 Offline ({pendingCount} queued)</span>}
  {networkStatus === 'SYNCING' && <span className="syncing">🔄 Syncing {syncProgress}%</span>}
</div>
```

---

## 📊 SUMMARY TABLE

| Bounded Context | # Rules | Key Themes |
|---|---|---|
| **Inspection** | 9 | Photo quality, validation, offline queue |
| **Approval** | 6 | RBAC, decision required, immutability |
| **Masters** | 5 | Admin-only, caching, CSV import with idempotency |
| **Auth** | 4 | Login gate, token expiration, generic errors |
| **Offline** | 4 | IndexedDB queue, exponential backoff, network indicator |

**Total Rules**: 28

---

## 🔗 TRACEABILITY

Rules traced to:
- **Backend Business Rules** (business-rules.md): FR-001↔BR-001, FR-004↔BR-002, FR-013↔BR-009, etc.
- **ADRs**: FR-002↔ADR-002 (Photo Validation), FR-025↔ADR-001 (Zero Data Loss), etc.
- **Domain Entities** (frontend-entities.md): Photo, Comment, SyncStatus value objects

---

**Status**: ✅ BUSINESS RULES DEFINED  
**Next**: business-logic-model.md (workflows and use cases)
