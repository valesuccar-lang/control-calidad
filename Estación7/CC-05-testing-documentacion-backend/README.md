# CC-05 — Testing y documentación Backend

**Milestone:** M1 | **Estimado:** 8d | **Prioridad:** high
**Unidad:** backend-api-unidad-1 | **Depende de:** CC-03, CC-04

## Definición
Alcanzar ≥80% cobertura con pytest, documentación OpenAPI completa, load testing básico y README con instrucciones de deploy.

## Acceptance Criteria
- pytest-cov reporta ≥80% cobertura en módulos de negocio
- Swagger UI funcional en /docs
- Load test: P95 ≤500ms con 50 usuarios concurrentes
- README incluye: setup, variables de entorno, comandos de deploy

## Plan de Tests
- Correr pytest --cov=app --cov-report=html
- Verificar /docs accesible y schemas correctos
- Locust/k6: 50 VUs × 60s en endpoints críticos

## Archivos de referencia
build-and-test/build-instructions.md, unit-test-instructions.md, integration-test-instructions.md
