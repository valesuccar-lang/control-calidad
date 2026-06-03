# CC-21 — UI resolución de conflictos

**Milestone:** M3 | **Estimado:** 5d | **Prioridad:** medium
**Unidad:** offline-unidad-4 | **Depende de:** CC-20

## Definición
Pantalla dedicada para que el Jefe QA resuelva conflictos manualmente: comparación lado a lado (versión local vs servidor) con elección.

## Acceptance Criteria
- Vista diff: versión local vs versión servidor
- Botones: "Usar local" / "Usar servidor"
- Resolución registrada en audit log
- Notificación al analista afectado

## Plan de Tests
- Resolver conflicto local → server version descartada
- Resolver conflicto server → local version descartada
- Audit log registra quién resolvió y cuándo

## Archivos de referencia
offline-sync-implementation-plan.md#Wave3
