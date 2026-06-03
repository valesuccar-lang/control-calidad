# CC-14 — Módulo Análisis con gráficos

**Milestone:** M2 | **Estimado:** 8d | **Prioridad:** high
**Unidad:** frontend-web-unidad-2 | **Depende de:** CC-10

## Definición
Dashboard ejecutivo con gráficos de reprocesos por tela/máquina/turno, tendencias temporales y KPIs clave para Gerente y CEO.

## Acceptance Criteria
- Gráfico de barras: top 10 defectos por tipo
- Gráfico de línea: tendencia reprocesos últimos 30 días
- Mapa de calor: % reprocesos por máquina
- KPIs: total reprocesos hoy, % vs ayer, meta -30%
- Filtros: fecha, línea, turno
- Datos actualizados cada 5 minutos

## Plan de Tests
- Test gráficos renderizan con datos vacíos sin error
- Test filtros actualizan gráficos correctamente
- Test performance: dashboard carga en <2s

## Archivos de referencia
frontend-web-implementation-plan.md#Wave2, requirements-analysis.md#Módulo3
