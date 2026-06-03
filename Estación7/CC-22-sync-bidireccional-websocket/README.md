# CC-22 — Sync bidireccional via WebSocket

**Milestone:** M3 | **Estimado:** 8d | **Prioridad:** medium
**Unidad:** offline-unidad-4 | **Depende de:** CC-21

## Definición
Implementar sincronización bidireccional via WebSocket para que cambios del servidor lleguen al cliente en tiempo real.

## Acceptance Criteria
- WebSocket conecta automáticamente al iniciar sesión
- Nueva aprobación en servidor → aparece en cliente <2s
- Cambio en maestros → refresh automático
- Reconexión automática si WebSocket cae
- Funciona con múltiples tabs abiertas

## Plan de Tests
- Aprobar desde Tab A → Tab B actualiza en <2s
- Cerrar WebSocket → reconexión automática en <10s
- 20 clientes simultáneos → sin degradación

## Archivos de referencia
offline-sync-implementation-plan.md#Wave3, Infrastructure-Design-Services.md
