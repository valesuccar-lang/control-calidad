# Business Rules — Unit 4 (Offline-First & Synchronization)

**Date**: 2026-06-01  
**Domain**: Offline-First Synchronization  
**Based on NFR Priorities**: Balanced performance, intelligent conflict resolution, selective encryption, offline-read-only, full DDD architecture, 200-500 inspector scale  

---

## 🎯 SYNCHRONIZATION STATE MACHINE

### SyncQueue Item States
```
PENDING → SYNCING → SYNCED ✅
         ↘ CONFLICT → RESOLVED → SYNCING → SYNCED
         ↘ FAILED → RETRY_PENDING → SYNCING → SYNCED
         ↘ FAILED → MAX_RETRIES → DEAD_LETTER
```

**State Definitions**:
1. **PENDING**: Operation enqueued, waiting for sync attempt
2. **SYNCING**: Network request in flight
3. **SYNCED**: Successfully persisted on server, ✅ confirmed
4. **CONFLICT**: Server returned 409 (version mismatch), requires resolution
5. **RESOLVED**: Conflict resolved (auto or manual), ready for retry
6. **FAILED**: Network/server error (500, timeout, parse error)
7. **RETRY_PENDING**: In exponential backoff retry queue
8. **MAX_RETRIES**: Failed after 5 retry attempts → moved to dead letter queue
9. **DEAD_LETTER**: Requires manual intervention (support ticket)

---

## 📋 CORE BUSINESS RULES (50 rules)

### BR-001 to BR-010: OFFLINE OPERATION

**BR-001**: Inspector can view cached master data (Defects, Machines, Fabrics) **without internet connection**.
- Cache: Last cached version + timestamp
- Fallback: If no cached masters, inspector cannot work
- Impact: Must pre-load masters before field work

**BR-002**: Inspector can **NOT create/edit/delete** inspections while offline.
- Only read-only access to cached data
- All write operations require connection
- Rationale: Avoid complex conflict resolution for high-frequency writes
- Trade-off: Inspectors can view data offline but must connect to submit

**BR-003**: If inspector attempts write while offline, show **"Connection required"** error immediately.
- Prevent queuing of writes to SyncQueue
- Encourage explicit online-first work pattern
- Exception: System detects connection, retry automatically

**BR-004**: When network is restored (online), **automatically initiate sync** without user action.
- Detect: NetworkStatus.is_online = true
- Trigger: SyncService.startSync()
- Timeout: If sync takes > 30 seconds, show progress indicator

**BR-005**: SyncQueue persists **all pending operations** in IndexedDB with metadata:
- operation_type: CREATE_INSPECTION, SUBMIT_INSPECTION, APPROVE_INSPECTION, etc.
- entity_id: Inspection ID or Approval ID
- payload: Full request body (serialized JSON)
- created_at: Timestamp of original operation
- retry_count: 0-5 (incremented on failure)
- last_retry_at: Timestamp of last sync attempt
- status: PENDING, SYNCING, SYNCED, CONFLICT, FAILED, etc.

**BR-006**: If sync fails with **network error** (timeout, no internet):
- Classify as FAILED
- Increment retry_count
- Schedule next retry using exponential backoff: **[5s, 10s, 30s, 60s, 60s]**
- Move to RETRY_PENDING state
- Show warning: "Sync pending (will retry in Xs)"

**BR-007**: If sync fails with **server error** (500, 503):
- Classify as FAILED
- Treat same as network error (exponential backoff)
- Log server error details for support

**BR-008**: If sync fails with **client error** (400, 403, 404):
- Classify as FAILED (non-recoverable)
- Do NOT retry
- Move to DEAD_LETTER (requires support intervention)
- Show error: "Sync failed - contact support"

**BR-009**: If sync fails with **validation error** (422, validation details):
- Classify as FAILED
- Show user-friendly validation error
- Allow user to edit and retry manually
- Example: "Defect not found - this defect may have been deleted"

**BR-010**: Maximum **5 retry attempts** per operation.
- After retry #5: Move to DEAD_LETTER
- Retry limits:
  - Network errors: Up to 5 retries (2.5 minutes total backoff)
  - Server errors: Up to 5 retries
  - Validation errors: Manual retry only (not automatic)
  - Client errors: No retry (immediate dead letter)

---

### BR-011 to BR-020: CONFLICT DETECTION & RESOLUTION

**BR-011**: A **CONFLICT** is detected when server returns HTTP 409 (Conflict).
- Trigger: Our version (v1) ≠ server version (v3) when updating
- Cause: Inspector's cached data is stale; another user edited since last sync
- Example: Inspector edits Defect v1 → sync fails with 409 because server has v3

**BR-012**: Conflict resolution strategy: **Intelligent (80% auto, 20% manual)**.
- Auto-resolve if: Our change + server change are **non-overlapping** (different fields)
  - Example: We changed description, server changed typical_process → merge safely
  - Logic: 3-way merge (our version, base version, server version)
- Manual resolution if: Both changed **same field** (true conflict)
  - Example: Both changed description → cannot auto-merge
  - Action: Show "Conflict detected" dialog, let inspector choose

**BR-013**: For auto-resolved conflicts:
- Fetch latest server version
- Apply our changes on top
- Retry sync (becomes SYNCING → SYNCED)
- Log: Conflict auto-resolved, both changes preserved
- No user notification (happened in background)

**BR-014**: For manual conflicts:
- Fetch latest server version
- Show side-by-side comparison:
  - Local version (what inspector wrote)
  - Server version (current server state)
- Options: Keep local, Use server, Manual merge
- After resolution: Retry sync
- Log: Inspector chose resolution strategy

**BR-015**: Conflict resolution must preserve **audit trail**.
- Record: Original change, server change, resolution strategy, resolver user
- Timestamp: Conflict detected time, resolved time
- Audit: "Conflict detected for Inspection #123 on 2026-06-01 14:30; auto-resolved (non-overlapping changes)"

**BR-016**: If conflict is **not resolved** within **24 hours**, move to DEAD_LETTER.
- Rationale: Inspector left conflict unresolved, sync cannot proceed
- Action: Notify inspector: "Sync conflict requires your attention (24h expiration)"
- After 24h: Auto-move to dead letter, require support

**BR-017**: **Deleted remote** conflict (SERVER_DELETE): Server deleted entity but inspector modified local copy.
- Detection: Sync returns 404 (entity not found)
- Options:
  1. Keep local (re-create on server) — Choose if deletion was mistake
  2. Discard local — Accept server deletion
  3. Manual review — Contact support
- Default: Prompt inspector to choose

**BR-018**: **Concurrent deletes**: Two inspectors delete same entity in parallel.
- Sync outcome: First sync succeeds (DELETE), second gets 404
- Rule: Second inspector's sync fails with 404
- Action: Show "Entity was deleted by another user" message
- No retry: This is expected behavior, not an error

**BR-019**: Conflict resolution **cannot block inspection workflow**.
- Timeout: Conflict resolution dialog auto-closes after 5 minutes (idle)
- Fallback: "Discard local" (server wins) to unblock
- Rationale: Inspector shouldn't abandon fieldwork due to sync conflict

**BR-020**: After conflict resolution, if retry **still fails**, treat as new error.
- Do not re-enter conflict resolution loop
- Move to FAILED state with backoff retry
- If fails twice: Move to DEAD_LETTER

---

### BR-021 to BR-030: CACHE MANAGEMENT

**BR-021**: Master data cache (Defects, Machines, Fabrics) is **read-only in offline mode**.
- Inspectors cannot add/edit masters offline
- Cache is populated by: GET /api/v1/masters/{type} when online
- Cache refresh: **Every 1 hour** (configurable, default 1h)

**BR-022**: Master cache has **version tracking**.
- Field: cache_version (integer)
- Increments when server sends updated masters
- Used to detect if local cache is stale

**BR-023**: Master cache refresh **must not block** inspector workflow.
- Fetch in background (background task)
- If refresh fails: Keep using stale cache
- Show indicator: "Masters cached as of 2h ago"

**BR-024**: If cache is **empty/missing** (e.g., first install on new device):
- Inspector cannot work offline
- Show: "Please connect to sync master data first"
- Disable offline mode until masters are cached

**BR-025**: Cache storage quota: **50MB maximum** per device.
- If cache exceeds 50MB: Remove oldest entries (LRU)
- Monitor: Warn user when cache > 40MB
- Clear button: User can manually clear cache

**BR-026**: Cached masters **never expire** (persist across sessions).
- Remain available until user deletes app or clears cache
- Sync keeps them fresh via background refresh

**BR-027**: Network quality impacts **cache refresh strategy**:
- EXCELLENT (5G, WiFi): Full masters (no limit)
- GOOD (4G): Top 500 masters (by frequency)
- POOR (3G, Edge): Top 100 masters (essentials only)
- OFFLINE: No refresh attempt

**BR-028**: Search within cached masters is **client-side** (offline).
- Use IndexedDB full-text search (browser native)
- Limit: Top 100 results per search
- No server query during offline search

**BR-029**: If inspectors search for master **NOT in cache**:
- Message: "Master not cached locally. Connect to sync first."
- Option: "Download missing masters" (if online)

**BR-030**: Master cache includes **audit metadata** (created_by, created_at, version).
- Used for: Inspectors to see who created a master
- Not used for: Sync decisions (version is canonical on server)

---

### BR-031 to BR-040: SYNC QUEUE MANAGEMENT

**BR-031**: Sync queue processes operations **in order** (FIFO).
- Enforce strict ordering to prevent causal inconsistencies
- Example: Create Inspection, then Submit Inspection — must sync in order

**BR-032**: Sync queue is **deduplicated**:
- If same operation (same entity_id, operation_type) is enqueued twice:
  - Keep first (PENDING)
  - Discard second (redundant)
- Exception: Different operations on same entity are allowed

**BR-033**: If sync queue has **> 100 pending items**:
- Show warning: "Large sync queue (100+ items), may take time"
- Recommend: "Consider submitting from online" if time-sensitive
- Continue processing but warn user

**BR-034**: Sync queue is **persisted across app crashes**.
- On app restart: Resume syncing from where left off
- Show: "Resuming sync (3/10 items remaining)"

**BR-035**: User can **manually clear** sync queue (experimental feature).
- Button: "Clear pending operations"
- Confirmation: "This will discard all pending operations. Continue?"
- Use case: User wants to start fresh after unresolvable conflicts

**BR-036**: Sync queue status is **always visible** to inspector.
- Status bar shows: "✓ Synced" or "⟳ Syncing 5/10" or "⚠️ 3 conflicts"
- Tappable: Opens sync detail modal with queue items

**BR-037**: Each sync queue item has **estimated retry time**.
- Shown in UI: "Next retry in 23s"
- Calculated: Current time + next backoff interval

**BR-038**: Sync queue operations **timeout after 10 seconds**.
- Network request max: 10s
- If no response: Treat as FAILED
- Move to RETRY_PENDING with backoff

**BR-039**: Sync queue operations are **atomic** (all-or-nothing per item).
- Server must accept or reject entire operation
- No partial success (transaction-like semantics)
- Server response: 200 OK (synced), 409 (conflict), 4xx (error), 5xx (error)

**BR-040**: Dead letter queue (max retries exceeded):
- Items remain in DLQ indefinitely
- Support team reviews DLQ daily
- Options: Manual fix + retry, or discard
- Notification: Email to support@aidlc.local when item added to DLQ

---

### BR-041 to BR-050: NETWORK & DEVICE MANAGEMENT

**BR-041**: Network quality is **continuously monitored**.
- Metrics:
  - Latency: Measure ping to API gateway
  - Packet loss: If > 5%, classify as POOR
  - Bandwidth: Estimate download speed
- Quality levels: EXCELLENT, GOOD, POOR, OFFLINE

**BR-042**: Network quality affects **sync strategy**:
- EXCELLENT: Full sync (all pending items)
- GOOD: Sync in batches (10 items/batch)
- POOR: Sync one-by-one (serialized)
- OFFLINE: No sync (queue operations but don't attempt)

**BR-043**: If network quality **degrades mid-sync**:
- Pause: Stop accepting new operations
- Resume: When quality improves
- Show: "Poor connection, pausing sync..."

**BR-044**: Detect **network transitions** (online → offline → online):
- Online → Offline: Stop sync attempt, queue remaining
- Offline → Online: **Auto-trigger sync** (no user action)
- Log: Each transition with timestamp

**BR-045**: Device storage is **monitored**:
- If available storage < 100MB: Warn user
- If available storage < 50MB: Disable offline mode
- Show: "Device storage low, connect to sync online"

**BR-046**: Battery status affects **sync strategy**:
- Full (> 80%): Normal sync
- Medium (20-80%): Reduce frequency (every 5 min instead of 2 min)
- Low (< 20%): Minimal sync (only critical operations)
- Charging: Full sync

**BR-047**: High-priority operations **sync immediately** (bypass queue):
- Example: Submit Inspection (time-sensitive)
- Attempt sync right away, even on POOR connection
- Fallback: If fails, add to queue with regular retry

**BR-048**: Background sync is **rate-limited**:
- Minimum interval between sync attempts: **2 seconds**
- Prevents: Excessive battery drain, API hammering
- Max frequency: 30 sync attempts/minute

**BR-049**: If inspector **enables airplane mode**:
- App detects: NetworkStatus.is_online = false
- Behavior: Disable all sync, queuing only
- On disable airplane mode: Auto-retry sync

**BR-050**: Device restart/app crash:
- On app relaunch: Resume syncing from queue
- Show: "Resuming previous sync (2 items pending)"
- No manual action required from inspector

---

## 📊 DATA VALIDATION RULES (10 rules)

**VR-001**: All operations in sync queue **must include**:
- operation_type (CREATE_INSPECTION, etc.)
- entity_id (Inspection UUID)
- payload (complete request body)
- timestamp (when operation was created)

**VR-002**: Payload validation happens **before enqueuing** to sync queue.
- Schema: Pydantic validation (same as online API)
- If invalid: Show error, do NOT queue operation
- Rationale: Catch errors immediately, don't waste sync queue space

**VR-003**: Entity IDs must be **UUIDs** (universally unique).
- Format: 36 characters (8-4-4-4-12)
- Generated on client (offline) before queuing
- Prevents: ID collisions when syncing from multiple devices

**VR-004**: Timestamps are **UTC** and include timezone.
- Format: ISO 8601 (2026-06-01T14:30:00Z)
- Validation: Must not be future-dated
- Used for: Audit, conflict resolution (last-write-wins)

**VR-005**: Field-level changes are **tracked** (for 3-way merge).
- Store: Original field values + new values
- Enable: Detection of non-overlapping changes
- Example: {description: {old: "...", new: "..."}}, {typical_process: {old: "...", new: "..."}}

**VR-006**: Enum fields (ProcessEnum, StatusEnum) must **match server enums**.
- Validation: Check against cached enum values
- If mismatch: Reject operation, show error
- Rationale: Prevent 422 validation errors on server

**VR-007**: Foreign key references (typical_machine_id) are **NOT validated offline**.
- Validation: Happens only on server during sync
- Rationale: Master data might be stale
- On conflict: Show error "Machine not found (may be deleted)"

**VR-008**: Version field (optimistic locking) is **required** for updates.
- Fetch: Latest version before editing
- Include: Version number in update payload
- Server validates: Our version must match server version for update to succeed

**VR-009**: Audit fields are **automatically populated**:
- created_by: Current user ID
- created_at: Current timestamp
- updated_by: Current user ID
- updated_at: Current timestamp
- App does NOT allow manual override

**VR-010**: Sensitive fields are **encrypted** before storage in IndexedDB.
- Fields: inspection_photo, approval_reason, defect_location (coordinates)
- Method: AES-256-GCM (browser crypto API)
- Key: Derived from user's password + device ID
- Decrypted: Only in memory during operations

---

## 🔐 SECURITY RULES (8 rules)

**SR-001**: Authentication token is **httpOnly** and **Secure** cookies.
- Not accessible to JavaScript (XSS protection)
- Only sent over HTTPS
- Renewed: Every 1 hour (sliding window)

**SR-002**: Refresh token is **stored in IndexedDB** (encrypted).
- Used to: Obtain new access token when expired
- Encryption: AES-256-GCM with device key
- Rotation: Automatic on each login

**SR-003**: Service Worker **must validate** requests before sync.
- Check: Authorization header present
- Check: Token not expired
- Check: User still has INSPECTOR role
- Reject: Any unauthenticated requests

**SR-004**: IndexedDB encryption uses **device-specific key**.
- Key derivation: PBKDF2(password + device_id, iterations=100k)
- Prevents: Data access if device is stolen
- Decryption: Only after user login

**SR-005**: Network requests **must use HTTPS only**.
- Enforce: No fallback to HTTP
- Certificate pinning: Pin API server certificate (optional, Phase 2)
- Rationale: Prevent man-in-the-middle attacks

**SR-006**: Offline data is **encrypted only for sensitive fields**.
- Encrypt: Inspection photo, approval reason, defect location
- Do NOT encrypt: Master data (public catalogs), metadata
- Rationale: Balance between security and performance

**SR-007**: Sync queue **never contains credentials** or secrets.
- Forbidden: Passwords, API keys, tokens
- Allowed: User ID, inspection data
- Validation: Reject any sync item containing sensitive keywords

**SR-008**: Service Worker intercepts all API requests for **logging**.
- Log: Request timestamp, URL, status code, user ID
- NO log: Request body, response body (contains data)
- Retention: 7 days, then purge

---

## 📈 PERFORMANCE TARGETS (5 rules)

**PT-001**: Sync **target latency < 3 seconds** for typical operation (1 inspection).
- Breakdown:
  - Network request: < 1 second (API response time)
  - IndexedDB update: < 0.5 seconds
  - UI update: < 0.5 seconds
  - Total: < 2 seconds (buffer: 1s for network variance)

**PT-002**: Sync payload **target size < 8MB** per batch.
- Limit: 10 items max per batch (GOOD network quality)
- Typical item: ~500KB (includes photo, attachments)
- Batches: Sequential to avoid overwhelming API

**PT-003**: Cache refresh **target latency < 5 seconds** (background task).
- Allowed: Runs in background, doesn't block inspector
- Timeout: If > 5 seconds, cancel and retry later

**PT-004**: IndexedDB queries **must return < 100ms**:
- Query: List inspections, search masters, fetch by ID
- Indexed: All common queries (indexed on entity_id, created_at, status)

**PT-005**: Service Worker **must not exceed 5MB** total code + caches.
- Limit: App itself (< 2MB), caches (< 3MB)
- Optimization: Code splitting, lazy loading of helpers

---

## 🎯 RULE PRIORITIES

**P0 (Critical - Must implement)**: BR-001 to BR-010, BR-031 to BR-040, VR-001 to VR-010, SR-001 to SR-005, PT-001 to PT-005

**P1 (Important - Should implement)**: BR-011 to BR-020, SR-006 to SR-008

**P2 (Nice to have - Could implement)**: BR-021 to BR-030, BR-041 to BR-050

**P3 (Future)**: Extended conflict resolution, predictive sync, differential sync

---

**Status**: 🎯 **BUSINESS RULES COMPLETE (50 rules)**  
**Next**: Generate NFR-Requirements.md and Business-Logic-Model.md  
**Usage**: These rules guide all testing and implementation in Activity 5 & 6
