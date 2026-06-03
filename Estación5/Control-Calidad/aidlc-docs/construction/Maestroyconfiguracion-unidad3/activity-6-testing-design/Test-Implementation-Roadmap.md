# Test Implementation Roadmap — Unit 3 (Maestros y Configuración)

**Date**: 2026-06-01  
**Scope**: Detailed test count, priorities, and implementation sequence  
**Audience**: Developers implementing Activity 6 tests  

---

## 🎯 TESTING PRIORITIES

### Priority 1: CRITICAL (Must Have)
**Reason**: Prevent data corruption, ensure business logic correctness  
**Estimated Effort**: 15 hours  
**Expected Coverage**: 80%+ of critical paths

1. **MastersService Tests** (6 tests, 2 hours)
   - create_defect (success + duplicate + invalid machine)
   - update_defect (success + version conflict)
   - archive_defect (success + recent usage + pending approvals)

2. **Repositories CRUD Tests** (8 tests, 2 hours)
   - save(), get_by_id(), exists_by_name() for Defect
   - Similar for Machine, Fabric
   - get_all_active() with pagination

3. **API Routes: Create & List** (4 tests, 2 hours)
   - POST /defects (success, duplicate, no auth, no permission)
   - GET /defects (list, search, pagination)
   - GET /defects/{id} (found, not found)

4. **API Routes: Update & Archive** (4 tests, 2 hours)
   - PATCH /defects/{id} (success, version conflict, no permission)
   - POST /defects/{id}/archive (success, recent usage, pending approvals)

5. **Schema Validation** (4 tests, 1 hour)
   - DefectCreate (valid, invalid name, invalid enum)
   - DefectUpdate (valid, version required)

6. **Audit Trail** (2 tests, 1 hour)
   - Verify audit log created on create
   - Verify old/new values in audit log

7. **CSV Import Validation** (4 tests, 3 hours)
   - Valid CSV validation passes
   - Duplicate detection
   - Header validation
   - Rollback on error

8. **E2E: Defect Lifecycle** (2 tests, 2 hours)
   - Create → search → update → archive workflow
   - Verify state transitions at each step

**Total**: ~32 tests, 15 hours

---

### Priority 2: HIGH (Important)
**Reason**: Cover main workflows, edge cases  
**Estimated Effort**: 8 hours  
**Coverage Addition**: +10%

1. **MachineService & FabricService Tests** (6 tests, 2 hours)
   - Similar to Defect (create, update, archive)
   - Machine-specific: process validation
   - Fabric-specific: width/weight range validation

2. **Repository Specialized Queries** (4 tests, 1.5 hours)
   - get_by_process() for machines
   - search_by_name() with pagination
   - get_system_masters()

3. **Concurrent Edit Handling** (2 tests, 1 hour)
   - Admin A & B edit same defect
   - B gets 409 Conflict
   - B refreshes and retries

4. **CSV Import Complete Workflow** (3 tests, 2 hours)
   - Upload → validate → preview → execute
   - Verify WebSocket progress updates
   - Verify job status transitions

5. **Error Scenarios** (4 tests, 1.5 hours)
   - System master protection (cannot edit/delete)
   - Archive with reason logging
   - Bulk archive (future feature)

**Total**: ~19 tests, 8 hours

---

### Priority 3: MEDIUM (Nice to Have)
**Reason**: Edge cases, non-critical paths, refining coverage  
**Estimated Effort**: 5 hours  
**Coverage Addition**: +3%

1. **Component Integration** (3 tests, 1 hour)
   - Service + Repository interaction
   - Transaction rollback on error
   - Cache invalidation after create

2. **Performance Tests** (2 tests, 1 hour)
   - Search with 1000 items < 100ms
   - List pagination < 150ms
   - CSV import 10k rows < 3 minutes

3. **Audit Trail Advanced** (2 tests, 1 hour)
   - Query audit by date range
   - Query audit by user
   - Immutability verification

4. **Data Cleanup & Lifecycle** (3 tests, 1.5 hours)
   - Archived masters don't appear in search
   - Restore archived master
   - Soft delete doesn't affect related data

5. **Documentation Tests** (1 test, 0.5 hour)
   - Verify API docs accurate
   - OpenAPI schema valid

**Total**: ~11 tests, 5 hours

---

## 📅 IMPLEMENTATION SCHEDULE

### Sprint 1: Weeks 1-2 (15 hours)
**Goal**: Get Priority 1 tests passing (32 tests)  
**Target Coverage**: 80%+

**Week 1**:
- Day 1-2: Set up pytest, fixtures, conftest.py (2h)
  - Create in-memory SQLite fixture
  - Create admin_user fixture
  - Create MastersService fixture

- Day 3-4: Write MastersService tests (3h)
  - test_create_defect_success
  - test_create_defect_duplicate_name
  - test_update_defect_success
  - test_update_defect_version_conflict
  - test_archive_defect_success
  - test_archive_defect_recent_usage

- Day 5: Write Repository CRUD tests (2h)
  - test_save_and_get_by_id
  - test_exists_by_name_case_insensitive
  - test_get_all_active_pagination
  - test_search_by_name

**Week 2**:
- Day 1-2: Write Routes tests (3h)
  - test_create_defect_endpoint_201
  - test_create_defect_duplicate_409
  - test_list_defects_with_pagination
  - test_update_defect_version_conflict_409
  - test_archive_defect_endpoint

- Day 3: Write Schema & Audit tests (2h)
  - test_defect_create_schema_validation
  - test_audit_log_on_create
  - test_audit_old_new_values

- Day 4-5: CSV Import & E2E (4h)
  - test_csv_validation_header_mismatch
  - test_csv_duplicate_detection
  - test_csv_import_rollback_on_error
  - test_e2e_defect_create_search_update_archive

**Deliverable**: Priority 1 passing, 80%+ coverage, green CI/CD

---

### Sprint 2: Weeks 3-4 (8 hours)
**Goal**: Complete Priority 2 tests (19 tests)  
**Target Coverage**: 85%+

**Week 3**:
- Day 1-2: Machine & Fabric Service tests (2h)
  - test_create_machine_with_process
  - test_create_fabric_with_width_validation
  - test_archive_machine_validation

- Day 3-4: Repository queries + Concurrent edits (2.5h)
  - test_get_by_process
  - test_search_pagination
  - test_concurrent_edit_version_conflict

- Day 5: CSV complete workflow (2h)
  - test_csv_upload_validate_preview_execute
  - test_csv_websocket_progress

**Week 4**:
- Day 1-2: Error scenarios (1.5h)
  - test_system_master_cannot_update
  - test_archive_with_reason_logging

- Day 3-4: Refinements + bug fixes (1h)
- Day 5: Coverage review (0.5h)

**Deliverable**: Priority 2 passing, 85%+ coverage

---

### Sprint 3: Week 5+ (5 hours)
**Goal**: Complete Priority 3 tests (11 tests)  
**Target Coverage**: 85%+

- Performance tests
- Audit trail advanced queries
- Data lifecycle tests
- Documentation tests
- Refactoring based on test learnings

---

## 🔧 TEST SETUP COMMANDS

### Installation

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock faker

# Verify installation
pytest --version
```

### Directory Structure

```bash
# Create test directories
mkdir -p tests/{services,repositories,routes,integration}
touch tests/__init__.py
touch tests/conftest.py
touch tests/services/__init__.py
touch tests/repositories/__init__.py
touch tests/routes/__init__.py
```

### Run Tests

```bash
# All tests
pytest

# Watch mode (auto-rerun on changes)
pip install pytest-watch
ptw

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/services/test_masters_service.py -v

# Specific test
pytest tests/services/test_masters_service.py::TestCreateDefect::test_creates_defect_successfully -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Last N failures
pytest --lf
pytest --ff
```

---

## 📝 FIRST TEST EXAMPLE (MastersService.create_defect)

### conftest.py (Fixtures)

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, User
from app.services import MastersService
from app.schemas import ProcessEnum

@pytest.fixture
def db():
    """In-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def admin_user(db):
    """Create admin user for testing"""
    user = User(
        id="admin-test-001",
        email="admin@test.com",
        hashed_password="hashed",
        full_name="Test Admin",
        role="ADMIN",
        is_active=True
    )
    db.add(user)
    db.commit()
    return user

@pytest.fixture
def service(db):
    """MastersService instance"""
    return MastersService(db)

@pytest.fixture
def valid_defect_payload():
    """Valid payload for creating defect"""
    from app.schemas import DefectCreate
    return DefectCreate(
        name="Roto",
        description="Tear in fabric",
        typical_process=ProcessEnum.TEÑIDO,
        typical_machine_id=None
    )
```

### Test File

```python
# tests/services/test_masters_service.py
import pytest
from app.services import MastersService, DuplicateError, ValidationError, ArchiveError
from app.models import StatusEnum
from app.schemas import DefectCreate, ProcessEnum

class TestCreateDefect:
    """Tests for MastersService.create_defect()"""
    
    def test_creates_defect_successfully(self, service, valid_defect_payload, admin_user):
        """Should create defect with valid payload"""
        # Act
        result = service.create_defect(valid_defect_payload, user_id=admin_user.id)
        
        # Assert
        assert result.id.startswith("DEF-")
        assert result.name == "Roto"
        assert result.description == "Tear in fabric"
        assert result.typical_process == ProcessEnum.TEÑIDO
        assert result.status == StatusEnum.ACTIVE
        assert result.is_system == False
        assert result.version == 1
        assert result.created_by == admin_user.id
        assert result.created_at is not None

    def test_rejects_duplicate_name(self, service, valid_defect_payload, admin_user):
        """Should reject duplicate defect names"""
        # Arrange: Create first defect
        service.create_defect(valid_defect_payload, user_id=admin_user.id)
        
        # Act & Assert: Second defect with same name
        with pytest.raises(DuplicateError) as exc_info:
            service.create_defect(valid_defect_payload, user_id=admin_user.id)
        
        assert "already exists" in str(exc_info.value)
        assert "Roto" in str(exc_info.value)

    def test_rejects_if_machine_not_found(self, service, admin_user):
        """Should reject if typical_machine_id doesn't exist"""
        payload = DefectCreate(
            name="Roto",
            typical_machine_id="MAQ-NONEXISTENT"
        )
        
        with pytest.raises(ValidationError) as exc_info:
            service.create_defect(payload, user_id=admin_user.id)
        
        assert "Machine" in str(exc_info.value)
        assert "not found" in str(exc_info.value)

    def test_creates_audit_log_entry(self, service, valid_defect_payload, admin_user, db):
        """Should create audit log on create"""
        # Act
        defect = service.create_defect(valid_defect_payload, user_id=admin_user.id)
        
        # Assert: Verify audit log
        audit_entries = db.query(AuditLog).filter(
            AuditLog.entity_id == defect.id
        ).all()
        
        assert len(audit_entries) == 1
        assert audit_entries[0].operation == "INSERT"
        assert audit_entries[0].user_id == admin_user.id
        assert audit_entries[0].old_values is None
        assert audit_entries[0].new_values is not None

    def test_sets_default_status_active(self, service, valid_defect_payload, admin_user):
        """Should default status to ACTIVE"""
        result = service.create_defect(valid_defect_payload, user_id=admin_user.id)
        assert result.status == StatusEnum.ACTIVE

    def test_sets_version_to_1(self, service, valid_defect_payload, admin_user):
        """Should initialize version to 1"""
        result = service.create_defect(valid_defect_payload, user_id=admin_user.id)
        assert result.version == 1


class TestUpdateDefect:
    """Tests for MastersService.update_defect()"""
    
    def test_updates_defect_successfully(self, service, admin_user, db):
        """Should update defect with valid payload"""
        # Arrange: Create defect
        payload = DefectCreate(name="Roto", typical_process=ProcessEnum.TEÑIDO)
        defect = service.create_defect(payload, user_id=admin_user.id)
        
        # Act: Update
        from app.schemas import DefectUpdate
        update = DefectUpdate(
            name="Rotura",
            version=defect.version
        )
        result = service.update_defect(defect.id, update, user_id=admin_user.id)
        
        # Assert
        assert result.name == "Rotura"
        assert result.version == 2

    def test_rejects_version_conflict(self, service, admin_user):
        """Should detect concurrent edit (version mismatch)"""
        # Arrange: Create defect
        payload = DefectCreate(name="Roto", typical_process=ProcessEnum.TEÑIDO)
        defect = service.create_defect(payload, user_id=admin_user.id)
        
        # Act: Try to update with wrong version
        from app.schemas import DefectUpdate
        update = DefectUpdate(name="Rotura", version=999)  # Wrong version
        
        # Assert
        with pytest.raises(ValidationError) as exc_info:
            service.update_defect(defect.id, update, user_id=admin_user.id)
        
        assert "version" in str(exc_info.value).lower()


class TestArchiveDefect:
    """Tests for MastersService.archive_defect()"""
    
    def test_archives_defect_successfully(self, service, admin_user):
        """Should archive defect"""
        # Arrange
        payload = DefectCreate(name="Roto")
        defect = service.create_defect(payload, user_id=admin_user.id)
        
        # Act
        result = service.archive_defect(defect.id, reason="Old defect", user_id=admin_user.id)
        
        # Assert
        assert result.status == StatusEnum.ARCHIVED

    def test_rejects_archive_if_recent_usage(self, service, admin_user, mocker):
        """Should reject archive if used in last 7 days"""
        # Arrange
        payload = DefectCreate(name="Roto")
        defect = service.create_defect(payload, user_id=admin_user.id)
        
        # Mock recent usage
        mocker.patch.object(
            service.defect_repo,
            'count_recent_usage',
            return_value=3
        )
        
        # Act & Assert
        with pytest.raises(ArchiveError) as exc_info:
            service.archive_defect(defect.id, None, user_id=admin_user.id)
        
        assert "recent" in str(exc_info.value).lower()
```

---

## ✅ QUALITY GATES

**Before merging code with tests**:
- [ ] All tests passing (pytest exit code 0)
- [ ] Coverage ≥ 80% (pytest-cov)
  - Services ≥ 95%
  - Repositories ≥ 85%
  - Routes ≥ 80%
  - Schemas ≥ 90%
- [ ] No console errors or warnings
- [ ] No hardcoded test data (use fixtures)
- [ ] All test names descriptive
- [ ] Fixtures reusable, DRY principle

**CI/CD Command**:
```bash
pytest --cov=app --cov-report=term-missing --cov-fail-under=80 -v
```

---

**Status**: 🎯 **TESTING DESIGN COMPLETE**  
**Next Step**: Implement tests per Priority 1 in weeks 1-2  
**Recommendation**: Start with conftest.py + MastersService tests (foundation for other tests)
