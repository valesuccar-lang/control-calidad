# Implementation Plan — Maestros y Configuración (Unidad 3)

**Wave**: Wave 1 (MVP Foundation)  
**Timeline**: Semana 1-4 (30 días)  
**Motivo de elección**: Datos maestros son prerequisito para que Inspección y Aprobación funcionen. Sin catálogos, no hay opciones para seleccionar.  
**Prioridad**: CRÍTICA  
**Status**: In Planning

---

## 📊 Overview

| Aspecto | Detalle |
|---------|---------|
| **Scope** | CRUD Defectos, Máquinas, Telas + Bulk import + Sincronización ACATEX |
| **Dependencias** | Backend API (Unidad 1) debe estar funcional |
| **Usuarios** | Admin, Jefe de Procesos |
| **Entidades Core** | Defect, Machine, Fabric, ImportLog, SyncConfig |
| **Tecnología** | Python (backend) + React (frontend) + Celery (async jobs) |

---

## 🎯 Objetivos de la Unidad

- ✅ CRUD operacional para los 3 catálogos maestros
- ✅ Bulk import de datos (CSV/Excel)
- ✅ Sincronización automática desde ACATEX (si aplica)
- ✅ Historial de cambios (auditoría)
- ✅ Soft delete (inactivar sin perder histórico)
- ✅ Validaciones de datos
- ✅ Admin UI intuitiva para gerentes

---

## 📋 Fases de Implementación

### Fase 1: Database Setup (Días 1-2)
- [ ] Tablas: defects, machines, fabrics, import_logs, change_logs
- [ ] Índices en nombres y códigos
- [ ] Migraciones Alembic versionadas
- [ ] Seed data inicial

### Fase 2: Backend APIs (Días 3-10)
- [ ] CRUD endpoints para Defects
  - GET /defects (con paginación)
  - POST /defects (crear)
  - PUT /defects/{id} (actualizar)
  - DELETE /defects/{id} (soft delete)
- [ ] CRUD endpoints para Machines (igual estructura)
- [ ] CRUD endpoints para Fabrics (igual estructura)
- [ ] Validaciones de datos
- [ ] Audit logging en cada cambio

### Fase 3: Bulk Import (Días 11-15)
- [ ] Endpoint POST /import/defects (CSV/Excel)
- [ ] Endpoint POST /import/machines
- [ ] Endpoint POST /import/fabrics
- [ ] Validación de datos antes de insertar
- [ ] Rollback en caso de error
- [ ] Reporte de importación (errores, éxitos)
- [ ] Background job con Celery para archivos grandes

### Fase 4: Frontend Masters UI (Días 16-22)
- [ ] Página Defects: tabla, crear, editar, inactivar
- [ ] Página Machines: tabla, crear, editar, inactivar
- [ ] Página Fabrics: tabla, crear, editar, inactivar
- [ ] Validación en formularios
- [ ] Confirmación de cambios
- [ ] Toast notifications
- [ ] Change history viewer

### Fase 5: Import UI (Días 23-26)
- [ ] Upload file interface
- [ ] Preview antes de importar
- [ ] Validación en cliente
- [ ] Progress bar para importes grandes
- [ ] Reporte de resultados

### Fase 6: Testing & Documentation (Días 27-30)
- [ ] Unit tests para APIs
- [ ] Integration tests (DB + API)
- [ ] UI tests para forms
- [ ] Import validation tests
- [ ] Documentation en Swagger
- [ ] Admin guide (How to manage masters)

---

## 📦 Deliverables

```
maestroyconfiguracion-unidad3/
├── CODE-GENERATION-INDEX.md
├── functional-design/
│   ├── domain-entities.md
│   ├── business-rules.md
│   └── business-logic-model.md
├── nfr-design/
│   ├── nfr-requirements.md
│   └── architecture-decisions.md
├── infrastructure-design/
│   ├── deployment-architecture.md
│   ├── database-schema.md
│   └── celery-job-design.md
├── code-generation/
│   ├── backend/
│   │   ├── models/masters_models.py
│   │   ├── routes/
│   │   │   ├── defects_routes.py
│   │   │   ├── machines_routes.py
│   │   │   ├── fabrics_routes.py
│   │   │   └── import_routes.py
│   │   ├── services/
│   │   │   ├── defect_service.py
│   │   │   ├── machine_service.py
│   │   │   ├── fabric_service.py
│   │   │   └── import_service.py
│   │   ├── repositories/
│   │   └── migrations/
│   ├── frontend/
│   │   ├── pages/
│   │   │   ├── DefectsManagement.tsx
│   │   │   ├── MachinesManagement.tsx
│   │   │   ├── FabricsManagement.tsx
│   │   │   └── ImportPage.tsx
│   │   ├── components/
│   │   │   ├── MasterForm.tsx
│   │   │   ├── ImportUpload.tsx
│   │   │   └── MasterTable.tsx
│   │   └── stores/masterStore.ts
│   └── tests/
├── build-and-test/
│   ├── build-instructions.md
│   ├── unit-test-instructions.md
│   └── integration-test-instructions.md
└── GENERATION-STATUS.md
```

---

## ✅ Criterios de Aceptación (Wave 1 Complete)

- [ ] Todos los CRUD operacionales
- [ ] Bulk import funcionando (archivos < 10MB)
- [ ] Coverage > 80% en APIs
- [ ] Validaciones strictas (sin datos inválidos)
- [ ] Audit log en cada cambio
- [ ] UI intuitiva para admin
- [ ] Performance: Listados con 10k registros en < 2s

---

## 🚨 Riesgos

| Riesgo | Impacto | Mitigación |
|--------|---------|-----------|
| Datos inválidos en importación | Alto | Validación exhaustiva + previsualización |
| Performance con muchos registros | Medio | Índices + paginación + caching |
| ACATEX integration complexity | Medio | Planeado para Wave 2 (puede aplazarse) |
| Cambios en estructura de datos | Bajo | Migraciones reversibles |

---

## 📅 Hitos

- **Día 2**: Schema DB completado
- **Día 10**: Todas las APIs CRUD funcionales
- **Día 15**: Bulk import funcionando
- **Día 22**: Frontend completado
- **Día 26**: Import UI completada
- **Día 30**: Testing completo, deployment en staging

---

## 🔄 Dependencias

- Backend API (Unidad 1) funcional
- Database ready
- Celery + Redis para async jobs

---

## 📞 Contactos & Escalaciones

- **Backend Lead**: Validaciones de datos robustas?
- **Admin User**: Necesidades específicas de validación?
- **IT/DevOps**: ACATEX integration requerida en Wave 1?
