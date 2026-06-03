# CC-10 — Módulo Aprobación UI

**Milestone:** M1 | **Estimado:** 4d | **Prioridad:** urgent
**Unidad:** frontend-web-unidad-2 | **Depende de:** CC-08, CC-03

## Definición
Vista de pendientes para Jefe QA: lista de inspecciones pendientes, detalle con foto fullscreen, botones Aprobar/Rechazar con notificación al gerente de calidad.

## Acceptance Criteria
- Lista muestra inspecciones pendientes paginadas
- Foto abre en modal fullscreen
- Aprobar/Rechazar actualiza estado en tiempo real
- Notificación enviada al Gerente de Calidad post-aprobación
- Solo visible para roles QA y Manager

## Plan de Tests
- Test RBAC: Analyst no ve menú de Aprobación
- Test flujo: aprobar inspección → desaparece de pendientes
- Test foto: click → modal fullscreen

## Archivos de referencia
frontend-web-implementation-plan.md#Fase4, requirements-analysis.md#Módulo2
