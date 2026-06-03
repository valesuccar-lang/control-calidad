# Activity 2: NFR Requirements — Unit 3 (Maestros y Configuración)

**Date**: 2026-06-01  
**Unit**: Maestros y Configuración (Masters & Configuration Domain)  
**Scope**: Non-Functional Requirements for master data management CRUD and CSV import workflows  
**Audience**: Architects, Developers, QA Engineers  

---

## 📋 EXECUTIVE SUMMARY

The Masters & Configuration unit handles creation and maintenance of reference data (Defects, Machines, Fabrics) that define the inspection domain. This unit serves administrators and must balance three competing priorities:

1. **High Performance**: CSV imports processing 100+ rows/second without blocking operations
2. **Security**: Strict role-based access (Admins only) with complete audit trails
3. **Reliability**: Data consistency guarantees during bulk imports and concurrent edits

This document captures the non-functional requirements elicited from stakeholder analysis and translates them into measurable criteria for design and implementation.

---

## 🎯 QUALITY ATTRIBUTES & REQUIREMENTS

### 1. PERFORMANCE

**Strategic Goal**: Enable administrators to bulk-import and manage thousands of masters without operational slowdown.

#### 1.1 CRUD Operations (Synchronous)

| Requirement | Specification | Rationale |
|-------------|---------------|-----------|
| **Create Master** | ≤ 200 ms per operation (p95) | Admin doesn't perceive lag; form submission feels responsive |
| **Read/List Masters** | ≤ 150 ms for 1000+ items (paginated) | List view with pagination remains interactive |
| **Update Master** | ≤ 200 ms per operation (p95) | Edit form submission completes quickly |
| **Archive Master** | ≤ 150 ms per operation (p95) | Soft-delete is lightweight; no cascading deletes |

**Constraints**:
- All times measured from API gateway to response
- Network latency (50 ms typical) not included in SLA
- Database query must use proper indexes (name, status, created_at)

**Measurement Method**: Apache Bench or Locust load testing; measure p50, p95, p99 latencies

---

#### 1.2 CSV Import (Asynchronous Background Job)

| Requirement | Specification | Rationale |
|-------------|---------------|-----------|
| **Import Throughput** | ≥ 100 rows/second (with validation) | Importing 10k defects takes < 2 minutes |
| **Total Time to Sync** | < 3 minutes for 10,000 rows | Admin can monitor progress without waiting |
| **Memory Usage** | ≤ 200 MB peak (10k row import) | No OOM errors on standard server (4GB available) |
| **Disk Space** | ≤ 50 MB per import attempt | Temporary files cleaned up after success/failure |

**Constraints**:
- CSV processing runs asynchronously (background queue job)
- Import doesn't block other CRUD operations
- Progress reported in real-time to UI (WebSocket or polling)

**Measurement Method**:
- Time end-to-end import with `time` command
- Monitor process memory with `ps` or application profiler
- Count rows processed per second in logs

---

#### 1.3 Search & Filtering

| Requirement | Specification | Rationale |
|-------------|---------------|-----------|
| **Search Response** | ≤ 100 ms for 5000 masters (in-memory cache) | Filter by name is instant for admins |
| **Filter by Status** | ≤ 50 ms (active/archived) | Toggle views without lag |
| **Sort by Usage Count** | ≤ 150 ms (requires aggregation) | "Most used defects" report is reasonable |

**Constraints**:
- Implement Redis cache for frequently accessed masters
- Cache TTL = 1 hour (rebuild on import completion)
- Partial string search (name prefix) supported

---

#### 1.4 Reporting (Analytics)

| Requirement | Specification | Rationale |
|-------------|---------------|-----------|
| **Usage Report** | ≤ 2 seconds per report | Admin doesn't wait long for insights |
| **Export to Excel** | ≤ 5 seconds for 5000 rows | Excel generation with formatting acceptable |
| **Non-blocking** | Report generation doesn't impact inspection workflow | Background task, no correlation to inspection speed |

---

### 2. SECURITY

**Strategic Goal**: Ensure only authorized personnel modify critical master data; maintain complete audit trail of all changes.

#### 2.1 Authentication & Authorization

| Requirement | Specification | Rationale |
|-------------|---------------|-----------|
| **Role-Based Access** | Only `ADMIN` role can create/update/delete masters | Non-admins (OPERARIO, JEFE_QA) are read-only |
| **JWT Tokens** | Same as Unit 2 (8h expiration, httpOnly cookies) | Consistency across system |
| **API Endpoint Protection** | All POST/PATCH/DELETE routes require `Authorization: Bearer <token>` | No unauthenticated requests possible |
| **Missing Permissions** | HTTP 403 Forbidden for non-admin attempts | Clear error; logged as security event |

**Constraints**:
- No API key-based access (JWT only)
- No hardcoded admin credentials
- Admin role checked server-side (never trust client claims)

---

#### 2.2 Audit Trail (Change Log)

| Requirement | Specification | Rationale |
|-------------|---------------|-----------|
| **Log All Changes** | Every create/update/archive logged with: WHO, WHEN, WHAT, OLD_VALUE, NEW_VALUE | Full traceability for compliance |
| **Tamper-Proof** | Audit logs immutable; no update/delete after creation | Historical accuracy guaranteed |
| **Retention Policy** | Keep audit logs for ≥ 2 years | Regulatory compliance (if needed) |
| **Query Audit** | Admins can search: "who changed defect X?", "what changed on 2026-05-01?" | Operational visibility |

**Implementation**:
- Separate `audit_log` table in PostgreSQL
- Triggers or ORM hooks to auto-log on insert/update
- No manual audit entry possible

---

#### 2.3 System Masters Protection

| Requirement | Specification | Rationale |
|-------------|---------------|-----------|
| **System Defects** | Defects with `is_system=true` cannot be modified or deleted | Prevents accidental corruption of "No Especificado" etc. |
| **Clear Marking** | UI clearly shows "System" badge on protected masters | Admin won't attempt to edit |
| **API Validation** | Attempt to update/delete system master returns HTTP 400 + clear error | No silent ignoring of requests |

**System Masters Example**:
- Defect: "No Especificado" (id=SYS-001)
- Machine: "No Aplica" (id=SYS-M01)
- Fabric: "No Especificado" (id=SYS-F01)

---

#### 2.4 CSV Import Security

| Requirement | Specification | Rationale |
|-------------|---------------|-----------|
| **File Validation** | Validate: file type (CSV), encoding (UTF-8), size (≤ 100 MB) | Prevent injection, resource exhaustion |
| **Header Validation** | CSV must have exact columns: name, description, ... | Malformed CSVs rejected before processing |
| **Data Sanitization** | All text fields trimmed, SQL injection patterns blocked | Security hardening |
| **Duplicate Detection** | Reject import if master with same name already exists (or flag for review) | Prevent accidental duplicates |
| **Rollback on Failure** | If any row fails validation, entire import rolls back or partially commits (configurable) | Consistent state after import |

---

### 3. RELIABILITY

**Strategic Goal**: Guarantee that master data remains consistent and valid even during failures or concurrent operations.

#### 3.1 CSV Import Consistency

| Requirement | Specification | Rationale |
|-------------|---------------|-----------|
| **Atomicity** | Either ALL rows imported successfully, OR none (transactional) | No partial/corrupt state |
| **Rollback on Error** | If row 5000 of 10000 fails validation, all changes rolled back | Easier for admin to fix CSV and retry |
| **Partial Import Mode** | Optional: Accept valid rows, skip invalid rows, report errors | Useful for large imports with scattered bad data |
| **Error Report** | Detailed report: "Row 47: 'name' field is empty", "Row 123: Duplicate of existing Defect XYZ" | Admin knows exactly what to fix |

**Constraints**:
- Use database transactions (PostgreSQL BEGIN/COMMIT/ROLLBACK)
- Transaction timeout: 5 minutes (abort if CSV processing > 5 min)
- No nested transactions allowed

---

#### 3.2 Operational Change Prevention

| Requirement | Specification | Rationale |
|-------------|---------------|-----------|
| **Immutable Active Masters** | Cannot archive a Defect that was used in inspections in last 7 days | Recent data remains valid |
| **Dependency Check** | Before archiving Machine X, verify no active inspections reference it | Inspections won't break |
| **Cascading Validation** | If Defect is archived, ensure no "pending approval" inspections depend on it | Approvals workflow won't have gaps |

**Validation Rules** (from domain-entities.md):

**Defect Archival**:
- Check: Has usage in last 7 days? If YES → reject archive
- Check: Has "pending approval" inspections? If YES → reject archive
- Allow archive only if: (1) No recent usage AND (2) No pending inspections

**Machine Archival**:
- Similar logic as Defect

---

#### 3.3 Concurrent Edit Protection

| Requirement | Specification | Rationale |
|-------------|---------------|-----------|
| **Optimistic Locking** | Include `version` field in Master; increment on update | Detect concurrent edits |
| **Conflict Resolution** | If admin A and B both edit Defect X, B's request rejected with: "Defect was modified since you loaded it. Refresh and retry" | Clear guidance to user |
| **No Silent Overwrites** | Never silently overwrite another user's changes | Data integrity preserved |

**Implementation**:
- Add `version: Int` column to defects/machines/fabrics tables
- Check version on UPDATE; if mismatch, return HTTP 409 Conflict

---

#### 3.4 Failure Recovery

| Requirement | Specification | Rationale |
|-------------|---------------|-----------|
| **Import Crash** | If backend crashes mid-import, state returns to pre-import (no partial data) | Admin can retry after restart |
| **Network Interruption** | If upload interrupted, server cleans temp file; admin can retry | No orphaned temp files |
| **Retry Strategy** | Admin can retry failed import with same CSV; system detects new duplicates correctly | Retry is safe |

**Constraints**:
- All file writes to temporary location first
- Move to permanent location only after success
- Cleanup of orphaned temp files daily (scheduled job)

---

### 4. USABILITY

**Strategic Goal**: Make master data management accessible to non-technical administrators; guide them through complex CSV imports.

#### 4.1 CRUD Interface (UI/UX)

| Requirement | Specification | Rationale |
|-------------|---------------|-----------|
| **Consistent CRUD Pattern** | For each master type (Defect, Machine, Fabric): List → Create → Edit → Archive | Admin learns one pattern, applies to all |
| **List View** | Table with columns: ID, Name, Status (Active/Archived), Used Count, Last Modified, Actions (Edit, Archive) | Full visibility |
| **Search Box** | Single search field filters by Name in real-time | Quick lookup |
| **Pagination** | Show 20 rows/page; clearly show "Page X of Y", total count | No overwhelming lists |
| **Create Form** | Simple form with validation: Required fields marked, inline error messages | Clear what's needed |
| **Edit Modal** | Pop-over or new page; confirm before saving | Review changes before commit |
| **Archive Button** | Confirmation dialog: "Archive Defect XYZ? Inspections using it will still be valid." | Prevent accidental deletes |

**Success Criteria**:
- Admin can list 100 defects in < 2 seconds
- Admin can create new defect in < 30 seconds (including typing)
- Admin can edit existing defect in < 20 seconds

---

#### 4.2 CSV Import Wizard

| Requirement | Specification | Rationale |
|-------------|---------------|-----------|
| **Step 1: Select File** | File input with preview; show: file name, size, # rows detected | Clear what's being imported |
| **Step 2: Validate** | Auto-validate CSV format; show: "✓ Header OK", "✓ All rows have 5 columns", "⚠ 2 duplicate names found" | Admin knows issues before import |
| **Step 3: Review Changes** | Show summary: "3 new defects, 5 updates, 1 skip (duplicate)" with detail table | Admin approves before writing to DB |
| **Step 4: Confirm & Import** | Final confirmation button; show progress bar during import; completion time estimate | Admin sees what's happening |
| **Step 5: Results** | Import report: "Successfully imported 8/10 rows. 2 rows failed. See error details below." | Clear outcome |

**Error Display**:
- Show each error with row number and reason: "Row 5: Name 'XXX' is empty"
- Link to download error report (CSV with errors)
- Option to fix and retry

---

#### 4.3 Search & Filter Experience

| Requirement | Specification | Rationale |
|-------------|---------------|-----------|
| **Filter by Status** | Toggle button: "Active / Archived / All" | Quick view switching |
| **Search by Name** | Real-time search; starts filtering as user types | No need to click "Search" button |
| **Sort by Column** | Clickable column headers; show ↑ ↓ arrows | Expected behavior |
| **Clear Filters** | "Clear All" button; shows current active filters | Easy reset |

---

#### 4.4 Undo & Recovery

| Requirement | Specification | Rationale |
|-------------|---------------|-----------|
| **Undo Recent Actions** | Toast notification after archive: "Archived Defect X • [Undo]" (active for 30 sec) | User can quickly undo mistakes |
| **Restore Archived Masters** | In list view, option to "Unarchive" archived items (if no conflicts) | Recovery is possible |
| **Undo Depth** | Support undo for last 5 actions | Reasonable safety net without complexity |

**Constraints**:
- Undo uses database transactions (rollback)
- Must respect audit trail (log the undo as new change)

---

### 5. MAINTAINABILITY

**Strategic Goal**: Enable developers to understand, test, and modify the codebase with confidence.

#### 5.1 Code Organization & Modularity

| Requirement | Specification | Rationale |
|-------------|---------------|-----------|
| **Service Layer** | MastersService encapsulates all business logic (validations, archival rules, etc.) | Single source of truth |
| **Repository Pattern** | DefectRepository, MachineRepository, FabricRepository abstract DB details | Easy to swap implementations (mock for tests) |
| **Domain Events** | DefectCreatedEvent, DefectUpdatedEvent published after DB writes | Decoupled from other services |
| **Clear Separation** | Routes (HTTP) → Services (business logic) → Repositories (data access) | Each layer has single responsibility |

**Constraints**:
- No business logic in routes (no if-else statements in endpoints)
- No direct database queries in services (use repositories)
- No HTTP concerns in repositories (no response codes)

---

#### 5.2 Testing Strategy

| Requirement | Specification | Rationale |
|-------------|---------------|-----------|
| **Unit Tests** | 90%+ coverage of MastersService methods (create, update, archive, CSV import logic) | Catch bugs before production |
| **Repository Tests** | 80%+ coverage of CRUD + special queries (by_name, recent_usage, etc.) | Verify database interactions |
| **Integration Tests** | Test CSV import end-to-end with real DB; verify rollback behavior | Real-world scenarios |
| **API Tests** | Test all endpoints with valid/invalid inputs, permission checks | HTTP contract validation |

**Test Framework**: pytest for backend; each test < 200 ms (except integration tests)

---

#### 5.3 Logging & Debugging

| Requirement | Specification | Rationale |
|-------------|---------------|-----------|
| **Structured Logging** | All operations logged in JSON format with: timestamp, operation, user_id, master_id, status | Easy to parse and search in logs |
| **Error Context** | When CSV import fails, log entire row data (sanitized) + validation error reason | Easier to debug customer issues |
| **Trace IDs** | Each import gets unique trace_id; all related logs include this ID | Correlate logs for single operation |

**Log Levels**:
- INFO: Successful CRUD operations, import start/completion
- WARN: Archive with lingering references, near-duplicate names
- ERROR: Validation failures, database errors

---

#### 5.4 Documentation

| Requirement | Specification | Rationale |
|-------------|---------------|-----------|
| **Business Rules Doc** | Document why archive fails, when masters are immutable, CSV format spec | New developers understand domain |
| **API Documentation** | OpenAPI/Swagger for all endpoints: /masters/defects GET/POST/PATCH/DELETE | Clear contracts |
| **CSV Format Spec** | Document required columns, data types, constraints (e.g., name length ≤ 100) | Admin understands import format |
| **Architecture Decisions** | Why optimistic locking for concurrent edits, why transactional imports | Rationale captured |

---

### 6. SCALABILITY

**Strategic Goal**: Ensure the system grows with the organization without requiring architectural redesign.

#### 6.1 Data Volume

| Requirement | Specification | Rationale |
|-------------|-------------|-----------|
| **Master Count** | System must support ≥ 5000 masters per type (defects, machines, fabrics) | Growth from 10 to 50+ sites |
| **Response Time** | CRUD operations remain ≤ 200 ms even with 5000+ masters | List view paginated; indexes on name/status |
| **List Performance** | Loading page with 5000 items (paginated 20/page) = ≤ 150 ms | Pagination + caching |
| **CSV Import Time** | Importing 5000 rows still ≤ 1 minute | Batch processing, not sequential |

**Implementation**:
- Database indexes: `(name)`, `(status, created_at)`, `(is_active)`, `(usage_count DESC)`
- Redis cache for list queries
- Pagination enforced (no "load all" API)

---

#### 6.2 Concurrent Administrators

| Requirement | Specification | Rationale |
|-------------|---------------|-----------|
| **Simultaneous Edits** | 5+ admins can edit different masters concurrently without blocking each other | No artificial serialization |
| **Connection Pool** | Database connection pool ≥ 20 (5 admins × 4 concurrent requests) | No connection starvation |
| **Lock Strategy** | Optimistic locking (version field); no pessimistic locks (no table locks) | Maximize concurrency |
| **Conflict Rate** | < 5% of edits result in conflict (statistically). Admin retries are acceptable | Rare enough for human retry workflow |

---

#### 6.3 Bulk Import Scalability

| Requirement | Specification | Rationale |
|-------------|-------------|-----------|
| **Large CSV Files** | Support imports of 10,000+ rows without timeout or OOM | Minimal file splits needed by admins |
| **Background Processing** | Import runs as background job (Celery, RQ, APScheduler) | Doesn't block HTTP server |
| **Progress Tracking** | Admin can check import status without re-submitting; real-time progress bar | Transparency during long import |
| **Cancellation** | Admin can cancel in-progress import; system cleans up and rolls back | No hung imports |

---

#### 6.4 Extensibility (New Master Types)

| Requirement | Specification | Rationale |
|-------------|-------------|-----------|
| **Add New Master Type** | Adding "Suppliers" or "Chemical Processes" requires: 1 new model, 1 service method, 1 API endpoint (< 2 hours) | Minimal code duplication |
| **Shared CSV Logic** | CSV parsing/validation logic reusable for new master types | DRY principle |
| **Shared Frontend** | CRUD UI components work for any master type (dynamic) | One component, many uses |

**Constraints**:
- All master types follow same structure: id, name, status, created_at, updated_at, is_system
- CSV column order irrelevant (header-driven parsing)

---

## 📊 CONSTRAINTS & ASSUMPTIONS

### Technical Constraints

| Constraint | Value | Impact |
|-----------|-------|--------|
| **Database** | PostgreSQL 12+ | JSON logging, JSONB audit trail possible |
| **Backend Framework** | FastAPI | Async background tasks via Celery or APScheduler |
| **Authentication** | JWT + httpOnly cookies | Consistent with Unit 2 (Frontend) |
| **File Storage** | Filesystem (no S3) | Imports saved to /data/uploads/ on server |
| **CSV Processing** | Synchronous read, async write | User uploads CSV → backend processes async |

### Business Constraints

| Constraint | Value | Impact |
|-----------|-------|--------|
| **User Base** | 2-5 administrators | Peak concurrent load = 5 admins; connection pool = 20 is sufficient |
| **Deployment** | Single server on-premises | No distributed transaction complexity; single point of failure acceptable |
| **Data Retention** | Masters kept indefinitely; archival ≠ deletion | Soft-delete strategy; audit trail 2+ years |
| **Compliance** | Internal tool, no GDPR/HIPAA | Audit trail for operational visibility, not legal requirement |

### Assumptions

1. **CSV Format Stable**: Admin templates don't change frequently; new columns added via backcompat (ignore unknown columns)
2. **Import Frequency Low**: CSV imports happen < 1x per week; not batch-heavy system
3. **Master Count Predictable**: Will not grow to 100k+ items (textile defects unlikely to exceed 10k)
4. **Admin Skill Level**: Basic CSV knowledge; can follow wizard step-by-step
5. **Network Reliable**: On-premises; low latency; not expecting frequent disconnects

---

## ✅ ACCEPTANCE CRITERIA

### For Design Phase (Activity 3)

- [ ] **Performance ADR**: Decision on caching strategy (Redis vs. in-memory), CSV background job framework (Celery vs. APScheduler)
- [ ] **Security ADR**: Audit log structure, JWT role checking strategy, system master protection mechanism
- [ ] **Reliability ADR**: Transaction handling for CSV, optimistic locking implementation, rollback strategy
- [ ] **Usability ADR**: UI framework decisions (React component library), CSV wizard architecture
- [ ] **Architecture Diagrams**: Data flow for CSV import, CRUD operations, audit logging

### For Implementation Phase (Activity 5)

- [ ] **Performance Testing**: CRUD operations measured at < 200 ms (p95) with 5000 masters
- [ ] **CSV Import Test**: 10,000 row import completes in < 1 minute
- [ ] **Security Audit**: 100% of CRUD endpoints require ADMIN role; all changes logged
- [ ] **Concurrent Edit Test**: 5 admins editing different masters simultaneously; no conflicts
- [ ] **UI Acceptance**: Admin imports 100-row CSV successfully in < 5 minutes (wizard walkthrough)
- [ ] **Code Coverage**: MastersService and repositories ≥ 90% test coverage

### For Testing Phase (Activity 6)

- [ ] **Load Test**: 20 concurrent requests (4 admins × 5 requests); response time ≤ 500 ms (p95)
- [ ] **Failure Recovery**: Simulate network interruption during import; verify rollback
- [ ] **Audit Trail**: Verify all changes logged with user, timestamp, old/new values
- [ ] **System Master Protection**: Attempt to delete "No Especificado" → rejected with HTTP 400
- [ ] **Archive Validation**: Attempt to archive defect with pending inspections → rejected
- [ ] **CSV Error Handling**: Upload malformed CSV; verify clear error report, no partial import

---

## 🔗 REFERENCES

- **Related Documents**:
  - [domain-entities.md](../activity-1-functional-design/domain-entities.md) — Bounded context, aggregates, domain services
  - [NFR-Design-Consolidated.md](../../frontend-web\ unidad\ 2/activity-3-nfr-design/NFR-Design-Consolidated.md) — Frontend NFR for consistency
  - [Infrastructure-Design-Services.md](../../frontend-web\ unidad\ 2/activity-4-infrastructure-design/Infrastructure-Design-Services.md) — Backend service specifications

- **External References**:
  - PostgreSQL Documentation: Indexing strategy, transaction isolation
  - FastAPI Background Tasks: https://fastapi.tiangolo.com/tutorial/background-tasks/
  - CSV Format: RFC 4180 (Comma-Separated Values)

---

**Status**: ✅ **ACTIVITY 2 COMPLETE**  
**Next Step**: Activity 3 — NFR Design (ADRs for caching, audit trail, CSV processing)  
**Recommendation**: Start with Security ADR (audit trail structure) and Reliability ADR (transaction handling)
