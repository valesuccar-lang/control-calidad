# Unit Test Instructions — Backend API

**Date**: 2026-05-28  
**Target Coverage**: >80% for domain services and repositories

---

## 🧪 UNIT TEST OVERVIEW

Unit tests verify isolated business logic without external dependencies (database, HTTP).

**Test Files**:
- `tests/unit/test_domain_services.py` — Domain service logic
- `tests/unit/test_repositories.py` — (Optional) Repository abstractions

**Target**: >80% coverage of:
- Domain services (InspectionService, ApprovalService, MastersService)
- Value objects (Comment, Photograph, InspectionTime)
- Business rule enforcement

---

## ⚙️ SETUP

### **Install Test Dependencies**
```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

### **Verify Installation**
```bash
pytest --version  # Should be pytest 7.4+
```

---

## 🚀 RUN UNIT TESTS

### **All Unit Tests**
```bash
pytest tests/unit -v
```

**Expected output:**
```
tests/unit/test_domain_services.py::test_inspection_service_register PASSED
tests/unit/test_domain_services.py::test_inspection_service_invalid_comment PASSED
tests/unit/test_domain_services.py::test_photo_value_object_validation PASSED
tests/unit/test_domain_services.py::test_comment_value_object_validation PASSED
tests/unit/test_domain_services.py::test_approval_service_approve PASSED
tests/unit/test_domain_services.py::test_approval_service_reject PASSED
tests/unit/test_domain_services.py::test_masters_service_bulk_import_defects PASSED

======== 7 passed in 0.45s ========
```

### **Specific Test**
```bash
pytest tests/unit/test_domain_services.py::test_inspection_service_register -v
```

### **With Coverage Report**
```bash
pytest tests/unit --cov=app --cov-report=html

# View HTML report
open htmlcov/index.html  # On macOS
start htmlcov/index.html  # On Windows
xdg-open htmlcov/index.html  # On Linux
```

### **Coverage in Terminal**
```bash
pytest tests/unit --cov=app --cov-report=term-missing

# Output shows coverage % and missing lines
# Expected:
# app/domain/services/inspection_service.py  98%
# app/domain/services/approval_service.py    95%
# app/repositories/inspection_repository.py  88%
```

---

## ✅ TEST COVERAGE GOALS

| Module | Target | Current |
|--------|--------|---------|
| app/domain/services/ | >80% | (measure after run) |
| app/domain/entities.py | >85% | |
| app/domain/value_objects.py | >90% | |
| app/repositories/ | >75% | |
| **Overall (domain)** | **>80%** | |

---

## 🧬 TEST STRUCTURE

### **Test File Organization**
```
tests/unit/
├── test_domain_services.py
│   ├── test_inspection_service_register()
│   ├── test_inspection_service_invalid_comment()
│   ├── test_photo_value_object_validation()
│   ├── test_comment_value_object_validation()
│   ├── test_approval_service_approve()
│   ├── test_approval_service_reject()
│   └── test_masters_service_bulk_import_defects()
│
└── test_repositories.py (optional)
    ├── test_inspection_repository_create()
    ├── test_inspection_repository_get_by_id()
    ├── test_approval_repository_get_pending()
    └── test_masters_repository_bulk_import_idempotency()
```

### **Test Fixtures** (conftest.py)
- `test_db` — In-memory SQLite database
- `db_session` — Async database session
- `test_user_data` — Mock user data
- `test_inspection_data` — Mock inspection data
- `test_approval_data` — Mock approval data

---

## 🔍 KEY TESTS

### **1. Value Object Validation**
```python
@pytest.mark.asyncio
async def test_comment_value_object_validation():
    """Comments must be 10-500 chars"""
    with pytest.raises(ValueError):
        Comment(text="short")  # Fails
    
    comment = Comment(text="Valid comment with 10+ chars")
    assert len(comment.text) > 10
```

**Purpose**: Ensures invalid data cannot be created (immutability + validation)

### **2. Business Rule Enforcement**
```python
@pytest.mark.asyncio
async def test_approval_service_one_per_inspection():
    """Only one approval allowed per inspection (BR-007)"""
    # Create approval
    approval1 = await service.approve_inspection(inspection_id, jefe_qa_id)
    
    # Try to approve again
    with pytest.raises(ValueError):
        approval2 = await service.approve_inspection(inspection_id, jefe_qa_id)
```

**Purpose**: Verifies business rules are enforced at service layer

### **3. Idempotency**
```python
@pytest.mark.asyncio
async def test_masters_bulk_import_idempotency():
    """Duplicate imports are skipped (BR-012)"""
    result = await service.bulk_import_defects([
        {"defect_id": "DEF_001", "name": "Tear"},
        {"defect_id": "DEF_001", "name": "Tear"},  # Duplicate
    ])
    
    assert result["created"] == 1
    assert result["skipped"] == 1
```

**Purpose**: Ensures sync operations don't create duplicates

---

## 📊 COVERAGE MEASUREMENT

### **Generate Coverage Report**
```bash
pytest tests/unit \
  --cov=app.domain \
  --cov=app.repositories \
  --cov-report=html \
  --cov-report=term-missing
```

### **Interpret Coverage Report**
- **Green (>85%)**: Well-tested, good coverage
- **Yellow (70-85%)**: Adequate coverage, could improve
- **Red (<70%)**: Insufficient coverage, add tests

### **View Missing Lines**
```bash
pytest tests/unit --cov-report=term-missing

# Shows:
# app/domain/services/inspection_service.py  98%  [45-47]
#                              ^^^^^ lines 45-47 not covered
```

---

## 🐛 DEBUGGING FAILED TESTS

### **Run with Verbose Output**
```bash
pytest tests/unit -vv --tb=long
```

### **Run with Print Statements**
```bash
pytest tests/unit -s  # Shows print() output

# In test code:
print(f"Inspection ID: {inspection.inspection_id}")
pytest tests/unit -s  # Will display above output
```

### **Run Single Test with Debugger**
```bash
pytest tests/unit/test_domain_services.py::test_inspection_service_register -vv --pdb
# (pdb) commands to step through code
```

### **Common Assertion Failures**
```python
# FAILED: AssertionError: assert None == 'value'
# → Check fixture setup, variable initialization

# FAILED: ValueError: Comment must be between 10 and 500 characters
# → Test data validation is working correctly (expected)
```

---

## ✔️ UNIT TEST CHECKLIST

- [ ] pytest installed (`pip install pytest pytest-asyncio`)
- [ ] All tests run without errors
- [ ] No skipped tests (unless @pytest.mark.skip is intentional)
- [ ] Coverage >80% for domain services
- [ ] Coverage >75% for repositories
- [ ] HTML coverage report generated (`htmlcov/index.html`)
- [ ] Critical business rules have tests
- [ ] Value object validation tests pass
- [ ] Edge cases covered (invalid inputs, duplicates, etc.)

---

## 🎯 PASSING CRITERIA

✅ **All tests pass:**
```bash
pytest tests/unit -q
# Expected: 7 passed in 0.45s
```

✅ **Coverage meets target:**
```bash
pytest tests/unit --cov=app --cov-report=term
# Expected: app coverage: 80%+
```

✅ **No warnings:**
```bash
pytest tests/unit -W error
# Should run without warnings
```

---

**Status**: ✅ Unit tests defined and runnable  
**Next**: Run integration tests for end-to-end verification
