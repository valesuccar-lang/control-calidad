# CC-24 — E2E testing + performance final

**Milestone:** M3 | **Estimado:** 5d | **Prioridad:** high
**Unidad:** transversal | **Depende de:** CC-23

## Definición
Suite completa de tests E2E cubriendo flujos críticos y pruebas de rendimiento con 20+ usuarios concurrentes.

## Acceptance Criteria
- E2E: flujo inspección completo (captura → aprobación → dashboard)
- E2E: flujo offline (captura sin red → sync → aprobación)
- Load test: 20 analistas simultáneos, P95 ≤2s
- 0 errores críticos en suite E2E

## Plan de Tests
- Playwright: 10 scenarios E2E críticos
- k6: 20 VUs × 5min en endpoints core
- Reporte de cobertura E2E publicado

## Archivos de referencia
Testing-Strategy-Design.md, build-and-test-summary.md
