# Activity 3: NFR Design (Consolidated ADRs) — Unit 3 (Maestros y Configuración)

**Date**: 2026-06-01  
**Unit**: Maestros y Configuración (Masters & Configuration Domain)  
**Scope**: Architectural decisions for implementing non-functional requirements  
**Audience**: Architects, Lead Developers, Technical Decision Makers  

---

## 📋 OVERVIEW

This document consolidates architectural decisions for all 6 quality attributes. Each attribute follows the flow:

**Pregunta (¿Cómo?) → NFR Requirement → Diseño NFR (Patrón Técnico) → ADR (Decisión Arquitectónica)**

---

## 🏗️ ATTRIBUTE 1: DESEMPEÑO (PERFORMANCE)

### 1.1 Pregunta Clave: ¿Cómo importar CSV con 10,000 filas sin bloquear operaciones?

**NFR Requirement**:
- CSV import throughput ≥ 100 rows/second
- Import < 3 minutes for 10,000 rows
- CRUD operations ≤ 200 ms (p95)
- Search/filter ≤ 100 ms even with 5,000+ masters

**Diseño NFR (Patrón Técnico)**:
- **Async Background Job Queue** (Celery/RQ) for CSV processing
- **Redis Cache** for frequently accessed masters (TTL 1 hour)
- **Database Indexing** on name, status, created_at
- **Pagination** for list endpoints (20 items/page max)
- **Stream-based CSV parsing** (no full file in memory)

---

### ADR-001: Background Job Queue for CSV Imports

**Contexto**:
- CSV imports can be large (10,000+ rows)
- Synchronous processing blocks HTTP request/response cycle
- Admin needs feedback during long-running operations
- Import must not slow down other operations (inspections, approvals)

**Decisión**:
- Use **Celery** (with Redis broker) for asynchronous CSV import job processing
- Frontend makes HTTP request → receives job_id immediately → polls for progress
- Backend processes CSV in background → publishes completion event → invalidates cache
- CSV import runs independently from request handler

**Alternativas Consideradas**:
1. **Synchronous Processing**: Process entire CSV before returning response
   - ❌ Blocks request for 1-3 minutes; poor UX
   - ❌ Risk of timeout (30-60s HTTP timeout)
   - ❌ No progress feedback

2. **Threading (Python threading)**: Process in separate thread
   - ❌ Limited by Python GIL (Global Interpreter Lock)
   - ❌ Hard to manage thread lifecycle
   - ❌ No persistence if process crashes

3. **APScheduler**: Schedule as periodic task
   - ❌ Designed for scheduled jobs, not on-demand imports
   - ❌ Less suitable for immediate feedback

**Decisión Tomada**: ✅ **Celery + Redis**

**Consecuencias**:
- ✅ Admin gets immediate response; can navigate away
- ✅ Progress visible via WebSocket or polling
- ✅ Import persists; survives process restart
- ✅ Scales horizontally (multiple workers)
- ⚠️ Adds infrastructure complexity (Redis, Celery workers)
- ⚠️ Requires monitoring of task queue health
- ⚠️ Eventual consistency (cache invalidation async)

**Implementation**:
```python
# backend/app/tasks.py
from celery import shared_task

@shared_task(bind=True)
def import_csv_task(self, file_path, user_id, import_mode):
    """Background job for CSV import"""
    total_rows = count_csv_rows(file_path)
    
    for idx, row in enumerate(read_csv_stream(file_path)):
        # Validate & insert
        process_row(row)
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': idx + 1, 'total': total_rows}
        )
    
    # Invalidate cache
    cache.delete('cache:defects:all')
    
    return {'status': 'success', 'rows_imported': total_rows}
```

**Estado**: ✅ **ACCEPTED**

---

### ADR-002: Redis Caching for Master Data Lists

**Contexto**:
- List endpoints return all defects/machines/fabrics (can be 1000+ items)
- Multiple users search masters during inspection workflow
- Every list request queries database (expensive with joins)
- Search response time critical for operational UX

**Decisión**:
- Cache all master lists in **Redis** with **1-hour TTL**
- Invalidate cache on any write operation (create/update/archive)
- Implement cache-aside pattern: check cache → miss → query DB → store in cache

**Alternativas Consideradas**:
1. **In-Memory Cache (Python dict)**: Simple, fast
   - ❌ Lost on app restart
   - ❌ Not shared across multiple server instances
   - ❌ No TTL management

2. **Database Query Optimization Only** (indexes, materialized views)
   - ❌ Still hit DB on every request
   - ❌ Slower than cache hit

3. **CDN Caching** (CloudFlare, etc.)
   - ❌ Overkill for internal tool
   - ❌ Cost not justified

**Decisión Tomada**: ✅ **Redis Cache with 1-hour TTL**

**Consecuencias**:
- ✅ List queries < 50 ms (cache hit)
- ✅ Reduces database load by 80%+
- ✅ Survives app restart
- ✅ Shared across multiple instances
- ⚠️ Adds Redis infrastructure
- ⚠️ Stale data possible (1-hour window)
- ⚠️ Cache invalidation complexity

**Implementation**:
```python
# backend/app/cache.py
from redis import Redis
import json

redis = Redis(host='localhost', port=6379)
CACHE_TTL = 3600  # 1 hour

def get_all_defects_cached():
    # Check cache
    cache_key = 'cache:defects:all'
    cached = redis.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # Cache miss: query DB
    defects = db.query(Defect).filter(
        Defect.is_system == False,
        Defect.status == 'ACTIVE'
    ).all()
    
    # Store in cache
    redis.setex(
        cache_key,
        CACHE_TTL,
        json.dumps([d.to_dict() for d in defects])
    )
    
    return defects

def invalidate_defects_cache():
    redis.delete('cache:defects:all')
    redis.delete('cache:masters:usage_counts')
```

**Cache Invalidation Strategy**:
- On `create_defect()`: Invalidate `cache:defects:all`
- On `update_defect()`: Invalidate `cache:defects:all`, `cache:defects:{id}`
- On `archive_defect()`: Invalidate `cache:defects:all`
- On CSV import completion: Invalidate all master caches

**Estado**: ✅ **ACCEPTED**

---

### ADR-003: Database Indexing Strategy

**Contexto**:
- Masters tables grow over time (1000s of records)
- Queries need to be fast for list/search operations
- Filter by status, name, created_at common
- Without indexes, sequential scans cause latency

**Decisión**:
- Create B-tree indexes on:
  1. `defects(LOWER(name))` — For unique name enforcement + search
  2. `defects(status, created_at DESC)` — For list filtering
  3. `defects(is_system)` — For filtering system vs user-created
  4. Similar for machines, fabrics

**Alternativas Consideradas**:
1. **No Indexes** (rely on sequential scan)
   - ❌ Becomes slow at 1000+ rows

2. **Full-Text Search Index** (PostgreSQL GIN)
   - ⚠️ Overkill for simple name search
   - ✅ Consider for future requirement

3. **Hash Indexes**
   - ❌ PostgreSQL hash indexes less reliable than B-tree

**Decisión Tomada**: ✅ **B-tree Indexes as specified**

**Consecuencias**:
- ✅ Name search < 100 ms even with 5000 records
- ✅ List filtering fast
- ⚠️ Slightly slower writes (index maintenance)
- ⚠️ Disk space for indexes

**SQL**:
```sql
CREATE UNIQUE INDEX idx_defects_name ON defects (LOWER(name))
WHERE is_system = false;

CREATE INDEX idx_defects_status_created ON defects (status, created_at DESC)
WHERE is_system = false;

CREATE INDEX idx_defects_is_system ON defects (is_system);

-- Same for machines, fabrics
```

**Estado**: ✅ **ACCEPTED**

---

## 🔐 ATTRIBUTE 2: SEGURIDAD (SECURITY)

### 2.1 Pregunta Clave: ¿Cómo garantizar que solo ADMIN modifique maestros y auditar todos los cambios?

**NFR Requirement**:
- Only ADMIN role can create/update/delete masters
- All changes logged: WHO, WHEN, WHAT, OLD_VALUE, NEW_VALUE
- Audit logs immutable (no update/delete)
- CSV import validated for correctness + audited

**Diseño NFR (Patrón Técnico)**:
- **JWT Role-Based Access Control** (RBAC) on all routes
- **Audit Log Table** (immutable, append-only)
- **Database Triggers** for auto-logging
- **CSV Header/Row Validation** before import
- **File Type Validation** (reject non-CSV)

---

### ADR-004: Role-Based Access Control (RBAC) for Masters CRUD

**Contexto**:
- Different user roles: ADMIN, JEFE_QA, OPERARIO
- Only ADMIN should modify master data
- JEFE_QA and OPERARIO should read-only
- Need to enforce at API route level

**Decisión**:
- Use **JWT claims** with role embedded
- Check role in route decorator: `@require_role('ADMIN')`
- Return HTTP 403 Forbidden if not authorized
- Log failed auth attempts

**Alternativas Consideradas**:
1. **Database-level permissions** (PostgreSQL row security)
   - ⚠️ Complex to set up; need per-user policies
   - ✅ Could combine with JWT

2. **Attribute-Based Access Control (ABAC)**
   - ❌ Overkill for 3 roles

3. **No role check** (rely on UI hiding)
   - ❌ Security vulnerability; client can call API directly

**Decisión Tomada**: ✅ **JWT Role Check in Route Decorator**

**Consecuencias**:
- ✅ Simple, fast (JWT decoded once at login)
- ✅ Role embedded in token
- ⚠️ If role changes, user must re-login (token stale)
- ⚠️ No real-time permission revocation

**Implementation**:
```python
# backend/app/security.py
from functools import wraps
from fastapi import HTTPException, status

def require_role(*allowed_roles):
    def decorator(func):
        async def wrapper(*args, current_user: User = None, **kwargs):
            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# backend/app/routes_masters.py
@router.post("/defects")
@require_role('ADMIN')
async def create_defect(payload: DefectCreate, current_user: User):
    # Only ADMIN can reach here
    service.create_defect(payload, user_id=current_user.id)
```

**Estado**: ✅ **ACCEPTED**

---

### ADR-005: Immutable Audit Trail with Database Triggers

**Contexto**:
- Need complete history of who changed what, when, and why
- Audit logs must be tamper-proof
- Manual audit entries can be forged
- Efficiency: auto-logging avoids code duplication

**Decisión**:
- Create **audit_log table** (append-only):
  - `id, entity_type, entity_id, operation, old_values, new_values, user_id, timestamp, trace_id`
- Use **PostgreSQL triggers** to auto-log on INSERT/UPDATE/DELETE
- Audit logs can only be inserted, never updated/deleted
- Query audit trail: `SELECT * FROM audit_log WHERE entity_id = 'DEF-123' ORDER BY timestamp DESC`

**Alternativas Consideradas**:
1. **Manual logging in code** (ORM hooks)
   - ⚠️ Error-prone; easy to miss a path
   - ✅ More flexible

2. **Event Sourcing** (store all events, rebuild state)
   - ✅ Complete history
   - ❌ Overkill for this use case; complex to query

3. **No audit trail**
   - ❌ No traceability; compliance issue

**Decisión Tomada**: ✅ **Database Triggers for Audit Trail**

**Consecuencias**:
- ✅ Automatic, guaranteed logging (can't be bypassed)
- ✅ Immutable (no delete/update on audit table)
- ⚠️ Triggers add complexity to schema
- ⚠️ Debugging harder (logic split between code + triggers)

**SQL Schema**:
```sql
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    entity_type VARCHAR(50),  -- 'defect', 'machine', 'fabric'
    entity_id VARCHAR(100),
    operation VARCHAR(20),    -- 'INSERT', 'UPDATE', 'DELETE'
    old_values JSONB,
    new_values JSONB,
    user_id VARCHAR(100),
    timestamp TIMESTAMP DEFAULT NOW(),
    trace_id VARCHAR(100)
);

CREATE INDEX idx_audit_entity ON audit_log(entity_id);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp DESC);

-- Trigger for defects table
CREATE TRIGGER audit_defect_changes
AFTER INSERT OR UPDATE OR DELETE ON defects
FOR EACH ROW
EXECUTE FUNCTION log_audit_entry('defect');
```

**Estado**: ✅ **ACCEPTED**

---

### ADR-006: CSV Import Validation & Sanitization

**Contexto**:
- CSV uploads are external input (potential attack vector)
- Malformed CSVs can cause crashes or data corruption
- Need to validate before processing

**Decisión**:
- Validate **file type** (magic bytes for CSV, not just extension)
- Validate **encoding** (UTF-8)
- Validate **file size** (≤ 100 MB)
- Validate **CSV structure** (header row, column count consistency)
- Sanitize **all text fields** (trim whitespace, block SQL patterns)
- Validate **enum fields** before insert

**Alternativas Consideradas**:
1. **No validation** (trust user input)
   - ❌ Security vulnerability

2. **Client-side validation only**
   - ❌ Can be bypassed; need server-side too

3. **Minimal validation** (just type check)
   - ⚠️ Incomplete; leaves gaps

**Decisión Tomada**: ✅ **Comprehensive Server-Side Validation**

**Consecuencias**:
- ✅ Safe import; rejects malicious/malformed CSVs
- ✅ Clear error messages to user
- ⚠️ More code; longer validation phase

**Implementation**:
```python
# backend/app/services/csv_import.py
import magic

def validate_csv_import(file_path: str):
    # Check file type
    mime = magic.from_file(file_path, mime=True)
    if mime not in ['text/csv', 'text/plain']:
        raise ValueError("File must be CSV")
    
    # Check file size
    file_size = os.path.getsize(file_path)
    if file_size > 100 * 1024 * 1024:  # 100 MB
        raise ValueError("File too large")
    
    # Check encoding
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Validate header
    header = lines[0].strip().split(',')
    expected = ['name', 'description', 'process', 'machine_id']
    if not all(col in header for col in expected):
        raise ValueError(f"Missing columns: {expected}")
    
    # Validate each row
    errors = []
    for row_num, line in enumerate(lines[1:], start=2):
        values = line.strip().split(',')
        if len(values) != len(header):
            errors.append(f"Row {row_num}: Column count mismatch")
        
        # Sanitize
        name = values[0].strip()
        if not re.match(r'^[a-zA-Z0-9\s\-_]{3,100}$', name):
            errors.append(f"Row {row_num}: Invalid name format")
    
    if errors:
        raise ValueError("\n".join(errors))
    
    return True
```

**Estado**: ✅ **ACCEPTED**

---

## 📊 ATTRIBUTE 3: CONFIABILIDAD (RELIABILITY)

### 3.1 Pregunta Clave: ¿Cómo garantizar que los datos son consistentes incluso si falla la importación CSV?

**NFR Requirement**:
- CSV import is atomic (all or nothing)
- Cannot archive defect if used recently
- Cannot modify machine if active inspections reference it
- If import fails mid-way, rollback to pre-import state

**Diseño NFR (Patrón Técnico)**:
- **Database Transactions** (ACID guarantees)
- **Soft Delete** (status=ARCHIVED, not hard delete)
- **Dependency Checking** (archive validation before allowing)
- **Optimistic Locking** (version field, detect conflicts)

---

### ADR-007: Transactional CSV Import with Rollback

**Contexto**:
- CSV import can be large (10,000+ rows)
- Partial import leaves database in inconsistent state
- If row 5000 fails validation, rows 1-4999 shouldn't be inserted
- Admin needs confidence that import is all-or-nothing

**Decisión**:
- Use **database transaction** (BEGIN → INSERT all rows → COMMIT/ROLLBACK)
- Validate entire CSV **before** transaction (fail fast)
- If any row fails, ROLLBACK entire transaction
- Return error report with specific row errors

**Alternativas Consideradas**:
1. **Partial Import** (insert valid rows, skip invalid)
   - ⚠️ Simpler code
   - ❌ Inconsistent state; hard to track which rows were imported

2. **Per-Row Transactions** (each row in separate transaction)
   - ❌ No atomicity; some rows inserted even if CSV has errors

3. **No Transactions** (just insert rows)
   - ❌ No rollback; corruption if process crashes mid-import

**Decisión Tomada**: ✅ **Validate-First, Transactional Insert**

**Consecuencias**:
- ✅ Atomic: all rows imported or none
- ✅ Clean error handling
- ⚠️ Two-phase approach: validate + insert
- ⚠️ Large transaction locks DB briefly

**Implementation**:
```python
# backend/app/services/csv_import.py
from sqlalchemy import text

def import_csv_transaction(file_path: str, user_id: str, mode: str):
    # Phase 1: Validate entire CSV
    errors = validate_csv(file_path)
    if errors:
        return {'status': 'VALIDATION_FAILED', 'errors': errors}
    
    # Phase 2: Atomic insert
    try:
        with db.begin():  # Starts transaction
            for row in read_csv_stream(file_path):
                if mode == 'skip_duplicates' and exists_by_name(row['name']):
                    continue
                
                defect = Defect(
                    name=row['name'],
                    description=row['description'],
                    typical_process=row['process'],
                    created_by=user_id
                )
                db.add(defect)
            
            db.flush()  # Ensure all inserts prepared
        
        # Transaction committed successfully
        return {'status': 'SUCCESS', 'rows_imported': len(parsed_rows)}
    
    except Exception as e:
        # Rollback happens automatically
        return {'status': 'FAILED', 'error': str(e)}
```

**Estado**: ✅ **ACCEPTED**

---

### ADR-008: Soft Delete with Archive Validation

**Contexto**:
- Cannot truly delete masters (inspections reference them)
- Archive = logical delete (status=ARCHIVED)
- Cannot archive if recently used (within 7 days)
- Cannot archive if pending approvals depend on it

**Decisión**:
- **Soft delete only**: Set `status='ARCHIVED'` (never hard delete)
- Before archive, check:
  1. Recent usage: `SELECT COUNT(*) FROM inspections WHERE defect_id=? AND created_at >= NOW() - 7 days`
  2. Pending approvals: `SELECT COUNT(*) FROM approvals WHERE inspection.defect_id=? AND status='PENDING_APPROVAL'`
- If either check fails, reject archive with clear error
- Archived masters invisible in normal lists (filtered: WHERE status='ACTIVE')

**Alternativas Consideradas**:
1. **Hard delete**: Remove from DB
   - ❌ Breaks historical inspections
   - ❌ Loss of audit trail

2. **Soft delete without validation** (just archive immediately)
   - ❌ Can break operational workflows

3. **Immutable archives** (never allow un-archive)
   - ⚠️ Less flexible; harder to recover

**Decisión Tomada**: ✅ **Soft Delete with Validation**

**Consecuencias**:
- ✅ Historical integrity (old inspections still work)
- ✅ Reversible (can unarchive)
- ✅ Prevents operational issues
- ⚠️ More validation logic

**Implementation**:
```python
# backend/app/services/masters_service.py
def archive_defect(defect_id: str, reason: str, user_id: str):
    defect = db.query(Defect).filter(Defect.id == defect_id).first()
    
    if defect.is_system:
        raise ArchiveError("Cannot archive system defect")
    
    # Check recent usage
    recent_count = db.query(Inspection).filter(
        Inspection.defect_type_id == defect_id,
        Inspection.created_at >= datetime.utcnow() - timedelta(days=7)
    ).count()
    
    if recent_count > 0:
        raise ArchiveError(
            f"Cannot archive; defect used {recent_count} times in last 7 days"
        )
    
    # Check pending approvals
    pending_count = db.query(Approval).filter(
        Approval.inspection.defect_type_id == defect_id,
        Approval.status == 'PENDING_APPROVAL'
    ).count()
    
    if pending_count > 0:
        raise ArchiveError(
            f"Cannot archive; {pending_count} inspections pending approval"
        )
    
    # Safe to archive
    defect.status = 'ARCHIVED'
    defect.updated_by = user_id
    defect.updated_at = datetime.utcnow()
    db.commit()
    
    # Log event
    publish_event('DefectArchivedEvent', {
        'defect_id': defect_id,
        'reason': reason,
        'user_id': user_id
    })
```

**Estado**: ✅ **ACCEPTED**

---

### ADR-009: Optimistic Locking for Concurrent Edits

**Contexto**:
- Multiple admins can edit same defect simultaneously
- Without conflict detection, one edit silently overwrites another
- Pessimistic locks (row locks) reduce concurrency
- Optimistic approach better for low-conflict scenarios

**Decisión**:
- Add **version field** to all master entities (INT, default=1)
- On UPDATE, check: `WHERE id=? AND version=?`
- If version doesn't match, return HTTP 409 Conflict
- Admin sees: "Master modified by another user. Refresh and retry."
- Increment version by 1 on successful update

**Alternativas Consideradas**:
1. **Pessimistic Locking** (SELECT FOR UPDATE)
   - ❌ Serializes edits; reduces concurrency
   - ✅ Simpler logic

2. **Last-Write-Wins** (no conflict detection)
   - ❌ Silent data loss

3. **Event Sourcing** (store all changes, replay)
   - ✅ Complete history
   - ❌ Complex for this use case

**Decisión Tomada**: ✅ **Optimistic Locking with Version Field**

**Consecuencias**:
- ✅ High concurrency (multiple admins can edit different records)
- ✅ Detects conflicts
- ⚠️ Admin must manually retry if conflict
- ⚠️ Conflict rate depends on usage patterns

**Implementation**:
```python
# backend/app/models.py
class Defect(Base):
    __tablename__ = 'defects'
    
    id = Column(String(100), primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    ...

# backend/app/routes_masters.py
@router.patch("/defects/{defect_id}")
async def update_defect(
    defect_id: str,
    payload: DefectUpdate,
    current_user: User
):
    # Check version
    result = db.execute(
        text("""
        UPDATE defects 
        SET name = :name, 
            version = version + 1,
            updated_by = :user_id,
            updated_at = NOW()
        WHERE id = :id AND version = :version
        """),
        {
            'id': defect_id,
            'name': payload.name,
            'user_id': current_user.id,
            'version': payload.version
        }
    )
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=409,
            detail="Defect was modified by another user. Refresh and retry."
        )
    
    return {'status': 'updated', 'version': payload.version + 1}
```

**Estado**: ✅ **ACCEPTED**

---

## 👥 ATTRIBUTE 4: USABILIDAD (USABILITY)

### 4.1 Pregunta Clave: ¿Cómo hacer que los admins puedan importar 10,000 maestros sin errores?

**NFR Requirement**:
- 5-step wizard guides admin through CSV import
- Clear error messages for each failure
- Ability to download error report
- Search/filter responsive and intuitive

**Diseño NFR (Patrón Técnico)**:
- **Multi-Step Wizard UI** (Step 1: Select → Step 2: Validate → Step 3: Review → Step 4: Execute → Step 5: Results)
- **Real-time Progress Indicator** (WebSocket or polling)
- **Error Detail Table** (row #, column, reason)
- **Smart Search** (type-ahead, instant filtering)

---

### ADR-010: CSV Import Wizard with Progressive Disclosure

**Contexto**:
- CSV import is complex (many validation options)
- Single-page form overwhelming
- Step-by-step approach reduces cognitive load
- Each step provides feedback before proceeding

**Decisión**:
- Implement **5-step wizard**:
  1. **File Selection**: Upload CSV, show preview (filename, size, row count)
  2. **Format Validation**: Auto-check headers, encoding, structure
  3. **Review Changes**: Show summary (new vs duplicate vs update), choose mode
  4. **Import Execution**: Progress bar, real-time updates
  5. **Results**: Success summary or error report with download option

- Use **React form state** or similar to manage wizard state
- Back/Next buttons to navigate
- Persist wizard state in sessionStorage (survive page refresh)

**Alternativas Consideradas**:
1. **Single-page form**: All options at once
   - ❌ Overwhelming
   - ✅ Fewer clicks

2. **API-first (no UI wizard)**: Admin posts CSV to API
   - ❌ Poor UX; requires API knowledge

3. **Spreadsheet import plugin** (e.g., react-csv-importer)
   - ✅ Pretty
   - ❌ Less control over validation

**Decisión Tomada**: ✅ **5-Step Wizard with Progressive Disclosure**

**Consecuencias**:
- ✅ Clear guidance for admin
- ✅ Validation feedback at each step
- ✅ Reversible (can go back and change)
- ⚠️ More UI code (5 components)
- ⚠️ More complex state management

**Frontend Structure**:
```typescript
// frontend/src/pages/ImportMastersPage.tsx
import { useState } from 'react';

export function ImportMastersPage() {
  const [step, setStep] = useState(1);  // 1-5
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [validationErrors, setValidationErrors] = useState([]);
  
  return (
    <div>
      {step === 1 && <Step1FileSelect {...} />}
      {step === 2 && <Step2Validate {...} />}
      {step === 3 && <Step3Review {...} />}
      {step === 4 && <Step4Execute {...} />}
      {step === 5 && <Step5Results {...} />}
    </div>
  );
}
```

**Estado**: ✅ **ACCEPTED**

---

### ADR-011: Real-Time Import Progress with WebSocket

**Contexto**:
- CSV import can take 1-3 minutes for large files
- Admin needs visibility into progress
- HTTP polling inefficient (many requests)
- WebSocket provides bidirectional, real-time updates

**Decisión**:
- Establish **WebSocket connection** when import starts
- Backend sends progress updates: `{current: 5000, total: 10000, status: 'PROCESSING'}`
- Frontend displays progress bar: "5,000/10,000 rows (50%)"
- WebSocket closes on completion

**Alternativas Consideradas**:
1. **HTTP Polling**: Frontend asks "what's the progress?" every 500ms
   - ❌ Many requests; server load
   - ✅ Simpler

2. **No Progress Indicator**: Admin waits in dark
   - ❌ Poor UX; admin thinks it's hung

3. **Server-Sent Events (SSE)**: One-way from server
   - ✅ Simpler than WebSocket
   - ⚠️ Less bidirectional

**Decisión Tomada**: ✅ **WebSocket for Real-Time Progress**

**Consecuencias**:
- ✅ Real-time feedback (no lag)
- ✅ Low server load
- ⚠️ Requires WebSocket infrastructure
- ⚠️ Connection state management (reconnect on drop)

**Implementation**:
```python
# backend/app/websocket.py
from fastapi import WebSocket

@router.websocket("/ws/import/{job_id}")
async def websocket_import_progress(websocket: WebSocket, job_id: str):
    await websocket.accept()
    
    while True:
        # Fetch job progress
        job = db.query(ImportJob).filter(ImportJob.id == job_id).first()
        
        if job.status == 'COMPLETED':
            await websocket.send_json({
                'status': 'completed',
                'total': job.total_rows
            })
            break
        
        if job.status == 'FAILED':
            await websocket.send_json({
                'status': 'failed',
                'error': job.error_message
            })
            break
        
        # Send progress update
        await websocket.send_json({
            'status': 'processing',
            'current': job.processed_rows,
            'total': job.total_rows
        })
        
        await asyncio.sleep(1)  # Update every 1 second
    
    await websocket.close()
```

**Frontend**:
```typescript
// frontend/src/components/ImportProgress.tsx
useEffect(() => {
  const ws = new WebSocket(`ws://localhost:8000/ws/import/${jobId}`);
  
  ws.onmessage = (event) => {
    const { status, current, total, error } = JSON.parse(event.data);
    setProgress({ current, total });
    
    if (status === 'completed') {
      setStatus('✓ Import complete');
      ws.close();
    }
  };
  
  return () => ws.close();
}, [jobId]);
```

**Estado**: ✅ **ACCEPTED**

---

### ADR-012: Type-Ahead Search with Instant Filtering

**Contexto**:
- Admin searches for defect while filling inspection form
- Dropdown can have 1000+ items
- Typing "Rot" should show only matching defects
- Response must be < 100ms for responsiveness

**Decisión**:
- Implement **client-side filtering** for fast response
  - Pre-load all masters into memory (from cache)
  - Filter in real-time as user types
  - Show first 20 matches
- Server-side: API returns all masters (paginated, cached)

**Alternativas Consideradas**:
1. **API call on every keystroke** (server-side filter)
   - ❌ Network latency; slow
   - ✅ Supports very large datasets

2. **No search** (show all 1000 items)
   - ❌ Overwhelming dropdown

3. **Database full-text search**
   - ✅ Scalable for huge datasets
   - ❌ Overkill for this use case

**Decisión Tomada**: ✅ **Client-Side Filtering**

**Consecuencias**:
- ✅ Instant filtering (< 10ms)
- ✅ Works offline (after initial load)
- ⚠️ Limited to reasonable dataset size (< 5000 items)
- ⚠️ Memory on client for all masters

**Implementation**:
```typescript
// frontend/src/hooks/useDefectSearch.ts
export function useDefectSearch(searchTerm: string) {
  const { defects } = useMaster();  // From Zustand store
  
  const filtered = useMemo(() => {
    if (!searchTerm) return defects;
    
    const lower = searchTerm.toLowerCase();
    return defects
      .filter(d => d.name.toLowerCase().includes(lower))
      .slice(0, 20);  // Top 20 matches
  }, [searchTerm, defects]);
  
  return filtered;
}

// Usage in form
<input
  type="text"
  value={searchTerm}
  onChange={(e) => setSearchTerm(e.target.value)}
  placeholder="Search defects..."
/>
<ul>
  {useDefectSearch(searchTerm).map(d => (
    <li key={d.id} onClick={() => selectDefect(d)}>
      {d.name}
    </li>
  ))}
</ul>
```

**Estado**: ✅ **ACCEPTED**

---

## 🔧 ATTRIBUTE 5: MANTENIBILIDAD (MAINTAINABILITY)

### 5.1 Pregunta Clave: ¿Cómo estructurar el código para que sea fácil de entender y modificar?

**NFR Requirement**:
- Service layer with clear business logic
- Repository pattern for data access
- ≥ 90% test coverage for services
- Structured logging for debugging
- ADR documentation for decisions

**Diseño NFR (Patrón Técnico)**:
- **Layered Architecture**: Routes → Services → Repositories → ORM
- **Domain Events** for decoupling
- **Unit Tests** for business logic
- **Structured Logging** (JSON format)

---

### ADR-013: Layered Architecture (Routes → Services → Repositories → ORM)

**Contexto**:
- Code organization affects maintainability
- Mixing concerns (HTTP, business logic, data access) reduces clarity
- Want ability to swap implementations (e.g., mock repository for tests)

**Decisión**:
- **4-Layer Architecture**:
  1. **Routes Layer** (FastAPI @router): HTTP concerns only
     - Validate request format
     - Call service
     - Format response
  
  2. **Service Layer** (MastersService): Business logic
     - Validate business rules
     - Coordinate operations
     - Publish events
  
  3. **Repository Layer** (DefectRepository): Data access abstraction
     - CRUD operations
     - Queries
     - Indexing strategy
  
  4. **ORM Layer** (SQLAlchemy): Database mapping

**Alternativas Consideradas**:
1. **Monolithic** (all logic in routes)
   - ❌ Hard to test, understand, modify

2. **MVC** (routes only, models handle everything)
   - ⚠️ Works but less separation

3. **Hexagonal/Ports & Adapters**
   - ✅ More sophisticated
   - ❌ Overkill for this domain

**Decisión Tomada**: ✅ **4-Layer Layered Architecture**

**Consecuencias**:
- ✅ Clear responsibility separation
- ✅ Easy to test (mock repositories)
- ✅ Easy to understand code flow
- ⚠️ More files/classes
- ⚠️ Slight performance overhead (function calls)

**File Structure**:
```
backend/app/
├── models.py              (ORM models)
├── schemas.py             (Pydantic schemas)
├── repositories/
│   ├── __init__.py
│   ├── base.py            (BaseRepository abstract)
│   ├── defect.py          (DefectRepository)
│   ├── machine.py         (MachineRepository)
│   └── fabric.py          (FabricRepository)
├── services/
│   ├── __init__.py
│   ├── masters.py         (MastersService)
│   ├── csv_import.py      (CsvImportService)
│   └── audit.py           (AuditService)
├── routes/
│   ├── __init__.py
│   ├── masters.py         (Defect, Machine, Fabric routes)
│   └── imports.py         (CSV import routes)
└── events/
    ├── __init__.py
    └── domain_events.py   (DefectCreatedEvent, etc.)
```

**Example: DefectRepository**:
```python
# backend/app/repositories/defect.py
class DefectRepository:
    def __init__(self, db_session):
        self.db = db_session
    
    def save(self, defect: Defect) -> Defect:
        self.db.add(defect)
        self.db.commit()
        return defect
    
    def get_by_id(self, defect_id: str) -> Defect:
        return self.db.query(Defect).filter(Defect.id == defect_id).first()
    
    def exists_by_name(self, name: str, exclude_id: str = None) -> bool:
        query = self.db.query(Defect).filter(
            func.lower(Defect.name) == name.lower()
        )
        if exclude_id:
            query = query.filter(Defect.id != exclude_id)
        return query.first() is not None
    
    def get_all_active(self) -> List[Defect]:
        return self.db.query(Defect).filter(
            Defect.status == 'ACTIVE',
            Defect.is_system == False
        ).order_by(Defect.name).all()
```

**Example: MastersService**:
```python
# backend/app/services/masters.py
class MastersService:
    def __init__(self, defect_repo: DefectRepository, audit_service: AuditService):
        self.defect_repo = defect_repo
        self.audit_service = audit_service
    
    def create_defect(self, payload: DefectCreate, user_id: str) -> Defect:
        # Validate business rules
        if self.defect_repo.exists_by_name(payload.name):
            raise DuplicateError(f"Defect '{payload.name}' already exists")
        
        # Create entity
        defect = Defect(
            id=generate_id('DEF'),
            name=payload.name,
            description=payload.description,
            typical_process=payload.typical_process,
            created_by=user_id
        )
        
        # Persist
        saved = self.defect_repo.save(defect)
        
        # Publish event
        publish_event('DefectCreatedEvent', {
            'defect_id': saved.id,
            'name': saved.name
        })
        
        return saved
```

**Example: Route**:
```python
# backend/app/routes/masters.py
@router.post("/defects")
@require_role('ADMIN')
async def create_defect(
    payload: DefectCreate,
    current_user: User,
    service: MastersService = Depends()
):
    try:
        defect = service.create_defect(payload, user_id=current_user.id)
        return {'status': 'created', 'defect': defect.to_dict()}
    except DuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))
```

**Estado**: ✅ **ACCEPTED**

---

### ADR-014: Unit Testing Strategy with ≥90% Coverage

**Contexto**:
- Business logic critical; bugs costly
- Want confidence before deploying changes
- Testing at service layer most valuable
- Repository layer also needs tests

**Decisión**:
- **Unit tests** for all service methods
- **Repository tests** for CRUD + special queries
- Mock database for service tests (use in-memory SQLite or pytest fixtures)
- Aim for ≥ 90% line coverage in services/repositories
- Use **pytest** with **pytest-cov** for coverage reporting

**Test Structure**:
```
backend/tests/
├── conftest.py                 (fixtures, setup)
├── test_services/
│   ├── test_masters_service.py (MastersService unit tests)
│   └── test_csv_import.py      (CsvImportService unit tests)
├── test_repositories/
│   └── test_defect_repo.py     (DefectRepository CRUD tests)
└── test_integration/
    └── test_import_workflow.py (End-to-end import)
```

**Example Test**:
```python
# backend/tests/test_services/test_masters_service.py
import pytest
from app.services.masters import MastersService
from app.repositories.defect import DefectRepository

@pytest.fixture
def service(db_session):
    repo = DefectRepository(db_session)
    return MastersService(repo)

def test_create_defect_success(service):
    payload = DefectCreate(
        name='Roto',
        description='Tear in fabric',
        typical_process='TEÑIDO'
    )
    
    defect = service.create_defect(payload, user_id='admin1')
    
    assert defect.id.startswith('DEF-')
    assert defect.name == 'Roto'
    assert defect.status == 'ACTIVE'

def test_create_defect_duplicate_name(service):
    # Create first defect
    service.create_defect(
        DefectCreate(name='Roto', ...),
        user_id='admin1'
    )
    
    # Try to create duplicate
    with pytest.raises(DuplicateError):
        service.create_defect(
            DefectCreate(name='Roto', ...),
            user_id='admin1'
        )
```

**Estado**: ✅ **ACCEPTED**

---

### ADR-015: Structured Logging for Debugging

**Contexto**:
- Need to debug production issues
- Unstructured logs hard to parse/search
- JSON logging enables log aggregation (ELK, DataDog)

**Decisión**:
- Use **structlog** (Python) for structured logging
- All logs in JSON format with fields:
  - `timestamp`, `level`, `logger`, `message`
  - `user_id`, `trace_id`, `operation`, `duration_ms`
- Log at service entry/exit
- Log errors with stack trace + context

**Alternativas Consideradas**:
1. **Print statements** (unstructured)
   - ❌ Hard to parse; no filtering

2. **Standard logging** (Python logging module)
   - ⚠️ Works but less structured
   - ✅ Built-in

3. **No logging**
   - ❌ Can't debug issues

**Decisión Tomada**: ✅ **Structured Logging with structlog**

**Consecuencias**:
- ✅ Searchable logs
- ✅ Easy log aggregation
- ✅ Operational insights
- ⚠️ Adds structlog dependency

**Implementation**:
```python
# backend/app/logging_config.py
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
)

logger = structlog.get_logger()

# Usage
logger.info(
    'defect_created',
    defect_id='DEF-123',
    name='Roto',
    user_id='admin1',
    trace_id='req-abc123'
)
```

**Estado**: ✅ **ACCEPTED**

---

## 📈 ATTRIBUTE 6: ESCALABILIDAD (SCALABILITY)

### 6.1 Pregunta Clave: ¿Cómo soportar crecimiento a 5000+ maestros y múltiples admins sin redesign?

**NFR Requirement**:
- Support 5,000+ masters per type without degradation
- Multiple concurrent admins (5+) editing simultaneously
- CSV import of 10,000+ rows
- Extensible to new master types

**Diseño NFR (Patrón Técnico)**:
- **Horizontal Scalability**: Stateless services + Redis shared state
- **Asynchronous Processing**: Background jobs for heavy operations
- **Database Optimization**: Indexes, connection pooling, query optimization
- **Domain Model Extensibility**: Generic master pattern

---

### ADR-016: Stateless Service Design for Horizontal Scaling

**Contexto**:
- Single server has resource limits
- May need to scale to multiple servers
- Sessions shouldn't be tied to single server
- Shared state (cache, session) must be external

**Decisión**:
- Design services as **stateless**:
  - No in-memory state
  - All state in external systems (Redis, database)
  - Any server can handle any request
- Use **Redis** for distributed caching
- Use **Celery** for distributed task queue

**Alternativas Consideradas**:
1. **Monolithic** (single server)
   - ✅ Simpler
   - ❌ Bottleneck; limited scaling

2. **Shared memory** (in-process cache)
   - ❌ Not shared across servers
   - ❌ Replication complexity

3. **Sticky sessions** (request goes to same server)
   - ❌ Limits scalability

**Decisión Tomada**: ✅ **Stateless with External State Management**

**Consecuencias**:
- ✅ Scales horizontally (add servers)
- ✅ Better fault tolerance (if one server down, others serve)
- ⚠️ Requires Redis, Celery infrastructure
- ⚠️ More complex debugging (distributed system)

**Deployment Topology**:
```
[Admin 1] \
[Admin 2] -- [Load Balancer] -- [API Server 1] \
[Admin 3] /                       [API Server 2] --- [Shared Redis Cache]
                                  [API Server 3] /    [Shared Database]
                                                      [Celery Workers]
```

**Estado**: ✅ **ACCEPTED**

---

### ADR-017: Connection Pooling for Database Scalability

**Contexto**:
- Each request needs database connection
- Creating connection is expensive
- Without pooling, many concurrent requests exhaust connections
- Need to support 5+ concurrent admins, each with 4+ requests

**Decisión**:
- Use **SQLAlchemy connection pool**
- Pool size: 20 connections (5 admins × 4 requests)
- Max overflow: 5 (queue additional requests)
- Pool recycle: 3600 seconds (recycle connections every hour)

**Alternativas Consideradas**:
1. **No pooling** (create new connection per request)
   - ❌ Slow; connection overhead

2. **Thread pool** (local connection per thread)
   - ⚠️ Works but not distributed

3. **PgBouncer** (external connection pooler)
   - ✅ Advanced; useful at scale
   - ❌ Extra infrastructure

**Decisión Tomada**: ✅ **SQLAlchemy Built-in Connection Pool**

**Consecuencias**:
- ✅ Connections reused
- ✅ Faster requests
- ✅ Prevents connection exhaustion
- ⚠️ Need to tune pool size for traffic

**Configuration**:
```python
# backend/app/database.py
from sqlalchemy import create_engine

engine = create_engine(
    'postgresql://user:pass@localhost/masters_db',
    pool_size=20,           # Standard connections
    max_overflow=5,         # Additional overflow connections
    pool_pre_ping=True,     # Validate connection before use
    pool_recycle=3600,      # Recycle connections every hour
    connect_args={'timeout': 30}
)
```

**Estado**: ✅ **ACCEPTED**

---

### ADR-018: Generic Master Pattern for Extensibility

**Contexto**:
- Defect, Machine, Fabric are similar entities
- Future: may add Suppliers, Processes, Certifications, etc.
- Want to avoid code duplication
- Want one CRUD UI to handle all master types

**Decisión**:
- Define **generic Master interface**:
  ```python
  class Master:
      id: str
      name: str
      status: str  # ACTIVE, ARCHIVED
      is_system: bool
      created_at: datetime
      updated_at: datetime
  ```
- Specific aggregates (Defect, Machine, Fabric) inherit/implement Master
- Service layer: `MastersService[T]` (generic, works with any Master type)
- Repository: `BaseRepository[T]` (generic CRUD)
- Routes: One generic endpoint handler for all types

**Alternativas Consideradas**:
1. **Single table** (polymorphic, all masters in one table)
   - ❌ Loss of type safety; confusing queries

2. **Duplicate code** (separate service for each type)
   - ❌ Maintenance burden

3. **NoSQL** (MongoDB, flexible schema)
   - ✅ Easy to extend
   - ❌ Loses relational integrity

**Decisión Tomada**: ✅ **Generic Pattern with Type Inheritance**

**Consecuencias**:
- ✅ Easy to add new master type (< 1 hour)
- ✅ Consistent behavior across types
- ✅ Reusable CRUD logic
- ⚠️ More abstract; harder to understand initially

**Implementation**:
```python
# backend/app/models.py
class MasterBase:
    """Base class for all master types"""
    id: str
    name: str
    status: str
    is_system: bool
    version: int
    created_by: str
    created_at: datetime
    updated_by: Optional[str]
    updated_at: Optional[datetime]

class Defect(Base, MasterBase):
    __tablename__ = 'defects'
    # Defect-specific fields
    typical_process: str
    typical_machine_id: Optional[str]

class Machine(Base, MasterBase):
    __tablename__ = 'machines'
    # Machine-specific fields
    process: str
    manufacturer: Optional[str]

# Generic repository
class BaseRepository(Generic[T]):
    def save(self, entity: T) -> T: ...
    def get_by_id(self, entity_id: str) -> T: ...
    def exists_by_name(self, name: str) -> bool: ...
    def get_all_active(self) -> List[T]: ...

# Specific repositories
class DefectRepository(BaseRepository[Defect]): ...
class MachineRepository(BaseRepository[Machine]): ...
```

**Adding New Master Type** (e.g., Supplier):
1. Create model: `class Supplier(Base, MasterBase): ...`
2. Create repository: `class SupplierRepository(BaseRepository[Supplier]): ...`
3. Add service method: `def create_supplier(...): ...`
4. Add routes: `POST /suppliers`, `GET /suppliers/{id}`, etc.
5. **Total**: ~200 LOC, no duplication

**Estado**: ✅ **ACCEPTED**

---

## 📊 CONSOLIDATED ADR SUMMARY

| ADR | Attribute | Decision | Status |
|-----|-----------|----------|--------|
| ADR-001 | Performance | Celery + Redis for async CSV import | ✅ Accepted |
| ADR-002 | Performance | Redis caching for master lists (1h TTL) | ✅ Accepted |
| ADR-003 | Performance | Database B-tree indexes on name/status | ✅ Accepted |
| ADR-004 | Security | JWT RBAC for role enforcement | ✅ Accepted |
| ADR-005 | Security | Immutable audit trail with DB triggers | ✅ Accepted |
| ADR-006 | Security | CSV validation & sanitization | ✅ Accepted |
| ADR-007 | Reliability | Transactional CSV import with rollback | ✅ Accepted |
| ADR-008 | Reliability | Soft delete with archive validation | ✅ Accepted |
| ADR-009 | Reliability | Optimistic locking for concurrent edits | ✅ Accepted |
| ADR-010 | Usability | CSV import wizard (5-step) | ✅ Accepted |
| ADR-011 | Usability | WebSocket for real-time progress | ✅ Accepted |
| ADR-012 | Usability | Type-ahead search with client-side filtering | ✅ Accepted |
| ADR-013 | Maintainability | Layered architecture (Routes → Services → Repos) | ✅ Accepted |
| ADR-014 | Maintainability | Unit testing with ≥90% coverage | ✅ Accepted |
| ADR-015 | Maintainability | Structured logging (JSON) | ✅ Accepted |
| ADR-016 | Scalability | Stateless service design | ✅ Accepted |
| ADR-017 | Scalability | Database connection pooling | ✅ Accepted |
| ADR-018 | Scalability | Generic master pattern for extensibility | ✅ Accepted |

---

## 🔗 IMPLEMENTATION ROADMAP

**Phase 1: Core Infrastructure** (ADR-001, 002, 003, 004, 005)
- Redis setup
- Celery configuration
- Database indexes + audit triggers
- JWT RBAC middleware

**Phase 2: Services & Repositories** (ADR-013)
- MastersService, repositories
- CSV import service
- Domain events

**Phase 3: API Routes & Validation** (ADR-006, 007, 008, 009)
- Master CRUD routes
- Import endpoint
- Optimistic locking checks

**Phase 4: Frontend** (ADR-010, 011, 012)
- CSV wizard UI
- WebSocket progress
- Search component

**Phase 5: Testing & Logging** (ADR-014, 015)
- Unit tests (≥90% coverage)
- Integration tests
- Structured logging

**Phase 6: Scaling & Extensibility** (ADR-016, 017, 018)
- Connection pooling
- Stateless design verification
- Generic pattern for new types

---

## ✅ ACCEPTANCE CRITERIA

**NFR Design Complete When**:

- [ ] All 18 ADRs documented with Contexto/Decisión/Alternativas/Consecuencias/Estado
- [ ] Each ADR linked to specific NFR requirement
- [ ] Implementation examples provided for critical ADRs
- [ ] Consolidated table shows all decisions
- [ ] Roadmap shows phased implementation
- [ ] No conflicts between ADRs (all compatible)
- [ ] All ADRs marked as ✅ ACCEPTED

---

**Status**: ✅ **ACTIVITY 3 COMPLETE**  
**Next Step**: Activity 4 — Infrastructure Design  
**Related Documents**: 
- [domain-entities.md](../activity-1-functional-design/domain-entities.md)
- [NFR-Requirements.md](../activity-2-nfr-requirements/NFR-Requirements.md)
- [Business-Rules.md](../activity-2-nfr-requirements/Business-Rules.md)
- [Business-Logic-Model.md](../activity-2-nfr-requirements/Business-Logic-Model.md)
