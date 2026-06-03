# CC-11 — DB + APIs Maestros backend (Unidad 3)

**Milestone:** M1 | **Estimado:** 10d | **Prioridad:** high
**Unidad:** maestros-unidad-3 | **Depende de:** CC-01

## Definición
Tablas y APIs para los 3 catálogos maestros con seed data inicial, CRUD completo, soft delete, audit logging y validaciones de datos.

## Acceptance Criteria
- Tablas: defects, machines, fabrics, import_logs, change_logs
- CRUD endpoints funcionando con paginación
- Seed data: 25 tipos de defecto + máquinas iniciales
- Soft delete operativo
- Audit log en cada operación CRUD

## Plan de Tests
- Seed data carga sin errores en DB limpia
- Test CRUD completo por cada catálogo
- Test soft delete no rompe inspecciones existentes

## Archivos de referencia
maestros-implementation-plan.md, domain-entities.md, Business-Rules.md
