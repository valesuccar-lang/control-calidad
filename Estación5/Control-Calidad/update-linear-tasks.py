#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linear Task Updater — OpenSymphony Contract Compliance

Updates the 32 issues already in Linear with the strict OpenSymphony
task contract: Definition + Acceptance Criteria + Test Plan +
Context References + Dependencies + Milestone Grouping.
"""

import requests
import sys
import io

# Fix encoding on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuration
LINEAR_API_KEY = os.environ.get("LINEAR_API_KEY", "")
LINEAR_ENDPOINT = "https://api.linear.app/graphql"
PROJECT_ID = "19a6b5ec-7a32-44b0-8d48-de0a5d753625"

HEADERS = {
    "Authorization": LINEAR_API_KEY,
    "Content-Type": "application/json",
}


def graphql_query(query, variables=None):
    payload = {"query": query, "variables": variables or {}}
    try:
        response = requests.post(LINEAR_ENDPOINT, json=payload, headers=HEADERS, timeout=15)
        data = response.json()
        if "errors" in data:
            print(f"GraphQL Error: {data['errors']}")
            return None
        return data.get("data", {})
    except Exception as e:
        print(f"API Error: {e}")
        return None


# ============================================================
# OpenSymphony-Contract Task Definitions (32 tasks)
# Each task: title -> {definition, ac, test_plan, context, deps, milestone, estimate}
# ============================================================

TASKS = {
    # ============= UNIT 1: BACKEND API (6 tasks) =============
    "backend-api-unidad-1 → Setup Infrastructure": {
        "milestone": "M1: Bootstrap & Setup",
        "estimate": 5,
        "definition": "Initialize the FastAPI backend repository with Python 3.11+, poetry for dependency management, PostgreSQL connection, and CI/CD via GitHub Actions. Establish directory structure for DDD layering (domain, application, infrastructure, presentation).",
        "ac": [
            "pyproject.toml with pinned dependencies (fastapi>=0.111, sqlalchemy>=2.0, alembic>=1.13, asyncpg>=0.29, pydantic>=2.7)",
            "Makefile targets: install, test, build, lint, deploy",
            "Directory structure: app/{domain,application,infrastructure,routes,schemas}, tests/{unit,integration}, migrations/versions/",
            "GitHub Actions workflow runs on PR (lint + tests)",
            "README with local setup instructions"
        ],
        "test_plan": [
            "Run `make install` → no dependency conflicts",
            "Run `make lint` → 0 violations (ruff + black check)",
            "Run `make test` → empty suite passes (pytest collects 0 tests OK)",
            "Push branch → GitHub Actions triggers and completes < 5min"
        ],
        "context_refs": [
            "aidlc-docs/inception/workflow-planning.md",
            "aidlc-docs/inception/application-design.md",
            "docs/tasks/001-backend-api-wave1.md (Phase 1)"
        ],
        "deps": "None (foundational task)",
    },
    "backend-api-unidad-1 → Domain & Entities": {
        "milestone": "M2: Domain & Data Layer",
        "estimate": 8,
        "definition": "Implement DDD domain layer: entities (Inspection, Approval, User, Master), value objects (DefectType, MachineStatus, LotNumber), business rules validators, and SQLAlchemy ORM models with relationships and indices.",
        "ac": [
            "Entities defined in app/domain/entities.py with type hints",
            "Value objects in app/domain/value_objects.py (immutable, hashable)",
            "Business rules enforced via __post_init__ or validators",
            "SQLAlchemy ORM mapped in app/models/orm.py with FK + unique constraints",
            "Initial Alembic migration generated and reversible (up/down tested)"
        ],
        "test_plan": [
            "Unit test each entity invariant (e.g., Inspection requires lot+defect+photo)",
            "Test value object equality and immutability",
            "Run `alembic upgrade head` then `alembic downgrade -1` → no errors",
            "Validate schema: `psql -c \"\\d+ inspections\"` shows expected indices"
        ],
        "context_refs": [
            "aidlc-docs/inception/ddd-design.md",
            "aidlc-docs/inception/units-ddd-mapping.md",
            "aidlc-docs/construction/backend-api-unidad 1/domain-entities.md",
            "aidlc-docs/construction/backend-api-unidad 1/business-rules.md"
        ],
        "deps": "Setup Infrastructure",
    },
    "backend-api-unidad-1 → Core APIs": {
        "milestone": "M3: API & Service Layer",
        "estimate": 13,
        "definition": "Implement 15+ REST endpoints across 4 modules (Auth, Inspection, Approval, Masters CRUD) using FastAPI routers, Pydantic v2 schemas, JWT authentication, and dependency injection. All endpoints return consistent error envelopes.",
        "ac": [
            "Auth: POST /login, POST /logout, POST /refresh, GET /me",
            "Inspections: POST /inspections, GET /inspections/{id}, GET /inspections (paginated), PUT /inspections/{id}",
            "Approvals: GET /approvals/pending, GET /approvals/{id}, POST /approvals/{id}/approve, POST /approvals/{id}/reject",
            "Masters CRUD: defects, machines, fabrics (full CRUD with soft delete)",
            "All endpoints documented in Swagger (auto-generated)",
            "RBAC enforced via FastAPI Depends (require_role)"
        ],
        "test_plan": [
            "Integration test happy path for each endpoint with TestClient",
            "Test 401 when no token, 403 when wrong role",
            "Test pagination: page=2&limit=10 returns correct slice",
            "Test soft delete: deleted items excluded from default queries",
            "Validate Swagger at /docs renders without errors"
        ],
        "context_refs": [
            "aidlc-docs/inception/user-stories-with-gherkin.md",
            "aidlc-docs/construction/backend-api-unidad 1/business-logic-model.md",
            "aidlc-docs/construction/backend-api-unidad 1/infrastructure-design.md"
        ],
        "deps": "Domain & Entities",
    },
    "backend-api-unidad-1 → Advanced Features": {
        "milestone": "M3: API & Service Layer",
        "estimate": 8,
        "definition": "Add cross-cutting concerns: audit logging on all mutations, soft delete pattern, standardized pagination, filter parameters, rate limiting (slowapi), and rich request validation via Pydantic custom validators.",
        "ac": [
            "AuditLog table populated on every CREATE/UPDATE/DELETE",
            "GET /audit endpoint (admin-only) with filters by entity/user/date",
            "Pagination: limit (default 20, max 100), offset; consistent envelope",
            "Filters on list endpoints: date range, status, search by name",
            "Rate limit: 100 req/min/user via slowapi middleware",
            "Pydantic validators for business invariants (e.g., reason required on reject)"
        ],
        "test_plan": [
            "Unit test audit_logger emits one row per mutation",
            "Integration test: deleted item is not returned by GET /defects",
            "Test pagination edge cases (offset > total, limit = 0)",
            "Load test: 110 rps → see 429 responses",
            "Test invalid input returns descriptive 400 with field-level errors"
        ],
        "context_refs": [
            "aidlc-docs/construction/backend-api-unidad 1/nfr-requirements-elicited.md",
            "aidlc-docs/construction/backend-api-unidad 1/nfr-design.md"
        ],
        "deps": "Core APIs",
    },
    "backend-api-unidad-1 → Testing & Documentation": {
        "milestone": "M6: Testing & Quality",
        "estimate": 8,
        "definition": "Build full test pyramid: unit tests for services/validators, integration tests against real PostgreSQL (testcontainers), performance baseline tests with locust, and OpenAPI documentation enriched with descriptions and examples.",
        "ac": [
            "Unit test coverage ≥ 85% on app/domain and app/application",
            "Integration tests cover full happy-path for each module",
            "Locust load test scenario: 100 rps sustained for 5min, p95 < 500ms",
            "Swagger /docs has descriptions + examples for all endpoints",
            "README has quickstart, endpoint reference, and deployment guide"
        ],
        "test_plan": [
            "Run `make test` → coverage ≥ 80% (combined), CI gate enforces",
            "Run `make test-integration` → all integration tests green",
            "Run `locust -f tests/perf/locustfile.py` → p95 < 500ms",
            "Manually browse /docs → verify examples render"
        ],
        "context_refs": [
            "aidlc-docs/construction/backend-api-unidad 1/build-and-test/unit-test-instructions.md",
            "aidlc-docs/construction/backend-api-unidad 1/build-and-test/integration-test-instructions.md"
        ],
        "deps": "Advanced Features",
    },
    "backend-api-unidad-1 → Deployment": {
        "milestone": "M7: Deployment & Infrastructure",
        "estimate": 5,
        "definition": "Containerize the backend with multi-stage Dockerfile, deploy to AWS Lambda (or ECS) via IaC, configure RDS PostgreSQL, manage env vars via Secrets Manager, and validate with smoke tests in staging.",
        "ac": [
            "Dockerfile multi-stage (builder + slim runtime), image < 200MB",
            "Image pushed to ECR with semantic version tag",
            "Lambda function deployed via Terraform/CDK with correct IAM role",
            "RDS PostgreSQL provisioned, migrations applied",
            "Secrets in AWS Secrets Manager (DB_URL, JWT_SECRET); no plaintext in env",
            "Smoke tests pass against staging URL"
        ],
        "test_plan": [
            "Build image locally → `docker run` exposes /health returning 200",
            "Deploy to staging → curl /health from public URL returns 200",
            "Run smoke suite (5 critical endpoints) → all 2xx",
            "Verify CloudWatch logs show structured JSON"
        ],
        "context_refs": [
            "aidlc-docs/construction/backend-api-unidad 1/deployment-architecture.md",
            "aidlc-docs/construction/backend-api-unidad 1/infrastructure-design.md"
        ],
        "deps": "Testing & Documentation",
    },

    # ============= UNIT 3: MAESTROS (6 tasks) =============
    "maestroyconfiguracion-unidad3 → Database Setup": {
        "milestone": "M2: Domain & Data Layer",
        "estimate": 3,
        "definition": "Create PostgreSQL tables for defects, machines, fabrics, import_logs, and change_logs with appropriate indices (unique on name+code), FK constraints, and Alembic versioned migrations.",
        "ac": [
            "5 tables created with correct columns and types",
            "Unique compound index on (tenant_id, code) for each master table",
            "Soft-delete column (deleted_at) on all masters",
            "Migration reversible via `alembic downgrade -1`",
            "Seed data SQL script for initial defect/machine/fabric types"
        ],
        "test_plan": [
            "`alembic upgrade head` succeeds on empty DB",
            "`alembic downgrade -1` rolls back without data loss for existing rows",
            "Insert duplicate code → unique constraint violation as expected",
            "Run seed script → tables populated"
        ],
        "context_refs": [
            "aidlc-docs/construction/Maestroyconfiguracion-unidad3/domain-entities.md",
            "aidlc-docs/construction/Maestroyconfiguracion-unidad3/Business-Logic-Model.md"
        ],
        "deps": "Backend Setup Infrastructure",
    },
    "maestroyconfiguracion-unidad3 → Backend APIs": {
        "milestone": "M3: API & Service Layer",
        "estimate": 8,
        "definition": "Implement CRUD endpoints for the 3 master entities (defects, machines, fabrics) with validation, soft delete, audit logging, and tenant-scoped queries.",
        "ac": [
            "GET /defects (paginated, searchable), POST, PUT, DELETE (soft)",
            "Same pattern for /machines and /fabrics",
            "Uniqueness validated server-side: 409 on duplicate (tenant_id, code)",
            "Audit log entry on every mutation",
            "All endpoints scoped to caller's tenant_id from JWT"
        ],
        "test_plan": [
            "Unit test service layer with mocked repository",
            "Integration test: create defect → list → update → soft delete → list excludes",
            "Test cross-tenant isolation: tenant A cannot see tenant B's masters",
            "Test 409 on duplicate code"
        ],
        "context_refs": [
            "aidlc-docs/construction/Maestroyconfiguracion-unidad3/Business-Rules.md",
            "aidlc-docs/construction/Maestroyconfiguracion-unidad3/NFR-Requirements.md"
        ],
        "deps": "Database Setup, Backend Core APIs",
    },
    "maestroyconfiguracion-unidad3 → Bulk Import": {
        "milestone": "M3: API & Service Layer",
        "estimate": 8,
        "definition": "Build CSV/Excel bulk import with preview, server-side validation, Celery-driven async processing for large files (>1MB), and detailed result reporting (success/error per row).",
        "ac": [
            "POST /import/defects accepts CSV or XLSX (multipart/form-data)",
            "Files > 1MB queued as Celery task; returns 202 + task_id",
            "Per-row validation; failed rows included in result report",
            "Atomic mode (all-or-nothing) and best-effort mode supported",
            "Same pattern for /import/machines and /import/fabrics"
        ],
        "test_plan": [
            "Import 10k-row CSV → completes < 30s",
            "Import file with 5 invalid rows → response shows 5 errors with row numbers",
            "Test atomic mode: 1 bad row → 0 rows inserted",
            "Test rollback on critical DB error mid-import"
        ],
        "context_refs": [
            "aidlc-docs/construction/Maestroyconfiguracion-unidad3/Infrastructure-Design-Services.md",
            "aidlc-docs/construction/Maestroyconfiguracion-unidad3/NFR-Design-Consolidated.md"
        ],
        "deps": "Backend APIs",
    },
    "maestroyconfiguracion-unidad3 → Frontend UI": {
        "milestone": "M4: UI Components & Pages",
        "estimate": 8,
        "definition": "Build React pages for managing the 3 masters: searchable/paginated tables, create/edit modals with form validation, delete confirmations, and toast notifications on success/error.",
        "ac": [
            "MastersPage with tabs for Defects/Machines/Fabrics",
            "Table with sort, filter, paginate (using TanStack Table)",
            "Create/Edit modal with Zod schema validation",
            "Delete confirmation modal (cannot accidentally delete)",
            "Toast feedback on every API success/error"
        ],
        "test_plan": [
            "Component test (React Testing Library) for table interactions",
            "Form validation test: submit invalid → see field errors",
            "Mock API test: POST returns 201 → table refreshes",
            "Manual a11y test: keyboard navigation reaches all controls"
        ],
        "context_refs": [
            "aidlc-docs/construction/Maestroyconfiguracion-unidad3/Business-Rules.md",
            "docs/tasks/002-maestros-wave1.md (Phase 4)"
        ],
        "deps": "Backend APIs, Frontend Setup & Architecture",
    },
    "maestroyconfiguracion-unidad3 → Import UI": {
        "milestone": "M4: UI Components & Pages",
        "estimate": 5,
        "definition": "Implement file upload UI with drag-and-drop, preview of first 10 rows with inline validation errors, progress bar for async imports, and downloadable result report.",
        "ac": [
            "Drag-and-drop or click-to-upload accepts .csv/.xlsx",
            "Preview shows first 10 rows; invalid cells highlighted red",
            "Progress bar polls task_id every 2s for async imports",
            "Result page shows totals (success, failed) + download error CSV"
        ],
        "test_plan": [
            "Drag CSV → preview renders",
            "Drag invalid file type → error shown, upload blocked",
            "Mock async import → progress bar reaches 100%, result rendered",
            "Click 'Download errors' → CSV downloads with bad rows"
        ],
        "context_refs": [
            "aidlc-docs/construction/Maestroyconfiguracion-unidad3/Business-Logic-Model.md"
        ],
        "deps": "Frontend UI, Bulk Import",
    },
    "maestroyconfiguracion-unidad3 → Testing & Documentation": {
        "milestone": "M6: Testing & Quality",
        "estimate": 5,
        "definition": "Add unit tests (service + UI), integration tests (full import pipeline), admin user guide, and API reference docs for the masters module.",
        "ac": [
            "Backend coverage ≥ 80% on services + repositories",
            "Frontend coverage ≥ 75% on components",
            "End-to-end test: upload CSV → see imported rows in table",
            "Admin guide doc in docs/admin-guide-masters.md",
            "API reference auto-generated and reviewed"
        ],
        "test_plan": [
            "Run `make test` → coverage gates pass",
            "Run Cypress e2e: upload → import → verify",
            "Peer review of admin guide for clarity"
        ],
        "context_refs": [
            "aidlc-docs/construction/Maestroyconfiguracion-unidad3/activity-6-testing-design/Testing-Strategy-Design.md"
        ],
        "deps": "Frontend UI, Import UI",
    },

    # ============= UNIT 2: FRONTEND WAVE 1 (6 tasks) =============
    "frontend-web-unidad-2-wave1 → Setup & Architecture": {
        "milestone": "M1: Bootstrap & Setup",
        "estimate": 5,
        "definition": "Scaffold Vite + React 18 + TypeScript app with Zustand stores, Tailwind CSS, React Router, axios API client with interceptors, and base UI component library (Button, Input, Modal, Card).",
        "ac": [
            "Vite project boots without warnings (TS strict mode on)",
            "5 Zustand stores: authStore, inspectionStore, approvalStore, masterStore, offlineStore",
            "Tailwind config has design tokens (colors, spacing)",
            "Router: /, /login, /inspections, /approvals, /masters with protection",
            "API client auto-attaches JWT, refreshes on 401, retries idempotent calls"
        ],
        "test_plan": [
            "`npm run dev` boots in < 3s, opens at localhost:5173",
            "`npm run build` produces dist/ < 1MB gzipped",
            "Test store: dispatch action → state updates as expected",
            "Test API client: 401 → refresh → retry original request"
        ],
        "context_refs": [
            "aidlc-docs/construction/frontend-web unidad 2/frontend-web/nfr-design/ADR-002-state-management-zustand.md",
            "docs/tasks/003-frontend-wave1.md (Phase 1)"
        ],
        "deps": "None (foundational task)",
    },
    "frontend-web-unidad-2-wave1 → Authentication & Layout": {
        "milestone": "M4: UI Components & Pages",
        "estimate": 5,
        "definition": "Build login page, JWT token storage (httpOnly cookie or secure localStorage), protected routes, role-based UI gating, and main app shell (sidebar + header + content area).",
        "ac": [
            "Login form with email + password, validation, error display",
            "Successful login stores token, navigates to /",
            "Protected routes redirect unauthenticated → /login",
            "Sidebar shows only links allowed by user's role",
            "Logout clears token and routes to /login"
        ],
        "test_plan": [
            "Cypress: type credentials → submit → land on dashboard",
            "Cypress: navigate to /admin as RECRUITER → redirect to /",
            "Unit test: useAuth hook returns null when no token",
            "Test 401 from any API → auto-logout + redirect"
        ],
        "context_refs": [
            "aidlc-docs/construction/frontend-web unidad 2/frontend-web/nfr-design/ADR-001-authentication-jwt-strategy.md",
            "aidlc-docs/construction/frontend-web unidad 2/frontend-business-rules.md"
        ],
        "deps": "Setup & Architecture, Backend Core APIs",
    },
    "frontend-web-unidad-2-wave1 → Inspection Module": {
        "milestone": "M4: UI Components & Pages",
        "estimate": 13,
        "definition": "Build the Inspection capture flow: lot lookup, mobile camera photo capture (with client-side compression), defect dropdown, machine selection, mandatory comment, save+history list.",
        "ac": [
            "POST /inspections invoked from form submit",
            "Photo captured via getUserMedia or file input fallback",
            "Image compressed client-side to < 500KB before upload",
            "Form validates: lot+defect+machine+comment+photo required",
            "Inspection list view with pagination + filters",
            "Detail view with fullscreen photo viewer"
        ],
        "test_plan": [
            "Cypress: complete capture flow → see new inspection in list",
            "Test compression: upload 5MB photo → POST body < 500KB",
            "Test validation: submit empty → see error messages",
            "Manual mobile test: iPhone Safari + Android Chrome"
        ],
        "context_refs": [
            "aidlc-docs/construction/frontend-web unidad 2/frontend-business-logic-model.md",
            "aidlc-docs/inception/user-stories-with-gherkin.md (INS-001..INS-008)"
        ],
        "deps": "Authentication & Layout",
    },
    "frontend-web-unidad-2-wave1 → Approval Module": {
        "milestone": "M4: UI Components & Pages",
        "estimate": 8,
        "definition": "Build the approval queue for QA leads: list of pending inspections, detail view with fullscreen photo, approve/reject actions with mandatory rejection reason, real-time count via polling.",
        "ac": [
            "List shows pending only (status=pending) with most recent first",
            "Detail view displays photo, defect, machine, comments, history",
            "Approve button → confirmation → POST /approvals/{id}/approve",
            "Reject requires reason textarea (min 10 chars) → POST .../reject",
            "Badge in sidebar shows pending count, polls every 30s"
        ],
        "test_plan": [
            "Cypress: approve flow end-to-end (login QA → approve → status changes)",
            "Test: reject without reason → submit disabled",
            "Test polling: open in 2 tabs → badge updates after action",
            "Visual regression: photo fullscreen preserves aspect ratio"
        ],
        "context_refs": [
            "aidlc-docs/construction/frontend-web unidad 2/frontend-business-rules.md",
            "aidlc-docs/inception/user-stories-with-gherkin.md (APR-001..APR-005)"
        ],
        "deps": "Authentication & Layout, Backend Core APIs",
    },
    "frontend-web-unidad-2-wave1 → Masters Module": {
        "milestone": "M4: UI Components & Pages",
        "estimate": 8,
        "definition": "Frontend Masters management — same UI patterns as Unit 3 Frontend UI but integrated within Wave 1 frontend scope (tables, forms, validations, soft-delete UX).",
        "ac": [
            "Page at /admin/masters with sub-routes per master entity",
            "Reuses MasterForm, MasterTable components from Unit 3",
            "Admin-only route guard",
            "Confirmation dialogs on delete actions",
            "Loading states + skeleton screens"
        ],
        "test_plan": [
            "Cypress: ADMIN → /admin/masters → create defect → see in table",
            "Cypress: RECRUITER → /admin/masters → redirected",
            "Test loading state: throttle network → see skeleton"
        ],
        "context_refs": [
            "aidlc-docs/construction/Maestroyconfiguracion-unidad3/domain-entities.md",
            "docs/tasks/003-frontend-wave1.md (Phase 5)"
        ],
        "deps": "Authentication & Layout, Maestros Backend APIs",
    },
    "frontend-web-unidad-2-wave1 → Testing & Polish": {
        "milestone": "M6: Testing & Quality",
        "estimate": 13,
        "definition": "Add unit tests, integration tests with mocked API, Cypress E2E for critical paths, accessibility audit (axe), performance optimization (code split, lazy load), and full mobile responsive sweep.",
        "ac": [
            "Test coverage ≥ 75% (statements + branches)",
            "E2E suite covers: login → inspection → approval → masters",
            "Axe accessibility audit: 0 critical/serious issues",
            "Lighthouse: Performance ≥ 80, A11y ≥ 90 (mobile)",
            "Mobile responsive: tested on 320px, 768px, 1024px, 1440px",
            "Zero console errors on full app walkthrough"
        ],
        "test_plan": [
            "`npm test -- --coverage` → coverage gates pass",
            "`npm run e2e` → all Cypress tests green",
            "Run axe-core in CI → 0 violations of severity >= serious",
            "Run Lighthouse CLI in CI → scores above gates"
        ],
        "context_refs": [
            "aidlc-docs/construction/frontend-web unidad 2/activity-6-testing-design/Testing-Strategy-Design.md",
            "aidlc-docs/construction/frontend-web unidad 2/activity-6-testing-design/Test-Implementation-Roadmap.md"
        ],
        "deps": "Inspection Module, Approval Module, Masters Module",
    },

    # ============= UNIT 2: FRONTEND WAVE 2 (4 tasks) =============
    "frontend-web-unidad-2-wave2 → Analysis Module": {
        "milestone": "M4: UI Components & Pages",
        "estimate": 13,
        "definition": "Build analytics dashboard with key metric cards, charts (bar by machine, pie by defect, pie by fabric), date range picker, and WebSocket-driven real-time updates.",
        "ac": [
            "4 metric cards: total today/week/month, top defect",
            "3 charts using Recharts (responsive containers)",
            "Date range picker affects all charts simultaneously",
            "WebSocket /ws/analytics pushes updates; UI refreshes < 1s",
            "Empty state when no data in selected range"
        ],
        "test_plan": [
            "Mock analytics API → all charts render correctly",
            "Change date range → charts refetch and update",
            "Mock WS message → metric cards update without reload",
            "Test empty state: range with 0 data → friendly message"
        ],
        "context_refs": [
            "aidlc-docs/construction/frontend-web unidad 2/NFR-Design-Consolidated.md",
            "docs/tasks/004-frontend-wave2.md (Phase 1)"
        ],
        "deps": "Frontend Wave 1 Testing & Polish",
    },
    "frontend-web-unidad-2-wave2 → Reports & Export": {
        "milestone": "M4: UI Components & Pages",
        "estimate": 13,
        "definition": "Build report builder with type/metric/date selection, PDF and Excel server-side generation, download manager with retry, and optional scheduled report creation.",
        "ac": [
            "Report builder UI selects type (Executive/Detailed), metrics, range",
            "POST /reports/export/pdf returns presigned download URL",
            "POST /reports/export/excel same pattern",
            "Multi-sheet Excel: summary, details, charts (as images)",
            "Download progress shown; retry on timeout"
        ],
        "test_plan": [
            "Generate PDF → opens in viewer with charts rendered",
            "Generate Excel → 3 sheets present with correct data",
            "Test download retry: throttle network → eventually succeeds",
            "Test large report (1 year of data) → completes < 30s"
        ],
        "context_refs": [
            "aidlc-docs/construction/frontend-web unidad 2/activity-4-infrastructure-design/Infrastructure-Design.md"
        ],
        "deps": "Analysis Module",
    },
    "frontend-web-unidad-2-wave2 → Advanced Features": {
        "milestone": "M4: UI Components & Pages",
        "estimate": 8,
        "definition": "Implement full-text search across inspections + comments, advanced multi-filter sidebar, saved-search persistence per user, and result detail page with sortable columns.",
        "ac": [
            "Debounced search input (300ms) hits POST /search",
            "Filter sidebar: machine, defect, fabric, status, date",
            "Saved searches stored in user preferences (backend)",
            "Results table sortable by any column",
            "Shareable URL with query params reflects current state"
        ],
        "test_plan": [
            "Type 'lot123' → results appear in < 500ms",
            "Apply 3 filters → URL updates → reload preserves state",
            "Save search 'Open issues this week' → reload page → search appears in dropdown"
        ],
        "context_refs": [
            "docs/tasks/004-frontend-wave2.md (Phase 3)"
        ],
        "deps": "Reports & Export",
    },
    "frontend-web-unidad-2-wave2 → Offline Preparation": {
        "milestone": "M5: Integration & State",
        "estimate": 5,
        "definition": "Lay foundation for Unit 4 offline work: register Service Worker, scaffold IndexedDB schema, define sync queue interface, create offline indicator component.",
        "ac": [
            "Service Worker registered, lifecycle managed (skipWaiting)",
            "IndexedDB schema v1 created with object stores",
            "OfflineIndicator component shows online/offline status",
            "Type definitions for sync queue events ready"
        ],
        "test_plan": [
            "DevTools → Application → Service Worker active",
            "Toggle network offline → indicator turns red",
            "IndexedDB inspector shows expected stores",
            "Test SW update flow: deploy new version → user prompted"
        ],
        "context_refs": [
            "aidlc-docs/construction/frontend-web unidad 2/frontend-web/nfr-design/ADR-003-offline-storage-indexeddb-service-worker.md"
        ],
        "deps": "Advanced Features",
    },

    # ============= UNIT 4: OFFLINE WAVE 2 (6 tasks) =============
    "offline-first-unidad-4-wave2 → Service Worker & Offline Detection": {
        "milestone": "M5: Integration & State",
        "estimate": 8,
        "definition": "Implement production Service Worker with network-first API caching, cache-first asset caching, stale-while-revalidate for non-critical data, and reliable online/offline detection.",
        "ac": [
            "SW registered in production build",
            "API requests use network-first with 5s timeout → cache fallback",
            "Static assets cached with versioned URLs",
            "Network detection works on iOS Safari (custom heartbeat)",
            "Offline page served when navigating offline"
        ],
        "test_plan": [
            "DevTools throttle Offline → app still navigates between cached pages",
            "Bring online → next API call hits network",
            "Test on iOS Safari real device (event reliability)",
            "Lighthouse PWA audit ≥ 90"
        ],
        "context_refs": [
            "aidlc-docs/construction/offline-first&synchronization-unidad 4/NFR-Design-Consolidated.md",
            "docs/tasks/005-offline-sync-wave2.md (Phase 1)"
        ],
        "deps": "Frontend Offline Preparation",
    },
    "offline-first-unidad-4-wave2 → IndexedDB Setup": {
        "milestone": "M5: Integration & State",
        "estimate": 5,
        "definition": "Build typed IndexedDB client using idb library: schema versioning, migrations, CRUD wrappers, indices on common query keys, and Zustand store persistence layer.",
        "ac": [
            "idb client with TypeScript generics for object stores",
            "Schema v1 + upgrade path for v2 (migration runner)",
            "CRUD methods async with proper error handling",
            "Zustand stores persist via subscribe → IDB writes",
            "Composite indices for offline list queries"
        ],
        "test_plan": [
            "Unit test CRUD: put → get → update → delete",
            "Test migration: open v1 DB, upgrade to v2, data intact",
            "Test reload: state recovered from IDB",
            "Test storage quota: handle QuotaExceededError gracefully"
        ],
        "context_refs": [
            "aidlc-docs/construction/offline-first&synchronization-unidad 4/Business-Logic-Model.md",
            "aidlc-docs/construction/offline-first&synchronization-unidad 4/domain-entities.md"
        ],
        "deps": "Service Worker & Offline Detection",
    },
    "offline-first-unidad-4-wave2 → Offline Data Capture": {
        "milestone": "M5: Integration & State",
        "estimate": 8,
        "definition": "Allow inspection creation while offline: write to IndexedDB, store photos as Blobs, validate locally, surface 'pending sync' UI indicators, handle storage quota errors.",
        "ac": [
            "Form submit offline → row saved to inspections store with status=pending",
            "Photo Blob stored as separate IDB entry (size optimized)",
            "Local validation matches server rules (DRY: share Zod schema)",
            "Badge on inspection list shows pending count",
            "Form recovery: app crash mid-typing → restored on reload"
        ],
        "test_plan": [
            "Offline + submit → verify row in IDB with correct shape",
            "Throw mid-submit (simulated crash) → restore form on reload",
            "Fill storage quota → see friendly warning, save blocked",
            "Bring online → row appears in sync queue"
        ],
        "context_refs": [
            "aidlc-docs/construction/offline-first&synchronization-unidad 4/Business-Rules.md"
        ],
        "deps": "IndexedDB Setup",
    },
    "offline-first-unidad-4-wave2 → Sync Queue & Mechanism": {
        "milestone": "M5: Integration & State",
        "estimate": 13,
        "definition": "Build sync queue with exponential backoff retries, batch posting to /sync, server-side merge service, and progress reporting back to UI.",
        "ac": [
            "Queue entry: {op, payload, timestamp, attempts, status}",
            "Auto-trigger sync on network reconnect",
            "Exponential backoff: 1s, 2s, 4s, 8s, 16s (max 5 attempts)",
            "POST /sync accepts batch up to 100 items",
            "Result per item: success/failure/conflict",
            "UI updates: progress bar, per-item status"
        ],
        "test_plan": [
            "Capture offline → reconnect → queue drains automatically",
            "Server returns 500 → retries with backoff → eventually marks failed",
            "Test batch of 100 → server processes in < 5s",
            "Test sync during user activity → no blocking of UI"
        ],
        "context_refs": [
            "aidlc-docs/construction/offline-first&synchronization-unidad 4/Infrastructure-Design-Services.md"
        ],
        "deps": "Offline Data Capture",
    },
    "offline-first-unidad-4-wave2 → Conflict Detection": {
        "milestone": "M5: Integration & State",
        "estimate": 8,
        "definition": "Implement last-write-wins conflict detection with version vectors. Mark conflicts for later manual resolution (Wave 3). Provide audit trail of conflicts.",
        "ac": [
            "Each entity has version field incremented on write",
            "Server compares client version vs current; flags mismatch",
            "Conflicted items stored in conflicts collection",
            "Sync result includes conflict count + IDs",
            "Audit log entry per conflict"
        ],
        "test_plan": [
            "User A updates lot X offline; user B updates same lot online; A reconnects → conflict logged",
            "Test version monotonicity: 10 sequential updates → versions 1..10",
            "Test conflict view: GET /conflicts returns flagged items"
        ],
        "context_refs": [
            "aidlc-docs/construction/offline-first&synchronization-unidad 4/Business-Rules.md"
        ],
        "deps": "Sync Queue & Mechanism",
    },
    "offline-first-unidad-4-wave2 → Testing & Documentation": {
        "milestone": "M6: Testing & Quality",
        "estimate": 5,
        "definition": "Add unit tests for sync logic, integration tests covering offline→online transitions, E2E with Playwright, performance baselines (battery, bandwidth), and architecture documentation.",
        "ac": [
            "Coverage ≥ 75% on sync + queue + IDB modules",
            "Playwright E2E: capture offline 10 items → reconnect → all sync",
            "Battery drain test: 1h offline standby < 5%",
            "Sync architecture doc with sequence diagrams"
        ],
        "test_plan": [
            "Run vitest → coverage gate enforced",
            "Run Playwright in headed mode → manual verification",
            "Battery: real device test over 1h",
            "Peer-review architecture doc"
        ],
        "context_refs": [
            "aidlc-docs/construction/offline-first&synchronization-unidad 4/activity-6-testing-design/testing-design.md"
        ],
        "deps": "Conflict Detection",
    },

    # ============= UNIT 4: OFFLINE WAVE 3 (4 tasks) =============
    "offline-first-unidad-4-wave3 → Conflict Resolution UI": {
        "milestone": "M5: Integration & State",
        "estimate": 13,
        "definition": "Build manual conflict resolution UI: list of conflicted items, side-by-side diff view, merge strategies (keep mine/theirs/manual field merge), batch resolution, audit trail.",
        "ac": [
            "/conflicts page lists all unresolved conflicts",
            "Detail view shows local vs server side-by-side with diff highlighting",
            "Per-field selectable merge for custom resolution",
            "Batch select + apply same strategy",
            "Resolution history visible per entity"
        ],
        "test_plan": [
            "Create 3 conflicts → /conflicts shows all 3",
            "Choose 'keep mine' → server accepts, conflict cleared",
            "Field-by-field merge → final state matches selection",
            "Audit log shows who resolved what when"
        ],
        "context_refs": [
            "docs/tasks/006-offline-sync-wave3.md (Phase 1)"
        ],
        "deps": "Offline Wave 2 Testing & Documentation",
    },
    "offline-first-unidad-4-wave3 → Bidirectional Sync": {
        "milestone": "M5: Integration & State",
        "estimate": 13,
        "definition": "Add server→client sync via WebSocket: real-time push of changes, selective sync by entity type/date, automatic reconnection with backoff, conflict detection on incoming updates.",
        "ac": [
            "WS /ws/sync authenticated by JWT",
            "Server pushes changes since last_sync_at",
            "Client applies non-conflicting changes silently",
            "Conflicts surface notification to user",
            "Reconnect on disconnect with exponential backoff"
        ],
        "test_plan": [
            "User A makes change → user B sees it < 2s",
            "Disconnect WS → reconnect happens automatically",
            "Test conflict path: simultaneous edits → conflict shown",
            "Load test: 1000 connected clients → server stable"
        ],
        "context_refs": [
            "aidlc-docs/construction/offline-first&synchronization-unidad 4/Infrastructure-Design-Services.md"
        ],
        "deps": "Conflict Resolution UI",
    },
    "offline-first-unidad-4-wave3 → Performance & Optimization": {
        "milestone": "M5: Integration & State",
        "estimate": 8,
        "definition": "Optimize sync performance: GZIP compression on payloads, differential sync (only changed fields), IndexedDB query indices, memory cleanup, network connection pooling.",
        "ac": [
            "Sync payloads compressed (Content-Encoding: gzip)",
            "Only changed fields sent on update (JSON patch)",
            "Bandwidth reduced ≥ 40% vs Wave 2 baseline",
            "Memory footprint stable over 24h offline session",
            "p95 sync latency < 2s for 10-item batches"
        ],
        "test_plan": [
            "Measure payload size before/after compression",
            "Run 24h soak test → no memory growth",
            "Measure p95 latency on production-like network",
            "Compare bandwidth before/after via DevTools"
        ],
        "context_refs": [
            "aidlc-docs/construction/offline-first&synchronization-unidad 4/NFR-Design-Consolidated.md"
        ],
        "deps": "Bidirectional Sync",
    },
    "offline-first-unidad-4-wave3 → Monitoring & Polish": {
        "milestone": "M7: Deployment & Infrastructure",
        "estimate": 5,
        "definition": "Add observability: sync success/failure metrics to CloudWatch, error tracking via Sentry, user-reported issue mechanism, alerts on sync failure spikes, final UX polish.",
        "ac": [
            "Custom CloudWatch metrics: sync_success, sync_failure, conflict_count",
            "Sentry captures unhandled errors with user context",
            "In-app 'Report a problem' form → ticket created",
            "CloudWatch alarm: failure rate > 5% in 5min → SNS notification",
            "Final UX pass: animations, microcopy, loading states polished"
        ],
        "test_plan": [
            "Generate sync failures → metrics visible in CW dashboard",
            "Throw test error → see in Sentry within 30s",
            "Submit problem report → ticket appears in queue",
            "Trigger alarm → SNS notification received"
        ],
        "context_refs": [
            "aidlc-docs/construction/frontend-web unidad 2/frontend-web/nfr-design/ADR-004-monitoring-error-tracking.md"
        ],
        "deps": "Performance & Optimization",
    },
}


def build_description(title, data):
    """Build OpenSymphony-contract description"""
    ac_lines = "\n".join(f"- [ ] {ac}" for ac in data["ac"])
    tp_lines = "\n".join(f"- {step}" for step in data["test_plan"])
    ctx_lines = "\n".join(f"- `{ref}`" for ref in data["context_refs"])

    return f"""## Definition

{data['definition']}

## Acceptance Criteria

{ac_lines}

## Test Plan

{tp_lines}

## Context References

{ctx_lines}

## Dependencies

**Depends on**: {data['deps']}

## Milestone

**{data['milestone']}**

---
*OpenSymphony contract — generated from `docs/tasks/task-package.yaml`*
"""


def fetch_issues_for_project(project_id):
    """Fetch all issues in a project"""
    print(f"\nFetching issues for project {project_id}...")
    query = """
    query($projectId: String!) {
        project(id: $projectId) {
            issues(first: 100) {
                nodes {
                    id
                    identifier
                    title
                    description
                }
            }
        }
    }
    """
    result = graphql_query(query, {"projectId": project_id})
    if result and result.get("project"):
        return result["project"]["issues"]["nodes"]
    return []


def update_issue(issue_id, title, description, estimate):
    """Update issue description and estimate"""
    mutation = """
    mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
        issueUpdate(id: $id, input: $input) {
            success
            issue { id title }
        }
    }
    """
    variables = {
        "id": issue_id,
        "input": {
            "description": description,
            "estimate": estimate,
        }
    }
    result = graphql_query(mutation, variables)
    return result and result.get("issueUpdate", {}).get("success", False)


def main():
    print("=" * 70)
    print("OpenSymphony Contract Compliance — Linear Issue Update")
    print("=" * 70)

    # Fetch existing issues
    issues = fetch_issues_for_project(PROJECT_ID)
    if not issues:
        print("ERROR: Could not fetch issues")
        return False

    print(f"Found {len(issues)} issues to update\n")

    updated = 0
    skipped = 0
    failed = 0

    for issue in issues:
        title = issue["title"]
        issue_id = issue["id"]
        identifier = issue["identifier"]

        if title not in TASKS:
            print(f"  - {identifier}: SKIP (no task definition)  [{title}]")
            skipped += 1
            continue

        data = TASKS[title]
        description = build_description(title, data)
        estimate = data["estimate"]

        if update_issue(issue_id, title, description, estimate):
            print(f"  + {identifier}: UPDATED  [{data['milestone']}]")
            updated += 1
        else:
            print(f"  x {identifier}: FAILED  [{title}]")
            failed += 1

    print("\n" + "=" * 70)
    print(f"Done. Updated: {updated} | Skipped: {skipped} | Failed: {failed}")
    print("=" * 70)
    return failed == 0


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nCancelled")
        sys.exit(1)
