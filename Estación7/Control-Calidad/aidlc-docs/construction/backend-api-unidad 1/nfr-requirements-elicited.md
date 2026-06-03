# NFR Requirements (Elicited) — Backend API Unit (Unit 1)
**Date**: 2026-05-28  
**Unit**: Backend API (Python FastAPI)  
**Phase**: Construction - Activity 2 (NFR Requirements)  
**Status**: ✅ ELICITATION COMPLETE

---

## 📊 GLOBAL PRIORITY

**Primary Desideratum**: **CONFIABILIDAD (Reliability)**
- Prioridad #1: Nunca perder datos
- Todas las inspecciones capturadas deben llegar al servidor
- Zero data loss es no-negociable

---

## 🎯 PERFORMANCE REQUIREMENTS

### P1: API Response Time (End-to-End)
**Requirement**: Flujo completo de inspección < **10 segundos** (flexible)

**Scope**: Analista: buscar lote → cargar foto → guardar

**Components**:
- LoteSearch: 1-2s
- CameraCapture + compression: 3-4s
- API POST + validation: 2-3s
- **Total: 6-9 seconds (acceptable)**

**Rationale**: Workflow en piso de producción; usuarios pueden tolerar esto

**Implementation**:
- [ ] Frontend: Async/await, minimal blocking
- [ ] API: Fast validation (Pydantic), no heavy computations
- [ ] DB: Efficient queries with indexes

---

### P2: Database Query Latency
**Requirement**: BD query execution time < **1 segundo** (flexible)

**Scope**: Single query p99

**Examples**:
- SELECT * FROM inspections WHERE lote_id = ? → <100ms
- SELECT * FROM approvals WHERE status = 'PENDING' → <200ms
- Complex joins → <500ms
- All p99 → <1 second

**Rationale**: PostgreSQL can handle; no extreme optimization needed

**Implementation**:
- [ ] Indexes: lote_id, analista_id, status, inspection_id, created_at
- [ ] Query optimization: EXPLAIN ANALYZE on hot paths
- [ ] Connection pooling: SQLAlchemy pool

---

### P3: Sync Performance (Offline → Online)
**Requirement**: Sincronizar 100 inspecciones offline en < **2 minutos** (flexible)

**Scope**: Background sync, no bloquea UI

**Why**: Sync puede ser asincrónico; user puede seguir trabajando mientras sincroniza

**Implementation**:
- [ ] Batch API: POST /api/inspections/sync (accept array)
- [ ] Parallel processing: SQLAlchemy bulk_insert_mappings
- [ ] Non-blocking: Service Worker handles in background

---

### P4: Photo Operations
**Requirement**: 
- Upload: ≤ 10 segundos para 500KB
- Download: ≤ 5 segundos para 500KB

**Scope**: File I/O operations

**Implementation**:
- [ ] Client: JPEG compression (80% quality)
- [ ] Server: Streaming response
- [ ] Storage: Local filesystem or S3

---

## 🛡️ RELIABILITY REQUIREMENTS

### R1: Zero Data Loss (CRITICAL ⭐⭐⭐)
**Requirement**: **100% de inspecciones capturadas deben llegar al servidor. NUNCA se pierdan datos.**

**Scope**: Todas las inspecciones (online + offline)

**Why**: Datos = evidencia legal de defectos; no recuperable

**Implementation**:
- [ ] Client-side: IndexedDB stores inspection BEFORE attempting sync
- [ ] Server-side: Idempotent API (inspection_id as unique key)
- [ ] Sync logic: Exponential backoff with manual retry button
- [ ] Verification: 100% synced OR marked SYNC_FAILED (not lost)

**Test Case**:
```
1. Create 10 inspections while offline
2. Go online
3. Verify all 10 synced OR queued for retry
4. Refresh browser
5. Verify all still queued (not lost from IndexedDB)
```

---

### R2: Uptime & Availability
**Requirement**: **99%+ uptime** (≤ 7.2 hours downtime/month)

**Why**: Production system; downtime impacta operaciones de Eliot

**Scope**: API server availability

**Implementation**:
- [ ] Health check: GET /health → { "status": "healthy" }
- [ ] Auto-restart: systemd or Docker restart policy
- [ ] Error handling: Graceful degradation on failures
- [ ] Database: Connection pooling handles transient failures
- [ ] Monitoring: Alerts on downtime

---

### R3: Error Recovery (Retry Strategy)
**Requirement**: Reintento exponencial **LARGO**: 5s, 10s, 30s, 60s

**Scope**: Offline sync failures due to network

**Why**: Network en piso es débil; reintentos espaciados reducen carga

**Retry Schedule**:
```
Attempt 1: 0s (immediate)
Attempt 2: 5s delay
Attempt 3: 10s delay
Attempt 4: 30s delay
Attempt 5: 60s delay
Total: ~105 seconds max auto-retry

After 5 attempts:
├─ Mark: sync_status = SYNC_FAILED
├─ Show: Manual retry button
└─ User can retry anytime
```

**Implementation**:
```python
backoff_seconds = [5, 10, 30, 60]  # 4 more attempts after initial
for attempt, delay in enumerate(backoff_seconds, start=2):
    try:
        sync_result = post_sync(inspection)
        return "SYNCED"
    except Exception:
        if attempt < len(backoff_seconds):
            await asyncio.sleep(delay)
        else:
            return "SYNC_FAILED"
```

---

### R4: Data Consistency (ACID Transactions)
**Requirement**: Inspeccciones MUST be persisted ATOMICALLY (all-or-nothing)

**Scope**: Inspection + Photo + Audit log creation

**Implementation**:
- [ ] PostgreSQL transactions: BEGIN, COMMIT, ROLLBACK
- [ ] SQLAlchemy: session.commit() = atomic
- [ ] No partial writes (photo saved but inspection not, etc.)

---

## 🔐 SECURITY REQUIREMENTS

### S1: Authentication (JWT)
**Requirement**: All API requests (except POST /auth/login) require valid JWT

**Token Lifespan**:
- Access token: 8 hours
- Refresh token: 30 days

**Scope**: Stateless auth, no session store

**Implementation**:
- [ ] POST /api/auth/login (email, password) → { access_token, refresh_token }
- [ ] FastAPI: @Depends(get_current_user) on all protected routes
- [ ] Token validation: Signature, expiration, claims

---

### S2: Authorization (RBAC - 4 Roles)
**Requirement**: All 4 roles implemented with granular access control

**Roles**:
1. **ANALISTA**: Create inspections, view own history
2. **JEFE_QA**: Approve/reject inspections
3. **ADMIN**: CRUD masters, CRUD users, audit logs
4. **GERENTE**: Dashboard, reports (future v1.1)

**Implementation**:
```python
@app.post("/api/inspections")
@require_role(["ANALISTA"])
async def create_inspection(...):
    pass

@app.post("/api/approvals")
@require_role(["JEFE_QA"])
async def approve_inspection(...):
    pass

@app.post("/api/masters/defects")
@require_role(["ADMIN"])
async def create_defect(...):
    pass
```

---

### S3: Input Validation (Whitelist)
**Requirement**: All inputs validated via Pydantic DTOs (whitelist approach)

**Scope**: All POST/PUT endpoints

**Example**:
```python
class InspectionCreateDTO(BaseModel):
    lote_id: str  # Non-empty
    defect_id: str  # Must exist in Masters
    comment: str  # Pydantic: 10-500 chars (min_length, max_length)
    photo_base64: str  # Max 500KB decoded
    machine_id: str
    
    @field_validator('comment')
    def validate_comment(cls, v):
        if len(v) < 10 or len(v) > 500:
            raise ValueError('comment length must be 10-500')
        return v
```

**FastAPI** auto-validates on route, returns 422 if invalid

---

### S4: Data Encryption
**Requirement**: TLS + field-level encryption for sensitive data

**Scope**:
- TLS 1.2+: All HTTP traffic (transport layer)
- Field encryption: Passwords in database

**Implementation**:
- [ ] HTTPS: SSL/TLS certificate (Nginx reverse proxy)
- [ ] Field encryption: bcrypt for passwords (12 rounds)
- [ ] Example:
  ```python
  # Password storage:
  from passlib.context import CryptContext
  pwd_context = CryptContext(schemes=["bcrypt"])
  hashed_password = pwd_context.hash(user_password)
  # Store hashed_password in DB
  
  # Password verification:
  if not pwd_context.verify(login_password, stored_hashed):
      raise ValueError("Invalid credentials")
  ```

---

### S5: Audit Logging (Parametrizable)
**Requirement**: Audit logging **configurable por performance de máquina**

**Scope**: All mutations (CREATE, UPDATE, DELETE)

**Configurability**:
```yaml
# config.yaml
audit:
  enabled: true
  log_level: "CRITICAL" or "ALL"  # CRITICAL = only errors, ALL = all mutations
  sample_rate: 0.5  # Log 50% of operations (reduce I/O)
  batch_write: true  # Batch audit logs before writing
```

**What to Log**:
```json
{
  "timestamp": "2026-05-28T14:35:22.123Z",
  "user_id": "analyst-001",
  "action": "CREATE",
  "resource_type": "Inspection",
  "resource_id": "550e8400-...",
  "lote_id": "HDR-12847",
  "ip_address": "192.168.1.100"
}
```

**Implementation**:
- [ ] Audit table: (timestamp, user_id, action, resource_type, resource_id, details)
- [ ] Log on service.save() calls
- [ ] Config: Enable/disable based on server capacity

---

### S6: Rate Limiting
**Requirement**: 100 requests/minute per user (prevent brute force, DoS)

**Scope**: All API endpoints

**Implementation**:
```python
# Middleware:
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    user_id = get_user_from_token(request)
    
    # Redis counter (or in-memory for local deployment)
    count = redis.incr(f"rate_limit:{user_id}")
    redis.expire(f"rate_limit:{user_id}", 60)  # 1-minute window
    
    if count > 100:
        return JSONResponse(status_code=429, content={"error": "Too many requests"})
    
    return await call_next(request)
```

---

## 📈 SCALABILITY REQUIREMENTS

### Sc1: Concurrent Users
**Requirement**: Support 20-50 simultaneous API users

**Scope**: Connection pooling, async handling

**Implementation**:
- [ ] FastAPI: Async routes (async def)
- [ ] SQLAlchemy: pool_size=10, max_overflow=20
- [ ] Load balancer: Nginx (if multiple servers later)

---

### Sc2: Data Growth (5-year projection)
**Requirement**: System remains responsive with 110,000+ inspections (5 years)

**Scope**: Query performance

**Data Volume**:
- Daily: ~60 inspections
- Monthly: ~1,800 inspections
- Yearly: ~22,000 inspections
- 5-year: ~110,000 inspections
- Photo storage: 900GB/month

**Implementation**:
- [ ] Indexes: (lote_id, analista_id, status, created_at)
- [ ] Pagination: Limit 100 records per page
- [ ] Archival: Move old data to cold storage after 1 year (future v1.1)

---

## 🎨 USABILITY REQUIREMENTS

### U1: Online/Offline Status Indicator (IMPORTANT)
**Requirement**: Show clearly in header/footer if ONLINE or OFFLINE

**Visual Design**:
```
Header (always visible):
┌─────────────────────────────────────────┐
│ Eliot QC System    📡 ONLINE           │
│ Analista: Juan    [Logout]             │
└─────────────────────────────────────────┘

Or when offline:
┌─────────────────────────────────────────┐
│ Eliot QC System    ⚠️  OFFLINE (1 pending)     │
│ Analista: Juan    [Logout]             │
└─────────────────────────────────────────┘
```

**Spec**:
- Color: Green (online), Red (offline)
- Icon: 📡 or ⚠️
- Text: "ONLINE" / "OFFLINE (N pending)"
- Location: Header or footer, always visible

**Implementation**:
- [ ] Zustand offlineStore tracks navigator.onLine
- [ ] React component renders indicator
- [ ] Updates real-time as connectivity changes

---

### U2: Photo Quality Validation (CRITICAL ⭐⭐⭐)
**Requirement**: **Validar ANTES de guardar** si foto está borrosa/oscura

**Scope**: Client-side validation in CameraCapture component

**Why**: Si foto mala llega a servidor, Jefe QA rechaza → analista debe recapturar → ciclo largo

**Validation Criteria**:
```
1. Blur detection: Analyze image sharpness (Laplacian variance)
2. Brightness: Ensure photo is not too dark or too bright
3. Contrast: Minimum contrast to distinguish defect
4. Size: ≤ 500KB (after compression)
```

**Implementation**:
```javascript
// Client-side (JavaScript/React):
function validatePhotoQuality(photoBlob) {
    const img = new Image()
    img.onload = () => {
        const canvas = document.createElement('canvas')
        const ctx = canvas.getContext('2d')
        canvas.width = img.width
        canvas.height = img.height
        ctx.drawImage(img, 0, 0)
        
        // Check blur (Laplacian variance)
        const variance = calculateBlurVariance(ctx.getImageData(0,0,w,h))
        if (variance < BLUR_THRESHOLD) {
            showError("Foto borrosa. Intenta de nuevo")
            return false
        }
        
        // Check brightness
        const brightness = calculateBrightness(ctx.getImageData(0,0,w,h))
        if (brightness < MIN_BRIGHTNESS || brightness > MAX_BRIGHTNESS) {
            showError("Foto muy oscura/clara. Ajusta iluminación")
            return false
        }
        
        // OK
        return true
    }
    img.src = URL.createObjectURL(photoBlob)
}

// UI:
if (!validatePhotoQuality(photoBlob)) {
    // Disable "Save" button, show error
    // User must retake photo
}
```

**User Experience**:
```
1. Analista: Take photo (camera opens)
2. System: Auto-validates quality
3. Case A (Good): ✅ Photo accepted, "Save" button enabled
4. Case B (Bad): ❌ Photo rejected, "Retake photo" message shown
5. Analista: Retakes photo until quality OK
```

---

## 🔧 MAINTAINABILITY REQUIREMENTS

### M1: Test Coverage
**Requirement**: Minimum **>60% code coverage** (domain + routes)

**Scope**: Unit tests + Integration tests

**Target Breakdown**:
- Domain services: >80% (critical business logic)
- Repositories: >70% (DB interactions)
- Routes: >60% (API contracts)
- Utilities: >50% (helpers)

**Tools**:
- pytest (unit + integration)
- pytest-cov (coverage reporting)
- FastAPI TestClient (route testing)

**Example Test**:
```python
def test_create_inspection_valid():
    # Arrange
    defect = Defect(defect_id="DEF-TON", defect_name="TONODIFFERENTE", ...)
    defect_repo.save(defect)
    
    # Act
    result = inspection_service.register_inspection(
        lote=lote,
        defect=DefectType(...),
        comment=Comment(text="Test comment with 20+ chars"),
        photograph=Photograph(...),
        machine=MachineId(...),
        analista_id="analyst-001"
    )
    
    # Assert
    assert result.inspection_id is not None
    assert result.sync_status == SyncStatus.PENDING or SYNCED
    assert inspection_repo.find_by_id(result.inspection_id) is not None
```

---

### M2: Monitoring (ALL of the following required)

#### M2.1: Prometheus Metrics
**Requirement**: Track key operations via Prometheus

**Metrics**:
```python
# HTTP metrics
http_requests_total{method, endpoint, status}
http_request_duration_seconds{endpoint}  # Histogram: p50, p95, p99

# Database metrics
db_query_duration_seconds{query_type}  # Histogram
db_active_connections
db_connection_pool_size

# Business metrics
inspections_created_total
approvals_total{decision}
sync_failures_total{reason}
```

**Endpoint**: GET /metrics (for Prometheus scraping)

---

#### M2.2: Structured Logging (JSON)
**Requirement**: All logs in JSON format (not plaintext)

**Format**:
```json
{
  "timestamp": "2026-05-28T14:35:22.123Z",
  "level": "INFO",
  "message": "Inspection created",
  "user_id": "analyst-001",
  "action": "create_inspection",
  "inspection_id": "550e8400-...",
  "request_id": "req-abc123",
  "duration_ms": 342
}
```

**Tool**: Loguru or Python logging with JSON formatter

---

#### M2.3: Alerting
**Requirement**: Automatic alerts on critical events

**Alert Conditions**:
```
1. Error rate > 1% (last 5 minutes)
   → Alert: "High error rate detected"

2. API latency p99 > 5 seconds (sustained)
   → Alert: "Slow API response"

3. Sync failure rate > 10% (last hour)
   → Alert: "Offline sync issues"

4. Uptime < 99% (last 24h)
   → Alert: "Low uptime, possible incidents"

5. Database connection pool exhausted
   → Alert: "DB connection pool full"
```

**Implementation**:
- [ ] Prometheus alerts: Define alert rules (.yml)
- [ ] Alertmanager: Send notifications (email, Slack, SMS)

---

#### M2.4: Distributed Tracing (Optional / Future)
**Requirement**: OpenTelemetry for request tracing (end-to-end visibility)

**Scope**: Optional, can be implemented in v1.1 if needed

**Purpose**: Trace a single request across services (frontend → API → DB)

---

## 📊 SUMMARY TABLE

| Category | Requirement | Metric | Target | Priority |
|----------|---|---|---|---|
| Performance | API response (end-to-end) | Time | <10s | FLEXIBLE |
| Performance | DB query latency | p99 | <1s | FLEXIBLE |
| Performance | Sync 100 items | Time | <2min | HIGH |
| Reliability | Data loss | % synced | 100% | CRITICAL ⭐⭐⭐ |
| Reliability | Uptime | % hours | 99%+ | CRITICAL |
| Reliability | Error retry | Strategy | Exponential (5,10,30,60s) | CRITICAL |
| Security | Auth | JWT | 8h token life | CRITICAL |
| Security | RBAC | Roles | 4 roles | CRITICAL |
| Security | Input validation | Approach | Whitelist (Pydantic) | CRITICAL |
| Security | Encryption | Scope | TLS + field encryption | CRITICAL |
| Security | Audit logging | Config | Parametrizable by perf | HIGH |
| Security | Rate limiting | req/min | 100/user | MEDIUM |
| Scalability | Concurrent users | Count | 20-50 | MEDIUM |
| Scalability | Data growth | Queries | <1s at 110K rows | MEDIUM |
| Usability | Online/offline indicator | Location | Header/footer | IMPORTANT |
| Usability | Photo quality validation | Timing | Before save (client) | CRITICAL ⭐⭐⭐ |
| Maintainability | Test coverage | % | >60% domain+routes | HIGH |
| Maintainability | Prometheus metrics | Coverage | All critical ops | HIGH |
| Maintainability | Structured logging | Format | JSON | HIGH |
| Maintainability | Alerting | Auto | Critical events | HIGH |

---

## 🎯 CRITICAL REQUIREMENTS (No Negotiable ⭐⭐⭐)

1. **Zero Data Loss**: 100% of inspections must sync or be marked failed
2. **Photo Quality Validation**: Client-side, before save
3. **Reliability**: 99%+ uptime
4. **Security**: JWT + RBAC + input validation
5. **Encryption**: TLS + password fields
6. **IMPORTANT**: Online/offline indicator visible

---

## ✅ VALIDATION CHECKLIST

- [x] Elicitation complete (20+ questions answered)
- [x] User provided clear priorities
- [x] Tech stack validation against NFRs
- [x] Implementation strategies documented
- [x] Monitoring/observability planned
- [x] Trade-offs understood (performance vs. reliability)

---

## 🚀 NEXT STEPS

1. ✅ **Functional Design** — COMPLETED (domain-entities.md, business-rules.md, business-logic-model.md)
2. ✅ **NFR Requirements** — COMPLETED (this document)
3. ➡️ **NFR Design** — Apply patterns to functional design
4. ➡️ **Infrastructure Design** — Database schema, deployment
5. ➡️ **Code Generation** — FastAPI routes, models, tests

---

**Status**: ✅ NFR REQUIREMENTS ELICITATION COMPLETE  
**Global Priority**: **RELIABILITY** (zero data loss)  
**Ready for**: NFR Design Phase (apply patterns)
