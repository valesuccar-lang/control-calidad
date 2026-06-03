# CC-08 — Auth Frontend + Layout principal

**Milestone:** M1 | **Estimado:** 3d | **Prioridad:** urgent
**Unidad:** frontend-web-unidad-2 | **Depende de:** CC-07, CC-03

## Definición
Pantalla de login con manejo de tokens JWT, sidebar de navegación, header con usuario activo y contexto global de usuario.

## Acceptance Criteria
- Login page funcional con validación de campos
- Token almacenado en memoria (no localStorage por seguridad)
- Sidebar muestra opciones según rol del usuario
- Logout limpia estado y redirige a /login
- Sesión expira y redirige automáticamente

## Plan de Tests
- Login con credenciales válidas → dashboard
- Login con credenciales inválidas → mensaje de error
- Token expirado → redirect automático a /login

## Archivos de referencia
frontend-web-implementation-plan.md#Fase2, ADR-001-authentication-jwt-strategy.md
