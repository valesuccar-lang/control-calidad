// frontend/hooks/useSync.ts
// Custom React hook for offline-first sync management

import { useCallback, useEffect, useState } from 'react'
import { useOfflineStore, triggerSync } from '../stores/offlineStore'
import { syncService } from '../services/syncService'
import type {
  SyncQueueItem,
  SyncQueueStatus,
  ConflictRecord,
  NetworkStatus,
  OperationType,
  ResolutionStrategy,
} from '../types/sync'

interface UseSyncReturn {
  queueStatus: SyncQueueStatus
  networkStatus: NetworkStatus
  isSyncing: boolean
  lastSyncTime?: Date
  pendingCount: number
  conflictCount: number

  addItem: (
    operationType: OperationType,
    entityType: string,
    entityId: string,
    payload: Record<string, unknown>
  ) => string

  removeItem: (itemId: string) => void
  clearQueue: () => void
  startSync: () => Promise<void>
  triggerManualSync: () => void
  cancelSync: (itemId: string) => void

  resolveConflict: (
    syncQueueItemId: string,
    strategy: ResolutionStrategy,
    resolvedData?: Record<string, unknown>
  ) => Promise<void>

  getUnresolvedConflicts: () => ConflictRecord[]
  getDeadLetterItems: () => SyncQueueItem[]
}

export function useSync(): UseSyncReturn {
  const store = useOfflineStore()
  const [queueStatus, setQueueStatus] = useState<SyncQueueStatus>(store.queueStatus())
  const [networkStatus, setNetworkStatus] = useState<NetworkStatus>(store.network)
  const [isSyncing, setIsSyncing] = useState(store.isSyncing)
  const [lastSyncTime, setLastSyncTime] = useState(store.lastSyncTime)

  useEffect(() => {
    const unsub = useOfflineStore.subscribe(
      (state) => ({
        syncQueue: state.syncQueue,
        network: state.network,
        isSyncing: state.isSyncing,
        lastSyncTime: state.lastSyncTime,
      }),
      (state) => {
        setQueueStatus(state.syncQueue.length > 0 ? useOfflineStore.getState().queueStatus() : emptyStatus)
        setNetworkStatus(state.network)
        setIsSyncing(state.isSyncing)
        setLastSyncTime(state.lastSyncTime)
      }
    )

    return unsub
  }, [])

  const addItem = useCallback(
    (operationType: OperationType, entityType: string, entityId: string, payload: Record<string, unknown>): string => {
      const itemId = store.addQueueItem({
        operation_type: operationType,
        entity_type: entityType,
        entity_id: entityId,
        payload,
      })

      if (networkStatus.is_online) {
        triggerSync()
      }

      return itemId
    },
    [store, networkStatus]
  )

  const removeItem = useCallback(
    (itemId: string) => {
      store.removeQueueItem(itemId)
    },
    [store]
  )

  const clearQueue = useCallback(() => {
    store.clearQueue()
  }, [store])

  const startSync = useCallback(async () => {
    if (!networkStatus.is_online) {
      console.warn('Cannot sync while offline')
      return
    }

    await syncService.startSync()
  }, [networkStatus])

  const triggerManualSync = useCallback(() => {
    triggerSync()
  }, [])

  const cancelSync = useCallback(
    (itemId: string) => {
      syncService.cancelSync(itemId)
    },
    []
  )

  const resolveConflict = useCallback(
    async (
      syncQueueItemId: string,
      strategy: ResolutionStrategy,
      resolvedData?: Record<string, unknown>
    ) => {
      await syncService.resolveConflict(syncQueueItemId, strategy, resolvedData)
    },
    []
  )

  const getUnresolvedConflicts = useCallback(() => {
    return store.getConflicts().filter((c) => !c.resolution_strategy)
  }, [store])

  const getDeadLetterItems = useCallback(() => {
    return store.getQueueItems('DEAD_LETTER')
  }, [store])

  return {
    queueStatus,
    networkStatus,
    isSyncing,
    lastSyncTime,
    pendingCount: queueStatus.pending + queueStatus.failed,
    conflictCount: queueStatus.conflicts,

    addItem,
    removeItem,
    clearQueue,
    startSync,
    triggerManualSync,
    cancelSync,

    resolveConflict,
    getUnresolvedConflicts,
    getDeadLetterItems,
  }
}

const emptyStatus: SyncQueueStatus = {
  total: 0,
  pending: 0,
  syncing: 0,
  synced: 0,
  conflicts: 0,
  failed: 0,
  dead_letter: 0,
}

export default useSync
