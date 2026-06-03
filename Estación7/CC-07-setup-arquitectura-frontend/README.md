# CC-07 — Setup y arquitectura Frontend

**Milestone:** M1 | **Estimado:** 3d | **Prioridad:** urgent
**Unidad:** frontend-web-unidad-2 | **Depende de:** ninguna

## Definición
Configurar Vite + React 18 + TypeScript, stores Zustand, Tailwind CSS, React Router y cliente HTTP axios con interceptors JWT.

## Acceptance Criteria
- Proyecto compila sin errores TypeScript
- Stores Zustand: Auth, Inspection, Approval, Master
- Axios interceptor agrega Bearer token automáticamente
- React Router con protected routes configurado
- Tailwind + design tokens básicos

## Plan de Tests
- npm run build exitoso
- Vitest: stores inicializan en estado correcto
- Navegación a ruta protegida sin token → redirect a /login

## Archivos de referencia
frontend-web-implementation-plan.md#Fase1, ADR-002-state-management-zustand.md, ADR-001-authentication-jwt-strategy.md
