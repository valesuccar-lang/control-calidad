# NFR Design — Consolidated ADRs for Unit 4 (Offline-First & Synchronization)

**Date**: 2026-06-01  
**Domain**: Offline-First Synchronization Architecture  
**Format**: Architecture Decision Records (ADR) per RFC 0001  
**Total ADRs**: 18 decisions covering storage, sync, conflict resolution, testing, and deployment  

---

## 📋 ADR INDEX

| # | Title | Status | Impact |
|---|-------|--------|--------|
| 1 | Service Worker + IndexedDB for Offline Storage | ✅ Decided | CRITICAL |
| 2 | Sync Queue Implementation Strategy | ✅ Decided | CRITICAL |
| 3 | Conflict Resolution: 3-Way Merge | ✅ Decided | CRITICAL |
| 4 | Exponential Backoff Retry Strategy | ✅ Decided | HIGH |
| 5 | Network Quality Detection | ✅ Decided | HIGH |
| 6 | Master Data Caching & Refresh | ✅ Decided | HIGH |
| 7 | Selective Field Encryption (AES-256-GCM) | ✅ Decided | HIGH |
| 8 | Sync Batching by Network Quality | ✅ Decided | HIGH |
| 9 | Client-Side Validation Before Queuing | ✅ Decided | MEDIUM |
| 10 | Dead Letter Queue for Max Retries | ✅ Decided | MEDIUM |
| 11 | WebSocket for Conflict Resolution & Status | ✅ Decided | MEDIUM |
| 12 | Service Worker Precaching Strategy | ✅ Decided | MEDIUM |
| 13 | IndexedDB Transaction Handling | ✅ Decided | MEDIUM |
| 14 | Conflict Resolution UI (Modal, Timeout, Default) | ✅ Decided | MEDIUM |
| 15 | Sync Queue Persistence Across Crashes | ✅ Decided | MEDIUM |
| 16 | Rate Limiting & Backpressure | ✅ Decided | MEDIUM |
| 17 | Testing Strategy: Offline Scenarios | ✅ Decided | MEDIUM |
| 18 | Progressive Enhancement & Fallbacks | ✅ Decided | LOW |

---

## 🏗️ DETAILED ADRs

---

## ADR-001: Service Worker + IndexedDB for Offline Storage

**Status**: ✅ **DECIDED**  
**Date**: 2026-06-01  
**Impact**: CRITICAL — Foundation for all offline functionality

### Context
We need to:
1. Cache master data (Defects, Machines, Fabrics) for offline access
2. Store inspection history for offline view
3. Persist sync queue across app restarts
4. Maintain operation integrity during network failures

**Options Considered**:

**Option A: Service Worker + IndexedDB (SELECTED)**
- Service Worker: Intercepts API requests, serves cached responses, handles sync
- IndexedDB: Structured storage (key-value + indexes), QueryAPI, transactional
- Pros:
  - ✅ Transparent to React components (intercept at network layer)
  - ✅ Works even with app closed (Service Worker stays alive)
  - ✅ Structured storage with queries (better than localStorage)
  - ✅ Can serve requests from cache immediately (offline UX)
  - ✅ Standard API (90% browser support)
- Cons:
  - ❌ Service Worker scope limited to HTTPS + localhost
  - ❌ IndexedDB quota limited (50MB per domain, varies by browser)
  - ❌ Debugging harder (DevTools learning curve)

**Option B: LocalStorage Only**
- Single key-value store (5-10MB)
- Pros: Simple, fast, no Service Worker complexity
- Cons: ❌ Too small for caching (1000+ masters + photos), ❌ Synchronous (blocks UI)

**Option C: WebSQL (Deprecated)**
- Pros: Structured queries like IndexedDB
- Cons: ❌ Deprecated by W3C, ❌ Not recommended for new projects

### Decision
**Use Service Worker + IndexedDB**

### Implementation Details
```typescript
// Service Worker structure
service-worker.ts
├── Install event: Pre-cache app shell (HTML, CSS, JS)
├── Activate event: Clean old caches
├── Fetch event:
│   ├── Request to /api/* → Check IndexedDB cache first
│   ├── If online & not cached → Fetch from network, update cache
│   ├── If offline → Serve from IndexedDB cache
│   ├── Sync queue operations → Queue in IndexedDB, retry periodically
│   └── Return response (from cache or network)

// IndexedDB schema
stores:
├── masters {keyPath: "id", indexes: ["name", "status", "created_at"]}
├── inspections {keyPath: "id", indexes: ["created_at", "status", "sync_status"]}
├── sync_queue {keyPath: "id", indexes: ["created_at", "status", "next_retry_at"]}
├── conflicts {keyPath: "id", indexes: ["sync_queue_item_id", "expires_at"]}
└── cache_metadata {keyPath: "store_name"}
```

### Consequences
- ✅ Offline functionality enabled
- ✅ Transparent caching (intercepted at network layer)
- ✅ App can work without network
- ❌ Additional complexity (Service Worker + IndexedDB APIs)
- ❌ Storage quota limits (need monitoring)
- ⚠️ HTTPS required (except localhost) — secure but may limit testing

### Acceptance Criteria
- [ ] Service Worker installs without errors
- [ ] IndexedDB stores created on app first load
- [ ] Offline requests served from cache (< 100ms)
- [ ] Cache updated on successful online requests
- [ ] Cache quota monitored (warn at 40MB, block at 50MB)

---

## ADR-002: Sync Queue Implementation Strategy

**Status**: ✅ **DECIDED**  
**Date**: 2026-06-01  
**Impact**: CRITICAL

### Context
Operations (create/update/delete inspections) must be queued when offline and synced when online. Queue must persist across app crashes and maintain order (FIFO).

**Options Considered**:

**Option A: IndexedDB-Backed Sync Queue (SELECTED)**
- Store queue items in IndexedDB (persistent)
- Query on app load: Restore queue from storage
- Process via Service Worker periodic sync
- Pros:
  - ✅ Persists across crashes
  - ✅ No in-memory loss if app closes
  - ✅ Can query/filter queue items
  - ✅ FIFO ordering maintained via created_at index
- Cons:
  - ❌ Slight latency querying/updating (vs in-memory)
  - ❌ Need transaction handling for consistency

**Option B: In-Memory Queue (with localStorage fallback)**
- Keep queue in Zustand store
- Periodic save to localStorage
- Pros: Fast access, simple
- Cons: ❌ Race conditions (save not atomic), ❌ localStorage limited 5-10MB

**Option C: IDB + Service Worker Background Sync API**
- Use Battery API native background sync
- Pros: System-managed retries, optimal battery efficiency
- Cons: ❌ Limited browser support (<70%), ❌ No control over retry logic

### Decision
**Use IndexedDB-Backed Sync Queue with Zustand cache**

### Implementation
```typescript
// Sync queue lifecycle
1. Operation enqueued:
   └─ Create SyncQueueItem in IndexedDB
   └─ Add to Zustand offlineStore (cache for UI)

2. App restarts:
   └─ Service Worker loads: Query all PENDING + RETRY_PENDING items
   └─ Restore to Zustand offlineStore
   └─ Resume processing

3. Item synced:
   └─ Update IndexedDB: status = SYNCED
   └─ Update Zustand cache
   └─ Remove from queue (eventually, keep for history)

4. Sync failure:
   └─ Update IndexedDB: status = RETRY_PENDING, next_retry_at = now + backoff
   └─ Service Worker reschedules: Check queue periodically (every 2 seconds)
```

### Consequences
- ✅ Queue survives app crashes
- ✅ FIFO ordering guaranteed
- ✅ Queryable queue (UI can show status)
- ✅ No data loss on app restart
- ❌ Slight complexity (IndexedDB transactions)
- ⚠️ Performance: < 10ms to query queue (acceptable)

### Acceptance Criteria
- [ ] Queue items persisted to IndexedDB
- [ ] Queue restored on app load (< 100ms)
- [ ] FIFO order maintained throughout sync process
- [ ] No duplicates in queue (deduplication working)
- [ ] Queue survives simulated app crash (restart + check restoration)

---

## ADR-003: Conflict Resolution — 3-Way Merge Strategy

**Status**: ✅ **DECIDED**  
**Date**: 2026-06-01  
**Impact**: CRITICAL

### Context
Two inspectors may edit the same inspection simultaneously:
- Inspector A: Edits description, syncs successfully (v1 → v2)
- Inspector B: Edited description offline, now tries to sync with v1 → gets 409 Conflict (server has v2)

Must resolve automatically when possible (non-overlapping changes), manually when necessary.

**Options Considered**:

**Option A: 3-Way Merge with Smart Analysis (SELECTED)**
- Compare: our_data, base_data (from when we fetched), server_data
- Detect: Which fields changed on each side
- Auto-merge if: Different fields changed (non-overlapping)
- Manual merge if: Same field changed both sides (true conflict)
- Pros:
  - ✅ 80% of conflicts auto-resolved (non-overlapping changes)
  - ✅ Only true conflicts require user action
  - ✅ Preserves both changes when possible
  - ✅ Reduces sync friction
- Cons:
  - ❌ Complex logic (3-way merge algorithm)
  - ❌ Requires base version (must cache when fetching)

**Option B: Last-Write-Wins (Simple)**
- Server version always wins
- Pros: Simple, deterministic
- Cons: ❌ Data loss (inspector's changes discarded), ❌ Frustrating UX

**Option C: Prompt Always (Safe but Annoying)**
- Show manual resolution for every conflict
- Pros: Zero data loss risk
- Cons: ❌ Terrible UX (frequent conflicts), ❌ Blocks workflow

### Decision
**Use 3-Way Merge with automatic non-overlapping resolution**

### Implementation
```typescript
// 3-way merge algorithm
function resolveConflict(ourData, baseData, serverData) {
  const ourChanges = diffObjects(baseData, ourData)
  const serverChanges = diffObjects(baseData, serverData)
  const overlappingFields = intersection(ourChanges.keys, serverChanges.keys)
  
  if (overlappingFields.length === 0) {
    // Non-overlapping: safe to merge
    return merge(ourData, serverData)
  } else {
    // Overlapping: true conflict, need manual resolution
    return {
      resolvable: false,
      overlappingFields,
      ourData,
      serverData,
      suggestedAction: "MANUAL_RESOLUTION"
    }
  }
}
```

### Consequences
- ✅ 80% of conflicts auto-resolved (better UX)
- ✅ Both changes preserved when possible
- ✅ Intelligent resolution (not blind last-write-wins)
- ❌ Complex implementation (merge algorithm)
- ❌ Must cache base version with every fetch

### Acceptance Criteria
- [ ] Non-overlapping changes auto-merged correctly (unit test)
- [ ] Overlapping changes prompt manual resolution
- [ ] Merged result includes both changes (no data loss)
- [ ] Base version cached and used for comparison
- [ ] Conflict resolution succeeds > 95% of cases

---

## ADR-004: Exponential Backoff Retry Strategy

**Status**: ✅ **DECIDED**  
**Date**: 2026-06-01  
**Impact**: HIGH

### Context
Sync operations may fail due to network or server issues. Must retry automatically without overwhelming the network or battery.

**Options Considered**:

**Option A: Exponential Backoff [5s, 10s, 30s, 60s, 60s] (SELECTED)**
- 1st retry: 5 seconds
- 2nd retry: 10 seconds
- 3rd retry: 30 seconds
- 4th retry: 60 seconds
- 5th retry: 60 seconds
- After 5 retries: Dead letter queue
- Pros:
  - ✅ Allows server time to recover
  - ✅ Reduces load during outages
  - ✅ Total backoff ~2.75 minutes (reasonable)
  - ✅ Not too aggressive (5s first retry is quick)
- Cons:
  - ❌ May not work for persistent failures (server down > 2.75 min)

**Option B: Linear Backoff [10s, 20s, 30s, 40s, 50s]**
- Simpler calculation
- Cons: ❌ Slower escalation, ❌ 150s total (too long)

**Option C: Immediate Retry (No Backoff)**
- Retry every 2 seconds indefinitely
- Cons: ❌ Hammers server, ❌ Drains battery, ❌ Thundering herd problem

### Decision
**Use Exponential Backoff with [5s, 10s, 30s, 60s, 60s] intervals**

### Implementation
```typescript
const BACKOFF_INTERVALS = [5000, 10000, 30000, 60000, 60000] // milliseconds
const MAX_RETRIES = 5

function calculateNextRetryTime(retryCount: number): number {
  if (retryCount >= MAX_RETRIES) return null // Dead letter
  const backoffMs = BACKOFF_INTERVALS[retryCount]
  return Date.now() + backoffMs
}
```

### Consequences
- ✅ Automatic recovery from transient failures
- ✅ Reduces server load during outages
- ✅ Battery efficient (spaced retry attempts)
- ✅ Clear progression (inspector can plan: "retry in 23s")
- ❌ Persistent failures may take 2.75 minutes to give up

### Acceptance Criteria
- [ ] Backoff intervals match spec [5, 10, 30, 60, 60]s
- [ ] retry_count incremented on failure
- [ ] next_retry_at calculated correctly
- [ ] After 5 retries: moved to dead letter
- [ ] Unit test: Verify backoff calculation (100 scenarios)

---

## ADR-005: Network Quality Detection

**Status**: ✅ **DECIDED**  
**Date**: 2026-06-01  
**Impact**: HIGH

### Context
Different network conditions (5G, WiFi, 4G, 3G, offline) require different sync strategies:
- EXCELLENT (5G, WiFi < 50ms): Batch 20 items
- GOOD (4G, WiFi 50-150ms): Batch 10 items
- POOR (3G, Edge 300+ ms): Batch 1 item (serialized)
- OFFLINE: No sync

Must detect this to optimize sync performance and battery usage.

**Options Considered**:

**Option A: Latency + Packet Loss Detection (SELECTED)**
- Ping API gateway every 5 seconds (ICMP like)
- Measure response time: latency
- Measure consecutive failures: packet loss
- Pros:
  - ✅ Accurate network assessment
  - ✅ Detects degradation in real-time
  - ✅ Can adapt sync strategy on-the-fly
- Cons:
  - ❌ Requires periodic requests (uses data/battery)
  - ❌ May fail on networks with ICMP blocked

**Option B: Bandwidth Estimation**
- Measure download speed of known-size resource
- Pros: Direct measurement of usable bandwidth
- Cons: ❌ Requires test file, ❌ Slow (takes 2-3 seconds per measurement)

**Option C: Connection API (navigator.connection)**
- Browser provides: type (4g, 3g, wifi), effectiveType
- Pros: ✅ Native, ✅ Low overhead
- Cons: ❌ Not supported everywhere, ❌ May be inaccurate

### Decision
**Use Latency Detection + navigator.connection fallback**

### Implementation
```typescript
async function detectNetworkQuality(): Promise<NetworkQuality> {
  try {
    // Method 1: Measure latency via ping endpoint
    const start = performance.now()
    const response = await fetch('/api/health', { method: 'HEAD', timeout: 5000 })
    const latency = performance.now() - start
    
    // Classify
    if (latency < 50) return 'EXCELLENT'  // 5G, WiFi
    if (latency < 150) return 'GOOD'      // 4G
    if (latency < 300) return 'POOR'      // 3G
    return 'VERY_POOR'                    // Edge, satellite
  } catch {
    // Fallback: Use browser Connection API
    const conn = navigator.connection
    if (!conn) return 'UNKNOWN'
    
    if (conn.type === 'wifi' || conn.type === 'ethernet') return 'EXCELLENT'
    if (conn.type === '4g') return 'GOOD'
    if (conn.type === '3g') return 'POOR'
    return 'VERY_POOR'
  }
}

// Check every 5 seconds
setInterval(detectNetworkQuality, 5000)
```

### Consequences
- ✅ Sync adapts to network conditions
- ✅ Better performance (batch sizing optimized)
- ✅ Battery efficient (POOR networks use fewer requests)
- ❌ Periodic pings use small amount of data
- ⚠️ Network quality can change, need updates every 5 seconds

### Acceptance Criteria
- [ ] Latency detection works (measure ping to /api/health)
- [ ] Classification accurate: EXCELLENT < 50ms, GOOD < 150ms, POOR < 300ms
- [ ] Fallback to Connection API if latency detection fails
- [ ] Quality updated every 5 seconds
- [ ] Batch size adjusts per quality: EXCELLENT 20, GOOD 10, POOR 1

---

## ADR-006: Master Data Caching & Refresh Strategy

**Status**: ✅ **DECIDED**  
**Date**: 2026-06-01  
**Impact**: HIGH

### Context
Inspectors need access to master data (Defects, Machines, Fabrics) for offline work. Must be cached but kept fresh (not stale > 1h).

**Options Considered**:

**Option A: Scheduled Refresh + LRU Eviction (SELECTED)**
- Cache masters in IndexedDB
- Refresh: Every 1 hour (background task)
- Eviction: LRU if cache > 50MB (keep most-accessed)
- Pros:
  - ✅ Automatic freshness (1h TTL)
  - ✅ Doesn't block sync queue
  - ✅ LRU prevents unbounded growth
  - ✅ Cached data always available (even if refresh fails)
- Cons:
  - ❌ May be stale (up to 1h old)
  - ❌ Uses data/battery for periodic refresh

**Option B: On-Demand Fetch (No Caching)**
- Fetch when online, fail when offline
- Pros: Always fresh
- Cons: ❌ Cannot work offline, ❌ Constant network usage

**Option C: Infinite Cache (No Refresh)**
- Cache once, never update
- Pros: Simplest
- Cons: ❌ Stale data (deleted masters still appear), ❌ No updates

### Decision
**Use 1-hour scheduled refresh with LRU eviction**

### Implementation
```typescript
// Master cache refresh
const CACHE_TTL = 1 * 60 * 60 * 1000  // 1 hour
const MAX_CACHE_SIZE = 50 * 1024 * 1024  // 50MB
const REFRESH_INTERVAL = 1 * 60 * 60 * 1000  // Check every 1 hour

async function refreshMasterCache() {
  const lastRefresh = await cache_metadata.get('masters_last_refresh')
  const now = Date.now()
  
  if (!lastRefresh || (now - lastRefresh) > CACHE_TTL) {
    try {
      // Fetch latest masters
      const defects = await fetch('/api/v1/masters/defects?limit=1000')
      const machines = await fetch('/api/v1/masters/machines?limit=1000')
      const fabrics = await fetch('/api/v1/masters/fabrics?limit=1000')
      
      // Update IndexedDB
      await idb.clear('masters')
      await idb.bulkPut('masters', [...defects, ...machines, ...fabrics])
      
      // Mark as refreshed
      await cache_metadata.put({store_name: 'masters', last_refresh: now})
    } catch (error) {
      // Refresh failed: keep using stale cache
      logger.warn('Master refresh failed', error)
    }
  }
}

// Check storage quota
async function evictLRU() {
  const cacheSize = await estimateIndexedDBSize()
  if (cacheSize > MAX_CACHE_SIZE) {
    // Remove oldest 10% of records
    const allMasters = await idb.getAll('masters')
    allMasters.sort((a, b) => a.accessed_at - b.accessed_at)
    const toDelete = allMasters.slice(0, Math.ceil(allMasters.length * 0.1))
    for (const master of toDelete) {
      await idb.delete('masters', master.id)
    }
  }
}

// Run refresh every 1 hour
setInterval(refreshMasterCache, REFRESH_INTERVAL)
```

### Consequences
- ✅ Offline access to masters (cached)
- ✅ Automatic refresh (1h TTL)
- ✅ Bounded storage (LRU eviction)
- ✅ Doesn't block sync queue (background task)
- ❌ May be up to 1 hour stale
- ⚠️ Network activity for periodic refresh (low impact)

### Acceptance Criteria
- [ ] Masters cached on first app load
- [ ] Refresh triggered every 1 hour
- [ ] Refresh doesn't block inspector workflow
- [ ] Cache size monitored, LRU evicts at 50MB
- [ ] Stale cache usable if refresh fails
- [ ] Offline search returns cached masters (< 100ms)

---

## ADR-007: Selective Field Encryption (AES-256-GCM)

**Status**: ✅ **DECIDED**  
**Date**: 2026-06-01  
**Impact**: HIGH

### Context
Some data is sensitive (inspection photos, approval reasons) and must be protected at rest. Other data (master catalogs, timestamps) is not sensitive. Full encryption would hurt performance.

**Options Considered**:

**Option A: Selective Encryption (SELECTED)**
- Encrypt only sensitive fields:
  - Inspection photos (JPEG/PNG)
  - Approval reasons (text)
  - Defect locations (GPS coordinates)
  - Quality metrics (numerical data)
- Don't encrypt:
  - Master data (public catalogs)
  - Metadata (timestamps, IDs, status)
- Algorithm: AES-256-GCM (authenticated encryption)
- Pros:
  - ✅ Protects sensitive data
  - ✅ Good performance (only sensitive fields encrypted)
  - ✅ Balance between security and speed
- Cons:
  - ❌ Need key management
  - ❌ Selective encryption adds complexity

**Option B: Full Encryption**
- Encrypt all data in IndexedDB
- Pros: ✅ Maximum security
- Cons: ❌ 15-20% performance overhead, ❌ Slower searches

**Option C: No Encryption**
- Store plaintext in IndexedDB
- Pros: ✅ Maximum performance
- Cons: ❌ No protection if device stolen, ❌ Compliance issue

### Decision
**Use Selective Encryption (AES-256-GCM) for sensitive fields only**

### Implementation
```typescript
// Key derivation (from password + device ID)
async function deriveEncryptionKey(password: string, deviceId: string): Promise<CryptoKey> {
  const salt = new TextEncoder().encode(`${deviceId}-salt`)
  const baseKey = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(password),
    {name: 'PBKDF2'},
    false,
    ['deriveBits']
  )
  
  const keyMaterial = await crypto.subtle.deriveBits(
    {name: 'PBKDF2', salt, iterations: 100000, hash: 'SHA-256'},
    baseKey,
    256
  )
  
  return crypto.subtle.importKey('raw', keyMaterial, {name: 'AES-GCM'}, false, ['encrypt', 'decrypt'])
}

// Encrypt sensitive field
async function encryptField(key: CryptoKey, plaintext: string): Promise<string> {
  const iv = crypto.getRandomValues(new Uint8Array(12))
  const encoded = new TextEncoder().encode(plaintext)
  
  const ciphertext = await crypto.subtle.encrypt(
    {name: 'AES-GCM', iv},
    key,
    encoded
  )
  
  // Return: base64(iv + ciphertext)
  const combined = new Uint8Array(iv.length + ciphertext.byteLength)
  combined.set(iv, 0)
  combined.set(new Uint8Array(ciphertext), iv.length)
  return btoa(String.fromCharCode(...combined))
}

// Decrypt sensitive field
async function decryptField(key: CryptoKey, encrypted: string): Promise<string> {
  const combined = new Uint8Array(atob(encrypted).split('').map(c => c.charCodeAt(0)))
  const iv = combined.slice(0, 12)
  const ciphertext = combined.slice(12)
  
  const plaintext = await crypto.subtle.decrypt(
    {name: 'AES-GCM', iv},
    key,
    ciphertext
  )
  
  return new TextDecoder().decode(plaintext)
}

// Storage
async function storeInspection(inspection, encryptionKey) {
  const encrypted = {
    ...inspection,
    photo: inspection.photo ? await encryptField(encryptionKey, inspection.photo) : null,
    location: inspection.location ? await encryptField(encryptionKey, JSON.stringify(inspection.location)) : null,
    // Other fields stored plaintext
  }
  await idb.put('inspections', encrypted)
}
```

### Consequences
- ✅ Sensitive data protected
- ✅ Good performance (minimal overhead)
- ✅ Balanced security/usability
- ❌ Key management complexity
- ❌ Need to handle decryption on data access

### Acceptance Criteria
- [ ] Sensitive fields encrypted using AES-256-GCM
- [ ] Encryption key derived from password + device ID
- [ ] Decryption < 500ms per field
- [ ] Key in memory only (not persisted)
- [ ] Plaintext fields searchable (masters, metadata)
- [ ] Unit test: Encrypt/decrypt roundtrip

---

## ADR-008: Sync Batching by Network Quality

**Status**: ✅ **DECIDED**  
**Date**: 2026-06-01  
**Impact**: HIGH

### Context
Sync queue may have many items (10-100). Must process efficiently based on network quality to avoid timeouts and battery drain.

**Options Considered**:

**Option A: Dynamic Batching by Network Quality (SELECTED)**
- EXCELLENT (latency < 50ms): Batch 20 items
- GOOD (latency 50-150ms): Batch 10 items
- POOR (latency > 150ms): Batch 1 item (serialized)
- Pros:
  - ✅ Optimized for each network condition
  - ✅ Reduces timeouts (POOR networks process fewer items)
  - ✅ Better battery efficiency (POOR networks: fewer requests, longer waits)
  - ✅ Adapts to changing network conditions
- Cons:
  - ❌ Need network quality detection (ADR-005)
  - ❌ Dynamic logic adds complexity

**Option B: Fixed Batch Size (e.g., always 10)**
- Pros: Simplicity
- Cons: ❌ Fails on POOR networks (timeout), ❌ Inefficient on EXCELLENT networks

**Option C: Progressive Batch Expansion**
- Start with 1, increase if successful: 1 → 2 → 4 → 8 → 16
- Pros: Adaptive without explicit network detection
- Cons: ❌ Slower on EXCELLENT networks (takes time to ramp up)

### Decision
**Use Dynamic Batching by Network Quality (detected via ADR-005)**

### Implementation
```typescript
function calculateBatchSize(networkQuality: NetworkQuality): number {
  switch (networkQuality) {
    case 'EXCELLENT': return 20
    case 'GOOD': return 10
    case 'POOR': return 1
    case 'OFFLINE': return 0
    default: return 10
  }
}

async function processSyncQueue() {
  const quality = await detectNetworkQuality()
  const batchSize = calculateBatchSize(quality)
  
  const pending = await idb.getAllFromIndex('sync_queue', 'status', 'PENDING')
  const batches = chunk(pending, batchSize)
  
  for (const batch of batches) {
    // Process batch sequentially (wait for all to complete)
    const results = await Promise.allSettled(
      batch.map(item => syncItem(item))
    )
    
    // Update statuses
    for (let i = 0; i < batch.length; i++) {
      if (results[i].status === 'fulfilled') {
        batch[i].status = results[i].value // SYNCED or CONFLICT
      } else {
        batch[i].status = 'FAILED'
      }
      await idb.put('sync_queue', batch[i])
    }
    
    // If POOR network: wait before next batch
    if (quality === 'POOR') {
      await sleep(1000) // 1s between items
    }
  }
}
```

### Consequences
- ✅ Efficient sync per network condition
- ✅ Reduced timeouts (POOR networks batch smaller)
- ✅ Battery efficient (longer waits on slow networks)
- ✅ Adapts to network changes
- ❌ Requires network quality detection
- ⚠️ POOR networks slower overall (serialized processing)

### Acceptance Criteria
- [ ] Batch size calculation correct per network quality
- [ ] EXCELLENT: 20 items/batch
- [ ] GOOD: 10 items/batch
- [ ] POOR: 1 item/batch (serialized)
- [ ] Items processed in batch sequentially (all complete before next batch)
- [ ] Integration test: Verify batching with simulated network qualities

---

## ADR-009: Client-Side Validation Before Queuing

**Status**: ✅ **DECIDED**  
**Date**: 2026-06-01  
**Impact**: MEDIUM

### Context
Operations should be validated before being added to sync queue. Invalid data should be rejected immediately with user feedback.

**Options Considered**:

**Option A: Validate Before Queuing (SELECTED)**
- Use Pydantic-like schemas (JavaScript: Zod, io-ts)
- Validate on client when operation submitted
- Reject invalid operations with clear error message
- Pros:
  - ✅ Immediate feedback to user
  - ✅ Don't waste queue space on invalid data
  - ✅ Same validation as server (consistency)
  - ✅ Prevent 422 errors on sync
- Cons:
  - ❌ Duplicate validation logic (client + server)
  - ❌ Schema updates must happen on both sides

**Option B: Validate Only on Server**
- Queue everything, server validates on sync
- Pros: Single source of validation truth
- Cons: ❌ User sees error only after queuing, ❌ Waste queue space

### Decision
**Validate on client before queuing using Zod schemas**

### Implementation
```typescript
// schemas.ts (shared schema definitions)
import { z } from 'zod'

export const InspectionCreateSchema = z.object({
  inspection_type: z.enum(['INCOMING', 'PROCESS', 'FINAL']),
  status: z.enum(['DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED']),
  description: z.string().min(1).max(1000),
  defect_id: z.string().uuid().optional(),
  machine_id: z.string().uuid().optional(),
  location: z.object({latitude: z.number(), longitude: z.number()}).optional(),
  photo_uri: z.string().optional(),
})

// Component
async function submitInspection(formData) {
  try {
    // Validate on client
    const validated = InspectionCreateSchema.parse(formData)
    
    // If valid: queue operation
    await offlineStore.enqueueOperation({
      operation_type: 'CREATE_INSPECTION',
      entity_id: uuidv4(),
      payload: validated,
    })
    
    // Success feedback
    showToast('Inspection queued for sync')
  } catch (error) {
    // Invalid: show error immediately
    showError(`Validation failed: ${error.message}`)
  }
}
```

### Consequences
- ✅ Immediate feedback to user
- ✅ Queue contains only valid data
- ✅ Prevents 422 errors on server
- ❌ Schemas must be maintained on both client and server
- ⚠️ Minor code duplication (validation logic)

### Acceptance Criteria
- [ ] Schemas defined in Zod
- [ ] Validation happens before enqueuing
- [ ] Invalid data rejected with error message
- [ ] User cannot queue invalid operation
- [ ] Schema includes all required fields
- [ ] Unit test: 100 validation scenarios

---

## ADR-010: Dead Letter Queue for Max Retries

**Status**: ✅ **DECIDED**  
**Date**: 2026-06-01  
**Impact**: MEDIUM

### Context
Operations that fail 5 times (after exponential backoff) need special handling. Can't retry forever (battery, storage), can't lose them (data loss).

**Options Considered**:

**Option A: Dead Letter Queue (SELECTED)**
- Move failed items to separate DLQ after max retries
- Keep in DLQ for support review
- Pros:
  - ✅ Clear separation (failed vs pending)
  - ✅ Queryable (support can see all failures)
  - ✅ No data loss
  - ✅ Inspector can see "Contact support" option
- Cons:
  - ❌ Requires support review (manual process)
  - ❌ Storage (DLQ items accumulate)

**Option B: Delete After Max Retries**
- After 5 retries, delete from queue
- Pros: Simplicity
- Cons: ❌ Data loss, ❌ No audit trail

**Option C: Indefinite Retry**
- Keep retrying forever with exponential backoff
- Pros: Eventually succeeds (if server recovers)
- Cons: ❌ Battery drain, ❌ Never moves on (stuck), ❌ Storage growth

### Decision
**Use Dead Letter Queue with daily support review**

### Implementation
```typescript
const MAX_RETRIES = 5

async function handleFailedItem(item: SyncQueueItem, error: Error) {
  if (item.retry_count >= MAX_RETRIES) {
    // Move to dead letter queue
    item.status = 'DEAD_LETTER'
    item.failure_reason = error.message
    item.failed_at = new Date()
    
    await idb.put('sync_queue', item)
    
    // Notify support
    await notifySupport({
      type: 'SYNC_FAILURE',
      item_id: item.id,
      entity_id: item.entity_id,
      operation_type: item.operation_type,
      error: error.message,
      user_id: currentUser.id,
      timestamp: new Date(),
    })
    
    // Show inspector: "Contact support"
    showNotification({
      type: 'error',
      title: 'Sync Error',
      message: 'Unable to sync. Contact support for help.',
      action: 'contact-support',
    })
  } else {
    // Retry: exponential backoff
    const backoff = BACKOFF_INTERVALS[item.retry_count]
    item.status = 'RETRY_PENDING'
    item.retry_count++
    item.next_retry_at = new Date(Date.now() + backoff)
    item.last_error = error.message
    
    await idb.put('sync_queue', item)
  }
}

// Daily: Support reviews DLQ
async function getDLQItems(): Promise<SyncQueueItem[]> {
  return idb.getAllFromIndex('sync_queue', 'status', 'DEAD_LETTER')
}
```

### Consequences
- ✅ Failed items don't get lost
- ✅ Queryable history (support can diagnose)
- ✅ Clear separation (pending vs dead letter)
- ✅ Inspector knows to contact support
- ❌ Requires manual support intervention
- ⚠️ DLQ items accumulate (need periodic cleanup)

### Acceptance Criteria
- [ ] Items moved to DLQ after retry #5
- [ ] DLQ items queryable per user
- [ ] Support team notified when item enters DLQ
- [ ] Inspector shown "Contact support" option
- [ ] DLQ items include full context (error, attempts, payload)
- [ ] Unit test: Verify DLQ movement after max retries

---

## ADR-011: WebSocket for Conflict Resolution & Status

**Status**: ✅ **DECIDED**  
**Date**: 2026-06-01  
**Impact**: MEDIUM

### Context
Need real-time updates for:
1. Conflict resolution: Show inspector modal when conflict detected
2. Sync status: Update progress bar as items sync

**Options Considered**:

**Option A: WebSocket (SELECTED)**
- Client opens WebSocket connection to sync service
- Service sends updates: conflict detected, item synced, sync completed
- Pros:
  - ✅ Real-time updates (low latency)
  - ✅ Server-initiated push (no polling)
  - ✅ Efficient (persistent connection)
- Cons:
  - ❌ Server complexity (maintain connections)
  - ❌ State management (reconnection handling)

**Option B: Polling**
- Client polls /api/sync/status every 2 seconds
- Pros: Simple, no server changes
- Cons: ❌ Latency (2s delay), ❌ More requests, ❌ Battery drain

**Option C: Server-Sent Events (SSE)**
- HTTP long-polling equivalent
- Pros: Simple, one-directional
- Cons: ❌ Not bidirectional, ❌ HTTP overhead

### Decision
**Use WebSocket for real-time sync status + conflict notifications**

### Implementation
```typescript
// Service Worker WebSocket handler
class SyncStatusManager {
  private ws: WebSocket
  
  connect() {
    this.ws = new WebSocket(`wss://${API_HOST}/ws/sync`)
    
    this.ws.onopen = () => logger.info('Sync WebSocket connected')
    
    this.ws.onmessage = async (event) => {
      const message = JSON.parse(event.data)
      
      switch (message.type) {
        case 'SYNC_PROGRESS':
          // Update status bar
          updateUI({processed: message.processed, total: message.total})
          break
          
        case 'CONFLICT_DETECTED':
          // Show modal
          showConflictModal(message.item, message.conflict)
          break
          
        case 'ITEM_SYNCED':
          // Update cache
          await updateQueueItemStatus(message.item_id, 'SYNCED')
          break
          
        case 'SYNC_COMPLETE':
          // Show toast
          showToast('All synced ✓')
          break
      }
    }
    
    this.ws.onerror = () => {
      logger.error('WebSocket error')
      // Fallback to polling
      this.startPolling()
    }
  }
  
  // Fallback: Polling if WebSocket fails
  private startPolling() {
    setInterval(async () => {
      const status = await fetch('/api/sync/status').then(r => r.json())
      updateUI(status)
    }, 2000)
  }
}
```

### Consequences
- ✅ Real-time conflict notifications
- ✅ Live sync progress updates
- ✅ Better UX (immediate feedback)
- ❌ WebSocket server complexity
- ✅ Graceful fallback to polling if WebSocket fails

### Acceptance Criteria
- [ ] WebSocket connection established
- [ ] CONFLICT_DETECTED messages show modal
- [ ] SYNC_PROGRESS updates UI in real-time
- [ ] ITEM_SYNCED marks queue item as synced
- [ ] Fallback to polling if WebSocket fails
- [ ] Integration test: Verify message flow

---

## ADR-012: Service Worker Precaching Strategy

**Status**: ✅ **DECIDED**  
**Date**: 2026-06-01  
**Impact**: MEDIUM

### Context
Service Worker must cache app shell (HTML, CSS, JS) so app works offline. Also need to serve cached API responses.

**Options Considered**:

**Option A: Precache App Shell + Cache-First Network (SELECTED)**
- Precache: App shell (main.html, index.css, bundle.js) on install
- Network:
  - API requests: Network first (online) → Cache fallback (offline)
  - Assets: Cache first (fast load) → Network fallback (update)
- Pros:
  - ✅ App loads instantly (precached app shell)
  - ✅ API responses cached automatically
  - ✅ Offline fallback for all requests
- Cons:
  - ❌ Complex cache management (old caches need cleanup)
  - ❌ Stale content if cache not updated

**Option B: Network-Only**
- No caching, always fetch from network
- Pros: Always fresh
- Cons: ❌ Cannot work offline, ❌ No speed benefits

**Option C: Cache-Only**
- Serve only from cache (no network)
- Pros: Fast, works offline
- Cons: ❌ Never updates (stale forever)

### Decision
**Use Precache App Shell + Network-First for API**

### Implementation
```typescript
// Service Worker installation
const CACHE_NAME = 'aidlc-offline-v1'
const PRECACHE_URLS = [
  '/',
  '/index.html',
  '/styles/main.css',
  '/scripts/bundle.js',
  '/manifest.json',
]

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_URLS)
    })
  )
})

// Request handling
self.addEventListener('fetch', (event) => {
  const {request} = event
  
  // API requests: Network first, cache fallback
  if (request.url.includes('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Cache successful responses
          const cache = caches.open(CACHE_NAME)
          cache.then(c => c.put(request, response.clone()))
          return response
        })
        .catch(() => {
          // Network failed: serve from cache
          return caches.match(request)
        })
    )
  } 
  // Static assets: Cache first, network fallback
  else {
    event.respondWith(
      caches.match(request)
        .then((response) => response || fetch(request))
    )
  }
})

// Cleanup old caches on activate
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) => {
      return Promise.all(
        names.map((name) => {
          if (name !== CACHE_NAME) {
            return caches.delete(name)
          }
        })
      )
    })
  )
})
```

### Consequences
- ✅ App loads fast (precached app shell)
- ✅ Offline functionality (cached API responses)
- ✅ Automatic cache updates (network first)
- ❌ Cache management complexity
- ✅ Clear cleanup strategy (old caches deleted on activate)

### Acceptance Criteria
- [ ] App shell precached on install
- [ ] API responses cached automatically
- [ ] Offline requests served from cache
- [ ] Old caches cleaned up on activate
- [ ] CACHE_NAME updated on app version bump
- [ ] Integration test: Verify cache behavior (online/offline)

---

## ADR-013: IndexedDB Transaction Handling

**Status**: ✅ **DECIDED**  
**Date**: 2026-06-01  
**Impact**: MEDIUM

### Context
IndexedDB operations must be atomic. Multiple concurrent operations (sync, UI updates) could cause race conditions or inconsistency.

**Options Considered**:

**Option A: Transaction-Based Operations (SELECTED)**
- All IndexedDB operations use transactions (readwrite)
- Atomic: All-or-nothing per transaction
- Pros:
  - ✅ Consistent state
  - ✅ No partial updates
  - ✅ ACID properties
- Cons:
  - ❌ Slightly slower (locking)
  - ❌ Need to handle transaction failures

**Option B: No Transactions (Direct Access)**
- Read/write directly to stores
- Pros: Simplicity, speed
- Cons: ❌ Race conditions possible, ❌ Inconsistent state

### Decision
**Use Transactions for all multi-step operations**

### Implementation
```typescript
// Utility: Transaction wrapper
async function transaction<T>(
  dbName: 'sync_queue' | 'masters' | 'inspections',
  mode: 'readonly' | 'readwrite',
  callback: (store: IDBObjectStore) => Promise<T>
): Promise<T> {
  const db = await openDB()
  const tx = db.transaction(dbName, mode)
  const store = tx.objectStore(dbName)
  
  return new Promise((resolve, reject) => {
    tx.oncomplete = () => resolve(result)
    tx.onerror = () => reject(new Error('Transaction failed'))
  })
}

// Example: Update queue item status + add to conflicts (atomic)
async function markConflict(item_id: string, conflictData: ConflictRecord) {
  return transaction('sync_queue', 'readwrite', async (store) => {
    // 1. Mark queue item as CONFLICT
    const item = await store.get(item_id)
    item.status = 'CONFLICT'
    await store.put(item)
    
    // 2. Add to conflicts table
    const conflictStore = store.parent.objectStore('conflicts')
    await conflictStore.add(conflictData)
    
    // Either both succeed or both fail (atomic)
    return item
  })
}

// Failure handling
try {
  await markConflict(item_id, conflictData)
} catch (error) {
  logger.error('Conflict marking failed', error)
  // Entire operation rolled back (queue item still SYNCING, conflict not added)
}
```

### Consequences
- ✅ Consistent state (no partial updates)
- ✅ ACID semantics
- ✅ No race conditions
- ❌ Slightly slower (transaction overhead)
- ⚠️ Must handle transaction failures gracefully

### Acceptance Criteria
- [ ] All multi-step operations use transactions
- [ ] Transaction failures rollback completely
- [ ] No partial updates possible
- [ ] Unit test: Verify atomicity (concurrent updates)
- [ ] Performance acceptable (< 10ms per transaction)

---

## ADR-014: Conflict Resolution UI (Modal, Timeout, Default)

**Status**: ✅ **DECIDED**  
**Date**: 2026-06-01  
**Impact**: MEDIUM

### Context
When true conflict detected (both sides changed same field), must show inspector options and let them choose, but can't block forever.

**Options Considered**:

**Option A: Modal with Timeout + Default Action (SELECTED)**
- Show modal: "Conflict detected for Inspection #123"
- Options: Keep local, Use server, Manual merge
- Timeout: 5 minutes idle → auto-select "Use server"
- Pros:
  - ✅ Inspector has time to make decision
  - ✅ Won't block forever (timeout)
  - ✅ Sensible default (server wins, least disruptive)
  - ✅ Manual merge for advanced users
- Cons:
  - ❌ Data loss risk (server wins by default)
  - ❌ Inspector might not notice timeout

**Option B: Block Until Resolved**
- Modal stays open, must resolve manually
- Pros: No automatic data loss
- Cons: ❌ Could block workflow indefinitely, ❌ Inspector forgets about it

**Option C: Auto-Resolve (Server Wins)**
- No modal, just silently use server version
- Pros: Simplicity
- Cons: ❌ Data loss, ❌ Inspector never knows

### Decision
**Use Modal with 5-minute timeout + default to "Use server version"**

### Implementation
```typescript
async function showConflictResolutionModal(
  item: SyncQueueItem,
  conflict: ConflictRecord
): Promise<'KEEP_LOCAL' | 'USE_SERVER' | 'MANUAL_MERGE'> {
  return new Promise((resolve) => {
    // Timeout: 5 minutes
    const timeout = setTimeout(() => {
      resolve('USE_SERVER') // Default
      logger.info('Conflict resolution timeout, applied default')
    }, 5 * 60 * 1000)
    
    // Show modal
    showModal({
      title: `Conflict: ${item.entity_id}`,
      description: 'This item was modified by another user. Choose how to resolve:',
      
      localData: conflict.our_data,
      serverData: conflict.server_data,
      
      options: [
        {
          label: 'Keep my changes',
          value: 'KEEP_LOCAL',
          description: 'Overwrite server with local changes'
        },
        {
          label: 'Use server version',
          value: 'USE_SERVER',
          description: 'Discard local changes (recommended)',
          default: true
        },
        {
          label: 'Manual merge',
          value: 'MANUAL_MERGE',
          description: 'Review both and edit manually'
        }
      ],
      
      onChoose: (choice) => {
        clearTimeout(timeout)
        resolve(choice)
      }
    })
  })
}

// In sync process
const choice = await showConflictResolutionModal(item, conflict)
switch (choice) {
  case 'KEEP_LOCAL':
    // Apply: local changes with server version number
    const merged = {...conflict.server_data, ...conflict.our_data}
    merged.version = conflict.server_version
    await retrySync(item, merged)
    break
    
  case 'USE_SERVER':
    // Apply: server version as-is
    await retrySync(item, conflict.server_data)
    break
    
  case 'MANUAL_MERGE':
    // Show editor: let inspector manually merge
    const manual = await showManualMergeEditor(
      conflict.our_data,
      conflict.server_data
    )
    await retrySync(item, manual)
    break
}
```

### Consequences
- ✅ Inspector can make informed choice
- ✅ Won't block forever (5-minute timeout)
- ✅ Default action reasonable (server wins)
- ✅ Advanced users can manually merge
- ❌ Risk of data loss (if timeout triggers)
- ⚠️ Need UX testing (is 5 minutes enough?)

### Acceptance Criteria
- [ ] Modal shows both versions side-by-side
- [ ] Inspector can choose resolution strategy
- [ ] Timeout fires after 5 minutes idle
- [ ] Default action ("Use server") applied on timeout
- [ ] Manual merge editor works (if implemented)
- [ ] UI test: Verify modal appearance + interaction

---

## ADR-015: Sync Queue Persistence Across Crashes

**Status**: ✅ **DECIDED**  
**Date**: 2026-06-01  
**Impact**: MEDIUM

### Context
If app crashes during sync, queue must be persisted so sync can resume on restart. Cannot lose operations.

**Options Considered**:

**Option A: IndexedDB Persistence (SELECTED)**
- All queue items stored in IndexedDB
- On app start: Load queue from storage
- Pros:
  - ✅ Survives crashes
  - ✅ No data loss
  - ✅ Can query queue (UI can show status)
- Cons:
  - ❌ Slight overhead (IndexedDB I/O)

**Option B: In-Memory Only**
- Queue in Zustand store only
- Save to localStorage periodically
- Pros: Speed
- Cons: ❌ Race condition with crash, ❌ Data loss possible

**Option C: SessionStorage**
- Queue lost on app close
- Pros: No persistence complexity
- Cons: ❌ Data loss on restart

### Decision
**Use IndexedDB for queue persistence**

### Implementation
```typescript
// On app startup
async function initializeSyncQueue() {
  // Load queue from IndexedDB
  const queueItems = await idb.getAllFromIndex(
    'sync_queue',
    'status',
    ['PENDING', 'RETRY_PENDING', 'CONFLICT', 'SYNCING']
  )
  
  // Restore to Zustand store
  offlineStore.setState({
    syncQueue: queueItems,
    queueStatus: {
      total: queueItems.length,
      syncing: queueItems.filter(i => i.status === 'SYNCING').length,
      conflicts: queueItems.filter(i => i.status === 'CONFLICT').length,
    }
  })
  
  logger.info(`Queue restored: ${queueItems.length} items`)
  
  // Resume sync if online
  if (navigator.onLine) {
    startSync()
  }
}

// When operation enqueued
async function enqueueOperation(operation) {
  const item = {
    id: uuidv4(),
    ...operation,
    status: 'PENDING',
    created_at: new Date(),
  }
  
  // 1. Store in IndexedDB (persistence)
  await idb.put('sync_queue', item)
  
  // 2. Add to Zustand store (for UI)
  offlineStore.addQueueItem(item)
  
  // 3. Return immediately (don't wait for sync)
  return item.id
}

// App startup hook
useEffect(() => {
  initializeSyncQueue()
}, [])
```

### Consequences
- ✅ Queue survives crashes
- ✅ No data loss
- ✅ Sync resumes automatically on restart
- ❌ IndexedDB overhead
- ⚠️ Stale SYNCING items on restart (might need cleanup)

### Acceptance Criteria
- [ ] Queue items persisted to IndexedDB
- [ ] Queue restored on app load (< 500ms for 100 items)
- [ ] No queue items lost after crash
- [ ] SYNCING items cleaned up on restart (reset to PENDING or FAILED)
- [ ] Integration test: Simulate crash + restart

---

## ADR-016: Rate Limiting & Backpressure

**Status**: ✅ **DECIDED**  
**Date**: 2026-06-01  
**Impact**: MEDIUM

### Context
Sync operations must not overwhelm the API or network. Need rate limiting to prevent thundering herd and DDoS-like behavior.

**Options Considered**:

**Option A: Client-Side Rate Limiting (SELECTED)**
- Min interval between sync attempts: 2 seconds
- Max concurrent requests: 5 (per ADR-008 batching)
- Backpressure: If server responds 429, exponential backoff
- Pros:
  - ✅ Client controls request rate
  - ✅ Prevents overwhelming API
  - ✅ Battery efficient
- Cons:
  - ❌ Server can still receive spikes (from multiple clients)

**Option B: Server-Side Rate Limiting Only**
- Server enforces limits (429 Too Many Requests)
- Client retries with backoff
- Pros: Single source of truth
- Cons: ❌ Less preventive (reactionary), ❌ Wasted requests

**Option C: No Rate Limiting**
- Sync as fast as possible
- Pros: Speed
- Cons: ❌ API overload risk, ❌ Battery drain

### Decision
**Use Client-Side Rate Limiting + Server-Side 429 handling**

### Implementation
```typescript
const SYNC_MIN_INTERVAL = 2000 // 2 seconds between sync attempts
const MAX_CONCURRENT_REQUESTS = 5

let lastSyncTime = 0
let activeRequests = 0

async function syncWithRateLimit() {
  // Check rate limit
  const now = Date.now()
  const timeSinceLastSync = now - lastSyncTime
  
  if (timeSinceLastSync < SYNC_MIN_INTERVAL) {
    const delayMs = SYNC_MIN_INTERVAL - timeSinceLastSync
    logger.info(`Rate limit: waiting ${delayMs}ms`)
    await sleep(delayMs)
  }
  
  lastSyncTime = Date.now()
  
  // Start sync
  const quality = await detectNetworkQuality()
  const batchSize = calculateBatchSize(quality)
  const queue = await getQueueItems()
  
  // Limit concurrent requests
  const batches = chunk(queue, Math.min(batchSize, MAX_CONCURRENT_REQUESTS))
  
  for (const batch of batches) {
    activeRequests += batch.length
    
    try {
      const results = await Promise.allSettled(
        batch.map(item => syncItem(item))
      )
      
      // Handle 429 Too Many Requests
      const throttled = results.filter(r => r.status === 'fulfilled' && r.value?.status === 429)
      if (throttled.length > 0) {
        logger.warn(`Received 429, backing off`)
        // Apply exponential backoff
        await sleep(5000) // 5 second backoff
      }
    } finally {
      activeRequests -= batch.length
    }
  }
}

// Rate-limit sync trigger
let syncTimeout: NodeJS.Timeout | null = null

function scheduleSyncIfNeeded() {
  if (syncTimeout) clearTimeout(syncTimeout)
  
  const timeSinceLastSync = Date.now() - lastSyncTime
  const delayMs = Math.max(0, SYNC_MIN_INTERVAL - timeSinceLastSync)
  
  syncTimeout = setTimeout(() => {
    syncWithRateLimit()
  }, delayMs)
}
```

### Consequences
- ✅ Controlled sync rate (prevents overload)
- ✅ Battery efficient (spaced requests)
- ✅ Better UX (predictable sync timing)
- ❌ Slightly slower (min 2s between attempts)
- ✅ Handles server 429 (exponential backoff)

### Acceptance Criteria
- [ ] Min 2 seconds between sync attempts
- [ ] Max 5 concurrent requests
- [ ] 429 responses trigger exponential backoff
- [ ] Unit test: Verify rate limit calculation
- [ ] Integration test: Verify with high-frequency enqueuing

---

## ADR-017: Testing Strategy for Offline Scenarios

**Status**: ✅ **DECIDED**  
**Date**: 2026-06-01  
**Impact**: MEDIUM

### Context
Offline-first code is hard to test (network state, timing, concurrency). Need comprehensive testing strategy.

**Options Considered**:

**Option A: Comprehensive Test Pyramid (SELECTED)**
- Unit tests (70%): Isolate functions (sync logic, merge, backoff)
- Integration tests (20%): Service Worker + IndexedDB
- E2E tests (10%): Full app flow (offline → online → sync)
- Mocking: Network events, IndexedDB, Service Worker
- Pros:
  - ✅ Good coverage
  - ✅ Fast feedback (unit tests run instantly)
  - ✅ Clear failure messages
- Cons:
  - ❌ High setup complexity
  - ❌ Mocking can be fragile

**Option B: E2E Only**
- Test full app behavior
- Pros: Real behavior tested
- Cons: ❌ Slow, ❌ Flaky, ❌ Hard to debug

### Decision
**Use Test Pyramid: 70% unit, 20% integration, 10% E2E**

### Implementation
```typescript
// Unit test: Conflict resolution logic
describe('3-way merge', () => {
  it('auto-merges non-overlapping changes', () => {
    const ourData = {description: 'New description', status: 'DRAFT'}
    const baseData = {description: 'Old', status: 'DRAFT'}
    const serverData = {description: 'Old', status: 'SUBMITTED', location: 'Factory A'}
    
    const result = threeWayMerge(ourData, baseData, serverData)
    
    expect(result).toEqual({
      description: 'New description',  // Ours (changed only on our side)
      status: 'SUBMITTED',              // Server (changed only on server)
      location: 'Factory A',            // Server (new field)
    })
  })
  
  it('detects conflicts on overlapping changes', () => {
    const ourData = {description: 'My description'}
    const baseData = {description: 'Old description'}
    const serverData = {description: 'Server description'}
    
    const result = threeWayMerge(ourData, baseData, serverData)
    
    expect(result).toEqual({
      resolvable: false,
      conflictingFields: ['description']
    })
  })
})

// Integration test: Sync queue + IndexedDB
describe('SyncQueue with IndexedDB', () => {
  let idb: IDBDatabase
  let queue: SyncQueueManager
  
  beforeEach(async () => {
    idb = await openDB()
    queue = new SyncQueueManager(idb)
  })
  
  it('persists queue items across restarts', async () => {
    // Enqueue item
    await queue.enqueue({
      operation_type: 'CREATE_INSPECTION',
      entity_id: 'INS-123',
      payload: {description: 'Test'}
    })
    
    // Simulate restart: Load from storage
    const queue2 = new SyncQueueManager(idb)
    const items = await queue2.getAll()
    
    expect(items).toHaveLength(1)
    expect(items[0].status).toBe('PENDING')
  })
})

// E2E test: Full workflow (Playwright)
test('offline → online → sync workflow', async ({page}) => {
  // 1. Go offline
  await page.context().setOffline(true)
  
  // 2. Try to create inspection
  await page.click('button:has-text("Create Inspection")')
  await page.fill('input[name="description"]', 'Test inspection')
  await page.click('button:has-text("Submit")')
  
  // 3. See offline error
  await expect(page.locator('text=Connection required')).toBeVisible()
  
  // 4. Go back online
  await page.context().setOffline(false)
  
  // 5. See status: "Syncing..."
  await expect(page.locator('text=Syncing')).toBeVisible()
  
  // 6. Wait for sync complete
  await expect(page.locator('text=Synced')).toBeVisible({timeout: 10000})
  
  // 7. Verify inspection appears on server (fetch API)
  const response = await page.context().request.get('/api/inspections')
  const inspections = await response.json()
  expect(inspections).toContainEqual(expect.objectContaining({
    description: 'Test inspection'
  }))
})
```

### Consequences
- ✅ Comprehensive coverage
- ✅ Fast feedback (unit tests)
- ✅ Clear failure messages
- ❌ High setup complexity
- ✅ Catching regressions early

### Acceptance Criteria
- [ ] 70% unit test coverage
- [ ] 20% integration test coverage
- [ ] 10% E2E test coverage
- [ ] Overall ≥ 85% code coverage
- [ ] All critical paths tested (sync, conflict, retry, offline)
- [ ] Tests run in < 60 seconds (unit)

---

## ADR-018: Progressive Enhancement & Fallbacks

**Status**: ✅ **DECIDED**  
**Date**: 2026-06-01  
**Impact**: LOW

### Context
Some browser features may not be available (Service Worker, IndexedDB, WebSocket). Need graceful degradation.

**Options Considered**:

**Option A: Progressive Enhancement (SELECTED)**
- Detect feature support on load
- Use advanced features if available (offline-first)
- Fallback to simpler behavior if not (online-only)
- Pros:
  - ✅ Works on more browsers
  - ✅ Graceful degradation
  - ✅ Better UX when features available
- Cons:
  - ❌ Code duplication (normal path + fallback path)

**Option B: Require All Features**
- If Service Worker or IndexedDB unavailable: Show error, cannot proceed
- Pros: Simplicity
- Cons: ❌ Doesn't work on older browsers

### Decision
**Use Progressive Enhancement with fallbacks**

### Implementation
```typescript
// Feature detection
const FEATURES = {
  serviceWorker: 'serviceWorker' in navigator,
  indexedDb: !!window.indexedDB,
  webSocket: !!window.WebSocket,
  backgroundSync: 'sync' in ServiceWorkerRegistration.prototype,
}

// On app load
async function initializeApp() {
  if (FEATURES.serviceWorker) {
    // Register Service Worker for offline
    await navigator.serviceWorker.register('/sw.js')
    enableOfflineMode()
  } else {
    // Fallback: Online-only
    logger.warn('Service Worker not supported, offline mode disabled')
    disableOfflineMode()
    showNotification({
      type: 'info',
      message: 'Your browser does not support offline mode'
    })
  }
  
  if (FEATURES.indexedDb) {
    // Use IndexedDB for caching
    await setupIndexedDB()
  } else {
    // Fallback: Use localStorage (5MB limit)
    logger.warn('IndexedDB not available, using localStorage')
    setupLocalStorageCache()
  }
  
  if (FEATURES.webSocket) {
    // Use WebSocket for real-time updates
    syncStatusManager.useWebSocket()
  } else {
    // Fallback: Polling
    logger.warn('WebSocket not supported, using polling')
    syncStatusManager.usePolling()
  }
}

// UI: Show feature support status
function FeatureSupportBar() {
  return (
    <div className="feature-support">
      <span>{FEATURES.serviceWorker ? '✓' : '✗'} Offline</span>
      <span>{FEATURES.indexedDb ? '✓' : '✗'} Storage</span>
      <span>{FEATURES.webSocket ? '✓' : '✗'} Real-time</span>
    </div>
  )
}
```

### Consequences
- ✅ Works on more browsers
- ✅ Graceful degradation (offline optional)
- ✅ Better UX when features available
- ❌ Code duplication (normal + fallback paths)
- ⚠️ Fallback paths need testing too

### Acceptance Criteria
- [ ] App works without Service Worker (online-only mode)
- [ ] App works without IndexedDB (localStorage fallback)
- [ ] App works without WebSocket (polling fallback)
- [ ] Feature support visible to user
- [ ] Integration test: Verify fallback paths work

---

## 📊 ADR SUMMARY TABLE

| ADR | Title | Status | Implementation Priority |
|-----|-------|--------|--------------------------|
| 1 | Service Worker + IndexedDB | ✅ | P0 (CRITICAL) |
| 2 | Sync Queue Implementation | ✅ | P0 (CRITICAL) |
| 3 | 3-Way Merge Conflict Resolution | ✅ | P0 (CRITICAL) |
| 4 | Exponential Backoff Retry | ✅ | P1 (HIGH) |
| 5 | Network Quality Detection | ✅ | P1 (HIGH) |
| 6 | Master Data Caching & Refresh | ✅ | P1 (HIGH) |
| 7 | Selective Field Encryption | ✅ | P1 (HIGH) |
| 8 | Sync Batching by Network Quality | ✅ | P1 (HIGH) |
| 9 | Client-Side Validation | ✅ | P2 (MEDIUM) |
| 10 | Dead Letter Queue | ✅ | P2 (MEDIUM) |
| 11 | WebSocket for Status | ✅ | P2 (MEDIUM) |
| 12 | Service Worker Precaching | ✅ | P2 (MEDIUM) |
| 13 | IndexedDB Transactions | ✅ | P2 (MEDIUM) |
| 14 | Conflict Resolution UI | ✅ | P2 (MEDIUM) |
| 15 | Queue Persistence | ✅ | P2 (MEDIUM) |
| 16 | Rate Limiting | ✅ | P2 (MEDIUM) |
| 17 | Testing Strategy | ✅ | P2 (MEDIUM) |
| 18 | Progressive Enhancement | ✅ | P3 (LOW) |

---

## 🔗 TRACEABILITY

| ADR | Business Rules | NFR Requirements | Use Cases |
|-----|-----------------|------------------|-----------|
| 1 | BR-001 to BR-030 | U-001 to U-005 | UC-001, UC-002 |
| 2 | BR-031 to BR-040 | P-001, R-001 | UC-002, UC-004 |
| 3 | BR-011 to BR-020 | R-002, R-003 | UC-003 |
| 4 | BR-006 to BR-010 | P-001, R-001 | UC-004 |
| 5 | BR-042 to BR-043 | P-001, P-002 | UC-002 |
| 6 | BR-021 to BR-030 | P-003, U-001 | UC-001 |
| 7 | SR-001 to SR-008 | S-001 | All |
| 8 | BR-042, BR-043 | P-002 | UC-002 |
| 9 | VR-001 to VR-010 | U-005 | All |
| 10 | BR-040 | R-001 | UC-004 |
| 11 | BR-036 | U-002 | UC-003 |
| 12 | BR-021 to BR-026 | U-001 | UC-001, UC-002 |
| 13 | BR-031 to BR-040 | R-004 | UC-002 |
| 14 | BR-013 to BR-016 | U-004 | UC-003 |
| 15 | BR-034 | R-001 | UC-004 |
| 16 | BR-048 | P-001 | UC-002 |
| 17 | All | All | All |
| 18 | All | All | All |

---

## 🚀 IMPLEMENTATION ROADMAP

**Phase 1 (Sprint 1-2)**: P0 ADRs (1, 2, 3)
- Service Worker + IndexedDB foundation
- Sync queue implementation
- Conflict resolution core

**Phase 2 (Sprint 3-4)**: P1 ADRs (4, 5, 6, 7, 8)
- Retry mechanism
- Network detection
- Caching & encryption
- Batching

**Phase 3 (Sprint 5+)**: P2 ADRs (9-16)
- Validation, dead letter, UI, transactions
- Rate limiting, persistence

**Phase 4**: P3 ADRs (18)
- Progressive enhancement & fallbacks

---

**Status**: 🎯 **ACTIVITY 3 COMPLETE (18 ADRs)**  
**Total**: 18 Architecture Decision Records covering all critical and important design decisions  
**Next**: Activity 4 (Infrastructure Design) with deployment topology and monitoring  
**Integration**: Each ADR traces to business rules, NFR requirements, and use cases
