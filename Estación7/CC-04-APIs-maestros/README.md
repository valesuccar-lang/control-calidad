# CC-04 — APIs Maestros: Defectos, Máquinas, Telas

**Milestone:** M1 | **Estimado:** 5d | **Prioridad:** high
**Unidad:** backend-api-unidad-1 | **Depende de:** CC-02

## Definición
Implementar CRUD completo para los 3 catálogos maestros (Defectos, Máquinas, Telas) con soft delete, paginación, filtros y audit logging en cada operación.

## Acceptance Criteria
- CRUD para /defects, /machines, /fabrics
- Soft delete (inactivar, no borrar físicamente)
- Paginación en listados (page, size, total)
- Filtros por nombre, código, estado
- Audit log registrado por cada cambio (quién, cuándo, qué)

## Plan de Tests
- Test soft delete: item inactivado no aparece en listados activos
- Test audit log: cada PUT genera entrada en audit_log
- Test paginación: página 2 con size=10 retorna items correctos

## Archivos de referencia
construction/Maestroyconfiguracion-unidad3/Business-Rules.md, domain-entities.md
