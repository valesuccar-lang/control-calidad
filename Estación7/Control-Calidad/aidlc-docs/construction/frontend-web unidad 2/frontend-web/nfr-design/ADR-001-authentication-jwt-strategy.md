# ADR-001: Authentication & JWT Strategy

**Date**: 2026-05-31  
**Status**: ACCEPTED  
**Context**: Frontend Web Unit — Multi-role security with basic protection (HTTPS + JWT + RBAC)  
**Decision Makers**: Frontend Team

---

## 📋 PROBLEM STATEMENT

The app requires multi-role authentication (Operario, Supervisor, Admin) with basic security (internal/public data, no IP secrets). We need to:
1. Implement secure JWT token handling
2. Enforce role-based access control (RBAC)
3. Minimize client-side complexity (small team, 2-3 devs)
4. Support device compatibility (iPhone 8+, Galaxy S5+)

---

## 🎯 DECISION

**Use JWT (JSON Web Token) authentication with the following strategy:**

```
┌─────────────┐
│   LOGIN     │
│ (Email/Pass)│
└──────┬──────┘
       │ POST /auth/login
       ↓
┌─────────────────────────────────────────┐
│ Backend: Validate credentials           │
│ Generate:                               │
│ - access_token (lifetime: 8 hours)      │
│ - refresh_token (lifetime: 30 days)     │
│ Response: { accessToken, refreshToken } │
└──────┬──────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────┐
│ Frontend: Store tokens securely         │
│ - accessToken: Memory + httpOnly cookie │
│ - refreshToken: httpOnly cookie only    │
│ - User data: Zustand auth store         │
└──────┬──────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────┐
│ API Calls: Include Authorization header │
│ Authorization: Bearer {accessToken}     │
└──────┬──────────────────────────────────┘
       │ Every request
       ↓
┌──────────────────────────────────────────┐
│ Token Expiration (8 hours):              │
│ IF accessToken expires:                  │
│   POST /auth/refresh {refreshToken}      │
│   Get new accessToken                    │
│ IF refreshToken expired:                 │
│   Redirect to /login                     │
└──────────────────────────────────────────┘
```

---

## 🏗️ IMPLEMENTATION DETAILS

### Token Storage Strategy

```typescript
// ✅ SECURE: HttpOnly Cookies (server sets, browser cannot JS access)
// Server sends: Set-Cookie: accessToken=...; HttpOnly; Secure; SameSite=Strict
// Browser stores automatically, included on all requests
// JavaScript cannot read: document.cookie returns empty
// Protection: XSS attack cannot steal tokens

// ⚠️ ALSO STORE in Memory for React access (Zustand)
// accessToken stored in memory for immediate route/component access
// If page refresh: Token re-fetched from httpOnly cookie
// Loss: Page refresh clears memory, but httpOnly cookie persists

// ❌ AVOID: localStorage for tokens (XSS risk)
// localStorage is readable by JavaScript (vulnerable to XSS)
// Do NOT store tokens here
```

### Role-Based Access Control (RBAC)

```typescript
// Zustand Auth Store
interface AuthStore {
  user: {
    id: string
    email: string
    name: string
    role: 'OPERARIO' | 'SUPERVISOR' | 'ADMIN'
  }
  accessToken: string  // From httpOnly cookie
  refreshToken: string // From httpOnly cookie
  isAuthenticated: boolean
  
  // Actions
  login(email: string, password: string): Promise<void>
  logout(): Promise<void>
  refreshToken(): Promise<void>
}

// Frontend Routes (React Router)
<PrivateRoute requiredRole="SUPERVISOR">
  <ApprovalPage />
</PrivateRoute>

// PrivateRoute checks:
if (!isAuthenticated) redirect('/login')
if (user.role !== requiredRole) redirect('/unauthorized')
```

### Token Refresh Flow

```typescript
// Intercept API calls
const api = axios.create({
  baseURL: 'https://api.company.local'
})

// Request interceptor: Add token to every request
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: Handle 401 (token expired)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, try to refresh
      try {
        const newToken = await authService.refreshToken()
        useAuthStore.setState({ accessToken: newToken })
        
        // Retry original request with new token
        return api.request(error.config)
      } catch (refreshError) {
        // Refresh also failed, redirect to login
        useAuthStore.setState({ isAuthenticated: false })
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)
```

### Multi-Role UI Implementation

```typescript
// useAuth hook
const useAuth = () => {
  const { user, isAuthenticated } = useAuthStore()
  
  return {
    canCreateInspection: isAuthenticated && user.role === 'OPERARIO',
    canApproveInspection: isAuthenticated && ['SUPERVISOR', 'ADMIN'].includes(user.role),
    canManageMasters: isAuthenticated && user.role === 'ADMIN',
    
    // Feature visibility
    showApprovalQueue: ['SUPERVISOR', 'ADMIN'].includes(user.role),
    showMastersConfig: user.role === 'ADMIN',
  }
}

// Component usage
const Layout = () => {
  const { canApproveInspection, showMastersConfig } = useAuth()
  
  return (
    <nav>
      <NavLink to="/inspections">My Inspections</NavLink>
      {canApproveInspection && <NavLink to="/approvals">Approval Queue</NavLink>}
      {showMastersConfig && <NavLink to="/config">Settings</NavLink>}
    </nav>
  )
}
```

---

## ✅ BENEFITS

1. **Security**: Tokens in httpOnly cookies, inaccessible to XSS
2. **Standard**: JWT is industry standard, well-tested
3. **Scalability**: Stateless on server (no session storage)
4. **Multi-Role**: Role info in token, easy RBAC implementation
5. **Refresh**: 8-hour access token limits damage if stolen
6. **Simplicity**: Minimal client-side complexity

---

## ⚠️ TRADEOFFS

1. **Cookie Limitations**: httpOnly cookies sent only same-origin (no cross-domain API)
   - Mitigation: Backend and frontend on same domain (api.company.local, app.company.local)
   
2. **CSRF Risk**: Cookies vulnerable to CSRF
   - Mitigation: CSRF tokens on state-changing requests (POST, PUT, DELETE)
   
3. **Token Refresh Complexity**: Manual refresh handling in interceptors
   - Mitigation: Centralized in api.ts, hidden from components

---

## 🔍 BACKEND REQUIREMENTS (For Frontend Team)

Ensure backend provides:
```
POST /auth/login
  Request: { email, password }
  Response: { 
    accessToken (JWT, 8 hours),
    refreshToken (JWT, 30 days),
    user { id, email, name, role }
  }
  Sets: Cookie accessToken + refreshToken (httpOnly, Secure, SameSite)

POST /auth/refresh
  Request: { refreshToken }
  Response: { accessToken (new), refreshToken (rotated) }
  
POST /auth/logout
  Clears: Cookies + blacklist tokens

GET /auth/me
  Headers: Authorization: Bearer {token}
  Response: { user { id, email, name, role } }
```

---

**Status**: ✅ ACCEPTED  
**Implementation**: Use axios interceptors + httpOnly cookies + Zustand for role management  
**Testing**: Auth flow tests, token refresh tests, RBAC route tests
