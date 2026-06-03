# PRODUCT.md — Sistema de Gestión de Control de Calidad Textil

**Versión**: 1.0  
**Última actualización**: 2026-06-01  
**Estado**: Listo para Desarrollo  
**Referencia**: PRD v1.0 (2026-05-26)

---

## 1. One-Liner

**"Un sistema de gestión de control de calidad que centraliza registros fotográficos de defectos, tiempos de inspección y comentarios del analista, reemplazando Excel y entregando trazabilidad completa en 90 días."**

---

## 2. Misión y Contexto

### Misión
**"De Excel a Control: Sistematizar la invisible labor de los analistas de calidad."**

Hoy, cada defecto detectado en Tintoreria (267K reprocesos en abril 2026) se registra en Excel, con pérdida de contexto fotográfico, tiempos inconsistentes y análisis manuales. Nuestro sistema:

1. ✅ Centraliza registro fotográfico (cada defecto queda documentado con imagen)
2. ✅ Sistematiza tiempos (check-in/check-out automático)
3. ✅ Crea base de datos de defectos (histórico por sección, máquina, analista)
4. ✅ Entrega métricas accesibles (KPIs sin cálculos manuales)

### Contexto: Planta Manufacturas Eliot - Bogotá

| Dato | Valor |
|------|-------|
| **Operarios** | ~1,000 |
| **Analistas QA** | 20 |
| **Volumen Reprocesos** | 267,119 lotes/mes (Abril 2026) |
| **Impacto Financiero** | $500K-1.3M USD/mes perdidos |
| **ERP Existente** | ACATEX (.NET + SQL Server) |
| **Defectos Críticos** | TONODIFFERENTE (29-40%), MANCHAS (13%), MAREO (10%) |
| **Timeline Entrega** | 90 días (Construcción 30d, Testing 30d, Go-live 30d) |

---

## 3. Problema → Solución → Resultado

### 🔴 Problema: Datos Dispersos, Decisiones a Ciegas

**Síntomas**:
- 267K defectos/mes documentados SOLO en Excel + papeleta
- Sin registro fotográfico sistemático (0% de telas fotografiadas)
- Tiempos inconsistentes (algunos anotan hora inicio, otros solo hora fin)
- Jefe de Calidad invierte 2-3 horas/día limpiando datos
- Jefe de Procesos toma decisiones SIN saber cuál máquina/turno/tela falla
- Auditoría imposible (sin trail fotográfico)
- Análisis manual tardío (reportes 2-3 días después)

**Costo**: Decisiones reactivas, no data-driven. Márgenes comprimidos.

---

### 🟢 Solución: Sistema Móvil Fotográfico + Dashboard en Tiempo Real

**Componentes principales**:
1. **App Móvil (Inspección)**: Analista captura foto + selecciona defecto + escribe comentario + tiempo automático
2. **Dashboard (Aprobación)**: Jefe QA revisa, aprueba/rechaza, notifica
3. **Analytics (Decisiones)**: Jefe Procesos/Gerente ve patrones por máquina, defecto, tela en tiempo real
4. **Integración ACATEX (Opcional)**: Sincroniza maestros (telas, máquinas, lotes) si ERP existe

**Diferenciadores**:
- ✅ **Especialización Textil**: 25+ defectos específicos (TONODIFFERENTE, MANCHAS, etc.), no genérico
- ✅ **Implementación Rápida**: 2-4 semanas vs. 3-6 meses de ERP
- ✅ **Offline-First**: Funciona sin wifi; sincroniza automáticamente
- ✅ **Agnóstico de ERP**: Funciona standalone O integrado con ACATEX
- ✅ **Foto + Trazabilidad**: Cada defecto queda documentado con imagen, quién lo registró, máquina, timestamp

---

### 📈 Resultado Esperado (90 Días)

| Métrica | Baseline | Meta 90d | Impacto |
|---------|----------|----------|---------|
| **Reprocesos/mes** | 267,119 | 187,183 (-30%) | $150K-400K USD/mes |
| **% Registro Fotográfico** | 0% | 95% | Trazabilidad completa |
| **% Analistas Activos** | 0% | 90% (18/20) | Adopción alta |
| **Tiempo Respuesta Jefe** | 120 min | <10 min | 10x más rápido |
| **Precisión Máquina Culpable** | ~70% | 85%+ | Data-driven decisions |

---

## 4. Job to be Done (JTBD)

**Cuando** un Analista de Calidad encuentra un defecto en tela durante inspección en Tintoreria,  
**Quiero** capturar una foto desde mi celular, escribir un comentario sobre el problema y registrar el tiempo de inspección en un sistema centralizado,  
**Para** que la planta tenga un registro organizado, trazable y accesible de todos los defectos (en lugar de dispersarlos en Excel), y los Jefes de Calidad puedan analizar patrones de reprocesos por máquina, sección y tipo de defecto.

---

## 5. Buyer Personas

### Persona 1: Jefe de Calidad (Decision Maker)
- **Edad**: 35-55 años, 10+ años en textil
- **Presión**: CEO exige bajar -30% reprocesos en 90 días
- **Pain**: Pasa 2+ horas/día en Excel; sin visibilidad en tiempo real
- **Goal**: Reducir reprocesos + tener dashboard ejecutivo por tela
- **Poder de Decisión**: ALTO (aprueba inversión hasta $50K USD)

### Persona 2: Analista de Calidad (Power User)
- **Edad**: 22-40 años, 2-8 años de experiencia
- **Pain**: Proceso manual lento; NO hay documentación visual del defecto
- **Goal**: Trabajar más rápido en piso; capturar foto + comentario sin Excel
- **Poder de Decisión**: BAJO, pero su buy-in es crítico

### Persona 3: Jefe de Procesos (Data-Driven)
- **Edad**: 40-60 años, experiencia en operaciones
- **Pain**: Toma decisiones SIN data (¿revisar AGOTAMIENTO 80 o RAMAS 19?)
- **Goal**: Análisis en línea por tela, máquina, turno, operario
- **Poder de Decisión**: MEDIO-ALTO (puede bloquear si sistema detiene línea)

### Persona 4: Gerente de Planta (Executive Sponsor)
- **Edad**: 45-65 años, MBA/ingeniería
- **Presión**: CEO exige bajar reprocesos; márgenes comprimidos
- **Goal**: Dashboard ejecutivo que muestre reprocesos POR TELA
- **Poder de Decisión**: MÁXIMO (aprueba presupuesto $50K-150K USD)

---

## 6. Top 5 Casos de Uso

### 1️⃣ Analista inspecciona lote, documenta defecto, lo vincula a máquina
**Valor**: Defecto trazado (quién, dónde, cuándo, por qué) con foto.

- Analista abre app móvil → escanea lote HDR #12847
- Sistema carga automáticamente: tela (NOVAKREPEL), máquinas, estación actual
- Inspecciona tela → encuentra variación de tono → presiona "Capturar Defecto"
- Captura foto (offline) → selecciona "TONODIFFERENTE" → escribe comentario
- Sistema sugiere máquina culpable (AGOTAMIENTO 80) → analista confirma
- Presiona "Guardar" → check-out automático (3'22")

**Tiempo**: <5 minutos vs. 10-15 min en Excel.

---

### 2️⃣ Jefe de Calidad analiza patrones en tiempo real
**Valor**: Causa raíz identificada en 10 minutos vs. 2 horas en Excel.

- Jefe abre dashboard QA → selecciona filtros (24h, TONODIFFERENTE, TODAS máquinas)
- Sistema genera análisis: "47 lotes con TONODIFFERENTE en 24h"
  - AGOTAMIENTO 80: 28 lotes (59%)
  - AGOTAMIENTO 19: 15 lotes (32%)
  - Otros: 4 lotes (9%)
- Filtra fotos de "AGOTAMIENTO 80 + TONODIFFERENTE" → galería de 10+ fotos
- Ve patrón claro: todas muestran variación de tono
- Prepara reporte PDF para Gerente en 10 minutos

---

### 3️⃣ Jefe de Procesos toma decisión data-driven
**Valor**: Decisión data-backed, no intuición. ROI medible.

- Jefe ve ranking por máquina (últimas 24h): AGOTAMIENTO 80 (27%), AGOTAMIENTO 19 (25%), RAMAS 19 (12%)
- Filtra fotos de "AGOTAMIENTO 80 + TONODIFFERENTE" → visualiza 100+ fotos
- Analiza patrón → "¿Problema es color, no tensión?"
- Toma decisión: "Revisar AGOTAMIENTO 80 mañana"
- 2 semanas después, mide resultado: AGOTAMIENTO 80 defectos bajaron 40%

---

### 4️⃣ Gerente reporta al CEO
**Valor**: CEO ve datos, no promesas. Confianza en proyecto.

- Gerente abre dashboard ejecutivo
- Muestra: Total reprocesos 267K (abril) → 225K (semana 1 mayo) = **-15.7%**
- Tendencia: gráfico de línea mostrando reducción
- Top telas: NOVAKREPEL 27.13% → 22.5% (-4.6 puntos)
- Reporta al CEO: "Bajamos 15.7% en 1 semana. Proyección: -30% en 90 días."

---

### 5️⃣ Auditor verifica cumplimiento de lotes
**Valor**: Trazabilidad completa. Cumplimiento regulatorio.

- Auditor accede a módulo de auditoría
- Sistema lista: "Mayo 2026: 127,000 lotes inspeccionados"
- Selecciona muestra: 100 lotes aleatorios
- Verifica para cada lote: foto ✓, comentario ✓, timestamp ✓, máquina ✓
- Sistema valida integridad: 100/100 completos
- Auditor firma: "Cumplimiento verificado. Trail completo."

---

## 7. MVP Scope (MoSCoW)

### 🔴 MUST HAVE (v1.0 — 10 features, 2-3 semanas)

| # | Feature | Timeline |
|---|---------|----------|
| 1 | Captura de foto desde celular (offline) | Sem 1 |
| 2 | Maestro de 25+ defectos textiles | Sem 1 |
| 3 | Comentario descriptivo obligatorio | Sem 1 |
| 4 | Check-in/check-out automático | Sem 1 |
| 5 | Integración ACATEX (maestros básicos) | Sem 2 |
| 6 | Máquina culpable estimada + confirmable | Sem 2 |
| 7 | Offline-first + sincronización automática | Sem 2 |
| 8 | Dashboard Jefe QA (aprobación) | Sem 2 |
| 9 | Notificaciones a Gerente | Sem 2 |
| 10 | Trail básico (auditoría simple) | Sem 2 |

---

### 🟡 SHOULD HAVE (v1.1 — 7 features, +1-2 semanas)

| # | Feature | Timeline |
|---|---------|----------|
| 1 | Análisis por máquina (gráficos) | Sem 3 |
| 2 | Análisis por tipo defecto | Sem 3 |
| 3 | Dashboard Gerente (3 KPIs) | Sem 3 |
| 4 | Exportar reportes (PDF/Excel) | Sem 3 |
| 5 | Auditoría completa (trail inmutable) | Sem 4 |
| 6 | Dashboard Jefe Procesos | Sem 4 |
| 7 | Integración MES de piso (si aplica) | Sem 4 |

---

### 🟢 COULD HAVE (v2.0 — Future, 4-8 semanas)

- IA sugerir máquina culpable inteligentemente
- Reportes predictivos (alertas máquinas)
- App nativa iOS/Android
- Multi-idioma
- Integración MES avanzada
- Alertas en tiempo real (push notifications)

---

### ⚪ WON'T HAVE (Out of Scope)

- Extensión a otras plantas (MVP: Bogotá)
- Detección automática de defectos (IA visión)
- Gestión de proveedores
- Integración Salesforce/CRM
- APIs abiertas para clientes

---

## 8. Principios de Diseño No Negociables

### ✅ 1. Foto + Tipo de Defecto + Comentario = Registro Válido
- Foto obligatoria
- Tipo defecto seleccionado (no texto libre)
- Comentario ≥10 caracteres
- **PROHIBIDO**: guardar sin los 3

### ✅ 2. Trazabilidad Completa de Lote
- Cada lote: HDR + máquinas del flujo + defecto + acción
- Trail visible en sistema
- **PROHIBIDO**: defecto huérfano sin máquina

### ✅ 3. Check-in / Check-out Automático
- Timestamp automático (inicio/fin)
- Sistema calcula tiempo inspección
- **PROHIBIDO**: ingreso manual de hora

### ✅ 4. ACATEX = Fuente Única de Verdad
- Telas, máquinas, lotes, operarios de ACATEX
- Sistema QA NO crea/edita maestros (excepto defectos)
- **PROHIBIDO**: catálogo paralelo en Excel

### ✅ 5. Sistema Agnóstico de ERP
- Funciona 100% sin ERP (maestros locales)
- Integración ACATEX es OPCIONAL
- **PROHIBIDO**: requerir ERP para funcionar

### ✅ 6. Especialización Textil
- Defectos: TONODIFFERENTE, MANCHAS, PILLING, etc. (no genérico)
- Máquinas: AGOTAMIENTO 80, RAMAS, etc. (no "Machine A")
- **PROHIBIDO**: términos genéricos

### ✅ 7. Máquina Culpable Estimada (Inteligencia, No Automatización)
- Sistema SUGIERE máquina culpable
- Analista DECIDE (puede cambiar)
- **PROHIBIDO**: máquina asignada sin lógica

### ✅ 8. Offline-First, Sincronización Garantizada
- Funciona sin wifi
- Captura foto + comenta + guarda offline
- Sincroniza automáticamente cuando hay conectividad
- **PROHIBIDO**: pérdida de datos, sincronización manual

---

## 9. Métricas de Éxito (90 Días)

### 🎯 North Star Metric
**Reducción de reprocesos de planta**: 267K → 187K (-30%)  
**Impacto financiero**: $150K-400K USD/mes ahorrados

### 📊 KPIs Activación
| KPI | Baseline | Meta 90d |
|-----|----------|----------|
| % lotes con registro fotográfico | 0% | 95% |
| % analistas activos | 0% | 90% (18/20) |
| % lotes procesados en sistema | 0% | 85% |

### 📊 KPIs Calidad
| KPI | Baseline | Meta 90d |
|-----|----------|----------|
| % precisión máquina culpable | ~70% | 85%+ |
| % fotos claras y útiles | N/A | 90%+ |
| % completitud registros | 0% | 98%+ |
| Tiempo promedio inspección | Manual | 3-5 minutos |

### 📊 KPIs Técnico
| KPI | Baseline | Meta 90d |
|-----|----------|----------|
| Uptime | N/A | ≥99% |
| Tasa sincronización exitosa | N/A | 99%+ |
| Latencia de respuesta | N/A | <2 segundos |
| Tasa pérdida de datos | N/A | 0% |

### ✅ Criterios de Éxito
✅ North Star: -30%+ en reprocesos  
✅ Adopción: ≥90% analistas  
✅ Calidad: ≥85% precisión máquina  
✅ Uptime: ≥99%  
✅ Retención: ≥80% semana 12

### ❌ Criterios de Fracaso
❌ North Star: <-15%  
❌ Adopción: <70%  
❌ Calidad: <70%  
❌ Uptime: <95%  
❌ Retención: <60%

---

## 10. Plan de Entrega 30/60/90 Días

### 📅 Fase 1: Días 1-30 (CONSTRUCCIÓN MVP)

#### Semana 1: Infraestructura + Módulo Maestros
- Setup dev, BD PostgreSQL, Git, CI/CD
- Entrevista analistas (validar 25+ defectos)
- Backend maestros (CRUD)
- Frontend maestros
- **Deliverable**: Sistema puede crear/editar defectos. BD funcional.

#### Semana 2: Módulo Inspección + App Móvil
- Framework app móvil (React Native / Flutter / Web PWA)
- Backend inspección (foto, defecto, comentario, timestamp)
- Flujo inspección completo
- Offline-first (caché local)
- **Deliverable**: Analista captura foto + defecto desde celular. Sin wifi.

#### Semana 3: Módulo Aprobación + Sincronización Básica
- Backend aprobación (approve/reject logic)
- Frontend aprobación (Jefe QA)
- Sincronización básica (app → servidor)
- Testing offline-sync robustez
- **Deliverable**: Jefe QA aprueba/rechaza. Fotos sincronizan sin pérdida.

#### Semana 4: Dashboard Análisis + Integración ACATEX (Opcional)
- Backend análisis (queries, agrupaciones)
- Frontend dashboards (gráficos, filtros)
- Integración ACATEX APIs (si aplica)
- Testing MVP standalone
- **Deliverable**: Dashboard muestra patrones. MVP 100% funcional.

---

### 📅 Fase 2: Días 31-60 (TESTING + ADOPCIÓN)

#### Semana 5: QA Testing + Change Management
- Unit, integration, edge cases testing
- Load testing (20 analistas simultáneos)
- Change management kickoff
- Training early adopters (5 analistas)
- **Deliverable**: MVP testeado. 5 analistas piloto listos.

#### Semana 6: Piloto Controlado + Auditoría
- Piloto: 5 analistas, 50+ lotes/día
- Should-have features (análisis, dashboard)
- Auditoría manual QA (100 registros)
- UX improvements basado en feedback
- **Deliverable**: Piloto funcional. Calidad validada (≥85% precisión).

#### Semana 7: Expansión Piloto + Legal/Privacy
- Piloto: 5 → 10 analistas
- Auditoría legal/privacidad
- Dashboard Gerente completo
- Training masivo (10 analistas más)
- **Deliverable**: 10/20 analistas. Legal aprobado.

#### Semana 8: Preparación Go-Live
- Integración ACATEX final
- Release notes, runbook, disaster recovery plan
- Testing regresión completo
- Reunión GO/NO-GO
- **Deliverable**: Sistema 100% listo. Go-live decision.

---

### 📅 Fase 3: Días 61-90 (GO-LIVE + MEDICIÓN)

#### Semana 9: GO-LIVE 🚀
- **DÍA 61**: Lanzamiento a producción (20 analistas)
- Go-live support 24/7 (Jefe QA + Dev)
- Métricas baseline (reprocesos, adopción)
- **Deliverable**: Sistema en vivo. Go-live exitoso.

#### Semana 10: Impacto Inicial
- Análisis Semana 1-2: -% reprocesos
- Identificar máquina #1 problemática
- Quick wins (acción en máquina target)
- Training refuerzo
- **Deliverable**: Impacto visible. Adopción >80%.

#### Semana 11: Iteración + Should-Have Finales
- Iteración basada en feedback analistas
- Análisis Semana 3-4: -% reprocesos
- Should-have features completadas
- Training especializado (advanced users)
- **Deliverable**: Sistema optimizado. -15%+ impacto.

#### Semana 12: MEDICIÓN FINAL + ROADMAP v2
- Medición 90 días: -% reprocesos (meta -30%)
- Adopción final: 95%+ analistas
- Auditoría final
- Reunión GO/NO-GO post-90d
- **Deliverable**: Éxito medido. Roadmap v2 definido.

---

## 11. Riesgos Principales y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|---|---|---|
| Analistas resisten cambio | MEDIA | ALTO | Change management intenso, early adopters, training práctico |
| Pérdida de datos en offline | MEDIA | ALTO | Arquitectura offline-first robusta, testing 100+ casos |
| Integración ACATEX toma más tiempo | MEDIA | ALTO | MVP agnóstico de ERP, integración OPCIONAL |
| Scope creep | ALTA | ALTO | Acta de entendimiento, reunión Semana 0 con CEO |
| No se alcanza meta -30% | MEDIA | ALTO | Bajar expectativas realistas, atacar causa raíz |

---

## 12. Especificación Técnica

### Tech Stack (Recomendado)

| Capa | Tecnología | Razón |
|------|-----------|-------|
| **Frontend (Web)** | React 18+ + TypeScript | SPA, mobile-friendly, component-driven |
| **Frontend (Mobile)** | React Native o PWA | iOS/Android, offline-capable |
| **Backend** | Node.js (Express) / Python (FastAPI) | Fast, JSON APIs, fácil de escalar |
| **Base de Datos** | PostgreSQL | Relacional robusto, JSONB para flexibilidad |
| **Storage (Fotos)** | Local + Cloud (S3 opcional) | Offline-first, sync a cloud |
| **Autenticación** | JWT / OAuth 2.0 | Stateless, seguro, escalable |
| **Testing** | Jest + React Testing Library + Cypress | Unit, component, e2e |
| **DevOps** | Docker + CI/CD (GitHub Actions/GitLab CI) | Reproducible, automated |

### Base de Datos (PostgreSQL)

#### Tablas Principales

```sql
-- Maestros (configurables por admin)
CREATE TABLE defectos (
  id SERIAL PRIMARY KEY,
  codigo VARCHAR(50) UNIQUE NOT NULL,
  nombre VARCHAR(255) NOT NULL,
  descripcion TEXT,
  proceso_tipico VARCHAR(100),
  maquina_tipica_id INT,
  activo BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE maquinas (
  id SERIAL PRIMARY KEY,
  codigo VARCHAR(50) UNIQUE NOT NULL,
  nombre VARCHAR(255) NOT NULL,
  proceso VARCHAR(100),
  capacidad VARCHAR(100),
  activo BOOLEAN DEFAULT true
);

CREATE TABLE operarios (
  id SERIAL PRIMARY KEY,
  cedula VARCHAR(20) UNIQUE NOT NULL,
  nombre VARCHAR(255) NOT NULL,
  rol VARCHAR(100),
  turno VARCHAR(50),
  activo BOOLEAN DEFAULT true
);

-- Operaciones (generadas por inspección)
CREATE TABLE inspecciones (
  id SERIAL PRIMARY KEY,
  lote_numero VARCHAR(50) NOT NULL,
  tela_id INT,
  maquina_culpable_id INT,
  analista_id INT,
  defecto_id INT NOT NULL,
  foto_url TEXT NOT NULL,
  comentario TEXT NOT NULL,
  check_in TIMESTAMP NOT NULL,
  check_out TIMESTAMP NOT NULL,
  tiempo_inspeccion_segundos INT,
  status VARCHAR(50) DEFAULT 'PENDIENTE', -- PENDIENTE, APROBADO, RECHAZADO
  aprobado_por INT,
  aprobado_en TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Auditoría (si habilitada)
CREATE TABLE audit_log (
  id SERIAL PRIMARY KEY,
  tabla VARCHAR(100),
  accion VARCHAR(50), -- CREATE, UPDATE, DELETE, APPROVE
  registro_id INT,
  usuario_id INT,
  datos_antes JSONB,
  datos_despues JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 13. Roadmap Futuro (Después de 90d)

### v2.0 (Meses 4-6)
- IA sugerir máquina culpable basado en histórico
- Reportes predictivos ("AGOTAMIENTO 80 va a fallar en 4h")
- App nativa iOS/Android (descargable)
- Multi-idioma (español, inglés, portugués)
- Alertas en tiempo real (push notifications)

### v3.0 (Meses 7-12)
- Extensión a otras plantas de Manufacturas Eliot
- Análisis predictivos avanzados
- Integración IoT sensores máquinas
- Mobile offline con sincronización inteligente
- API abierta para clientes

---

## 14. Contacto y Escalación

| Categoría | Contacto |
|-----------|----------|
| **Product Owner** | Jefe de Calidad / Gerente |
| **Technical Lead** | Dev Lead |
| **Change Management** | Jefe QA |
| **ACATEX Integration** | IT Manager (ACATEX) |
| **Design/UX** | UX Designer (basado en DESIGN.md) |

---

## 15. Aprobaciones

| Rol | Nombre | Firma | Fecha |
|-----|--------|-------|-------|
| Gerente de Planta | _____________ | __________ | __________ |
| Jefe de Calidad | _____________ | __________ | __________ |
| Dev Lead | _____________ | __________ | __________ |
| CEO | _____________ | __________ | __________ |

---

**Documento completo**  
Versión 1.0 | Listo para Desarrollo | 2026-06-01
