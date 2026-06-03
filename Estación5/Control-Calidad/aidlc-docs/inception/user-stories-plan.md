# User Stories Plan — Control de Calidad Textil
**Date**: 2026-05-26 | **Personas**: 6 | **Stories Totales**: 30 | **MVP 30d Scope**: 18 stories | **Estimación**: Small/Medium/Large

---

## 🎯 TIMELINE ACTUALIZADO
- **Semana 1-4 (30 días)**: MVP Inspección + Aprobación + Maestros (18 stories)
- **Semana 5-8 (30 días)**: v1.1 Análisis + Sincronización ACATEX + Testing
- **Semana 9-12 (30 días)**: Go-live + Medición + Roadmap v2

---

## 👥 PERSONAS (6)

| # | Persona | Rol | Módulos | Questions Clave |
|---|---------|-----|---------|-----------------|
| **1** | Analista de Calidad | Daily User | Inspección | ¿Capturar foto rápido? ¿Offline? |
| **2** | Jefe de Calidad | Power User + Approver | Aprobación + Análisis | ¿Aprobar 50 lotes/hora? ¿Notificaciones? |
| **3** | Gerente de Planta | Executive | Análisis | ¿Ver -% en tiempo real? ¿Exportar reporte? |
| **4** | Jefe de Procesos | Data-Driven | Análisis | ¿Qué máquina falla más? ¿Sugerencias? |
| **5** | Admin / IT | System Config | Maestros + Config | ¿Agregar defectos nuevos? ¿Integrar ACATEX? |
| **6** | Sistema (Automated) | Process | Sincronización | ¿Traer maestros automáticamente? |

---

## 📋 MÓDULOS Y STORIES (30 Total)

### Módulo 1: Inspección — 8 Stories (Analista)

| Story | Título | Estimación |
|-------|--------|-----------|
| INS-001 | Buscar/escanear lote HDR | **Small** |
| INS-002 | Capturar foto del defecto | **Medium** |
| INS-003 | Seleccionar tipo defecto (dropdown) | **Small** |
| INS-004 | Escribir comentario obligatorio | **Small** |
| INS-005 | Confirmar máquina culpable (editable) | **Small** |
| INS-006 | Check-in/check-out automático | **Medium** |
| INS-007 | Guardar offline + sincronizar cuando hay wifi | **Large** |
| INS-008 | Ver historial de mis inspecciones | **Small** |

---

### Módulo 2: Aprobación — 5 Stories (Jefe QA)

| Story | Título | Estimación |
|-------|--------|-----------|
| APR-001 | Ver lotes pendientes aprobación | **Small** |
| APR-002 | Ver foto grande + detalles lote | **Medium** |
| APR-003 | Aprobar reproceso | **Small** |
| APR-004 | Rechazar lote | **Small** |
| APR-005 | Notificar Gerente automáticamente | **Medium** |

---

### Módulo 3: Análisis — 6 Stories (Jefe QA / Gerente / Jefe Procesos)

| Story | Título | Estimación |
|-------|--------|-----------|
| ANL-001 | Dashboard: Total reprocesos hoy/semana/mes | **Medium** |
| ANL-002 | Gráfico % reprocesos POR MÁQUINA | **Medium** |
| ANL-003 | Gráfico % reprocesos POR TIPO DEFECTO | **Medium** |
| ANL-004 | Gráfico % reprocesos POR TELA | **Medium** |
| ANL-005 | Aplicar filtros (período, máquina, defecto, tela) | **Medium** |
| ANL-006 | Exportar reporte PDF/Excel | **Medium** |

---

### Módulo 4: Maestros — 4 Stories (Admin)

| Story | Título | Estimación |
|-------|--------|-----------|
| MAE-001 | CRUD Defectos (crear, editar, inactivar) | **Small** |
| MAE-002 | CRUD Máquinas | **Small** |
| MAE-003 | CRUD Telas | **Small** |
| MAE-004 | Cargar maestros iniciales | **Medium** |

---

### Módulo 5: Sincronización — 3 Stories (Sistema)

| Story | Título | Estimación |
|-------|--------|-----------|
| SIN-001 | Integración opcional ACATEX (SÍ/NO en setup) | **Small** |
| SIN-002 | Traer maestros de ACATEX automáticamente | **Large** |
| SIN-003 | Enviar resultado inspección a ACATEX | **Large** |

---

### Módulo 6: Configuración — 4 Stories (Admin)

| Story | Título | Estimación |
|-------|--------|-----------|
| CON-001 | Setup inicial (empresa, integración ACATEX) | **Medium** |
| CON-002 | Gestión usuarios y roles (CRUD + RBAC) | **Medium** |
| CON-003 | Habilitar/deshabilitar auditoría | **Small** |
| CON-004 | Ver logs de sincronización | **Small** |

---

## ✅ DISTRIBUCIÓN DE TAMAÑO

| Tamaño | Count | Esfuerzo Total |
|--------|-------|----------------|
| **Small** | 12 | 12 días (1 dev, 1 día cada) |
| **Medium** | 16 | 32 días (2 días cada) |
| **Large** | 2 | 10 días (5 días cada) |
| **TOTAL** | 30 | ~54 días (base) + overhead |

**Timeline**: 90 días = 54 dev-days + 2 devs + testing = ✅ Viable

---

## 📝 PRÓXIMO PASO: GENERAR STORIES DETALLADAS

Cuando apruebes, generaré:
- ✅ 30 stories completas (As a... I want... So that...)
- ✅ Acceptance Criteria por story (2-4 criterios)
- ✅ Technical Notes donde aplique
- ✅ Referencia a Requirements Analysis

---

**Status**: ⏳ AWAITING APPROVAL

**Pregunta**: ¿Aprobado? → Procederemos a generar las 30 historias detalladas.

