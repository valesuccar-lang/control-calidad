# Frontend Web — Wave 1 (Core Modules)

**Unit**: frontend-web-unidad-2-wave1  
**Wave**: Wave 1 (MVP Foundation)  
**Duration**: 30 days (2026-06-01 to 2026-06-30)  
**Story Points**: 280  
**Team**: 2 frontend developers  
**Priority**: CRITICAL  
**Status**: Blocked (waiting for Backend API)

---

## 📋 Overview

Build core user interface for Quality Control platform. Includes Dashboard, Inspection module, Approval workflow, and Masters management UI.

### Key Deliverables
- Responsive dashboard
- Inspection capture workflow (photos, defects, comments)
- Approval queue interface
- Masters management (CRUD)
- JWT authentication and protected routes
- Mobile-first responsive design

---

## 🎯 Acceptance Criteria

- [ ] All pages functional and responsive
- [ ] Mobile responsive (320px+)
- [ ] Page load < 3s (3G)
- [ ] Lighthouse score ≥ 80
- [ ] Accessibility WCAG AA
- [ ] Test coverage ≥ 75%
- [ ] Zero console errors
- [ ] All user flows end-to-end testable

---

## 📊 Phase Breakdown

### Phase 1: Setup & Architecture (Days 1-3)
**Story Points**: 25  
**Assignee**: Frontend Lead

- [ ] Setup Vite + React 18 + TypeScript
  - Create project with: `npm create vite@latest`
  - Configure TypeScript strict mode
  - Estimate: 3 SP
  
- [ ] Setup Zustand state management
  - Create stores: authStore, inspectionStore, approvalStore, masterStore
  - Setup store persistence
  - Estimate: 5 SP
  
- [ ] Configure Tailwind CSS
  - Install and setup Tailwind
  - Create theme (colors, spacing, etc.)
  - Estimate: 3 SP
  
- [ ] Setup React Router
  - Create routes: /, /login, /inspections, /approvals, /masters
  - Protected routes with auth check
  - Estimate: 4 SP
  
- [ ] Create API client
  - Setup axios with interceptors
  - Error handling middleware
  - Token management
  - Estimate: 5 SP
  
- [ ] Component library setup
  - Create Button, Input, Modal, Card components
  - Storybook setup (optional)
  - Estimate: 5 SP

**Acceptance Criteria**
- [ ] App runs locally without errors
- [ ] All routes accessible
- [ ] State management working
- [ ] API client ready

---

### Phase 2: Authentication & Layout (Days 4-6)
**Story Points**: 25  
**Assignee**: Frontend Lead

- [ ] Create Login page
  - Email and password inputs
  - Form validation
  - Login button
  - Error message display
  - Estimate: 6 SP
  
- [ ] Implement authentication flow
  - POST /auth/login integration
  - Store JWT token
  - Redirect to dashboard on success
  - Estimate: 5 SP
  
- [ ] Create main layout
  - Sidebar navigation
  - Header with user info
  - Logout button
  - Estimate: 6 SP
  
- [ ] Protected routes
  - Redirect to login if not authenticated
  - Check user role for access
  - Estimate: 4 SP
  
- [ ] Add user context
  - Global user state
  - Role-based UI elements
  - Estimate: 4 SP

**Acceptance Criteria**
- [ ] Login works end-to-end
- [ ] Protected routes require auth
- [ ] Logout clears token
- [ ] Navigation is intuitive

---

### Phase 3: Inspection Module (Days 7-12)
**Story Points**: 60  
**Assignee**: Frontend Lead + 1 Developer

- [ ] Create Inspection list page
  - GET /inspections integration
  - Table with inspection details
  - Pagination
  - Filter by date
  - Estimate: 8 SP
  
- [ ] Create Inspection form (Create)
  - Lot number/barcode search input
  - Photo upload from camera
  - Defect type dropdown (GET /defects)
  - Machine selection dropdown
  - Comment textarea
  - Save button (POST /inspections)
  - Estimate: 15 SP
  
- [ ] Photo capture component
  - Mobile camera access
  - Preview before upload
  - Image compression
  - Estimate: 8 SP
  
- [ ] Create Inspection detail view
  - Display all inspection info
  - Show photo (fullscreen option)
  - Edit button (if not approved)
  - Estimate: 6 SP
  
- [ ] Inspection history
  - List user's inspections
  - Filter by status
  - Estimate: 6 SP
  
- [ ] Error handling & validation
  - Form validation (client-side)
  - Display server errors
  - Retry mechanism
  - Estimate: 6 SP
  
- [ ] Loading states and skeleton screens
  - Show loading while fetching
  - Skeleton screens for better UX
  - Estimate: 5 SP

**Acceptance Criteria**
- [ ] Photo capture works on mobile
- [ ] Form validation prevents submission of incomplete data
- [ ] All API calls working
- [ ] Loading states visible
- [ ] Error messages helpful

---

### Phase 4: Approval Module (Days 13-16)
**Story Points**: 40  
**Assignee**: Frontend Lead

- [ ] Create Pending approvals list
  - GET /approvals/pending
  - Table with lot info, defect, photo
  - Filter by date
  - Estimate: 8 SP
  
- [ ] Create Approval detail view
  - Display inspection details
  - Show photo (fullscreen)
  - Machine and defect info
  - Estimate: 8 SP
  
- [ ] Approval actions
  - Approve button (POST /approvals/{id}/approve)
  - Reject button (POST /approvals/{id}/reject)
  - With confirmation modal
  - Estimate: 6 SP
  
- [ ] Rejection reason input
  - Textarea for rejection comment
  - Required field validation
  - Estimate: 4 SP
  
- [ ] Status indicators
  - Visual status (pending, approved, rejected)
  - Badge styling
  - Estimate: 4 SP
  
- [ ] Real-time updates
  - Poll for new approvals (every 30s)
  - Badge notification for pending count
  - Estimate: 6 SP
  
- [ ] Bulk approval (optional)
  - Select multiple items
  - Batch approve/reject
  - Estimate: 4 SP

**Acceptance Criteria**
- [ ] Can approve/reject without errors
- [ ] Status updates immediately
- [ ] Pending count accurate
- [ ] Photo display is clear

---

### Phase 5: Masters Module (Days 17-20)
**Story Points**: 50  
**Assignee**: Frontend Lead

- [ ] Create Defects management page
  - GET /defects table
  - Search/filter by name
  - Pagination
  - Estimate: 8 SP
  
- [ ] Defects CRUD operations
  - Create modal (POST /defects)
  - Edit modal (PUT /defects/{id})
  - Delete with confirmation (DELETE /defects/{id})
  - Estimate: 10 SP
  
- [ ] Repeat for Machines
  - Same as Defects
  - Estimate: 10 SP
  
- [ ] Repeat for Fabrics
  - Same as Defects
  - Estimate: 10 SP
  
- [ ] Validation and error handling
  - Form validation
  - Duplicate name prevention
  - Display server errors
  - Estimate: 6 SP
  
- [ ] Confirmation dialogs
  - Confirm delete
  - Confirm submit
  - Estimate: 3 SP
  
- [ ] Loading states
  - Show loading during save
  - Disable buttons while loading
  - Estimate: 3 SP

**Acceptance Criteria**
- [ ] CRUD operations working
- [ ] Validation prevents bad data
- [ ] Confirmation dialogs prevent accidents
- [ ] Error messages are clear

---

### Phase 6: Testing & Polish (Days 21-30)
**Story Points**: 85  
**Assignee**: Frontend Lead + 1 Developer

- [ ] Unit tests for stores
  - authStore tests
  - inspectionStore tests
  - Estimate: 12 SP
  
- [ ] Component tests
  - Test form components
  - Test button click handlers
  - Test conditional rendering
  - Estimate: 15 SP
  
- [ ] Integration tests (API mocking)
  - Test login flow
  - Test inspection creation
  - Test approval workflow
  - Estimate: 15 SP
  
- [ ] E2E tests
  - Critical path: login → inspect → approve
  - Using Cypress or Playwright
  - Estimate: 12 SP
  
- [ ] Accessibility audit
  - Run axe accessibility checker
  - Fix WCAG AA issues
  - Estimate: 6 SP
  
- [ ] Performance optimization
  - Code splitting
  - Lazy loading routes
  - Image optimization
  - Estimate: 10 SP
  
- [ ] Mobile responsiveness
  - Test on multiple screen sizes
  - Fix layout issues
  - Test touch interactions
  - Estimate: 8 SP
  
- [ ] Browser compatibility
  - Test Chrome, Firefox, Safari
  - Fix compatibility issues
  - Estimate: 4 SP
  
- [ ] Documentation
  - Component documentation
  - Setup guide
  - Deployment guide
  - Estimate: 3 SP

**Acceptance Criteria**
- [ ] Test coverage ≥ 75%
- [ ] Lighthouse score ≥ 80
- [ ] Accessibility WCAG AA
- [ ] Mobile responsive
- [ ] Page load < 3s (3G)
- [ ] Zero console errors

---

## 🎯 Success Metrics

| Metric | Target |
|--------|--------|
| Lighthouse Score | ≥ 80 |
| Page Load Time (3G) | < 3s |
| Test Coverage | ≥ 75% |
| Accessibility Score | WCAG AA |
| Mobile Responsive | 320px+ |

---

## 🚨 Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Photo upload slow on mobile | High | Compress client-side, show progress |
| API changes break UI | Medium | Use OpenAPI contract, mock in tests |
| Performance issues with large tables | Medium | Use pagination, virtualization |

---

## 📦 Definition of Done

- [ ] All pages functional
- [ ] Mobile responsive
- [ ] Tests passing
- [ ] Coverage ≥ 75%
- [ ] Lighthouse ≥ 80
- [ ] Accessibility verified
- [ ] Deployed to staging

---

## 🔗 Dependencies

- **Requires**: backend-api-unidad-1 (APIs must be ready)
- **Requires**: maestroyconfiguracion-unidad3 (master data endpoints)

---

**Created**: 2026-06-01  
**Estimate Confidence**: High
