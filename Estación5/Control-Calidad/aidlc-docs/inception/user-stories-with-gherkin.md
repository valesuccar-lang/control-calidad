# User Stories con Gherkin (BDD) — MVP 30 Días
**Date**: 2026-05-27 | **Stories**: 21 MVP | **Format**: As a... I want... + Gherkin Scenarios

---

## 📝 FORMATO

Cada story tiene:
1. **As a... I want... So that** (objetivo usuario)
2. **Gherkin Scenarios** (2-3 escenarios: happy path + edge case)

---

## MÓDULO 1: INSPECCIÓN (8 Stories)

### INS-001: Buscar/escanear lote HDR

**As a** Analista **I want to** buscar HDR **So that** cargo rápidamente el contexto del lote

```gherkin
Feature: Buscar y cargar lote
  Scenario: Búsqueda exitosa por código HDR
    Given estoy en página Inspección
    When ingreso "HDR-12847"
    And presiono Buscar
    Then sistema carga: "NOVAKREPEL 500m"
    And muestra máquinas típicas
    
  Scenario: Lote no existe
    Given estoy en página Inspección
    When ingreso "HDR-NOEXISTE"
    Then muestra error "Lote no encontrado"
    And campo búsqueda limpio para nuevo intento
```

---

### INS-002: Capturar foto del defecto

**As a** Analista **I want to** capturar foto clara **So that** queda documentado visualmente

```gherkin
Feature: Capturar y guardar foto
  Scenario: Foto capturada correctamente
    Given lote está cargado
    When presiono "Capturar Foto"
    Then abre cámara nativa
    When captuvo foto clara
    Then foto se guarda en IndexedDB
    And muestra preview 300x300px
    And sin foto: botón Guardar deshabilitado
    
  Scenario: Re-capturar foto
    Given tengo foto guardada
    When presiono "Cambiar Foto"
    Then cámara abre nuevamente
    And foto anterior se reemplaza
```

---

### INS-003: Seleccionar tipo defecto

**As a** Analista **I want to** seleccionar defecto de dropdown **So that** sistema identifica qué encontré

```gherkin
Feature: Seleccionar tipo de defecto
  Scenario: Seleccionar defecto del catálogo
    Given estoy en formulario inspección
    When presiono dropdown "Tipo Defecto"
    Then muestra 25+ opciones (TONODIFFERENTE, MANCHAS, etc.)
    And selecciono "TONODIFFERENTE"
    Then máquina se pre-llena "AGOTAMIENTO 80"
    And defecto es OBLIGATORIO
    
  Scenario: Defecto no catalogado
    Given no encuentro defecto en lista
    When presiono "Reportar Defecto Nuevo"
    Then abre formulario para describir
    And puedo guardar como temporal
```

---

### INS-004: Escribir comentario obligatorio

**As a** Analista **I want to** escribir comentario ≥10 caracteres **So that** documento dónde está el defecto

```gherkin
Feature: Agregar comentario descriptivo
  Scenario: Comentario válido (≥10 chars)
    Given estoy en formulario
    When escribo "Variación de tono entre 200-250m"
    And presiono Guardar
    Then comentario se acepta
    
  Scenario: Comentario muy corto
    Given escribo "Defecto"
    Then botón Guardar permanece deshabilitado
    And muestra error "Mínimo 10 caracteres"
```

---

### INS-005: Confirmar máquina culpable

**As a** Analista **I want to** confirmar o editar máquina **So that** registro es exacto

```gherkin
Feature: Seleccionar máquina culpable
  Scenario: Aceptar máquina sugerida
    Given sistema sugiere "AGOTAMIENTO 80"
    When presiono Confirmar
    Then máquina se registra como culpable
    
  Scenario: Cambiar máquina sugerida
    Given máquina sugerida es "AGOTAMIENTO 80"
    When presiono campo para editar
    And selecciono "AGOTAMIENTO 19"
    Then aparece campo "¿Por qué diferente?"
    And puedo completar y guardar
```

---

### INS-006: Check-in/check-out automático

**As a** Analista **I want to** timestamps automáticos **So that** miden tiempo inspección

```gherkin
Feature: Registro automático de tiempos
  Scenario: Check-in al abrir lote
    Given presiono Buscar lote
    Then check-in = timestamp actual (servidor)
    And contador muestra "0:00" en tiempo real
    
  Scenario: Check-out al guardar
    Given inspeccioné 3 minutos
    When presiono Guardar
    Then check-out = timestamp actual
    And sistema calcula "Tiempo: 3:22"
    And NO puedo editar timestamps
```

---

### INS-007: Guardar offline + sincronizar

**As a** Analista **I want to** guardar sin wifi y sincronizar después **So that** no pierdo datos

```gherkin
Feature: Sincronización offline-first
  Scenario: Guardar sin wifi
    Given indicador muestra "📡 OFFLINE"
    When presiono Guardar inspección
    Then guardado en IndexedDB localmente
    And UI muestra "✓ Guardado localmente"
    And foto almacenada en IndexedDB (blob)
    
  Scenario: Sincronizar cuando wifi vuelve
    Given tengo 3 inspecciones offline
    When wifi se activa (navigator.onLine = true)
    Then sincronización automática inicia
    And Service Worker envía al servidor
    And UI muestra "✓ 3 registros sincronizados"
    And cero pérdida de datos
    
  Scenario: Fallo de sincronización
    Given wifi vuelve pero API no responde
    Then Service Worker reintenta con backoff
    And UI muestra "⚠️ Sincronización pendiente"
    And user puede reintentar manualmente
```

---

### INS-008: Ver historial de mis inspecciones

**As a** Analista **I want to** ver mis últimos registros **So that** verifico que llegaron bien

```gherkin
Feature: Consultar historial personal
  Scenario: Ver últimas 20 inspecciones
    Given presiono "Mis Inspecciones"
    Then muestra tabla: Lote, Defecto, Fecha, Status, Tiempo
    And status color-coded: gris=pendiente, verde=aprobado, rojo=rechazado
    
  Scenario: Filtrar por período
    Given estoy en Mis Inspecciones
    When selecciono "Últimos 7 días"
    Then tabla muestra solo inspecciones de semana actual
```

---

## MÓDULO 2: APROBACIÓN (5 Stories)

### APR-001: Ver lotes pendientes aprobación

**As a** Jefe QA **I want to** ver tabla de lotes pendientes **So that** no pierdo ninguno

```gherkin
Feature: Listar lotes pendientes
  Scenario: Ver tabla pendientes
    Given presiono "Aprobaciones Pendientes"
    Then muestra tabla: Lote, Analista, Defecto, Fecha, Máquina
    And header muestra "42 pendientes"
    And orden: más reciente primero
    
  Scenario: Filtrar por defecto
    Given tengo 42 pendientes
    When selecciono filtro "Defecto = TONODIFFERENTE"
    Then tabla muestra solo 28 registros con TONODIFFERENTE
```

---

### APR-002: Ver foto grande + detalles

**As a** Jefe QA **I want to** ver foto + detalles antes de aprobar **So that** valido calidad de inspección

```gherkin
Feature: Ver detalle de lote con foto
  Scenario: Abrir modal detalle
    Given veo tabla pendientes
    When presiono lote HDR-12847
    Then muestra modal con:
      - Foto defecto (80% pantalla)
      - Lote, Tela, Analista, Defecto, Máquina, Comentario
      - Timestamps: check-in y check-out
    
  Scenario: Navegar entre fotos sin cerrar
    Given modal está abierto
    When presiono flecha derecha
    Then carga siguiente lote pendiente
    And foto se actualiza
    
  Scenario: Foto borrosa
    Given foto tiene baja calidad
    When abro modal
    Then UI muestra "⚠️ Foto baja calidad"
    And puedo aprobar igualmente o pedir re-inspección
```

---

### APR-003: Aprobar reproceso

**As a** Jefe QA **I want to** presionar Aprobar **So that** lote se marca como válido

```gherkin
Feature: Aprobar inspección
  Scenario: Aprobar lote
    Given veo detalle lote
    When presiono botón "Aprobar"
    Then pide confirmación: "¿Confirmar?"
    When presiono Sí
    Then approval registrado: status=APPROVED, timestamp, user=yo
    And lote desaparece de pendientes
    And UI muestra "✓ Lote aprobado"
```

---

### APR-004: Rechazar lote

**As a** Jefe QA **I want to** rechazar lote con motivo **So that** analista re-inspecciona

```gherkin
Feature: Rechazar inspección
  Scenario: Rechazar con motivo
    Given veo detalle lote
    When presiono "Rechazar"
    Then abre campo "Motivo" (obligatorio ≥10 chars)
    And sugiere: "Foto borrosa", "Falsa alarma", "No confirmado"
    When ingreso motivo
    And presiono Confirmar
    Then rejection registrado: status=REJECTED, motivo
    And lote desaparece de pendientes
```

---

### APR-005: Notificar Gerente automáticamente

**As a** Jefe QA **I want to** que Gerente reciba notificación **So that** ve cambios en tiempo real

```gherkin
Feature: Notificación a Gerente
  Scenario: Enviar notificación al aprobar
    Given presiono "Aprobar"
    When aprobación se registra en BD
    Then notificación enviada a Gerente en <30 seg
    And Gerente recibe: "Nuevo lote aprobado: HDR-12847"
    And puede hacer click → ver detalles
```

---

## MÓDULO 4: MAESTROS (4 Stories)

### MAE-001: CRUD Defectos

**As an** Admin **I want to** crear/editar/inactivar defectos **So that** catálogo está actualizado

```gherkin
Feature: Gestionar maestro defectos
  Scenario: Crear defecto
    Given presiono "Crear Defecto"
    Then abre form: id, nombre, descripción, máquina_típica
    When completo form (id="DEF-NEW", nombre="RAYADO")
    And presiono Guardar
    Then defecto creado en BD
    And aparece en dropdown Inspección
    
  Scenario: Editar defecto
    Given veo tabla defectos
    When presiono "Editar" en DEF-TON
    Then abre form con valores actuales
    And puedo cambiar (excepto id)
    
  Scenario: Inactivar defecto
    Given presiono "Inactivar" en defecto
    Then aparece confirmación
    When confirmo
    Then defecto marcado inactivo (soft delete)
    And ya no aparece en dropdown
    And pero se ve en histórico de inspecciones pasadas
```

---

### MAE-002: CRUD Máquinas

**As an** Admin **I want to** mantener catálogo máquinas **So that** están disponibles para seleccionar

```gherkin
Feature: Gestionar maestro máquinas
  Scenario: Crear máquina
    Given presiono "Crear Máquina"
    When ingreso id="MAQ-AGO-90", nombre="AGOTAMIENTO 90", proceso="TINTORERIA"
    And presiono Guardar
    Then máquina disponible en dropdown
```

---

### MAE-003: CRUD Telas

**As an** Admin **I want to** mantener catálogo telas **So that** analistas seleccionan tela correcta

```gherkin
Feature: Gestionar maestro telas
  Scenario: Cargar 20 telas iniciales
    Given estoy en Maestro Telas
    When presiono "Cargar Iniciales"
    Then carga: NOVAKREPEL, AMORELA, SUEA OS, etc. (20 telas)
    And UI muestra "✓ 20 telas cargadas"
```

---

### MAE-004: Cargar maestros iniciales (CSV)

**As an** Admin **I want to** importar CSV con 25 defectos, 15 máquinas, 20 telas **So that** no rellenar manualmente

```gherkin
Feature: Importar maestros desde CSV
  Scenario: Importar CSV defectos
    Given presiono "Importar CSV"
    When selecciono archivo defectos.csv
    And archivo tiene columnas: id, nombre, descripción, máquina_típica
    And presiono Importar
    Then progress bar muestra progreso
    Then "✓ 25 defectos importados, 0 errores"
    
  Scenario: Duplicados detectados
    Given CSV contiene id duplicado "DEF-TON"
    When intento importar
    Then muestra error: "DEF-TON ya existe"
    And pregunta: ¿Reemplazar o saltear?
```

---

## MÓDULO 6: CONFIGURACIÓN (4 Stories)

### CON-001: Setup inicial

**As an** Admin **I want to** completar setup en primer login **So that** sistema está configurado

```gherkin
Feature: Setup inicial del sistema
  Scenario: Wizard setup completo
    Given primer login como ADMIN
    Then redirige a SetupWizard
    
    Paso 1: Información empresa
    When ingreso "Manufactureras Eliot", "Bogotá"
    And presiono Siguiente
    
    Paso 2: Integración ACATEX
    When respondo "¿Integrar con ACATEX?" = "No"
    And presiono Siguiente
    
    Paso 3: Resumen
    Then muestra resumen: Empresa=Eliot, ACATEX=NO
    When presiono "Confirmar Setup"
    Then redirect a cargar maestros
    And setup completado en <10 minutos
```

---

### CON-002: Gestión usuarios y roles

**As an** Admin **I want to** crear usuarios + asignar roles **So that** cada uno accede a lo suyo

```gherkin
Feature: Gestionar usuarios y permisos
  Scenario: Crear usuario ANALISTA
    Given presiono "Crear Usuario"
    When ingreso email="analista@eliot.com", nombre="María", rol="ANALISTA"
    And presiono Guardar
    Then usuario creado
    And email sent con password temporal
    And María recibe acceso como ANALISTA
    
  Scenario: RBAC enforced
    Given María es ANALISTA
    When intenta acceder a /config/usuarios
    Then muestra error 403 "No autorizado"
```

---

### CON-003: Habilitar auditoría

**As an** Admin **I want to** opcionalmente activar auditoría **So that** cumplo políticas internas

```gherkin
Feature: Configurar auditoría
  Scenario: Habilitar auditoría
    Given estoy en Settings
    When activo toggle "Auditoría"
    And presiono Guardar
    Then todos los cambios se loguean
    And default MVP: OFF (v1.1 completa)
```

---

### CON-004: Ver logs de sincronización

**As an** Admin **I want to** ver logs de sincronización ACATEX **So that** diagnóstico problemas

```gherkin
Feature: Consultar logs de sincronización
  Scenario: Ver logs (v1.1)
    Given Settings → Sincronización
    Then muestra tabla: Fecha, Tipo, Status, Detalles
    And filtro: Éxito / Error
    
    Note: MVP básico, v1.1 será exhaustivo
```

---

## ✅ RESUMEN GHERKIN

| Story | Escenarios | Status |
|-------|-----------|--------|
| INS-001 | 2 (buscar éxito, lote no existe) | ✅ |
| INS-002 | 2 (capturar, re-capturar) | ✅ |
| INS-003 | 2 (seleccionar, no catalogado) | ✅ |
| INS-004 | 2 (válido, muy corto) | ✅ |
| INS-005 | 2 (aceptar, cambiar) | ✅ |
| INS-006 | 2 (check-in, check-out) | ✅ |
| INS-007 | 3 (offline, sync éxito, sync fail) | ✅ |
| INS-008 | 2 (ver historial, filtro) | ✅ |
| APR-001 | 2 (ver tabla, filtro) | ✅ |
| APR-002 | 3 (modal, navegar, foto borrosa) | ✅ |
| APR-003 | 1 (aprobar) | ✅ |
| APR-004 | 1 (rechazar) | ✅ |
| APR-005 | 1 (notificación) | ✅ |
| MAE-001 | 3 (crear, editar, inactivar) | ✅ |
| MAE-002 | 1 (crear) | ✅ |
| MAE-003 | 1 (cargar iniciales) | ✅ |
| MAE-004 | 2 (importar CSV, duplicados) | ✅ |
| CON-001 | 1 (wizard) | ✅ |
| CON-002 | 2 (crear usuario, RBAC) | ✅ |
| CON-003 | 1 (toggle auditoría) | ✅ |
| CON-004 | 1 (ver logs) | ✅ |
| **TOTAL** | **39 escenarios** | **✅ LISTO** |

---

## 🎯 PRÓXIMOS PASOS

1. ✅ **User Stories con Gherkin**: Completado (21 stories, 39 escenarios)
2. ✅ **Application Design**: Completado
3. ➡️ **CONSTRUCTION PHASE - CODE GENERATION**: Siguiente

---

**Status**: ✅ INCEPTION PHASE COMPLETADO - LISTO PARA CONSTRUCTION

