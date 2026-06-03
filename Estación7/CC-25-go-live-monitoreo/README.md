# CC-25 — Go-live + monitoreo en producción

**Milestone:** M3 | **Estimado:** 3d | **Prioridad:** urgent
**Unidad:** transversal | **Depende de:** CC-24

## Definición
Deploy final a producción AWS, configurar alertas de monitoreo, capacitación a 20 analistas y seguimiento de adopción semana 1.

## Acceptance Criteria
- Sistema disponible en URL de producción
- CloudWatch alertas: error rate >5%, latencia P95 >2s
- 20 analistas capacitados (sesión hands-on 1h)
- Adopción día 1: ≥50% analistas con al menos 1 inspección
- Runbook de incidentes documentado

## Plan de Tests
- Smoke tests en producción post-deploy
- Alerta disparada manualmente → notificación recibida
- Métricas de adopción visibles en dashboard

## Archivos de referencia
deployment-architecture.md, Deployment-Architecture.md
