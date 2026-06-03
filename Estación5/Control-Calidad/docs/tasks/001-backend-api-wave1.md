# Backend API — Wave 1

**Unit**: backend-api-unidad-1  
**Wave**: Wave 1 (MVP Foundation)  
**Duration**: 30 days (2026-06-01 to 2026-06-30)  
**Story Points**: 200  
**Team**: 2 developers  
**Priority**: CRITICAL  
**Status**: Not Started

---

## 📋 Overview

Build the foundational REST API for the Quality Control platform. This unit provides the backend services for Inspection, Approval, and Masters modules.

### Key Deliverables
- 15+ REST endpoints (Auth, Inspection, Approval, Masters CRUD)
- PostgreSQL database with migrations
- JWT authentication with role-based access
- Audit logging for all operations
- Comprehensive test suite (>80% coverage)
- Production-ready deployment

---

## 🎯 Acceptance Criteria (Unit-Level)

- [ ] All APIs documented in Swagger/OpenAPI
- [ ] Test coverage ≥ 80% (unit + integration)
- [ ] Response time < 500ms (p95) for all endpoints
- [ ] Database migrations are reversible
- [ ] Security audit passed (OWASP Top 10)
- [ ] Performance: Handle 100 req/s sustained
- [ ] Successfully deployed to AWS staging
- [ ] Runbook documentation complete

---

## 📊 Phase Breakdown

### Phase 1: Setup Infrastructure (Days 1-2)
**Story Points**: 20  
**Assignee**: Backend Lead

#### Tasks
- [ ] Initialize FastAPI project with poetry
  - [ ] Create pyproject.toml with core dependencies
  - [ ] Setup virtual environment
  - [ ] Configure development environment
  - Estimate: 3 SP
  
- [ ] Setup PostgreSQL & database migrations
  - [ ] Create PostgreSQL instance (local/cloud)
  - [ ] Initialize Alembic for migrations
  - [ ] Test migration system
  - Estimate: 5 SP
  
- [ ] Configure project structure
  - [ ] Create domain/, routes/, schemas/, repositories/, services/
  - [ ] Setup __init__.py files
  - [ ] Create config.py and settings.py
  - Estimate: 3 SP
  
- [ ] Setup CI/CD pipeline
  - [ ] Create GitHub Actions workflow
  - [ ] Configure linting (flake8, black)
  - [ ] Setup automated tests
  - Estimate: 5 SP
  
- [ ] Create base documentation
  - [ ] README with setup instructions
  - [ ] CONTRIBUTING guidelines
  - Estimate: 4 SP

**Acceptance Criteria**
- [ ] Project runs locally without errors
- [ ] Database connections work
- [ ] CI/CD pipeline triggers on push
- [ ] Team can clone and setup in < 10 minutes

---

### Phase 2: Domain & Entities (Days 3-5)
**Story Points**: 35  
**Assignee**: Backend Lead

#### Tasks
- [ ] Define domain entities (DDD)
  - [ ] User (with roles: Admin, QA, Manager, Analyst)
  - [ ] Inspection (lot, defects, photo, comments)
  - [ ] Approval (inspection approval, rejection)
  - [ ] Master entities (Defect types, Machines, Fabrics)
  - Estimate: 8 SP
  
- [ ] Create value objects
  - [ ] DefectType (id, name, description)
  - [ ] MachineStatus (operational, broken, maintenance)
  - [ ] Photo (url, timestamp, size)
  - Estimate: 5 SP
  
- [ ] Define business rules
  - [ ] An inspection requires: lot_id, defects[], machine, comments, photo
  - [ ] Approval requires: inspection_id, approver_id, status (approved/rejected)
  - [ ] Masters can only be soft-deleted (marked inactive)
  - Estimate: 5 SP
  
- [ ] Create SQLAlchemy ORM models
  - [ ] Map entities to tables
  - [ ] Define relationships (1:N, N:M)
  - [ ] Add indices on frequently queried fields
  - Estimate: 10 SP
  
- [ ] Create initial migration
  - [ ] `alembic revision --autogenerate -m "Initial schema"`
  - [ ] Test migration up/down
  - Estimate: 7 SP

**Acceptance Criteria**
- [ ] All entity diagrams in documentation
- [ ] SQLAlchemy models match entities
- [ ] Migration is reversible
- [ ] No raw SQL in application code

---

### Phase 3: Core APIs (Days 6-15)
**Story Points**: 85  
**Assignee**: Backend Lead + 1 Developer

#### Tasks

##### Auth Module
- [ ] POST /auth/login (email, password)
  - Validate credentials against users table
  - Generate JWT token
  - Return token + user info
  - Estimate: 5 SP
  
- [ ] POST /auth/logout
  - Invalidate token (add to blacklist)
  - Estimate: 2 SP
  
- [ ] POST /auth/refresh
  - Refresh expired token
  - Estimate: 3 SP
  
- [ ] GET /auth/me
  - Return current user info
  - Requires valid JWT
  - Estimate: 2 SP

##### Inspection Module
- [ ] POST /inspections
  - Create new inspection
  - Validate required fields
  - Store photo in S3
  - Estimate: 8 SP
  
- [ ] GET /inspections/{id}
  - Retrieve single inspection
  - Include defect details, photo URL
  - Estimate: 3 SP
  
- [ ] GET /inspections (with pagination)
  - List inspections (current user's)
  - Pagination (limit, offset)
  - Filter by date range
  - Estimate: 5 SP
  
- [ ] PUT /inspections/{id}
  - Update inspection (before approval)
  - Only creator can update
  - Estimate: 4 SP

##### Approval Module
- [ ] GET /approvals/pending
  - List inspections pending approval
  - Filter by QA role
  - Estimate: 4 SP
  
- [ ] GET /approvals/{id}
  - Detailed approval view
  - Include all inspection details
  - Estimate: 3 SP
  
- [ ] POST /approvals/{id}/approve
  - Mark inspection as approved
  - Change status to "approved"
  - Trigger notification
  - Estimate: 4 SP
  
- [ ] POST /approvals/{id}/reject
  - Reject inspection
  - Require rejection reason
  - Estimate: 4 SP

##### Masters Module
- [ ] GET /defects
  - List all defect types (active)
  - Pagination
  - Estimate: 3 SP
  
- [ ] POST /defects
  - Create new defect type
  - Require: name, description
  - Only admin can create
  - Estimate: 3 SP
  
- [ ] PUT /defects/{id}
  - Update defect type
  - Admin only
  - Estimate: 2 SP
  
- [ ] DELETE /defects/{id}
  - Soft delete (mark inactive)
  - Estimate: 2 SP
  
- [ ] GET /machines, POST /machines, PUT /machines/{id}, DELETE /machines/{id}
  - Same CRUD pattern as defects
  - Estimate: 8 SP
  
- [ ] GET /fabrics, POST /fabrics, PUT /fabrics/{id}, DELETE /fabrics/{id}
  - Same CRUD pattern as defects
  - Estimate: 8 SP

**Acceptance Criteria**
- [ ] All endpoints have request/response examples
- [ ] All endpoints require authentication (except /auth/login)
- [ ] Role-based access control working
- [ ] Error responses are consistent
- [ ] Swagger docs auto-generated

---

### Phase 4: Advanced Features (Days 16-20)
**Story Points**: 35  
**Assignee**: Backend Lead

#### Tasks
- [ ] Implement audit logging
  - [ ] Create AuditLog table
  - [ ] Log all CREATE, UPDATE, DELETE operations
  - [ ] Include user_id, timestamp, old_value, new_value
  - [ ] Endpoint: GET /audit (admin only)
  - Estimate: 8 SP
  
- [ ] Add pagination to all list endpoints
  - [ ] Standardize pagination (limit, offset)
  - [ ] Add default limit (20), max limit (100)
  - Estimate: 5 SP
  
- [ ] Implement filtering on list endpoints
  - [ ] Filter inspections by date, machine, status
  - [ ] Filter approvals by date, approver, status
  - Estimate: 8 SP
  
- [ ] Add soft delete support
  - [ ] Add deleted_at column to relevant tables
  - [ ] Queries exclude soft-deleted by default
  - [ ] Endpoint to restore deleted items
  - Estimate: 7 SP
  
- [ ] Implement rate limiting
  - [ ] Rate limit by API key/user
  - [ ] 100 requests/minute per user
  - Estimate: 5 SP
  
- [ ] Add request/response validation
  - [ ] Use Pydantic schemas
  - [ ] Custom validators for business rules
  - Estimate: 7 SP

**Acceptance Criteria**
- [ ] Audit log captures all mutations
- [ ] Soft deletes cannot be queried
- [ ] Rate limiting prevents abuse
- [ ] Validation errors are descriptive

---

### Phase 5: Testing & Documentation (Days 21-28)
**Story Points**: 40  
**Assignee**: Backend Lead + QA

#### Tasks
- [ ] Write unit tests for services
  - [ ] Test inspection service (create, update, get)
  - [ ] Test approval service
  - [ ] Test auth service
  - [ ] Target: > 85% coverage
  - Estimate: 12 SP
  
- [ ] Write integration tests
  - [ ] Test API endpoints with real database
  - [ ] Test auth flow (login → request → logout)
  - [ ] Test approval workflow
  - [ ] Test data validation
  - Estimate: 15 SP
  
- [ ] Write performance tests
  - [ ] Load test: 100 req/s sustained
  - [ ] Query performance: < 500ms (p95)
  - [ ] Database connection pooling
  - Estimate: 8 SP
  
- [ ] Generate Swagger/OpenAPI docs
  - [ ] Auto-generate from FastAPI models
  - [ ] Add description and examples
  - [ ] Test docs are interactive
  - Estimate: 3 SP
  
- [ ] Write API documentation
  - [ ] Create ENDPOINTS.md with all routes
  - [ ] Include request/response examples
  - [ ] Add error codes documentation
  - Estimate: 5 SP
  
- [ ] Create deployment guide
  - [ ] Docker image creation
  - [ ] Environment variables documentation
  - [ ] Database migration instructions
  - Estimate: 5 SP

**Acceptance Criteria**
- [ ] Test coverage ≥ 80%
- [ ] All tests passing (CI/CD green)
- [ ] Swagger docs complete and interactive
- [ ] README has quickstart guide

---

### Phase 6: Deployment (Days 29-30)
**Story Points**: 25  
**Assignee**: DevOps Lead + Backend Lead

#### Tasks
- [ ] Create Docker image
  - [ ] Write Dockerfile with best practices
  - [ ] Test image locally
  - [ ] Push to ECR
  - Estimate: 5 SP
  
- [ ] Setup AWS Lambda + RDS
  - [ ] Configure Lambda function with FastAPI
  - [ ] Setup RDS PostgreSQL instance
  - [ ] Configure VPC and security groups
  - Estimate: 8 SP
  
- [ ] Configure environment variables
  - [ ] DB_URL, JWT_SECRET, AWS credentials
  - [ ] Create .env.example
  - [ ] Document all required variables
  - Estimate: 3 SP
  
- [ ] Run database migrations in staging
  - [ ] Apply Alembic migrations to staging DB
  - [ ] Test migration rollback
  - Estimate: 3 SP
  
- [ ] Perform smoke tests in staging
  - [ ] Test all major endpoints
  - [ ] Verify database connectivity
  - [ ] Check logs for errors
  - Estimate: 3 SP
  
- [ ] Monitor and alerting setup
  - [ ] CloudWatch alarms for errors
  - [ ] Lambda duration monitoring
  - [ ] Database connection pool monitoring
  - Estimate: 3 SP

**Acceptance Criteria**
- [ ] API responds from staging environment
- [ ] Database migrations applied successfully
- [ ] All endpoints returning 200/400 as expected
- [ ] Logs are being captured in CloudWatch
- [ ] No console errors or warnings

---

## 🎯 Success Metrics

| Metric | Target |
|--------|--------|
| Test Coverage | ≥ 80% |
| API Response Time (p95) | < 500ms |
| Load Capacity | 100 req/s sustained |
| Swagger Docs Completeness | 100% |
| Security Audit Score | Pass (0 Critical) |
| Staging Uptime | > 99% |

---

## 🚨 Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| DB schema changes late | High | Lock schema design by Day 5 |
| Performance issues with large datasets | Medium | Add indices early, load test Day 20 |
| Missing authentication on endpoints | High | Use OpenAPI validation, code review |
| Deployment failures | Medium | Test Docker locally, practice migrations |

---

## 📦 Definition of Done

- [ ] All tasks marked complete
- [ ] Code reviewed and merged to main
- [ ] Tests passing (CI/CD green)
- [ ] Documentation complete
- [ ] Deployed to staging successfully
- [ ] Accepted by QA Lead
- [ ] Linear issue marked "Done"

---

## 🔗 Dependencies

- None (this is Wave 1 foundation)

## 👥 Blockers For

- maestroyconfiguracion-unidad3 (backend APIs needed)
- frontend-web-unidad-2-wave1 (backend APIs needed)

---

**Created**: 2026-06-01  
**Last Updated**: 2026-06-01  
**Estimate Confidence**: High
