// frontend/components/SyncStatusBar.tsx
// Real-time sync status indicator and queue monitor

import React, { useEffect, useState } from 'react'
import { useOfflineStore, getQueueStatus, getNetworkStatus } from '../stores/offlineStore'
import type { SyncQueueStatus, NetworkStatus, NetworkQuality } from '../types/sync'

interface SyncStatusBarProps {
  position?: 'top' | 'bottom'
  compact?: boolean
}

export const SyncStatusBar: React.FC<SyncStatusBarProps> = ({
  position = 'bottom',
  compact = false,
}) => {
  const isSyncing = useOfflineStore((state) => state.isSyncing)
  const lastSyncTime = useOfflineStore((state) => state.lastSyncTime)
  const [queueStatus, setQueueStatus] = useState<SyncQueueStatus>(getQueueStatus())
  const [networkStatus, setNetworkStatus] = useState<NetworkStatus>(getNetworkStatus())

  useEffect(() => {
    const unsub = useOfflineStore.subscribe(
      (state) => ({
        syncQueue: state.syncQueue,
        conflicts: state.conflicts,
        network: state.network,
        isSyncing: state.isSyncing,
      }),
      (state) => {
        setQueueStatus(state.syncQueue.length > 0 ? getQueueStatus() : initialQueueStatus)
        setNetworkStatus(state.network)
      }
    )
    return unsub
  }, [])

  const pendingCount = queueStatus.pending + queueStatus.failed
  const syncedCount = queueStatus.synced
  const conflictCount = queueStatus.conflicts
  const isOnline = networkStatus.is_online
  const quality = networkStatus.quality

  const getStatusColor = (): string => {
    if (!isOnline) return 'bg-red-100 text-red-800'
    if (isSyncing) return 'bg-blue-100 text-blue-800'
    if (conflictCount > 0) return 'bg-yellow-100 text-yellow-800'
    if (pendingCount > 0) return 'bg-orange-100 text-orange-800'
    return 'bg-green-100 text-green-800'
  }

  const getStatusIcon = (): React.ReactNode => {
    if (!isOnline) return '⚠️'
    if (isSyncing) return '⟳'
    if (conflictCount > 0) return '⚡'
    if (pendingCount > 0) return '⋯'
    return '✓'
  }

  const getStatusText = (): string => {
    if (!isOnline) return 'Offline'
    if (isSyncing) return 'Syncing...'
    if (conflictCount > 0) return `${conflictCount} conflict${conflictCount > 1 ? 's' : ''}`
    if (pendingCount > 0) return `${pendingCount} pending`
    return 'Synced'
  }

  const getQualityIndicator = (): string => {
    switch (quality) {
      case 'EXCELLENT':
        return '5 bars'
      case 'GOOD':
        return '4 bars'
      case 'POOR':
        return '2 bars'
      case 'VERY_POOR':
        return '1 bar'
      case 'OFFLINE':
        return 'offline'
      default:
        return 'unknown'
    }
  }

  const formatLastSyncTime = (): string => {
    if (!lastSyncTime) return 'Never'
    const now = new Date()
    const diffMs = now.getTime() - lastSyncTime.getTime()
    const diffMins = Math.floor(diffMs / 60000)

    if (diffMins === 0) return 'Just now'
    if (diffMins === 1) return '1 min ago'
    if (diffMins < 60) return `${diffMins} mins ago`

    const diffHours = Math.floor(diffMins / 60)
    if (diffHours === 1) return '1 hour ago'
    if (diffHours < 24) return `${diffHours} hours ago`

    const diffDays = Math.floor(diffHours / 24)
    return `${diffDays} days ago`
  }

  if (compact) {
    return (
      <div
        className={`fixed ${position}-0 left-0 right-0 px-4 py-2 text-center text-sm font-medium ${getStatusColor()}`}
      >
        <span className="mr-2">{getStatusIcon()}</span>
        {getStatusText()}
      </div>
    )
  }

  return (
    <div
      className={`fixed ${position}-0 left-0 right-0 px-6 py-4 border-t border-gray-200 bg-white shadow-lg`}
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className={`flex items-center gap-2 px-3 py-1 rounded-full ${getStatusColor()}`}>
            <span className="text-lg">{getStatusIcon()}</span>
            <span className="font-semibold">{getStatusText()}</span>
          </div>

          <div className="text-sm text-gray-600">
            <span className="font-medium">Network:</span> {getQualityIndicator()}
          </div>

          <div className="text-sm text-gray-600">
            <span className="font-medium">Last sync:</span> {formatLastSyncTime()}
          </div>
        </div>

        <div className="flex items-center gap-6 text-sm">
          {syncedCount > 0 && (
            <div className="flex items-center gap-1">
              <span className="text-green-600">✓</span>
              <span className="text-gray-700">{syncedCount}</span>
            </div>
          )}

          {pendingCount > 0 && (
            <div className="flex items-center gap-1">
              <span className="text-orange-600">⋯</span>
              <span className="text-gray-700">{pendingCount}</span>
            </div>
          )}

          {conflictCount > 0 && (
            <div className="flex items-center gap-1">
              <span className="text-yellow-600">⚡</span>
              <span className="text-gray-700">{conflictCount}</span>
            </div>
          )}

          {queueStatus.dead_letter > 0 && (
            <div className="flex items-center gap-1">
              <span className="text-red-600">✕</span>
              <span className="text-gray-700">{queueStatus.dead_letter}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

const initialQueueStatus: SyncQueueStatus = {
  total: 0,
  pending: 0,
  syncing: 0,
  synced: 0,
  conflicts: 0,
  failed: 0,
  dead_letter: 0,
}

export default SyncStatusBar
