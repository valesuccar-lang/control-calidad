# CC-20 — Detección de conflictos en sincronización

**Milestone:** M2 | **Estimado:** 6d | **Prioridad:** medium
**Unidad:** offline-unidad-4 | **Depende de:** CC-19

## Definición
Implementar detección de conflictos (last-write-wins básico + comparación de versiones), marcar items conflictuados para revisión manual y detectar conflictos en Aprobaciones.

## Acceptance Criteria
- Last-write-wins aplicado automáticamente en conflictos simples
- Conflicto de Aprobación → marcado para revisión manual
- UI muestra lista de items conflictuados con opción de resolver
- Version field en cada entidad sincronizada

## Plan de Tests
- Simular edición simultánea → last-write-wins aplicado
- Aprobación conflictuada → aparece en lista de conflictos
- Resolver conflicto manualmente → item synced

## Archivos de referencia
offline-sync-implementation-plan.md#Fase5, NFR-Design-Consolidated.md
