# Workflow Planning — Control de Calidad Textil
**Date**: 2026-05-26 | **Status**: PLANNING PHASE | **Timeline**: 90 días total

---

## 📊 FASES DEL PROYECTO

```
┌──────────────────────────────────────────────────────────────────┐
│                    INCEPTION PHASE (HOY)                         │
│  ✅ Workspace Detection                                          │
│  ✅ Requirements Analysis                                        │
│  ✅ User Stories Plan                                            │
│  ➡️  Workflow Planning (ACTUAL)                                  │
│  ➡️  Application Design (SIGUIENTE)                              │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│               CONSTRUCTION PHASE (Semana 1-4, 30 días)            │
│  - Per-Unit Loop: 4 módulos principales                          │
│    Per cada módulo: Functional Design + Code Generation          │
│  - Build & Test: Unit + Integration + E2E                        │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│          OPERATIONS PHASE (Semana 5-12, 60 días)                 │
│  - Testing avanzado + Piloto controlado (Semana 5-8)             │
│  - Go-live + Medición + Roadmap v2 (Semana 9-12)                │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ UNITS DE CONSTRUCCIÓN (Per-Unit Loop)

Según el Scope MVP 30d, tendremos **4 unidades de construcción**:

### Unit 1: Backend API (Python FastAPI)
**Responsabilidad**: Servicios REST para todas las operaciones  
**Stories**: INS-001-007, APR-001-004, MAE-001-004, CON-001-002  
**Duración Estimada**: 10 días (1 dev)  
**Deliverable**: API running en localhost

### Unit 2: Frontend Web (React + TypeScript)
**Responsabilidad**: UI para Analista + Jefe QA + Admin  
**Stories**: INS-001-007, APR-001-004, MAE-001-004, CON-001-002  
**Duración Estimada**: 12 días (1 dev — tu especialidad)  
**Deliverable**: Web app running en localhost

### Unit 3: Maestros y Configuración (Backend)
**Responsabilidad**: CRUD defectos, máquinas, telas + setup inicial  
**Stories**: MAE-001-004, CON-001-002  
**Duración Estimada**: 4 días (backend)  
**Deliverable**: Maestros funcionales, setup completable

### Unit 4: Base de Datos y Sincronización Offline (Backend)
**Responsabilidad**: Schema SQL, sincronización offline→online  
**Stories**: INS-007 (guardar offline), sincronización básica  
**Duración Estimada**: 4 días (backend)  
**Deliverable**: Offline-first funcional, cero pérdida de datos

---

## 📅 SECUENCIA DE CONSTRUCCIÓN (Orden Recomendado)

```
Semana 1: Unit 3 + Unit 4 (Infraestructura base)
  ├─ Unit 3: Maestros CRUD (4 días)
  └─ Unit 4: BD Schema + Offline-first (4 días)

Semana 2-3: Unit 1 (Backend API completo)
  └─ Unit 1: APIs Inspección + Aprobación (10 días)

Semana 3-4: Unit 2 (Frontend web)
  └─ Unit 2: React UI Inspección + Aprobación (12 días)

Semana 4: Build & Test
  ├─ Unit tests (backend + frontend)
  ├─ Integration tests
  ├─ E2E tests
  └─ Bug fixes críticos
```

**Lógica**: Infraestructura primero → APIs → Frontend. Frontend depende de APIs.

---

## 🎯 PROFUNDIDAD POR FASE (Construction)

### Per-Unit: Functional Design
**Ejecutar**: ✅ SÍ (cada unit)  
**Razón**: Necesitamos entender models, schemas, flows antes de codear  
**Profundidad**: STANDARD (especificación clara, no exceso)

### Per-Unit: NFR Requirements
**Ejecutar**: ✅ SÍ (especialmente Units 1, 4)  
**Razón**: Performance, seguridad, offline-first son críticos  
**Profundidad**: COMPREHENSIVE (queremos que funcione en producción)

### Per-Unit: NFR Design
**Ejecutar**: ✅ SÍ (especialmente Units 1, 4)  
**Razón**: Implementar patrones para performance y confiabilidad  
**Profundidad**: COMPREHENSIVE

### Per-Unit: Infrastructure Design
**Ejecutar**: ⏳ CONDICIONAL (Unit 1 si hay cloud)  
**Razón**: MVP es on-premise (SQL Server local), no cloud aún  
**Si aplica**: Local PostgreSQL + Python FastAPI local

### Per-Unit: Code Generation
**Ejecutar**: ✅ SIEMPRE (todos los units)  
**Profundidad**: COMPREHENSIVE (genera tests también)

### Build & Test
**Ejecutar**: ✅ SIEMPRE  
**Profundidad**: COMPREHENSIVE (unit + integration + E2E)

---

## 📋 MÓDULOS QUE NO CONSTRUIMOS EN MVP 30d

| Módulo | Razón | Versión |
|--------|-------|---------|
| **Análisis (6 stories)** | Scope reducido, too big for 30d | v1.1 (Semana 5-8) |
| **Sincronización ACATEX (3 stories)** | Depende de APIs ACATEX (aún pending) | v1.1 (Semana 5-8) |
| **Notificaciones automáticas** | Nice-to-have, no crítico para MVP | v1.1 (Semana 5-8) |

---

## 📊 MATRIX DE FASES × UNITS

| Unit | Functional Design | NFR Requirements | NFR Design | Infrastructure | Code Gen | Build & Test |
|------|---|---|---|---|---|---|
| **1: Backend API** | ✅ STANDARD | ✅ COMP | ✅ COMP | ❌ N/A | ✅ COMP | ✅ COMP |
| **2: Frontend Web** | ✅ STANDARD | ✅ STANDARD | ✅ STANDARD | ❌ N/A | ✅ COMP | ✅ COMP |
| **3: Maestros** | ✅ STANDARD | ❌ N/A | ❌ N/A | ❌ N/A | ✅ STANDARD | ✅ STANDARD |
| **4: Offline-First** | ✅ STANDARD | ✅ COMP | ✅ COMP | ❌ N/A | ✅ COMP | ✅ COMP |

**Leyenda**: STANDARD = suficiente para MVP | COMP = comprehensive (production-ready) | N/A = no aplica

---

## 🎯 RECOMENDACIÓN GENERAL

### Enfoque Recomendado para 30 días:

1. ✅ **Ejecutar TODAS las fases de Inception** (hoy):
   - Workspace Detection ✅
   - Requirements Analysis ✅
   - User Stories (planar, generar luego)
   - Workflow Planning ← ACTUAL
   - Application Design (siguiente)

2. ✅ **Ejecutar Construction completo** (Semana 1-4):
   - Functional Design + NFR Design para cada unit
   - Code Generation full
   - Build & Test comprehensive

3. ✅ **Esperar al testing para v1.1** (Semana 5-8):
   - Validación piloto
   - Feedback analistas
   - Agregar Análisis + ACATEX en v1.1

4. ⏳ **Operations** (Semana 9-12):
   - Go-live controlado
   - Medición de impacto
   - Roadmap v2

---

## ✅ DECISIONES CRÍTICAS (User Input Needed)

### Decisión 1: ¿Quién construye?
| Opción | Implicación |
|--------|-----------|
| **1 dev (tú)** | Secuencial: Backend semanas 1-2, Frontend semanas 3-4 (posible pero ajustado) |
| **2+ devs** | Paralelo: Backend + Frontend simultáneo (mejor para 30d) |

**Recomendación**: Si tienes acceso a 1 dev backend + tú (frontend) = ✅ paralelo es posible

### Decisión 2: ¿Base de datos local o cloud?
| Opción | Implicación |
|--------|-----------|
| **PostgreSQL local** | Más simple, sin costos, alineado con Eliot infrastructure |
| **Cloud (AWS RDS)** | Más escalable, pero costo + setup complejo |

**Recomendación**: PostgreSQL local en Eliot (más simple para 30d)

### Decisión 3: ¿PWA (Progressive Web App) o App Nativa?
| Opción | Implicación |
|--------|-----------|
| **PWA (web responsive)** | Una codebase, funciona offline, instalar en home screen |
| **React Native** | App nativa iOS/Android, pero +2 semanas |

**Recomendación**: PWA (cabe en 30d, mismo React)

---

## 📈 TIMELINE FINAL (Recomendado)

```
HOY (26 Mayo):
└─ Inception: Workflow Planning + Application Design (2-3 días)

Semana 1 (Lunes 1 Junio):
├─ Unit 3 + 4: Infraestructura (BD, maestros, offline-first) — 4-5 días
├─ Code Gen: Backend basic structure
└─ Build: Environment setup

Semana 2-3 (Junio 8-21):
├─ Unit 1: Backend API (10 días paralelos)
├─ Unit 2: Frontend Web (12 días paralelos — TÚ)
└─ Code Gen ambos units

Semana 4 (Junio 22-28):
├─ Build & Test (unit + integration + E2E)
├─ Bug fixes críticos
└─ MVP Ready ✅

Semana 5-8 (Julio):
├─ v1.1: Análisis + ACATEX + Testing piloto
└─ Ready para go-live beta

Semana 9-12 (Agosto):
├─ Go-live producción (20 analistas)
├─ Medición -% reprocesos
└─ Roadmap v2
```

---

## ✅ PRÓXIMOS PASOS

1. ✅ **Hoy**: Aprobación Workflow Planning
2. **Mañana**: Application Design (componentes, BD schema, API contracts)
3. **Luego**: Code Generation empieza
4. **Fin Semana**: MVP arquitectura completada

---

**Status**: ⏳ AWAITING USER APPROVAL

**Preguntas a responder**:
- [ ] ¿Tienes 1 dev backend disponible (paralelo) o solo tú (secuencial)?
- [ ] ¿PostgreSQL local o preferencia diferente?
- [ ] ¿PWA es suficiente o necesitas app nativa?

