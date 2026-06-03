# User Stories Detalladas — Control de Calidad Textil
**Date**: 2026-05-27 | **Total Stories**: 30 | **MVP 30d Scope**: 18 stories | **Status**: GENERATION PHASE

---

## MÓDULO 1: INSPECCIÓN (Analista de Calidad) — 8 Stories

### INS-001: Buscar/escanear lote HDR
**Size**: Small (1-2 días)

**As a** Analista de Calidad  
**I want to** buscar un lote por código HDR (ej: "HDR-12847") o escanear código de barras  
**So that** puedo cargar rápidamente la tela, máquinas y contexto del lote sin escriptorios

**Acceptance Criteria**:
- [ ] Pantalla tiene campo búsqueda + botón escanear QR
- [ ] Buscar por código exacto retorna lote (ej: HDR-12847 → NOVAKREPEL, 500m)
- [ ] Si lote no existe → mensaje claro "Lote no encontrado"
- [ ] Escaneo QR funciona offline (ej: búsqueda en caché local)
- [ ] Carga <2 segundos

**Gherkin Scenarios**:
```gherkin
Feature: Buscar lote por HDR
  Scenario: Buscar lote existente por código
    Given analista está en página Inspección
    When ingresa código "HDR-12847"
    And presiona botón buscar
    Then sistema carga lote: NOVAKREPEL, 500m
    And muestra máquinas típicas (AGOTAMIENTO 80, etc.)
    
  Scenario: Lote no existe
    Given analista está en página Inspección
    When ingresa código "HDR-FAKE"
    And presiona buscar
    Then muestra mensaje "Lote no encontrado"
    And campo búsqueda permanece activo
```

---

### INS-002: Capturar foto del defecto
**Size**: Medium (2-3 días)

**As a** Analista de Calidad  
**I want to** capturar una foto clara del defecto directamente desde mi celular  
**So that** queda documentado visualmente y el Jefe QA puede ver exactamente qué se detectó

**Acceptance Criteria**:
- [ ] Botón "Capturar foto" abre cámara nativa del celular
- [ ] Foto se guarda localmente (IndexedDB)
- [ ] Compresión JPEG automática (max 500KB para no llenar storage)
- [ ] Puedo re-capturar si necesito cambiar la foto
- [ ] Sin foto → botón "Guardar" deshabilitado
- [ ] Foto se incluye en sincronización offline→online

---

### INS-003: Seleccionar tipo defecto
**Size**: Small (1 día)

**As a** Analista de Calidad  
**I want to** seleccionar el tipo de defecto de un dropdown con 25+ opciones textiles  
**So that** sistema sabe exactamente qué defecto encontré (TONODIFFERENTE, MANCHAS, etc.)

**Acceptance Criteria**:
- [ ] Dropdown muestra 25+ defectos (TONODIFFERENTE, MANCHAS, PILLING, MAREO, ENCOGIMIENTO, DESFILAMENTO, etc.)
- [ ] Defecto es OBLIGATORIO (no puedo guardar sin seleccionar)
- [ ] Búsqueda dentro dropdown (si tipeo "TONO" → filtra a TONODIFFERENTE)
- [ ] Defecto NO catalogado → opción "Reportar defecto nuevo" (abre form)
- [ ] Seleccionar defecto → sistema pre-llena "máquina típica" (ej: TONODIFFERENTE → AGOTAMIENTO)

---

### INS-004: Escribir comentario obligatorio
**Size**: Small (1 día)

**As a** Analista de Calidad  
**I want to** escribir un comentario descriptivo del defecto (≥10 caracteres)  
**So that** documento dónde exactamente está el defecto y qué lo causó probablemente

**Acceptance Criteria**:
- [ ] Campo comentario es OBLIGATORIO
- [ ] Mínimo 10 caracteres (validación cliente + servidor)
- [ ] Si <10 chars → error "Comentario muy corto"
- [ ] Campo soporta acentos, emojis, saltos de línea
- [ ] Max 500 caracteres (o límite razonable)
- [ ] Sin comentario → botón "Guardar" deshabilitado

---

### INS-005: Confirmar máquina culpable (editable)
**Size**: Small (1-2 días)

**As a** Analista de Calidad  
**I want to** confirmar o cambiar la máquina culpable sugerida por el sistema  
**So that** el registro es exacto si la sugerencia es incorrecta

**Acceptance Criteria**:
- [ ] Sistema sugiere máquina basada en defecto (ej: TONODIFFERENTE → AGOTAMIENTO 80)
- [ ] Campo está pre-rellenado pero EDITABLE
- [ ] Puedo hacer click y seleccionar máquina diferente del dropdown
- [ ] Si cambio máquina → aparece campo comentario "¿Por qué diferente?"
- [ ] Máquina culpable es OBLIGATORIA
- [ ] Sin máquina → botón "Guardar" deshabilitado

---

### INS-006: Check-in/check-out automático
**Size**: Medium (2 días)

**As a** Analista de Calidad  
**I want to** que sistema registre automáticamente la hora de inicio (check-in) y fin (check-out) de mi inspección  
**So that** pueda medir cuánto tiempo tomo revisando cada lote (KPI de velocidad)

**Acceptance Criteria**:
- [ ] Check-in: automático cuando abro lote (timestamp servidor)
- [ ] Check-out: automático cuando presiono "Guardar" (timestamp servidor)
- [ ] Pantalla muestra contador: "Tiempo transcurrido: 3'22"" en tiempo real
- [ ] NO puedo editar timestamps manualmente
- [ ] Timestamps se sincronizan con servidor (o caché offline)
- [ ] Sistema calcula "Tiempo inspección" = check_out - check_in

---

### INS-007: Guardar offline + sincronizar cuando hay wifi
**Size**: Large (4-5 días)

**As a** Analista de Calidad  
**I want to** guardar mi inspección aunque no tenga wifi, y sincronizar automáticamente cuando vuelva la conexión  
**So that** no pierdo datos ni tengo que esperar a tener señal para registrar defectos

**Acceptance Criteria**:
- [ ] Indicador "📡 ONLINE / OFFLINE" visible en pantalla
- [ ] Presionar "Guardar" sin wifi → guardado en IndexedDB localmente
- [ ] Foto guardada en IndexedDB (blob)
- [ ] UI muestra: "✓ Guardado localmente. Sincronizará cuando haya wifi"
- [ ] Cuando wifi vuelve → sincronización automática (background)
- [ ] Cero pérdida de datos (foto + comentario + defecto + timestamps)
- [ ] Service Worker maneja retry automático si falla sincronización
- [ ] Max 100 registros offline simultáneos

---

### INS-008: Ver historial de mis inspecciones
**Size**: Small (2 días)

**As a** Analista de Calidad  
**I want to** ver mis últimas 20 inspecciones con estado (pendiente aprobación, aprobado, rechazado)  
**So that** puedo verificar que mis registros llegaron bien y qué aprobó el Jefe QA

**Acceptance Criteria**:
- [ ] Página "Mis Inspecciones" muestra tabla con últimas 20 registros
- [ ] Columnas: Lote, Defecto, Fecha, Status, Tiempo inspeccionó
- [ ] Filtro: Hoy, Últimos 7 días, Último mes
- [ ] Click en registro → muestra foto + detalles completos
- [ ] Status color-coded: gris=pendiente, verde=aprobado, rojo=rechazado

---

## MÓDULO 2: APROBACIÓN (Jefe de Calidad) — 5 Stories

### APR-001: Ver lotes pendientes aprobación
**Size**: Small (1-2 días)

**As a** Jefe de Calidad  
**I want to** ver una tabla clara de todos los lotes pendientes mi aprobación  
**So that** no pierdo ningún registro y puedo priorizar cuál revisar primero

**Acceptance Criteria**:
- [ ] Página "Aprobaciones Pendientes" muestra tabla por defecto
- [ ] Tabla: Lote, Analista, Defecto, Fecha, Máquina, Estado
- [ ] Orden: Más reciente primero
- [ ] Total en header: "42 pendientes"
- [ ] Filtro rápido: Por defecto, Por analista, Por máquina
- [ ] Click en lote → abre modal detalle

---

### APR-002: Ver foto grande + detalles del lote
**Size**: Medium (2 días)

**As a** Jefe de Calidad  
**I want to** ver la foto del defecto en grande + comentario + máquina + tiempo inspección  
**So that** puedo validar que la inspección es correcta antes de aprobar

**Acceptance Criteria**:
- [ ] Modal muestra: foto en grande (80% pantalla)
- [ ] Debajo foto: Lote, Tela, Analista, Defecto, Máquina, Comentario, Check-in/out
- [ ] Foto zoomable (pinch-to-zoom en mobile)
- [ ] Puedo ver foto anterior/siguiente sin cerrar modal (flechas)
- [ ] Timestamp visible: "Inspeccionado hace 5 minutos"
- [ ] Calidad foto: "Alta" / "Media" / "Baja" (automático)

---

### APR-003: Aprobar reproceso
**Size**: Small (1 día)

**As a** Jefe de Calidad  
**I want to** presionar botón "Aprobar" para confirmar que el defecto es válido y necesita reproceso  
**So that** registro queda aprobado y estadísticas actualizadas

**Acceptance Criteria**:
- [ ] Botón "Aprobar" verde visible en modal
- [ ] Presionar → sistema pide confirmación: "¿Confirmar aprobación?"
- [ ] Aprobación registra: quién (yo), cuándo, status=APPROVED
- [ ] Inspección desaparece de "pendientes"
- [ ] Estadísticas se actualizan (# aprobadas sube)
- [ ] Confirmación visual: "✓ Lote aprobado"

---

### APR-004: Rechazar lote
**Size**: Small (1 día)

**As a** Jefe de Calidad  
**I want to** presionar botón "Rechazar" si la foto/inspección no es clara o el defecto no aplica  
**So that** analista puede re-inspeccionar o lote se marca como falsa alarma

**Acceptance Criteria**:
- [ ] Botón "Rechazar" rojo visible en modal
- [ ] Presionar → abre campo "Motivo del rechazo" (obligatorio ≥10 chars)
- [ ] Motivos sugeridos: "Foto borrosa", "Falsa alarma", "Defecto no confirmado", etc.
- [ ] Rechazo registra: quién, cuándo, status=REJECTED, motivo
- [ ] Inspección desaparece de pendientes
- [ ] Analista recibe notificación (si v1.1 lo implementa)

---

### APR-005: Notificar Gerente automáticamente
**Size**: Medium (2 días)

**As a** Jefe de Calidad  
**I want to** que cuando apruebo un lote, el Gerente reciba notificación automáticamente  
**So that** Gerente ve cambios en tiempo real (sin polling cada 5 min)

**Acceptance Criteria**:
- [ ] Cuando presiono "Aprobar" → se envía notificación a Gerente
- [ ] Notificación: "Nuevo lote aprobado: HDR-12847 (TONODIFFERENTE)"
- [ ] Gerente recibe en: Dashboard UI + email (opcional v1.1)
- [ ] Latencia: <30 segundos
- [ ] Gerente puede hacer click en notificación → va a detalles lote

---

## MÓDULO 3: ANÁLISIS (Jefe QA / Gerente) — 6 Stories ⚠️ FUERA MVP 30d

### ANL-001: Dashboard total reprocesos hoy/semana/mes
**Size**: Medium (2 días) | **Status**: ⏳ v1.1 (Semana 5-8)

**As a** Gerente de Planta  
**I want to** ver en dashboard el total de lotes defectuosos hoy, esta semana, este mes  
**So that** monitoreo el volumen de reprocesos en tiempo real

---

### ANL-002 a ANL-006: Gráficos y Filtros
**Status**: ⏳ v1.1 (Semana 5-8)

---

## MÓDULO 4: MAESTROS (Admin) — 4 Stories

### MAE-001: CRUD Defectos (crear, editar, inactivar)
**Size**: Small (2 días)

**As an** Admin  
**I want to** crear, editar e inactivar defectos en la BD  
**So that** tengo catálogo actualizado de los 25+ defectos textiles

**Acceptance Criteria**:
- [ ] Página "Maestro Defectos" muestra tabla (id, nombre, descripción)
- [ ] Botón "Crear Defecto" → abre form (id, nombre, descripción, máquina típica)
- [ ] Validación: id único, nombre único
- [ ] Botón "Editar" → edita campos (excepto id)
- [ ] Botón "Inactivar" → marca como inactivo (no borra)
- [ ] Inactivos se ocultan en dropdown Inspección (pero se ven en histórico)
- [ ] Confirmación antes de cada acción

---

### MAE-002: CRUD Máquinas
**Size**: Small (1 día)

**As an** Admin  
**I want to** mantener catálogo de máquinas (AGOTAMIENTO 80, RAMAS 19, etc.)  
**So that** están disponibles para seleccionar en inspecciones

**Acceptance Criteria**:
- [ ] CRUD similar a defectos
- [ ] Campos: id, nombre, proceso (TINTORERIA, RAMAS, etc.)
- [ ] Mínimo 15 máquinas cargar en setup inicial

---

### MAE-003: CRUD Telas
**Size**: Small (1 día)

**As an** Admin  
**I want to** mantener catálogo de telas procesadas (NOVAKREPEL, AMORELA, etc.)  
**So that** analistas seleccionan tela correcta en lotes

**Acceptance Criteria**:
- [ ] CRUD similar
- [ ] Campos: id, nombre, composición, ancho (cm), peso (gsm)
- [ ] Mínimo 20 telas cargar en setup

---

### MAE-004: Cargar maestros iniciales
**Size**: Medium (2 días)

**As an** Admin  
**I want to** cargar datos iniciales (25 defectos, 15 máquinas, 20 telas) desde CSV o manual  
**So that** el sistema está listo sin rellenar manualmente 60 registros

**Acceptance Criteria**:
- [ ] Botón "Importar CSV" en cada maestro
- [ ] CSV: columnas deben coincidir (id, nombre, descripción, etc.)
- [ ] Validación de duplicados antes de importar
- [ ] Progress bar durante carga
- [ ] Resumen: "✓ Cargados 25 defectos, 0 errores"
- [ ] Opción manual si CSV no es posible (form masivo)

---

## MÓDULO 5: SINCRONIZACIÓN (Sistema) — 3 Stories ⚠️ FUERA MVP 30d

### SIN-001: Integración opcional ACATEX (SÍ/NO)
**Size**: Small (1 día) | **Status**: ⏳ v1.1 (Semana 5-8)

**As an** Admin  
**I want to** decidir en Setup si integro con ACATEX o uso maestros locales  
**So that** sistema es flexible (on-premise Eliot o standalone)

---

### SIN-002 a SIN-003: Traer maestros + Enviar resultados
**Status**: ⏳ v1.1 (Semana 5-8) — Depende de APIs ACATEX disponibles

---

## MÓDULO 6: CONFIGURACIÓN (Admin) — 4 Stories

### CON-001: Setup inicial (empresa, integración)
**Size**: Medium (2 días)

**As an** Admin  
**I want to** completar setup inicial en primer login: empresa, ciudad, integración ACATEX (sí/no)  
**So that** sistema está configurado antes de que analistas empiecen a usar

**Acceptance Criteria**:
- [ ] Wizard setup: Paso 1 (Empresa), Paso 2 (Integración), Paso 3 (Resumen)
- [ ] Paso 1: Nombre empresa, ubicación, email soporte
- [ ] Paso 2: ¿Integrar ACATEX? → Si sí, solicitar URL + credenciales
- [ ] Validar credenciales ACATEX (si aplica)
- [ ] Paso 3: Resumen + botón "Confirmar Setup"
- [ ] Setup completado → redirige a cargar maestros
- [ ] Max 10 minutos para completar todo

---

### CON-002: Gestión usuarios y roles (CRUD + RBAC)
**Size**: Medium (2 días)

**As an** Admin  
**I want to** crear usuarios (email, rol) y asignar permisos (ANALISTA, JEFE_QA, GERENTE, ADMIN)  
**So that** cada persona accede solo a lo que necesita

**Acceptance Criteria**:
- [ ] Página "Usuarios" muestra tabla (email, nombre, rol, estado, último login)
- [ ] Botón "Crear Usuario" → form (email, nombre, rol, password temporal)
- [ ] Roles: ANALISTA (crear inspecciones), JEFE_QA (aprobar), GERENTE (ver dashboards), ADMIN (todo)
- [ ] Enviar email con contraseña temporal al nuevo usuario
- [ ] Botón "Editar" → cambiar rol o desactivar usuario
- [ ] RBAC enforced en backend (middleware JWT)
- [ ] Al crear ANALISTA → automáticamente asignado a máquina/línea (opcional MVP)

---

### CON-003: Habilitar/deshabilitar auditoría
**Size**: Small (1 día)

**As an** Admin  
**I want to** opcionalmente habilitar auditoría (trail completo de cambios)  
**So that** cumplimos con políticas internas o regulatorias si lo necesitan

**Acceptance Criteria**:
- [ ] Settings → "Auditoría": checkbox ON/OFF
- [ ] Si ON: todos los cambios se loguean (quién, qué, cuándo)
- [ ] Si OFF: sin logging (más performante)
- [ ] MVP default: OFF (auditoría es v1.1 completa)

---

### CON-004: Ver logs de sincronización
**Size**: Small (1 día)

**As an** Admin  
**I want to** ver logs de sincronización ACATEX (si integración está habilitada)  
**So that** diagnóstico problemas de integración

**Acceptance Criteria**:
- [ ] Settings → "Sincronización ACATEX"
- [ ] Tabla: Fecha, Tipo (import maestros, export resultados), Status, Detalles
- [ ] Filtrar por: Éxito / Error / Última sincronización
- [ ] Click en error → muestra mensaje detallado
- [ ] MVP: básico (v1.1 más detallado)

---

## 📊 RESUMEN DE STORIES POR MÓDULO

| Módulo | Stories | MVP 30d? | v1.1? |
|--------|---------|----------|-------|
| **Inspección** | 8 | ✅ 8 | - |
| **Aprobación** | 5 | ✅ 5 | - |
| **Análisis** | 6 | ❌ 0 | ✅ 6 |
| **Maestros** | 4 | ✅ 4 | - |
| **Sincronización** | 3 | ❌ 0 (solo CON-004) | ✅ 3 |
| **Configuración** | 4 | ✅ 4 | - |
| **TOTAL** | 30 | **18** | **12** |

---

## ✅ MVP 30d SCOPE = 18 Stories

```
Inspección (8):     INS-001 a INS-008
Aprobación (5):     APR-001 a APR-005
Maestros (4):       MAE-001 a MAE-004
Config (4):         CON-001 a CON-004
─────────────────────────────────────
TOTAL MVP 30d:      21 Stories
Esfuerzo:           ~40 dev-days (Backend 10d + Frontend 12d + Infrastructure 4d + overhead)
Timeline:           4 semanas ✅ VIABLE
```

---

## 🎯 MAPPING STORIES → APPLICATION DESIGN COMPONENTS

| Story | Frontend Component | Backend Service | Database Table |
|-------|---|---|---|
| INS-001 | InspectionPage.LoteSearchBar | inspection_service.search_lote | lotes |
| INS-002 | CameraCapture component | upload_photo() | inspections.photo_path |
| INS-003 | DefectTypeSelector | defect_service.get_defects() | defects |
| INS-004 | CommentInput | inspection_service.validate_comment() | inspections.comment |
| INS-005 | MachineSelector | machine_service.get_typical() | inspections.machine_culpable_id |
| INS-006 | OfflineIndicator + Timer | inspection_service.set_timestamps() | inspections.check_in/out |
| INS-007 | offlineSync util + Service Worker | sync_service.upload_pending() | - |
| INS-008 | InspectionHistory Table | inspection_service.get_my_inspections() | inspections |
| APR-001 | PendingLotsTable | approval_service.get_pending() | approvals |
| APR-002 | LoteDetailModal | inspection_service.get_detail() | inspections + photos |
| APR-003 | ApprovalDecision.approveBtn | approval_service.approve() | approvals |
| APR-004 | ApprovalDecision.rejectBtn | approval_service.reject() | approvals |
| APR-005 | notificationService | notification_service.notify_gerente() | (v1.1) |
| MAE-001 | MasterCRUDForm | defect_service.crud() | defects |
| MAE-002 | MasterCRUDForm | machine_service.crud() | machines |
| MAE-003 | MasterCRUDForm | fabric_service.crud() | fabrics |
| MAE-004 | ImportCSV Modal | master_service.bulk_import() | any |
| CON-001 | SetupWizard | config_service.initial_setup() | config table |
| CON-002 | UserManagementPage | user_service.crud() | users |
| CON-003 | AuditToggle Settings | config_service.set_audit() | config table |
| CON-004 | SyncLogsViewer | sync_service.get_logs() | sync_logs table (v1.1) |

---

**Status**: ✅ READY FOR USER REVIEW

