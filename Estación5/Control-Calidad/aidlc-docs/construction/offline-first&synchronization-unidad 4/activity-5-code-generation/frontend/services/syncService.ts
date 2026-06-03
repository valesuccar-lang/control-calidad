// frontend/services/syncService.ts
// Frontend sync orchestration and queue management

import {
  SyncQueueItem,
  ConflictRecord,
  SyncStatus,
  OperationType,
  NetworkQuality,
  ResolutionStrategy,
  BACKOFF_INTERVALS_MS,
  MAX_RETRIES,
  SYNC_TIMEOUT_MS,
  ConflictError,
  SyncError,
  ValidationError,
} from '../types/sync'
import { useOfflineStore, triggerSync } from '../stores/offlineStore'

interface SyncConfig {
  apiBaseUrl: string
  timeout: number
  maxRetries: number
  backoffIntervals: readonly number[]
}

export class SyncService {
  private config: SyncConfig
  private abortControllers: Map<string, AbortController> = new Map()

  constructor(apiBaseUrl: string = '/api/v1') {
    this.config = {
      apiBaseUrl,
      timeout: SYNC_TIMEOUT_MS,
      maxRetries: MAX_RETRIES,
      backoffIntervals: BACKOFF_INTERVALS_MS,
    }
  }

  // ==================== SYNC ORCHESTRATION ====================

  async startSync(): Promise<void> {
    const store = useOfflineStore.getState()

    if (!store.network.is_online) {
      console.log('Offline, sync deferred')
      return
    }

    if (store.isSyncing) {
      console.log('Already syncing')
      return
    }

    store.startSync()

    try {
      const pending = store.getQueueItems('PENDING')
      const retryPending = store.getQueueItems('RETRY_PENDING')
      const items = [...pending, ...retryPending]

      if (items.length === 0) {
        store.endSync()
        return
      }

      const quality = store.network.quality
      const batchSize = this.calculateBatchSize(quality)

      for (let i = 0; i < items.length; i += batchSize) {
        const batch = items.slice(i, i + batchSize)
        await this.processBatch(batch)

        if (quality === 'POOR') {
          await this.sleep(1000)
        }
      }

      // Process conflicts
      const conflicts = store.getConflicts()
      for (const conflict of conflicts) {
        if (conflict.can_auto_merge && !conflict.resolution_strategy) {
          await this.autoResolveConflict(conflict)
        }
      }

      store.endSync()
    } catch (error) {
      console.error('Sync error:', error)
      store.endSync()
      throw error
    }
  }

  private async processBatch(items: SyncQueueItem[]): Promise<void> {
    const store = useOfflineStore.getState()

    const results = await Promise.allSettled(items.map((item) => this.syncItem(item)))

    for (let i = 0; i < items.length; i++) {
      const item = items[i]
      const result = results[i]

      if (result.status === 'fulfilled') {
        const response = result.value
        if (response.status === 'SYNCED') {
          store.updateQueueItem(item.id, {
            status: 'SYNCED',
            synced_at: new Date(),
          })
        } else if (response.status === 'CONFLICT') {
          store.updateQueueItem(item.id, { status: 'CONFLICT' })
          store.addConflict(response.conflict)
        }
      } else {
        const error = result.reason
        if (this.isRetryable(error)) {
          this.scheduleRetry(item)
        } else {
          store.updateQueueItem(item.id, {
            status: 'DEAD_LETTER',
            last_error: error.message,
          })
        }
      }
    }
  }

  private async syncItem(item: SyncQueueItem): Promise<{
    status: 'SYNCED' | 'CONFLICT'
    conflict?: ConflictRecord
  }> {
    const store = useOfflineStore.getState()
    const abortController = new AbortController()
    this.abortControllers.set(item.id, abortController)

    try {
      store.updateQueueItem(item.id, { status: 'SYNCING' })

      const timeout = setTimeout(() => abortController.abort(), this.config.timeout)

      const response = await fetch(`${this.config.apiBaseUrl}/sync/items`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          operation_type: item.operation_type,
          entity_id: item.entity_id,
          payload: item.payload,
          version: item.payload.version,
          timestamp: new Date().toISOString(),
        }),
        signal: abortController.signal,
      })

      clearTimeout(timeout)

      if (response.status === 200) {
        return { status: 'SYNCED' }
      }

      if (response.status === 409) {
        const data = await response.json()
        const conflict = this.createConflictRecord(item, data)
        return { status: 'CONFLICT', conflict }
      }

      if (response.status === 422) {
        const data = await response.json()
        throw new ValidationError(data.fields || {}, data.message)
      }

      if (response.status >= 500) {
        throw new SyncError('SERVER_ERROR', `Server error: ${response.status}`)
      }

      throw new SyncError('REQUEST_FAILED', `Request failed: ${response.status}`)
    } finally {
      this.abortControllers.delete(item.id)
    }
  }

  // ==================== CONFLICT RESOLUTION ====================

  private createConflictRecord(item: SyncQueueItem, conflictData: unknown): ConflictRecord {
    const data = conflictData as Record<string, unknown>
    return {
      id: crypto.randomUUID(),
      sync_queue_item_id: item.id,
      entity_type: item.entity_type,
      entity_id: item.entity_id,
      conflict_type: 'VERSION_MISMATCH',
      our_version: (item.payload.version as number) || 1,
      server_version: (data.server_version as number) || 2,
      our_data: item.payload,
      server_data: (data.server_data as Record<string, unknown>) || {},
      can_auto_merge: false,
      overlapping_fields: [],
      created_at: new Date(),
      expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000),
    }
  }

  private async autoResolveConflict(conflict: ConflictRecord): Promise<void> {
    const store = useOfflineStore.getState()
    const merged = this.perform3WayMerge(conflict)

    if (merged) {
      store.updateConflict(conflict.id, 'AUTO_MERGE')
      const queueItem = store.getQueueItems().find((i) => i.id === conflict.sync_queue_item_id)

      if (queueItem) {
        queueItem.payload = merged
        await this.syncItem(queueItem)
      }
    }
  }

  private perform3WayMerge(conflict: ConflictRecord): Record<string, unknown> | null {
    const base = conflict.base_data || conflict.server_data
    const ourChanges = this.getChangedFields(base, conflict.our_data)
    const theirChanges = this.getChangedFields(base, conflict.server_data)

    const overlapping = ourChanges.filter((f) => theirChanges.includes(f))

    if (overlapping.length > 0) {
      return null // Can't auto-merge
    }

    return {
      ...conflict.server_data,
      ...Object.fromEntries(
        Object.entries(conflict.our_data).filter(([k]) => ourChanges.includes(k))
      ),
    }
  }

  private getChangedFields(base: Record<string, unknown>, current: Record<string, unknown>): string[] {
    return Object.keys(current).filter((key) => {
      const baseVal = base?.[key]
      const currentVal = current[key]
      return JSON.stringify(baseVal) !== JSON.stringify(currentVal)
    })
  }

  // ==================== RETRY LOGIC ====================

  private scheduleRetry(item: SyncQueueItem): void {
    const store = useOfflineStore.getState()
    const nextRetryCount = item.retry_count + 1

    if (nextRetryCount >= this.config.maxRetries) {
      store.updateQueueItem(item.id, {
        status: 'DEAD_LETTER',
        last_error: 'Max retries exceeded',
      })
      return
    }

    const backoffMs = this.config.backoffIntervals[nextRetryCount]
    const nextRetryAt = new Date(Date.now() + backoffMs)

    store.updateQueueItem(item.id, {
      status: 'RETRY_PENDING',
      retry_count: nextRetryCount,
      last_retry_at: new Date(),
      next_retry_at: nextRetryAt,
    })

    setTimeout(() => {
      if (useOfflineStore.getState().network.is_online) {
        triggerSync()
      }
    }, backoffMs)
  }

  // ==================== CONFLICT RESOLUTION API ====================

  async resolveConflict(
    syncQueueItemId: string,
    strategy: ResolutionStrategy,
    resolvedData?: Record<string, unknown>
  ): Promise<void> {
    const response = await fetch(`${this.config.apiBaseUrl}/sync/resolve-conflict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sync_queue_item_id: syncQueueItemId,
        resolution_strategy: strategy,
        resolved_data: resolvedData,
      }),
    })

    if (!response.ok) {
      throw new SyncError('RESOLUTION_FAILED', `Failed to resolve conflict: ${response.status}`)
    }

    const store = useOfflineStore.getState()
    const conflict = store.getConflicts().find((c) => c.sync_queue_item_id === syncQueueItemId)

    if (conflict) {
      store.updateConflict(conflict.id, strategy)
      triggerSync()
    }
  }

  // ==================== UTILITIES ====================

  private calculateBatchSize(quality: NetworkQuality): number {
    switch (quality) {
      case 'EXCELLENT':
        return 20
      case 'GOOD':
        return 10
      case 'POOR':
      case 'VERY_POOR':
        return 1
      case 'OFFLINE':
        return 0
      default:
        return 10
    }
  }

  private isRetryable(error: unknown): boolean {
    if (error instanceof ConflictError) return true
    if (error instanceof ValidationError) return false
    if (error instanceof SyncError) {
      return error.code !== 'CLIENT_ERROR'
    }
    return true
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms))
  }

  cancelSync(itemId: string): void {
    const controller = this.abortControllers.get(itemId)
    if (controller) {
      controller.abort()
      this.abortControllers.delete(itemId)
    }
  }
}

// Export singleton instance
export const syncService = new SyncService()
