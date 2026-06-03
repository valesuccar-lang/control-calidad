# Conocimiento Reutilizable — control-calidad

Cada sección captura lo aprendido al completar una tarea: decisiones validadas, invariantes, bugs, docs afectados.

---

## CC-01 — Setup infraestructura Backend

**Decisión validada:** CI/CD usa base de datos PostgreSQL 16 real (no mock). Incidente previo: mock pasaba pero migración fallaba en producción.

**Docs afectados:** `.github/workflows/ci.yml`, `alembic.ini`, `migrations/env.py`

**Conocimiento:** `migrations/env.py` usa `.replace("+asyncpg", "")` para convertir la URL async a sync que necesita Alembic.

---

## CC-02 — Dominio y entidades DDD

**Invariantes validados con 27 tests:**
- `Comment`: 10–500 chars — `ValueError` si no cumple
- `Photograph`: ≤500 KB, checksum SHA256 exactamente 64 hex chars
- `Approval REJECTED` siempre requiere `rejection_reason`
- `Lote.quantity` > 0
- `SyncStatus`: PENDING → SYNCED | SYNC_FAILED (sin reversión en dominio puro)

**Validación útil:** `@dataclass(frozen=True)` garantiza inmutabilidad de value objects — los tests verifican que `c.text = "x"` lanza excepción.

---

## CC-03 — APIs Core Auth + RBAC

**Decisión validada:** Los tests de CC-03 NO duplican el `app/` completo. Usan `PYTHONPATH` apuntando a Estación5 donde vive la implementación real.

**Bug encontrado:** `HTTPAuthCredentials` fue renombrado a `HTTPAuthorizationCredentials` en FastAPI reciente.
- **Fix:** `from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials as HTTPAuthCredentials`
- **Archivo:** `Estación5/Control-Calidad/app/auth/dependencies.py`

**Bug encontrado:** `func` de SQLAlchemy no importado en `orm.py` línea ~166 — `NameError: name 'func' is not defined`.
- **Fix pendiente:** agregar `func` al import de sqlalchemy en `orm.py`

---

## CC-04 — APIs Maestros

**Invariante:** Bulk import es idempotente — duplicados se saltan (no lanzan error).

**Decisión:** `MastersService` solo recibe repos como dependencias — facilita tests con fake repos sin DB.

---

## CC-05 — Testing y documentación

**Decisión:** `pytest.ini` con `--cov-fail-under=80` local, CI usa `--cov-fail-under=60` (más permisivo para pipeline rápido).

**Herramienta load test:** `locustfile.py` — 50 VUs, targets: `/health`, `/auth/login`, `/api/inspections`.

---

## CC-06 — Deployment AWS Lambda

**Decisión:** Mangum adapter para FastAPI en Lambda. `lifespan="off"` requerido para Lambda (no hay proceso persistente).

**Invariante:** Docker image debe ser < 500MB — Dockerfile multi-stage logra esto copiando solo `.local` de pip.

---

## CC-07 — Frontend Setup

**Decisión:** Token almacenado en `sessionStorage` (no localStorage) por seguridad — no persiste entre tabs ni después de cerrar.

**Invariante:** Axios interceptor redirige a `/login` automáticamente en 401.

---

## CC-08 — Auth Frontend

**Decisión:** Zustand store para auth — no Context API. Razón: más simple, sin re-renders de árbol completo.

**Validación útil:** Zod schema en login valida email format antes de llamar API.

---

## CC-09 a CC-15 — Módulos UI y Reportes

**Invariante UI:** Comentario de inspección mínimo 10 chars — validado tanto en frontend (zod) como en backend (domain entity).

**Decisión:** Recharts para gráficos (ya en ecosistema React, sin deps pesadas).

**Decisión:** jsPDF + autotable para PDF, xlsx para Excel — ambas sin servidor, generan en el browser.

---

## CC-16 a CC-21 — Offline + Sync

**Decisión:** Service Worker usa cache-first para estáticos, network-first para API. Si API falla → 503 JSON (no página de error HTML).

**Invariante:** La cola offline (IndexedDB) es la fuente de verdad cuando no hay red. Al reconectar, `flushQueue` procesa en orden de creación (`by_created` index).

**Invariante conflicto:** Un conflicto ocurre cuando un `inspection_id` local ya existe en el servidor con payload diferente. Resolución: el usuario decide descartar local o ignorar.

---

## CC-22 a CC-23 — WebSocket + Batch Sync

**Decisión:** JWT en query param `?token=` para WebSocket (headers no soportados en browser WS nativo).

**Invariante:** Batch máximo 100 items por request. Gzip compresión activada cuando cliente envía `Content-Encoding: gzip`.

---

## CC-24 — E2E Testing

**Tests verificados:** login → refresh → /me con `httpx.AsyncClient` + `ASGITransport` (sin servidor real).

---

## CC-25 — Go-live + Monitoreo

**CloudWatch alarms definidas:** 5XX alto, Lambda duration P95 >3s, RDS CPU >80%.

**health_check.py:** script autónomo para cron — exit code 0 si todo ok, 1 si algo falla.

---

## Bugs globales conocidos

| Archivo | Bug | Fix |
|---------|-----|-----|
| `requirements.txt` CC-01 | `PyJWT==2.8.1` no existe | cambiado a `2.9.0` ✅ |
| `app/auth/dependencies.py` | `HTTPAuthCredentials` renombrado | alias a `HTTPAuthorizationCredentials` ✅ |
| `app/models/orm.py` | `func` no importado | pendiente: agregar `func` al import sqlalchemy |

---

## Entorno local

- **Python 3.12.10** instalado via winget ✅
- **Docker Desktop 4.76** instalado via winget — requiere reinicio para activar WSL2 ✅
- **Node.js v24.15** disponible ✅
- **Push pendiente:** 7+ commits locales, usar GitHub Desktop (PAT sin scope `workflow`)
