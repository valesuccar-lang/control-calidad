# ADR-003: Offline Storage with IndexedDB + Service Worker

**Date**: 2026-05-31  
**Status**: ACCEPTED  
**Context**: Frontend Web Unit — Zero data loss guarantee + offline-first sync  
**Decision Makers**: Frontend Team

---

## 📋 PROBLEM STATEMENT

**Requirement**: ZERO data loss tolerance
- Inspections captured offline must survive app crash, power loss, browser close
- Photos must be stored locally and synced when online
- Sync must auto-retry with exponential backoff
- Must work on older devices (2-3GB RAM, limited storage)

Storage options:
- **localStorage**: Max 5MB, blocks main thread, no structured data
- **WebSQL**: Deprecated
- **IndexedDB**: Async, large capacity (50MB+), proper transactions
- **Service Worker Cache**: For assets and photos, not structured data

---

## 🎯 DECISION

**Use IndexedDB + Service Worker + Dexie.js wrapper**

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

---

## 🏗️ IMPLEMENTATION DETAILS

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
      // Schema: ++ = auto-increment, & = unique, * = multi-valued
      inspections: '++id, loteId, status, syncStatus, createdAt',
      photos: '++id, inspectionId',
      syncQueue: '++id, operation, status, enqueuedAt',
      masters: '++id, type, status'  // type = DEFECT, MACHINE, FABRIC
    })
  }
}

export const db = new TextileQCDb()

// Size estimate:
// - 1 inspection: ~500 bytes (text + metadata)
// - 10 photos × 500KB: 5MB per inspection
// - 100 inspections: 500MB (mostly photos)
// Device storage: 32-64 GB, plenty of room
// IndexedDB soft limit: 50MB per domain (can request more)
```

### Auto-Save to IndexedDB

```typescript
// stores/inspection.store.ts
import { useShallow } from 'zustand/react'
import { db } from '../db'

export const useInspectionStore = create<InspectionStore>((set, get) => {
  // Subscribe to state changes, auto-save to IndexedDB
  const unsubscribe = useInspectionStore.subscribe(
    useShallow((state) => state.inspections),
    async (inspections) => {
      // Save to IndexedDB asynchronously
      try {
        for (const [id, inspection] of Object.entries(inspections)) {
          await db.inspections.put({
            ...inspection,
            updatedAt: new Date().toISOString()
          })
        }
      } catch (err) {
        console.error('Failed to save to IndexedDB:', err)
        // Don't fail user operation, just log
      }
    }
  )
  
  return {
    // ... store definition
  }
})

// On photos added
addPhoto: async (inspectionId, photoBlob) => {
  // Validate quality
  const metrics = await photoValidationService.validate(photoBlob)
  
  // Save photo blob to IndexedDB
  await db.photos.add({
    id: uuid(),
    inspectionId,
    blob: photoBlob,
    metadata: metrics
  })
  
  // Update inspection state
  set((state) => ({
    inspections: {
      ...state.inspections,
      [inspectionId]: {
        ...state.inspections[inspectionId],
        photos: [...state.inspections[inspectionId].photos, metrics]
      }
    }
  }))
}
```

### Service Worker + Sync Queue

```typescript
// service-worker.ts
import { db } from './db'

// Listen for online event
self.addEventListener('online', async () => {
  console.log('[SW] Device online, starting sync')
  await syncPendingItems()
})

// Periodic sync (every 30 seconds when online)
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
    // Update status to SYNCING
    await db.syncQueue.update(item.id, {
      status: 'SYNCING'
    })

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
    await db.syncQueue.update(item.id, {
      status: 'SYNCED'
    })

    // Update inspection syncStatus in local DB
    await db.inspections.update(item.payload.id, {
      syncStatus: 'SYNCED'
    })

    console.log(`[SW] Synced inspection ${item.payload.id}`)

  } catch (err) {
    console.error(`[SW] Sync failed for ${item.id}:`, err)

    // Exponential backoff
    const delays = [5000, 10000, 30000, 60000, 60000] // 5s, 10s, 30s, 60s, 60s
    const nextDelay = delays[item.retryCount] || 60000

    if (item.retryCount < 5) {
      // Schedule retry
      await db.syncQueue.update(item.id, {
        status: 'PENDING',
        retryCount: item.retryCount + 1,
        lastError: err.message
      })

      // Retry after delay (or on next online event)
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

      // Notify user (postMessage to React)
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

// Helper: Convert Blob to Base64
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
// components/SyncStatusIndicator.tsx
import { useEffect, useState } from 'react'
import { useOfflineStore } from '../stores/offline.store'

export const SyncStatusIndicator = () => {
  const [syncMessage, setSyncMessage] = useState<string>('')
  const { networkStatus, getPendingCount, getFailedCount } = useOfflineStore()
  const pending = getPendingCount()
  const failed = getFailedCount()

  useEffect(() => {
    // Listen for Service Worker messages
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

---

## ✅ BENEFITS

1. **Zero Data Loss**: IndexedDB persists across power loss, app crash
2. **Offline-First**: Full app functionality without network
3. **Automatic Sync**: Service Worker handles background sync
4. **Transparent to User**: Sync happens silently, no UI blocking
5. **Conflict-Free**: Sync is append-only (inspections never modified)
6. **Large Capacity**: Can store 500MB+ (photos) safely

---

## ⚠️ TRADEOFFS

1. **Complexity**: Service Worker + IndexedDB requires careful management
   - Mitigation: Use Dexie.js wrapper, abstract away details
   
2. **Storage Cleanup**: Large photos accumulate over time
   - Mitigation: Auto-delete synced photos older than 7 days

3. **Network Timing**: Can't guarantee exactly when sync happens
   - Mitigation: Accept eventual consistency, user can force retry

---

## 🧹 STORAGE CLEANUP POLICY

```typescript
// maintenance-worker.ts
// Run monthly cleanup
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

---

**Status**: ✅ ACCEPTED  
**Implementation**: Dexie.js + Service Worker for background sync + exponential backoff  
**Testing**: IndexedDB hydration tests, sync retry tests, Service Worker tests, offline scenario tests
