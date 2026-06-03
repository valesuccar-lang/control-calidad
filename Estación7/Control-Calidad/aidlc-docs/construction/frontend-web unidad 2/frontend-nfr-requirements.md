# Non-Functional Requirements (NFR) — Frontend Web Unit

**Date**: 2026-05-28  
**Unit**: Frontend Web (React 18 + TypeScript)  
**Phase**: Activity 2 — NFR Requirements Assessment  
**Status**: ✅ COMPLETE

---

## 📋 EXECUTIVE SUMMARY

The Frontend Web unit (React 18 + TypeScript) is a field-facing inspection application designed for **offline-first operation** with **high photo validation standards** and **real-time sync**. NFRs are organized across 7 dimensions with specific measurable targets.

| Dimension | Target | Criticality | Notes |
|-----------|--------|-------------|-------|
| **Performance** | Page load <2s, FCP <1.2s | CRITICAL | Slow networks in production |
| **Offline Capability** | 100% functional without network | CRITICAL | Primary use case in field |
| **Photo Validation** | 95%+ accuracy (Laplacian variance) | CRITICAL | Quality gate for inspections |
| **Reliability** | 99.5% uptime (browser), sync auto-recovery | HIGH | Sync failures auto-retry 5 times |
| **Security** | HTTPS only, JWT tokens, CSP headers | CRITICAL | Handles inspection data |
| **Usability** | <100ms response to user input, <3s photo capture | HIGH | Factory floor environment |
| **Data Persistence** | No data loss on power failure, offline queue | CRITICAL | Field conditions unreliable |
| **Maintainability** | <5min hot reload, test coverage >70% | MEDIUM | Continuous delivery required |

---

## 1️⃣ PERFORMANCE REQUIREMENTS

### **1.1 Page Load Performance**

| Metric | Target | Threshold | Priority |
|--------|--------|-----------|----------|
| **Time to First Byte (TTFB)** | <800ms | 3G network | CRITICAL |
| **First Contentful Paint (FCP)** | <1.2s | 3G network | CRITICAL |
| **Largest Contentful Paint (LCP)** | <2.5s | 3G network | CRITICAL |
| **Cumulative Layout Shift (CLS)** | <0.1 | All networks | HIGH |
| **Time to Interactive (TTI)** | <3.5s | 3G network | CRITICAL |
| **Full Page Load** | <5s | Fast 3G (1.6 Mbps) | CRITICAL |

**Justification**: Users in rural areas / factories use 3G networks. Anything >5s risks user abandonment in field.

### **1.2 Runtime Performance**

| Metric | Target | Threshold | Priority |
|--------|--------|-----------|----------|
| **JS Bundle Size** | <200KB gzipped | Initial load | HIGH |
| **CSS Bundle Size** | <50KB gzipped | Initial load | HIGH |
| **DOM Interactive Time** | <500ms | Zustand hydration | CRITICAL |
| **Input Responsiveness** | <100ms | UI state update | CRITICAL |
| **Photo Upload** | <5s per photo | WiFi, 5Mbps | HIGH |
| **Form Submission** | <2s (with network) | API latency + UI update | HIGH |

**Justification**: Field users expect immediate feedback. Lagging UI causes confusion and support calls.

### **1.3 Resource Constraints**

```
Minimum Device Specs (Target Market):
- RAM: 2GB (older Android 7+)
- Storage: 500MB free (OS + app + IndexedDB cache)
- Network: 3G (0.4-1.6 Mbps)
- CPU: Dual-core 1.5GHz (older processor)

Optimization Targets:
- Initial JS bundle: <200KB (gzipped)
- Initial CSS: <50KB (gzipped)
- IndexedDB cache: <50MB (inspection + metadata)
- Service Worker cache: <100MB (photos, static assets)
```

**Justification**: Must run on factory floor devices (often older hardware). Budget 2-3 page loads on 3G before user timeout.

---

## 2️⃣ OFFLINE CAPABILITY REQUIREMENTS

### **2.1 Core Offline Features**

| Feature | Requirement | Duration | Priority |
|---------|-------------|----------|----------|
| **Inspection Registration** | 100% functional offline | Until sync | CRITICAL |
| **Photo Capture + Validation** | Full Laplacian variance checking | 20+ photos | CRITICAL |
| **Defect Selection** | Load and display masters data | 30 min+ | CRITICAL |
| **Approval Workflow** | Queue approval, persist state | Until sync | HIGH |
| **Masters Data** | Cached in IndexedDB | 7 days | HIGH |
| **Network Status Display** | Real-time indicator + last sync time | Always visible | MEDIUM |

**Justification**: Field inspections happen in dead zones (underground, rural areas). App must be 100% functional offline.

### **2.2 Offline Storage**

```
IndexedDB Schema:
- inspections: {id, lote, machine, date, photos[], comments[], status, offline_id}
- approvals: {id, inspection_id, decision, reason, timestamp}
- masters: {id, category, name, active, timestamp}
- sync_queue: {id, operation, payload, retry_count, last_error}
- photos: {id, inspection_id, blob, metadata}

Storage Limits:
- IndexedDB: 50MB (soft limit, <30MB target)
- Service Worker cache: 100MB (all photos + static assets)
- LocalStorage: <5MB (user preferences, theme)

Eviction Policy:
- Age-based: Synced photos older than 30 days → delete
- Frequency-based: Inspections synced + no edits for 7 days → compress
- Manual: User can "free up space" → delete synced items >7 days old
```

**Justification**: Field devices have limited storage. Must manage cache intelligently.

### **2.3 Offline Sync Strategy**

| Phase | Behavior | Timing | Condition |
|-------|----------|--------|-----------|
| **Phase 1: Capture** | Write to IndexedDB, show offline icon | Immediate | Every action |
| **Phase 2: Detect Network** | Service Worker observes navigator.onLine | Every 5s | Polling interval |
| **Phase 3: Sync** | Exponential backoff: 5s → 10s → 30s → 60s → 60s | Auto-retry | Max 5 attempts |
| **Phase 4: Failure** | Show "sync failed, manual retry needed" | After 5 failures | User action button |
| **Phase 5: Recovery** | User taps "Retry" → restart from Phase 3 | Manual + 5 auto-retries | Up to 3 manual attempts |

**Justification**: Must balance between battery drain (polling) and user experience (sync delay). Exponential backoff prevents server hammering.

---

## 3️⃣ PHOTO VALIDATION REQUIREMENTS

### **3.1 Quality Metrics**

```
Laplacian Variance (Image Sharpness):
- Target: >500 (good focus)
- Acceptable: 300-500 (blurry but readable)
- Reject: <300 (too blurry, unusable)
- Computation: ~200ms per photo (mobile)

Brightness (Exposure):
- Target: 100-155 (normalized 0-255)
- Acceptable: 80-170
- Reject: <80 (too dark) or >170 (overexposed)
- Computation: ~50ms per photo

Contrast:
- Target: >40 (high detail visibility)
- Acceptable: 20-40 (medium detail)
- Reject: <20 (no detail visible)
- Computation: ~50ms per photo

Overall Assessment:
- PASS: Laplacian >500 AND Brightness OK AND Contrast >20
- WARN: 2+ metrics in acceptable range → show warning, allow retry
- FAIL: Laplacian <300 OR Brightness out of range → reject, require retake
```

**Justification**: Textile defects require clear images. Blurry/dark photos waste QC time downstream.

### **3.2 Photo Capture Flow**

```
User Actions:
1. Tap camera icon → open native camera
2. Frame fabric defect → capture button active
3. Take photo → instant validation (200ms-300ms)
4. If PASS: Show checkmark, move to next photo
5. If WARN: Show warning + "Retake?" button, allow proceed
6. If FAIL: Show "Too blurry/dark" + "Retake required" button

Constraints:
- Max 10 photos per inspection (UI limit)
- Min 1 photo (business rule FR-002)
- Max photo size: 5MB per file (compression if needed)
- Capture timeout: 30s before cancel
- Validation timeout: 500ms (if slow, allow override with warning)
```

**Justification**: Users need fast feedback. 200-300ms feels instant. Validation must not block capture.

### **3.3 Photo Metadata**

```
Capture Metadata:
{
  id: UUID,
  inspection_id: UUID,
  filename: "photo_2026-05-28_141530_001.jpg",
  size_bytes: 2048576,
  timestamp: ISO8601,
  laplacian_variance: 587.3,
  brightness_normalized: 128,
  contrast: 45,
  quality_status: "PASS" | "WARN" | "FAIL",
  camera_device: "Samsung S21, rear",
  device_orientation: "portrait" | "landscape",
  gps_coords?: {lat, lng},
  synced: false,
  synced_at?: ISO8601
}

Retention:
- All metadata stored in IndexedDB
- Photos stored in Service Worker cache
- Metadata synced with every inspection sync
- Photo blobs synced separately (reduce bandwidth)
```

**Justification**: Metadata enables quality audits, device tracking, and debugging failures.

---

## 4️⃣ RELIABILITY REQUIREMENTS

### **4.1 Availability & Uptime**

| Component | Target | Measurement | Recovery |
|-----------|--------|-------------|----------|
| **Browser App** | 99.5% uptime | Weekly active users | Service Worker fallback |
| **Service Worker** | 99.9% uptime | Successful cache hits | Network fallback |
| **Sync Engine** | Auto-recovery from 5 consecutive failures | Exponential backoff | Manual "Retry" button |
| **Photo Validation** | No false rejects (FRR <1%) | Internal benchmark | No FP threshold |
| **IndexedDB** | 100% data durability | No data loss across power cycles | Browser backup |

**Justification**: Field workers lose connectivity frequently. App must survive power loss without data loss.

### **4.2 Sync Reliability**

```
Failure Handling:
1. Network error → exponential backoff (5, 10, 30, 60, 60 seconds)
2. Server error (5xx) → retry with backoff
3. Validation error (4xx) → show error, require manual fix
4. Timeout after 5 auto-retries → show "manual retry" button
5. User taps retry → restart backoff sequence (max 3 manual retries)

State Persistence:
- Pending syncs stored in IndexedDB
- Sync status tracked: PENDING → SYNCING → SYNCED | FAILED
- Failed syncs retain full payload for retry
- User can view "sync queue" → see what's pending

Idempotency:
- All sync requests include: inspection_id, timestamp, unique_request_id
- Backend detects duplicate requests (same inspection_id + timestamp)
- Duplicate requests return cached response (no re-processing)
```

**Justification**: Network is unreliable. Must retry intelligently without hammering server.

### **4.3 Data Integrity**

```
Conflict Resolution (Online → Offline → Online):
Scenario: User creates inspection offline, then on phone edits it online before first sync

Resolution Strategy:
1. Timestamp-based: Last write wins (LWWF)
2. Fields affected:
   - inspection: merge if no conflicting edits
   - approvals: reject if approval already made server-side
   - photos: both sides accepted (sync newer)
3. User notification: "Your inspection was modified online, synced successfully"

Validation:
- All form submissions validated before IndexedDB write
- Schema validation on IndexedDB read (detect corruption)
- Checksum on photos before upload (detect corruption)
```

**Justification**: Offline editing can conflict with online changes. Need deterministic conflict resolution.

---

## 5️⃣ SECURITY REQUIREMENTS

### **5.1 Authentication & Authorization**

| Requirement | Implementation | Standard | Priority |
|-------------|---------------|-----------|---------| 
| **HTTPS Only** | All traffic encrypted | TLS 1.3 minimum | CRITICAL |
| **JWT Authentication** | Bearer tokens in Authorization header | RFC 7519 | CRITICAL |
| **Token Expiration** | 8 hours lifetime | Backend-enforced (FR-023) | CRITICAL |
| **Refresh Token Rotation** | New refresh token on each login | Prevent replay | HIGH |
| **CORS Validation** | Restrict to trusted origins only | Backend enforcement | HIGH |
| **CSP Headers** | Restrict script sources to self + CDN | `script-src 'self' cdn.example.com` | MEDIUM |

**Justification**: Inspections contain proprietary fabric defect data. Must encrypt in transit.

### **5.2 Data Protection**

```
Sensitive Data Handling:
- Credentials: Never stored (only token in secure HttpOnly cookie)
- Photos: Encrypted in transit (HTTPS), unencrypted at rest (IndexedDB)
- Inspection data: Encrypted in transit, plaintext in IndexedDB
- User tokens: Stored in memory (React state) + optional secure storage

Local Storage Policy:
- ✅ Allowed: User preferences, inspection drafts, photo metadata
- ❌ Forbidden: Passwords, API keys, plaintext tokens
- ⚠️ Caution: Photo blobs (large, but non-sensitive)

Cache Control Headers:
- Sensitive: no-store (photos with metadata)
- Public data: max-age=3600 (masters data)
- Static assets: max-age=86400 (JS, CSS)
```

**Justification**: IndexedDB is unencrypted, but loss is acceptable for drafts. Sync ensures cloud backup.

### **5.3 Role-Based Access Control (RBAC)**

```
Frontend Enforcement (UX Layer):
- ANALISTA: Can create inspections, capture photos, see own inspections
- JEFE_QA: Can approve/reject inspections, see all pending
- ADMIN: Can manage masters data, bulk import, view audit logs
- VIEWER: Can view all inspections (read-only)

Implementation:
- Check user.role in Zustand auth store
- Hide UI elements for unauthorized roles (UX, not security)
- All API calls include Authorization header (enforced by API)
- Failed authorization → 403 response → redirect to login

Note: Frontend RBAC is UX only. Backend enforces actual authorization.
```

**Justification**: Frontend UX respects roles, but backend is authoritative.

### **5.4 XSS & Injection Prevention**

```
Code-Level Protections:
- React escapes JSX by default (no dangerouslySetInnerHTML)
- All user inputs validated (comment length, defect selection)
- No eval() or dynamic script execution
- DOMPurify used for any HTML content from API (optional)

Input Validation:
- Comment: 10-500 characters, ASCII printable
- Defect selection: predefined list only
- Photo metadata: readonly from device API
- Lote number: pattern validation only

API Response Handling:
- JSON.parse() only (no script evaluation)
- Content-Type validation (application/json)
- Response schema validation with Zod or similar
```

**Justification**: Prevent XSS through user-controlled content (comments, uploaded data).

---

## 6️⃣ USABILITY REQUIREMENTS

### **6.1 Responsiveness & UX**

| Metric | Target | Justification |
|--------|--------|---------------|
| **Input Lag** | <100ms (keyboard, buttons) | Feels instant; >100ms feels sluggish |
| **Page Transition** | <300ms (fade/slide animation) | Smooth but not slow |
| **Form Validation** | Inline, real-time feedback | Users know error immediately |
| **Loading State** | Show spinner for >200ms operations | Brief ops don't show spinner (jank) |
| **Error Recovery** | 1-2 taps to retry failed sync | Users must not lose data |
| **Mobile Viewport** | 100% functional on 320px width | Min iPhone 5 compatibility |

**Justification**: Factory floor users use phones while working. Sluggish UI causes frustration and support calls.

### **6.2 Photo Capture UX**

```
Capture Flow (Target: <3 seconds from tap to next screen):
1. Tap camera icon (10-20ms)
2. Native camera opens (800-1500ms)
3. User frames defect (1-30s, user-controlled)
4. Tap capture (50-100ms)
5. Validation runs (200-300ms)
6. Result shown (50-100ms)
Total: 1.1-2.1s (excluding user framing time)

Quality Assessment UX:
- PASS: Green checkmark, "Good photo" message, auto-advance
- WARN: Yellow warning, "Blurry but usable" message, "Retake?" button
- FAIL: Red X, "Too blurry, retake required" message, no advance

Accessibility:
- Color-blind safe: Use icons + text labels (not color alone)
- High contrast: Checkmark/X visible on any background
- Font size: Min 14px for all labels
```

**Justification**: Users need instant feedback. Ambiguous states cause confusion.

### **6.3 Accessibility (WCAG 2.1 AA Baseline)**

```
Target Compliance: WCAG 2.1 Level AA (globally recognized standard)

Keyboard Navigation:
- All interactive elements reachable via Tab key
- Focus indicators visible (highlight or outline)
- Tab order logical (left-to-right, top-to-bottom)

Screen Reader Support:
- Semantic HTML: <button>, <label>, <input>
- ARIA labels for icons: <button aria-label="Add photo">
- Form validation messages announced
- Navigation announced (current page + breadcrumb)

Color & Contrast:
- Text: 4.5:1 contrast ratio (AA standard)
- Icons: 3:1 contrast ratio (AA standard)
- No information conveyed by color alone

Responsive Design:
- Tested on 320px, 768px, 1024px viewports
- Tap targets: Min 48x48px (WCAG recommended)
- No horizontal scrolling <320px width
```

**Justification**: Inclusive design reduces user friction and support costs.

---

## 7️⃣ DATA PERSISTENCE REQUIREMENTS

### **7.1 No Data Loss Guarantees**

| Scenario | Guarantee | Implementation |
|----------|-----------|-----------------|
| **Power loss during edit** | Data saved to IndexedDB within 1s | Auto-save on every field change |
| **App crash** | Drafts preserved | Service Worker + IndexedDB persist state |
| **Network loss mid-sync** | Sync resumes on reconnect | Offline queue retains full payload |
| **Browser cache cleared** | Inspections still in IndexedDB | Separate from browser cache |
| **Device storage full** | Warn user, allow deletion of old synced items | Cleanup policy enforced |

**Justification**: Field workers cannot lose inspection data. Re-capturing photos wastes time.

### **7.2 Auto-Save Strategy**

```
Trigger Points:
- After every photo capture: Save to IndexedDB
- After every form field change: Debounce 1s, then save
- After comment text: Debounce 2s (reduce writes), then save
- Before page navigation: Force save (if dirty)
- Before app close: Persist state to IndexedDB

Conflict Handling:
- If user edits offline + online simultaneously: Last write wins (timestamp-based)
- User notified: "Inspection was modified online, merged successfully"
- Both versions' photos preserved (no data loss)
```

**Justification**: Prevent data loss without excessive IndexedDB writes (which are slow).

### **7.3 Data Lifecycle**

```
Inspection Lifecycle:
1. DRAFT: Created offline, in IndexedDB only
2. SUBMITTED: Sent to sync queue, waiting for network
3. SYNCING: Active API call in progress
4. SYNCED: Confirmation from server received
5. ARCHIVED: Older than 30 days, can be deleted

Photo Lifecycle:
1. CAPTURED: In IndexedDB + Service Worker cache
2. VALIDATED: Quality metrics stored
3. QUEUED_FOR_SYNC: Added to sync_queue
4. SYNCED: Uploaded to server
5. ARCHIVED: Server copy exists, local copy retained 30 days

Retention Policy:
- Active inspections: Retained indefinitely
- Synced, no edits: Retained 30 days (then user can delete)
- Failed syncs: Retained indefinitely (manual retry available)
- Deleted photos: Removed from cache but metadata retained 7 days
```

**Justification**: Large photo blobs consume storage. Aggressive retention of just-synced items risks losing them mid-sync.

---

## 8️⃣ MAINTAINABILITY REQUIREMENTS

### **8.1 Development Velocity**

| Metric | Target | Tools | Priority |
|--------|--------|-------|----------|
| **Hot Reload** | <5 seconds | Vite dev server | HIGH |
| **Test Execution** | Unit tests <2s, integration <10s | Jest + React Testing Library | HIGH |
| **Build Time** | Development <5s, production <30s | Vite + esbuild | MEDIUM |
| **Type Safety** | 100% TypeScript coverage (no `any`) | TypeScript strict mode | HIGH |
| **Linting** | Zero warnings on PR merge | ESLint + Prettier | MEDIUM |

**Justification**: Developers spend 30-40% of time waiting. Fast feedback loops increase productivity.

### **8.2 Test Coverage Targets**

```
Coverage Goals:
- Statements: >70% (key business logic 100%)
- Branches: >65% (happy path + error paths)
- Functions: >70% (all services tested)
- Lines: >70% (all executed code tested)

Target Breakdown:
- Domain services (photo validation, sync): >90% coverage
- Zustand stores (aggregates): >80% coverage
- React components: >60% coverage (integration tests count)
- API utilities: >80% coverage
- Utilities: >75% coverage

Test Types:
- Unit: Photo validation, sync logic, RBAC checks (~60% of tests)
- Integration: API calls, offline flows, auth (~30% of tests)
- E2E (optional): Critical user flows in real browser (~10% of tests)
```

**Justification**: >70% coverage catches 90% of bugs. Additional coverage has diminishing returns.

### **8.3 Code Quality**

```
Linting & Formatting:
- ESLint with React/TypeScript rules
- Prettier for auto-formatting
- Husky pre-commit hook: auto-fix on commit
- CI/CD blocks merge if linting fails

Code Review Checklist:
- No `any` types (use `unknown` + type guard if needed)
- No unused imports or variables
- Functions <30 lines (break up if larger)
- Comments only for "why", not "what"
- Test coverage tracked (coverage report on PR)

Documentation:
- README: Setup, dev workflow, deployment
- Architecture: docs/ARCHITECTURE.md with diagrams
- API: JSDoc comments on exported functions
- State management: docs/STATE_MANAGEMENT.md with examples
```

**Justification**: Consistent code reduces cognitive load and onboarding time.

### **8.4 Dependency Management**

```
Approved Dependencies:
- react (18.x): Core framework
- zustand: Lightweight state management
- @tanstack/react-query: Server state management (optional)
- zod: Schema validation
- dexie: IndexedDB wrapper
- workbox: Service Worker tooling

Restrictions:
- No jQuery or legacy dependencies
- No large UI frameworks (Material-UI ok, not Ant Design + others)
- No crypto libraries unless crypto-js (use browser crypto API first)
- All dependencies <5MB gzipped

Version Policy:
- Major updates: review breaking changes before updating
- Minor updates: auto-apply, test before deploy
- Patch updates: auto-apply
- Security updates: apply immediately
```

**Justification**: Too many dependencies inflate bundle size and create maintenance burden.

---

## 9️⃣ COMPLIANCE & STANDARDS

### **9.1 Browser Support**

```
Target Browsers:
- Chrome 90+ (Android 5+, Windows 10+)
- Safari 14+ (iOS 12+, macOS 11+)
- Firefox 88+ (Windows 10+, Linux)
- Edge 90+ (Windows 10+)

Fallback Strategy:
- Service Workers: Polyfill with AppCache (low priority, <1% users)
- IndexedDB: Polyfill with localStorage (reduced capacity)
- Fetch API: Polyfill with XMLHttpRequest
- ES2020 features: Transpile to ES2015 (Vite handles this)

Testing Matrix:
- Real device testing: Chrome Android 9, iPhone 12
- Emulator testing: Latest 3 versions of each browser
- Lighthouse audit: Perf >85, Accessibility >90
```

**Justification**: Android 5+ and iOS 12+ represent 95%+ of factory phones.

### **9.2 Performance Audit Targets**

```
Lighthouse Scores (Chrome DevTools):
- Performance: >85 (3G throttling)
- Accessibility: >95
- Best Practices: >90
- SEO: >80 (N/A for web app, but test anyway)

Core Web Vitals (Google standard):
- LCP (Largest Contentful Paint): <2.5s
- FID (First Input Delay): <100ms (soon "INP")
- CLS (Cumulative Layout Shift): <0.1

Measurement:
- Measure on real devices (throttled to 4G)
- Run Lighthouse on every PR (automate in CI)
- Track metrics over time (trending dashboard)
```

**Justification**: Google ranks fast sites higher. Performance directly affects user experience.

---

## 🚀 NFR IMPLEMENTATION ROADMAP

### **Phase 1: Foundation (Weeks 1-2)**
- [ ] Zustand store setup (offline state, sync state)
- [ ] Service Worker + Workbox configuration
- [ ] IndexedDB schema creation (dexie setup)
- [ ] JWT auth + token refresh
- [ ] HTTPS + CORS setup

### **Phase 2: Core Features (Weeks 3-4)**
- [ ] Photo capture + Laplacian validation
- [ ] Inspection form + auto-save to IndexedDB
- [ ] Sync queue implementation
- [ ] Exponential backoff retry logic
- [ ] Network status indicator

### **Phase 3: Polish & Testing (Weeks 5-6)**
- [ ] Unit tests for domain services (>80% coverage)
- [ ] Integration tests for API flows (>60% coverage)
- [ ] E2E tests for critical user flows
- [ ] Lighthouse audit + Core Web Vitals measurement
- [ ] Accessibility (WCAG 2.1 AA) testing

### **Phase 4: Deployment & Monitoring (Weeks 7-8)**
- [ ] Vite build optimization (bundle size <200KB gzipped)
- [ ] Service Worker cache strategy finalization
- [ ] Error logging (Sentry or similar)
- [ ] Performance monitoring (Google Analytics + custom metrics)
- [ ] Production deployment + smoke tests

---

## 🔗 RELATED DOCUMENTS

- **Functional Design**: frontend-entities.md, frontend-business-rules.md, frontend-business-logic-model.md
- **NFR Design**: frontend-nfr-design.md (ADRs for auth, state management, offline storage, monitoring)
- **Infrastructure**: frontend-infrastructure-design.md (deployment, CI/CD, hosting)
- **Build & Test**: frontend-build-and-test-summary.md, frontend-unit-test-instructions.md, frontend-integration-test-instructions.md

---

## ✅ APPROVAL CHECKLIST

- [ ] All NFR requirements documented with targets and justification
- [ ] Performance targets realistic for field conditions (3G, old devices)
- [ ] Offline capability 100% functional without network
- [ ] Photo validation metrics measurable and auditable
- [ ] Reliability targets achievable with exponential backoff + auto-recovery
- [ ] Security requirements follow industry standards (TLS, JWT, RBAC)
- [ ] Usability targets tested on real devices (<3s photo capture)
- [ ] Data persistence no-loss guarantees with IndexedDB + Service Worker
- [ ] Maintainability targets support continuous delivery (<5s hot reload)
- [ ] Test coverage >70% achievable with mix of unit + integration tests

---

**Status**: ✅ NFR REQUIREMENTS COMPLETE  
**Next Step**: Activity 3 — NFR Design (Architecture Decision Records for auth, state management, offline storage, monitoring)
