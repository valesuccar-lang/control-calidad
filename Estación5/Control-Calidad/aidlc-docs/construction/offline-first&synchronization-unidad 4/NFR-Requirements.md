# NFR Requirements — Unit 4 (Offline-First & Synchronization)

**Date**: 2026-06-01  
**Domain**: Offline-First Synchronization for Textile Quality Control  
**Approach**: Quality attribute-driven requirements with measurable specifications  

---

## 🎯 QUALITY ATTRIBUTES & SPECIFICATIONS

### 1. PERFORMANCE (Balanced: < 3s, < 8MB per batch)

**NFR-P-001: Sync Operation Latency**
- **Definition**: Time from user initiating sync to completion and UI update
- **Target**: < 3 seconds for typical operation (1 inspection + metadata)
- **Acceptance Criteria**:
  - Network request (API): < 1 second (95th percentile)
  - IndexedDB update: < 0.5 seconds
  - UI update: < 0.5 seconds
  - Total: < 2 seconds nominal, < 3 seconds p95
- **Measurement**: Client-side timer from sync start to success callback
- **Context**: GOOD network quality (4G, WiFi)
- **Exception**: POOR network (3G/Edge) allows < 5 seconds

**NFR-P-002: Sync Payload Size**
- **Definition**: Total bytes transmitted per sync batch
- **Target**: < 8MB per batch (GOOD network) or < 5MB (POOR network)
- **Breakdown**:
  - Metadata (headers, auth, timestamps): ~2KB
  - Single inspection (data + photo): ~500KB
  - Batch of 10: ~5MB
- **Acceptance Criteria**:
  - No single operation > 2MB
  - Batch size auto-adjusts per network quality:
    - EXCELLENT: 20 items/batch
    - GOOD: 10 items/batch
    - POOR: 1 item/batch (serialized)
- **Measurement**: HTTP request size (Content-Length header)

**NFR-P-003: Cache Refresh Latency**
- **Definition**: Time to fetch updated master data from server
- **Target**: < 5 seconds (background task, non-blocking)
- **Acceptance Criteria**:
  - Background task doesn't block inspector workflow
  - If refresh > 5s: Cancel and retry later (exponential backoff)
  - Timeout: 5 seconds max
  - Retry interval: 1 hour default
- **Measurement**: Background task duration
- **Note**: Runs in background, inspector doesn't wait

**NFR-P-004: Database Query Performance**
- **Definition**: Response time for IndexedDB queries
- **Target**: < 100ms for all queries
- **Queries**:
  - Get inspection by ID: < 20ms
  - List inspections (paginated, 50 items): < 50ms
  - Search masters (full-text): < 100ms
  - Count pending sync items: < 10ms
- **Acceptance Criteria**:
  - All critical queries indexed
  - No N+1 queries in UI rendering
  - Pagination: 50 items per page
- **Measurement**: Browser DevTools IndexedDB profiler

**NFR-P-005: Battery Impact**
- **Definition**: Battery drain during active sync
- **Target**: < 5% battery per 10 minutes of sync
- **Acceptance Criteria**:
  - Sync rate-limited to 2s minimum between attempts
  - Batch processing to reduce wake-ups
  - Service Worker sleeps when no operations
  - Background sync respects battery saver mode
- **Measurement**: Battery API (navigator.getBattery)
- **Context**: Important for fieldwork (all-day battery needed)

---

### 2. RELIABILITY (Intelligent Conflict Resolution: 80% auto, 20% manual)

**NFR-R-001: Operation Durability**
- **Definition**: Percentage of queued operations that successfully sync
- **Target**: > 99.5% of operations sync within 24 hours
- **Acceptance Criteria**:
  - Operations never lost (persisted to IndexedDB)
  - Retry mechanism: Exponential backoff [5s, 10s, 30s, 60s, 60s]
  - Max 5 retries (total ~2.5 minutes)
  - If still fails: Move to dead letter queue (support review)
  - Success metric: 99.5% of operations reach SYNCED state
- **Measurement**: ImportJob.status == SYNCED / total operations
- **Tracking**: Daily sync success rate report

**NFR-R-002: Conflict Detection Accuracy**
- **Definition**: Percentage of actual conflicts detected by system
- **Target**: > 98% of version mismatches detected
- **Acceptance Criteria**:
  - 409 Conflict response from server → marked as CONFLICT state
  - Manual verification: Inspector can identify all conflicts in UI
  - False positives: < 1% (incorrectly flagged as conflict)
  - False negatives: < 2% (missed actual conflicts)
- **Measurement**: Conflict detection test suite (100+ scenarios)
- **Log**: Every conflict logged with version numbers

**NFR-R-003: Conflict Resolution Success Rate**
- **Definition**: Percentage of conflicts resolved (not moved to dead letter)
- **Target**: > 95% of conflicts resolved within 24 hours
- **Resolution Types**:
  - Auto-resolved (non-overlapping): 80% (no user action)
  - Manual resolved: 15% (inspector chooses)
  - Expired (moved to DLQ): 5% (requires support)
- **Acceptance Criteria**:
  - Auto-resolution logic: 3-way merge (ours, base, theirs)
  - Manual resolution: 5-minute timeout + default action (server wins)
  - No deadlocks: Conflict resolution never hangs
- **Measurement**: Conflict resolution status tracking

**NFR-R-004: Data Consistency**
- **Definition**: No data loss or corruption during sync
- **Target**: 100% consistency (zero data loss)
- **Acceptance Criteria**:
  - Atomic operations: All-or-nothing per sync item
  - No partial uploads
  - Rollback on error: If sync fails, local state unchanged
  - Audit trail: Every operation logged with full context
  - Verification: Server-side validation on all inputs
- **Measurement**: Audit log integrity checks (monthly)

**NFR-R-005: Network Resilience**
- **Definition**: Ability to recover from network disruptions
- **Target**: Automatic recovery within 10 seconds of reconnect
- **Acceptance Criteria**:
  - Detects online/offline transition
  - Auto-triggers sync on reconnect (no user action)
  - Handles interruptions mid-sync (timeout after 10s)
  - Supports: WiFi → cellular switch, mobile → desktop
  - No manual "Retry" button needed (happens automatically)
- **Measurement**: Reconnect test suite (simulate network cuts)

---

### 3. SECURITY (Selective Encryption: Sensitive Fields Only)

**NFR-S-001: Offline Data Encryption**
- **Definition**: Protection of sensitive data at rest in IndexedDB
- **Target**: Encrypt sensitive fields; others plaintext (for performance)
- **Sensitive Fields** (encrypted):
  - Inspection photo (JPEG/PNG binary)
  - Approval reason (text, up to 500 chars)
  - Defect location (GPS coordinates)
  - Quality metrics (numerical measurements)
- **Non-Sensitive** (plaintext):
  - Master data (Defects, Machines, Fabrics — public catalogs)
  - Inspection metadata (created_at, created_by, status)
  - Timestamps, IDs
- **Algorithm**: AES-256-GCM (browser crypto API)
- **Key Management**:
  - Key derivation: PBKDF2(password + device_id, 100k iterations)
  - Salt: Random 16 bytes per device
  - Key stored: In-memory only (not persisted)
- **Acceptance Criteria**:
  - Decryption < 500ms per field
  - No plaintext in IndexedDB for sensitive fields
  - Encryption overhead: < 10% CPU
- **Measurement**: IndexedDB inspection + crypto benchmarks

**NFR-S-002: Network Data Encryption**
- **Definition**: Protection of data in transit
- **Target**: HTTPS only, TLS 1.2+
- **Acceptance Criteria**:
  - No HTTP fallback (HTTPS mandatory)
  - TLS version: 1.2 or higher
  - Cipher suites: Only strong ciphers (no RC4, DES)
  - Certificate validation: Verify server certificate
  - Certificate pinning: (Phase 2 enhancement)
- **Measurement**: TLS analyzer (testssl.sh)

**NFR-S-003: Authentication & Authorization**
- **Definition**: Only authorized users can sync
- **Target**: 100% authorization enforcement
- **Mechanisms**:
  - JWT token in httpOnly cookie (XSS protection)
  - Token expiration: 1 hour (sliding window refresh)
  - Role check: INSPECTOR role required (read), ADMIN (write masters)
  - Service Worker validates: Every request checked
- **Acceptance Criteria**:
  - Expired token → 401 Unauthorized
  - Invalid token → 401 Unauthorized
  - Non-INSPECTOR role → 403 Forbidden
  - Token refresh automatic (no user action)
- **Measurement**: Auth test suite (100+ scenarios)

**NFR-S-004: Sensitive Data Logging**
- **Definition**: No sensitive data leaks via logs
- **Target**: Zero sensitive data in logs
- **Sensitive Data** (never logged):
  - Passwords, API keys, tokens
  - Inspection photos (binary), coordinates (GPS)
  - Approval reasons, user comments
- **Safe to Log**:
  - User ID, operation type, timestamps
  - Entity IDs, status, error codes
  - Request/response headers (not body)
- **Acceptance Criteria**:
  - Log redaction: Strip sensitive fields before logging
  - Log retention: 7 days then purge
  - Audit: Weekly scan for sensitive data in logs
- **Measurement**: Log analysis (grep for sensitive patterns)

**NFR-S-005: Device Security**
- **Definition**: Protection if device is physically compromised
- **Target**: No unencrypted access to sensitive offline data
- **Acceptance Criteria**:
  - IndexedDB encrypted with device key (derived from password)
  - Service Worker code minified/obfuscated
  - No sensitive data in localStorage (IndexedDB only)
  - Device ID: Unique per device (hardware fingerprint)
  - If device stolen: Data unreadable without password
- **Measurement**: Penetration test (device extraction scenario)

---

### 4. USABILITY (Offline Read-Only: View Masters, Sync When Online)

**NFR-U-001: Offline Functionality**
- **Definition**: What inspectors can do without internet
- **Target**: Read-only access to cached master data
- **Offline Capabilities**:
  - ✅ View cached Defects, Machines, Fabrics
  - ✅ Search locally (client-side full-text search)
  - ✅ View cached inspection history
  - ❌ Create new inspections (requires connection)
  - ❌ Submit inspections (requires connection)
  - ❌ Approve inspections (requires connection)
- **User Feedback**:
  - Clear indication: "Offline mode - viewing cached data"
  - Action blocking: "Connect to sync before submitting"
  - Encouragement: "You're offline, but cached data is available"
- **Acceptance Criteria**:
  - No crashes when offline
  - Search latency < 100ms
  - Graceful error messages
- **Measurement**: User testing in offline scenarios

**NFR-U-002: Network Status Visibility**
- **Definition**: Inspectors know network status at all times
- **Target**: Always visible status indicator
- **Indicator Shows**:
  - Online/Offline status (icon + text)
  - Network quality: EXCELLENT, GOOD, POOR, OFFLINE
  - Sync status: "✓ Synced", "⟳ Syncing 3/10", "⚠️ Conflict", "❌ 2 errors"
  - Tap for details: Modal shows queue items, retry times, conflict info
- **Placement**: Top status bar (always visible)
- **Auto-update**: Refreshes every 2 seconds
- **Acceptance Criteria**:
  - Status accurate within 2 seconds
  - Tappable for details
  - Clear icons and colors (WCAG AA)
- **Measurement**: UI testing (screenshot + contrast checks)

**NFR-U-003: Sync Transparency**
- **Definition**: Inspectors understand what's syncing and why
- **Target**: Full visibility into sync queue and status
- **Transparency Components**:
  - Sync queue list: Show pending items with timestamps
  - Retry schedule: "Next retry in 23s"
  - Conflict details: Side-by-side comparison with options
  - Error messages: Plain language (not technical codes)
- **Examples**:
  - "Inspection #123 syncing... (2/5)"
  - "Conflict detected for Defect 'Roto' - choose resolution"
  - "Sync paused due to poor connection, will retry in 1 minute"
- **Acceptance Criteria**:
  - No technical jargon (suitable for non-technical users)
  - Action items clear (what should user do)
  - Estimated times (when will sync complete)
- **Measurement**: User testing comprehension

**NFR-U-004: Error Recovery Self-Service**
- **Definition**: Inspectors can resolve common sync issues
- **Target**: 90% of issues self-resolvable in UI
- **Self-Service Options**:
  - Conflict resolution: Choose local, server, or manual merge
  - Retry: Manual "Retry now" button for failed items
  - Connection: "Retry" when connection restored
  - Clear queue: "Clear pending operations" (last resort)
- **Assisted Options** (not self-service):
  - Contact support: Button to open support form
  - Logs: Download sync logs for debugging
- **Acceptance Criteria**:
  - Common issues (conflict, timeout) resolvable in UI
  - Support contact easy to find
  - Help text for each issue
- **Measurement**: User testing + support ticket volume

**NFR-U-005: Sync Efficiency**
- **Definition**: Sync happens without disrupting inspector workflow
- **Target**: Background sync (no blocking)
- **Behavior**:
  - Auto-trigger: When connection restored (no user action)
  - Background: Doesn't freeze UI or app
  - Rate-limited: Max 30 sync attempts/minute (prevent spam)
  - Interruptible: Inspector can cancel if desired
  - Non-blocking: Inspector can work while syncing
- **Acceptance Criteria**:
  - UI responsiveness: < 100ms frame time during sync
  - Sync doesn't interfere with data entry
  - Inspector notified of completion
- **Measurement**: Performance profiling (frame time monitoring)

---

### 5. MAINTAINABILITY (Full DDD Architecture: 2000-3000 lines)

**NFR-M-001: Architecture Clarity**
- **Definition**: Code structure and patterns are clear to developers
- **Target**: DDD-based architecture with defined layers
- **Layers**:
  1. **Domain**: SyncQueue, NetworkState, SyncConflict, OfflineStorage aggregates
  2. **Application Services**: SyncService, ConflictResolutionService, RetryService
  3. **Infrastructure**: IndexedDB repository, HTTP client, Service Worker
  4. **Presentation**: React components, Zustand store
- **Patterns Used**:
  - Aggregate root pattern
  - Value objects for immutable data
  - Domain events for state transitions
  - Repository pattern for persistence
  - Service layer for orchestration
- **Acceptance Criteria**:
  - Each layer has clear responsibilities
  - No circular dependencies
  - Interfaces defined (TypeScript types)
  - Aggregates are transaction boundaries
- **Measurement**: Architecture review (code walkthrough)

**NFR-M-002: Code Organization**
- **Definition**: Files and modules organized logically
- **Target**: Domain-driven folder structure
- **Structure**:
  ```
  src/
  ├── domain/
  │   ├── aggregates/
  │   │   ├── SyncQueue.ts
  │   │   ├── NetworkState.ts
  │   │   ├── SyncConflict.ts
  │   │   └── OfflineStorage.ts
  │   ├── services/
  │   │   ├── SyncService.ts
  │   │   ├── ConflictResolutionService.ts
  │   │   └── RetryService.ts
  │   ├── events/
  │   │   └── DomainEvents.ts
  │   └── types/
  │       └── Entities.ts
  ├── infrastructure/
  │   ├── repositories/
  │   │   ├── SyncQueueRepository.ts
  │   │   └── NetworkStatusRepository.ts
  │   ├── http/
  │   │   └── ApiClient.ts
  │   └── storage/
  │       └── IndexedDBStore.ts
  ├── application/
  │   ├── usecases/
  │   │   ├── EnqueueOperationUsecase.ts
  │   │   ├── SyncOperationsUsecase.ts
  │   │   └── ResolveConflictUsecase.ts
  │   └── services/
  │       └── SyncApplicationService.ts
  ├── presentation/
  │   ├── components/
  │   │   ├── SyncStatusBar.tsx
  │   │   └── ConflictResolutionModal.tsx
  │   └── store/
  │       └── offlineStore.ts
  └── ui/
      ├── styles/
      └── icons/
  ```
- **Acceptance Criteria**:
  - Files organized by layer, not by feature
  - Max 300 lines per file
  - Clear naming conventions
  - No utils/ dumping ground
- **Measurement**: Code review + linting rules

**NFR-M-003: Testing Coverage**
- **Definition**: Percentage of code covered by tests
- **Target**: ≥ 85% overall coverage
- **Breakdown**:
  - Domain aggregates: ≥ 95% (critical)
  - Services: ≥ 90% (critical)
  - Repositories: ≥ 85% (important)
  - React components: ≥ 70% (UI logic)
- **Test Pyramid**:
  - Unit tests: 70% (fast, isolated)
  - Integration tests: 20% (service + repo)
  - E2E tests: 10% (full flow)
- **Acceptance Criteria**:
  - Coverage enforced in CI/CD
  - Every aggregate has test suite
  - Happy path + edge cases covered
  - Error scenarios tested
- **Measurement**: Istanbul coverage report

**NFR-M-004: Documentation**
- **Definition**: Code-level and design documentation
- **Target**: Self-documenting code + architecture docs
- **Documentation Types**:
  - Docstrings: Every public method has 1-2 line summary
  - README: Architecture overview + setup instructions
  - ADRs: Architecture decisions (ADR-001 to ADR-018)
  - Diagrams: Sequence diagrams for main flows
  - Comments: Only for non-obvious logic (why, not what)
- **Acceptance Criteria**:
  - README is current and accurate
  - No outdated comments
  - Docstrings exist for all public APIs
  - Architecture is documented (not assumed)
- **Measurement**: Documentation review + link checker

**NFR-M-005: Technical Debt Management**
- **Definition**: Code quality and debt level
- **Target**: Low debt, technical health score ≥ 80%
- **Debt Monitoring**:
  - Cyclomatic complexity: Max 10 per function
  - Code smells: < 5 per 1000 LOC
  - Deprecations: None used
  - TODOs: Resolved within 2 sprints
- **Health Checks**:
  - SonarQube: Quality gate A
  - ESLint: 0 errors (max 10 warnings)
  - TypeScript strict mode: Enabled
- **Acceptance Criteria**:
  - Debt ratio monitored in CI/CD
  - Refactoring sprints planned if debt > 20%
  - No shortcuts (no "ignore" flags)
- **Measurement**: SonarQube metrics

---

### 6. SCALABILITY (200-500 Inspectors, 5k records/device, prepared for 1000+)

**NFR-SC-001: Concurrent Inspectors**
- **Definition**: Number of inspectors syncing simultaneously
- **Phase 1 Target**: 200-500 concurrent inspectors
- **Phase 2 Target** (future): 1000+ inspectors
- **Acceptance Criteria (Phase 1)**:
  - 500 concurrent connections to API (via load balancer)
  - No sync failures due to server capacity
  - API response time: < 1 second p95
  - Server utilization: < 70% at 500 concurrent
- **Acceptance Criteria (Phase 2)**:
  - 2000 concurrent connections
  - Sync sharding: Distribute across multiple API instances
  - Queue batching: Prevent thundering herd
- **Measurement**: Load testing (k6, Gatling)

**NFR-SC-002: Local Storage Capacity**
- **Definition**: Amount of data stored offline per device
- **Phase 1 Target**: 5,000 records max per device (5MB IndexedDB)
- **Phase 2 Target**: 10,000 records (10MB IndexedDB)
- **Breakdown**:
  - Cached masters: 1000 records (~2MB)
  - Inspection history: 4000 records (~3MB)
  - Metadata: 100KB
- **Acceptance Criteria**:
  - Storage quota enforcement: Warn at 40MB, block at 50MB
  - LRU eviction: Remove oldest records if quota exceeded
  - Storage monitoring: User can see available space
- **Measurement**: IndexedDB size monitoring

**NFR-SC-003: Sync Payload Optimization**
- **Definition**: Data sent per sync operation
- **Phase 1 Target**: < 8MB per batch
- **Phase 2 Target**: < 20MB per batch (differential sync)
- **Optimization Strategies**:
  - Batching: Group 10 items per batch
  - Compression: Gzip payloads (Phase 2)
  - Filtering: Only changed fields (Phase 2)
  - Delta sync: Only send deltas (Phase 2)
- **Acceptance Criteria**:
  - Average payload: 500KB-1MB per item
  - Photo compression: JPEG with quality=85
  - Metadata stripped: No server-side data in payload
- **Measurement**: Network waterfall analysis

**NFR-SC-004: Sync Queue Performance**
- **Definition**: Processing speed of sync queue
- **Phase 1 Target**: Process 100 items/minute
- **Phase 2 Target**: Process 500 items/minute (with optimization)
- **Acceptance Criteria**:
  - Queue processing: FIFO order maintained
  - Throughput: At least 100 items/minute
  - Latency: < 3 seconds per item
  - Memory: < 100MB for 1000-item queue
- **Measurement**: Benchmarks (queue throughput test)

**NFR-SC-005: Future-Proofing**
- **Definition**: Architecture can scale to 1000+ inspectors
- **Phase 1 Design** (not implemented):
  - Selective sync: Client can filter what to cache
  - Pagination: Masters fetched page-by-page (50 items/page)
  - Differential sync: Send only changed fields
  - Sharding: API can distribute across instances
- **Acceptance Criteria**:
  - No architectural changes needed for Phase 2
  - Interfaces designed for optional features
  - Database can handle indexed queries on 10k records
  - Service Worker can handle concurrent operations
- **Measurement**: Scalability design review

---

## 📊 SUMMARY TABLE

| Attribute | Priority | Target | Status |
|-----------|----------|--------|--------|
| **Performance** | HIGH | < 3s sync, < 8MB | ✅ Specified |
| **Reliability** | CRITICAL | 99.5% success, 80% auto-resolve | ✅ Specified |
| **Security** | CRITICAL | Selective encryption, HTTPS only | ✅ Specified |
| **Usability** | HIGH | Offline read-only, clear status | ✅ Specified |
| **Maintainability** | MEDIUM | Full DDD, 85% coverage | ✅ Specified |
| **Scalability** | MEDIUM | 200-500 inspectors, prepared for 1000+ | ✅ Specified |

---

## 🔗 TRACEABILITY TO BUSINESS RULES

| NFR | Business Rules |
|-----|-----------------|
| P-001 to P-005 | BR-031 (queue order), BR-038 (timeout), BR-048 (rate limit) |
| R-001 to R-005 | BR-006 to BR-010 (retry), BR-011 to BR-020 (conflicts) |
| S-001 to S-005 | SR-001 to SR-008 (security rules) |
| U-001 to U-005 | BR-001 to BR-004 (offline mode), BR-036 (visibility) |
| M-001 to M-005 | Architecture decisions (ADRs) |
| SC-001 to SC-005 | BR-027 (network quality), BR-033 (queue limits) |

---

**Status**: 🎯 **NFR REQUIREMENTS COMPLETE (30 specifications)**  
**Next**: Generate Business-Logic-Model.md with use cases and workflows  
**Integration**: Each NFR traces to business rules and implementation requirements
