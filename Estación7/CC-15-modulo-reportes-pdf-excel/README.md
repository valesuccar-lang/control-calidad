# CC-15 — Módulo Reportes PDF/Excel

**Milestone:** M2 | **Estimado:** 5d | **Prioridad:** medium
**Unidad:** frontend-web-unidad-2 | **Depende de:** CC-14

## Definición
Exportación de reportes de inspecciones y análisis en formato PDF y Excel, con filtros por período, máquina y tipo de defecto.

## Acceptance Criteria
- Exportar lista de inspecciones filtrada a Excel
- Exportar reporte ejecutivo a PDF con gráficos
- Generación en <10s para períodos de 30 días
- PDF incluye logo Manufacturas Eliot y fecha de generación

## Plan de Tests
- Export Excel: archivo descargado con datos correctos
- Export PDF: gráficos renderizados correctamente
- Test 1000 registros → export <10s

## Archivos de referencia
frontend-web-implementation-plan.md#Wave2
