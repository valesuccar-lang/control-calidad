# CC-17 — IndexedDB setup + integración Zustand

**Milestone:** M2 | **Estimado:** 5d | **Prioridad:** high
**Unidad:** offline-unidad-4 | **Depende de:** CC-16

## Definición
Diseñar esquema IndexedDB (tablas: inspections, approvals, sync_queue), integrar con stores Zustand y manejar versiones/migraciones de BD local.

## Acceptance Criteria
- IndexedDB inicializa en primer load
- Tablas: inspections, approvals, sync_queue creadas
- Zustand store persiste en IndexedDB automáticamente
- Migración de versión funciona sin pérdida de datos
- CRUD operations en IndexedDB funcionan

## Plan de Tests
- Crear inspección offline → aparece en IndexedDB
- Reload página → datos persisten
- Test migración: v1 → v2 schema sin pérdida

## Archivos de referencia
offline-sync-implementation-plan.md#Fase2, domain-entities.md
