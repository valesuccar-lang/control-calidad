# ADR-002: State Management with Zustand Aggregates

**Date**: 2026-05-31  
**Status**: ACCEPTED  
**Context**: Frontend Web Unit — Lightweight state management for DDD aggregates  
**Decision Makers**: Frontend Team

---

## 📋 PROBLEM STATEMENT

The app has complex state (inspections, approvals, masters, auth, offline queue) that must:
1. Follow Domain-Driven Design (aggregates, value objects)
2. Support offline-first with sync queue
3. Be maintainable by 2-3 developers
4. Work on devices with 2-3GB RAM

Options considered:
- Redux (powerful but boilerplate-heavy)
- Context API (too complex for this scale)
- **Zustand** (lightweight, minimal boilerplate)
- Jotai (atom-based, overkill for this app)

---

## 🎯 DECISION

**Use Zustand for state management, implementing 5 aggregates as separate stores:**

```
Zustand Store = DDD Aggregate
├── Auth Store (User, tokens, role-based access)
├── Inspection Store (Inspections, photos, drafts)
├── Approval Store (Pending approvals, decisions)
├── Masters Store (Defects, machines, fabrics cache)
└── Offline Store (Sync queue, network status)
```

---

## 🏗️ IMPLEMENTATION DETAILS

### Store Architecture

```typescript
// stores/auth.store.ts
import { create } from 'zustand'

interface User {
  id: string
  email: string
  name: string
  role: 'OPERARIO' | 'SUPERVISOR' | 'ADMIN'
}

interface AuthStore {
  // State
  user: User | null
  isAuthenticated: boolean
  accessToken: string | null
  isLoading: boolean
  error: string | null
  
  // Actions
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
  },
  
  // ... other actions
}))

// ✅ Usage in components
function LoginForm() {
  const { login, isLoading, error } = useAuthStore()
  
  const handleLogin = async (email, password) => {
    await login(email, password)
  }
  
  return (
    <form onSubmit={(e) => {
      e.preventDefault()
      handleLogin(...)
    }}>
      {error && <Error>{error}</Error>}
      <button disabled={isLoading}>Sign In</button>
    </form>
  )
}
```

### Inspection Store (Complex Aggregate)

```typescript
// stores/inspection.store.ts
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
  // State (DDD Aggregate)
  inspections: Record<string, Inspection>
  currentInspectionId: string | null
  loading: boolean
  error: string | null
  
  // Actions (Domain Logic)
  createInspection: (loteId: string) => Promise<void>
  addPhoto: (inspectionId: string, photo: Photo) => Promise<void>
  updateComment: (inspectionId: string, comment: string) => void
  submitInspection: (inspectionId: string) => Promise<void>
  
  // Selectors (Computed)
  getCurrentInspection: () => Inspection | null
  getPendingPhotos: () => number
  canSubmit: () => boolean
}

export const useInspectionStore = create<InspectionStore>((set, get) => ({
  inspections: {},
  currentInspectionId: null,
  loading: false,
  error: null,
  
  createInspection: async (loteId) => {
    const newId = uuid()
    set((state) => ({
      inspections: {
        ...state.inspections,
        [newId]: {
          id: newId,
          loteId,
          defectId: '',
          comment: '',
          photos: [],
          machineId: '',
          status: 'DRAFT',
          syncStatus: 'PENDING',
          createdAt: new Date().toISOString(),
        }
      },
      currentInspectionId: newId
    }))
  },
  
  addPhoto: async (inspectionId, photo) => {
    // Validate photo quality
    const validation = await photoValidationService.validate(photo)
    
    set((state) => ({
      inspections: {
        ...state.inspections,
        [inspectionId]: {
          ...state.inspections[inspectionId],
          photos: [...state.inspections[inspectionId].photos, photo]
        }
      }
    }))
  },
  
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
  
  // Selectors
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
// stores/offline.store.ts
interface SyncQueueItem {
  id: string
  operation: 'CREATE_INSPECTION' | 'APPROVE' | 'REJECT'
  payload: any
  retryCount: number
  lastError: string | null
  status: 'PENDING' | 'SYNCING' | 'SYNCED' | 'FAILED'
}

interface OfflineStore {
  // State
  syncQueue: SyncQueueItem[]
  networkStatus: 'ONLINE' | 'OFFLINE' | 'POOR_CONNECTION'
  lastSyncTime: string | null
  
  // Actions
  enqueueOperation: (operation: SyncQueueItem['operation'], payload: any) => void
  startSync: () => Promise<void>
  retrySync: (itemId: string) => Promise<void>
  setNetworkStatus: (status: OfflineStore['networkStatus']) => void
  
  // Selectors
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
  
  startSync: async () => {
    const { syncQueue } = get()
    const pending = syncQueue.filter((item) => item.status === 'PENDING')
    
    for (const item of pending) {
      try {
        set((state) => ({
          syncQueue: state.syncQueue.map((i) =>
            i.id === item.id ? { ...i, status: 'SYNCING' } : i
          )
        }))
        
        // Call API
        await api.post('/api/sync', item.payload)
        
        // Mark as synced
        set((state) => ({
          syncQueue: state.syncQueue.map((i) =>
            i.id === item.id ? { ...i, status: 'SYNCED' } : i
          ),
          lastSyncTime: new Date().toISOString()
        }))
        
      } catch (err) {
        // Retry logic
        const nextRetry = item.retryCount < 5
        set((state) => ({
          syncQueue: state.syncQueue.map((i) =>
            i.id === item.id
              ? {
                  ...i,
                  status: nextRetry ? 'PENDING' : 'FAILED',
                  retryCount: i.retryCount + 1,
                  lastError: err.message
                }
              : i
          )
        }))
      }
    }
  },
  
  getPendingCount: () => {
    return get().syncQueue.filter((i) => i.status === 'PENDING').length
  },
  
  getFailedCount: () => {
    return get().syncQueue.filter((i) => i.status === 'FAILED').length
  },
  
  isSyncing: () => {
    return get().syncQueue.some((i) => i.status === 'SYNCING')
  }
}))
```

### Store Composition (Using Multiple Stores)

```typescript
// hooks/useInspection.ts
// High-level hook combining multiple stores
export const useInspection = () => {
  const auth = useAuthStore()
  const inspection = useInspectionStore()
  const offline = useOfflineStore()
  
  const handleSubmitInspection = async () => {
    if (!auth.isAuthenticated) {
      return  // Redirect to login
    }
    
    const currentInsp = inspection.getCurrentInspection()
    if (!currentInsp) return
    
    try {
      // Save locally (offline guarantee)
      await inspection.submitInspection(currentInsp.id)
      
      // Queue for sync
      offline.enqueueOperation('CREATE_INSPECTION', currentInsp)
      
      // If online, start sync immediately
      if (offline.networkStatus === 'ONLINE') {
        offline.startSync()
      }
      
    } catch (err) {
      inspection.setError(err.message)
    }
  }
  
  return {
    currentInspection: inspection.getCurrentInspection(),
    canSubmit: inspection.canSubmit(),
    onSubmit: handleSubmitInspection,
    syncStatus: offline.networkStatus,
    pendingCount: offline.getPendingCount()
  }
}
```

---

## ✅ BENEFITS

1. **Lightweight**: ~10KB minified, minimal dependencies
2. **Familiar**: Redux-like but simpler API
3. **TypeScript-Friendly**: Full type inference
4. **Offline-Ready**: Stores can be hydrated from IndexedDB
5. **Performance**: No unnecessary re-renders (subscriptions are fine-grained)
6. **DDD-Aligned**: Stores map to aggregates naturally

---

## ⚠️ TRADEOFFS

1. **No Built-in DevTools**: Redux DevTools integration requires extra setup
   - Mitigation: Use browser DevTools + console logging
   
2. **No Built-in Middleware**: Thunks/effects handled differently than Redux
   - Mitigation: Use async functions directly in actions
   
3. **No Undo/Redo**: Redux has plugins for this
   - Mitigation: Not needed for this app (inspections are append-only)

---

## 🔄 INTEGRATION WITH OFFLINE

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
  (state) => state.inspections,
  (inspections) => inspectionDb.saveAll(inspections)
)

useOfflineStore.subscribe(
  (state) => state.syncQueue,
  (queue) => queueDb.saveAll(queue)
)
```

---

**Status**: ✅ ACCEPTED  
**Implementation**: Zustand with 5 separate stores, each representing a DDD aggregate  
**Testing**: Store action tests, selector tests, offline hydration tests
