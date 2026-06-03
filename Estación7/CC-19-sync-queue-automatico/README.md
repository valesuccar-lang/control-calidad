# CC-19 — Sync Queue + mecanismo automático

**Milestone:** M2 | **Estimado:** 5d | **Prioridad:** high
**Unidad:** offline-unidad-4 | **Depende de:** CC-18

## Definición
Implementar cola de sincronización con timestamp, operación y estado, sincronización automática al reconectar, sync manual (botón) y exponential backoff para reintentos fallidos.

## Acceptance Criteria
- Al reconectar: sync automático inicia en <5s
- Botón "Sincronizar ahora" disponible cuando hay pendientes
- Exponential backoff: 1s, 2s, 4s, 8s (max 5 intentos)
- Estado en UI: "3 inspecciones pendientes de sync"
- Sync exitoso → items marcados "synced", salen de queue

## Plan de Tests
- Reconectar → sync automático en <5s
- Forzar fallo servidor → reintentos con backoff
- 50 items en queue → todos synced en orden correcto

## Archivos de referencia
offline-sync-implementation-plan.md#Fase4, NFR-Requirements.md
