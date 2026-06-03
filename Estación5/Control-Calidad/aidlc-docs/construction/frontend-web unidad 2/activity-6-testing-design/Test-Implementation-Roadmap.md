# Test Implementation Roadmap
## Priority Order for Activity 5 → Testing Integration

**Date**: 2026-06-01  
**Scope**: Which tests to write first, in what order  
**Audience**: Developers implementing Activity 5 code

---

## 🎯 TESTING PRIORITIES

### Priority 1: CRITICAL (Must Have)
**Reason**: These tests prevent catastrophic bugs and data loss  
**Estimated Effort**: 20 hours  
**Expected Coverage**: 70%+ of critical paths

1. **Auth Store Tests** (3 tests, 30 min)
   - Login success/failure
   - Token refresh
   - RBAC selectors (canApprove, hasPermission)

2. **Offline Store Tests** (4 tests, 1 hour)
   - Enqueue operation
   - Start sync + retry logic
   - Network status change triggers sync
   - Queue status selectors

3. **Inspection Store Tests** (5 tests, 1.5 hours)
   - Create inspection
   - Add photo + validate quality
   - Submit inspection validation
   - Update sync status

4. **Auth Routes (Backend)** (3 tests, 1 hour)
   - POST /auth/login (success, invalid creds)
   - POST /auth/refresh (valid, expired token)
   - GET /auth/me (authorized, unauthorized)

5. **Inspection Routes (Backend)** (4 tests, 1.5 hours)
   - POST /inspections (create with photo)
   - GET /inspections/pending-approval (pagination)
   - GET /inspections/{id} (detail view)
   - POST /inspections/sync (offline merge)

6. **Integration: Auth Flow** (1 test, 1 hour)
   - Login → token storage → access protected endpoint

7. **Integration: Offline Sync Flow** (1 test, 1.5 hours)
   - Create inspection offline → go online → auto-sync
   - Verify queue status transitions

8. **E2E: Login Flow** (1 test, 30 min)
   - Open app → login → see dashboard

9. **E2E: Inspection Creation** (1 test, 1 hour)
   - Search lote → capture photo → submit → verify synced

**Total**: ~10 hours, 2,500 lines of test code

---

### Priority 2: HIGH (Important)
**Reason**: These cover main user workflows  
**Estimated Effort**: 12 hours  
**Coverage Addition**: +15%

1. **Master Store Tests** (3 tests, 1.5 hours)
   - Fetch with cache TTL
   - CRUD operations (defects)
   - Cache expiration + refresh

2. **Approval Store Tests** (3 tests, 1 hour)
   - Fetch pending approvals
   - Approve inspection
   - Reject with reason

3. **Error Tracking Service Tests** (2 tests, 1 hour)
   - Capture error + queue
   - Flush queue on API success

4. **Performance Monitoring Tests** (2 tests, 1 hour)
   - Track API timing
   - Threshold alerts

5. **Approval Routes (Backend)** (2 tests, 1 hour)
   - POST /approvals (approve/reject with RBAC)
   - GET /approvals/stats

6. **Master Routes (Backend)** (2 tests, 1.5 hours)
   - GET /masters/defects (list)
   - POST /masters/defects (create)

7. **E2E: Approval Workflow** (1 test, 1 hour)
   - See pending → approve → verify in history

8. **E2E: Offline + Sync** (1 test, 1.5 hours)
   - Go offline → create inspection → go online → auto-sync

**Total**: ~12 hours, 1,800 lines of test code

---

### Priority 3: MEDIUM (Nice to Have)
**Reason**: Edge cases and non-critical paths  
**Estimated Effort**: 10 hours  
**Coverage Addition**: +8%

1. **Component Tests** (15+ tests, 8 hours)
   - LoginPage, InspectionPage, ApprovalPage
   - Form validation, error display
   - Button states during loading

2. **Utility Tests** (3 tests, 1 hour)
   - Validators (email, comment, photo size)
   - Formatters (date, file size)

3. **E2E: Config/Masters** (1 test, 1 hour)
   - Create master → edit → inactivate

**Total**: ~10 hours, 1,500 lines of test code

---

## 📅 IMPLEMENTATION SCHEDULE

### Sprint 1: Weeks 1-2 (20 hours)
**Goal**: Get Priority 1 tests passing  
**Target Coverage**: 70%+

**Week 1**:
- Day 1-2: Set up Jest + pytest, write first auth store tests
- Day 3-4: Write offline store + inspection store tests
- Day 5: Write backend auth routes tests

**Week 2**:
- Day 1-2: Write backend inspection routes tests
- Day 3: Write integration tests (auth flow, sync flow)
- Day 4-5: Write E2E tests (login, inspection creation)

**Deliverable**: All Priority 1 tests green, coverage >= 70%

---

### Sprint 2: Weeks 3-4 (12 hours)
**Goal**: Complete Priority 2 tests  
**Target Coverage**: 75%+

**Week 3**:
- Day 1-2: Master store tests
- Day 3-4: Approval store + routes tests
- Day 5: Service tests (error tracking, performance)

**Week 4**:
- Day 1: E2E approval workflow
- Day 2-3: E2E offline + sync
- Day 4-5: Bug fixes + coverage improvements

**Deliverable**: All Priority 2 tests green, coverage >= 75%

---

### Sprint 3: Week 5+ (10 hours)
**Goal**: Complete Priority 3 tests + refinements  
**Target Coverage**: 78%+

- Component tests
- Utility tests
- Edge case E2E tests
- Performance benchmarks

---

## 🔧 TEST SETUP COMMANDS

### Frontend Setup

```bash
# Install test dependencies
npm install --save-dev jest @testing-library/react @testing-library/jest-dom vitest msw @playwright/test

# Create jest config
npx jest --init

# Create test directories
mkdir -p tests/{stores,services,components,utils,integration}

# Run tests
npm test                           # Watch mode
npm run test:coverage              # Coverage report
npm run test:e2e                   # Playwright E2E
```

### Backend Setup

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov faker

# Create pytest config
# pytest.ini or pyproject.toml

# Create test directories
mkdir -p tests/{services,models,routes,integration}

# Run tests
pytest                             # All tests
pytest --cov=app                   # With coverage
pytest -v                          # Verbose
pytest -k "test_login"             # Specific test
```

---

## 📝 FIRST TEST EXAMPLE (Auth Store)

```typescript
// frontend/tests/stores/authStore.test.ts
import { renderHook, act } from '@testing-library/react'
import { useAuthStore } from '../../src/stores/authStore'
import * as authService from '../../src/services/authService'

// Mock the auth service
jest.mock('../../src/services/authService')

describe('AuthStore', () => {
  beforeEach(() => {
    useAuthStore.getState().resetAuth()
    jest.clearAllMocks()
  })

  describe('login()', () => {
    it('should set user and tokens on successful login', async () => {
      const mockResponse = {
        user: {
          id: 'user-123',
          email: 'test@example.com',
          full_name: 'Test User',
          role: 'OPERARIO'
        },
        access_token: 'token-123',
        refresh_token: 'refresh-123'
      }

      ;(authService.login as jest.Mock).mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useAuthStore())

      await act(async () => {
        await result.current.login('test@example.com', 'password')
      })

      expect(result.current.user).toEqual(mockResponse.user)
      expect(result.current.access_token).toBe('token-123')
      expect(result.current.is_authenticated).toBe(true)
      expect(result.current.error).toBeNull()
    })

    it('should set error on failed login', async () => {
      ;(authService.login as jest.Mock).mockRejectedValue(
        new Error('Invalid credentials')
      )

      const { result } = renderHook(() => useAuthStore())

      await act(async () => {
        await expect(
          result.current.login('test@example.com', 'wrong')
        ).rejects.toThrow()
      })

      expect(result.current.error).toBe('Invalid credentials')
      expect(result.current.is_authenticated).toBe(false)
    })
  })

  describe('canApproveInspection()', () => {
    it('should return true for JEFE_QA role', () => {
      const { result } = renderHook(() => useAuthStore())

      act(() => {
        result.current.setUser({
          id: 'user-123',
          email: 'qa@example.com',
          full_name: 'QA Lead',
          role: 'JEFE_QA'
        })
      })

      expect(result.current.canApproveInspection()).toBe(true)
    })

    it('should return false for OPERARIO role', () => {
      const { result } = renderHook(() => useAuthStore())

      act(() => {
        result.current.setUser({
          id: 'user-123',
          email: 'op@example.com',
          full_name: 'Operator',
          role: 'OPERARIO'
        })
      })

      expect(result.current.canApproveInspection()).toBe(false)
    })
  })
})
```

---

## 🚀 TESTING BEST PRACTICES

1. **Test User Behavior, Not Implementation**
   ```typescript
   // ❌ Bad: Testing implementation detail
   expect(store.users.length).toBe(1)
   
   // ✅ Good: Testing behavior
   expect(store.hasUser('user-123')).toBe(true)
   ```

2. **Use Descriptive Test Names**
   ```typescript
   // ❌ Bad
   it('works', () => { ... })
   
   // ✅ Good
   it('should add inspection to queue when offline', () => { ... })
   ```

3. **One Assertion Per Test (Usually)**
   ```typescript
   // ❌ Bad: Multiple assertions in one test
   it('should handle login', () => {
     expect(user).toBeDefined()
     expect(token).toBeDefined()
     expect(isAuth).toBe(true)
   })
   
   // ✅ Good: One logical assertion per test
   it('should set user on successful login', () => {
     expect(result.current.user).toBeDefined()
   })
   
   it('should set access token on successful login', () => {
     expect(result.current.access_token).toBeDefined()
   })
   ```

4. **Test Edge Cases**
   ```typescript
   // Success case
   it('should approve inspection with comment', () => { ... })
   
   // Failure case
   it('should reject if inspection not found', () => { ... })
   
   // Edge case
   it('should handle concurrent approvals without race condition', () => { ... })
   ```

5. **Mock External Dependencies**
   ```typescript
   // ✅ Mock API calls
   jest.mock('../../services/api')
   
   // ✅ Test store logic in isolation
   // ❌ Don't make real API calls in unit tests
   ```

---

## ✅ QUALITY GATES

**Before merging code with tests**:
- [ ] All tests passing
- [ ] Coverage >= 75% for modified code
- [ ] No console errors or warnings
- [ ] No hardcoded test data in tests
- [ ] Tests document expected behavior (readable)

---

**Status**: 🎯 TESTING DESIGN COMPLETE  
**Next Step**: Implement tests per Priority 1 in Activity 5 Phase 7  
**Recommendation**: Start with authStore tests (quickest wins, foundation for other tests)

