# Requirements Analysis — Control de Calidad Textil
**Project**: Sistema de Gestión de Control de Calidad Textil (Manufacturas Eliot)  
**Date**: 2026-05-26  
**Status**: COMPREHENSIVE ANALYSIS  
**Timeline**: 90 días (Semana 1-4: MVP | Semana 5-8: Testing | Semana 9-12: Go-live + Medición)

---

## 📌 RESUMEN EJECUTIVO

### Problema
Manufacturas Eliot registra **267,119 reprocesos/mes** en Excel + papeleta, sin:
- Registro fotográfico sistematizado
- Control de tiempos (timestamps)
- Trazabilidad completa
- Análisis por tela/máquina en tiempo real

**Costo**: ~$500K-1.3M USD/mes perdidos  
**Presión**: CEO exige -30% en 90 días

### Solución
**Sistema agéntico de QA fotográfico** que centraliza:
1. ✅ Captura de foto + tipo defecto + comentario (Analista)
2. ✅ Aprobación de reproceso (Jefe QA)
3. ✅ Análisis patrones + dashboards ejecutivos (Gerente/Jefe Procesos)
4. ✅ Integración opcional con ACATEX (maestros: telas, máquinas, lotes)

### Resultado Esperado
- **Trazabilidad completa**: Cada defecto = foto + tipo + máquina + timestamp + quién detectó
- **Análisis instantáneo**: Dashboard muestra % reprocesos por tela/máquina en tiempo real
- **Reducción medible**: -30% reprocesos en 90 días = $150K-400K USD/mes ahorrados

---

## 🎯 STAKEHOLDERS Y OBJETIVOS

### Personas Clave (del PRD)

| Persona | Rol | Objetivo | Poder Decisión |
|---------|-----|----------|---|
| **Jefe de Calidad** | Power User + Aprobador | Reducir reprocesos -30%, tener dashboard para CEO | ALTO |
| **Analista de Calidad** | Daily User (20 en planta) | Capturar defecto rápido desde celular, sin Excel | BAJO (pero buy-in crítico) |
| **Jefe de Procesos** | Data-Driven Decision | Ver análisis por máquina/turno para decisiones rápidas | MEDIO-ALTO |
| **Gerente de Planta** | Executive Sponsor | Mostrar progreso a CEO, ROI claro | MÁXIMO (budget) |
| **CEO** | Ultimate Sponsor | -30% reprocesos en 90 días | MÁXIMO (kill/go) |

### Objetivos Primarios
1. **Adopción**: ≥90% analistas usando sistema en Semana 12
2. **Reducción**: -30% reprocesos (267K → 187K lotes) en 90 días
3. **Trazabilidad**: 100% defectos con foto + tipo + máquina + timestamp
4. **Speed**: Respuesta a CEO en <10 minutos (vs. 2 horas hoy)

### Objetivos Secundarios
5. Precisión máquina culpable: ≥85%
6. Integración sin fricción con ACATEX (si aplica)
7. Offline-first: funciona sin wifi en piso

---

## 📋 REQUISITOS FUNCIONALES

### MVP SCOPE (Días 1-30) — Lo que SÍ construimos

#### MÓDULO 1: Inspección (Analista)
**Responsabilidad**: Capturar defecto desde celular en piso

| Requisito | Descripción | Prioridad |
|-----------|---|---|
| **F1.1** | Buscar/escanear lote (código HDR) desde app móvil | MUST |
| **F1.2** | Capturar foto clara del defecto (cámara integrada) | MUST |
| **F1.3** | Seleccionar tipo defecto del dropdown (25+ opciones textiles) | MUST |
| **F1.4** | Escribir comentario descriptivo (obligatorio ≥10 caracteres) | MUST |
| **F1.5** | Confirmar máquina culpable (pre-rellenada, editable) | MUST |
| **F1.6** | Check-in/check-out automático (timestamp, sin intervención) | MUST |
| **F1.7** | Guardar localmente (offline-first) + sincronizar cuando hay wifi | MUST |
| **F1.8** | Ver historial de mis inspecciones | SHOULD |

#### MÓDULO 2: Aprobación (Jefe QA)
**Responsabilidad**: Revisar y aprobar/rechazar defectos

| Requisito | Descripción | Prioridad |
|-----------|---|---|
| **F2.1** | Ver lista lotes pendientes aprobación | MUST |
| **F2.2** | Ver foto grande + comentario + tipo defecto + máquina | MUST |
| **F2.3** | Botón "Aprobar Reproceso" | MUST |
| **F2.4** | Botón "Rechazar Lote" | MUST |
| **F2.5** | Campo comentario interno (solo Jefe ve) | SHOULD |
| **F2.6** | Notificación automática a Gerente cuando aprueba | SHOULD |

#### MÓDULO 3: Análisis y Dashboards (Jefe QA / Gerente / Jefe Procesos)
**Responsabilidad**: Visualizar patrones, identificar máquinas problemáticas

| Requisito | Descripción | Prioridad |
|-----------|---|---|
| **F3.1** | Dashboard: Total reprocesos hoy/semana/mes | MUST |
| **F3.2** | Gráfico: % reprocesos POR MÁQUINA (top 5) | MUST |
| **F3.3** | Gráfico: % reprocesos POR TIPO DEFECTO (top 5) | MUST |
| **F3.4** | Gráfico: % reprocesos POR TELA (top 5) | MUST |
| **F3.5** | Filtros: Período, máquina, defecto, tela | MUST |
| **F3.6** | Galería de fotos: visualizar defecto con filtros | SHOULD |
| **F3.7** | Exportar reporte (PDF/Excel) | SHOULD |
| **F3.8** | Dashboard Ejecutivo (Gerente): 3 KPIs principales | MUST |

#### MÓDULO 4: Maestros (Admin / IT)
**Responsabilidad**: Mantener catálogos (defectos, máquinas, telas, operarios)

| Requisito | Descripción | Prioridad |
|-----------|---|---|
| **F4.1** | CRUD Defectos (código, nombre, descripción, máquina típica) | MUST |
| **F4.2** | CRUD Máquinas (código, nombre, proceso) | SHOULD |
| **F4.3** | CRUD Telas (código, nombre, composición) | SHOULD |
| **F4.4** | Importar maestros desde ACATEX (si integración habilitada) | SHOULD |

#### MÓDULO 5: Sincronización (Sistema)
**Responsabilidad**: Traer/enviar datos a ACATEX si integración está habilitada

| Requisito | Descripción | Prioridad |
|-----------|---|---|
| **F5.1** | Integración optional: ¿Integrar con ACATEX? SÍ / NO en setup | MUST |
| **F5.2** | Si SÍ: traer maestros de ACATEX (telas, máquinas, lotes, operarios) | MUST |
| **F5.3** | Si SÍ: enviar resultado inspección a ACATEX (lote → defecto → máquina) | SHOULD |
| **F5.4** | Si NO: maestros locales en BD, sistema standalone | MUST |

#### MÓDULO 6: Configuración (Admin)
**Responsabilidad**: Settings del sistema

| Requisito | Descripción | Prioridad |
|-----------|---|---|
| **F6.1** | Información empresa (nombre, ubicación) | MUST |
| **F6.2** | Configuración integración ACATEX (URL, credenciales, sync freq) | MUST |
| **F6.3** | Habilitar/deshabilitar auditoría (opcional) | SHOULD |
| **F6.4** | Gestión usuarios y roles (RBAC) | MUST |

---

## 🔒 REQUISITOS NO FUNCIONALES

### Performance
| Requisito | Target | Razón |
|-----------|--------|-------|
| **NFR1** | Latencia respuesta app: <2 seg | Analista en piso impaciente |
| **NFR2** | Dashboard carga: <3 seg | Jefe QA con 100K registros |
| **NFR3** | Sincronización: <5 min después wifi | Operacional: no puede esperar horas |

### Disponibilidad
| Requisito | Target | Razón |
|-----------|--------|-------|
| **NFR4** | Uptime: ≥99% | CEO exige confiabilidad |
| **NFR5** | Offline-first: funciona sin wifi | Piso tiene wifi débil/intermitente |
| **NFR6** | Sincronización confiable: 99%+ éxito | Cero pérdida de datos |

### Seguridad
| Requisito | Target | Razón |
|-----------|--------|-------|
| **NFR7** | Autenticación: usuario + contraseña + MFA (opcional) | Fotos son sensibles |
| **NFR8** | RBAC: Analista ≠ Jefe ≠ Gerente | Control de acceso |
| **NFR9** | Validación input: prevenir SQL injection, XSS | Datos críticos |
| **NFR10** | Almacenamiento fotos: local encriptado (si aplica) | Privacidad datos planta |

### Escalabilidad
| Requisito | Target | Razón |
|-----------|--------|-------|
| **NFR11** | DB: soportar 100K registros sin degradación | 90 días = ~300K registros |
| **NFR12** | Concurrencia: 20 analistas simultáneos | Número de usuarios |
| **NFR13** | Foto: compresión o límite de tamaño | No reventar storage |

### Usabilidad
| Requisito | Target | Razón |
|-----------|--------|-------|
| **NFR14** | Training: 2 horas por analista max | Presión time-to-value |
| **NFR15** | UI intuitiva: 1 botón = 1 acción | Operario sin tech background |
| **NFR16** | Mobile-first: responsive en 4"-6" | Analista con celular en piso |

### Confiabilidad
| Requisito | Target | Razón |
|-----------|--------|-------|
| **NFR17** | Integridad datos: cero pérdida offline→online | Cada defecto es crítico |
| **NFR18** | Validación: rechazar datos incompletos | No permitir registros sin foto |

---

## 🏗️ ARQUITECTURA DE ALTO NIVEL (Confirmada)

```
┌──────────────────────────────────────────────────────────────┐
│                        USUARIOS                              │
├──────────┬──────────────┬────────────────┬──────────────────┤
│ Analista │ Jefe de QA   │ Jefe Procesos  │ Gerente / Admin  │
└────┬─────┴──────┬───────┴────────────┬───┴──────────┬───────┘
     │            │                    │              │
     v            v                    v              v
┌────────────────────────────────────────────────────────────┐
│              FRONTEND (React + TypeScript)                 │
├──────────────┬──────────────┬──────────────┬──────────────┤
│ App Móvil    │ Dashboard    │ Análisis     │ Settings     │
│ (Inspección) │ (Aprobación) │ (Gráficos)   │ (Admin)      │
└──────┬───────┴──────┬───────┴──────────┬──┴──────────┬────┘
       │              │                  │             │
       └──────────────┴──────────────────┴─────────────┘
                      │
                      v
       ┌─────────────────────────────────────┐
       │   BACKEND API (Python FastAPI)      │
       ├──────────────────────────────────────┤
       │ - Inspección                         │
       │ - Aprobación                         │
       │ - Análisis/Reportes                  │
       │ - Maestros (CRUD)                    │
       │ - Sincronización ACATEX (opcional)   │
       │ - Autenticación / RBAC               │
       └──────────────────────────────────────┘
                      │
           ┌──────────┴──────────┐
           v                     v
    ┌─────────────────┐  ┌──────────────────┐
    │  BD Local       │  │  ACATEX (ERP)    │
    │  (PostgreSQL)   │  │  (Opcional)      │
    │  - Inspecciones │  │  - Maestros      │
    │  - Defectos     │  │  - Lotes/HDR     │
    │  - Usuarios     │  │  - Status        │
    └─────────────────┘  └──────────────────┘
```

### Stack Tecnológico Confirmado (ACTUALIZADO)
- **Backend**: Python 3.10+ + FastAPI (async, moderno, scalable)
- **Frontend**: React 18+ (TypeScript, Zustand/Redux, Axios)
- **Mobile**: React responsive (web + PWA optional)
- **Database**: PostgreSQL o SQL Server (on-premise Eliot, flexible)
- **ORM**: SQLAlchemy (Python) o Prisma
- **Auth**: JWT + RBAC
- **Deployment**: TBD (on-premise vs. cloud)
- **Ventaja**: No depende de .NET, más rápido desarrollo, mejor para integración ACATEX opcional

---

## ⚠️ DEPENDENCIAS Y RESTRICCIONES

### Dependencia #1: ACATEX Access (Crítica)
| Aspecto | Detalle |
|---------|---------|
| **Dependencia** | APIs de ACATEX disponibles |
| **Status** | ⏳ PENDIENTE: Verificar con IT Eliot |
| **Contingencia** | Si no hay APIs: maestros locales (sistema standalone funciona) |
| **Impacto** | Si no hay acceso, sistema sigue siendo útil; solo sin sincronización automática |

### Dependencia #2: Datos Iniciales (Crítica)
| Aspecto | Detalle |
|---------|---------|
| **Dependencia** | Maestro de Defectos inicial (25+ defectos textiles) |
| **Status** | ✅ EN HAND: PRD lista defectos (TONODIFFERENTE, MANCHAS, etc.) |
| **Acción** | Semana 0: Entrevista Jefe QA para validar completitud |

### Dependencia #3: Hardware/Wifi (Media)
| Aspecto | Detalle |
|---------|---------|
| **Dependencia** | Celulares para analistas (iOS/Android) |
| **Status** | ✅ EN HAND: Manufacturera probablemente tiene |
| **Acción** | Semana 0: Confirmar modelos, versiones SO |

### Dependencia #4: Training (Media)
| Aspecto | Detalle |
|---------|---------|
| **Dependencia** | Jefe QA disponible para cambio management |
| **Status** | ✅ EN HAND: Es stakeholder crítico |
| **Acción** | Semana 5: Kick-off training con 5 early adopters |

### Restricción #1: Timeline (Crítica)
- **Límite**: 90 días (Semana 1-4 construcción, 5-8 testing, 9-12 go-live)
- **Implicación**: Scope FIJO. Cambios = deben salir de algo existente

### Restricción #2: Budget (Crítica)
- **Presupuesto**: $20K-50K USD (implementación + año 1 licencias)
- **ROI**: Si baja -30%, payback en 4-8 semanas

### Restricción #3: Infraestructura (Media)
- **DB**: SQL Server on-premise (no cloud migration)
- **API**: Si integra ACATEX, debe ser vía APIs existentes (no custom ETL)

---

## ✅ CRITERIOS DE ÉXITO

### North Star Metric
**Reducción de Reprocesos: -30% en 90 días**

| Métrica | Baseline | Meta 90d |
|---------|----------|----------|
| Lotes defectuosos/mes | 267,119 | 187,183 (-30%) |
| Costo ahorrado/mes | $500K-1.3M | Ahorro de $150K-400K |

### KPIs por Fase
| KPI | Fase | Meta |
|-----|------|------|
| Adopción (% analistas activos) | Semana 12 | ≥90% |
| Completitud (foto + tipo + comentario) | Semana 12 | ≥98% |
| Precisión máquina culpable | Semana 12 | ≥85% |
| Uptime | Semana 12 | ≥99% |
| Retención (% uso semanal) | Semana 12 | ≥80% |
| NPS (Net Promoter Score) | Semana 12 | ≥40 |

### Go/No-Go Checkpoints
| Hito | Día | Criterio |
|------|-----|----------|
| MVP funcional | 30 | 10/10 features, <10 bugs críticos |
| Piloto validado | 44 | 5 analistas, ≥85% precisión |
| Listo go-live | 60 | 18/20 entrenados, 0 blockers |
| Go-live | 67 | Sistema en vivo, 0 crashes |
| Impacto visible | 74 | -15%+ reprocesos |
| Objetivo 90d | 90 | -30%, 95% adopción, CEO satisfecho |

---

## 🚨 RIESGOS PRINCIPALES (Top 5)

| Riesgo | Prob | Impacto | Mitigación |
|--------|------|---------|-----------|
| **R1**: Analistas resisten cambio (prefieren Excel) | MEDIA 50% | ALTO | Change management intenso, early adopters, support 24/7 semana 1-2 |
| **R2**: App móvil pierde datos offline | MEDIA 40% | ALTO | Arquitectura offline-first robusta, testing 100+ casos, UI feedback claro |
| **R3**: Integración ACATEX toma más tiempo | MEDIA 45% | ALTO | MVP agnóstico de ERP, integración OPTIONAL, fallback a maestros locales |
| **R4**: Scope creep CEO pide features nuevas | ALTA 70% | ALTO | Acta de entendimiento Semana 0, "puerta de cambios", reunión semanal CEO |
| **R5**: No se alcanza -30% (solo -15%) | MEDIA 40% | ALTO | Atacar causa raíz clara Semana 6, quick wins, re-evaluación estrategia |

---

## 📅 TIMELINE (Confirmado)

| Fase | Semanas | Entregables |
|------|---------|-------------|
| **Inception** | 0 (Hoy) | Este documento, Workflow Plan, Diseño Arquitectura |
| **Construction** | 1-4 | 10 must-have features, MVP funcional |
| **Testing** | 5-8 | Piloto controlado, validación QA, training |
| **Go-Live** | 9-12 | Lanzamiento producción, medición, roadmap v2 |

---

## 📊 MATRIZ DE TRAZABILIDAD

| Feature (F) | Requisito (R) | Persona | Éxito |
|-------------|---|---------|-------|
| F1.1-F1.7 | Inspección completa | Analista | Foto + defecto guardado offline |
| F2.1-F2.6 | Aprobación + notificación | Jefe QA | Gerente recibe notificación <1 min |
| F3.1-F3.8 | Análisis + dashboards | Gerente | Ver -% en tiempo real |
| F4.1-F4.4 | Maestros | Admin | CRUD defectos funcional |
| F5.1-F5.4 | Sincronización opcional | Sistema | Datos sincronizados sin pérdida |
| F6.1-F6.4 | Configuración | Admin | Setup inicial <30 min |

---

## 🎯 PRÓXIMOS PASOS

1. ✅ **Este documento**: Requirements Analysis completado
2. ➡️ **User Stories**: Crear historias de usuario para 6 módulos
3. ➡️ **Workflow Planning**: Planificar fases construction (por módulo)
4. ➡️ **Application Design**: Diseñar componentes, servicios, BD schema
5. ➡️ **Code Generation**: Generar código (backend + frontend)
6. ➡️ **Build & Test**: Testing, validación, go-live

---

**Status**: ✅ READY FOR USER APPROVAL

