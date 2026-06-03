# CC-03 — APIs Core: Auth + Inspección + Aprobación

**Milestone:** M1 | **Estimado:** 10d | **Prioridad:** urgent
**Unidad:** backend-api-unidad-1 | **Depende de:** CC-02

## Definición
Implementar endpoints REST para autenticación JWT (Login, Refresh, Logout), Inspección (Create, Read, Update, List) y Aprobación (Get pending, Approve, Reject). Incluye RBAC con roles: Admin, QA, Manager, Analyst.

## Acceptance Criteria
- POST /auth/login → JWT access + refresh tokens
- POST /auth/refresh → nuevo access token
- POST /inspections → crea inspección con foto, tipo, máquina, comentario
- GET /inspections → lista paginada con filtros
- GET /approvals/pending → pendientes para Jefe QA
- POST /approvals/{id}/approve y /reject funcionan
- RBAC: Analyst solo puede crear, QA puede aprobar
- Error handling estándar (400/401/403/404/500)

## Plan de Tests
- Integration tests con DB de test
- Test RBAC: Analyst no puede aprobar (403)
- Test JWT expirado → 401
- Load test básico: 50 req/s en /inspections

## Archivos de referencia
backend-api-implementation-plan.md#Fase3, nfr-requirements-elicited.md, nfr-design.md
