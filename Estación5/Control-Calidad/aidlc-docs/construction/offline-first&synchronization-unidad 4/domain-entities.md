# Activity 1: Functional Design (Domain Entities) — Unit 4 (Offline-First & Synchronization)

**Date**: 2026-06-01  
**Unit**: Offline-First & Synchronization (Sync & Offline Management)  
**Scope**: Bounded context, aggregates, value objects, domain services, and events  
**Audience**: Domain Architects, Backend Developers, System Designers  

---

## 📋 OVERVIEW

Unit 4 manages offline-first synchronization for the textile quality control system. When inspectors work offline (no internet), inspection data is captured locally and synced to the backend when connectivity is restored.

**Core Problem**: Inspectors in remote textile factories may work in areas with intermittent internet. Data must be captured offline, queued, and synced reliably with conflict detection and retry logic.

**Key Capabilities**:
1. Queue inspection operations when offline
2. Detect conflicts when syncing (same inspection edited by multiple users)
3. Retry failed syncs with exponential backoff [5s, 10s, 30s, 60s, 60s]
4. Resolve conflicts (last-write-wins, discard local, ask user)
5. Track sync status (PENDING, SYNCING, SYNCED, FAILED, CONFLICT)

---

## 🎯 BOUNDED CONTEXT: Sync & Offline Management

**Responsibilities**:
- Manage operations queue (offline persistence)
- Detect and track sync status
- Implement retry strategy with exponential backoff
- Resolve data conflicts
- Notify UI of sync state changes

**Constraints**:
- Works with IndexedDB on frontend (browser storage)
- Works with PostgreSQL on backend (server state)
- Must handle network disconnections gracefully
- No data loss allowed (queue persisted locally)

**Key Flows**:
```
Inspector Offline                    Inspector Online
├─ Create Inspection (local)         ├─ Sync started
├─ Enqueue in SyncQueue              ├─ Send all PENDING items
└─ Mark PENDING                      ├─ Detect conflicts
                                     ├─ Resolve conflicts
                                     ├─ Mark items SYNCED
                                     └─ Clear local queue
```

---

## 🏛️ ROOT AGGREGATES

### AGGREGATE 1: SyncQueue (Sync Operations Queue)

**Purpose**: Queue and track operations for synchronization

**Root Entity: SyncQueueItem**

```
SyncQueueItem {
  id: String                    // UUID-v4, unique per operation
  operation_type: OperationType // CREATE_INSPECTION, UPDATE_INSPECTION, SUBMIT_INSPECTION, etc.
  entity_type: String          // 'inspection', 'defect', 'machine', 'fabric'
  entity_id: String            // e.g., "INS-123" (local id)
  payload: Object              // Full data to sync (JSON)
  
  status: SyncStatus           // PENDING → SYNCING → SYNCED (or FAILED, CONFLICT)
  retry_count: Int             // 0-5, incremented on failure
  last_retry_at: DateTime      // When last retry attempted
  next_retry_at: DateTime      // When next retry should happen
  
  error_message: String        // Reason for failure (if FAILED)
  conflict_detected: Boolean   // True if conflict found
  conflict_resolution: ConflictResolution  // How conflict was resolved
  
  enqueued_at: DateTime        // When operation was queued
  synced_at: DateTime          // When successfully synced (NULL until SYNCED)
  
  metadata: Object             // {wifi_signal: "strong", timestamp: "2026-06-01T10:30:00Z"}
}
```

**Status Values** (State Machine):
```
PENDING (new)
  ↓ (network online)
SYNCING
  ├→ SYNCED (success)
  │
  ├→ FAILED (error, retry_count < 5)
  │  └→ PENDING (after exponential backoff)
  │
  └→ CONFLICT (detected, awaiting resolution)
     ├→ SYNCED (resolved)
     └→ FAILED (unresolvable)
```

**Value Objects**:
- **OperationType**: CREATE_INSPECTION, UPDATE_INSPECTION, SUBMIT_INSPECTION, ARCHIVE_DEFECT, CREATE_DEFECT, UPDATE_MACHINE, etc.
- **SyncStatus**: PENDING, SYNCING, SYNCED, FAILED, CONFLICT
- **RetryCount**: 0-5 (Int, immutable after increment)
- **ConflictResolution**: LAST_WRITE_WINS, DISCARD_LOCAL, MANUAL_RESOLUTION

**Invariants**:
1. `status = SYNCED` → `synced_at ≠ NULL` and `error_message = NULL`
2. `status = FAILED` → `error_message ≠ NULL` and `synced_at = NULL`
3. `retry_count` increments only when retry attempted
4. `next_retry_at` follows exponential backoff: [5s, 10s, 30s, 60s, 60s]
5. Cannot retry if `retry_count = 5` (max retries exceeded)
6. `conflict_detected = true` → manual or automatic resolution required

**Behaviors**:
```
enqueueOperation(operation_type, entity_type, entity_id, payload, user_id)
  → Creates PENDING SyncQueueItem
  → Persists to IndexedDB
  → Returns queue item ID

markSyncing()
  → Transition PENDING → SYNCING
  → Used when sync starts

markSynced(synced_at)
  → Transition to SYNCED
  → Set synced_at timestamp
  → Remove from local queue (archived)

markFailed(error_message)
  → Transition to FAILED
  → Set error_message
  → If retry_count < 5: schedule retry

scheduleRetry()
  → Calculate next_retry_at using exponential backoff
  → Transition back to PENDING
  → Increment retry_count

detectConflict(server_version)
  → Compare payload.version with server_version
  → If versions differ: status = CONFLICT
  → Publish ConflictDetectedEvent

resolveConflict(resolution_strategy)
  → Apply resolution (LAST_WRITE_WINS, DISCARD_LOCAL, etc.)
  → Set conflict_resolution field
  → Transition to SYNCED
  → Publish ConflictResolvedEvent
```

---

### AGGREGATE 2: NetworkState (Network Connectivity & Status)

**Purpose**: Track network status and sync readiness

**Root Entity: NetworkStatus**

```
NetworkStatus {
  is_online: Boolean           // true = connected, false = offline
  last_status_check: DateTime  // When last checked online status
  last_sync_at: DateTime       // When last successful sync completed
  
  connection_quality: Enum     // EXCELLENT, GOOD, POOR, OFFLINE
  estimated_bandwidth_mbps: Float  // Estimated connection speed (if online)
  signal_strength: Int         // 0-100 (mobile signal, if available)
  
  pending_sync_count: Int      // Number of items in PENDING state
  failed_sync_count: Int       // Number of items in FAILED state
  
  metadata: Object             // {wifi_ssid: "...", latency_ms: 45, ...}
}
```

**Connection Quality Levels**:
- **EXCELLENT**: Latency < 50ms, Bandwidth > 1 Mbps
- **GOOD**: Latency 50-200ms, Bandwidth 500Kbps-1Mbps
- **POOR**: Latency > 200ms, Bandwidth < 500Kbps
- **OFFLINE**: No connection detected

**Behaviors**:
```
checkConnectivity()
  → Make lightweight HTTP request to server
  → Update is_online, connection_quality
  → Publish NetworkStatusChangedEvent
  → Auto-trigger sync if transitions from OFFLINE → ONLINE

goOnline()
  → Set is_online = true
  → Trigger sync of pending operations
  → Notify UI: "Syncing X items..."

goOffline()
  → Set is_online = false
  → Stop active sync requests
  → Notify UI: "Working offline, will sync when online"

estimateConnectivityRecovery()
  → Based on signal_strength, connection_quality
  → Return estimated time to next sync attempt
```

---

### AGGREGATE 3: SyncConflict (Conflict Detection & Resolution)

**Purpose**: Detect and resolve conflicts when same entity edited offline and online

**Root Entity: ConflictRecord**

```
ConflictRecord {
  id: String                   // UUID-v4
  sync_item_id: String         // Reference to SyncQueueItem that detected conflict
  
  entity_type: String          // 'inspection', 'defect', etc.
  entity_id: String            // 'INS-123'
  
  local_version: Int           // Version in IndexedDB/offline
  server_version: Int          // Version on server
  
  local_payload: Object        // Local data (JSON)
  server_payload: Object       // Server data (JSON)
  
  conflict_type: ConflictType  // VERSION_MISMATCH, DELETED_REMOTE, EDITED_BOTH
  
  resolution_strategy: ConflictResolution  // LAST_WRITE_WINS, DISCARD_LOCAL, MANUAL_RESOLUTION, MERGE
  resolved_payload: Object     // Final data after resolution (NULL until resolved)
  resolved_by_user_id: String  // User who made final choice (if MANUAL)
  
  detected_at: DateTime
  resolved_at: DateTime        // NULL until resolved
}
```

**Conflict Types**:
- **VERSION_MISMATCH**: Same entity edited both offline and on server
  - Example: Inspector A (offline) edits inspection while Inspector B (online) edits same inspection
  
- **DELETED_REMOTE**: Entity deleted on server but edited locally
  - Example: Defect archived on server while inspector was offline
  
- **EDITED_BOTH**: Both local and server have changes; versions diverged
  - Example: Multiple pending edits to same inspection

**Resolution Strategies**:
```
1. LAST_WRITE_WINS (automatic)
   → Compare timestamps (local vs server)
   → Keep version with newer timestamp
   → Apply automatically

2. DISCARD_LOCAL (automatic)
   → Discard local changes
   → Accept server version
   → Applied when server is authoritative

3. MERGE (semi-automatic)
   → Try to merge non-conflicting fields
   → Example: Inspector A added comment, Inspector B changed status
   → Merge both changes if fields don't overlap

4. MANUAL_RESOLUTION (user intervention)
   → Show UI with both versions
   → User chooses: "Keep local", "Keep server", or "Merge manually"
   → Requires user interaction
```

**Behaviors**:
```
detectConflict(sync_item, server_payload)
  → Compare versions, timestamps, payloads
  → Classify conflict type
  → Create ConflictRecord in UNRESOLVED state

canAutoResolve()
  → If LAST_WRITE_WINS or DISCARD_LOCAL: return true
  → If MERGE possible: return true
  → Otherwise: return false (needs manual resolution)

autoResolve()
  → Apply resolution_strategy
  → Calculate resolved_payload
  → Transition to RESOLVED
  → Return merged/final payload

manualResolve(user_choice_payload)
  → Accept user-provided resolution
  → Set resolved_payload
  → Set resolved_by_user_id
  → Transition to RESOLVED

publishConflictToUI()
  → Send ConflictDetectedEvent with both payloads
  → UI shows both versions to user
  → User selects resolution
```

---

### AGGREGATE 4: OfflineStorage (Local Persistent Storage)

**Purpose**: Manage IndexedDB schema and draft data storage

**Root Entity: LocalDataStore**

```
LocalDataStore {
  store_id: String             // Device identifier (random UUID)
  
  // IndexedDB Stores:
  drafts: {                    // Draft inspections not yet submitted
    [inspection_id]: {
      id, lote_id, photos[], comment, defect_type_id, 
      machine_culpable_id, status, last_edited_at
    }
  }
  
  sync_queue: {                // Queue of operations to sync
    [sync_item_id]: SyncQueueItem
  }
  
  cached_masters: {            // Cached defects, machines, fabrics
    defects: [{ id, name, status, created_at }],
    machines: [{ id, name, process, status }],
    fabrics: [{ id, name, composition }]
  }
  
  metadata: {
    last_sync_at: DateTime
    cache_ttl_ms: Int          // 1 hour = 3600000ms
    indexeddb_quota_used_mb: Float
  }
}
```

**IndexedDB Schema**:
```
Database: "textile-qc"
Version: 1

ObjectStore: drafts
  keyPath: "id"
  index: "status" (DRAFT, SUBMITTED_LOCALLY, SYNCING)
  index: "created_at"

ObjectStore: sync_queue
  keyPath: "id"
  index: "status" (PENDING, SYNCING, SYNCED, FAILED, CONFLICT)
  index: "enqueued_at"

ObjectStore: cached_masters
  keyPath: "type" (defects, machines, fabrics)
  index: "updated_at"

ObjectStore: network_status
  keyPath: "id"
  (singleton, stores current network state)
```

**Behaviors**:
```
saveDraft(inspection_id, draft_data)
  → Insert/update in IndexedDB drafts store
  → Mark status = DRAFT

submitDraft(inspection_id)
  → Move from drafts → sync_queue
  → Create SyncQueueItem(CREATE_INSPECTION, payload=draft)
  → Remove from drafts

getCachedMasters()
  → Check cache_ttl_ms: if expired, return null
  → Otherwise return cached masters

invalidateCache()
  → Clear cached_masters
  → Set cache_ttl_ms to 0 (expired)

getDraftsByStatus(status)
  → Query IndexedDB with index
  → Return matching drafts

calculateStorageUsage()
  → Estimate IndexedDB size
  → Warn if > 90% of quota

clearOldData(days)
  → Delete synced items older than N days
  → Keep failed items for manual recovery
```

---

## 📦 VALUE OBJECTS

### OperationType (Enum)
```
CREATE_INSPECTION      # New inspection started offline
SUBMIT_INSPECTION      # Inspection submitted while offline
UPDATE_INSPECTION      # Inspection updated while offline
ADD_PHOTO              # Photo added to inspection offline
COMMENT_INSPECTION     # Comment added while offline

CREATE_DEFECT          # New master created offline (rare)
UPDATE_DEFECT          # Master updated offline (rare)
ARCHIVE_DEFECT         # Master archived offline (rare)
```

### SyncStatus (Enum)
```
PENDING               # Waiting to sync (queued)
SYNCING               # Currently syncing with server
SYNCED                # Successfully synced, removed from queue
FAILED                # Sync failed, will retry
CONFLICT              # Conflict detected, awaiting resolution
```

### ConflictResolution (Enum)
```
LAST_WRITE_WINS       # Automatic: newer timestamp wins
DISCARD_LOCAL         # Automatic: server version wins
MERGE                 # Automatic: merge non-conflicting fields
MANUAL_RESOLUTION     # Requires user choice via UI
```

### RetryStrategy (Value Object)
```
RetryStrategy {
  max_retries: 5
  backoff_ms: [5000, 10000, 30000, 60000, 60000]  // [5s, 10s, 30s, 60s, 60s]
  
  calculateNextRetryTime(retry_count: Int) -> DateTime:
    → backoff_ms[min(retry_count, 4)] milliseconds from now
}
```

### NetworkQuality (Value Object)
```
NetworkQuality {
  latency_ms: Int
  bandwidth_mbps: Float
  signal_strength: Int  // 0-100
  
  getQualityLevel() -> ConnectionQuality:
    → "EXCELLENT" if latency < 50 && bandwidth > 1
    → "GOOD" if latency < 200 && bandwidth > 0.5
    → "POOR" otherwise
    → "OFFLINE" if no connection
}
```

---

## 🎭 DOMAIN SERVICES

### SyncService (Orchestrates Synchronization)

```
SyncService {
  constructor(sync_queue_repo, network_status_repo, conflict_repo)
  
  startSync(inspector_id)
    → Check network online
    → Get all PENDING items from sync_queue
    → For each item: send to server API
    → Handle responses: SYNCED, FAILED, CONFLICT
    → Return sync_result summary

  processSyncResponse(sync_item, server_response)
    → If success: markSynced(sync_item)
    → If error: markFailed(sync_item, error)
    → If conflict: detectConflict(sync_item, server_response)
    → Publish event

  retryFailedItems()
    → Get all FAILED items
    → For each: check if next_retry_at elapsed
    → If yes: reset to PENDING, schedule next retry
    → Call startSync()

  onNetworkStatusChange(new_status)
    → If OFFLINE → ONLINE: immediately startSync()
    → If ONLINE → OFFLINE: pause active syncs
    → Publish NetworkStatusChangedEvent
}
```

### ConflictResolutionService (Conflict Handling)

```
ConflictResolutionService {
  constructor(conflict_repo)
  
  detectConflict(sync_item, server_payload)
    → Compare local vs server payloads
    → Classify conflict type (VERSION_MISMATCH, DELETED_REMOTE, EDITED_BOTH)
    → Create ConflictRecord
    → Determine if auto-resolvable
    → Publish ConflictDetectedEvent

  attemptAutoResolve(conflict_record)
    → Try LAST_WRITE_WINS (compare timestamps)
    → Try MERGE (if fields don't overlap)
    → Return resolved_payload or null (needs manual)

  manualResolve(conflict_record, user_resolution)
    → Validate user choice
    → Apply resolution
    → Create merged_payload
    → Mark as RESOLVED
    → Publish ConflictResolvedEvent
    → Resume sync of this item
}
```

### RetryService (Exponential Backoff)

```
RetryService {
  strategy: RetryStrategy = {max_retries: 5, backoff_ms: [5s, 10s, 30s, 60s, 60s]}
  
  scheduleRetry(sync_item)
    → If retry_count >= 5: return false (max retries exceeded)
    → Calculate next_retry_at = now + backoff_ms[retry_count]
    → Set sync_item.next_retry_at
    → Increment retry_count
    → Return true (retry scheduled)

  shouldRetryNow(sync_item)
    → Return (now >= next_retry_at) && (retry_count < 5)

  getRetryDelay(sync_item)
    → Return (next_retry_at - now) in milliseconds
}
```

---

## 📡 DOMAIN EVENTS

### Event 1: OfflineOperationEnqueued
```
{
  id: UUID
  sync_item_id: String
  operation_type: OperationType
  entity_type: String
  entity_id: String
  enqueued_at: DateTime
  inspector_id: String
}
→ Fired when operation queued (inspector goes offline)
→ UI: Show "Queued for sync when online"
```

### Event 2: SyncStarted
```
{
  id: UUID
  sync_session_id: UUID
  pending_items_count: Int
  started_at: DateTime
}
→ Fired when sync begins
→ UI: Show "Syncing X items..."
```

### Event 3: SyncCompleted
```
{
  id: UUID
  sync_session_id: UUID
  synced_count: Int
  failed_count: Int
  conflict_count: Int
  completed_at: DateTime
}
→ Fired when all sync attempts finish
→ UI: Show results, "X synced, Y failed"
```

### Event 4: SyncFailed
```
{
  id: UUID
  sync_item_id: String
  error_message: String
  retry_count: Int
  next_retry_at: DateTime
  failed_at: DateTime
}
→ Fired when individual sync fails
→ UI: Show error, "Will retry in X seconds"
```

### Event 5: ConflictDetected
```
{
  id: UUID
  conflict_record_id: String
  entity_id: String
  conflict_type: ConflictType
  local_version: Int
  server_version: Int
  detected_at: DateTime
}
→ Fired when conflict found during sync
→ UI: Show conflict dialog with both versions
```

### Event 6: ConflictResolved
```
{
  id: UUID
  conflict_record_id: String
  resolution_strategy: ConflictResolution
  resolved_by_user_id: String (if MANUAL)
  resolved_at: DateTime
}
→ Fired after conflict resolved (auto or manual)
→ UI: Confirm resolution, "Syncing with server data..."
```

### Event 7: NetworkStatusChanged
```
{
  id: UUID
  previous_status: ConnectionQuality  (ONLINE, OFFLINE, POOR, GOOD, EXCELLENT)
  current_status: ConnectionQuality
  changed_at: DateTime
}
→ Fired on any network status change
→ UI: Update status indicator, trigger sync if OFFLINE→ONLINE
```

---

## 📚 REPOSITORY CONTRACTS

### SyncQueueRepository
```
interface SyncQueueRepository {
  save(sync_queue_item: SyncQueueItem) -> SyncQueueItem
  get_by_id(id: String) -> Optional<SyncQueueItem>
  get_all_by_status(status: SyncStatus, skip: Int, limit: Int) -> List<SyncQueueItem>
  get_pending_count() -> Int
  get_failed_count() -> Int
  mark_synced(sync_item_id: String) -> void
  mark_failed(sync_item_id: String, error: String) -> void
  mark_syncing(sync_item_id: String) -> void
  delete_synced_older_than(days: Int) -> void
}
```

### NetworkStatusRepository
```
interface NetworkStatusRepository {
  get_current_status() -> NetworkStatus
  update_status(status: NetworkStatus) -> void
  log_connectivity_event(event: ConnectivityEvent) -> void
}
```

### ConflictRepository
```
interface ConflictRepository {
  save(conflict_record: ConflictRecord) -> ConflictRecord
  get_by_id(id: String) -> Optional<ConflictRecord>
  get_unresolved() -> List<ConflictRecord>
  mark_resolved(conflict_id: String, resolution: ConflictResolution) -> void
}
```

---

## 🎯 KEY USE CASES

### UC1: Inspector Works Offline
```
1. Inspector starts inspection (no internet)
2. Creates/edits inspection locally (IndexedDB)
3. Submits inspection locally
   → Create SyncQueueItem(CREATE_INSPECTION)
   → Enqueue in sync_queue store
   → Mark status = PENDING
4. UI shows: "✓ Queued for sync when online"
5. Inspector continues working
```

### UC2: Network Restored
```
1. Network comes online
2. NetworkStatusService detects online
3. Publishes NetworkStatusChanged(ONLINE)
4. SyncService.startSync() triggered
5. Get all PENDING items from sync_queue
6. For each:
   → Mark status = SYNCING
   → Send to server API
   → If success: mark SYNCED
   → If conflict: create ConflictRecord
   → If error: mark FAILED, schedule retry
7. SyncCompleted event fired
8. UI updated with results
```

### UC3: Conflict Detected
```
1. During sync, inspector's offline edit conflicts with server
2. ConflictResolutionService.detectConflict() called
3. Classify: VERSION_MISMATCH
4. Try auto-resolve (LAST_WRITE_WINS):
   → Compare timestamps
   → Server is newer → auto-discard local
   → Mark SYNCED
5. If cannot auto-resolve:
   → ConflictDetectedEvent fired
   → UI shows both versions
   → Inspector chooses resolution
   → ConflictResolvedEvent fired
   → Resume sync
```

### UC4: Max Retries Exceeded
```
1. Sync fails (network error, server error)
2. RetryService.scheduleRetry() called
3. Increment retry_count (now 1)
4. Calculate next_retry_at = now + 5 seconds
5. Mark status = PENDING (wait for next retry)
6. [5 seconds later]
7. SyncService checks and retries (retry_count 2)
8. ... continues with backoff [5s, 10s, 30s, 60s, 60s]
9. After 5 attempts (retry_count = 5):
   → Cannot retry anymore
   → Mark FAILED permanently
   → UI shows: "Sync failed, manual intervention needed"
   → Inspector can manually retry or discard
```

---

## ✅ DESIGN PRINCIPLES

1. **Local-First**: Data captured locally immediately (no wait for network)
2. **Eventual Consistency**: Data syncs when network available
3. **No Data Loss**: All operations queued persistently
4. **Conflict Detection**: Identify when simultaneous edits occur
5. **User Control**: Inspector can choose conflict resolution
6. **Transparent**: UI always shows sync status clearly
7. **Automatic Retry**: Exponential backoff without user intervention
8. **Graceful Degradation**: System works offline; syncs when possible

---

## 📊 STATE TRANSITIONS DIAGRAM

```
SyncQueueItem Lifecycle:

PENDING (enqueued)
  ↓ [network online]
SYNCING (sending to server)
  ├→ SYNCED (success) ✓
  │  └→ Removed from queue (archived)
  │
  ├→ CONFLICT (detected on server)
  │  ├→ AUTO-RESOLVED
  │  │  └→ SYNCED ✓
  │  └→ MANUAL RESOLUTION NEEDED
  │     ├→ SYNCED ✓ (after user chooses)
  │     └→ FAILED (user discards)
  │
  └→ FAILED (error)
     └→ [after exponential backoff]
        └→ PENDING (retry_count < 5)
           ├→ Retries up to 5 times
           └→ FAILED permanently (retry_count ≥ 5)

Network State Transitions:

ONLINE ↔ OFFLINE
  ONLINE → OFFLINE: Pause syncs, queue operations
  OFFLINE → ONLINE: Resume/start syncs
```

---

**Status**: ✅ **ACTIVITY 1 COMPLETE**  
**Next Step**: Activity 2 — NFR Requirements for Unit 4  
**Key Domains Covered**: 
- 4 Root Aggregates (SyncQueue, NetworkState, SyncConflict, OfflineStorage)
- 5 Value Objects (OperationType, SyncStatus, ConflictResolution, RetryStrategy, NetworkQuality)
- 3 Domain Services (SyncService, ConflictResolutionService, RetryService)
- 7 Domain Events (OfflineOperationEnqueued, SyncStarted, SyncCompleted, SyncFailed, ConflictDetected, ConflictResolved, NetworkStatusChanged)
- 4 Repository Contracts
