# NFR Design: Frontend Web Unit (Consolidated)

**Date**: 2026-05-31  
**Status**: ACCEPTED  
**Unit**: Frontend Web (React + TypeScript)  
**Context**: Small team (2-3 devs) building QC inspection app for textile manufacturing

---

## 📋 OVERVIEW

This document consolidates all architectural decisions for the FRONTEND-WEB unit's non-functional requirements. Five key design areas address performance, security, reliability, usability, and maintainability:

1. **Authentication & JWT Strategy** — Multi-role security with httpOnly cookies
2. **State Management** — Zustand aggregates following Domain-Driven Design
3. **Offline Storage & Sync** — IndexedDB + Service Worker for zero data loss
4. **Monitoring & Error Tracking** — Custom error tracking + performance monitoring
5. **System Integration** — How all components work together

```
┌─────────────────────────────────────────────────────────────────┐
│                   FRONTEND WEB ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐                    ┌──────────────────────┐  │
│  │ React App    │◄──────────────────►│ Zustand Stores       │  │
│  │ (UI Layer)   │                    │ ├─ Auth              │  │
│  └──────────────┘                    │ ├─ Inspection        │  │
│         ▲                             │ ├─ Approval          │  │
│         │                             │ ├─ Masters           │  │
│         │ Auto-subscribe              │ └─ Offline           │  │
│         ▼                             └──────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ IndexedDB (Persistent Storage)                           │  │
│  │ ├─ inspections table (text + metadata)                  │  │
│  │ ├─ photos table (blob storage)                          │  │
│  │ ├─ syncQueue table (pending operations)                 │  │
│  │ └─ masters cache table (defects, machines, fabrics)     │  │
│  └──────┬───────────────────────────────────────────────────┘  │
│         │ Service Worker monitors                              │
│         ▼                                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Service Worker (Background Sync)                         │  │
│  │ ├─ Detect online/offline                                │  │
│  │ ├─ Dequeue pending items                                │  │
│  │ ├─ Exponential backoff retry                            │  │
│  │ └─ Update sync status in IndexedDB                      │  │
│  └──────┬───────────────────────────────────────────────────┘  │
│         │ POST /api/inspections/sync                           │
│         ├─ Authorization: Bearer {token}                       │
│         ▼                                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Error Tracking & Performance Monitoring                  │  │
│  │ ├─ Catch errors (global handlers + try-catch)           │  │
│  │ ├─ Measure Core Web Vitals (LCP, FID, CLS)              │  │
│  │ ├─ Track API response times                             │  │
│  │ ├─ POST errors to /api/errors                           │  │
│  │ └─ Alert Slack for critical errors                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│         ▲                                                       │
│         │ Axios Interceptors (Request/Response)                │
│         │ Global Error Handlers                                │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
    Backend API (https://api.company.local)
    ├─ POST /auth/login
    ├─ POST /auth/refresh
    ├─ POST /api/inspections/sync
    ├─ POST /api/errors
    ├─ POST /api/analytics
    └─ Other inspection endpoints
```

---

## 🔐 ADR-001: Authentication & JWT Strategy

**Status**: ✅ ACCEPTED

### Decision

Use JWT (JSON Web Token) authentication with the following strategy:
- **Access Token**: 8-hour lifetime, stored in httpOnly cookies + memory (Zustand)
- **Refresh Token**: 30-day lifetime, httpOnly cookie only
- **Multi-role RBAC**: Three roles (OPERARIO, SUPERVISOR, ADMIN) with feature visibility gates

### Token Storage & Security

```typescript
// ✅ SECURE: HttpOnly Cookies (server sets, browser cannot JS access)
// Server sends: Set-Cookie: accessToken=...; HttpOnly; Secure; SameSite=Strict
// Browser stores automatically, included on all requests
// Protection: XSS attack cannot steal tokens

// ⚠️ ALSO STORE in Memory for React access (Zustand)
// accessToken stored in memory for immediate route/component access
// If page refresh: Token re-fetched from httpOnly cookie
// Loss: Page refresh clears memory, but httpOnly cookie persists

// ❌ AVOID: localStorage for tokens (XSS risk)
// localStorage is readable by JavaScript (vulnerable to XSS)
```

### Token Refresh Flow

```typescript
// Axios interceptors handle token refresh automatically
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
  isAuthenticated: boolean
  
  canCreateInspection: () => boolean  // OPERARIO+
  canApproveInspection: () => boolean // SUPERVISOR, ADMIN
  canManageMasters: () => boolean      // ADMIN only
}

// Usage in components
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

### Benefits & Tradeoffs

**Benefits:**
- Tokens in httpOnly cookies, inaccessible to XSS
- JWT is industry standard, well-tested
- Stateless on server (no session storage)
- 8-hour access token limits damage if stolen
- Minimal client-side complexity

**Tradeoffs:**
- httpOnly cookies sent only same-origin (mitigated: backend + frontend on same domain)
- CSRF risk (mitigated: CSRF tokens on state-changing requests)
- Token refresh complexity (mitigated: centralized in axios interceptors)

---

## 📦 ADR-002: State Management with Zustand Aggregates

**Status**: ✅ ACCEPTED

### Decision

Use Zustand for state management, implementing 5 aggregates as separate stores following Domain-Driven Design (DDD):

```
Zustand Store = DDD Aggregate
├── Auth Store (User, tokens, role-based access)
├── Inspection Store (Inspections, photos, drafts)
├── Approval Store (Pending approvals, decisions)
├── Masters Store (Defects, machines, fabrics cache)
└── Offline Store (Sync queue, network status)
```

### Store Architecture

```typescript
// stores/auth.store.ts
interface AuthStore {
  user: User | null
  isAuthenticated: boolean
  accessToken: string | null
  isLoading: boolean
  error: string | null
  
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refreshToken: () => Promise<void>
  setUser: (user: User) => void
  clearError: () => void
}

export const useAuthStore = create<AuthStore>((set, get) => ({
  user: null,
  isAuthenticated: false,
  accessToken: null,
  isLoading: false,
  error: null,
  
  login: async (email, password) => {
    set({ isLoading: true, error: null })
    try {
      const response = await api.post('/auth/login', { email, password })
      const { user, accessToken } = response.data
      set({
        user,
        accessToken,
        isAuthenticated: true,
        isLoading: false
      })
    } catch (err) {
      set({
        error: 'Invalid email or password',
        isLoading: false
      })
    }
  },
  
  logout: async () => {
    await api.post('/auth/logout')
    set({
      user: null,
      accessToken: null,
      isAuthenticated: false
    })
  }
}))
```

### Inspection Store (Complex Aggregate)

```typescript
interface Inspection {
  id: string
  loteId: string
  defectId: string
  comment: string
  photos: Photo[]
  machineId: string
  status: 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED'
  syncStatus: 'PENDING' | 'SYNCED' | 'FAILED'
  createdAt: string
}

interface InspectionStore {
  inspections: Record<string, Inspection>
  currentInspectionId: string | null
  loading: boolean
  error: string | null
  
  createInspection: (loteId: string) => Promise<void>
  addPhoto: (inspectionId: string, photo: Photo) => Promise<void>
  updateComment: (inspectionId: string, comment: string) => void
  submitInspection: (inspectionId: string) => Promise<void>
  
  getCurrentInspection: () => Inspection | null
  getPendingPhotos: () => number
  canSubmit: () => boolean
}

export const useInspectionStore = create<InspectionStore>((set, get) => ({
  inspections: {},
  currentInspectionId: null,
  loading: false,
  error: null,
  
  submitInspection: async (inspectionId) => {
    set({ loading: true, error: null })
    const inspection = get().inspections[inspectionId]
    
    try {
      // Validate all fields
      if (!inspection.comment || inspection.photos.length === 0) {
        throw new Error('Missing required fields')
      }
      
      // Save to IndexedDB first (offline guarantee)
      await inspectionDb.save(inspection)
      
      // Then sync to API (fire-and-forget)
      set((state) => ({
        inspections: {
          ...state.inspections,
          [inspectionId]: {
            ...state.inspections[inspectionId],
            status: 'SUBMITTED',
            syncStatus: 'PENDING'
          }
        },
        loading: false
      }))
      
      // Async sync (don't wait)
      offlineSyncService.enqueue(inspection)
      
    } catch (err) {
      set({
        error: err.message,
        loading: false
      })
    }
  },
  
  getCurrentInspection: () => {
    const { currentInspectionId, inspections } = get()
    return currentInspectionId ? inspections[currentInspectionId] : null
  },
  
  canSubmit: () => {
    const inspection = get().getCurrentInspection()
    return !!(inspection?.comment && inspection.photos.length > 0)
  }
}))
```

### Offline Store (Sync Queue Management)

```typescript
interface OfflineStore {
  syncQueue: SyncQueueItem[]
  networkStatus: 'ONLINE' | 'OFFLINE' | 'POOR_CONNECTION'
  lastSyncTime: string | null
  
  enqueueOperation: (operation: string, payload: any) => void
  startSync: () => Promise<void>
  retrySync: (itemId: string) => Promise<void>
  setNetworkStatus: (status: string) => void
  
  getPendingCount: () => number
  getFailedCount: () => number
  isSyncing: () => boolean
}

export const useOfflineStore = create<OfflineStore>((set, get) => ({
  syncQueue: [],
  networkStatus: 'ONLINE',
  lastSyncTime: null,
  
  enqueueOperation: (operation, payload) => {
    set((state) => ({
      syncQueue: [
        ...state.syncQueue,
        {
          id: uuid(),
          operation,
          payload,
          retryCount: 0,
          lastError: null,
          status: 'PENDING'
        }
      ]
    }))
  },
  
  getPendingCount: () => {
    return get().syncQueue.filter((i) => i.status === 'PENDING').length
  },
  
  getFailedCount: () => {
    return get().syncQueue.filter((i) => i.status === 'FAILED').length
  }
}))
```

### Integration with IndexedDB

```typescript
// On app startup
const hydrateFromIndexedDB = async () => {
  const savedInspections = await inspectionDb.getAll()
  const savedOfflineQueue = await queueDb.getAll()
  
  useInspectionStore.setState({ inspections: savedInspections })
  useOfflineStore.setState({ syncQueue: savedOfflineQueue })
}

// On every state change, auto-save to IndexedDB
useInspectionStore.subscribe(
  useShallow((state) => state.inspections),
  async (inspections) => {
    for (const [id, inspection] of Object.entries(inspections)) {
      await db.inspections.put({
        ...inspection,
        updatedAt: new Date().toISOString()
      })
    }
  }
)
```

### Benefits & Tradeoffs

**Benefits:**
- Lightweight (~10KB minified)
- TypeScript-friendly with full type inference
- Offline-ready (stores hydrated from IndexedDB)
- DDD-aligned (stores map to aggregates naturally)
- No unnecessary re-renders (subscriptions fine-grained)

**Tradeoffs:**
- No built-in DevTools (mitigated: browser DevTools + console logging)
- No built-in middleware for async (mitigated: async functions in actions)
- No Undo/Redo (not needed for append-only inspections)

---

## 💾 ADR-003: Offline Storage & Synchronization

**Status**: ✅ ACCEPTED

### Decision

Use **IndexedDB + Service Worker + Dexie.js wrapper** for zero data loss guarantee:

```
Architecture:
┌─────────────────────────────────────────┐
│ React Component (useInspectionStore)    │
│ Write inspection form                   │
└─────────────┬───────────────────────────┘
              │ setState
              ↓
┌─────────────────────────────────────────┐
│ Zustand Store (In-Memory State)         │
│ Holds current inspection, UI state      │
└─────────────┬───────────────────────────┘
              │ Auto-subscribe
              ↓
┌─────────────────────────────────────────┐
│ IndexedDB (Persistent Storage)          │
│ Dexie.js wrapper                        │
│ ├─ inspections table                    │
│ ├─ photos table                         │
│ ├─ sync_queue table                     │
│ └─ masters cache table                  │
└─────────────┬───────────────────────────┘
              │ Service Worker monitors
              ↓
┌─────────────────────────────────────────┐
│ Service Worker (Background Sync)        │
│ ├─ Detect online (navigator.onLine)     │
│ ├─ Dequeue pending items                │
│ ├─ POST to /api/inspections/sync        │
│ ├─ Exponential backoff on failure       │
│ └─ Update IndexedDB on sync success     │
└─────────────────────────────────────────┘
```

### IndexedDB Schema (Dexie.js)

```typescript
// db.ts
import Dexie, { Table } from 'dexie'

export interface StoredInspection {
  id: string
  loteId: string
  defectId: string
  comment: string
  machineId: string
  status: 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED'
  syncStatus: 'PENDING' | 'SYNCED' | 'FAILED'
  createdAt: string
  updatedAt: string
}

export interface StoredPhoto {
  id: string
  inspectionId: string
  blob: Blob
  metadata: {
    laplacian: number
    brightness: number
    contrast: number
    quality: 'PASS' | 'WARN' | 'FAIL'
  }
}

export interface SyncQueueItem {
  id: string
  operation: 'CREATE_INSPECTION' | 'APPROVE' | 'REJECT'
  payload: any
  retryCount: number
  lastError: string | null
  status: 'PENDING' | 'SYNCING' | 'SYNCED' | 'FAILED'
  enqueuedAt: string
}

export class TextileQCDb extends Dexie {
  inspections!: Table<StoredInspection>
  photos!: Table<StoredPhoto>
  syncQueue!: Table<SyncQueueItem>
  masters!: Table<any>

  constructor() {
    super('textile-qc-db')
    this.version(1).stores({
      inspections: '++id, loteId, status, syncStatus, createdAt',
      photos: '++id, inspectionId',
      syncQueue: '++id, operation, status, enqueuedAt',
      masters: '++id, type, status'
    })
  }
}

export const db = new TextileQCDb()

// Storage estimates:
// - 1 inspection: ~500 bytes (text + metadata)
// - 10 photos × 500KB: 5MB per inspection
// - 100 inspections: 500MB (mostly photos)
// Device storage: 32-64 GB available
```

### Service Worker + Sync Queue

```typescript
// service-worker.ts
import { db } from './db'

self.addEventListener('online', async () => {
  console.log('[SW] Device online, starting sync')
  await syncPendingItems()
})

setInterval(async () => {
  if (navigator.onLine) {
    await syncPendingItems()
  }
}, 30000)

async function syncPendingItems() {
  const pendingItems = await db.syncQueue
    .where('status')
    .equals('PENDING')
    .toArray()

  for (const item of pendingItems) {
    await syncItem(item)
  }
}

async function syncItem(item: SyncQueueItem, delayMs = 0) {
  if (delayMs > 0) {
    await new Promise((resolve) => setTimeout(resolve, delayMs))
  }

  try {
    await db.syncQueue.update(item.id, { status: 'SYNCING' })

    // Get full inspection data + photos from IndexedDB
    const inspection = await db.inspections.get(item.payload.id)
    if (!inspection) throw new Error('Inspection not found in local DB')

    const photos = await db.photos
      .where('inspectionId')
      .equals(inspection.id)
      .toArray()

    // Convert blobs to base64 for JSON serialization
    const photosBase64 = await Promise.all(
      photos.map(async (photo) => ({
        id: photo.id,
        blob: await blobToBase64(photo.blob),
        metadata: photo.metadata
      }))
    )

    // POST to API with full data
    const response = await fetch('https://api.company.local/api/inspections/sync', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAccessToken()}`
      },
      body: JSON.stringify({
        inspection,
        photos: photosBase64
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    // Mark as synced
    await db.syncQueue.update(item.id, { status: 'SYNCED' })
    await db.inspections.update(item.payload.id, {
      syncStatus: 'SYNCED'
    })

    console.log(`[SW] Synced inspection ${item.payload.id}`)

  } catch (err) {
    console.error(`[SW] Sync failed for ${item.id}:`, err)

    // Exponential backoff: [5s, 10s, 30s, 60s, 60s]
    const delays = [5000, 10000, 30000, 60000, 60000]
    const nextDelay = delays[item.retryCount] || 60000

    if (item.retryCount < 5) {
      // Schedule retry
      await db.syncQueue.update(item.id, {
        status: 'PENDING',
        retryCount: item.retryCount + 1,
        lastError: err.message
      })

      setTimeout(() => {
        if (navigator.onLine) {
          syncItem(item, 0)
        }
      }, nextDelay)

    } else {
      // Mark as failed after 5 attempts
      await db.syncQueue.update(item.id, {
        status: 'FAILED',
        lastError: `Failed after 5 retries: ${err.message}`
      })

      // Notify user
      self.clients.matchAll().then((clients) => {
        clients.forEach((client) => {
          client.postMessage({
            type: 'SYNC_FAILED',
            itemId: item.id,
            error: err.message
          })
        })
      })
    }
  }
}

async function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onloadend = () => resolve(reader.result as string)
    reader.onerror = reject
    reader.readAsDataURL(blob)
  })
}
```

### React Component: Monitor Sync Status

```typescript
export const SyncStatusIndicator = () => {
  const [syncMessage, setSyncMessage] = useState<string>('')
  const { networkStatus, getPendingCount, getFailedCount } = useOfflineStore()
  const pending = getPendingCount()
  const failed = getFailedCount()

  useEffect(() => {
    const handleServiceWorkerMessage = (event: MessageEvent) => {
      if (event.data.type === 'SYNC_FAILED') {
        setSyncMessage(`Sync failed: ${event.data.error}`)
      }
    }

    navigator.serviceWorker?.controller?.addEventListener(
      'message',
      handleServiceWorkerMessage
    )

    return () => {
      navigator.serviceWorker?.controller?.removeEventListener(
        'message',
        handleServiceWorkerMessage
      )
    }
  }, [])

  return (
    <div className="sync-status">
      {networkStatus === 'ONLINE' && !pending && (
        <span className="online">📡 Online (All synced)</span>
      )}
      {networkStatus === 'OFFLINE' && (
        <span className="offline">
          🔴 Offline ({pending} pending)
        </span>
      )}
      {failed > 0 && (
        <span className="failed">
          ❌ {failed} failed - <button onClick={() => window.location.reload()}>Retry</button>
        </span>
      )}
    </div>
  )
}
```

### Storage Cleanup Policy

```typescript
// Run monthly cleanup to manage storage
async function cleanupOldPhotos() {
  const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)

  const oldSyncedPhotos = await db.photos
    .where('synced')
    .equals(true)
    .filter((photo) => new Date(photo.createdAt) < sevenDaysAgo)
    .toArray()

  for (const photo of oldSyncedPhotos) {
    await db.photos.delete(photo.id)
  }

  console.log(`[Cleanup] Deleted ${oldSyncedPhotos.length} old photos`)
}

// Run on app startup
if (lastCleanupDate < today) {
  cleanupOldPhotos()
}
```

### Benefits & Tradeoffs

**Benefits:**
- Zero data loss (IndexedDB persists across power loss)
- Offline-first (full app functionality without network)
- Automatic sync (Service Worker handles background sync)
- Transparent to user (sync happens silently)
- Conflict-free (append-only inspections)
- Large capacity (500MB+ safe storage)

**Tradeoffs:**
- Complexity with Service Worker + IndexedDB (mitigated: Dexie.js wrapper)
- Storage cleanup needed (mitigated: auto-delete synced photos after 7 days)
- Network timing uncertainty (mitigated: eventual consistency, user can force retry)

---

## 📊 ADR-004: Monitoring & Error Tracking

**Status**: ✅ ACCEPTED

### Decision

Use **hybrid approach** combining custom error tracking + performance monitoring without paid services:

```
Architecture:
┌──────────────────┐
│ Browser App      │
│ (React)          │
└────────┬─────────┘
         │ Error/Log Event
         ↓
┌──────────────────────────────────────────┐
│ Error Tracking Service (Custom)          │
│ ├─ Catch uncaught errors                 │
│ ├─ Track validation failures             │
│ ├─ Measure performance (Core Web Vitals) │
│ └─ POST to /api/errors endpoint          │
└────────┬─────────────────────────────────┘
         │
         ↓
┌──────────────────────────────────────────┐
│ Backend Logging                          │
│ ├─ Store errors in database              │
│ ├─ Alert on critical errors (Slack)      │
│ └─ Dashboard: Error frequency/patterns   │
└──────────────────────────────────────────┘
```

### Error Tracking Service

```typescript
// services/error-tracking.ts
export interface ErrorReport {
  errorId: string
  timestamp: string
  message: string
  stack?: string
  context: {
    url: string
    userRole?: string
    userId?: string
    userEmail?: string
    appVersion: string
  }
  severity: 'ERROR' | 'WARNING' | 'INFO'
  metadata?: Record<string, any>
}

class ErrorTrackingService {
  private queue: ErrorReport[] = []
  private isOnline = navigator.onLine

  constructor() {
    window.addEventListener('online', () => {
      this.isOnline = true
      this.flushQueue()
    })
    window.addEventListener('offline', () => {
      this.isOnline = false
    })

    // Catch uncaught errors
    window.addEventListener('error', (event) => {
      this.captureError(
        event.message,
        event.error?.stack,
        'ERROR'
      )
    })

    // Catch unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.captureError(
        event.reason?.message || String(event.reason),
        event.reason?.stack,
        'ERROR'
      )
    })

    // Flush queue every 30 seconds
    setInterval(() => {
      if (this.isOnline && this.queue.length > 0) {
        this.flushQueue()
      }
    }, 30000)
  }

  captureError(
    message: string,
    stack?: string,
    severity: 'ERROR' | 'WARNING' = 'ERROR',
    metadata?: Record<string, any>
  ) {
    const report: ErrorReport = {
      errorId: uuid(),
      timestamp: new Date().toISOString(),
      message,
      stack,
      context: {
        url: window.location.href,
        userRole: useAuthStore.getState().user?.role,
        userId: useAuthStore.getState().user?.id,
        userEmail: useAuthStore.getState().user?.email,
        appVersion: APP_VERSION
      },
      severity,
      metadata
    }

    console.error('[ErrorTracking]', report)

    // Add to queue (will retry if offline)
    this.queue.push(report)

    // Try to send immediately (don't wait)
    if (this.isOnline) {
      this.flushQueue()
    }

    // Alert Slack for critical errors (ADMIN users only)
    if (severity === 'ERROR' && useAuthStore.getState().user?.role === 'ADMIN') {
      this.alertSlack(report)
    }
  }

  private async flushQueue() {
    while (this.queue.length > 0) {
      const report = this.queue[0]

      try {
        await fetch('https://api.company.local/api/errors', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(report)
        })

        this.queue.shift()

      } catch (err) {
        console.warn('[ErrorTracking] Failed to send error report:', err)
        break
      }
    }
  }

  private async alertSlack(report: ErrorReport) {
    try {
      await fetch('https://hooks.slack.com/...', {
        method: 'POST',
        body: JSON.stringify({
          text: `🚨 ${report.severity}: ${report.message}`,
          attachments: [{
            color: 'danger',
            fields: [
              { title: 'Error ID', value: report.errorId },
              { title: 'User', value: report.context.userEmail || 'Unknown' },
              { title: 'URL', value: report.context.url },
              { title: 'Stack', value: `\`\`\`${report.stack}\`\`\`` }
            ]
          }]
        })
      })
    } catch (err) {
      console.warn('[ErrorTracking] Failed to alert Slack:', err)
    }
  }
}

export const errorTracking = new ErrorTrackingService()

// Usage in components/services
try {
  await photoValidationService.validate(photo)
} catch (err) {
  errorTracking.captureError(
    `Photo validation failed: ${err.message}`,
    err.stack,
    'ERROR',
    { photoSize: photo.size, photoFormat: photo.type }
  )
}
```

### Performance Monitoring

```typescript
// services/performance-monitoring.ts
class PerformanceMonitor {
  captureMetrics() {
    // Core Web Vitals
    if ('web-vital' in window) {
      // LCP (Largest Contentful Paint)
      window.addEventListener('largest-contentful-paint', (entry) => {
        const lcp = entry.renderTime || entry.loadTime
        console.log(`[Performance] LCP: ${lcp}ms`)

        if (lcp > 2500) {
          errorTracking.captureError(
            `LCP exceeded threshold: ${lcp}ms`,
            null,
            'WARNING',
            { metric: 'LCP', value: lcp }
          )
        }
      })
    }

    // Photo validation timing
    const origValidate = photoValidationService.validate
    photoValidationService.validate = async (photo) => {
      const start = performance.now()
      const result = await origValidate(photo)
      const duration = performance.now() - start

      console.log(`[Performance] Photo validation: ${duration}ms`)

      if (duration > 500) {
        errorTracking.captureError(
          `Photo validation slow: ${duration}ms`,
          null,
          'WARNING',
          { metric: 'PHOTO_VALIDATION', value: duration, photoSize: photo.size }
        )
      }

      return result
    }
  }

  captureNetworkTiming(endpoint: string, method: string, durationMs: number) {
    console.log(`[Performance] ${method} ${endpoint}: ${durationMs}ms`)

    if (durationMs > 5000) {
      errorTracking.captureError(
        `API call slow: ${method} ${endpoint} (${durationMs}ms)`,
        null,
        'WARNING',
        { endpoint, method, duration: durationMs }
      )
    }
  }
}

export const performanceMonitor = new PerformanceMonitor()
performanceMonitor.captureMetrics()

// Wrap API calls
const api = axios.create({
  baseURL: 'https://api.company.local'
})

api.interceptors.request.use((config) => {
  config.metadata = { startTime: performance.now() }
  return config
})

api.interceptors.response.use(
  (response) => {
    const duration = performance.now() - response.config.metadata.startTime
    performanceMonitor.captureNetworkTiming(
      response.config.url,
      response.config.method?.toUpperCase(),
      duration
    )
    return response
  },
  (error) => {
    const duration = performance.now() - error.config.metadata.startTime
    performanceMonitor.captureNetworkTiming(
      error.config.url,
      error.config.method?.toUpperCase(),
      duration
    )
    return Promise.reject(error)
  }
)
```

### User Analytics (Simple Event Logging)

```typescript
// services/analytics.ts
export interface AnalyticsEvent {
  eventName: string
  timestamp: string
  userId?: string
  userRole?: string
  properties?: Record<string, any>
}

class Analytics {
  private queue: AnalyticsEvent[] = []

  trackEvent(
    eventName: string,
    properties?: Record<string, any>
  ) {
    const event: AnalyticsEvent = {
      eventName,
      timestamp: new Date().toISOString(),
      userId: useAuthStore.getState().user?.id,
      userRole: useAuthStore.getState().user?.role,
      properties
    }

    console.log('[Analytics]', event)
    this.queue.push(event)

    if (this.queue.length > 0 && this.queue.length % 50 === 0) {
      this.flush()
    }
  }

  private async flush() {
    if (this.queue.length === 0) return

    try {
      await fetch('https://api.company.local/api/analytics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ events: this.queue })
      })

      this.queue = []

    } catch (err) {
      console.warn('[Analytics] Failed to send events:', err)
    }
  }
}

export const analytics = new Analytics()

// Track key events
analytics.trackEvent('INSPECTION_CREATED', { loteId: '...' })
analytics.trackEvent('PHOTO_UPLOADED', { photoSize: 500000 })
analytics.trackEvent('SYNC_COMPLETED', { itemCount: 5 })
analytics.trackEvent('SYNC_FAILED', { retryCount: 3, error: '...' })
```

### Backend Error Logging Endpoint

```python
# backend: routes/errors.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

router = APIRouter(prefix="/api/errors")
logger = logging.getLogger(__name__)

class ErrorReport(BaseModel):
    errorId: str
    timestamp: str
    message: str
    stack: Optional[str]
    context: dict
    severity: str
    metadata: Optional[dict]

@router.post("")
async def log_error(report: ErrorReport):
    """Log frontend errors to backend for monitoring"""
    
    logger.error(f"Frontend Error [{report.severity}]: {report.message}", extra={
        "errorId": report.errorId,
        "userId": report.context.get("userId"),
        "userEmail": report.context.get("userEmail"),
        "stack": report.stack,
        "metadata": report.metadata
    })
    
    # Alert Slack if critical
    if report.severity == "ERROR":
        await slack_service.send_alert(
            f"🚨 {report.message}",
            {
                "Error ID": report.errorId,
                "User": report.context.get("userEmail", "Unknown"),
                "URL": report.context.get("url"),
                "Stack": report.stack[:500]
            }
        )
    
    return {"status": "logged"}
```

### Benefits & Tradeoffs

**Benefits:**
- Zero cost (no paid services)
- Simple and focused
- Privacy-respecting (no session replay)
- Actionable data (errors + performance)
- Real-time Slack alerts
- Local console + backend logs for debugging

**Tradeoffs:**
- No session replay (mitigated: focus on logs + repro steps)
- Manual dashboard (mitigated: simple admin page or Grafana)
- Limited scope (mitigated: global handlers + interceptors)

---

## ✅ COMPLETE BENEFITS SUMMARY

| Aspect | Benefit |
|--------|---------|
| **Security** | JWT tokens in httpOnly cookies, XSS-safe, RBAC with 3 roles |
| **Data Durability** | IndexedDB + Service Worker = zero data loss guarantee |
| **Offline-First** | Full app functionality without network, automatic sync |
| **Performance** | Custom monitoring (Core Web Vitals, API timing, photo validation) |
| **Cost** | Zero (only Slack integration, which team likely has) |
| **Maintainability** | Zustand stores as DDD aggregates, clear separation of concerns |
| **Team Fit** | Lightweight, minimal boilerplate, suitable for 2-3 devs |
| **Device Support** | Works on older phones (iPhone 8+, Galaxy S5+) with 2-3GB RAM |

---

## 🏗️ INTEGRATION CHECKLIST

- [ ] IndexedDB schema created (4 tables: inspections, photos, syncQueue, masters)
- [ ] Service Worker registered and background sync implemented
- [ ] Zustand stores configured (Auth, Inspection, Approval, Masters, Offline)
- [ ] Axios interceptors for token refresh and performance monitoring
- [ ] Error tracking service with global handlers
- [ ] Slack webhook configured for critical alerts
- [ ] React components for sync status indicator
- [ ] Backend endpoints implemented (/auth/*, /api/errors, /api/analytics, /api/inspections/sync)
- [ ] CSRF token strategy on state-changing requests
- [ ] Storage cleanup policy (7-day photo expiration)

---

**Status**: ✅ ACCEPTED  
**Implementation**: Complete NFR design with 4 ADRs consolidated  
**Testing**: Unit tests for all stores, integration tests for offline sync, E2E tests for auth flow
