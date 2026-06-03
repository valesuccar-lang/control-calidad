# Activity 6: Testing Strategy & Design
## Frontend Web Unit

**Date**: 2026-06-01  
**Status**: DESIGN PHASE  
**Context**: Small team (2-3 devs), 10-20 users, critical offline-first data integrity  
**Decision Makers**: QA Lead + Frontend Team

---

## 📋 TESTING PHILOSOPHY

**Core Principles**:
1. **High Confidence, Low Overhead** — Test critical paths thoroughly, don't chase 100% coverage
2. **Offline-First Testing** — Prioritize sync queue, IndexedDB, and conflict resolution
3. **User-Centric** — Test user workflows (login → inspect → approve → sync), not implementation details
4. **Small Team Efficiency** — Automate repetitive tests, minimize manual QA burden
5. **Fast Feedback** — Unit tests < 5s, integration tests < 30s, E2E tests < 2 min

---

## 🎯 TESTING PYRAMID

```
                     🏔️
                  E2E Tests
                 (Critical paths)
                    5-10%
            ━━━━━━━━━━━━━━━━━━
                   🔺
            Integration Tests
          (API, IndexedDB, Sync)
                  20-30%
        ━━━━━━━━━━━━━━━━━━━━━━━━━
                   🔸
              Unit Tests
         (Stores, Services, Utils)
                  60-70%
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Target Coverage: 75-80% (not 100%)
    Focus: Critical user paths + offline sync
```

---

## 🔍 TESTING STRATEGY BY LAYER

### FRONTEND TESTING

#### 1. Unit Tests (Store + Services)
**Goal**: Test business logic in isolation  
**Tools**: Jest + Vitest  
**Coverage Target**: 80%+

**Test Suites**:

```
frontend/tests/
├── stores/
│   ├── authStore.test.ts
│   │   ├── login() success/failure
│   │   ├── logout() clears state
│   │   ├── refreshToken() renews access token
│   │   └── Selectors: canCreateInspection(), hasPermission(), etc.
│   │
│   ├── inspectionStore.test.ts
│   │   ├── createInspection() initializes properly
│   │   ├── addPhoto() validates quality metadata
│   │   ├── submitInspection() validates required fields
│   │   ├── updateSyncStatus() tracks offline state
│   │   └── getCurrentInspection() returns correct inspection
│   │
│   ├── approvalStore.test.ts
│   │   ├── fetchPendingApprovals() API call + state
│   │   ├── approveInspection() removes from pending
│   │   ├── rejectInspection() with reason validation
│   │   └── getApprovalStats() returns correct stats
│   │
│   ├── masterStore.test.ts
│   │   ├── fetchAllMasters() caches + TTL
│   │   ├── createDefect() adds to list
│   │   ├── updateDefect() modifies existing
│   │   ├── inactivateDefect() removes from list
│   │   └── getCacheStatus() returns correct TTL
│   │
│   └── offlineStore.test.ts
│       ├── enqueueOperation() adds to queue
│       ├── startSync() retries on failure
│       ├── setNetworkStatus() triggers auto-sync
│       ├── retryFailed() resets failed items
│       └── getQueueStatus() returns correct counts
│
├── services/
│   ├── authService.test.ts
│   │   ├── login() stores tokens correctly
│   │   ├── refreshToken() updates in memory
│   │   ├── logout() clears all state
│   │   └── getAccessToken() returns from storage
│   │
│   ├── inspectionService.test.ts
│   │   ├── searchLote() calls API correctly
│   │   ├── registerInspection() validates + saves
│   │   ├── saveDraftOffline() persists to IndexedDB
│   │   ├── syncPendingInspections() retries failed
│   │   └── addPhoto() validates metadata
│   │
│   ├── errorTracking.test.ts
│   │   ├── captureError() queues error
│   │   ├── flushQueue() sends to API
│   │   ├── Offline retry with backoff
│   │   └── Slack alert triggered for critical
│   │
│   ├── performanceMonitoring.test.ts
│   │   ├── captureNetworkTiming() logs API calls
│   │   ├── LCP threshold triggers warning
│   │   └── Photo validation timing tracked
│   │
│   └── analytics.test.ts
│       ├── trackEvent() queues event
│       ├── flush() batches events
│       └── Properties included correctly
│
└── utils/
    ├── validators.test.ts
    │   ├── validateEmail() valid/invalid
    │   ├── validateComment() length + content
    │   ├── validatePhotoSize() compression needed
    │   └── validateInspection() all required fields
    │
    └── formatters.test.ts
        ├── formatDate() timezone handling
        ├── formatFileSize() bytes → MB
        └── formatErrorMessage() sanitization
```

**Test Structure Example**:
```typescript
// authStore.test.ts
describe("AuthStore", () => {
  beforeEach(() => {
    useAuthStore.getState().resetAuth()
  })

  describe("login()", () => {
    it("should set user and tokens on success", async () => {
      await useAuthStore.getState().login("test@example.com", "password")
      const state = useAuthStore.getState()
      
      expect(state.user).toBeDefined()
      expect(state.access_token).toBeDefined()
      expect(state.is_authenticated).toBe(true)
    })

    it("should set error on invalid credentials", async () => {
      await expect(
        useAuthStore.getState().login("test@example.com", "wrong")
      ).rejects.toThrow()
      
      expect(useAuthStore.getState().error).toBeDefined()
    })
  })

  describe("canApproveInspection()", () => {
    it("should return true for JEFE_QA role", () => {
      useAuthStore.setState({
        user: { id: "1", email: "qa@test.com", role: "JEFE_QA", full_name: "QA Lead" }
      })
      
      expect(useAuthStore.getState().canApproveInspection()).toBe(true)
    })

    it("should return false for OPERARIO role", () => {
      useAuthStore.setState({
        user: { id: "1", email: "op@test.com", role: "OPERARIO", full_name: "Operator" }
      })
      
      expect(useAuthStore.getState().canApproveInspection()).toBe(false)
    })
  })
})
```

---

#### 2. Component Tests (React)
**Goal**: Test UI interactions and state binding  
**Tools**: Jest + React Testing Library  
**Coverage Target**: 60%+

**Test Suites**:

```
frontend/tests/components/
├── LoginPage.test.tsx
│   ├── Renders email + password inputs
│   ├── Submits form on button click
│   ├── Shows error on invalid credentials
│   ├── Redirects on successful login
│   └── Disables button while loading
│
├── InspectionPage.test.tsx
│   ├── Loads lote data on search
│   ├── Displays "Offline" status correctly
│   ├── Adds photo and validates quality
│   ├── Shows validation errors for missing fields
│   ├── Submits inspection + updates queue
│   └── Disables submit button while syncing
│
├── ApprovalPage.test.tsx
│   ├── Fetches and displays pending approvals
│   ├── Opens modal with photo + details on row click
│   ├── Approves inspection with comment
│   ├── Rejects with required reason
│   ├── Removes approved item from list
│   └── Shows error toast on failure
│
├── ConfigPage.test.tsx
│   ├── Displays defects, machines, fabrics tabs
│   ├── Creates new defect with validation
│   ├── Updates existing master
│   ├── Inactivates master (soft delete)
│   └── Shows cache refresh button
│
└── SyncIndicator.test.tsx
    ├── Shows "📡 Online (All synced)" when status online
    ├── Shows "🔴 Offline (5 pending)" when offline
    ├── Shows "❌ 2 failed - Retry" when failed
    └── Triggers retry on button click
```

**Example**:
```typescript
// InspectionPage.test.tsx
describe("InspectionPage", () => {
  it("should display offline indicator", () => {
    useOfflineStore.setState({ network_status: "OFFLINE" })
    
    const { getByText } = render(<InspectionPage />)
    expect(getByText(/offline/i)).toBeInTheDocument()
  })

  it("should submit inspection with photos", async () => {
    const { getByRole } = render(<InspectionPage />)
    
    // Upload photo
    const input = getByRole("input", { name: /photo/i })
    const file = new File(["photo"], "test.jpg", { type: "image/jpeg" })
    fireEvent.change(input, { target: { files: [file] } })
    
    // Submit form
    fireEvent.click(getByRole("button", { name: /save/i }))
    
    await waitFor(() => {
      expect(useInspectionStore.getState().can_submit).toBe(false)
    })
  })
})
```

---

#### 3. Integration Tests
**Goal**: Test store + API interactions, offline sync  
**Tools**: Jest + MSW (Mock Service Worker)  
**Coverage Target**: Critical paths only

**Test Scenarios**:

```
frontend/tests/integration/
├── Auth Flow
│   ├── Login → token storage → redirect to dashboard
│   ├── Token refresh on 401 response
│   └── Logout → clear state → redirect to login
│
├── Inspection Offline Sync
│   ├── Create inspection offline → save to IndexedDB
│   ├── Go online → auto-sync to API
│   ├── Sync failure → retry with exponential backoff
│   └── Successful sync → update syncStatus
│
├── Approval Workflow
│   ├── Fetch pending → display in table
│   ├── Approve → remove from pending → add to history
│   ├── Reject with reason → validation + API call
│   └── Concurrent approvals (no race conditions)
│
├── Master Data Cache
│   ├── First fetch → API call + cache
│   ├── Within TTL → use cache (no API call)
│   ├── After TTL → API call + refresh
│   └── Manual refresh → bypass TTL
│
└── Network Status Changes
    ├── Online → Offline → auto-pause sync
    ├── Offline → Online → auto-resume sync
    ├── Network error → retry with backoff
    └── Sync queue persisted across page reload
```

**Example**:
```typescript
// offlineSync.integration.test.ts
describe("Offline Sync Integration", () => {
  it("should sync inspection when coming online", async () => {
    // Start offline
    useOfflineStore.setState({ network_status: "OFFLINE" })
    
    // Create inspection
    useInspectionStore.getState().createInspection("HDR-123")
    useInspectionStore.getState().submitInspection("insp-id")
    
    // Verify queued
    expect(useOfflineStore.getState().getPendingCount()).toBe(1)
    
    // Go online
    useOfflineStore.setState({ network_status: "ONLINE" })
    await useOfflineStore.getState().startSync()
    
    // Verify synced
    await waitFor(() => {
      expect(useOfflineStore.getState().getFailedCount()).toBe(0)
    })
  })
})
```

---

#### 4. E2E Tests (Cypress/Playwright)
**Goal**: Test complete user workflows  
**Tools**: Playwright (lightweight)  
**Coverage Target**: Critical paths only (5-10 tests)

**Test Scenarios**:

```
e2e/tests/
├── Auth Flow
│   └── Login → See Dashboard
│
├── Inspection Creation (Operario)
│   └── Search Lote → Capture Photo → Add Defect → Submit → See "Synced" ✓
│
├── Offline Inspection (Operario)
│   └── Offline Mode → Capture → Save → Go Online → Auto-Sync
│
├── Approval Workflow (Jefe QA)
│   └── See Pending → Approve → See in History
│
├── Master Management (Admin)
│   └── Go to Config → Create Defect → Edit → Inactivate
│
└── Sync Recovery
    └── Create Inspection → Sync Fails → Retry → Success
```

---

### BACKEND TESTING

#### 1. Unit Tests (Services)
**Goal**: Test business logic  
**Tools**: pytest + pytest-asyncio  
**Coverage Target**: 80%+

```
backend/tests/
├── services/
│   ├── test_auth_service.py
│   │   ├── hash_password() produces different hashes
│   │   ├── verify_password() validates correctly
│   │   ├── create_access_token() valid JWT
│   │   └── verify_token() validates signature
│   │
│   ├── test_inspection_service.py
│   │   ├── register_inspection() validates lote/defect/machine
│   │   ├── get_pending_approvals() queries correctly
│   │   ├── sync_offline_inspections() merges data
│   │   └── save_photo() handles base64 + compression
│   │
│   ├── test_approval_service.py
│   │   ├── approve_inspection() creates approval + updates status
│   │   ├── reject_inspection() with reason
│   │   └── get_approval_stats() calculates correctly
│   │
│   └── test_sync_service.py
│       ├── merge_offline_data() conflict resolution
│       ├── handle_duplicate_inspection() server wins
│       └── retry_failed_operations() exponential backoff
│
├── models/
│   ├── test_user_model.py
│   │   ├── User creation + roles
│   │   └── Password hashing on save
│   │
│   ├── test_inspection_model.py
│   │   ├── Inspection relationships (lote, analista, defect, machine)
│   │   ├── Status transitions valid
│   │   └── Timestamps auto-set
│   │
│   └── test_approval_model.py
│       ├── Approval unique per inspection
│       └── Cascade delete with inspection
│
└── routes/
    ├── test_auth_routes.py
    │   ├── POST /auth/login (success/failure)
    │   ├── POST /auth/refresh (valid/expired token)
    │   └── GET /auth/me (authorized/unauthorized)
    │
    ├── test_inspection_routes.py
    │   ├── POST /inspections (create with photo)
    │   ├── GET /inspections/pending-approval (pagination)
    │   ├── GET /inspections/{id} (detail)
    │   └── POST /inspections/sync (offline merge)
    │
    ├── test_approval_routes.py
    │   ├── POST /approvals (approve/reject with RBAC)
    │   ├── GET /approvals/stats
    │   └── GET /approvals/my-approvals
    │
    └── test_master_routes.py
        ├── GET /masters/defects (list all)
        ├── POST /masters/defects (create)
        ├── PUT /masters/defects/{id} (update)
        └── DELETE /masters/defects/{id} (soft delete)
```

**Example**:
```python
# test_auth_service.py
import pytest
from app.routes_auth import hash_password, verify_password, create_access_token

def test_hash_password_produces_different_hashes():
    pwd = "test_password_123"
    hash1 = hash_password(pwd)
    hash2 = hash_password(pwd)
    
    assert hash1 != hash2  # Different salts
    assert verify_password(pwd, hash1)
    assert verify_password(pwd, hash2)

def test_create_access_token_valid_jwt():
    token = create_access_token("user123", "test@example.com", "OPERARIO")
    
    assert isinstance(token, str)
    assert len(token) > 0
    # Can decode without exception
    from app.routes_auth import verify_token
    payload = verify_token(token)
    
    assert payload["user_id"] == "user123"
    assert payload["email"] == "test@example.com"
```

---

#### 2. API Tests (pytest + httpx)
**Goal**: Test endpoints end-to-end  
**Tools**: pytest + TestClient  
**Coverage Target**: Critical endpoints (80%+)

```python
# test_inspection_routes.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def auth_token(db: Session):
    """Create test user and return token"""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("password"),
        full_name="Test User",
        role="OPERARIO"
    )
    db.add(user)
    db.commit()
    
    from app.routes_auth import create_access_token
    return create_access_token(str(user.id), user.email, user.role)

def test_create_inspection_success(auth_token, db: Session):
    """POST /inspections with valid data"""
    # Create lote and defect first
    lote = Lote(id="HDR-123", fabric_id="FABRIC-1", quantity_meters=100)
    defect = Defect(id="DEF-TON", name="TONODIFFERENTE")
    db.add_all([lote, defect])
    db.commit()
    
    # Create inspection
    response = client.post(
        "/inspections",
        json={
            "lote_id": "HDR-123",
            "defect_type_id": "DEF-TON",
            "comment": "Variación de tono significativa",
            "photos": [
                {
                    "id": "photo-1",
                    "base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
                    "metadata": {
                        "laplacian": 150,
                        "brightness": 128,
                        "contrast": 100,
                        "quality": "PASS"
                    }
                }
            ]
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "REGISTERED"
    assert data["synced"] == True

def test_get_pending_approvals_pagination():
    """GET /inspections/pending-approval with pagination"""
    response = client.get(
        "/inspections/pending-approval?limit=10&offset=0"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10
```

---

#### 3. Integration Tests (Database + API)
**Goal**: Test multi-step workflows  
**Tools**: pytest with real/test PostgreSQL  
**Coverage Target**: Critical workflows only

```
backend/tests/integration/
├── Auth Flow
│   ├── Register → Login → Get Token → Access Protected
│   └── Refresh Token → Auto-Retry on 401
│
├── Inspection Workflow
│   ├── Create → Verify in DB → Approve → Verify Status
│   └── Offline Sync → Merge Data → Verify Final State
│
├── Approval Workflow
│   ├── Get Pending → Approve → Update Status → Verify
│   └── Multiple Approvers → No Race Conditions
│
└── Master Data
    ├── CRUD Defect → Verify Cache → Clear → Refresh
    └── Concurrent Updates → Last Write Wins
```

---

## 📊 TESTING COVERAGE TARGETS

| Module | Unit | Component | Integration | E2E | Overall |
|--------|------|-----------|-------------|-----|---------|
| **Auth** | 85% | 70% | 90% | 100% | 85% |
| **Inspection** | 80% | 75% | 85% | 100% | 85% |
| **Approval** | 80% | 70% | 80% | 100% | 80% |
| **Masters** | 75% | 60% | 70% | 80% | 70% |
| **Offline Sync** | 85% | 50% | 95% | 100% | 85% |
| **Utils** | 90% | N/A | N/A | N/A | 90% |
| **Overall** | 83% | 67% | 84% | 96% | **78%** |

**Target**: 75-80% overall coverage (not 100%)  
**Priority**: Auth + Inspection + Offline Sync (highest risk)

---

## 🛠️ TESTING TOOLS & SETUP

### Frontend

```json
{
  "devDependencies": {
    "jest": "^29.0.0",
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^6.0.0",
    "vitest": "^0.34.0",
    "@playwright/test": "^1.40.0",
    "msw": "^1.3.0"
  }
}
```

### Backend

```toml
[tool.poetry.group.dev.dependencies]
pytest = "^7.0"
pytest-asyncio = "^0.21"
pytest-cov = "^4.0"
httpx = "^0.24"
faker = "^18.0"
```

---

## 🔄 TESTING WORKFLOW

```
┌─────────────────────────────────────────────────────────┐
│ Developer commits code                                  │
└────────────┬────────────────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────────────────┐
│ GitHub Actions: Run Tests (5 min)                       │
│ ├─ Lint (1 min)                                        │
│ ├─ Unit Tests (2 min)                                  │
│ ├─ Integration Tests (2 min)                           │
│ └─ Upload Coverage Report                              │
└────────────┬────────────────────────────────────────────┘
             │
      ┌──────┴──────┐
      │             │
      ↓             ↓
   PASS          FAIL
      │             │
      ↓             ↓
   Merge       Manual Review
   to main     + Fix Issues
      │
      ↓
┌─────────────────────────────────────────────────────────┐
│ Deploy to Staging (runs E2E tests)                      │
│ ├─ E2E Tests (2 min)                                   │
│ └─ Smoke Tests                                          │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ TESTING CHECKLIST

**Before Merge to Main**:
- [ ] All unit tests pass (npm test)
- [ ] All integration tests pass (npm run test:integration)
- [ ] Code coverage >= 75%
- [ ] No TypeScript errors (npm run type-check)
- [ ] No eslint errors (npm run lint)
- [ ] Critical E2E tests pass

**Before Deploy to Production**:
- [ ] All E2E tests pass
- [ ] Manual smoke tests on staging
- [ ] Performance benchmarks (< 3s page load)
- [ ] Accessibility audit (a11y)
- [ ] Security scan (no XSS, SQL injection, etc.)

---

## 📈 SUCCESS METRICS

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Code Coverage** | 75% | npm test --coverage |
| **Unit Test Pass Rate** | 100% | npm test |
| **E2E Test Pass Rate** | 95%+ | npm run test:e2e |
| **Test Execution Time** | < 5 min | CI pipeline timing |
| **Bug Escape Rate** | < 5% | Production defects / sprint |
| **Offline Sync Reliability** | 99.9% | Successful syncs / total attempts |

---

**Status**: 🎯 TESTING DESIGN COMPLETE  
**Next**: Implement tests per this design (Phase 7 of Activity 5)  
**Recommendation**: Write tests as features are implemented (TDD approach)

