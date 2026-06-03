# CC-23 — Batch sync + compresión de datos

**Milestone:** M3 | **Estimado:** 5d | **Prioridad:** low
**Unidad:** offline-unidad-4 | **Depende de:** CC-22

## Definición
Optimizar sincronización agrupando múltiples operaciones en un solo request y comprimiendo payload para reducir uso de datos en conexiones lentas.

## Acceptance Criteria
- Batch de hasta 50 operaciones en 1 request POST /sync
- Compresión gzip en payloads >1KB
- Sync de 200 inspecciones offline <30s
- Historial de sincronización visible al usuario

## Plan de Tests
- 200 items offline → sync en <30s
- Payload comprimido <50% del original
- Historial muestra últimas 20 sincronizaciones

## Archivos de referencia
offline-sync-implementation-plan.md#Wave3, NFR-Requirements.md
