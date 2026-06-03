# Business Logic Model — Frontend Web (React + TypeScript)

**Date**: 2026-05-31  
**Unit**: Frontend Web (React + TypeScript)  
**Total Workflows**: 4 main use cases with detailed process flows  
**Status**: ✅ DESIGN PHASE

---

## 📋 WORKFLOW INDEX

| # | Use Case | Actor | Goal | Complexity |
|---|----------|-------|------|------------|
| **UC1** | Register Inspection | Analista | Capture defect + photo + comment + save | High (photo validation + offline) |
| **UC2** | Approve/Reject Inspection | Jefe QA | Review + decide + document reason | Medium |
| **UC3** | Manage Masters Data | Admin | CRUD maestros + CSV import | Medium |
| **UC4** | Offline Sync | System (Automatic) | Sync pending inspections with retries | High (exponential backoff) |

---

## 🔄 UC1: REGISTER INSPECTION (Analista)

**Actor**: Analista (textile inspector in factory)  
**Goal**: Capture defect finding with photo, defect type, and comment, then save locally/sync to backend  
**Preconditions**: User authenticated, app loaded, camera/microphone permissions granted  
**Success Criteria**: Inspection saved to IndexedDB with PENDING sync status, or synced to API if online

### **MAIN FLOW** (Happy Path)

```
1. Analista opens Inspection page
   → Page loads lotes list from cache (or API if online)
   → Network status indicator shows: 📡 ONLINE

2. Analista searches for lote (HDR-12847)
   → Input triggers API query: GET /api/lotes?q=HDR-12847
   → Results show 3 lotes matching search
   → Analista selects lote HDR-12847
   → Page shows: Lote status = PENDING, quantity = 100 meters

3. System pre-loads lote details
   → Defect dropdown shows 25+ active defects (from cache)
   → Machine dropdown empty (user will select after defect)

4. Analista opens camera and captures photo
   → Permission dialog shown (if first time): "App needs camera access"
   → Analista clicks photo, canvas shows preview
   → Photo file size: 245 KB ✅ (under 500KB limit)
   
5. System validates photo quality
   → Laplacian variance = 72 ✅ (>50, not blurry)
   → Brightness = 120 ✅ (50-200 range)
   → Contrast = 42 ✅ (>30)
   → Quality score: 98% 🟢
   → "Photo quality: Good" message shown

6. Analista selects defect type
   → Clicks dropdown: "Tear" (defect_id: DEF_001)
   → System auto-fills machine: "Loom A" (from master mapping)
   → Machine field is editable (user can override if needed)

7. Analista enters comment
   → Types: "Found 3cm tear on warp side of fabric"
   → Character count shown: 45/500 ✅
   → Real-time validation: "✅ Valid comment"

8. Analista clicks "Save Inspection"
   → Form validated: All fields present, all validations pass
   → Save button enabled, analista clicks it
   → UI shows loading spinner: "Saving..."

9. System stores inspection
   → IF ONLINE:
      → POST /api/inspections (JSON with all fields + photo binary)
      → Backend returns: inspection_id = "550e8400-e29b-41d4-a716-446655440000"
      → Update IndexedDB: sync_status = SYNCED
      → Toast message: "✅ Inspection saved and synced"
      → Inspection appears in history table
   
   → IF OFFLINE:
      → Save to IndexedDB with sync_status = PENDING
      → Toast message: "✅ Saved locally (pending sync when online)"
      → Offline queue shows: "1 inspection queued"
      → Service Worker monitors queue for sync opportunity

10. Inspection added to user's history
    → Table refreshes, new inspection visible at top
    → Timestamp: "2026-05-31 14:23:45 UTC"
    → Status badge: "🔄 Pending sync" (if offline) or "✅ Synced" (if online)

11. Form resets for next inspection
    → All fields cleared
    → Lote dropdown stays focused
    → Analista ready for next defect
```

### **ALTERNATIVE FLOW A: Photo Quality Validation Fails**

```
5a. System validates photo quality
    → Laplacian variance = 35 ❌ (< 50, blurry)
    → Quality score: 22% 🔴
    → Message shown: "⚠️ Photo is blurry. Please retake."
    → "Retake Photo" button enabled
    → "Save" button DISABLED (cannot proceed)

6a. Analista clicks "Retake Photo"
    → Camera preview resets
    → Flow returns to step 4 (capture photo again)

7a. [After retake] Photo quality passes
    → Resume flow at step 5 (validation successful)
```

### **ALTERNATIVE FLOW B: Lote Not Found**

```
2b. Analista searches for non-existent lote
    → API returns empty results: []
    → Message shown: "❌ Lote HDR-99999 not found"
    → Lote dropdown empty, selection cannot proceed
    → Suggestion: "Check lote code or scan barcode again"

3b. [User corrects search]
    → Flow returns to step 2 (search again)
```

### **ALTERNATIVE FLOW C: Network Connection Lost During Save**

```
9c. Analista clicks "Save Inspection"
    → Network status changes: ONLINE → OFFLINE
    → POST request times out after 30 seconds
    → Toast error: "⚠️ Failed to save online, saved locally instead"
    → Inspection stored in IndexedDB with sync_status = PENDING
    → Offline indicator updates: "🔴 OFFLINE (1 queued)"
    → Service Worker will auto-sync when online again

10c. [Later, network restored]
     → Service Worker detects online status
     → Starts sync immediately (or waits for next interval)
     → Flow: UC4 (Offline Sync)
```

### **ERROR MATRIX**

| Error | Cause | User Sees | Resolution |
|-------|-------|-----------|------------|
| Photo > 500KB | Large image | "Photo too large (X KB, max 500KB)" | Retake with lower resolution |
| Photo blurry | Shaky hand | "Photo is blurry. Steady your hand." | Retake |
| Photo dark | Poor lighting | "Photo too dark (brightness: Y/50-200)" | Improve lighting |
| Photo low contrast | Monochrome | "Photo lacks contrast (C/30)" | Different angle |
| Comment < 10 chars | Too short | "Comment too short (X/10 chars)" | Add more detail |
| Lote not found | Typo | "Lote not found. Check code." | Re-scan barcode |
| Offline + IndexedDB full | Storage limit | "Storage full. Delete old inspections?" | Clear cache |

### **TIMING & PERFORMANCE**

| Step | Expected Duration | Notes |
|------|-------------------|-------|
| Load lotes | 1-2 sec (online) | Instant if cached |
| Search lote | 0.5-1 sec | API query + filter |
| Capture photo | 3-5 sec | User action (camera) |
| Validate photo quality | 1-2 sec | Canvas pixel analysis |
| POST inspection | 2-5 sec (online) | JSON + binary photo |
| Save to IndexedDB | <0.1 sec | Local DB (fast) |
| **Total** | **10-20 sec** | Most time is user actions |

---

## 🟢 UC2: APPROVE/REJECT INSPECTION (Jefe QA)

**Actor**: Jefe QA (quality assurance supervisor)  
**Goal**: Review inspection, decide approval/rejection, document reason (if rejecting)  
**Preconditions**: User authenticated as JEFE_QA, inspections available for approval  
**Success Criteria**: Approval record created, inspection marked as approved/rejected

### **MAIN FLOW**

```
1. Jefe QA opens Approval page
   → Page queries: GET /api/approvals/pending?jefe_qa_id={userId}
   → Table shows 5 pending approvals awaiting decision
   → Each row shows: Lote ID, Analista name, Check-in time, Status
   → Network indicator: 📡 ONLINE

2. Jefe QA selects first pending inspection
   → Clicks row: "HDR-12847 | 2026-05-31 14:23 | Pending"
   → Detail modal opens showing:
      → Photo (large preview, zoomed)
      → Defect type: "Tear"
      → Comment: "Found 3cm tear on warp side"
      → Machine: "Loom A"
      → Analista: "Juan Pérez"
      → Timestamp: "2026-05-31 14:23:45 UTC"

3. Jefe QA reviews inspection details
   → Studies photo (zoomed in on defect)
   → Reads comment
   → Forms decision

4. Jefe QA clicks "Approve" button
   → Optional notes field shown: "Add notes (optional)"
   → Jefe QA types notes: "Quality acceptable, proceed"
   → Clicks "Confirm Approve"

5. System submits approval
   → POST /api/approvals/approve
   → Payload: { inspection_id, jefe_qa_id, notes }
   → Backend returns: approval_id, timestamp
   → Toast message: "✅ Inspection approved"
   → Modal closes, table refreshes
   → Approval disappears from "Pending" table

6. Jefe QA checks approval history
   → Navigates to "Approval History" tab
   → New approval visible at top: "APPROVED | 2026-05-31 14:35"
   → No edit/delete buttons (immutable)

7. Jefe QA reviews next pending inspection
   → Flow returns to step 2 (select next)
```

### **ALTERNATIVE FLOW A: Reject Inspection**

```
4a. Jefe QA reviews photo and decides to REJECT
    → Clicks "Reject" button (instead of "Approve")
    → Rejection reason field appears (required)
    → Field label: "Reason for rejection (10-500 chars)"
    → Jefe QA types: "Tear exceeds tolerance limit of 2cm"
    → Character count: 50/500 ✅
    → Optional notes: "Recommend re-spinning fabric"

5a. System submits rejection
    → POST /api/approvals/reject
    → Payload: { inspection_id, jefe_qa_id, rejection_reason, notes }
    → Toast: "✅ Inspection rejected"
    → Approval record created with decision = REJECTED
```

### **ALTERNATIVE FLOW B: Inspection Already Approved**

```
2b. Jefe QA selects inspection
    → Detail modal starts loading
    → API response error: "This inspection was already approved"
    → Message shown: "❌ Already approved by Maria García on 2026-05-31 14:31"
    → Show existing approval details (read-only)
    → Modal shows previous approval decision
    → Buttons hidden: "Approve" and "Reject" disabled
    → "Close" button only action available
```

### **ALTERNATIVE FLOW C: Photo Fails to Load**

```
2c. Detail modal opens
    → Photo image fails to load (404 error)
    → Placeholder shown: "📸 Photo not available"
    → Error message: "Unable to load photo. Check connection or contact admin."
    → Inspection details still visible (comment, metadata)
    → Jefe QA can still approve/reject based on comment
```

### **STATE DIAGRAM**

```
PENDING
  ↓
[Jefe QA Reviews]
  ├─→ Approve → APPROVED (immutable)
  └─→ Reject → REJECTED (immutable)
       ↳ (requires rejection_reason)
```

### **TIMING**

| Step | Duration | Notes |
|------|----------|-------|
| Load pending list | 1-2 sec | API query |
| Open detail modal | 1-2 sec | Photo loads |
| Review inspection | 10-30 sec | User action |
| Submit approval | 2-3 sec | API POST |
| **Total** | **15-40 sec per inspection** | Variable (review time) |

---

## ⚙️ UC3: MANAGE MASTERS DATA (Admin)

**Actor**: Admin (system administrator)  
**Goal**: Create/edit/inactivate master data, or bulk import from CSV  
**Preconditions**: User authenticated as ADMIN  
**Success Criteria**: Master records created/updated, data available in dropdowns

### **MAIN FLOW: Create New Defect**

```
1. Admin opens Config page
   → Requires ADMIN role
   → Page shows 3 tabs: Defects | Machines | Fabrics
   → Defects tab selected
   → Table shows 25 active defects

2. Admin clicks "Create Defect" button
   → Modal opens with form:
      - Defect ID (text, required): [           ]
      - Name (text, required): [                ]
      - Category (dropdown, required): [Physical, Visible, Mechanical]
      - Severity (dropdown, optional): [LOW, MEDIUM, HIGH]
      - Status (radio, default ACTIVE): ○ ACTIVE ◉ INACTIVE

3. Admin fills form
   → Defect ID: "DEF_026"
   → Name: "Color Fading"
   → Category: "Visible"
   → Severity: "MEDIUM"
   → Status: ACTIVE (default)

4. Admin clicks "Save"
   → Form validated:
      - Defect ID required ✅
      - Name required ✅
      - Category required ✅
   → POST /api/masters/defects
   → Backend checks: Defect ID not duplicate
   → Returns: defect_id, created_at
   → Toast: "✅ Defect created: DEF_026"
   → Modal closes, table refreshes

5. New defect visible in table
   → Table shows 26 defects now
   → DEF_026 at bottom with timestamp
   → Dropdown in Inspection page updated

6. Admin sees new defect in dropdown
   → [Later] Analista opens Inspection page
   → Defect dropdown now includes "Color Fading"
   → Available for selection
```

### **ALTERNATIVE FLOW B: Bulk Import from CSV**

```
1. Admin opens Config page → Defects tab

2. Admin clicks "Import CSV" button
   → File upload dialog opens
   → Accepts: .csv files
   → Admin selects file: "defects_2026.csv"
   → File format:
      defect_id,name,category,severity
      DEF_027,Shrinkage,Physical,HIGH
      DEF_028,Pilling,Visible,MEDIUM
      DEF_027,Shrinkage,Physical,HIGH   [duplicate!]

3. System parses and validates CSV
   → Validates all rows:
      - Row 1: DEF_027 ✅
      - Row 2: DEF_028 ✅
      - Row 3: DEF_027 ⚠️ (duplicate in file)
   → Validation report:
      Total rows: 3
      Valid: 2
      Invalid: 0
      Duplicates: 1
   → Message: "Ready to import 2 defects (1 duplicate will be skipped)"

4. Admin confirms import
   → Clicks "Import" button
   → POST /api/masters/import-csv
   → Payload: { data: [...], type: 'defects' }

5. Backend processes import
   → Inserts 2 new defects
   → Skips 1 duplicate (DEF_027 already exists)
   → Returns: { created: 2, skipped: 1, total: 3 }

6. System shows success
   → Toast: "✅ Import complete: 2 created, 1 skipped (duplicate)"
   → Table refreshes, shows 27 defects now
   → Dropdowns updated in Inspection page
```

### **ALTERNATIVE FLOW C: Edit Existing Master**

```
1. Admin clicks "Edit" button on defect row (DEF_001)
   → Modal opens with form pre-filled:
      - Defect ID: "DEF_001" (read-only, cannot change)
      - Name: "Tear" (editable)
      - Category: "Physical" (editable)
      - Severity: "HIGH" (editable)

2. Admin updates Name
   → Changes: "Tear" → "Large Tear (>2cm)"

3. Admin clicks "Save"
   → PUT /api/masters/defects/DEF_001
   → Payload: { name: "Large Tear (>2cm)", ... }
   → Backend updates record
   → Toast: "✅ Defect updated: DEF_001"

4. Change reflected immediately
   → Dropdown shows: "Large Tear (>2cm)"
   → Analistas see new name in inspection page
```

### **ERROR MATRIX**

| Error | Cause | Shown To | Fix |
|-------|-------|----------|-----|
| Duplicate ID | Already exists | Admin | Use different ID |
| Missing required field | Empty field | Admin | Fill field |
| Invalid category | Not in enum | Admin | Select from list |
| CSV parse error | Bad format | Admin | Fix CSV structure |
| CSV row invalid | Missing field | Admin | Check row N, add field |

---

## 🔄 UC4: OFFLINE SYNC (Automatic + Manual)

**Actor**: System (Service Worker) + Analista (manual trigger)  
**Goal**: Synchronize pending inspections to backend, with automatic retries and exponential backoff  
**Preconditions**: One or more inspections in IndexedDB with sync_status = PENDING  
**Success Criteria**: All inspections synced to API (sync_status = SYNCED) or marked unrecoverable (SYNC_FAILED)

### **AUTOMATIC SYNC FLOW** (Background)

```
0. [Precondition] Analista saved inspection offline
   → IndexedDB: { inspection_id, lote_id, ..., sync_status: "PENDING" }
   → Service Worker registered and active

1. Service Worker detects online state
   → Network.onOnline event fired
   → Service Worker: "Network status changed to ONLINE"

2. Service Worker checks IndexedDB for pending items
   → Query: SELECT * FROM inspections WHERE sync_status = "PENDING"
   → Result: 1 inspection found with ID "550e8400-e29b-41d4-a716-446655440000"
   → localStorage update: syncQueue = [550e8400...]

3. Service Worker starts sync loop
   → For each pending inspection:
      → Attempt 1 (immediate):
         POST /api/inspections/sync-batch
         Payload: [{ inspection_id, lote_id, ... }]
         Response: 201 Created ✅
         Update IndexedDB: sync_status = SYNCED
         Remove from pending queue
         Toast (if app open): "✅ Inspection synced"

4. [If sync succeeds]
   → Inspection marked SYNCED
   → IndexedDB updated
   → Service Worker checks for more pending items
   → All done ✅

5. [If sync FAILS - simulate network timeout on first attempt]
   → POST times out after 30 seconds
   → Error caught: TimeoutError
   → IndexedDB update: 
      - sync_status = "SYNC_FAILED"
      - retry_count = 1
      - last_error = "TimeoutError"
      - next_retry = now + 5000ms
   → Service Worker schedules retry

6. [5 seconds later] Retry attempt 2
   → POST /api/inspections/sync-batch again
   → Response: 409 Conflict (inspection_id already exists from partial write)
   → But idempotency check: inspection_id is UNIQUE key
   → Backend skips duplicate, returns 201 ✅
   → Update IndexedDB: sync_status = SYNCED
   → Sync complete!

7. Service Worker continues checking
   → Every 30 seconds: Check for new pending items
   → If offline: Stop checking, wait for online event
   → If online: Sync any new pending items
```

### **MANUAL RETRY FLOW** (User-Triggered)

```
1. Analista opens app
   → Offline indicator shows: "🔴 OFFLINE (1 failed, 2 queued)"
   → Sync status panel visible with failed items
   → "Retry Now" button displayed

2. [Network restored but auto-sync failed]
   → Analista clicks "Retry Now" button
   → Manual sync triggered immediately (bypass backoff)

3. Service Worker performs urgent retry
   → Attempt 1 (attempt count continues from 1):
      POST /api/inspections/sync-batch
      [Failed inspection retry]
      Response: 201 ✅
      Update: sync_status = SYNCED
      Toast: "✅ Failed inspection synced"

4. [If still fails after retry]
   → Analista sees updated error message
   → "Still failing. Check your connection or contact support."
   → Retry button remains available
```

### **EXPONENTIAL BACKOFF TABLE**

| Attempt # | Delay | Total Wait | Example Scenario |
|-----------|-------|-----------|------------------|
| 1 | 5s | 5s | App closed, network brief blip |
| 2 | 10s | 15s | Backend busy, slow response |
| 3 | 30s | 45s | Intermittent connectivity |
| 4 | 60s | 105s | Server maintenance window |
| 5 | 60s | 165s | Persistent outage |
| **After 5** | ❌ Failed | 165s total | Manual retry or contact admin |

### **STATE DIAGRAM: Sync Status Lifecycle**

```
IndexedDB Saved
  ↓
sync_status = PENDING
  ↓
[Auto-Sync Starts] (if online) OR [Manual Retry]
  ├─→ Attempt 1 (0s delay)
  │    ├─ Success → SYNCED ✅ (done)
  │    └─ Fail → SYNC_FAILED, retry_count=1
  │
  ├─→ Attempt 2 (wait 5s)
  │    ├─ Success → SYNCED ✅ (done)
  │    └─ Fail → retry_count=2
  │
  ├─→ Attempt 3 (wait 10s)
  │    ├─ Success → SYNCED ✅ (done)
  │    └─ Fail → retry_count=3
  │
  ├─→ Attempt 4 (wait 30s)
  │    ├─ Success → SYNCED ✅ (done)
  │    └─ Fail → retry_count=4
  │
  └─→ Attempt 5 (wait 60s)
       ├─ Success → SYNCED ✅ (done)
       └─ Fail → SYNC_FAILED, exhausted
                 [Manual retry available]
```

### **ERROR SCENARIOS**

| Scenario | Trigger | Behavior |
|----------|---------|----------|
| Network timeout | POST hangs >30s | Retry with backoff |
| 500 Server error | Backend down | Retry with backoff |
| 409 Conflict | Duplicate inspection_id | Idempotent: Treat as success |
| 400 Bad request | Invalid payload | Don't retry (data error) |
| 403 Forbidden | Token expired | Refresh token, retry |
| 5 attempts exhausted | Persistent failure | Mark SYNC_FAILED, await manual retry |

### **PERFORMANCE**

| Scenario | Time | Notes |
|----------|------|-------|
| Immediate sync (online) | 2-5 sec | Fast path |
| Retry after 1 failure | 5 + 2-5 sec = 7-10 sec | After first backoff |
| All 5 attempts | ~165 sec (2.75 min) | Worst case |
| 100 inspections batch | ~5 sec | Parallel processing |

### **USER FEEDBACK DURING SYNC**

```
// Header indicator
ONLINE: 📡 Online (Last synced: 2 minutes ago)
OFFLINE: 🔴 Offline (3 queued, 1 failed)
SYNCING: 🔄 Syncing 45% complete

// Sync status panel (if offline or syncing)
┌─────────────────────────────┐
│ Offline Queue & Sync Status │
├─────────────────────────────┤
│ ✅ 5 synced                │
│ 🔄 2 pending               │
│ ❌ 1 failed                │
│                             │
│ [Retry Now] button         │
└─────────────────────────────┘

// Toast notifications
✅ "Inspection synced"
⚠️ "Sync failed, will retry in 5 seconds"
❌ "Sync exhausted after 5 attempts"
🔄 "Syncing 3 inspections..."
```

---

## 📊 PROCESS FLOW SUMMARY

| UC # | Actor | Duration | Complexity | Dependencies |
|------|-------|----------|------------|--------------|
| **UC1** | Analista | 10-20 sec | High | Photo validation, offline queue |
| **UC2** | Jefe QA | 15-40 sec | Medium | Backend API approval |
| **UC3** | Admin | 2-10 sec | Medium | CSV parsing, deduplication |
| **UC4** | System | 2-165 sec | High | Network detection, IndexedDB, exponential backoff |

---

## 🔗 CROSS-PROCESS INTERACTIONS

```
UC1 (Save Inspection)
  ↓ [IF OFFLINE]
  ↓
UC4 (Offline Sync)
  ↓ [When online]
  ↓
[Inspection appears in backend]
  ↓
UC2 (Jefe QA reviews)
  ↓
[Approval created]
```

---

**Status**: ✅ BUSINESS LOGIC MODEL DEFINED  
**Unit Completion**: Activity 1 (Functional Design) COMPLETE for FRONTEND WEB
