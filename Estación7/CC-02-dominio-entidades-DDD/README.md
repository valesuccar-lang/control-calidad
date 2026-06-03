# CC-02 — Implementar dominio y entidades DDD

**Milestone:** M1 | **Estimado:** 3d | **Prioridad:** urgent
**Unidad:** backend-api-unidad-1 | **Depende de:** CC-01

## Definición
Implementar las entidades de dominio (Inspection, Approval, User, AuditLog), Value Objects (DefectType, MachineStatus) y reglas de negocio con validación.

## Acceptance Criteria
- Entidades con validación Pydantic v2
- Value Objects inmutables
- SQLAlchemy ORM models mapeados
- Business rules validadas en capa de dominio
- 100% cobertura en tests de entidades

## Plan de Tests
- Unit tests: crear entidad válida e inválida por cada tipo
- Test de Value Objects (igualdad, inmutabilidad)
- Test de business rules (ej. comentario ≥10 chars)

## Archivos de referencia
construction/backend-api-unidad 1/domain-entities.md, business-rules.md, business-logic-model.md
