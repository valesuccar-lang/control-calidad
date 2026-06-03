# CC-12 — Bulk Import CSV/Excel (Unidad 3)

**Milestone:** M1 | **Estimado:** 5d | **Prioridad:** medium
**Unidad:** maestros-unidad-3 | **Depende de:** CC-11

## Definición
Endpoints de importación masiva para los 3 catálogos con validación previa, rollback en error, background jobs Celery para archivos grandes y reporte de resultados.

## Acceptance Criteria
- POST /import/{defects|machines|fabrics} acepta CSV y XLSX
- Validación retorna errores por fila antes de insertar
- Rollback completo si hay error en cualquier fila
- Celery job para archivos >1000 filas
- Reporte: N exitosos, M errores con detalle por fila

## Plan de Tests
- Import CSV válido → todos los registros insertados
- Import CSV con 1 fila inválida → rollback total
- Import 5000 filas → job asíncrono completado

## Archivos de referencia
maestros-implementation-plan.md#Fase3
