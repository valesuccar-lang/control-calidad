# Non-Functional Requirements (NFR) — Frontend Web Unit (FINAL)

**Date**: 2026-05-31  
**Unit**: Frontend Web (React 18 + TypeScript)  
**Phase**: Activity 2 — NFR Requirements Assessment (User-Elicited)  
**Status**: ✅ COMPLETE

---

## 📋 EXECUTIVE SUMMARY

Based on detailed requirements elicitation, the Frontend Web unit has specific NFR targets optimized for **small factory deployments** (10-20 users) with **critical offline-occasional support**, **smartphone compatibility (3-5 year old devices)**, and **zero data loss tolerance**.

| Dimension | Target | Criticality | Rationale |
|-----------|--------|-------------|-----------|
| **Performance** | <1s page load (WiFi 20+ Mbps) | HIGH | Fast network, users expect instant feedback |
| **Security** | Basic (HTTPS + JWT + RBAC) | HIGH | Internal/public data, no IP secrets |
| **Reliability** | 100% data durability (zero loss) | CRITICAL | Manufacturing data cannot be lost |
| **Usability** | Multi-role UI (operarios, supervisores, admin) | HIGH | Mixed user profiles with different needs |
| **Maintainability** | Clean code for 2-3 dev team | HIGH | Long-term ownership, internal IT team |
| **Scalability** | Small (10-20 users, ~100 insp/day) | MEDIUM | Currently small, but architecture should support future growth |
| **Offline** | Occasional (important, not critical) | MEDIUM | WiFi usually available, but support intermittent outages |
| **Multimedia** | High volume (5-10 photos/insp, high quality) | CRITICAL | Photo compression & caching essential |
| **Devices** | Smartphone compatibility (3-5 year old) | HIGH | iPhone 8+, Galaxy S5+, not bleeding-edge |
| **Integrations** | ERP/MES integration critical | CRITICAL | Must sync with manufacturing systems |

---

## 1️⃣ PERFORMANCE REQUIREMENTS

### 1.1 Network Environment & Targets
```
Network: WiFi 20+ Mbps (stable, factory/office environment)
Latency: <30ms typical
Bandwidth: Not constrained (local network)

Page Load Targets:
- Time to First Byte (TTFB): <300ms
- First Contentful Paint (FCP): <600ms
- Largest Contentful Paint (LCP): <1000ms (1 second)
- Time to Interactive (TTI): <1000ms
- Full Page Load: <1000ms (1 second total)

Justification: Fast network → users expect sub-second response.
Anything >1s feels laggy to factory workers.
```

### 1.2 Bundle Size Optimization

```
Constraint: Smartphone memory is 2-3GB (moderate devices)
3-5 year old phones have slower JS engines

Targets:
- JavaScript bundle: <150KB gzipped (core app)
  ├─ React + ReactDOM: ~45KB
  ├─ Zustand + utilities: ~10KB
  ├─ Domain services (photo validation, sync): ~30KB
  ├─ UI components: ~30KB
  └─ Remaining: ~35KB (vendor libs)

- CSS bundle: <40KB gzipped
- Initial load assets: <250KB total (JS + CSS + fonts)

Strategy:
- Code splitting by route (lazy load Approval page, Masters page)
- Tree-shaking: Remove unused Tailwind classes
- Dynamic imports: Photo validation lib loads only when needed
```

### 1.3 Runtime Performance

```
DOM Rendering: <100ms per state update
Input Responsiveness: <100ms (keyboard, button clicks)
Photo Validation: <500ms per photo (canvas processing)
Form Submission: <2s (API call + UI update)
List Rendering: <200ms for 100 inspection rows
Navigation: <300ms between pages
```

**Justification**: Factory workers interact with this on the floor. 
Laggy response = frustration = support calls.

---

## 2️⃣ SECURITY REQUIREMENTS

### 2.1 Authentication & Authorization

```
Protocol: HTTPS only (TLS 1.2 minimum)
Authentication: JWT (JSON Web Token)
  ├─ Access token lifetime: 8 hours
  ├─ Refresh token rotation: New token on each refresh
  └─ Token storage: Secure HTTP-only cookies OR memory + refresh

Authorization: Role-Based Access Control (RBAC)
  ├─ OPERARIO: Create inspections, view own history
  ├─ SUPERVISOR: Approve/reject, see all inspections, view reports
  ├─ ADMIN: Manage masters, manage users, system config
  └─ VIEWER: Read-only access to all data

Implementation:
- No passwords stored client-side
- No tokens in localStorage (use httpOnly cookies or memory)
- Automatic logout after 8 hours inactivity
- CSRF tokens on state-changing requests
```

### 2.2 Data Protection

```
In Transit:
- HTTPS with valid certificate
- TLS 1.2+
- Cipher suites: ECDHE for perfect forward secrecy

At Rest (Client):
- IndexedDB: Unencrypted (acceptable for non-IP data)
- LocalStorage: Minimal use (preferences only, not sensitive)
- SessionStorage: Volatile, cleared on close

Data Sensitivity:
- Public: Plant schedules, generic defect types
- Internal: Inspection photos, defect findings, comments
- Confidential: NONE (no trade secrets in app)

No Client-Side Encryption: Not required (data is internal/public, 
                            network is encrypted, local storage is trusted)
```

### 2.3 Input Validation & XSS Prevention

```
Validation Layer:
- Pydantic (backend): Validate all API requests
- Zod (frontend): Validate form inputs before send
- React: JSX auto-escapes (prevents XSS)

Rules:
- No dangerouslySetInnerHTML
- Comment text: 10-500 chars, ASCII-friendly, no script tags
- Photo metadata: Read-only from device API
- Defect selection: Predefined list only, no free text injection
- All strings escaped on display

CORS: Backend restricts to frontend domain only
CSP: script-src 'self' + CDN (if using), no inline scripts
```

---

## 3️⃣ RELIABILITY REQUIREMENTS

### 3.1 Data Durability (Zero Loss Guarantee)

```
CRITICAL: Manufacturing inspection data CANNOT be lost.

Strategy: Multiple persistence layers

Layer 1 - IndexedDB (Client-side):
  └─ Every inspection/approval saved before ANY network call
  └─ Survives: App crash, page reload, browser close

Layer 2 - Service Worker:
  └─ Monitors offline queue, batches syncs on reconnect
  └─ Survives: Network outage, server downtime

Layer 3 - Backend Database:
  └─ Server-side backup, disaster recovery
  └─ Survives: Client device loss/destruction

Flow:
1. User saves inspection form
2. Immediately write to IndexedDB ✓
3. Show success toast to user ✓
4. Attempt API sync (fire-and-forget) ↓
5. If online: Sync succeeds, mark as SYNCED
6. If offline: Auto-retry when online (eventually consistent)
7. If user closes app: Inspection stays in IndexedDB
8. On next app open: Resume sync

Guarantee:
- Zero inspections lost from IndexedDB crash
- Zero inspections lost from power failure (IndexedDB survives)
- All pending syncs retried indefinitely
- User can always see what's queued for sync
```

### 3.2 Offline-Occasional Support

```
Usage Pattern:
- 80% of time: Connected to WiFi
- 15% of time: Temporary outages (<5 minutes)
- 5% of time: Extended outages (>5 minutes)

Requirements:
- App fully functional during ANY outage duration
- All data captured in IndexedDB
- Automatic resume when online
- User gets clear feedback on sync status

Sync Strategy:
- Attempt 1: Immediate
- Attempt 2: 5 seconds later (if failed)
- Attempt 3: 10 seconds later
- Attempt 4: 30 seconds later
- Attempt 5: 60 seconds later
  └─ After 5 failures (165 seconds = 2.75 min): Stop auto-retry
  └─ User sees "Sync Failed" + "Retry Now" button
  └─ Manual retries available indefinitely

Exponential backoff: [5, 10, 30, 60, 60] seconds
Total wait time: ~165 seconds (worst case)
Max retries: 5 automatic, unlimited manual
```

### 3.3 Uptime & Error Recovery

```
Expected Availability:
- Browser app: 99.9%+ (Service Worker fallback)
- Photo validation: 99%+ (CPU-intensive but fast)
- API sync: 95%+ (depends on server)
- IndexedDB: 99.99%+ (browser feature)

Error Handling:
- Network error → Exponential backoff + manual retry
- Validation error (e.g., defect not found) → Show error, require fix
- Server error (500) → Retry with backoff
- Storage error (quota exceeded) → Prompt user to clear old data
- Permission error (403) → Redirect to login

Recovery:
- Failed sync: Inspect error message, fix offline, retry
- Corrupted photo: Show checksum mismatch, retake photo
- Lost token: Auto-logout, re-login, app state restored from IndexedDB
```

---

## 4️⃣ USABILITY REQUIREMENTS

### 4.1 Multi-Role UI

```
Three user profiles in same app:

1. OPERARIO (Factory Floor Worker)
   - Motivation: Capture defects quickly
   - Tech level: Low
   - Screen space: Small phone
   - Interaction: Big buttons, minimal text
   
   Features visible:
   ├─ Inspection form (lote, defect, comment, photo)
   ├─ History (my inspections only)
   └─ Sync status indicator
   
   Hidden from:
   ├─ Masters management
   ├─ Approval queue
   └─ Admin settings

2. SUPERVISOR (Jefe QA / Supervisor)
   - Motivation: Review quality, approve/reject
   - Tech level: Moderate
   - Screen space: Medium-large phone or tablet
   - Interaction: Detailed forms, tables, decision UX
   
   Features visible:
   ├─ Inspection form (same as operario)
   ├─ Approval queue (pending inspections)
   ├─ Approval history (my decisions)
   ├─ Reports (defects by type, defects by operator)
   └─ Masters list (read-only)
   
   Hidden from:
   ├─ User management
   ├─ System config

3. ADMIN (System Administrator)
   - Motivation: Configure system, manage data
   - Tech level: High
   - Screen space: Full app
   - Interaction: Advanced forms, bulk operations
   
   Features visible:
   ├─ All of above (operario + supervisor features)
   ├─ Masters management (CRUD defects, machines, fabrics)
   ├─ CSV import/export
   ├─ User management
   ├─ System logs & audit trail
   └─ Integration settings (ERP connection)

Implementation:
- Route-based: <PrivateRoute requiredRole="OPERARIO" />
- Component-level: {canViewApprovals && <ApprovalQueue />}
- Menu-based: Hide menu items by role
```

### 4.2 Form UX & Validation Feedback

```
Inspection Capture Form:
├─ Lote search: Auto-complete, scan barcode, dropdown
├─ Photo capture: Camera button, instant validation feedback
│  ├─ Green checkmark if quality passes
│  ├─ Yellow warning if blurry but usable
│  └─ Red X if quality fails (retake required)
├─ Defect selection: Dropdown (only ACTIVE defects)
├─ Machine: Auto-filled, editable override
├─ Comment: Textarea with char counter (10/500)
└─ [Save] button: Disabled until all validations pass

Validation Feedback:
- Real-time (as user types/selects)
- Color-coded: Green (valid), Yellow (warning), Red (error)
- Clear messages: "Photo is blurry, steady your hand"
- No technical jargon
```

### 4.3 Error Messages & Accessibility

```
Error Messages: Spanish, clear, actionable
❌ "Defect not found" → ❌ "El tipo de defecto seleccionado no existe. Recargue la página."
❌ "Network error" → ❌ "Sin conexión a internet. Los datos se guardarán localmente."
❌ "Validation failed" → ❌ "El comentario debe tener al menos 10 caracteres."

Accessibility (WCAG 2.1 AA):
- Color not only indicator: Use icons + text + color
- Touch targets: Min 48x48px for buttons
- Font size: Min 14px for body text
- Contrast: 4.5:1 for text
- Keyboard navigation: All features accessible via Tab + Enter
- Screen reader: Semantic HTML, aria-labels for icons
```

---

## 5️⃣ MAINTAINABILITY REQUIREMENTS

### 5.1 Code Quality Standards

```
Target Audience: 2-3 member internal IT team (long-term ownership)

Code Style:
- TypeScript strict mode (no 'any')
- ESLint + Prettier auto-formatting
- Functional components (no class components)
- Custom hooks for reusable logic
- Zustand for state (not Redux)

Naming Conventions:
- Components: PascalCase (InspectionForm, PhotoCapture)
- Functions: camelCase (capturePhoto, validateDefect)
- Constants: UPPER_SNAKE_CASE (MAX_PHOTO_SIZE)
- Files: kebab-case (inspection-form.tsx, photo-validator.ts)

File Structure:
src/
├── components/         # React UI components
├── hooks/             # Custom React hooks
├── stores/            # Zustand stores (aggregates)
├── services/          # Domain services (photo validation, sync)
├── utils/             # Helper functions
├── types/             # TypeScript type definitions
├── constants/         # App constants
└── pages/             # Page-level components
```

### 5.2 Documentation Requirements

```
Code-Level Documentation:
- JSDoc comments for functions (what, why, not just what)
- Type annotations (no 'any')
- Clear variable names (no abbreviations)

Project Documentation:
README.md
├─ Setup instructions (npm install, npm run dev)
├─ Environment variables (.env.example)
├─ Tech stack overview
├─ Folder structure explanation

docs/ARCHITECTURE.md
├─ DDD design (bounded contexts, aggregates)
├─ State management (Zustand stores)
├─ Offline-first design
├─ Photo validation algorithm

docs/SETUP.md
├─ Local development setup
├─ Database initialization
├─ Common issues & fixes

docs/DEPLOYMENT.md
├─ Build process
├─ Docker setup
├─ Deployment checklist
```

### 5.3 Testing Strategy

```
Test Coverage Target: >70% (key business logic 100%)

Unit Tests (Jest):
- Photo validation logic (Laplacian variance calculation)
- Form validation rules
- Zustand store logic
- Domain service methods
- Utility functions

Integration Tests (Cypress/Playwright):
- Inspection capture flow (offline → online)
- Approval workflow
- Masters management
- Sync queue behavior

E2E Tests (Optional but recommended):
- Full user journey: Login → Capture → Submit → Sync
- Critical paths only (not every feature)

Pre-commit Hooks (Husky):
- Run linting
- Run type check
- Run unit tests
- Fail if any check fails
```

---

## 6️⃣ SCALABILITY REQUIREMENTS

### 6.1 Current Capacity (Small)

```
Expected Users: 10-20 concurrent
Expected Data: ~100 inspections/day
Expected Photos: ~500-1000 photos/day

Client Capacity:
- Device storage: 1-2 GB available (phone has 32-64 GB)
- IndexedDB: 50-100MB soft limit (plenty of room)
- Memory: 500-1000 inspections in memory (not a problem)

Server Capacity:
- Database: PostgreSQL (handles millions of records easily)
- API: FastAPI (handles thousands of req/sec)
- Storage: 100GB available for photos
- Cost: Minimal (single server sufficient)

Performance Impact:
- Page load: Still <1s
- Sync batch: 50-100 items per sync
- List rendering: 100-200 inspections per page
```

### 6.2 Future Scalability (Prepared)

```
If grows to 50+ users OR 500+ inspections/day:

Potential Bottlenecks:
- IndexedDB size (currently OK, but design for 1000+ inspections)
- API response time (add pagination, filtering)
- Photo storage (currently <100GB, but design for growth)
- List rendering performance (virtualize long lists)

Recommendations for Future:
- Implement list virtualization (react-window)
- Add server-side pagination to inspection list
- Archive old inspections (>30 days) to cold storage
- Consider CDN for photo delivery
- Implement server-side filtering (not client-side)

Current Actions:
- Don't pre-optimize (current scale doesn't need it)
- But code should be modular (easy to add optimization later)
- Avoid hardcoded limits (use constants)
```

---

## 7️⃣ MULTIMEDIA HANDLING (HIGH VOLUME PHOTOS)

### 7.1 Photo Capture & Compression

```
Requirements:
- Capture 5-10 high-quality photos per inspection
- Each photo: 2-4 MB raw (camera default)
- Constraint: IndexedDB soft limit 50MB total, Service Worker cache 100MB

Strategy:

Step 1: Capture
├─ Native camera API captures photo
├─ User sees preview (full resolution)
└─ Estimate size: ~3MB per photo

Step 2: Client-Side Compression
├─ Convert to JPEG (not PNG, which is 2-3x larger)
├─ Compression quality: 80% (good balance quality/size)
├─ Resize: Max 1920x1440 (typical phone resolution)
├─ Target size: 400-600KB per photo
└─ Compression time: <1 second per photo

Step 3: Calculate Checksum
├─ SHA256 hash of compressed bytes
├─ Used for: Integrity check, duplicate detection
└─ Computation: ~100ms

Step 4: Store Locally
├─ Save to IndexedDB (Dexie blob store)
├─ Also cache in Service Worker (for retry)
└─ Space used: 400KB × 10 photos = 4MB per inspection

Step 5: Sync to Server
├─ Batch: 5 photos per API call (to avoid timeout)
├─ Upload: Base64-encoded in JSON (alternative: multipart/form-data)
├─ Retry: Up to 5 attempts with exponential backoff
└─ Time estimate: ~5-10 seconds total for 10 photos
```

### 7.2 Storage Optimization

```
Device Storage Estimate:
- 1 inspection = ~10 photos × 500KB = 5MB
- 100 inspections (1 day) = 500MB
- 7 days = 3.5GB (typical phone has 32-64GB)
- Acceptable: Synced photos can be deleted after 7 days (server has backup)

Implementation:
- Delete photos from IndexedDB after sync confirmed (7 day grace period)
- Keep metadata indefinitely (small, needed for audit trail)
- Offer "Clear Cache" button to free up space
- Warn user if storage <10% available
```

---

## 8️⃣ DEVICE COMPATIBILITY (3-5 YEAR OLD SMARTPHONES)

### 8.1 Target Devices

```
Baseline: iPhone 8 (2017), Samsung Galaxy S5 (2014)
- CPU: Dual-core 1.5-2.5 GHz (older, slower)
- RAM: 2-3 GB (moderate memory pressure)
- Storage: 32-64 GB (some phones very full)
- OS: iOS 12+ (iPhone 6), Android 5+ (Samsung)
- Network: 4G LTE, WiFi 802.11ac

Performance Implications:
- Avoid heavy animations (60fps only)
- Avoid excessive re-renders in React
- Keep JS bundles <200KB (parse time matters)
- Canvas operations (photo validation) may take 300-500ms (OK, not blocking)
- Photo capture/compression slower on old phones (acceptable)
```

### 8.2 Compatibility Testing

```
Required:
- Test on iPhone 8 or later
- Test on Samsung Galaxy S5 or later
- Test on Android 5+ emulator
- Test on 4G network (not just WiFi)

Performance Thresholds:
- Page load: <2s on iPhone 8 (not <1s)
- Photo validation: <600ms on Galaxy S5 (not <200ms)
- Bundle size: <200KB (strict)
- CSS layout shifts: <0.1 CLS (visual stability)
```

---

## 9️⃣ ERP/MES INTEGRATION

### 9.1 Integration Points

```
CRITICAL: Must sync with manufacturing ERP/MES system

Integration Requirements:
1. Defect Masters
   ├─ Pull: List of active defects from ERP weekly
   ├─ Push: New defects created in app → to ERP
   └─ Conflict: ERP is source of truth (app can only add, not delete)

2. Lote/Work Order Reference
   ├─ Pull: Lote details from ERP (ID, fabric type, quantity, status)
   ├─ Validation: Can only inspect PENDING lotes
   └─ Push: Inspection completed → update ERP lote status

3. Inspection Results
   ├─ Push: All inspections → to ERP (for downstream processing)
   ├─ Format: JSON REST API + CSV export (for legacy compatibility)
   └─ Frequency: Real-time (on sync) + nightly batch

4. Machine References
   ├─ Pull: List of active machines from ERP
   ├─ Immutable: Cannot create machines in app (read-only)
   └─ Validation: Photo defect must match machine in ERP

API Spec (to be detailed later):
- Endpoint: https://erp.company.local/api/inspections
- Auth: OAuth2 (or API key)
- Rate limit: 100 req/sec
- Retry: 5 attempts with backoff
```

### 9.2 Data Sync Architecture

```
Flow:
App → IndexedDB (immediate) ✓
App → Sync Queue (fire-and-forget) ↓
Service Worker → API /api/inspections/sync ↓
↓
Backend → ERP Integration Service ↓
ERP Integration Service → ERP REST API ↓
ERP → Update manufacturing records ✓

Failure Handling:
- App API succeeds but ERP fails: Log in backend, retry nightly
- App offline: Sync queued locally, sent when online
- ERP unavailable: Backend queues for retry, doesn't block user
```

---

## ✅ SUMMARY TABLE

| NFR Attribute | Target | Measurement | Implementation |
|---|---|---|---|
| **Performance** | <1s page load | Core Web Vitals | <150KB JS, lazy loading |
| **Security** | Basic + HTTPS | OWASP compliance | JWT + RBAC + CORS |
| **Reliability** | 100% data durability | Zero inspections lost | IndexedDB + Service Worker |
| **Usability** | Multi-role UI | 3 user profiles | Role-based routing + feature flags |
| **Maintainability** | Clean code, documented | Team of 2-3 | TypeScript strict, tests >70% |
| **Scalability** | Small (10-20 users) | Horizontal capacity | Modular code, no premature optimization |
| **Offline** | Occasional support | Intermittent outages | IndexedDB queue + exponential backoff |
| **Multimedia** | 5-10 high-quality photos | JPEG 80% compression | Service Worker caching |
| **Devices** | 3-5 year old phones | iPhone 8+, Galaxy S5+ | <200KB bundle, 60fps animations |
| **Integration** | ERP/MES critical | Real-time + batch | REST API + nightly sync |

---

**Status**: ✅ NFR REQUIREMENTS COMPLETE (USER-ELICITED)  
**Next Step**: Activity 3 — NFR Design (Architecture Decision Records for implementing these NFRs)
