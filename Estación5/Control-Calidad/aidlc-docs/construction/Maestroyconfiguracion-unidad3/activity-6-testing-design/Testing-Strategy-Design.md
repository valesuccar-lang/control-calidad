# Activity 6: Testing Strategy & Design — Unit 3 (Maestros y Configuración)

**Date**: 2026-06-01  
**Unit**: Maestros y Configuración (Masters & Configuration Domain)  
**Scope**: Testing strategy, pyramid, coverage targets, and quality gates  
**Audience**: QA Engineers, Developers, Test Architects  

---

## 📋 OVERVIEW

This document defines the testing strategy for the Masters & Configuration backend service. It covers unit, integration, and E2E tests with specific coverage targets and quality gates.

**Key Testing Principles**:
1. **Test Pyramid**: 70% unit, 20% integration, 10% E2E
2. **Coverage Target**: 80%+ for critical paths (services, repositories)
3. **Fast Feedback**: Unit tests < 100ms, integration < 1s
4. **Realistic Data**: Use realistic test data, avoid mocks where integration matters
5. **Clear Names**: Test names document expected behavior

---

## 🎯 TESTING PYRAMID

```
        /\
       /  \   E2E Tests (10%)
      /    \  - Full workflow
     /______\
     
    /        \
   /          \  Integration Tests (20%)
  /            \ - API endpoints
 /______________\ - Database interactions
 
/                \
/                  \  Unit Tests (70%)
/                    \ - Services
/______________________ - Repositories
                       - Schemas
```

**Rationale**:
- **Unit (70%)**: Fast, isolated, catch most bugs
- **Integration (20%)**: Catch real DB/API interactions
- **E2E (10%)**: Catch workflow issues
- **Total Target**: 80%+ coverage of critical code

---

## 🧪 TEST TYPES & COVERAGE

### 1. UNIT TESTS (70% = ~500 lines)

**Target**: MastersService, Repositories, Schemas

#### 1.1 Service Unit Tests (250 lines, ~30 tests)

**DefectService Tests**:
```
Test create_defect():
  ✓ Creates defect with all fields
  ✓ Rejects duplicate name
  ✓ Validates machine reference exists
  ✓ Sets default status=ACTIVE
  ✓ Increments version to 1
  ✓ Logs audit entry

Test update_defect():
  ✓ Updates name with validation
  ✓ Detects version conflict (409 Conflict)
  ✓ Prevents system master modification
  ✓ Increments version on successful update
  ✓ Checks duplicate name (excluding self)

Test archive_defect():
  ✓ Archives defect successfully
  ✓ Rejects archive if recent usage (7 days)
  ✓ Rejects archive if pending approvals
  ✓ Prevents system master archive
  ✓ Sets status=ARCHIVED
  ✓ Creates audit log
```

**MachineService Tests**: Similar 10 tests
**FabricService Tests**: Similar 10 tests

**Test Approach**: Mock repositories, focus on business logic

#### 1.2 Repository Unit Tests (150 lines, ~20 tests)

**DefectRepository Tests**:
```
Test save():
  ✓ Inserts new defect
  ✓ Returns inserted entity

Test get_by_id():
  ✓ Returns defect if exists
  ✓ Returns None if not found

Test exists_by_name():
  ✓ Returns True for existing name (case-insensitive)
  ✓ Returns False for non-existing
  ✓ Excludes self in duplicate check

Test search_by_name():
  ✓ Returns matching defects (case-insensitive)
  ✓ Respects pagination (skip, limit)
  ✓ Filters archived

Test get_all_active():
  ✓ Returns only ACTIVE defects
  ✓ Excludes system masters
  ✓ Ordered by name
  ✓ Respects pagination
```

**Test Approach**: Use in-memory SQLite for DB tests

#### 1.3 Schema Validation Tests (100 lines, ~15 tests)

**DefectCreate Schema**:
```
Test name validation:
  ✓ Accepts valid names (3-100 chars)
  ✗ Rejects short names (< 3 chars)
  ✗ Rejects long names (> 100 chars)
  ✗ Rejects invalid characters (SQL chars)

Test enum validation:
  ✓ Accepts valid process enum
  ✗ Rejects invalid process

Test machine reference:
  ✓ Accepts valid machine_id
  ✓ Accepts None (optional)
  ✗ Rejects non-existent machine_id (at schema level: format only)
```

**Test Approach**: Direct schema validation, no DB needed

---

### 2. INTEGRATION TESTS (20% = ~200 lines)

**Target**: API routes with real DB interactions

#### 2.1 API Endpoint Tests (120 lines, ~12 tests)

**Create Defect Endpoint**:
```
Test POST /api/v1/masters/defects:
  ✓ Returns 201 Created with defect data
  ✓ Returns 409 Conflict if duplicate name
  ✓ Returns 400 Bad Request if invalid data
  ✓ Returns 403 Forbidden if not ADMIN
  ✓ Saves to database
  ✓ Creates audit log entry
```

**List Defects Endpoint**:
```
Test GET /api/v1/masters/defects:
  ✓ Returns 200 OK with paginated results
  ✓ Respects page/page_size parameters
  ✓ Supports search parameter
  ✓ Filters archived by default
  ✓ Includes total count
  ✓ Returns empty list if no matches
```

**Update Defect Endpoint**:
```
Test PATCH /api/v1/masters/defects/{id}:
  ✓ Returns 200 OK with updated data
  ✓ Returns 409 Conflict if version mismatch
  ✓ Returns 404 Not Found if defect doesn't exist
  ✓ Increments version
  ✓ Prevents ADMIN->non-ADMIN downgrade
```

**Archive Defect Endpoint**:
```
Test POST /api/v1/masters/defects/{id}/archive:
  ✓ Returns 200 OK on success
  ✓ Returns 400 Bad Request if recent usage
  ✓ Returns 400 Bad Request if pending approvals
  ✓ Sets status=ARCHIVED in DB
  ✓ Returns 403 if not ADMIN
```

**Test Approach**: TestClient, real DB (in-memory), JWT token mock

#### 2.2 CSV Import Workflow (80 lines, ~8 tests)

```
Test CSV validation:
  ✓ Validates file type (CSV only)
  ✓ Validates encoding (UTF-8)
  ✓ Validates file size (≤ 100MB)
  ✓ Validates header row
  ✓ Returns detailed error report

Test CSV import:
  ✓ Inserts new rows
  ✓ Detects duplicates
  ✓ Skips or updates based on mode
  ✓ Rolls back on error
  ✓ Completes successfully
  ✓ Updates import job status
```

---

### 3. E2E TESTS (10% = ~100 lines)

**Target**: Complete workflows

#### 3.1 Defect Lifecycle E2E (50 lines, ~3 tests)

```
Test Create → Update → Archive:
  1. Create defect "Roto"
  2. Verify appears in list
  3. Update name to "Rotura"
  4. Verify search finds updated name
  5. Archive with reason
  6. Verify doesn't appear in active list
  7. Verify appears in archived list
```

#### 3.2 CSV Import Workflow E2E (50 lines, ~3 tests)

```
Test Upload → Validate → Import:
  1. Upload 100-row CSV
  2. Validate format
  3. Preview changes (new/dup/update counts)
  4. Execute import
  5. Check progress via WebSocket
  6. Verify all 100 rows in DB
  7. Verify audit logs created
```

---

## 📊 COVERAGE TARGETS

| Component | Target | Rationale |
|-----------|--------|-----------|
| **MastersService** | ≥ 95% | Critical business logic |
| **Repositories** | ≥ 85% | Data access layer |
| **Routes** | ≥ 80% | HTTP contract |
| **Schemas** | ≥ 90% | Input validation |
| **Models** | ≥ 60% | Mostly data structures |
| **Overall** | ≥ 80% | Target for production readiness |

**Coverage Exclusions** (acceptable):
- `__repr__()`, `__str__()` methods
- Exception classes (basic definitions)
- Optional/logging statements
- Type hints (no runtime impact)

---

## 🛠️ TEST TOOLS & SETUP

### Frontend Testing Tools

| Tool | Purpose | Version |
|------|---------|---------|
| **pytest** | Unit & integration test framework | 7.0+ |
| **pytest-asyncio** | Async test support | 0.20+ |
| **pytest-cov** | Coverage reporting | 4.0+ |
| **SQLAlchemy** | In-memory SQLite for DB tests | 1.4+ |
| **httpx** | TestClient for FastAPI | 0.23+ |
| **faker** | Fake data generation | 15.0+ |

### Setup Commands

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock faker httpx

# Create test directories
mkdir -p tests/{services,repositories,routes}

# Run all tests
pytest                              # All tests
pytest --cov=app --cov-report=html # With coverage report
pytest -v                           # Verbose
pytest -k "test_create"             # Specific tests
pytest tests/services/ -v           # Specific directory

# Watch mode (requires pytest-watch)
pip install pytest-watch
ptw                                 # Re-run on file change
```

---

## 📋 TEST STRUCTURE

### conftest.py (Fixtures & Setup)

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def db():
    """In-memory SQLite database"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

@pytest.fixture
def admin_user(db):
    """Admin user for tests"""
    user = User(id="admin1", email="admin@test.com", role="ADMIN")
    db.add(user)
    db.commit()
    return user

@pytest.fixture
def service(db):
    """MastersService instance"""
    return MastersService(db)
```

### Test File Naming

```
tests/
├── test_services/
│   └── test_masters_service.py     # Defect, Machine, Fabric tests
├── test_repositories/
│   ├── test_defect_repository.py
│   ├── test_machine_repository.py
│   └── test_fabric_repository.py
├── test_routes/
│   └── test_masters_routes.py      # All endpoints
├── test_integration/
│   └── test_csv_import.py          # CSV workflow
└── conftest.py                      # Shared fixtures
```

---

## ✅ QUALITY GATES

**All tests must pass before merge:**

- [ ] All tests passing (0 failures)
- [ ] Coverage ≥ 80% overall
  - Services ≥ 95%
  - Repositories ≥ 85%
  - Routes ≥ 80%
  - Schemas ≥ 90%
- [ ] No console errors or warnings
- [ ] No hardcoded test data (use fixtures)
- [ ] No flaky tests (consistent results)
- [ ] Performance acceptable (unit < 100ms, integration < 1s)

**CI/CD Check**:
```yaml
pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

---

## 🔍 TESTING BEST PRACTICES

### 1. Test Names Document Behavior

```python
# ❌ Bad: What's being tested?
def test_defect():
    ...

# ✅ Good: Clear expected behavior
def test_create_defect_with_duplicate_name_raises_error():
    ...
    
def test_archive_defect_prevents_archive_if_recent_usage():
    ...
```

### 2. One Assertion Per Test (Usually)

```python
# ❌ Bad: Multiple assertions obscure failures
def test_create_defect():
    result = service.create_defect(payload, user_id="admin1")
    assert result.id is not None
    assert result.name == "Roto"
    assert result.status == StatusEnum.ACTIVE
    assert result.is_system == False

# ✅ Good: Single logical assertion
def test_create_defect_sets_status_active():
    result = service.create_defect(payload, user_id="admin1")
    assert result.status == StatusEnum.ACTIVE
```

### 3. Use Descriptive Fixtures

```python
# ✅ Good: Fixtures with clear purpose
@pytest.fixture
def valid_defect_payload():
    return DefectCreate(
        name="Roto",
        description="Tear in fabric",
        typical_process=ProcessEnum.TEÑIDO
    )

@pytest.fixture
def duplicate_defect_payload(db, admin_user):
    # Create defect first
    service = MastersService(db)
    service.create_defect(
        DefectCreate(name="Roto", ...),
        user_id=admin_user.id
    )
    # Payload with same name
    return DefectCreate(name="Roto", ...)
```

### 4. Test Edge Cases

```python
# Success path
def test_archive_defect_success():
    ...

# Failure paths
def test_archive_defect_fails_if_recent_usage():
    ...

def test_archive_defect_fails_if_pending_approvals():
    ...

# Edge cases
def test_archive_defect_fails_if_system_master():
    ...
```

### 5. Mock External Dependencies

```python
# ✅ Good: Mock repositories in service tests
def test_create_defect_validates_machine_reference(service, mocker):
    mock_repo = mocker.patch.object(service, 'machine_repo')
    mock_repo.get_by_id.return_value = None
    
    with pytest.raises(ValidationError):
        service.create_defect(payload, user_id="admin1")
    
    mock_repo.get_by_id.assert_called_with("MAQ-001")
```

### 6. Use Real DB for Integration

```python
# ✅ Good: Use real SQLite in-memory for integration tests
def test_create_defect_saves_to_db(db, admin_user):
    service = MastersService(db)
    service.create_defect(payload, user_id=admin_user.id)
    
    # Verify actually saved
    saved = db.query(Defect).filter(Defect.name == "Roto").first()
    assert saved is not None
```

---

## 📈 COVERAGE REPORT EXAMPLE

```
Name                        Stmts   Miss  Cover   Missing
---------------------------------------------------------
app/services.py             250     12    95%     123-125, 456-458
app/repositories.py         180     27    85%     45-50, 78-82
app/routes_masters.py       200     40    80%     150-160, 220-230
app/schemas.py              150     15    90%     88-90, 145-147
app/models.py               120     48    60%     25-30, 45-55 (OK to exclude)
---------------------------------------------------------
TOTAL                      900     142    84%

Coverage by component:
- Services: 95%       ✅ TARGET MET
- Repositories: 85%   ✅ TARGET MET
- Routes: 80%         ✅ TARGET MET
- Schemas: 90%        ✅ TARGET MET
- Overall: 84%        ✅ TARGET MET (≥80%)
```

---

## 🚀 CI/CD INTEGRATION

### GitHub Actions Workflow

```yaml
name: Tests & Coverage

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run tests
        run: pytest --cov=app --cov-report=xml
      
      - name: Check coverage
        run: pytest --cov=app --cov-fail-under=80
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

---

## 📅 TESTING SCHEDULE

### Sprint 1: Weeks 1-2 (15 hours)

**Week 1**:
- Day 1-2: Set up pytest, conftest, fixtures (2h)
- Day 3-4: Write DefectService tests (3h)
- Day 5: Write DefectRepository tests (2h)

**Week 2**:
- Day 1-2: Write routes tests (3h)
- Day 3: Write CSV validation tests (2h)
- Day 4-5: Bug fixes, refactor (1h)

**Deliverable**: Services & repositories ≥ 90% coverage

### Sprint 2: Weeks 3-4 (10 hours)

**Week 3**:
- Day 1-2: Write MachineService & FabricService tests (3h)
- Day 3-4: Write E2E workflow tests (3h)
- Day 5: Performance tests (1h)

**Week 4**:
- Day 1-2: Refactor & optimize (1h)
- Day 3-4: Bug fixes (1h)
- Day 5: Final coverage check, documentation (1h)

**Deliverable**: Overall coverage ≥ 80%, all E2E passing

---

## 📝 EXAMPLE TEST

### DefectService Create Test

```python
# tests/test_services/test_masters_service.py
import pytest
from app.services import MastersService, DuplicateError, ValidationError
from app.schemas import DefectCreate, ProcessEnum

@pytest.fixture
def service(db):
    return MastersService(db)

@pytest.fixture
def valid_payload():
    return DefectCreate(
        name="Roto",
        description="Tear in fabric",
        typical_process=ProcessEnum.TEÑIDO
    )

class TestCreateDefect:
    
    def test_creates_defect_successfully(self, service, valid_payload, admin_user):
        """Create defect with all required fields"""
        result = service.create_defect(valid_payload, user_id=admin_user.id)
        
        assert result.id.startswith("DEF-")
        assert result.name == "Roto"
        assert result.description == "Tear in fabric"
        assert result.status == StatusEnum.ACTIVE
        assert result.version == 1
        assert result.created_by == admin_user.id
    
    def test_rejects_duplicate_name(self, service, valid_payload, admin_user):
        """Cannot create duplicate names"""
        # Create first
        service.create_defect(valid_payload, user_id=admin_user.id)
        
        # Try to create duplicate
        with pytest.raises(DuplicateError) as exc_info:
            service.create_defect(valid_payload, user_id=admin_user.id)
        
        assert "already exists" in str(exc_info.value)
    
    def test_validates_machine_reference(self, service, mocker):
        """Machine reference must exist"""
        payload = DefectCreate(
            name="Roto",
            typical_machine_id="MAQ-001"
        )
        
        mock_repo = mocker.patch.object(service, 'machine_repo')
        mock_repo.get_by_id.return_value = None
        
        with pytest.raises(ValidationError) as exc_info:
            service.create_defect(payload, user_id="admin1")
        
        assert "Machine" in str(exc_info.value)
```

---

**Status**: ✅ **ACTIVITY 6 STRATEGY COMPLETE**  
**Next Step**: Test Implementation Roadmap with specific test count & timeline  
**Recommendation**: Start with MastersService tests (highest ROI, catches most bugs)
