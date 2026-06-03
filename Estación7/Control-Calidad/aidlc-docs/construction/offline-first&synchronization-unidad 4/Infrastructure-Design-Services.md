# Infrastructure Design — Services & Components for Unit 4 (Offline-First & Synchronization)

**Date**: 2026-06-01  
**Domain**: Offline-First Synchronization Architecture  
**Scope**: Frontend services, backend services, data layer, caching, messaging, monitoring  
**Scale**: 200-500 concurrent inspectors, prepared for 1000+  

---

## 🏗️ ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CLIENT (Browser)                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ React App (React 18, TypeScript)                                       │ │
│  │  ├─ Pages: Inspections, Masters, Approvals, Settings                 │ │
│  │  ├─ Components: SyncStatusBar, ConflictModal, OfflineIndicator      │ │
│  │  └─ Store: offlineStore (Zustand) — Queue, network status           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│          ↓                                   ↓                              │
│  ┌────────────────────────────┐  ┌───────────────────────────┐             │
│  │ Service Worker             │  │ IndexedDB                 │             │
│  │ ─────────────────────────── │  │ ─────────────────────────│             │
│  │ • Intercepts API requests  │  │ • masters store           │             │
│  │ • Offline fallback         │  │ • inspections store       │             │
│  │ • Sync queue orchestration │  │ • sync_queue store        │             │
│  │ • Background sync retry    │  │ • conflicts store         │             │
│  │ • Cache management         │  │ • cache_metadata          │             │
│  └────────────────────────────┘  └───────────────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
         ↓ HTTPS ↓                    ↓ HTTPS ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                        NETWORK & API GATEWAY                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Nginx (Reverse Proxy, Load Balancer, SSL termination)              │   │
│  │ • Routes:                                                           │   │
│  │   /api/v1/masters/* → Masters API                                  │   │
│  │   /api/v1/sync/* → Sync API (new endpoints)                        │   │
│  │   /api/v1/inspections/* → Inspections API                          │   │
│  │   /ws/sync → WebSocket (sync status updates)                       │   │
│  │ • TLS 1.2+ enforcement                                             │   │
│  │ • Rate limiting (DDoS protection)                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
         ↓ (200-500 concurrent connections) ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BACKEND SERVICES (Kubernetes Cluster)                   │
│                                                                              │
│  ┌──────────────────────────┐  ┌──────────────────────────┐               │
│  │ Sync API Service         │  │ Masters API Service      │               │
│  │ (Node.js/FastAPI)        │  │ (FastAPI)                │               │
│  │ ──────────────────────── │  │ ──────────────────────── │               │
│  │ • POST /sync/items       │  │ • GET /masters/defects   │               │
│  │ • POST /conflicts/{id}   │  │ • GET /masters/machines  │               │
│  │ • GET /sync/status       │  │ • GET /masters/fabrics   │               │
│  │ • WebSocket handler      │  │ • CRUD operations        │               │
│  │ • Conflict analysis      │  │ • Caching headers        │               │
│  │ • Sync orchestration     │  │ • Rate limiting          │               │
│  │ • Error handling         │  │                          │               │
│  └──────────────────────────┘  └──────────────────────────┘               │
│         ↓                              ↓                                    │
│  ┌──────────────────────────────────────────────────────┐                 │
│  │ Service Layer                                        │                 │
│  │ ──────────────────────────────────────────────────── │                 │
│  │ • SyncService: Orchestrate sync operations          │                 │
│  │ • ConflictResolutionService: 3-way merge logic      │                 │
│  │ • MastersService: CRUD + validation (from Unit 3)   │                 │
│  │ • CacheService: Master data caching strategy        │                 │
│  │ • ValidationService: Schema validation              │                 │
│  │ • AuditService: Audit trail logging                 │                 │
│  └──────────────────────────────────────────────────────┘                 │
│         ↓                              ↓                                    │
│  ┌──────────────────────────────────────────────────────┐                 │
│  │ Data Layer (Repositories)                            │                 │
│  │ ──────────────────────────────────────────────────── │                 │
│  │ • SyncQueueRepository: Manage queue items            │                 │
│  │ • ConflictRepository: Store conflict records         │                 │
│  │ • MastersRepository: Defects, Machines, Fabrics      │                 │
│  │ • InspectionsRepository: Inspection data             │                 │
│  │ • AuditRepository: Audit trail                       │                 │
│  └──────────────────────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────────────────────┘
         ↓                                 ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DATA & CACHE LAYER                                       │
│                                                                              │
│  ┌──────────────────────────┐  ┌──────────────────────────┐               │
│  │ PostgreSQL Database      │  │ Redis Cache              │               │
│  │ (Primary Data Store)     │  │ (Caching & Session)      │               │
│  │ ──────────────────────── │  │ ──────────────────────── │               │
│  │ • sync_queue table       │  │ • masters_cache          │               │
│  │ • conflicts table        │  │   (1h TTL)               │               │
│  │ • inspections table      │  │ • cache:version          │               │
│  │ • masters tables         │  │ • session:{user_id}      │               │
│  │ • audit_log table        │  │ • rate_limit:{ip}        │               │
│  │ (from Unit 3)            │  │                          │               │
│  │ • Transaction isolation  │  │ • Pub/Sub for progress   │               │
│  │ • ACID semantics         │  │   updates                │               │
│  └──────────────────────────┘  └──────────────────────────┘               │
└─────────────────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MESSAGE QUEUE (Optional, Phase 2)                        │
│  ┌──────────────────────────────────────────────────────┐                  │
│  │ RabbitMQ or AWS SQS                                  │                  │
│  │ ──────────────────────────────────────────────────── │                  │
│  │ • Async processing of sync items (high volume)       │                  │
│  │ • Retry scheduling                                   │                  │
│  │ • Conflict resolution notifications                  │                  │
│  │ • Audit log async write                              │                  │
│  └──────────────────────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MONITORING & OBSERVABILITY                               │
│  ┌──────────────────────────┐  ┌──────────────────────────┐               │
│  │ ELK Stack (Logging)      │  │ Prometheus + Grafana     │               │
│  │ ──────────────────────── │  │ ──────────────────────── │               │
│  │ • Elasticsearch: Logs    │  │ • Prometheus: Metrics    │               │
│  │ • Logstash: Processing   │  │ • Grafana: Dashboards    │               │
│  │ • Kibana: UI             │  │ • Alerts: Thresholds     │               │
│  │ • Structured logging     │  │ • Request latency        │               │
│  │   (JSON format)          │  │ • Error rates            │               │
│  │                          │  │ • Queue depth            │               │
│  └──────────────────────────┘  └──────────────────────────┘               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 FRONTEND SERVICES

### Service 1: React Application (React 18, TypeScript)

**Purpose**: Main UI application for inspectors and admins  
**Tech Stack**: React 18, TypeScript, Zustand, TailwindCSS  
**Deployment**: Static hosting (Netlify, S3 + CloudFront, or self-hosted)  

**Key Features**:
- Pages:
  - `InspectionsPage`: List, create, view inspections
  - `ApproversPage`: Approve/reject inspections
  - `MastersPage`: View cached masters (offline)
  - `SyncStatusPage`: Detailed queue and conflict status
  - `SettingsPage`: Cache management, offline preferences
- Components:
  - `SyncStatusBar`: Top bar showing sync status, queue count, conflicts
  - `ConflictResolutionModal`: Manual resolution UI
  - `OfflineIndicator`: Network status badge
  - `NetworkQualityBadge`: EXCELLENT/GOOD/POOR/OFFLINE
  - `QueueProgressBar`: Animated sync progress
- State Management:
  - `offlineStore` (Zustand): Queue, network status, conflicts
  - `authStore` (Zustand): User, authentication state
  - `mastersStore` (Zustand): Cached masters (synced from IndexedDB)

**API Endpoints Used**:
```
GET /api/v1/masters/defects          (cached, with 1h TTL)
GET /api/v1/masters/machines         (cached, with 1h TTL)
GET /api/v1/masters/fabrics          (cached, with 1h TTL)
GET /api/v1/inspections              (online: fetch from server, offline: IndexedDB)
POST /api/v1/inspections             (online only, queued if offline)
GET /api/v1/sync/status              (polling fallback)
WebSocket wss://api/ws/sync          (real-time status)
```

**Performance Requirements**:
- Page load: < 2 seconds (with precached app shell)
- Route transition: < 500ms
- Sync status update: < 100ms UI refresh
- Search masters: < 100ms (client-side IndexedDB)

**Monitoring**:
- Web Vitals (LCP, FID, CLS)
- API request latency
- Sync queue processing time
- Error rate tracking

---

### Service 2: Service Worker

**Purpose**: Intercept API requests, serve offline fallbacks, orchestrate sync  
**Tech Stack**: Web Workers API, Cache API, IndexedDB  
**Scope**: Application scope (/)  
**Lifespan**: Persists across browser sessions  

**Responsibilities**:
1. **Fetch Interception**:
   - Intercept all API requests
   - Network-first for /api/* (try network, fallback to cache)
   - Cache-first for /assets/* (quick load, update in background)
   - Return from cache if offline

2. **Sync Queue Orchestration**:
   - Monitor queue in IndexedDB
   - Process items when online (every 2 seconds check)
   - Respect network quality (ADR-008: batch sizing)
   - Handle retries with exponential backoff
   - Broadcast progress via WebSocket or Redis Pub/Sub

3. **Cache Management**:
   - Precache app shell on install
   - Update caches as requests succeed
   - Delete old cache versions on activate
   - Monitor storage quota (warn at 40MB, block at 50MB)

4. **Background Tasks**:
   - Master data refresh (every 1 hour)
   - Queue cleanup (remove old SYNCED items)
   - Cache eviction (LRU if over quota)

**Code Structure**:
```typescript
// service-worker.ts
├── Install: Precache app shell
├── Activate: Cleanup old caches
├── Fetch: Intercept & serve
├── Message: Handle commands from app
├── Sync: Background sync (if available)
└── Periodic: Scheduled background tasks
```

**Performance**:
- Request interception: < 50ms overhead
- Cache lookup: < 20ms
- Queue processing: < 100ms per item
- Background refresh: Non-blocking, < 5 seconds

**Browser Support**:
- Modern browsers (90%+ coverage)
- Graceful fallback to polling if not supported

---

### Service 3: IndexedDB Store

**Purpose**: Local persistent storage for offline data  
**Type**: Client-side NoSQL database  
**Quota**: 50MB per domain (browser default, varies)  

**Schema**:

**Store: `masters`**
- Key: `id` (string, e.g., "DEF-001")
- Indexes: `name` (unique), `status`, `created_at`, `type`
- Fields:
  ```typescript
  {
    id: string
    type: 'DEFECT' | 'MACHINE' | 'FABRIC'
    name: string
    description?: string
    status: 'ACTIVE' | 'ARCHIVED'
    created_by: string
    created_at: Date
    version: number
    // Encrypted (AES-256-GCM): photo?, location?, metrics?
  }
  ```
- TTL: 1 hour (refresh via Service Worker)
- Total: ~1000-2000 records (~2-3MB)

**Store: `inspections`**
- Key: `id` (UUID)
- Indexes: `created_at`, `status`, `sync_status`, `user_id`
- Fields:
  ```typescript
  {
    id: UUID
    inspection_type: 'INCOMING' | 'PROCESS' | 'FINAL'
    status: 'DRAFT' | 'SUBMITTED' | 'APPROVED'
    description: string
    location: {lat: number, lon: number}
    defect_ids: string[]
    
    // Encrypted fields (AES-256-GCM)
    photo_uri?: string  // Base64-encoded JPEG
    notes?: string
    
    sync_status: 'LOCAL' | 'SYNCED' | 'CONFLICT'
    created_at: Date
    synced_at?: Date
  }
  ```
- Total: ~4000 records (~3-5MB)

**Store: `sync_queue`**
- Key: `id` (UUID)
- Indexes: `created_at`, `status`, `next_retry_at`
- Fields:
  ```typescript
  {
    id: UUID
    operation_type: 'CREATE_INSPECTION' | 'UPDATE_INSPECTION' | 'APPROVE_INSPECTION'
    entity_id: UUID
    payload: JSON  // Full request body
    
    status: 'PENDING' | 'SYNCING' | 'SYNCED' | 'CONFLICT' | 'FAILED' | 'RETRY_PENDING' | 'DEAD_LETTER'
    retry_count: 0-5
    last_error?: string
    
    created_at: Date
    last_retry_at?: Date
    next_retry_at?: Date
    synced_at?: Date
  }
  ```
- Total: ~100 items (~100KB typical, up to 500KB peak)

**Store: `conflicts`**
- Key: `id` (UUID)
- Indexes: `sync_queue_item_id`, `created_at`, `expires_at`
- Fields:
  ```typescript
  {
    id: UUID
    sync_queue_item_id: UUID
    entity_type: 'INSPECTION'
    entity_id: UUID
    
    our_version: number
    server_version: number
    our_data: JSON
    server_data: JSON
    
    can_auto_merge: boolean
    resolution_strategy?: 'KEEP_LOCAL' | 'USE_SERVER' | 'MANUAL_MERGE'
    resolved_at?: Date
    
    created_at: Date
    expires_at: Date  // 24h from creation
  }
  ```
- Total: ~10 items (~50KB typical)

**Store: `cache_metadata`**
- Key: `store_name` (string)
- Fields:
  ```typescript
  {
    store_name: 'masters' | 'inspections'
    last_refresh: Date
    cache_version: number
    size_bytes: number
    item_count: number
  }
  ```

**Operations**:
- Transactional (ACID semantics)
- Async (non-blocking)
- Queries via indexes (fast)
- Encryption/decryption as needed

**Monitoring**:
- Storage quota usage (warn at 40MB)
- Cache hit rate (for IndexedDB reads)
- Transaction latency (< 50ms p95)

---

## 🖥️ BACKEND SERVICES

### Service 4: Sync API (Node.js or FastAPI)

**Purpose**: Receive and process sync operations from inspectors  
**Tech Stack**: Node.js (Express/Fastify) or Python (FastAPI)  
**Concurrency**: Handle 200-500 concurrent connections  
**Deployment**: Kubernetes pods, auto-scaling based on queue depth  

**Endpoints**:

**POST /api/v1/sync/items**
```
Request:
{
  operation_type: "CREATE_INSPECTION",
  entity_id: "INS-123",
  payload: {
    inspection_type: "INCOMING",
    description: "Tear in fabric",
    defect_ids: ["DEF-001"],
    location: {lat: 3.4, lon: -76.5}
  },
  version: 1,
  timestamp: "2026-06-01T14:30:00Z"
}

Response (Success - 200 OK):
{
  id: "INS-123",
  sync_status: "SYNCED",
  server_version: 1,
  synced_at: "2026-06-01T14:30:05Z"
}

Response (Conflict - 409):
{
  error: "VERSION_CONFLICT",
  our_version: 1,
  server_version: 3,
  server_data: {...}
}

Response (Validation - 422):
{
  error: "VALIDATION_ERROR",
  details: ["location.lat must be between -90 and 90"]
}
```

**POST /api/v1/sync/resolve-conflict**
```
Request:
{
  sync_queue_item_id: "SYN-456",
  resolution_strategy: "KEEP_LOCAL" | "USE_SERVER" | "MANUAL_MERGE",
  resolved_data?: {...}  // For MANUAL_MERGE
}

Response (200 OK):
{
  message: "Conflict resolved",
  retry_in_seconds: 5
}
```

**GET /api/v1/sync/status**
```
Response (200 OK):
{
  online: true,
  network_quality: "GOOD",
  queue_status: {
    pending: 0,
    syncing: 1,
    synced: 15,
    conflicts: 0,
    failed: 0
  },
  last_sync: "2026-06-01T14:30:45Z",
  estimated_completion: "2026-06-01T14:31:00Z"
}
```

**WebSocket: wss://api.aidlc.local/ws/sync**
```
Server → Client messages:
{
  type: "SYNC_PROGRESS",
  processed: 5,
  total: 10,
  current_item: "INS-123"
}

{
  type: "CONFLICT_DETECTED",
  item_id: "SYN-789",
  entity_id: "INS-123",
  conflict: {...}
}

{
  type: "ITEM_SYNCED",
  item_id: "SYN-456",
  entity_id: "INS-123"
}

{
  type: "SYNC_COMPLETE",
  total_synced: 10,
  total_conflicts: 0,
  duration_ms: 15000
}
```

**Processing Logic**:
```
1. Receive sync item
2. Authenticate & authorize (INSPECTOR role)
3. Validate payload (Pydantic/Zod)
4. Check version (optimistic locking)
   ├─ Version match → Proceed to 5
   └─ Version mismatch → 409 Conflict (send server version)
5. Store operation in sync_queue (database)
6. Dispatch to async worker (if high volume)
   OR process synchronously (if low volume)
7. Return 200 OK + synced timestamp
8. Emit WebSocket "ITEM_SYNCED" message
```

**Performance SLOs**:
- P50 latency: < 200ms
- P95 latency: < 1 second
- P99 latency: < 5 seconds
- Availability: 99.9% uptime
- Throughput: 1000+ operations/minute (at 500 concurrent inspectors)

**Concurrency Model**:
- Connection pool: 100-200 connections per node
- Request queuing: If > queue_depth (100), return 503 Service Unavailable
- Backpressure: Reject new sync if processing lag > 5 minutes

**Error Handling**:
- 400 Bad Request: Invalid JSON
- 401 Unauthorized: Missing or expired token
- 403 Forbidden: Non-INSPECTOR role
- 404 Not Found: Entity not found (e.g., master deleted)
- 409 Conflict: Version mismatch (send server version)
- 422 Unprocessable Entity: Validation error (detailed messages)
- 429 Too Many Requests: Rate limit exceeded
- 500 Internal Server Error: Unexpected error (logged)
- 503 Service Unavailable: Server queue overflow

---

### Service 5: Masters API (Existing from Unit 3)

**Purpose**: Serve master data (Defects, Machines, Fabrics)  
**Tech Stack**: FastAPI (Python)  
**Endpoints**: GET /api/v1/masters/{type}  

**Integration with Unit 4**:
- **Caching**: Response cached by Service Worker (network-first)
- **Cache TTL**: 1 hour (inspectors can work offline with 1h-old data)
- **Pagination**: Support pagination (limit=1000 for bulk fetch)
- **Version**: Include version field for cache validation

**Endpoints Used by Sync Service**:
```
GET /api/v1/masters/defects?include_archived=false&limit=1000
GET /api/v1/masters/machines?include_archived=false&limit=1000
GET /api/v1/masters/fabrics?include_archived=false&limit=1000
```

**Performance**:
- Response time: < 500ms (cached)
- Cache refresh: Happens in background, doesn't block sync queue

---

### Service 6: Inspections API (Existing)

**Purpose**: CRUD for inspection data  
**Modifications for Unit 4**:
- **Sync Status Tracking**: Track which inspections are synced vs pending
- **Conflict Detection**: Return 409 if version mismatch (for offline edits)
- **Bulk Operations**: Support bulk create/update (for processing sync queue)

---

### Service 7: Conflict Resolution Service (Backend)

**Purpose**: Analyze conflicts and suggest/apply resolutions  
**Type**: Internal service (not exposed via API)  

**Responsibilities**:
1. **3-Way Merge Analysis**:
   ```python
   def analyze_conflict(our_data, base_data, server_data):
     our_changes = diff(base_data, our_data)
     server_changes = diff(base_data, server_data)
     overlapping = intersection(our_changes.keys(), server_changes.keys())
     
     if len(overlapping) == 0:
       return {resolvable: true, merged_data: merge(our_data, server_data)}
     else:
       return {resolvable: false, overlapping_fields: overlapping}
   ```

2. **Resolution Strategies**:
   - AUTO_MERGE: Automatically merge non-overlapping changes
   - KEEP_LOCAL: Inspector's changes win (overwrite server)
   - USE_SERVER: Server version wins (discard local)
   - MANUAL_MERGE: Inspector manually merges (show UI)

3. **Conflict Logging**:
   - Log conflict with full context (for debugging)
   - Track resolution strategy used
   - Update audit trail

---

## 💾 DATA LAYER

### Database: PostgreSQL

**Tables** (Addition to Unit 3):

**Table: `sync_queue`**
```sql
CREATE TABLE sync_queue (
  id UUID PRIMARY KEY,
  operation_type VARCHAR(50),  -- CREATE_INSPECTION, UPDATE_INSPECTION, etc.
  entity_type VARCHAR(50),     -- INSPECTION, APPROVAL, etc.
  entity_id UUID,
  payload JSONB,
  
  status VARCHAR(20),          -- PENDING, SYNCING, SYNCED, CONFLICT, FAILED, RETRY_PENDING, DEAD_LETTER
  retry_count INT DEFAULT 0,
  last_error TEXT,
  
  created_at TIMESTAMP,
  last_retry_at TIMESTAMP,
  next_retry_at TIMESTAMP,
  synced_at TIMESTAMP,
  
  user_id UUID NOT NULL,
  
  INDEXES: (status, created_at), (next_retry_at), (user_id)
)
```

**Table: `conflicts`**
```sql
CREATE TABLE conflicts (
  id UUID PRIMARY KEY,
  sync_queue_item_id UUID NOT NULL REFERENCES sync_queue(id),
  entity_type VARCHAR(50),
  entity_id UUID,
  
  our_version INT,
  server_version INT,
  our_data JSONB,
  server_data JSONB,
  base_data JSONB,
  
  can_auto_merge BOOLEAN,
  overlapping_fields TEXT[],
  
  resolution_strategy VARCHAR(20),  -- KEEP_LOCAL, USE_SERVER, MANUAL_MERGE
  resolved_by_user_id UUID,
  resolved_at TIMESTAMP,
  
  created_at TIMESTAMP,
  expires_at TIMESTAMP,  -- 24h from creation (for cleanup)
  
  INDEXES: (sync_queue_item_id), (expires_at)
)
```

**Table: `sync_metadata`**
```sql
CREATE TABLE sync_metadata (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  device_id VARCHAR(256),
  
  last_sync_at TIMESTAMP,
  last_masters_refresh_at TIMESTAMP,
  cache_version INT,
  
  INDEXES: (user_id, device_id)
)
```

**Relationships**:
- `sync_queue.user_id` → `auth_users.id`
- `conflicts.sync_queue_item_id` → `sync_queue.id`
- `sync_queue.entity_id` → `inspections.id` (or other entities)

**ACID Properties**:
- Transactions for multi-step operations (e.g., update inspection + mark synced)
- Isolation level: READ_COMMITTED (prevents dirty reads)
- Foreign key constraints enforced

---

### Cache: Redis

**Purpose**: Cache frequently accessed data, manage sessions  

**Key Namespace**:
```
masters:defects        → HSET of all defects (1h TTL)
masters:machines       → HSET of all machines (1h TTL)
masters:fabrics        → HSET of all fabrics (1h TTL)
cache:version          → Current cache version (for invalidation)

session:{user_id}      → JWT session data (1h TTL)
rate_limit:{ip}        → Request count (sliding window, 1m)
queue:status:{user_id} → Sync queue status snapshot
```

**Operations**:
- GET/SET: Cache read/write
- EXPIRE: Set TTL
- INCR: Rate limiting counter
- LPUSH/LPOP: Queue operations (if async worker needed)
- PUBLISH/SUBSCRIBE: Broadcast sync progress to connected clients

**Performance**:
- Latency: < 10ms per operation
- Throughput: 10k+ ops/sec
- Eviction policy: LRU (least recently used)

---

## 📊 DATA FLOWS

### Flow 1: Normal Sync (Inspector → Server)

```
1. Inspector (online) submits inspection
   ↓
2. React app validates payload (Zod)
   ├─ Invalid → Show error, stop
   └─ Valid → Continue
   ↓
3. POST /api/v1/sync/items (Sync API)
   ↓
4. Sync API: Authenticate & validate
   ├─ Unauthorized → 401
   ├─ Invalid → 422 (validation error)
   └─ Valid → Continue
   ↓
5. Sync API: Check version (optimistic locking)
   ├─ Mismatch → 409 Conflict (send server data)
   └─ Match → Continue
   ↓
6. Sync API: Store in sync_queue table (PostgreSQL)
   ↓
7. Sync API: Dispatch to worker (if async) OR process directly
   ↓
8. Worker: Process operation (create/update inspection)
   ├─ Validate business rules
   ├─ Update inspections table
   └─ Create audit log entry
   ↓
9. Sync API: Return 200 OK (synced_at, server_version)
   ↓
10. Service Worker: Receive response
    ├─ Update sync_queue item in IndexedDB (SYNCED)
    ├─ Emit WebSocket message "ITEM_SYNCED"
    └─ Update UI (remove from queue, show progress)
    ↓
11. React app: Update status bar "✓ Synced"
    Auto-dismiss in 3 seconds
```

---

### Flow 2: Conflict During Sync

```
1. Inspector (offline, then online) edited Inspection v1
   ↓
2. Server has Inspection v3 (another inspector edited)
   ↓
3. POST /api/v1/sync/items (version=1, but server has 3)
   ↓
4. Sync API: Version mismatch detected
   ├─ our_version: 1
   ├─ server_version: 3
   └─ Return 409 Conflict + server_data
   ↓
5. Service Worker: Receive 409
   ├─ Mark sync_queue item as CONFLICT
   ├─ Fetch full conflict details (3-way merge analysis)
   └─ Update conflicts table in IndexedDB
   ↓
6. React app: Show ConflictResolutionModal
   ├─ Left: Inspector's version
   ├─ Right: Server's version
   └─ Options: Keep Local / Use Server / Manual Merge
   ↓
7. Inspector: Choose resolution (e.g., "Keep Local")
   ↓
8. React app: POST /api/v1/sync/resolve-conflict
   {
     sync_queue_item_id: "...",
     resolution_strategy: "KEEP_LOCAL"
   }
   ↓
9. Sync API: Apply resolution
   ├─ Merge: Inspector's changes + server version
   └─ Update conflicts table (resolved_at, strategy)
   ↓
10. Sync API: Retry sync with resolved data
    ├─ POST /api/v1/sync/items (with merged payload + server_version)
    └─ Return 200 OK (SYNCED)
    ↓
11. Service Worker: Update UI
    ├─ Mark conflict as resolved
    ├─ Update sync_queue item (SYNCED)
    └─ Show toast "Conflict resolved"
```

---

### Flow 3: Exponential Backoff Retry

```
1. Sync attempt fails (e.g., 500 Server Error, timeout)
   ↓
2. Classify error:
   ├─ Network error (timeout, offline) → Retryable
   ├─ Server error (500, 503) → Retryable
   └─ Client error (401, 403, 404) → Non-retryable (dead letter)
   ↓
3. If retryable and retry_count < 5:
   ├─ Calculate backoff: [5s, 10s, 30s, 60s, 60s][retry_count]
   ├─ Update sync_queue: next_retry_at = now + backoff
   ├─ Mark as RETRY_PENDING
   ├─ Update UI: "⚠️ Retry in 23s"
   └─ Continue
   ↓
4. Wait for backoff interval (or until online)
   ↓
5. Attempt retry: POST /api/v1/sync/items (same payload)
   ├─ Success (200) → Mark SYNCED, stop
   ├─ Conflict (409) → Go to Conflict flow
   └─ Failure → Increment retry_count, go to step 3
   ↓
6. After 5 retries: Move to DEAD_LETTER
   ├─ Update sync_queue: status = DEAD_LETTER
   ├─ Notify support team
   └─ Show inspector: "Contact support for help"
```

---

## 🔍 MONITORING & OBSERVABILITY

### Logging (ELK Stack)

**Log Format** (JSON, structured):
```json
{
  "timestamp": "2026-06-01T14:30:45.123Z",
  "level": "INFO",
  "service": "sync-api",
  "trace_id": "abc123...",
  "user_id": "USER-001",
  
  "event": "sync_item_processed",
  "operation_type": "CREATE_INSPECTION",
  "entity_id": "INS-123",
  
  "duration_ms": 245,
  "status": "SYNCED",
  "server_version": 1,
  
  "tags": ["sync", "inspection", "online"]
}
```

**Logs Indexed**:
- Elasticsearch: All logs searchable by trace_id, user_id, service, event
- Kibana: Dashboards for sync health, error rates, latency
- Retention: 30 days (automated cleanup)

**Key Events Logged**:
- sync_item_received
- sync_item_validated
- sync_item_processed
- conflict_detected
- conflict_resolved
- sync_retry_scheduled
- sync_failed (permanent)
- cache_refresh_completed
- storage_quota_warning

---

### Metrics (Prometheus + Grafana)

**Metrics to Collect**:
```
# Sync API
http_request_duration_seconds{service="sync-api", endpoint="/sync/items"}
http_requests_total{service="sync-api", status="200|409|422|500"}
sync_queue_depth{user_id="..."}
sync_item_processing_duration_seconds
conflict_detection_rate
conflict_resolution_rate{strategy="AUTO_MERGE|KEEP_LOCAL|USE_SERVER"}

# Database
pg_query_duration_seconds{query="sync_queue_insert"}
pg_connection_pool_size
pg_active_connections

# Redis
redis_command_duration_seconds{command="GET|SET|..."}
redis_memory_usage_bytes
cache_hit_ratio

# Infrastructure
kubernetes_pod_cpu_usage
kubernetes_pod_memory_usage
kubernetes_pod_restarts_total
```

**Dashboards**:
1. **Sync Health**: Queue depth, sync latency, success/failure rates
2. **Infrastructure**: Pod utilization, database connections, Redis memory
3. **Errors**: Error rates, types, top errors by frequency
4. **Performance**: P50/P95/P99 latencies, throughput (ops/sec)

**Alerts**:
- Queue depth > 500: Needs investigation
- Sync latency p95 > 5s: Performance degradation
- Error rate > 5%: Service health issue
- Pod restarts > 3 in 10 minutes: Crash loop
- Database connection pool exhausted: Capacity issue
- Redis memory > 80%: Eviction happening

---

## 🚀 DEPLOYMENT ARCHITECTURE

**Container Strategy**:
- Docker image for each service (Sync API, Masters API, Workers)
- Image registry: Docker Hub or ECR
- Image scanning: Security scanning (Trivy, Snyk)

**Kubernetes Configuration**:
```yaml
# Sync API Deployment
- Replicas: 3 (minimum)
- Auto-scaling: 3-10 based on queue depth + CPU
- Resource limits: 500m CPU, 512Mi memory per pod
- Liveness probe: /health (checks database connectivity)
- Readiness probe: /ready (checks sync queue processing)
- Termination grace period: 30s (time to drain requests)

# Redis Cache
- Deployment: Redis cluster or managed service (Elasticache, Redis Cloud)
- Replicas: 2 (for high availability)
- Persistence: RDB snapshot + AOF (optional, Phase 2)

# PostgreSQL Database
- Deployment: Managed service (RDS, CloudSQL) recommended
- Instance: db.t3.medium (or larger, based on load)
- Backup: Daily snapshots, 30-day retention
- Replication: Multi-AZ for failover

# API Gateway (Nginx)
- Deployment: 2-3 replicas (load balanced)
- TLS: Certificates rotated automatically
- Rate limiting: 1000 req/s per IP
- Compression: gzip enabled (reduces bandwidth)
```

---

**Status**: 🎯 **INFRASTRUCTURE DESIGN COMPLETE (Artefacto 1)**  
**Services Defined**: 7 major services + data layer + monitoring  
**Scale**: 200-500 concurrent inspectors, prepared for 1000+  
**Next**: Artefacto 2 (Deployment Architecture) + Artefacto 3 (Data Flow Diagrams)
