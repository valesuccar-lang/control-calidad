# Maestros y Configuración — Wave 1

**Unit**: maestroyconfiguracion-unidad3  
**Wave**: Wave 1 (MVP Foundation)  
**Duration**: 30 days (2026-06-01 to 2026-06-30)  
**Story Points**: 120  
**Team**: 1 developer (backend) + 1 developer (frontend)  
**Priority**: CRITICAL  
**Status**: Blocked (waiting for Backend API)

---

## 📋 Overview

Build master data management system for managing Defects, Machines, and Fabrics. Includes CRUD operations, bulk import, and admin UI.

### Key Deliverables
- 3 master data entities (Defects, Machines, Fabrics)
- Bulk import (CSV/Excel support)
- Admin UI for master management
- Data validation and audit logging
- Performance optimized (10k+ records)

---

## 🎯 Acceptance Criteria

- [ ] All CRUD operations working
- [ ] Bulk import handles 10k+ records in < 30s
- [ ] Data validation prevents invalid entries
- [ ] Soft delete preserves history
- [ ] Admin UI is intuitive
- [ ] Test coverage ≥ 80%
- [ ] Performance: List 10k records in < 2s

---

## 📊 Phase Breakdown

### Phase 1: Database Setup (Days 1-2)
**Story Points**: 15  
**Assignee**: Backend Lead

- [ ] Design master tables schema
  - defects: id, name, code, description, active, created_at, updated_at
  - machines: id, name, code, location, active, created_at, updated_at
  - fabrics: id, name, code, supplier, active, created_at, updated_at
  - Estimate: 5 SP
  
- [ ] Create Alembic migrations
  - Estimate: 5 SP
  
- [ ] Add indices and constraints
  - Unique on name/code
  - Foreign key constraints
  - Estimate: 5 SP

**Acceptance Criteria**
- [ ] Schema matches entity design
- [ ] Migrations are reversible
- [ ] Indices improve query performance

---

### Phase 2: Backend APIs (Days 3-10)
**Story Points**: 45  
**Assignee**: Backend Lead

- [ ] Create CRUD endpoints for Defects
  - GET /defects (paginated, searchable)
  - POST /defects
  - PUT /defects/{id}
  - DELETE /defects/{id} (soft delete)
  - Estimate: 10 SP
  
- [ ] Create CRUD endpoints for Machines
  - Same pattern as defects
  - Estimate: 10 SP
  
- [ ] Create CRUD endpoints for Fabrics
  - Same pattern as defects
  - Estimate: 10 SP
  
- [ ] Implement validation service
  - Name uniqueness validation
  - Code format validation
  - Enum validation for status
  - Estimate: 8 SP
  
- [ ] Add audit logging
  - Log all changes to masters
  - Endpoint: GET /masters/audit
  - Estimate: 7 SP

**Acceptance Criteria**
- [ ] All CRUD operations working
- [ ] Validations enforced
- [ ] Audit log complete
- [ ] API tests > 80% coverage

---

### Phase 3: Bulk Import (Days 11-15)
**Story Points**: 25  
**Assignee**: Backend Lead

- [ ] Create import endpoints
  - POST /import/defects
  - POST /import/machines
  - POST /import/fabrics
  - Estimate: 8 SP
  
- [ ] Implement CSV/Excel parser
  - Using pandas/openpyxl
  - Handle large files (100MB+)
  - Estimate: 8 SP
  
- [ ] Add validation and error handling
  - Validate each row before insert
  - Rollback on critical error
  - Generate error report
  - Estimate: 7 SP
  
- [ ] Create Celery task for async import
  - Background job for large imports
  - Progress tracking
  - Email notification on completion
  - Estimate: 2 SP

**Acceptance Criteria**
- [ ] Import 10k records in < 30s
- [ ] Validation prevents bad data
- [ ] Error report is clear
- [ ] Rollback works correctly

---

### Phase 4: Frontend UI (Days 16-22)
**Story Points**: 28  
**Assignee**: Frontend Lead

- [ ] Create Masters management page
  - Navigation to Defects/Machines/Fabrics tabs
  - Estimate: 4 SP
  
- [ ] Create Defects table component
  - Display all defects
  - Search/filter by name
  - Pagination
  - Estimate: 6 SP
  
- [ ] Create Defects form (Create/Edit)
  - Form validation (client-side)
  - Submit to backend
  - Error handling
  - Estimate: 6 SP
  
- [ ] Repeat for Machines and Fabrics
  - Estimate: 12 SP

**Acceptance Criteria**
- [ ] Forms work correctly
- [ ] Validation prevents submission of bad data
- [ ] UI is responsive (mobile + desktop)
- [ ] Accessibility WCAG AA

---

### Phase 5: Import UI (Days 23-26)
**Story Points**: 10  
**Assignee**: Frontend Lead

- [ ] Create import page
  - File upload component
  - Drag-and-drop support
  - Estimate: 4 SP
  
- [ ] Add preview before import
  - Show first 10 rows
  - Highlight validation errors
  - Estimate: 3 SP
  
- [ ] Progress and results display
  - Progress bar during import
  - Success/error report
  - Estimate: 3 SP

**Acceptance Criteria**
- [ ] Upload works for CSV and Excel
- [ ] Preview prevents accidental imports
- [ ] User gets clear feedback

---

### Phase 6: Testing & Documentation (Days 27-30)
**Story Points**: 17  
**Assignee**: Backend Lead + Frontend Lead

- [ ] Unit tests
  - Service layer tests
  - Validation logic tests
  - Estimate: 6 SP
  
- [ ] Integration tests
  - API + DB tests
  - Import end-to-end
  - Estimate: 6 SP
  
- [ ] UI tests
  - Form submissions
  - Error scenarios
  - Estimate: 3 SP
  
- [ ] Documentation
  - API endpoints doc
  - Admin user guide
  - Estimate: 2 SP

**Acceptance Criteria**
- [ ] Coverage ≥ 80%
- [ ] All tests passing
- [ ] Documentation complete

---

## 🎯 Success Metrics

| Metric | Target |
|--------|--------|
| Import Speed (10k records) | < 30s |
| Query Performance (10k records) | < 2s |
| Test Coverage | ≥ 80% |
| Data Validation Pass Rate | 100% |

---

## 🚨 Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Slow import performance | High | Optimize DB writes, use bulk insert |
| Duplicate data import | Medium | Add uniqueness validation, preview step |
| File upload size limits | Medium | Chunk large files, use async jobs |

---

## 📦 Definition of Done

- [ ] All CRUD operations working
- [ ] Bulk import tested with 10k+ records
- [ ] Admin UI functional and responsive
- [ ] Test coverage ≥ 80%
- [ ] Deployed to staging
- [ ] Accepted by QA

---

## 🔗 Dependencies

- **Blocks**: frontend-web-unidad-2-wave1 (needs master data endpoints)

---

**Created**: 2026-06-01  
**Estimate Confidence**: High
