// frontend/stores/offlineStore.ts
// Zustand store for offline-first sync management

import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import type {
  SyncQueueItem,
  ConflictRecord,
  NetworkStatus,
  SyncQueueStatus,
  SyncStatus,
  OperationType,
  NetworkQuality,
  ResolutionStrategy,
} from '../types/sync'

interface OfflineStore {
  // State
  syncQueue: SyncQueueItem[]
  conflicts: ConflictRecord[]
  network: NetworkStatus
  isSyncing: boolean
  lastSyncTime?: Date

  // Queue actions
  addQueueItem: (item: Omit<SyncQueueItem, 'id' | 'created_at' | 'status'>) => string
  updateQueueItem: (id: string, updates: Partial<SyncQueueItem>) => void
  removeQueueItem: (id: string) => void
  clearQueue: () => void
  getQueueItems: (status?: SyncStatus) => SyncQueueItem[]

  // Conflict actions
  addConflict: (conflict: ConflictRecord) => void
  updateConflict: (id: string, resolution: ResolutionStrategy) => void
  removeConflict: (id: string) => void
  getConflicts: () => ConflictRecord[]

  // Network actions
  setNetworkStatus: (status: Partial<NetworkStatus>) => void
  setOnline: (online: boolean) => void

  // Sync actions
  startSync: () => void
  endSync: () => void

  // Computed
  queueStatus: () => SyncQueueStatus
  getPendingCount: () => number
  getConflictCount: () => number
}

const calculateQueueStatus = (queue: SyncQueueItem[]): SyncQueueStatus => ({
  total: queue.length,
  pending: queue.filter((i) => i.status === 'PENDING').length,
  syncing: queue.filter((i) => i.status === 'SYNCING').length,
  synced: queue.filter((i) => i.status === 'SYNCED').length,
  conflicts: queue.filter((i) => i.status === 'CONFLICT').length,
  failed: queue.filter((i) => i.status === 'FAILED').length,
  dead_letter: queue.filter((i) => i.status === 'DEAD_LETTER').length,
})

export const useOfflineStore = create<OfflineStore>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        syncQueue: [],
        conflicts: [],
        network: {
          is_online: typeof navigator !== 'undefined' ? navigator.onLine : true,
          quality: 'GOOD' as NetworkQuality,
          latency_ms: 0,
          packet_loss_pct: 0,
          last_check: new Date(),
        },
        isSyncing: false,

        // Queue actions
        addQueueItem: (item) => {
          const id = crypto.randomUUID()
          const queueItem: SyncQueueItem = {
            ...item,
            id,
            status: 'PENDING',
            retry_count: 0,
            created_at: new Date(),
          }

          set((state) => ({
            syncQueue: [...state.syncQueue, queueItem],
          }))

          // Persist to IndexedDB
          void persistToIDB('sync_queue', queueItem)
          return id
        },

        updateQueueItem: (id, updates) => {
          set((state) => ({
            syncQueue: state.syncQueue.map((item) =>
              item.id === id ? { ...item, ...updates } : item
            ),
          }))

          void updateInIDB('sync_queue', id, updates)
        },

        removeQueueItem: (id) => {
          set((state) => ({
            syncQueue: state.syncQueue.filter((item) => item.id !== id),
          }))

          void deleteFromIDB('sync_queue', id)
        },

        clearQueue: () => {
          set({ syncQueue: [] })
          void clearIDB('sync_queue')
        },

        getQueueItems: (status?: SyncStatus) => {
          const queue = get().syncQueue
          return status ? queue.filter((item) => item.status === status) : queue
        },

        // Conflict actions
        addConflict: (conflict) => {
          set((state) => ({
            conflicts: [...state.conflicts, conflict],
          }))

          void persistToIDB('conflicts', conflict)
        },

        updateConflict: (id, resolution) => {
          set((state) => ({
            conflicts: state.conflicts.map((c) =>
              c.id === id ? { ...c, resolution_strategy: resolution, resolved_at: new Date() } : c
            ),
          }))

          void updateInIDB('conflicts', id, { resolution_strategy: resolution, resolved_at: new Date() })
        },

        removeConflict: (id) => {
          set((state) => ({
            conflicts: state.conflicts.filter((c) => c.id !== id),
          }))

          void deleteFromIDB('conflicts', id)
        },

        getConflicts: () => get().conflicts,

        // Network actions
        setNetworkStatus: (status) => {
          set((state) => ({
            network: {
              ...state.network,
              ...status,
              last_check: new Date(),
            },
          }))
        },

        setOnline: (online) => {
          set((state) => ({
            network: { ...state.network, is_online: online },
          }))

          if (online) {
            triggerSync()
          }
        },

        // Sync actions
        startSync: () => set({ isSyncing: true }),
        endSync: () => set({ isSyncing: false, lastSyncTime: new Date() }),

        // Computed
        queueStatus: () => calculateQueueStatus(get().syncQueue),

        getPendingCount: () =>
          get().syncQueue.filter((i) => i.status === 'PENDING' || i.status === 'RETRY_PENDING')
            .length,

        getConflictCount: () => get().conflicts.length,
      }),
      {
        name: 'offline-store',
        partialize: (state) => ({
          syncQueue: state.syncQueue,
          conflicts: state.conflicts,
        }),
      }
    )
  )
)

// ==================== INDEXEDDB INTEGRATION ====================

async function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open('aidlc-offline', 1)
    req.onerror = () => reject(req.error)
    req.onsuccess = () => resolve(req.result)
    req.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result
      if (!db.objectStoreNames.contains('sync_queue')) {
        db.createObjectStore('sync_queue', { keyPath: 'id' })
      }
      if (!db.objectStoreNames.contains('conflicts')) {
        db.createObjectStore('conflicts', { keyPath: 'id' })
      }
    }
  })
}

async function persistToIDB(store: string, item: unknown): Promise<void> {
  try {
    const db = await openDB()
    const tx = db.transaction(store, 'readwrite')
    await tx.objectStore(store).put(item)
  } catch (error) {
    console.error(`Failed to persist to IDB (${store}):`, error)
  }
}

async function updateInIDB(store: string, id: string, updates: unknown): Promise<void> {
  try {
    const db = await openDB()
    const tx = db.transaction(store, 'readwrite')
    const obj = await tx.objectStore(store).get(id)
    if (obj) {
      await tx.objectStore(store).put({ ...obj, ...updates })
    }
  } catch (error) {
    console.error(`Failed to update in IDB (${store}):`, error)
  }
}

async function deleteFromIDB(store: string, id: string): Promise<void> {
  try {
    const db = await openDB()
    const tx = db.transaction(store, 'readwrite')
    await tx.objectStore(store).delete(id)
  } catch (error) {
    console.error(`Failed to delete from IDB (${store}):`, error)
  }
}

async function clearIDB(store: string): Promise<void> {
  try {
    const db = await openDB()
    const tx = db.transaction(store, 'readwrite')
    await tx.objectStore(store).clear()
  } catch (error) {
    console.error(`Failed to clear IDB (${store}):`, error)
  }
}

// ==================== NETWORK LISTENERS ====================

if (typeof window !== 'undefined') {
  window.addEventListener('online', () => {
    useOfflineStore.getState().setOnline(true)
  })

  window.addEventListener('offline', () => {
    useOfflineStore.getState().setOnline(false)
  })
}

// ==================== UTILITIES ====================

export function triggerSync(): void {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.controller?.postMessage({ type: 'START_SYNC' })
  }
}

export function getQueueStatus(): SyncQueueStatus {
  return useOfflineStore.getState().queueStatus()
}

export function getNetworkStatus(): NetworkStatus {
  return useOfflineStore.getState().network
}
