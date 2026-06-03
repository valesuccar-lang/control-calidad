# Frontend Web — Wave 2 (Analysis & Reports)

**Unit**: frontend-web-unidad-2-wave2  
**Wave**: Wave 2 (Enhancement)  
**Duration**: 30 days (2026-07-01 to 2026-07-31)  
**Story Points**: 150  
**Team**: 2 frontend developers  
**Priority**: HIGH  
**Status**: Not Started (starts after Wave 1)

---

## 📋 Overview

Build analytics and reporting capabilities for quality control data. Includes dashboards with charts, PDF/Excel export, and advanced search.

### Key Deliverables
- Analytics dashboard with key metrics
- Charts: By Machine, By Defect, By Fabric
- PDF and Excel report export
- Advanced search and filters
- Real-time updates via WebSocket

---

## 🎯 Acceptance Criteria

- [ ] Dashboard displays real data
- [ ] Charts render correctly
- [ ] PDF/Excel exports working
- [ ] Search filters responsive (< 200ms)
- [ ] Mobile responsive
- [ ] Test coverage ≥ 75%

---

## 📊 Phase Breakdown

### Phase 1: Analysis Dashboard (Days 1-10)
**Story Points**: 50  
**Assignee**: Frontend Lead

- [ ] Create analytics page layout
  - Key metrics cards (total, last 24h, last week, last month)
  - Chart containers
  - Filter section
  - Estimate: 8 SP
  
- [ ] Implement key metrics cards
  - Total reprocesos hoy/semana/mes
  - GET /analytics/metrics integration
  - Card component styling
  - Estimate: 8 SP
  
- [ ] Create bar chart (by machine)
  - Using Chart.js or Recharts
  - Integration with GET /analytics/machines
  - Responsive sizing
  - Estimate: 8 SP
  
- [ ] Create pie chart (by defect)
  - GET /analytics/defects
  - Legend with percentages
  - Estimate: 8 SP
  
- [ ] Create pie chart (by fabric)
  - GET /analytics/fabrics
  - Estimate: 8 SP
  
- [ ] Add date range picker
  - Select period (today, week, month, custom)
  - Update charts on change
  - Estimate: 8 SP
  
- [ ] Real-time updates
  - WebSocket connection to /ws/analytics
  - Update charts every 30s
  - Estimate: 2 SP

**Acceptance Criteria**
- [ ] Charts display data correctly
- [ ] Filters update charts
- [ ] Responsive on mobile
- [ ] No console errors

---

### Phase 2: Reports & Export (Days 11-20)
**Story Points**: 50  
**Assignee**: Frontend Lead + 1 Developer

- [ ] Create report builder page
  - Select report type (Executive, Detailed)
  - Choose metrics to include
  - Select date range
  - Estimate: 10 SP
  
- [ ] PDF export functionality
  - POST /reports/export/pdf
  - Include charts and tables
  - Branding (header/footer)
  - Estimate: 15 SP
  
- [ ] Excel export functionality
  - POST /reports/export/excel
  - Multiple sheets (summary, details, charts)
  - Formatting (colors, fonts)
  - Estimate: 15 SP
  
- [ ] Download management
  - Show download progress
  - Handle errors gracefully
  - Auto-retry on failure
  - Estimate: 6 SP
  
- [ ] Scheduled reports (advanced)
  - Create scheduled report (daily/weekly/monthly)
  - Email delivery
  - Estimate: 4 SP

**Acceptance Criteria**
- [ ] PDF exports correctly
- [ ] Excel exports correctly
- [ ] Download progress visible
- [ ] Files open properly in external apps

---

### Phase 3: Advanced Search & Filters (Days 21-28)
**Story Points**: 40  
**Assignee**: Frontend Lead

- [ ] Advanced search interface
  - Full-text search on comments
  - Multi-select filters (machine, defect, fabric, status)
  - Date range picker
  - Estimate: 12 SP
  
- [ ] Filter persistence
  - Save favorite filters
  - Load saved filters
  - Share filter link
  - Estimate: 8 SP
  
- [ ] Search results page
  - Table with detailed results
  - Pagination
  - Sort by columns
  - Estimate: 10 SP
  
- [ ] Saved searches
  - Create/manage saved searches
  - Quick access from sidebar
  - Estimate: 6 SP
  
- [ ] Performance optimization
  - Debounce search input (300ms)
  - Lazy load results
  - Cache results
  - Estimate: 4 SP

**Acceptance Criteria**
- [ ] Search filters responsive (< 200ms)
- [ ] Results display correctly
- [ ] Saved searches work
- [ ] Mobile accessible

---

### Phase 4: Testing & Polish (Days 29-30)
**Story Points**: 10  
**Assignee**: Frontend Lead

- [ ] Component tests for charts
  - Chart rendering tests
  - Data update tests
  - Estimate: 3 SP
  
- [ ] Integration tests for analytics
  - API mocking
  - Full flow testing
  - Estimate: 4 SP
  
- [ ] Performance testing
  - Chart rendering performance
  - Search responsiveness
  - Estimate: 2 SP
  
- [ ] Documentation
  - Report template guide
  - Search guide
  - Estimate: 1 SP

**Acceptance Criteria**
- [ ] Coverage ≥ 75%
- [ ] Performance baseline met
- [ ] Documentation complete

---

## 🎯 Success Metrics

| Metric | Target |
|--------|--------|
| Chart Render Time | < 1s |
| Search Response Time | < 200ms |
| Export Time (PDF) | < 5s |
| Test Coverage | ≥ 75% |

---

## 🚨 Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Large dataset performance | High | Pagination, virtualization, caching |
| Chart rendering slow | Medium | Use efficient library, optimize data |
| Export generation timeout | Medium | Background job, progress tracking |

---

## 📦 Definition of Done

- [ ] All features implemented
- [ ] Tests passing
- [ ] Performance baselines met
- [ ] Mobile responsive
- [ ] Documentation complete

---

## 🔗 Dependencies

- **Requires**: frontend-web-unidad-2-wave1 (Wave 1 must be complete)
- **Requires**: Backend API (analytics endpoints)

---

**Created**: 2026-06-01  
**Estimate Confidence**: Medium
