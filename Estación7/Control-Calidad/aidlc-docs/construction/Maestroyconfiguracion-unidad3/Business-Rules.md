# Business Rules — Unit 3 (Maestros y Configuración)

**Date**: 2026-06-01  
**Unit**: Maestros y Configuración (Masters & Configuration Domain)  
**Scope**: Domain rules, validation constraints, and operational policies  
**Audience**: Developers, QA Engineers, Business Analysts  

---

## 📌 OVERVIEW

This document specifies the business rules that govern the creation, modification, and archival of master data (Defects, Machines, Fabrics). These rules ensure data consistency, prevent operational issues, and protect critical system configuration.

Rules are enforced at:
1. **Service Layer** (MastersService): Business logic validation
2. **Repository Layer**: Database constraints (unique indexes, foreign keys)
3. **API Layer** (routes): HTTP contract enforcement
4. **Database Layer**: Check constraints, triggers

---

## 🎯 MASTER CREATION RULES

### Defect Creation

**Rule 1.1: Defect Name Uniqueness**
- **Statement**: No two active defects can have the same name (case-insensitive)
- **Validation Point**: MastersService.create_defect() checks `exists_by_name(name)`
- **Error Response**: HTTP 409 Conflict | Message: "Defect '{name}' already exists"
- **Rationale**: Inspection technician selects from dropdown; duplicates cause confusion
- **Implementation**: Unique index on `defects(LOWER(name))` in PostgreSQL

**Rule 1.2: Name Length & Characters**
- **Statement**: Defect name must be 3-100 characters; alphanumeric + spaces/hyphens/underscores only
- **Validation Pattern**: `^[a-zA-Z0-9\s\-_]{3,100}$`
- **Error Response**: HTTP 400 Bad Request | Message: "Name must be 3-100 characters, alphanumeric only"
- **Rationale**: Prevents SQL injection, truncation in UI, and nonsensical entries
- **Implementation**: Regex validation in service + database check constraint

**Rule 1.3: Description Optional but Validated**
- **Statement**: Description is optional; if provided, max 500 characters
- **Validation**: Length check only; no format restrictions
- **Rationale**: Freeform text field; length prevents abuse
- **Implementation**: Database column VARCHAR(500), optional

**Rule 1.4: Typical Process Valid Values**
- **Statement**: Typical process must be one of: {TEÑIDO, ESTAMPADO, ACABADO, OTRA}
- **Enum**: ProcessType in code
- **Validation Point**: Validate at service layer before DB insert
- **Error Response**: HTTP 400 Bad Request | Message: "Invalid process '{value}'. Allowed: TEÑIDO, ESTAMPADO, ACABADO, OTRA"
- **Rationale**: Constrains to known manufacturing processes; enables aggregation reports
- **Implementation**: ENUM type in PostgreSQL or lookup table with FK

**Rule 1.5: Typical Machine Reference (Optional)**
- **Statement**: If `typical_machine_id` provided, machine must exist and be active
- **Validation Point**: Repository.get_machine(typical_machine_id) must return non-null
- **Error Response**: HTTP 400 Bad Request | Message: "Machine with ID '{id}' not found or archived"
- **Rationale**: Prevents orphaned references; helps QA suggest "typical" machine for this defect
- **Implementation**: Foreign key constraint `defects.typical_machine_id → machines.id`

**Rule 1.6: Initial Status = ACTIVE**
- **Statement**: All newly created defects must have `status = ACTIVE`
- **Implementation**: Default value in service; never accept `status` parameter on POST
- **Rationale**: Archival is separate workflow; creation = activation

**Rule 1.7: Audit Metadata Auto-Set**
- **Statement**: `created_at`, `created_by`, `updated_at`, `updated_by` auto-populated
- **created_by**: From JWT token (user_id of admin making request)
- **created_at**: Server timestamp (UTC)
- **Rationale**: Automatic tracking; no user tampering
- **Implementation**: ORM model with datetime.utcnow() and request context

---

### Machine Creation

**Rule 1.8: Machine Name Uniqueness**
- **Statement**: No two active machines can have the same name (case-insensitive)
- **Validation**: Similar to Defect 1.1
- **Unique Index**: `machines(LOWER(name))`

**Rule 1.9: Machine Process Valid Values**
- **Statement**: `process` must be one of: {TEÑIDO, ESTAMPADO, ACABADO}
- **Validation**: Service layer enum check
- **Rationale**: Narrower than defect processes; not all machines do all processes

**Rule 1.10: Manufacturer & Model Optional**
- **Statement**: `manufacturer` and `model` are optional; if provided, max 100 chars each
- **Rationale**: Some machines lack clear manufacturer info; optional to prevent blockers

**Rule 1.11: Installation Date Optional**
- **Statement**: `installation_date` optional; if provided, must be ≤ today
- **Validation**: `installation_date <= DATE(today)`
- **Error Response**: HTTP 400 Bad Request | Message: "Installation date cannot be in the future"
- **Rationale**: Data sanity; prevents nonsensical future dates

---

### Fabric Creation

**Rule 1.12: Fabric Name Uniqueness**
- **Statement**: No two active fabrics can have the same name (case-insensitive)
- **Validation**: Similar to Defect 1.1

**Rule 1.13: Composition Format**
- **Statement**: `composition` is required; format: "Cotton 50%, Polyester 50%" or "100% Polyester"
- **Validation Pattern**: `^\d+%\s+[a-zA-Z\s\-]+(\s*,\s*\d+%\s+[a-zA-Z\s\-]+)*$`
- **Error Response**: HTTP 400 Bad Request | Message: "Composition format invalid. Example: 'Cotton 60%, Polyester 40%'"
- **Rationale**: Consistency for reporting; helps defect analysis by fiber type

**Rule 1.14: Width & Weight Constraints**
- **Statement**: 
  - `width_cm` required; valid range: 10-300 cm
  - `weight_gsm` required; valid range: 50-1000 g/m²
- **Validation**: Range checks at service layer
- **Error Response**: HTTP 400 Bad Request | Message: "Width must be 10-300 cm; Weight must be 50-1000 g/m²"
- **Rationale**: Physical constraints; prevents nonsensical fabric specs; enables QA filtering by similar fabrics

---

## 🔄 MASTER UPDATE RULES

### Defect Update

**Rule 2.1: System Defects Immutable**
- **Statement**: Defects with `is_system = true` cannot be updated (all fields read-only)
- **System Defects**: 
  - DEF-SYS-001: "No Especificado"
  - DEF-SYS-002: "Defecto Genérico"
- **Validation Point**: Service checks `defect.is_system` before allowing PATCH
- **Error Response**: HTTP 400 Bad Request | Message: "Cannot modify system defect '{name}'"
- **Rationale**: Prevents accidental corruption of fallback/placeholder entries
- **Implementation**: Guard clause in update_defect() service method

**Rule 2.2: Name Change Subject to Uniqueness**
- **Statement**: When updating name, must check new name doesn't collide with other defects
- **Validation**: `exists_by_name(new_name, exclude_id=current_id)` returns false
- **Error Response**: HTTP 409 Conflict | Message: "Defect '{new_name}' already exists"
- **Rationale**: Same as creation rule; prevent duplicates via update path

**Rule 2.3: Only Updateable Fields**
- **Statement**: Admin can only update: `name`, `description`, `typical_process`, `typical_machine_id`
- **Immutable Fields**: `id`, `status`, `created_by`, `created_at`
- **Validation Point**: Service ignores other fields; API schema only accepts updateable fields
- **Rationale**: Prevents accidental/malicious overwrites of critical metadata

**Rule 2.4: Optimistic Locking (Version Check)**
- **Statement**: PATCH request must include `version` field; must match current DB version
- **Header/Body**: `"version": 3` (current version from GET)
- **Update Action**: Increment version by 1; save new version
- **Error Response**: HTTP 409 Conflict | Message: "Defect was modified by another user. Refresh and retry"
- **Rationale**: Detect concurrent edits; prevent silent overwrites
- **Implementation**: 
  ```sql
  UPDATE defects 
  SET name = ?, version = version + 1, updated_at = NOW(), updated_by = ? 
  WHERE id = ? AND version = ?
  -- If no rows affected: return 409
  ```

**Rule 2.5: Status Transition (Archive Only)**
- **Statement**: Admin cannot directly PATCH `status`. Status changes via dedicated archive endpoint
- **Current States**: ACTIVE → ARCHIVED (no other transitions)
- **Rationale**: Encapsulate complex archive logic in service method; prevent direct status manipulation

---

### Machine & Fabric Update

**Rules 2.6-2.8**: Similar to Defect (uniqueness, system immutability, versioning, field constraints)

**Rule 2.9: Prevent Modification of Active Machines (Inspection Context)**
- **Statement**: If machine has active inspections (status = PENDING_APPROVAL or APPROVED), cannot update `process`
- **Validation**: Service queries: `SELECT COUNT(*) FROM inspections WHERE machine_culpable_id = ? AND status IN (PENDING_APPROVAL, APPROVED)`
- **If Count > 0**: Reject update with HTTP 400 | Message: "Cannot change process; machine has {count} active inspections"
- **Rationale**: Prevent data inconsistency; inspection records the machine's process at capture time

---

## 🗂️ MASTER ARCHIVAL RULES

### Defect Archival

**Rule 3.1: Archive (Soft Delete) Only**
- **Statement**: No hard deletes. Archival = set `status = ARCHIVED`
- **Archived Defects**: Still queryable, but filtered out in normal lists (shown separately)
- **Rationale**: Preserves historical data; inspections created with "Roto" defect should still reference it
- **Implementation**: All queries filter: `WHERE is_system = false OR status = 'ACTIVE'` (or allow explicit include_archived flag)

**Rule 3.2: Cannot Archive If Recent Usage**
- **Statement**: Cannot archive defect if used in inspections in the last **7 days**
- **Validation Logic**:
  ```sql
  SELECT COUNT(*) FROM inspections 
  WHERE defect_type_id = ? 
  AND created_at >= (NOW() - INTERVAL '7 days')
  ```
- **If Count > 0**: Reject archive with HTTP 400 | Message: "Cannot archive; defect was used {count} times in last 7 days"
- **Rationale**: Prevents inspection data from referencing archived masters; allows investigation period
- **Configurable**: 7-day window can be adjusted in config

**Rule 3.3: Cannot Archive If Pending Approvals**
- **Statement**: Cannot archive defect if inspections with that defect await approval (status = PENDING_APPROVAL)
- **Validation**:
  ```sql
  SELECT COUNT(*) FROM inspections 
  WHERE defect_type_id = ? 
  AND status = 'PENDING_APPROVAL'
  ```
- **If Count > 0**: Reject archive with HTTP 400 | Message: "Cannot archive; {count} inspections pending approval reference this defect"
- **Rationale**: Approval workflow breaks if defect disappears during review

**Rule 3.4: Archive Requires Confirmation**
- **Statement**: Archive endpoint requires admin to provide `reason` (optional freeform text)
- **Purpose**: Audit trail records why admin archived the defect
- **Max Length**: 500 characters
- **Rationale**: Historical context for future investigation

**Rule 3.5: Audit Log Entry**
- **Statement**: Archive operation logged in audit_log with: who, when, defect_id, old_status, new_status, reason
- **Implementation**: Trigger or ORM hook on status update
- **Rationale**: Compliance and operational visibility

---

### Machine & Fabric Archival

**Rules 3.6-3.10**: Similar archival logic as Defect
- **7-day window** for recent usage
- **Cannot archive if active inspections exist** (check machine_culpable_id or fabric_id)
- **Soft delete only**
- **Audit trail**

---

## 📤 CSV IMPORT RULES

### File Validation

**Rule 4.1: File Format & Encoding**
- **Statement**: CSV file must be:
  - **Format**: Plain text CSV (RFC 4180), no Excel/XLSX
  - **Encoding**: UTF-8 (or auto-detect ASCII subset)
  - **Size**: ≤ 100 MB (prevent resource exhaustion)
  - **Rows**: ≤ 50,000 per import (configurable)
- **Validation**: Check file extension, read first byte (BOM/UTF-8), measure file size
- **Error Response**: HTTP 400 Bad Request | Message: "File must be CSV, UTF-8 encoded, ≤ 100 MB"

**Rule 4.2: Header Row Validation**
- **Statement**: CSV must have header row with exact column names (order irrelevant):
  - For Defects: `name`, `description`, `typical_process`, `typical_machine_id`
  - For Machines: `name`, `process`, `manufacturer`, `model`, `installation_date`
  - For Fabrics: `name`, `composition`, `width_cm`, `weight_gsm`
- **Validation**: Parse header row; compare against expected columns
- **Error Response**: HTTP 400 Bad Request | Message: "CSV header missing required columns: {list}. Expected: {expected}"
- **Rationale**: Operator error; guide admin to correct format

**Rule 4.3: Column Count Consistency**
- **Statement**: Each data row must have same number of columns as header
- **Validation**: Check each row's column count == header's column count
- **Error Response**: HTTP 400 Bad Request | Message: "Row {row_number}: Expected {n} columns, found {m}"

---

### Row Validation

**Rule 4.4: Required Fields Presence**
- **Statement**: 
  - **Defects**: `name` required; others optional
  - **Machines**: `name`, `process` required; others optional
  - **Fabrics**: `name`, `composition`, `width_cm`, `weight_gsm` required
- **Validation**: Check each row; collect errors per row
- **Error Response**: Detailed row-level error report (see Rule 4.14)

**Rule 4.5: Data Type Validation**
- **Statement**: 
  - Text fields (name, description): UTF-8 string, max length enforced
  - Numeric fields (width_cm, weight_gsm, installation_date): Valid data type
  - Enum fields (process, typical_process): Must match allowed values
- **Validation**: Type-specific checks per column
- **Error Format**: "Row 47, Column 'width_cm': Expected number, got 'ABC'"

**Rule 4.6: Referential Integrity (Lookups)**
- **Statement**: If CSV references another entity (e.g., `typical_machine_id`), must exist in DB
- **Validation**: For each machine_id reference, query: `SELECT COUNT(*) FROM machines WHERE id = ?`
- **If 0 rows**: Error per row
- **Error Message**: "Row 15, Column 'typical_machine_id': Machine '{value}' not found"
- **Rationale**: Prevent broken references

**Rule 4.7: Duplicate Detection Within Import**
- **Statement**: Within single CSV, cannot have duplicate `name` values
- **Validation**: As rows parsed, track names seen; reject duplicates
- **Error Response**: "Row 23: Defect name 'Roto' is duplicate of Row 5"
- **Rationale**: Prevent importing conflicting data

**Rule 4.8: Collision with Existing Masters**
- **Statement**: If master with same name exists in DB, determine action:
  - **Option A (Default)**: Reject import with error "Name already exists"
  - **Option B (Upsert)**: Update existing master with new values (requires admin confirmation)
- **Configuration**: Admin chooses during CSV wizard Step 3 (Review)
- **Rationale**: Different admin workflows; some want updates, some want strict insert

---

### Import Processing

**Rule 4.9: Transactional Atomicity (All or Nothing)**
- **Statement**: Either all valid rows imported, or none. No partial state.
- **Mechanism**: 
  - **Validation Phase**: Parse entire CSV, collect all errors
  - **If errors**: Report errors; do NOT write to DB; offer fix & retry
  - **If clean**: Begin DB transaction → insert all rows → COMMIT
- **Rollback**: If DB error mid-transaction, rollback entire import
- **Error Response**: CSV validation error report with per-row details (Rule 4.14)
- **Rationale**: No corrupt/inconsistent state

**Rule 4.10: Audit Trail for Import**
- **Statement**: Every import logged in audit_log with:
  - `operation`: 'csv_import_started', 'csv_import_completed', 'csv_import_failed'
  - `user_id`: Admin who initiated import
  - `filename`: Original CSV filename
  - `row_count`: Rows processed
  - `timestamp`: When import started/finished
  - `duration_ms`: How long import took
  - `trace_id`: Unique ID to correlate logs
- **Implementation**: Log on import start, completion, and failure

**Rule 4.11: Performance Constraints**
- **Statement**: CSV import must complete in < 3 minutes for 10,000 rows
- **Timeout**: If import exceeds 5 minutes, cancel and rollback
- **Notification**: Admin notified; can retry
- **Rationale**: Prevent hung jobs blocking server resources

**Rule 4.12: Memory Limits**
- **Statement**: CSV processing must not exceed 200 MB peak memory
- **Strategy**: Stream-based row parsing (not load entire file into memory)
- **Monitoring**: Track peak memory during import; log if > 150 MB

---

### Import Error Reporting

**Rule 4.13: Error Collection (All Rows Validated)**
- **Statement**: Even if Row 5 fails, continue validating Rows 6-1000. Collect all errors.
- **Rationale**: Admin sees comprehensive error list; can fix all issues at once
- **No Partial Abort**: Don't stop at first error

**Rule 4.14: Error Report Structure**
- **Output**: JSON or CSV format listing each error:
  ```json
  {
    "status": "VALIDATION_FAILED",
    "total_rows": 1000,
    "valid_rows": 995,
    "error_rows": 5,
    "errors": [
      {
        "row_number": 5,
        "column": "width_cm",
        "value": "invalid",
        "error": "Expected number between 10-300"
      },
      {
        "row_number": 47,
        "column": "name",
        "value": "",
        "error": "Required field cannot be empty"
      }
    ]
  }
  ```
- **UI Display**: Human-readable summary + downloadable error CSV
- **Rationale**: Admin can quickly fix and re-upload

**Rule 4.15: Retry Safety**
- **Statement**: Admin can fix CSV and re-upload; system detects which rows are new vs. duplicates
- **Strategy**: Compare by name; if name exists, decide: skip or update (based on upsert mode)
- **Idempotency**: Re-uploading same CSV twice should be safe (duplicates detected and skipped)

---

## 🔒 PROTECTION RULES

### System Masters

**Rule 5.1: System Master Identification**
- **Statement**: Certain masters marked with `is_system = true`; cannot be modified or archived
- **System Masters Seed**:
  - Defects: "No Especificado" (SYS-001), "Defecto Genérico" (SYS-002)
  - Machines: "No Aplica" (SYS-M01)
  - Fabrics: "No Especificado" (SYS-F01)
- **Protection**: 
  - Cannot update any field
  - Cannot archive
  - Cannot delete (hard or soft)
  - Can only READ
- **Rationale**: Fallback entries; must always exist; prevent accidental loss

**Rule 5.2: UI Marking**
- **Statement**: All system masters display "🔒 System" badge in UI
- **Edit Button**: Disabled for system masters (grayed out, no click allowed)
- **Rationale**: Prevent accidental click→edit attempt

---

## 📊 DATA CONSISTENCY RULES

### Concurrent Operations

**Rule 6.1: Optimistic Locking for Concurrent Edits**
- **Statement**: All master entities have `version` field (incremented on update)
- **Check-and-Set Pattern**: 
  ```sql
  UPDATE masters 
  SET name = ?, version = version + 1 
  WHERE id = ? AND version = current_version
  -- If 0 rows: Concurrent edit detected; return 409 Conflict
  ```
- **Conflict Message**: "Master was modified by another user. Refresh your view and try again."
- **Rationale**: Allow concurrent reads; detect conflicts on write
- **No Pessimistic Locks**: Don't use row locks (reduces concurrency)

**Rule 6.2: Connection Pool Limits**
- **Statement**: Database connection pool = 20 connections (5 admins × 4 concurrent requests)
- **Overflow Behavior**: Queue requests; process in order (FIFO)
- **Timeout**: Connection request timeout = 30 seconds; return HTTP 503 Service Unavailable
- **Rationale**: Prevent thundering herd; graceful degradation

---

### Cache Consistency

**Rule 6.3: Cache Invalidation on Write**
- **Statement**: When defect/machine/fabric is created/updated/archived, invalidate Redis cache
- **Strategy**: Clear cache key(s) related to that entity type:
  - `cache:defects:all` (list view cache)
  - `cache:defects:{id}` (single defect cache)
  - `cache:masters:usage_counts` (aggregation cache)
- **Timing**: Synchronous invalidation (happens within same transaction as write)
- **Rationale**: Prevent stale reads in list views immediately after edit

**Rule 6.4: Cache TTL**
- **Statement**: All master lists cached for 1 hour (3600 seconds)
- **Exception**: After CSV import, cache refreshed immediately (see Rule 6.3)
- **Cold Start**: First list request after app restart; cache miss; rebuild from DB (acceptable latency)

---

## 📋 VALIDATION SUMMARY TABLE

| Entity | Field | Type | Length | Required | Unique | Default | Constraints |
|--------|-------|------|--------|----------|--------|---------|-------------|
| **Defect** | id | String | 10 | ✓ | ✓ | DEF-{seq} | System-generated |
| | name | String | 3-100 | ✓ | ✓ | - | Alphanumeric + space/-/_ |
| | description | String | 0-500 | - | - | - | Optional |
| | typical_process | Enum | - | ✓ | - | OTRA | {TEÑIDO, ESTAMPADO, ACABADO, OTRA} |
| | typical_machine_id | FK | - | - | - | NULL | Must exist in machines table |
| | status | Enum | - | ✓ | - | ACTIVE | {ACTIVE, ARCHIVED} |
| | is_system | Boolean | - | ✓ | - | false | Cannot change after creation |
| | version | Int | - | ✓ | - | 1 | Incremented on update |
| | created_by | FK | - | ✓ | - | - | User ID from JWT |
| | created_at | Timestamp | - | ✓ | - | NOW() | UTC, immutable |
| | updated_by | FK | - | - | - | NULL | User ID, updated on PATCH |
| | updated_at | Timestamp | - | - | - | NULL | UTC, updated on PATCH |
| **Machine** | id | String | 10 | ✓ | ✓ | MAQ-{seq} | System-generated |
| | name | String | 3-100 | ✓ | ✓ | - | Alphanumeric + space/-/_ |
| | process | Enum | - | ✓ | - | OTRA | {TEÑIDO, ESTAMPADO, ACABADO} |
| | manufacturer | String | 0-100 | - | - | NULL | Optional |
| | model | String | 0-100 | - | - | NULL | Optional |
| | installation_date | Date | - | - | - | NULL | Must be ≤ today |
| | status | Enum | - | ✓ | - | ACTIVE | {ACTIVE, ARCHIVED} |
| | is_system | Boolean | - | ✓ | - | false | Cannot change |
| | version | Int | - | ✓ | - | 1 | Optimistic lock |
| **Fabric** | id | String | 10 | ✓ | ✓ | FAB-{seq} | System-generated |
| | name | String | 3-100 | ✓ | ✓ | - | Alphanumeric + space/-/_ |
| | composition | String | 3-100 | ✓ | - | - | Format: "50% Cotton, 50% Poly" |
| | width_cm | Numeric | - | ✓ | - | - | Range: 10-300 cm |
| | weight_gsm | Numeric | - | ✓ | - | - | Range: 50-1000 g/m² |
| | status | Enum | - | ✓ | - | ACTIVE | {ACTIVE, ARCHIVED} |
| | is_system | Boolean | - | ✓ | - | false | Cannot change |
| | version | Int | - | ✓ | - | 1 | Optimistic lock |

---

## ✅ RULE ENFORCEMENT LAYERS

| Rule Type | Enforced At | Technology | Example |
|-----------|-------------|-----------|---------|
| **Format** | API Schema | FastAPI Pydantic | String max length, enum values |
| **Uniqueness** | Database Index | PostgreSQL UNIQUE constraint | `UNIQUE(LOWER(name))` |
| **Referential** | Database FK | PostgreSQL FK | `typical_machine_id → machines.id` |
| **Business Logic** | Service Layer | Python/FastAPI service methods | Archive 7-day rule, system master check |
| **Concurrency** | ORM/Database | SQLAlchemy + PostgreSQL transactions | Version check, optimistic locking |
| **Audit Trail** | Database Trigger/ORM | PostgreSQL trigger or SQLAlchemy hook | Auto-log on insert/update |
| **Performance** | Database Indexes | PostgreSQL B-tree indexes | Index on (name), (status, created_at) |
| **Data Type** | Database Column | PostgreSQL type system | width_cm as NUMERIC, status as ENUM |

---

## 🔄 WORKFLOW EXAMPLES

### Example 1: Create New Defect

```
Admin clicks "New Defect"
  ↓
Form shows: Name, Description, Process, Typical Machine
  ↓
Admin enters: "Roto", "Tear in fabric", "TEÑIDO", "MAQ-TINT-01"
  ↓
Admin clicks "Create"
  ↓
[Service.create_defect()]
  1. Validate name length (3-100) ✓
  2. Check uniqueness (name = "Roto" doesn't exist) ✓
  3. Validate process enum (TEÑIDO in {TEÑIDO, ESTAMPADO, ACABADO, OTRA}) ✓
  4. Lookup machine (MAQ-TINT-01 exists, is_active=true) ✓
  5. Set defaults: status=ACTIVE, is_system=false, version=1, created_by=<admin_id>, created_at=NOW()
  6. Insert into DB ✓
  7. Publish DefectCreatedEvent
  ↓
Response: HTTP 201 Created | Body: {id: "DEF-1234", name: "Roto", ...}
```

---

### Example 2: Archive Defect with Active Inspections

```
Admin clicks "Archive" on Defect "Roto" (DEF-1234)
  ↓
[Service.archive_defect(defect_id, reason="Roto not seen recently")]
  ↓
  1. Fetch defect (DEF-1234) ✓
  2. Check is_system=false ✓ (allow archive)
  3. Check 7-day usage: 
     SELECT COUNT(*) FROM inspections 
     WHERE defect_type_id = 'DEF-1234' 
     AND created_at >= (NOW() - INTERVAL '7 days')
     → Result: 3 recent inspections ✗
  4. Reject: HTTP 400 Bad Request
     Message: "Cannot archive; defect used 3 times in last 7 days"
  ↓
Response to admin: Toast notification showing error reason
```

---

### Example 3: CSV Import with Duplicate

```
Admin uploads CSV: "import_defects.csv"
Rows:
  1. "Roto", "Tear", "TEÑIDO", ""
  2. "Mancha", "Stain", "TEÑIDO", ""
  3. "Roto", "Different defect", "ESTAMPADO", ""  ← DUPLICATE NAME
  ↓
[Service.import_csv(file)]
  ↓
Validation Phase:
  - Row 1: Name="Roto" (NEW) ✓
  - Row 2: Name="Mancha" (NEW) ✓
  - Row 3: Name="Roto" (DUPLICATE of Row 1) ✗
  ↓
Errors collected:
  {
    "valid_rows": 2,
    "error_rows": 1,
    "errors": [{
      "row_number": 3,
      "column": "name",
      "error": "Duplicate name found at Row 1"
    }]
  }
  ↓
Response: HTTP 400 Bad Request | Error report JSON
Admin sees: "2 valid, 1 error. Remove duplicate on Row 3 and re-upload."
```

---

**Status**: ✅ **COMPLETE**  
**Related**: [NFR-Requirements.md](./NFR-Requirements.md) | [domain-entities.md](../activity-1-functional-design/domain-entities.md)
