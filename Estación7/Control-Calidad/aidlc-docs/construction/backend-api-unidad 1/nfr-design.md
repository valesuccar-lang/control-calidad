# NFR Design — Architecture Decision Records (ADRs)
**Date**: 2026-05-28  
**Unit**: Backend API (Python FastAPI)  
**Status**: ✅ ACCEPTED

---

## 📋 ADR INDEX

| # | NFR | Pregunta | Patrón | Estatus |
|---|-----|----------|--------|---------|
| ADR-001 | Zero Data Loss | ¿Garantizar 100% sync sin perder datos? | Multi-Layer Persistence | ✅ ACCEPTED |
| ADR-002 | Photo Quality | ¿Validar fotos borrosas ANTES de guardar? | Image Analysis | ✅ ACCEPTED |
| ADR-003 | RBAC Security | ¿Controlar 4 roles de forma segura? | JWT + Decorators | ✅ ACCEPTED |
| ADR-004 | API Performance | ¿Garantizar <10s flujo completo? | Async + Indexes | ✅ ACCEPTED |
| ADR-005 | Sync Performance | ¿Sync 100 inspections en <2min? | Batch + Parallel | ✅ ACCEPTED |
| ADR-006 | Uptime 99%+ | ¿Asegurar disponibilidad 99%+? | Health Checks | ✅ ACCEPTED |
| ADR-007 | Test Coverage >60% | ¿Medir >60% cobertura de tests? | Pyramid Testing | ✅ ACCEPTED |
| ADR-008 | Monitoring | ¿Observar sistema en producción? | Prometheus + Logs | ✅ ACCEPTED |

---

---

# ADR-001: Zero Data Loss Strategy (CRITICAL ⭐⭐⭐)

## 🤔 PREGUNTA

**¿Cómo garantizar que el 100% de inspecciones capturadas lleguen al servidor sin perderse NUNCA?**

**Contexto del Problema**:
- Analistas crean inspecciones en piso (WiFi débil, desconexiones frecuentes)
- App PUEDE cerrar, browser PUEDE crashear, usuario PUEDE recargar página
- Datos de inspecciones son **EVIDENCIA LEGAL** (no recuperable)
- Usuario dijo: "CRÍTICO: 100% de datos (NUNCA se pierdan)"

---

## ✅ NFR REQUIREMENT

**Requirement**: CERO PÉRDIDA DE DATOS
- **Métrica**: 100% de inspecciones creadas → SYNCED O FAILED
- **Target**: No hay excepción; todos los datos se persisten
- **Scope**: Inspections offline + online

---

## 🏗️ DISEÑO NFR CON PATRÓN TÉCNICO

**Patrón**: **Multi-Layer Persistence with Idempotent Sync**

### Layer 1: Client-Side Storage (IndexedDB)
```javascript
// Guardar ANTES de intentar sync
async function storeInspectionLocally(inspection) {
    const db = await openIndexedDB()
    await db.put('inspections', {
        inspection_id: inspection.inspection_id,
        lote_id: inspection.lote_id,
        ...otherData,
        sync_status: 'PENDING'
    })
    // ← Data is SAFE (persisted even if browser crashes)
}
```

### Layer 2: Idempotent API Endpoint
```python
# POST /api/inspections/sync
# - inspection_id = unique key
# - Same request 5 times = 1 record (idempotent, safe)

POST /api/inspections/sync {
    inspection_id: "550e8400-...",
    lote_id: "HDR-12847",
    defect_id: "DEF-TON",
    ...
}

# Server:
SELECT * FROM inspections WHERE inspection_id = ?

If exists AND sync_status = 'SYNCED':
    Return: { status: "SYNCED" }  ← Idempotent

If not exists:
    INSERT inspection (atomic transaction)
    Return: { status: "SYNCED" }
```

### Layer 3: Exponential Backoff Retry
```
Sync attempt 1: 0ms (immediate)
    ↓ Fail (network error)
Sync attempt 2: 5s delay
    ↓ Fail
Sync attempt 3: 10s delay
    ↓ Fail
Sync attempt 4: 30s delay
    ↓ Fail
Sync attempt 5: 60s delay
    ↓ Fail
Final: Mark as SYNC_FAILED + Show "Manual Retry" button

Total automatic retry time: ~105 seconds
```

---

## 📋 ADR-001

### CONTEXTO

**Necesidad del Negocio**:
- Inspecciones son evidencia legal de defectos
- NO se pueden perder datos bajo ninguna circunstancia
- Eliot opera en piso con WiFi débil (desconexiones frecuentes)

**Restricciones**:
- Offline-first: debe funcionar sin internet
- On-premise: datos no pueden ir a cloud
- 100% guarantee: no hay trade-offs aceptables

---

### DECISIÓN

**Implementar: Multi-Layer Persistence + Idempotent API + Exponential Backoff**

**Garantía Final**:
- ✅ Inspection guardada en IndexedDB ANTES de sync
- ✅ Si sync falla: Retry automático (5 veces, ~2 minutos)
- ✅ Si todas fallan: Manual retry button siempre disponible
- ✅ Data nunca perdida (remains in IndexedDB until SYNCED)

---

### ALTERNATIVAS

| Alternativa | Pros | Cons | Decisión |
|-------------|------|------|----------|
| **A: No Offline** | Simple | ❌ Violates requirement, Poor UX | REJECTED |
| **B: Cloud Backup** | Redundant | ❌ No on-premise, Cost, Violates isolati | REJECTED |
| **C: SQLite DB** | SQL interface | ❌ Heavier, Overkill | REJECTED |

---

### CONSECUENCIAS

**Positivas** ✅
- 100% zero data loss guarantee
- Works fully offline
- Handles network flakiness
- No external dependencies
- User has control (manual retry)

**Negativas** ❌
- Client-side complexity (~250 lines JS)
- Sync can take up to 2 minutes
- Deduplication logic (minor DB overhead)

---

### ESTADO

**Status**: **✅ ACCEPTED**  
**Approved**: 2026-05-28  
**Rationale**: CRÍTICO: 100% zero data loss (user priority)

---

---

# ADR-002: Photo Quality Validation (CRITICAL ⭐⭐⭐)

## 🤔 PREGUNTA

**¿Cómo evitar que analista capture fotos borrosas/oscuras que luego serán rechazadas por Jefe QA?**

**Contexto**:
- Si foto mala → Jefe QA rechaza → Analista recaptura
- Ciclo largo, ineficiente
- User said: "CRITICO: Validación en cliente OBLIGATORIA"

---

## ✅ NFR REQUIREMENT

**Requirement**: VALIDACIÓN DE CALIDAD DE FOTO
- **Timing**: ANTES de guardar (client-side)
- **Criteria**: Sharpness, brightness, contrast
- **Action**: Auto-reject fotos malas, mostrar feedback
- **Target**: 90%+ fotos válidas a primera captura

---

## 🏗️ DISEÑO NFR CON PATRÓN TÉCNICO

**Patrón**: **Image Analysis + User Feedback Loop**

```javascript
// Metrics para evaluar:
interface PhotoMetrics {
    sharpness: number      // Laplacian variance (higher = sharper)
    brightness: number     // Mean pixel brightness (0-255)
    contrast: number       // Std dev (higher = more contrast)
}

// Thresholds:
const BLUR_THRESHOLD = 50
const BRIGHTNESS_MIN = 50
const BRIGHTNESS_MAX = 200
const CONTRAST_MIN = 30

// Validación:
function validatePhotoQuality(canvas) {
    metrics = calculateMetrics(canvas)
    
    if (metrics.sharpness < BLUR_THRESHOLD)
        return { valid: false, message: "Foto borrosa. Intenta de nuevo." }
    
    if (metrics.brightness < BRIGHTNESS_MIN)
        return { valid: false, message: "Foto muy oscura. Mejora iluminación." }
    
    if (metrics.brightness > BRIGHTNESS_MAX)
        return { valid: false, message: "Foto muy clara. Reduce iluminación." }
    
    if (metrics.contrast < CONTRAST_MIN)
        return { valid: false, message: "Foto sin contraste. Mejora composición." }
    
    return { valid: true, message: "Foto válida ✓" }
}

// UX Flow:
// [Analista abre cámara] → [Captura foto] → [Sistema analiza]
// ├─ Foto BUENA → ✅ "Save" button ENABLED
// ├─ Foto MALA  → ❌ "Retake" message + button DISABLED
// → [Analista retoma hasta OK] → [Guarda]
```

---

## 📋 ADR-002

### CONTEXTO

**Problema**:
- Fotos borrosas/oscuras no se detectan hasta aprobación
- Jefe QA rechaza → Analista recaptura → ciclo largo

**Oportunidad**:
- Validar antes de guardar
- Feedback inmediato
- 90%+ fotos válidas a primera captura

---

### DECISIÓN

**Implementar: Client-Side Image Analysis (Laplacian + Brightness + Contrast)**

**Algoritmo**:
1. Captura foto en canvas
2. Calcula métricas (Laplacian, brightness, contrast)
3. Compara contra thresholds
4. Si OK: Enable "Save", Si BAD: Show error + "Retake"

**Why Client-Side**:
- Instant feedback (no server latency)
- Works offline
- Reduce server load (no invalid images)

---

### ALTERNATIVAS

| Alternativa | Pros | Cons | Decisión |
|-------------|------|------|----------|
| **A: No Validation** | Simple | ❌ Long cycle, Poor UX | REJECTED |
| **B: ML-Based** | Accurate | ❌ Overkill, Scope creep | REJECTED |
| **C: User Confirm** | Simple | ❌ Subjective | REJECTED |

---

### CONSECUENCIAS

**Positivas** ✅
- Instant feedback (better UX)
- 90%+ first-capture success
- Reduce rejection cycle

**Negativas** ❌
- ~200 lines JavaScript
- May reject some valid photos (false negatives)
- Thresholds need tuning per environment

---

### ESTADO

**Status**: **✅ ACCEPTED**  
**Approved**: 2026-05-28  
**Rationale**: CRITICO: Validación en cliente OBLIGATORIA

---

---

# ADR-003: RBAC Security (JWT + Role Decorators)

## 🤔 PREGUNTA

**¿Cómo controlar acceso a 4 roles (ANALISTA, JEFE_QA, ADMIN, GERENTE) de forma segura y escalable?**

---

## ✅ NFR REQUIREMENT

**Requirement**: ROLE-BASED ACCESS CONTROL
- **Authentication**: JWT (stateless, 8h)
- **Roles**: 4 (ANALISTA, JEFE_QA, ADMIN, GERENTE)
- **Enforcement**: Per-route RBAC decorators
- **Token Life**: 8h access, 30d refresh

---

## 🏗️ DISEÑO NFR CON PATRÓN TÉCNICO

**Patrón**: **JWT + Dependency Injection Role Decorators**

```python
# 1. Token Generation (login):
from datetime import timedelta
from jose import jwt

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ACCESS_TOKEN_EXPIRE_HOURS = 8

def create_access_token(user_id: str, roles: List[str]):
    payload = {
        "sub": user_id,
        "roles": roles,
        "exp": datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

@app.post("/api/auth/login")
async def login(email: str, password: str):
    user = verify_credentials(email, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(user.id, user.roles)
    return {"access_token": token, "token_type": "bearer"}

# 2. Token Validation (on protected routes):
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        roles = payload.get("roles", [])
        return User(id=user_id, roles=roles)
    except:
        raise HTTPException(status_code=401, detail="Token invalid")

# 3. Role Enforcement (decorator):
def require_role(required_roles: List[str]):
    async def role_checker(current_user = Depends(get_current_user)):
        if not any(r in current_user.roles for r in required_roles):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

# 4. Usage on routes:
@app.post("/api/inspections")
@require_role(["ANALISTA"])  # ← Only ANALISTA
async def create_inspection(req, current_user = Depends(require_role(["ANALISTA"]))):
    pass

@app.post("/api/approvals")
@require_role(["JEFE_QA"])  # ← Only JEFE_QA
async def approve_inspection(req, current_user = Depends(require_role(["JEFE_QA"]))):
    pass

@app.post("/api/masters/defects")
@require_role(["ADMIN"])  # ← Only ADMIN
async def create_defect(req, current_user = Depends(require_role(["ADMIN"]))):
    pass
```

---

## 📋 ADR-003

### CONTEXTO

**Necesidad**:
- 4 roles diferentes con permisos distintos
- Escalable sin complejidad
- Stateless (no session store)

---

### DECISIÓN

**Implementar: JWT-Based RBAC with FastAPI Dependency Injection**

**Por qué**:
- JWT = stateless, escalable
- Dependency Injection = clean code
- Token decode = ~1ms (fast)

---

### ALTERNATIVAS

| Alternativa | Pros | Cons | Decisión |
|-------------|------|------|----------|
| **A: Sessions** | Traditional | ❌ Requires session store | REJECTED |
| **B: ACL** | Fine-grained | ❌ Overkill for 4 roles | REJECTED |
| **C: OAuth2** | External provider | ❌ On-premise not suitable | REJECTED |

---

### CONSECUENCIAS

**Positivas** ✅
- Scalable (stateless)
- Fast (JWT decode ~1ms)
- Simple (~80 lines)
- Industry standard

**Negativas** ❌
- Token can't be revoked immediately
- Need secure SECRET_KEY
- Short lifetime (8h) needed

---

### ESTADO

**Status**: **✅ ACCEPTED**  
**Approved**: 2026-05-28

---

---

# ADR-004: API Performance (<10 seconds)

## 🤔 PREGUNTA

**¿Cómo garantizar que flujo completo (buscar lote → foto → guardar) tome < 10 segundos?**

---

## ✅ NFR REQUIREMENT

**Requirement**: API RESPONSE TIME
- **Target**: <10 segundos end-to-end (FLEXIBLE)
- **p50**: <500ms per API call
- **p99**: <2s per API call

---

## 🏗️ DISEÑO NFR CON PATRÓN TÉCNICO

**Patrón**: **Async Routing + Connection Pooling + Database Indexing**

```python
# 1. Async Routes (FastAPI):
@app.post("/api/inspections")
async def create_inspection(req, current_user = Depends(...)):
    # Non-blocking I/O
    # While this waits for DB, others are served
    pass

# 2. Connection Pooling (SQLAlchemy):
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_size=10,           # Min connections
    max_overflow=20,        # Max overflow
    pool_timeout=30,        # 30s timeout
    pool_pre_ping=True,     # Health check
    pool_recycle=3600       # Recycle every 1h
)

# 3. Database Indexes (PostgreSQL):
CREATE INDEX idx_inspections_lote_id 
    ON inspections(lote_id);

CREATE INDEX idx_approvals_status 
    ON approvals(status) 
    WHERE status = 'PENDING';

CREATE INDEX idx_inspections_analista_created 
    ON inspections(analista_id, created_at DESC);

# 4. Query Optimization (Eager Loading):
# BAD: N+1 problem
inspections = session.query(Inspection).all()
for insp in inspections:
    print(insp.defect)  # Triggers N more queries

# GOOD: Eager loading
inspections = session.query(Inspection).options(
    joinedload(Inspection.defect),
    joinedload(Inspection.machine)
).all()  # Single query
```

---

## 📋 ADR-004

### DECISIÓN

**Implementar: Async + Connection Pooling + Indexes + Eager Loading**

---

### ALTERNATIVAS

| Alternativa | Decisión |
|-------------|----------|
| Synchronous (Blocking) | REJECTED (can't handle load) |
| Caching (Redis) | REJECTED (not needed yet) |
| DB Replication | REJECTED (premature) |

---

### ESTADO

**Status**: **✅ ACCEPTED**

---

---

# ADR-005: Sync Performance (<2 minutes for 100)

## 🤔 PREGUNTA

**¿Cómo sincronizar 100+ inspecciones offline en < 2 minutos sin bloquear UI?**

---

## ✅ NFR REQUIREMENT

**Requirement**: SYNC PERFORMANCE
- **Target**: <2 minutos para 100 inspections (FLEXIBLE)
- **Background**: No bloquea UI
- **Batch API**: POST /api/inspections/sync-batch

---

## 🏗️ DISEÑO NFR CON PATRÓN TÉCNICO

**Patrón**: **Batch API + Parallel Processing + Async**

```python
# Batch endpoint (not 100 individual POSTs):
@app.post("/api/inspections/sync-batch")
async def sync_batch(req: SyncBatchDTO):
    # Parallel sync: 10 concurrent requests
    tasks = [
        service.sync_offline_inspection(insp)
        for insp in req.inspections
    ]
    results = await asyncio.gather(*tasks)
    
    return {
        "synced": sum(1 for r in results if r),
        "failed": sum(1 for r in results if not r),
        "total": len(results)
    }

# Performance comparison:
# Sequential: 100 × 0.5s = 50 seconds
# Batch + parallel: (100 / 10) × 0.5s = 5 seconds
```

---

## 📋 ADR-005

### DECISIÓN

**Implementar: Batch API + asyncio.gather() Parallelism**

---

### ESTADO

**Status**: **✅ ACCEPTED**

---

---

# ADR-006: Uptime 99%+

## 🤔 PREGUNTA

**¿Cómo asegurar que API esté disponible 99%+ del tiempo en producción?**

---

## ✅ NFR REQUIREMENT

**Requirement**: AVAILABILITY
- **Target**: 99%+ uptime (≤7.2h downtime/month)
- **Health Check**: GET /health endpoint
- **Recovery**: Auto-restart on failure

---

## 🏗️ DISEÑO NFR CON PATRÓN TÉCNICO

**Patrón**: **Health Checks + Auto-Restart**

```python
@app.get("/health")
async def health_check():
    status = { "status": "healthy", "timestamp": datetime.utcnow() }
    
    # Check database
    try:
        db.execute("SELECT 1")
        status["checks"]["database"] = "healthy"
    except:
        status["checks"]["database"] = "unhealthy"
        status["status"] = "degraded"
    
    return status

# Load balancer checks /health every 10s:
# If unhealthy → remove from rotation
# If healthy → add back to rotation

# Auto-restart (systemd or Docker):
# [Service]
# Restart=always
# RestartSec=5
```

---

## 📋 ADR-006

### DECISIÓN

**Implementar: Health Endpoint + Auto-Restart Policy**

---

### ESTADO

**Status**: **✅ ACCEPTED**

---

---

# ADR-007: Test Coverage >60%

## 🤔 PREGUNTA

**¿Cómo medir y asegurar >60% code coverage?**

---

## ✅ NFR REQUIREMENT

**Requirement**: TEST COVERAGE
- **Target**: >60% (domain + routes)
- **Tools**: pytest + pytest-cov
- **Focus**: Domain services >80%, Routes >60%

---

## 🏗️ DISEÑO NFR CON PATRÓN TÉCNICO

**Patrón**: **Pyramid Testing (Unit > Integration)**

```python
# Unit test (domain service):
def test_register_inspection_valid():
    # Arrange
    defect_repo.find_by_id.return_value = Defect(...)
    
    # Act
    result = service.register_inspection(...)
    
    # Assert
    assert result.inspection_id is not None

# Integration test (API route):
def test_create_inspection_route(client):
    token = create_test_token(role="ANALISTA")
    
    response = client.post(
        "/api/inspections",
        json={...},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201

# Run coverage:
# pytest --cov=app --cov-report=html
```

---

## 📋 ADR-007

### DECISIÓN

**Implementar: Pyramid Testing (Unit > Integration > E2E)**

---

### ESTADO

**Status**: **✅ ACCEPTED**

---

---

# ADR-008: Monitoring (Prometheus + Logs + Alerts)

## 🤔 PREGUNTA

**¿Cómo observar sistema en producción para detectar problemas rápidamente?**

---

## ✅ NFR REQUIREMENT

**Requirement**: MONITORING
- **Metrics**: Prometheus (latency, errors, throughput)
- **Logs**: JSON structured (not plaintext)
- **Alerts**: Automáticas en eventos críticos
- **Trace**: OpenTelemetry (optional, future)

---

## 🏗️ DISEÑO NFR CON PATRÓN TÉCNICO

**Patrón**: **Instrumentation + Metrics Export + Alerting**

```python
from prometheus_client import Counter, Histogram

# Prometheus metrics:
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

sync_failures_total = Counter(
    'sync_failures_total',
    'Total sync failures',
    ['reason']
)

# JSON Logs (Loguru):
from loguru import logger

logger.bind(
    user_id="analyst-001",
    action="create_inspection",
    request_id="req-550e..."
).info("Inspection created", inspection_id="550e...", duration_ms=342)

# Output:
# {
#   "timestamp": "2026-05-28T14:35:22.123Z",
#   "level": "INFO",
#   "message": "Inspection created",
#   "user_id": "analyst-001",
#   "action": "create_inspection",
#   "inspection_id": "550e...",
#   "duration_ms": 342
# }

# Alerts (Prometheus rules):
# - Error rate > 1% → Alert "High error rate"
# - API latency p99 > 5s → Alert "Slow API"
# - Sync failures > 10% → Alert "Sync issues"
```

---

## 📋 ADR-008

### DECISIÓN

**Implementar: Prometheus + JSON Logs + Alert Rules**

---

### ESTADO

**Status**: **✅ ACCEPTED**

---

---

## ✅ SUMMARY: All ADRs ACCEPTED

| ADR | NFR | Patrón | Estatus |
|-----|-----|--------|---------|
| ADR-001 | Zero Data Loss ⭐ | Multi-Layer Persistence | ✅ ACCEPTED |
| ADR-002 | Photo Quality ⭐ | Image Analysis | ✅ ACCEPTED |
| ADR-003 | RBAC Security | JWT + Decorators | ✅ ACCEPTED |
| ADR-004 | API Performance | Async + Indexes | ✅ ACCEPTED |
| ADR-005 | Sync Performance | Batch + Parallel | ✅ ACCEPTED |
| ADR-006 | Uptime 99%+ | Health Checks | ✅ ACCEPTED |
| ADR-007 | Test Coverage >60% | Pyramid Testing | ✅ ACCEPTED |
| ADR-008 | Monitoring | Prometheus + Logs | ✅ ACCEPTED |

---

## 🚀 PRÓXIMOS PASOS

1. ✅ **Functional Design** — COMPLETED (domain-entities.md, business-rules.md, business-logic-model.md)
2. ✅ **NFR Requirements** — COMPLETED (nfr-requirements-elicited.md)
3. ✅ **NFR Design (ADRs)** — COMPLETED (this file)
4. ➡️ **Infrastructure Design** — Database schema, deployment architecture
5. ➡️ **Code Generation** — FastAPI routes, SQLAlchemy models, tests

---

**Status**: ✅ **ACTIVITY 3 (NFR Design) COMPLETE**

**Ready for**: Infrastructure Design → Code Generation Phase
