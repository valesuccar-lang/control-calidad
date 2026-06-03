# Milestones — Control de Calidad Textil
**Project**: Sistema de Gestión de Control de Calidad (Manufacturas Eliot)  
**Planning Wave**: entrevista-auth-lambda-implementation  
**Generated**: 2026-06-02

---

## M1 — MVP Foundation (Días 1–30)
**Objetivo**: Sistema operativo para Analistas y Jefe QA con captura, aprobación y maestros.  
**Meta de negocio**: 100% defectos capturados con foto + tipo + máquina + timestamp.

| Task ID | Título | Unidad |
|---------|--------|--------|
| CC-01 | Setup Backend API (infra + proyecto) | U1 Backend |
| CC-02 | Dominio y entidades (DDD) | U1 Backend |
| CC-03 | APIs core: Auth, Inspección, Aprobación | U1 Backend |
| CC-04 | APIs Maestros (Defectos, Máquinas, Telas) | U1 Backend |
| CC-05 | Testing y documentación Backend | U1 Backend |
| CC-06 | Deployment Backend (AWS Lambda + RDS) | U1 Backend |
| CC-07 | Setup y arquitectura Frontend | U2 Frontend |
| CC-08 | Auth Frontend + Layout | U2 Frontend |
| CC-09 | Módulo Inspección UI | U2 Frontend |
| CC-10 | Módulo Aprobación UI | U2 Frontend |
| CC-11 | DB + APIs Maestros backend | U3 Maestros |
| CC-12 | Bulk Import (CSV/Excel) | U3 Maestros |
| CC-13 | Frontend Maestros UI | U3 Maestros |

---

## M2 — Enhancement Wave (Días 31–60)
**Objetivo**: Análisis de datos, reportes, modo offline básico y sincronización.  
**Meta de negocio**: Dashboard ejecutivo listo para CEO. -30% reprocesos medible.

| Task ID | Título | Unidad |
|---------|--------|--------|
| CC-14 | Módulo Análisis (gráficos) | U2 Frontend |
| CC-15 | Módulo Reportes (PDF/Excel) | U2 Frontend |
| CC-16 | Service Worker + detección offline | U4 Offline |
| CC-17 | IndexedDB setup + integración Zustand | U4 Offline |
| CC-18 | Captura offline (Inspección sin red) | U4 Offline |
| CC-19 | Sync Queue + mecanismo automático | U4 Offline |
| CC-20 | Detección de conflictos | U4 Offline |

---

## M3 — Optimization & Go-Live (Días 61–90)
**Objetivo**: Resolución de conflictos, sync bidireccional, go-live en planta.  
**Meta de negocio**: ≥90% adopción analistas. Sistema estable en producción.

| Task ID | Título | Unidad |
|---------|--------|--------|
| CC-21 | UI resolución de conflictos | U4 Offline |
| CC-22 | Sync bidireccional (WebSocket) | U4 Offline |
| CC-23 | Batch sync + compresión | U4 Offline |
| CC-24 | E2E testing + performance | Transversal |
| CC-25 | Go-live + monitoreo producción | Transversal |
