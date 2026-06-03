// frontend/components/ConflictResolutionModal.tsx
// Modal for visualizing and resolving sync conflicts with 3-way merge

import React, { useState } from 'react'
import { useOfflineStore } from '../stores/offlineStore'
import { syncService } from '../services/syncService'
import type { ConflictRecord, ResolutionStrategy } from '../types/sync'

interface ConflictResolutionModalProps {
  conflict: ConflictRecord
  isOpen: boolean
  onClose: () => void
  onResolved?: (conflictId: string) => void
}

export const ConflictResolutionModal: React.FC<ConflictResolutionModalProps> = ({
  conflict,
  isOpen,
  onClose,
  onResolved,
}) => {
  const [selectedStrategy, setSelectedStrategy] = useState<ResolutionStrategy | null>(null)
  const [manualMergeData, setManualMergeData] = useState<Record<string, unknown>>(conflict.our_data)
  const [isResolving, setIsResolving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const store = useOfflineStore()

  if (!isOpen) return null

  const handleResolveConflict = async () => {
    if (!selectedStrategy) {
      setError('Please select a resolution strategy')
      return
    }

    setIsResolving(true)
    setError(null)

    try {
      const resolveData = selectedStrategy === 'MANUAL_MERGE' ? manualMergeData : undefined
      await syncService.resolveConflict(conflict.sync_queue_item_id, selectedStrategy, resolveData)
      store.updateConflict(conflict.id, selectedStrategy)
      onResolved?.(conflict.id)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resolve conflict')
    } finally {
      setIsResolving(false)
    }
  }

  const handleManualMergeChange = (key: string, value: unknown) => {
    setManualMergeData((prev) => ({
      ...prev,
      [key]: value,
    }))
  }

  const getAllKeys = (): Set<string> => {
    const keys = new Set<string>()
    Object.keys(conflict.our_data).forEach((k) => keys.add(k))
    Object.keys(conflict.server_data).forEach((k) => keys.add(k))
    return keys
  }

  const getFieldDiff = (key: string): 'ours' | 'theirs' | 'both' | 'same' => {
    const ourVal = conflict.our_data[key]
    const serverVal = conflict.server_data[key]
    const ourStr = JSON.stringify(ourVal)
    const serverStr = JSON.stringify(serverVal)

    if (ourStr === serverStr) return 'same'
    if (key in conflict.our_data && !(key in conflict.server_data)) return 'ours'
    if (!(key in conflict.our_data) && key in conflict.server_data) return 'theirs'
    return 'both'
  }

  const allKeys = Array.from(getAllKeys())
  const conflictingKeys = allKeys.filter((k) => getFieldDiff(k) === 'both')
  const ourOnlyKeys = allKeys.filter((k) => getFieldDiff(k) === 'ours')
  const theirsOnlyKeys = allKeys.filter((k) => getFieldDiff(k) === 'theirs')

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-screen overflow-y-auto">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 sticky top-0 bg-white">
          <h2 className="text-xl font-bold text-gray-900">Resolve Conflict</h2>
          <p className="text-sm text-gray-600 mt-1">
            Entity: {conflict.entity_type} ({conflict.entity_id})
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Our version {conflict.our_version} vs Server version {conflict.server_version}
          </p>
        </div>

        {/* Content */}
        <div className="px-6 py-4">
          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-300 rounded text-red-800 text-sm">
              {error}
            </div>
          )}

          {/* Strategy Selection */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Resolution Strategy</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {(['KEEP_LOCAL', 'USE_SERVER', 'AUTO_MERGE', 'MANUAL_MERGE'] as const).map(
                (strategy) => (
                  <button
                    key={strategy}
                    onClick={() => {
                      setSelectedStrategy(strategy)
                      setError(null)
                    }}
                    className={`p-3 border-2 rounded-lg text-left transition-colors ${
                      selectedStrategy === strategy
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 bg-white hover:border-gray-300'
                    }`}
                  >
                    <div className="font-medium text-sm text-gray-900">{strategy}</div>
                    <div className="text-xs text-gray-600 mt-1">
                      {getStrategyDescription(strategy)}
                    </div>
                  </button>
                )
              )}
            </div>
          </div>

          {/* 3-Way Merge View */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Field Comparison</h3>

            {conflictingKeys.length > 0 && (
              <div className="mb-4">
                <div className="text-xs font-medium text-gray-600 mb-2">Conflicting Fields</div>
                <div className="space-y-2">
                  {conflictingKeys.map((key) => (
                    <FieldComparison
                      key={key}
                      fieldKey={key}
                      ourValue={conflict.our_data[key]}
                      serverValue={conflict.server_data[key]}
                      isEditable={selectedStrategy === 'MANUAL_MERGE'}
                      onValueChange={(value) => handleManualMergeChange(key, value)}
                      currentValue={manualMergeData[key]}
                    />
                  ))}
                </div>
              </div>
            )}

            {ourOnlyKeys.length > 0 && (
              <div className="mb-4">
                <div className="text-xs font-medium text-gray-600 mb-2">Only in Our Version</div>
                <div className="space-y-2">
                  {ourOnlyKeys.map((key) => (
                    <div key={key} className="flex items-start gap-2 p-2 bg-blue-50 rounded border border-blue-200 text-xs">
                      <span className="font-medium text-blue-900 flex-shrink-0 mt-0.5">+</span>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-900">{key}</div>
                        <div className="text-gray-600 break-words">
                          {JSON.stringify(conflict.our_data[key], null, 2)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {theirsOnlyKeys.length > 0 && (
              <div>
                <div className="text-xs font-medium text-gray-600 mb-2">Only in Server Version</div>
                <div className="space-y-2">
                  {theirsOnlyKeys.map((key) => (
                    <div key={key} className="flex items-start gap-2 p-2 bg-green-50 rounded border border-green-200 text-xs">
                      <span className="font-medium text-green-900 flex-shrink-0 mt-0.5">+</span>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-900">{key}</div>
                        <div className="text-gray-600 break-words">
                          {JSON.stringify(conflict.server_data[key], null, 2)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 sticky bottom-0 bg-white flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={isResolving}
            className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleResolveConflict}
            disabled={isResolving || !selectedStrategy}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {isResolving ? 'Resolving...' : 'Resolve'}
          </button>
        </div>
      </div>
    </div>
  )
}

interface FieldComparisonProps {
  fieldKey: string
  ourValue: unknown
  serverValue: unknown
  isEditable: boolean
  onValueChange: (value: unknown) => void
  currentValue: unknown
}

const FieldComparison: React.FC<FieldComparisonProps> = ({
  fieldKey,
  ourValue,
  serverValue,
  isEditable,
  onValueChange,
  currentValue,
}) => {
  return (
    <div className="p-3 bg-gray-50 rounded border border-gray-200">
      <div className="font-medium text-gray-900 mb-2">{fieldKey}</div>
      <div className="grid grid-cols-3 gap-2 text-xs">
        <div>
          <div className="font-medium text-blue-700 mb-1">Our Version</div>
          <div className="p-2 bg-blue-50 rounded border border-blue-200 break-words max-h-20 overflow-y-auto">
            {JSON.stringify(ourValue, null, 2)}
          </div>
        </div>
        <div>
          <div className="font-medium text-green-700 mb-1">Server Version</div>
          <div className="p-2 bg-green-50 rounded border border-green-200 break-words max-h-20 overflow-y-auto">
            {JSON.stringify(serverValue, null, 2)}
          </div>
        </div>
        <div>
          <div className="font-medium text-purple-700 mb-1">
            {isEditable ? 'Merged Value (Editable)' : 'Preview'}
          </div>
          {isEditable ? (
            <textarea
              value={JSON.stringify(currentValue, null, 2)}
              onChange={(e) => {
                try {
                  onValueChange(JSON.parse(e.target.value))
                } catch {}
              }}
              className="w-full p-2 bg-purple-50 rounded border border-purple-200 font-mono text-xs resize-none"
              rows={3}
            />
          ) : (
            <div className="p-2 bg-purple-50 rounded border border-purple-200 break-words max-h-20 overflow-y-auto">
              {JSON.stringify(currentValue, null, 2)}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function getStrategyDescription(strategy: ResolutionStrategy): string {
  switch (strategy) {
    case 'KEEP_LOCAL':
      return 'Keep our local changes, discard server changes'
    case 'USE_SERVER':
      return 'Accept server changes, discard our local changes'
    case 'AUTO_MERGE':
      return 'Automatically merge if no overlapping fields'
    case 'MANUAL_MERGE':
      return 'Manually select which values to keep'
    default:
      return ''
  }
}

export default ConflictResolutionModal
