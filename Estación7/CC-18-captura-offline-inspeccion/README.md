# CC-18 — Captura offline en módulo Inspección

**Milestone:** M2 | **Estimado:** 5d | **Prioridad:** high
**Unidad:** offline-unidad-4 | **Depende de:** CC-17, CC-09

## Definición
Modificar el módulo Inspección para guardar en IndexedDB cuando no hay red, mostrar indicador "pendiente de sync" y manejar errores de almacenamiento local.

## Acceptance Criteria
- Inspección creada offline → guardada en IndexedDB con status "pending"
- UI muestra badge "Pendiente sync" en inspecciones offline
- Error si disco lleno → mensaje claro al usuario
- Validación local funciona igual que online
- Foto almacenada como Blob en IndexedDB

## Plan de Tests
- Offline → crear inspección → aparece con badge pending
- Disk full simulation → error manejado gracefully
- Foto capturada offline → persiste en IndexedDB

## Archivos de referencia
offline-sync-implementation-plan.md#Fase3, Business-Rules.md
