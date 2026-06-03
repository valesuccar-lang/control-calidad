# CC-16 — Service Worker + detección offline

**Milestone:** M2 | **Estimado:** 5d | **Prioridad:** high
**Unidad:** offline-unidad-4 | **Depende de:** CC-09

## Definición
Registrar Service Worker con lifecycle management, detectar eventos online/offline, mostrar indicador visual de conectividad y aplicar cache strategy network-first.

## Acceptance Criteria
- Service Worker registrado y activo en /sw.js
- Banner visible cuando no hay red: "Sin conexión"
- Banner verde cuando se reconecta: "Conectado — sincronizando..."
- Assets estáticos en cache (HTML, CSS, JS)
- Network-first para llamadas API

## Plan de Tests
- Chrome DevTools: offline mode → banner visible
- Reconectar → banner desaparece, sync inicia
- Reload offline → app carga desde cache

## Archivos de referencia
offline-sync-implementation-plan.md#Fase1, ADR-003-offline-storage-indexeddb-service-worker.md
