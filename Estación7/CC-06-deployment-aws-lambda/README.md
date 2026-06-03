# CC-06 — Deployment Backend en AWS Lambda + RDS

**Milestone:** M1 | **Estimado:** 2d | **Prioridad:** high
**Unidad:** backend-api-unidad-1 | **Depende de:** CC-05

## Definición
Buildear imagen Docker multi-stage, deployar en AWS Lambda con Mangum, conectar a RDS PostgreSQL y ejecutar smoke tests en staging.

## Acceptance Criteria
- Docker image < 500MB buildea sin errores
- Lambda responde en < 3s en cold start
- RDS connection estable (pool configurado)
- Variables de entorno en AWS Secrets Manager
- Smoke tests: /health, /auth/login, /inspections retornan 200

## Plan de Tests
- docker build exitoso
- Lambda invoke manual desde consola AWS
- Smoke tests automatizados en pipeline post-deploy

## Archivos de referencia
deployment-architecture.md, infrastructure-design.md
