# CC-09 — Módulo Inspección UI

**Milestone:** M1 | **Estimado:** 6d | **Prioridad:** urgent
**Unidad:** frontend-web-unidad-2 | **Depende de:** CC-08, CC-03

## Definición
Formulario de inspección mobile-first: búsqueda de lote, captura de foto, selección de tipo de defecto (25+ opciones), comentario obligatorio ≥10 chars, confirmación de máquina e historial de inspecciones propias.

## Acceptance Criteria
- Búsqueda de lote por código HDR en ≤2s
- Captura de foto desde cámara del dispositivo
- Dropdown con ≥25 tipos de defecto
- Validación: comentario ≥10 caracteres
- Máquina pre-rellenada, editable
- Historial muestra últimas 50 inspecciones del usuario
- Funciona en pantallas de 375px (móvil)

## Plan de Tests
- Cypress/Playwright: flujo completo de inspección end-to-end
- Test validación: submit sin foto → error visible
- Test responsive: render correcto en 375px y 1440px

## Archivos de referencia
frontend-business-logic-model.md, frontend-business-rules.md, requirements-analysis.md#Módulo1
