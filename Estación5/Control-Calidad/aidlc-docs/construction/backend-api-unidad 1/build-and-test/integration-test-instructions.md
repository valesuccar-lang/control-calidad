# Integration Test Instructions — Backend API

**Date**: 2026-05-28  
**Target Coverage**: >60% for API routes (end-to-end flows)

---

## 🧪 INTEGRATION TEST OVERVIEW

Integration tests verify complete API flows with realistic data, including HTTP requests/responses and database interactions.

**Test Files**:
- `tests/integration/test_inspection_routes.py` — Inspection CRUD + validation
- `tests/integration/test_auth_routes.py` — Authentication flow
- `tests/integration/test_offline_sync.py` — Sync configuration + batch validation

**Target**: >60% coverage of:
- API endpoints (POST, GET, etc.)
- Request validation (400 errors)
- Authorization (403 for wrong role)
- Business logic (one approval per inspection, idempotency, etc.)

---

## ⚙️ SETUP

### **Install Additional Test Dependencies**
```bash
pip install httpx  # Async HTTP client for FastAPI testing
pip install pytest-asyncio  # Already installed, but confirm
```

### **Verify Installation**
```bash
python -c "import httpx; print('httpx OK')"
```

---

## 🚀 RUN INTEGRATION TESTS

### **All Integration Tests**
```bash
pytest tests/integration -v
```

**Expected output:**
```
tests/integration/test_inspection_routes.py::test_create_inspection_unauthorized PASSED
tests/integration/test_inspection_routes.py::test_create_inspection_invalid_comment PASSED
tests/integration/test_inspection_routes.py::test_list_inspections PASSED
tests/integration/test_inspection_routes.py::test_health_check PASSED

tests/integration/test_auth_routes.py::test_login_success PASSED
tests/integration/test_auth_routes.py::test_login_invalid_credentials PASSED
tests/integration/test_auth_routes.py::test_refresh_token PASSED
tests/integration/test_auth_routes.py::test_get_current_user PASSED

tests/integration/test_offline_sync.py::test_exponential_backoff_delays PASSED
tests/integration/test_offline_sync.py::test_sync_configuration PASSED
tests/integration/test_offline_sync.py::test_batch_sync_endpoint_structure PASSED

======== 11 passed in 2.34s ========
```

### **Specific Test Suite**
```bash
pytest tests/integration/test_auth_routes.py -v
```

### **With Coverage**
```bash
pytest tests/integration --cov=app.routes --cov-report=html
```

### **Run Tests with Real Database** (Optional)
```bash
# Set environment to use test database
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/textile_qc_test"

# Run tests against real database
pytest tests/integration -v
```

---

## 📋 TEST SCENARIOS

### **Authentication Flow**
```
1. POST /auth/login (valid credentials) → 200 + tokens
2. POST /auth/login (invalid credentials) → 401
3. POST /auth/refresh (valid token) → 200 + new access token
4. GET /auth/me (with token) → 200 + user info
5. GET /auth/me (without token) → 401
```

### **Inspection CRUD**
```
1. POST /api/inspections (ANALISTA) → 201 + inspection_id
2. POST /api/inspections (invalid comment) → 400
3. POST /api/inspections (unauthorized) → 403
4. GET /api/inspections → 200 + list
5. GET /api/inspections/{id} → 200 + details
6. GET /api/inspections/{id} (not found) → 404
```

### **Approval Workflow**
```
1. POST /api/approvals/approve (JEFE_QA) → 201
2. POST /api/approvals/approve (duplicate) → 400 (one per inspection)
3. POST /api/approvals/reject (with reason) → 201
4. POST /api/approvals/reject (no reason) → 400
5. GET /api/approvals/pending → 200 + list
```

### **Masters Management**
```
1. GET /api/masters/defects (ANALISTA) → 200 + active list
2. GET /api/masters/machines → 200
3. GET /api/masters/fabrics → 200
4. POST /api/masters/import-csv (ADMIN) → 201 + import result
5. POST /api/masters/import-csv (duplicates) → 201 + skipped count
```

### **Offline Sync**
```
1. POST /api/inspections/sync-batch (array of 50 items) → 200
2. POST /api/inspections/sync-batch (100 items) → 200
3. POST /api/inspections/sync-batch (>100 items) → 400 (validation)
4. Verify exponential backoff config → [5, 10, 30, 60, 60]
```

---

## 🔍 TEST PATTERNS

### **Pattern 1: Happy Path (Valid Request)**
```python
async def test_login_success():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            json={"email": "analista@example.com", "password": "password"}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
```

### **Pattern 2: Validation Error (Invalid Input)**
```python
async def test_create_inspection_invalid_comment():
    """Comments must be 10+ characters"""
    response = await client.post(
        "/api/inspections",
        json={...comment_text: "short"...}  # < 10 chars
    )
    assert response.status_code == 400
```

### **Pattern 3: Authorization (Role-Based)**
```python
async def test_create_inspection_unauthorized():
    """Only ANALISTA can create inspections"""
    response = await client.post(
        "/api/inspections",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 403  # Forbidden
```

### **Pattern 4: Idempotency Check**
```python
async def test_approve_inspection_duplicate():
    """One approval per inspection enforced"""
    await service.approve_inspection(inspection_id, jefe_qa_id)
    
    # Try again
    with pytest.raises(ValueError):
        await service.approve_inspection(inspection_id, jefe_qa_id)
```

---

## 📊 API COVERAGE CHECKLIST

### **Authentication Routes** (5 tests)
- [ ] POST /auth/login (success)
- [ ] POST /auth/login (invalid credentials)
- [ ] POST /auth/refresh
- [ ] GET /auth/me (authenticated)
- [ ] GET /auth/me (unauthenticated)

### **Inspection Routes** (5+ tests)
- [ ] POST /api/inspections (create, ANALISTA role)
- [ ] POST /api/inspections (invalid comment length)
- [ ] POST /api/inspections (invalid photo size)
- [ ] POST /api/inspections/sync-batch (100 items)
- [ ] GET /api/inspections (list with pagination)
- [ ] GET /api/inspections/{id} (get single)

### **Approval Routes** (4+ tests)
- [ ] POST /api/approvals/approve (success)
- [ ] POST /api/approvals/approve (duplicate rejection)
- [ ] POST /api/approvals/reject (with reason)
- [ ] POST /api/approvals/reject (missing reason)
- [ ] GET /api/approvals/pending

### **Masters Routes** (4+ tests)
- [ ] GET /api/masters/defects (list active)
- [ ] GET /api/masters/machines
- [ ] GET /api/masters/fabrics
- [ ] POST /api/masters/import-csv (with duplicates)

### **Sync Configuration** (3 tests)
- [ ] Exponential backoff delays correct
- [ ] Batch sync validation (max 100 items)
- [ ] Sync configuration accessible

### **Health & Config** (2+ tests)
- [ ] GET /health (database connected)
- [ ] GET /api/config (returns feature flags)

---

## 🐛 DEBUGGING INTEGRATION TEST FAILURES

### **View Full Response**
```python
response = await client.post("/auth/login", json={...})
print(f"Status: {response.status_code}")
print(f"Body: {response.json()}")  # Shows full error
```

### **Enable Request Logging**
```bash
pytest tests/integration -v --log-cli-level=DEBUG
```

### **Check Database State**
```bash
# If using real database, query it directly
psql -U postgres -d textile_qc_test

# SELECT * FROM inspections;
# SELECT * FROM approvals;
```

### **Common Issues**

| Error | Cause | Fix |
|-------|-------|-----|
| `422 Validation Error` | Invalid request schema | Check JSON structure matches Pydantic model |
| `401 Unauthorized` | Missing/invalid token | Include proper Authorization header |
| `403 Forbidden` | Wrong role | Use token with correct role |
| `409 Conflict` | Duplicate approval | Check business rule enforcement |
| `500 Internal Error` | Database connection | Verify PostgreSQL running |

---

## ✔️ INTEGRATION TEST CHECKLIST

- [ ] httpx installed
- [ ] All integration tests pass
- [ ] Coverage >60% for app/routes/
- [ ] No flaky tests (run 2-3 times, should pass consistently)
- [ ] Happy path tests (valid requests) pass
- [ ] Validation tests (invalid data) pass
- [ ] Authorization tests (role-based) pass
- [ ] Business logic tests (one approval, idempotency) pass
- [ ] Health check endpoint works
- [ ] API docs available at /docs

---

## 🎯 PASSING CRITERIA

✅ **All tests pass:**
```bash
pytest tests/integration -q
# Expected: 11+ passed
```

✅ **Coverage meets target:**
```bash
pytest tests/integration --cov=app.routes --cov-report=term
# Expected: app/routes coverage: 60%+
```

✅ **Consistent results:**
```bash
# Run 3 times - should all pass
pytest tests/integration
pytest tests/integration
pytest tests/integration
```

---

**Status**: ✅ Integration tests defined  
**Next**: Run both unit + integration tests together for complete coverage
