/**
 * Offline Store — Zustand
 * Manages sync queue, network status, and offline synchronization
 */

import { create } from 'zustand'
import { SyncQueueItem, NetworkStatus, SyncStatus, SyncOperationType, QueueStatus } from '../types'

export interface OfflineState {
  // State
  sync_queue: SyncQueueItem[]
  network_status: NetworkStatus
  is_syncing: boolean
  last_sync_time: string | null
  sync_errors: Record<string, string>

  // Actions
  setNetworkStatus: (status: NetworkStatus) => void
  enqueueOperation: (operation: SyncOperationType, payload: any) => void
  dequeueOperation: (item_id: string) => void
  startSync: () => Promise<void>
  retryFailed: () => Promise<void>
  setSyncStatus: (item_id: string, status: SyncStatus, error?: string) => void
  removeSyncedItems: () => void
  clearErrors: () => void

  // Selectors
  getPendingCount: () => number
  getFailedCount: () => number
  getSyncingCount: () => number
  getQueueStatus: () => QueueStatus
  hasFailedItems: () => boolean
}

export const useOfflineStore = create<OfflineState>((set, get) => ({
  sync_queue: [],
  network_status: navigator.onLine ? NetworkStatus.ONLINE : NetworkStatus.OFFLINE,
  is_syncing: false,
  last_sync_time: null,
  sync_errors: {},

  setNetworkStatus: (status: NetworkStatus) => {
    set({ network_status: status })

    // Auto-sync when coming online
    if (status === NetworkStatus.ONLINE) {
      get().startSync()
    }
  },

  enqueueOperation: (operation: SyncOperationType, payload: any) => {
    const now = new Date().toISOString()
    const item: SyncQueueItem = {
      id: `${operation}-${Date.now()}`,
      operation,
      payload,
      retry_count: 0,
      status: SyncStatus.PENDING,
      enqueued_at: now,
    }

    set((state) => ({
      sync_queue: [...state.sync_queue, item],
    }))
  },

  dequeueOperation: (item_id: string) => {
    set((state) => ({
      sync_queue: state.sync_queue.filter((item) => item.id !== item_id),
    }))
  },

  startSync: async () => {
    const state = get()
    const pending = state.sync_queue.filter((item) => item.status === SyncStatus.PENDING)

    if (pending.length === 0 || state.is_syncing) {
      return
    }

    set({ is_syncing: true })

    for (const item of pending) {
      try {
        set((state) => ({
          sync_queue: state.sync_queue.map((i) =>
            i.id === item.id ? { ...i, status: SyncStatus.SYNCING } : i,
          ),
        }))

        // Simulate API call
        await new Promise((resolve) => setTimeout(resolve, 1000))

        set((state) => ({
          sync_queue: state.sync_queue.map((i) =>
            i.id === item.id
              ? {
                  ...i,
                  status: SyncStatus.SYNCED,
                  retry_count: 0,
                }
              : i,
          ),
          last_sync_time: new Date().toISOString(),
          sync_errors: { ...state.sync_errors, [item.id]: undefined },
        }))
      } catch (err) {
        const error_msg = err instanceof Error ? err.message : 'Sync failed'
        const nextRetry = item.retry_count < 5

        set((state) => ({
          sync_queue: state.sync_queue.map((i) =>
            i.id === item.id
              ? {
                  ...i,
                  status: nextRetry ? SyncStatus.PENDING : SyncStatus.FAILED,
                  retry_count: i.retry_count + 1,
                  last_error: error_msg,
                }
              : i,
          ),
          sync_errors: {
            ...state.sync_errors,
            [item.id]: error_msg,
          },
        }))

        if (!nextRetry) {
          console.error(`Sync failed for ${item.id} after 5 retries`, error_msg)
        }
      }
    }

    set({ is_syncing: false })
  },

  retryFailed: async () => {
    const state = get()
    const failed = state.sync_queue.filter((item) => item.status === SyncStatus.FAILED)

    // Reset failed items to pending
    set((state) => ({
      sync_queue: state.sync_queue.map((item) =>
        failed.find((f) => f.id === item.id)
          ? {
              ...item,
              status: SyncStatus.PENDING,
              retry_count: 0,
              last_error: undefined,
            }
          : item,
      ),
      sync_errors: {},
    }))

    // Start sync again
    await get().startSync()
  },

  setSyncStatus: (item_id: string, status: SyncStatus, error?: string) => {
    set((state) => ({
      sync_queue: state.sync_queue.map((item) =>
        item.id === item_id
          ? {
              ...item,
              status,
              last_error: error,
              retry_count:
                status === SyncStatus.FAILED
                  ? item.retry_count + 1
                  : item.retry_count,
            }
          : item,
      ),
    }))
  },

  removeSyncedItems: () => {
    set((state) => ({
      sync_queue: state.sync_queue.filter((item) => item.status !== SyncStatus.SYNCED),
    }))
  },

  clearErrors: () => {
    set({ sync_errors: {} })
  },

  // Selectors
  getPendingCount: () => {
    return get().sync_queue.filter((item) => item.status === SyncStatus.PENDING).length
  },

  getFailedCount: () => {
    return get().sync_queue.filter((item) => item.status === SyncStatus.FAILED).length
  },

  getSyncingCount: () => {
    return get().sync_queue.filter((item) => item.status === SyncStatus.SYNCING).length
  },

  getQueueStatus: () => {
    const { sync_queue, last_sync_time } = get()
    return {
      pending: sync_queue.filter((i) => i.status === SyncStatus.PENDING).length,
      syncing: sync_queue.filter((i) => i.status === SyncStatus.SYNCING).length,
      synced: sync_queue.filter((i) => i.status === SyncStatus.SYNCED).length,
      failed: sync_queue.filter((i) => i.status === SyncStatus.FAILED).length,
      last_sync_time,
    }
  },

  hasFailedItems: () => {
    return get().sync_queue.some((item) => item.status === SyncStatus.FAILED)
  },
}))

// Setup network listeners
if (typeof window !== 'undefined') {
  window.addEventListener('online', () => {
    useOfflineStore.setState({ network_status: NetworkStatus.ONLINE })
    useOfflineStore.getState().startSync()
  })

  window.addEventListener('offline', () => {
    useOfflineStore.setState({ network_status: NetworkStatus.OFFLINE })
  })
}

// Hook for component usage
export const useOfflineSync = () => {
  const store = useOfflineStore()
  const status = store.getQueueStatus()

  return {
    network_status: store.network_status,
    is_syncing: store.is_syncing,
    pending_count: status.pending,
    failed_count: status.failed,
    synced_count: status.synced,
    last_sync_time: status.last_sync_time,
    has_failed: store.hasFailedItems(),
    startSync: store.startSync,
    retryFailed: store.retryFailed,
    setNetworkStatus: store.setNetworkStatus,
  }
}
