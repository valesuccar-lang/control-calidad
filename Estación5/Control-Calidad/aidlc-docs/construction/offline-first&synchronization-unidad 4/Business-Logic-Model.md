# Business Logic Model — Unit 4 (Offline-First & Synchronization)

**Date**: 2026-06-01  
**Domain**: Offline-First Synchronization for Textile Quality Control  
**Scope**: 4 primary use cases with detailed workflows, decision trees, and state transitions  

---

## 🎯 PRIMARY USE CASES

### UC-001: Inspector Works Offline (Read Masters, Cannot Write)

**Actor**: Inspector (field worker)  
**Preconditions**:
- App installed and authenticated
- Masters (Defects, Machines, Fabrics) cached from previous sync
- Network is offline or unreliable
- Inspector has cached inspection history

**Main Flow**:
1. Inspector opens app
2. System detects: `NetworkStatus.is_online = false`
3. App displays: "Offline mode - viewing cached data" (in status bar)
4. Inspector browses and searches cached masters (Defect types, machines, fabrics)
5. Inspector views cached inspection history (read-only)
6. Inspector attempts to create new inspection → **App shows modal**: "Connect to sync before submitting"
7. Inspector cannot proceed (offline mode is read-only)
8. Inspector closes app and waits for connection

**Postconditions**:
- No data created or modified (read-only)
- Cache remains intact (no changes)
- Inspector knows next action: "Connect to sync"

**Variations**:
- **V-1**: Inspector has no cached masters
  - System shows: "No data cached. Please connect to sync first."
  - Inspector cannot work (must go online)
  
- **V-2**: Inspector accidentally opens offline mode
  - Status bar clearly shows: "📵 OFFLINE"
  - Color: Red/orange for visibility
  - Tap: Opens info modal explaining limitations

**Business Rules Involved**: BR-001 to BR-004, BR-021 to BR-030, BR-041 to BR-045

---

### UC-002: Network Restored → Automatic Sync

**Actor**: System (automatic, no user action)  
**Preconditions**:
- Network was offline
- Sync queue has pending operations (or never synced)
- Masters cache is stale (> 1 hour old)

**Main Flow**:
1. Network restored: `NetworkStatus.is_online = true`
2. System triggers: `SyncService.startSync()`
3. System determines network quality (EXCELLENT/GOOD/POOR)
4. System refreshes masters cache (background task, non-blocking)
5. Master cache refresh succeeds/fails (continues regardless)
6. System processes sync queue:
   - Batch 1: 10 items (if GOOD network) or 1 item (if POOR)
   - For each item:
     - Attempt POST to `/api/v1/sync/item` with operation data
     - Response: 200 (success), 409 (conflict), 4xx/5xx (error)
7. Update SyncQueue item status based on response:
   - 200 → Mark as SYNCED ✅
   - 409 → Mark as CONFLICT, move to ConflictQueue
   - 5xx → Mark as FAILED, schedule retry
   - 4xx (non-422) → Mark as FAILED (non-recoverable)
   - 422 → Mark as FAILED with validation error details
8. Continue processing remaining items
9. Sync completes: Show UI update "All synced ✓" (auto-dismiss in 3s)

**Postconditions**:
- Sync queue processed (most items SYNCED)
- Conflicts displayed in UI (if any)
- Dead letter queue updated (if max retries exceeded)
- Masters cache refreshed (if successful)
- UI status bar shows: "✓ Synced" or "⚠️ 2 conflicts"

**Timing**:
- Master refresh: < 5 seconds (background)
- Sync item: < 1 second each
- Total: < 30 seconds for 10-item queue (GOOD network)

**Network Quality Impact**:
- EXCELLENT (5G): Batch 20 items, < 2 seconds total
- GOOD (4G, WiFi): Batch 10 items, < 3 seconds total
- POOR (3G, Edge): Batch 1 item, < 5 seconds each
- Timeout: If any item > 10 seconds, mark FAILED

**Business Rules Involved**: BR-004, BR-031 to BR-040, BR-041 to BR-048, PT-001 to PT-005

---

### UC-003: Conflict Detected During Sync

**Actor**: System (during sync) + Inspector (resolution)  
**Preconditions**:
- Sync in progress
- Operation sync returns HTTP 409 (Conflict)
- Version mismatch: Our version ≠ Server version

**Main Flow**:

**Phase 1: Detection (automatic)**
1. System sends: `PATCH /api/v1/inspections/INS-123` with version=1
2. Server responds: `409 Conflict` + `{version: 3, ...server_data}`
3. System marks: SyncQueueItem.status = CONFLICT
4. System logs conflict details:
   - our_version: 1
   - server_version: 3
   - our_data: {description: "...", status: "..."}
   - server_data: {description: "...", status: "..."}
5. System pauses: Stops processing this item (retries later)

**Phase 2: Intelligent Analysis (automatic)**
1. System performs 3-way merge analysis:
   - Compare: our_data, base_data (cached when we fetched), server_data
   - Changed fields (ours): [description, status]
   - Changed fields (server): [location, typical_machine_id]
   - Overlapping fields: NONE (different fields changed)
2. System determines: Non-conflicting changes → **Can auto-resolve**
3. System generates: Merged version = server_data + our changes
4. System retries sync: `PATCH /api/v1/inspections/INS-123` with merged data + version=3

**Phase 2B: If Overlapping Changes** (true conflict):
1. System determines: Same field changed both sides → **Cannot auto-resolve**
2. System shows modal: **Conflict Resolution Dialog**
   - Title: "Conflict detected for Inspection #123"
   - Your version: (left column, highlighted changes)
   - Server version: (right column, highlighted changes)
   - Overlapping field: "description" (shown in red both sides)
3. Inspector chooses:
   - Option A: "Keep my changes" (overwrite server)
   - Option B: "Use server version" (discard local)
   - Option C: "Manual merge" (edit and combine)
4. Inspector selects option → Move to Phase 3

**Phase 3: Resolution (automatic or manual)**
- **If auto-resolved (Phase 2)**: Already done, move to Phase 4
- **If manual resolved (Phase 2B)**:
  - Apply: Selected resolution strategy
  - Show: "Conflict resolved, retrying sync..."
  - Retry: Send resolved data to server
  - If success: Move to Phase 4
  - If fails again: Treat as new error (backoff retry)

**Phase 4: Completion**
1. Mark: SyncQueueItem.status = RESOLVED
2. Mark: SyncQueueItem.status = SYNCING (automatic retry)
3. Retry succeeds: SyncQueueItem.status = SYNCED ✅
4. Log: "Conflict resolved via [AUTO-MERGE | KEEP-LOCAL | USE-SERVER]"
5. Update UI: Remove conflict indicator, show success

**Timeout Handling**:
- If conflict unresolved after 5 minutes: Auto-close modal
- Default action: "Use server version" (prevents blocking)
- Log: "Conflict resolution timeout, applied default action"

**24-Hour Expiration**:
- If conflict not resolved within 24 hours:
  - Move to DEAD_LETTER
  - Notify: Inspector gets notification "Sync issue requires attention"
  - Support: Review dead letter queue

**Business Rules Involved**: BR-011 to BR-020, VR-005 (3-way merge)

---

### UC-004: Sync Fails → Exponential Backoff Retry

**Actor**: System (automatic retry)  
**Preconditions**:
- Sync operation failed (FAILED state)
- Network error, server error, or timeout
- Not a permanent failure (non-400 client error)

**Main Flow**:

**Phase 1: Failure Classification**
1. Sync attempt returns error response or timeout
2. System classifies:
   - **Network error** (timeout, no internet): Retryable
   - **Server error** (500, 503): Retryable
   - **Validation error** (422): Retryable (show validation details)
   - **Not found** (404): Non-retryable → DEAD_LETTER
   - **Auth error** (401, 403): Non-retryable → DEAD_LETTER
3. If retryable: Mark as FAILED, increment retry_count
4. If non-retryable: Mark as FAILED, move to DEAD_LETTER (no retry)

**Phase 2: Exponential Backoff Schedule**
1. Calculate next retry time:
   ```
   retry_count = 0 → backoff = 5 seconds
   retry_count = 1 → backoff = 10 seconds
   retry_count = 2 → backoff = 30 seconds
   retry_count = 3 → backoff = 60 seconds
   retry_count = 4 → backoff = 60 seconds
   ```
2. Schedule: `next_retry_at = now + backoff`
3. Move to: RETRY_PENDING state
4. Log: "Retry scheduled in 5s (attempt 1/5)"

**Phase 3: Automatic Retry**
1. Wait: Until next_retry_at
2. System checks: Is network available? (is_online == true)
3. If offline: Wait for network, then retry
4. If online: Attempt sync again
5. If succeeds: Move to SYNCED ✅
6. If fails again: Go back to Phase 1 (increment retry_count)

**Phase 4: Max Retries Exceeded**
1. If retry_count >= 5 after all attempts:
   - Move to: DEAD_LETTER
   - Status: "FAILED (max retries)"
   - Log: "Max retries exceeded for operation"
   - Notify: Support team (daily report)
   - Inspector: Shows error "Sync issue - contact support"

**UI Feedback**:
- Status bar shows: "⟳ Syncing 1/10" (during attempt)
- Status bar shows: "⚠️ Retry in 23s" (during backoff)
- Tappable status: Shows queue with estimated retry times
- No blocking: Inspector can work while retrying

**Cancellation**:
- Inspector can manually clear sync queue (last resort)
- Confirmation: "This will discard all pending operations. Continue?"
- After clear: Fresh start, no more retries

**Business Rules Involved**: BR-006 to BR-010, BR-034 to BR-037

---

## 📊 STATE MACHINE DIAGRAM

```
┌─────────────────────────────────────────────────────────────┐
│                    SyncQueue Item Lifecycle                 │
└─────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │   PENDING    │ ← User enqueues operation
                    │ retry_count=0│
                    └──────┬───────┘
                           │ startSync()
                           ▼
                    ┌──────────────┐
                    │   SYNCING    │ ← Attempt POST to server
                    │  timeout=10s │
                    └──────┬───────┘
                    ┌──────┴──────────────────────────┐
                    │                                 │
              Response: 200                    Response: 409
              ✅ Success                       ⚠️ Conflict
                    │                                 │
                    ▼                                 ▼
            ┌──────────────┐                ┌──────────────┐
            │    SYNCED    │                │  CONFLICT    │
            │ ✓ Done       │                │ Analyze      │
            └──────────────┘                └──────┬───────┘
                    ▲                              │
                    │                   Can auto-resolve?
                    │                              │
                    │    ┌─────────────────────────┴────────┐
                    │    │ YES                  NO           │
                    │    ▼                      ▼            │
                    │  Apply merge      Show resolution     │
                    │  Retry → 200        dialog to user    │
                    │                    Inspector chooses  │
                    │                   (timeout: 5 min)    │
                    │                         │             │
                    │                   Inspector resolved   │
                    │                         │             │
                    │    ┌────────────────────┘             │
                    │    ▼                                   │
                    │  Apply resolution                     │
                    │  Retry → 200                          │
                    │    │                                   │
        Other response   │   Other response                 │
        4xx (400, 403)   │   4xx/5xx                        │
        401 (auth)       │   (network, server, validation)  │
              │          │   │                              │
              └──────┬───┼───┘                              │
                     ▼   ▼                                  │
             ┌──────────────┐                              │
             │   FAILED     │                              │
             │ Non-retry?   │◄─────────────────────────────┘
             │ (401, 403,   │
             │  404, etc.)  │
             └──────┬───┬───┘
                    │   │ Retryable?
            ❌ No   │   │ Yes
                    │   │
         Dead Letter │   ├─► ┌──────────────┐
                    ▼   │    │RETRY_PENDING │
             ┌───────────┐   │ next_retry_at│
             │DEAD_LETTER│   │ retry_count++│
             │ Requires  │   └──────┬───────┘
             │ support   │          │
             │           │      Wait + Check network
             └───────────┘          │
                                    ▼ Online?
                          ┌─────────────────────┐
                          │  Retry SYNCING      │
                          │  (Go back to top)   │
                          │  Max 5 retries      │
                          └─────────────────────┘
```

---

## 🔄 SYNC ORCHESTRATION WORKFLOW

```
Sync Triggered (Network Online)
    │
    ├─► Check: Queue empty?
    │   ├─ YES → Done, exit
    │   └─ NO → Continue
    │
    ├─► Measure: Network quality (latency, packet loss)
    │   ├─ EXCELLENT → Batch size = 20
    │   ├─ GOOD → Batch size = 10
    │   ├─ POOR → Batch size = 1
    │   └─ OFFLINE → Stop, re-check later
    │
    ├─► Refresh: Master data cache (background, non-blocking)
    │   ├─ Success → Update cache_version
    │   ├─ Timeout (> 5s) → Skip and continue
    │   └─ Failure → Ignore and continue (use stale cache)
    │
    ├─► Process: Sync queue items (FIFO, with batching)
    │   │
    │   ├─► Item 1: PENDING → SYNCING
    │   │   ├─ POST /sync/item with payload
    │   │   ├─ Wait (timeout 10s)
    │   │   └─ Handle response:
    │   │       ├─ 200 → SYNCED ✅
    │   │       ├─ 409 → CONFLICT ⚠️
    │   │       ├─ 422 → FAILED (show validation error)
    │   │       ├─ 5xx → FAILED (schedule retry)
    │   │       └─ 4xx → FAILED (dead letter)
    │   │
    │   ├─► Item 2: PENDING → SYNCING → ...
    │   ├─► Item 3: PENDING → SYNCING → ...
    │   ...
    │   └─► Item N: Process until queue empty or batch size reached
    │
    ├─► Post-process: Handle conflicts
    │   ├─ For each CONFLICT:
    │   │   ├─ Analyze: 3-way merge
    │   │   ├─ If auto-resolvable: Apply merge, set to SYNCING (auto-retry)
    │   │   └─ If not: Show UI dialog, wait for user resolution
    │   │
    │   └─ For each FAILED:
    │       ├─ If retryable (5xx, timeout, network):
    │       │   └─ Schedule retry: next_retry_at = now + backoff[retry_count]
    │       └─ If not retryable (401, 403, 404):
    │           └─ Move to dead letter queue
    │
    └─► Notify: Update UI status bar
        ├─ "✓ Synced" (all done)
        ├─ "⟳ Syncing 5/10" (still processing)
        ├─ "⚠️ 2 conflicts" (pending resolution)
        ├─ "⚠️ 1 failed (retry in 23s)" (backoff)
        └─ "❌ 1 error (contact support)" (dead letter)
```

---

## 🎯 USE CASE: INSPECTOR WORKFLOWS

### UC-2A: Inspector in Field (Online)
```
1. Inspector arrives at factory (WiFi available)
2. App auto-syncs: Masters refresh + queue processes
3. Inspector can: View masters, create inspection, submit inspection
4. Submission syncs immediately (high-priority)
5. If conflict: Show modal, inspector resolves
6. Result: Inspection synced to server
```

### UC-2B: Inspector in Field (Offline)
```
1. Inspector has no WiFi (field area, 3G only)
2. App detects: POOR network quality
3. Behavior:
   - Masters cached from earlier (1 hour ago)
   - Can view inspection history (cached)
   - Cannot create new inspections
4. Message: "Offline mode - connect to submit"
5. When WiFi available: Auto-sync masters + queue
```

### UC-2C: Inspector at End of Day (Multiple Pending)
```
1. Inspector returns to office (WiFi available)
2. Sync queue has 10 pending items (created throughout day)
3. App auto-syncs: Processes 10 items in batch (< 3 seconds)
4. Result: All synced or conflicts shown
5. Conflicts: Inspector resolves (2 items had conflicts, 8 synced)
6. Final: 10/10 synced after resolution
```

---

## 🔀 DECISION TREES

### DT-001: Should Operation Be Queued?
```
Operation Requested (Create/Update/Delete)
    │
    ├─ Network.is_online = true?
    │  ├─ YES → Sync immediately (high-priority)
    │  │        └─ Success → Done
    │  │        └─ Failure → Queue + retry
    │  │
    │  └─ NO → Offline mode
    │         ├─ Operation is CREATE/WRITE → Block with error "Connect required"
    │         └─ Operation is READ → Allowed (use cache)
```

### DT-002: Classify Sync Error
```
Sync Response Received
    │
    ├─ Timeout (no response after 10s) → Network error → Retry
    ├─ 200 OK → Success → Mark SYNCED
    ├─ 409 Conflict → Analyze + Resolve
    │  ├─ 3-way merge possible? → Auto-merge + retry
    │  └─ True conflict? → Show dialog, wait for user
    ├─ 422 Validation → Validation error → Show error, allow manual retry
    ├─ 500-503 Server → Server error → Retry with backoff
    ├─ 400, 404, etc. → Client error → Dead letter (no retry)
    ├─ 401, 403 Auth → Auth error → Dead letter (no retry, prompt re-login)
    └─ Network unreachable → Network error → Retry with backoff
```

### DT-003: Should Retry?
```
Sync Failed
    │
    ├─ Is Retryable Error?
    │  ├─ YES (network, server, 422 validation) → Continue
    │  └─ NO (401, 403, 404) → Move to dead letter, exit
    │
    ├─ Retry Count < 5?
    │  ├─ YES → Schedule retry
    │  │        ├─ backoff = [5s, 10s, 30s, 60s, 60s][retry_count]
    │  │        ├─ next_retry_at = now + backoff
    │  │        ├─ Move to RETRY_PENDING
    │  │        └─ Wait for timer or network change
    │  │
    │  └─ NO (5 retries done) → Move to dead letter, notify support
```

---

## 📋 CONFLICT RESOLUTION MATRIX

```
┌──────────────────┬──────────────────┬────────────────┬──────────────┐
│ Conflict Type    │ Detection        │ Auto-Resolve?  │ Action       │
├──────────────────┼──────────────────┼────────────────┼──────────────┤
│ Version Mismatch │ 409 response     │ 3-way merge    │ Analyze      │
│                  │ our_v ≠ server_v │ if possible    │ changes      │
├──────────────────┼──────────────────┼────────────────┼──────────────┤
│ Non-overlapping  │ Our field A +    │ YES ✅         │ Auto-merge   │
│ changes          │ Server field B   │ Combine both   │ + retry      │
│                  │ (different)      │ changes        │              │
├──────────────────┼──────────────────┼────────────────┼──────────────┤
│ Overlapping      │ Both changed     │ NO ❌          │ Show modal   │
│ changes          │ same field       │ True conflict  │ to inspector │
│                  │ (e.g., desc)     │ requires user  │              │
├──────────────────┼──────────────────┼────────────────┼──────────────┤
│ Deleted remote   │ 404 Not Found    │ Depends        │ Ask inspector│
│ but local edited │ Entity gone      │ Delete was     │ Keep/Discard │
│                  │                  │ intentional?   │              │
├──────────────────┼──────────────────┼────────────────┼──────────────┤
│ Concurrent       │ Two deletes of   │ Expected       │ Accept 404   │
│ deletes          │ same entity      │ behavior       │ (entity gone)│
│                  │ (second gets 404)│ No error       │              │
└──────────────────┴──────────────────┴────────────────┴──────────────┘
```

---

## ⏱️ TIMING SPECIFICATIONS

### Sync Operation Latencies
```
Network Quality: EXCELLENT (5G, WiFi < 50ms latency)
├─ Operation: 1 inspection
├─ Time breakdown:
│  ├─ Network request: ~300ms
│  ├─ Server processing: ~400ms
│  ├─ Network response: ~300ms
│  ├─ IndexedDB update: ~50ms
│  └─ UI update: ~50ms
├─ Total: ~1.1 seconds
└─ Target: < 3 seconds ✅

Network Quality: GOOD (4G, WiFi 50-150ms latency)
├─ Operation: 1 inspection + 10 items batch
├─ Time breakdown:
│  ├─ Network request: ~500ms
│  ├─ Server processing: ~500ms
│  ├─ Network response: ~500ms
│  ├─ Batch items (10 × 100ms): ~1000ms
│  ├─ IndexedDB batch update: ~200ms
│  └─ UI update: ~100ms
├─ Total: ~2.8 seconds
└─ Target: < 3 seconds ✅

Network Quality: POOR (3G, Edge 300+ ms latency)
├─ Operation: 1 inspection (serialized, no batching)
├─ Time breakdown:
│  ├─ Network request: ~1000ms (high latency)
│  ├─ Server processing: ~500ms
│  ├─ Network response: ~1000ms
│  ├─ IndexedDB update: ~50ms
│  └─ UI update: ~50ms
├─ Total: ~2.6 seconds per item
└─ 10 items: ~26 seconds (serialized)
```

### Retry Backoff Schedule
```
Attempt 1 (immediate): Now
├─ Fails → Schedule retry

Attempt 2: Now + 5 seconds
├─ Fails → Schedule retry

Attempt 3: Previous + 10 seconds (5s + 10s = 15s from start)
├─ Fails → Schedule retry

Attempt 4: Previous + 30 seconds (15s + 30s = 45s from start)
├─ Fails → Schedule retry

Attempt 5: Previous + 60 seconds (45s + 60s = 105s from start)
├─ Fails → Schedule retry

Attempt 6: Previous + 60 seconds (105s + 60s = 165s from start)
├─ Fails → Move to dead letter

Total time for 5 retries: ~2.75 minutes (165 seconds)
```

---

## 🎪 SEQUENCE DIAGRAMS

### Diagram 1: Normal Sync (Happy Path)
```
Inspector     App           Service Worker    API Server
    │          │                  │                │
    │ 1. Online│                  │                │
    │ detected │                  │                │
    │◄─────────│                  │                │
    │          │ 2. startSync()   │                │
    │          │─────────────────►│                │
    │          │                  │ 3. POST /sync  │
    │          │                  │───────────────►│
    │          │                  │ (Inspection)   │
    │          │                  │                │ 4. Validate
    │          │                  │                │ process
    │          │                  │                │
    │          │                  │◄───────────────│
    │          │                  │ 200 OK + data  │
    │          │ 5. Item SYNCED   │                │
    │          │◄─────────────────│                │
    │          │                  │                │
    │ 6. Update│                  │                │
    │ status ✓ │                  │                │
    │◄─────────│                  │                │
    │          │ 7. Continue queue│                │
    │          │ (next item)      │                │
    │          │─────────────────►│                │
    │          │ ...              │                │
    │          │ (repeat until queue empty)        │
    │          │                  │                │
    │ 8. "Synced"                 │                │
    │ notification                │                │
    │◄─────────────────────────────────────────────│
```

### Diagram 2: Conflict Resolution
```
Inspector     App           Service Worker    API Server
    │          │                  │                │
    │ 1. Sync  │                  │                │
    │ operation│                  │                │
    │◄─────────│                  │                │
    │          │ 2. POST /sync    │                │
    │          │─────────────────►│                │
    │          │                  │ 3. PATCH /item│
    │          │                  │───────────────►│
    │          │                  │ (version: 1)   │
    │          │                  │                │
    │          │                  │◄───────────────│
    │          │                  │ 409 Conflict   │
    │          │                  │ (version: 3)   │
    │ 4. Analyze
    │ 3-way merge
    │          │                  │                │
    │ 5. Overlapping changes?     │                │
    │ YES → Show modal            │                │
    │          │                  │                │
    │ 6. [Modal: Choose resolution]              │
    │ Options: Keep Local / Use Server / Manual  │
    │          │                  │                │
    │ 7. Choose: "Keep Local"     │                │
    │──────────►                  │                │
    │          │ 8. Apply: Merge data            │
    │          │ with server version             │
    │          │ Retry: PATCH with merged data + v3
    │          │─────────────────►│                │
    │          │                  │ 9. PATCH /item│
    │          │                  │ (version: 3)  │
    │          │                  │───────────────►│
    │          │                  │                │ 10. Validate
    │          │                  │                │
    │          │                  │◄───────────────│
    │          │                  │ 200 OK         │
    │ 11. SYNCED│                  │                │
    │◄──────────│                  │                │
```

### Diagram 3: Exponential Backoff Retry
```
Time →

Attempt 1 (Immediate)
├─ Request sent
├─ Response: 500 Server Error
├─ Status: FAILED
└─ Reason: Retryable (server error)

Backoff 1: 5 seconds
├─ [RETRY_PENDING state]
├─ Wait...
└─ [5s elapsed]

Attempt 2 (at 5s)
├─ Request sent
├─ Response: Timeout (10s)
├─ Status: FAILED
└─ Reason: Retryable (network)

Backoff 2: 10 seconds
├─ [RETRY_PENDING state]
├─ Wait...
└─ [10s elapsed]

Attempt 3 (at 15s)
├─ Request sent
├─ Response: 500 Server Error
├─ Status: FAILED
└─ Reason: Retryable

Backoff 3: 30 seconds
├─ [RETRY_PENDING state]
├─ Wait...
└─ [30s elapsed]

Attempt 4 (at 45s)
├─ Request sent
├─ Response: 503 Service Unavailable
├─ Status: FAILED
└─ Reason: Retryable

Backoff 4: 60 seconds
├─ [RETRY_PENDING state]
├─ Wait...
└─ [60s elapsed]

Attempt 5 (at 105s)
├─ Request sent
├─ Response: 200 OK ✅
├─ Status: SYNCED
└─ Success: Took ~1.75 minutes total

UI Feedback During Backoff:
├─ "⟳ Syncing 1/5 (waiting...)"
├─ "⚠️ Failed, retrying in 27s"
├─ "⚠️ Failed, retrying in 18s"
├─ "⚠️ Failed, retrying in 8s"
└─ "✓ Synced" (when success)
```

---

## 📊 DATA MODELS

### SyncQueueItem Entity
```typescript
interface SyncQueueItem {
  id: UUID
  operation_type: OperationType  // CREATE_INSPECTION, SUBMIT_INSPECTION, etc.
  entity_id: UUID                 // Which inspection/approval
  payload: JSON                   // Full request body
  
  status: SyncStatus              // PENDING, SYNCING, SYNCED, CONFLICT, FAILED, RETRY_PENDING, DEAD_LETTER
  retry_count: 0-5
  last_error: string
  
  created_at: DateTime UTC
  last_retry_at: DateTime UTC
  next_retry_at: DateTime UTC
  synced_at: DateTime UTC (null if not synced)
  
  conflict_details: {
    our_version: number
    server_version: number
    our_data: JSON
    server_data: JSON
    resolution_strategy: "AUTO_MERGE" | "KEEP_LOCAL" | "USE_SERVER" | "MANUAL" | null
  } (null if no conflict)
}
```

### ConflictRecord Entity
```typescript
interface ConflictRecord {
  id: UUID
  sync_queue_item_id: UUID
  entity_type: "INSPECTION" | "APPROVAL"
  entity_id: UUID
  
  conflict_type: "VERSION_MISMATCH" | "DELETED_REMOTE" | "EDITED_BOTH"
  
  our_version: number
  server_version: number
  
  our_data: JSON
  server_data: JSON
  base_data: JSON  // For 3-way merge
  
  can_auto_merge: boolean
  merge_analysis: {
    our_changes: string[]      // ["description", "status"]
    server_changes: string[]   // ["location"]
    overlapping: string[]      // Common fields both changed
  }
  
  resolution_strategy: "AUTO_MERGE" | "KEEP_LOCAL" | "USE_SERVER" | "MANUAL_MERGE" | null
  resolved_by_user_id: UUID | null
  resolved_at: DateTime UTC | null
  
  created_at: DateTime UTC
  expires_at: DateTime UTC (24h from creation)
}
```

---

## ✅ ACCEPTANCE CRITERIA BY USE CASE

| UC | Scenario | Acceptance | Measurement |
|----|----------|-----------|-------------|
| UC-001 | Offline view masters | No crashes, search < 100ms | Manual test + perf metrics |
| UC-001 | Offline write blocked | Error modal shown immediately | UI test |
| UC-002 | Auto-sync on reconnect | Processes queue within 30s | Timer test |
| UC-002 | Master refresh parallel | Doesn't block queue processing | Concurrency test |
| UC-003 | Auto-merge non-conflicts | 3-way merge applied correctly | Unit test (merge logic) |
| UC-003 | Manual resolution timeout | Default action applied after 5m | Timeout test |
| UC-003 | 24h conflict expiration | Moved to dead letter | Scheduled task test |
| UC-004 | Exponential backoff | Correct intervals [5,10,30,60,60]s | Unit test (backoff calc) |
| UC-004 | Max 5 retries | Moved to dead letter on retry #5 | Integration test |

---

**Status**: 🎯 **BUSINESS LOGIC MODEL COMPLETE**  
**Total**: 4 use cases + state machines + sequence diagrams + decision trees  
**Next**: Activity 3 (NFR Design) with Architecture Decision Records (ADRs)
