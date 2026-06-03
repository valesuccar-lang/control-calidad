// frontend/types/sync.ts
// Type definitions for offline-first synchronization

// ==================== ENUMS ====================

export enum SyncStatus {
  PENDING = 'PENDING',
  SYNCING = 'SYNCING',
  SYNCED = 'SYNCED',
  CONFLICT = 'CONFLICT',
  FAILED = 'FAILED',
  RETRY_PENDING = 'RETRY_PENDING',
  DEAD_LETTER = 'DEAD_LETTER',
}

export enum OperationType {
  CREATE_INSPECTION = 'CREATE_INSPECTION',
  UPDATE_INSPECTION = 'UPDATE_INSPECTION',
  SUBMIT_INSPECTION = 'SUBMIT_INSPECTION',
  APPROVE_INSPECTION = 'APPROVE_INSPECTION',
  REJECT_INSPECTION = 'REJECT_INSPECTION',
  DELETE_INSPECTION = 'DELETE_INSPECTION',
}

export enum NetworkQuality {
  EXCELLENT = 'EXCELLENT', // latency < 50ms
  GOOD = 'GOOD',           // latency 50-150ms
  POOR = 'POOR',           // latency 150-300ms
  VERY_POOR = 'VERY_POOR', // latency > 300ms
  OFFLINE = 'OFFLINE',     // no connection
}

export enum ConflictType {
  VERSION_MISMATCH = 'VERSION_MISMATCH',
  DELETED_REMOTE = 'DELETED_REMOTE',
  EDITED_BOTH = 'EDITED_BOTH',
}

export enum ResolutionStrategy {
  AUTO_MERGE = 'AUTO_MERGE',
  KEEP_LOCAL = 'KEEP_LOCAL',
  USE_SERVER = 'USE_SERVER',
  MANUAL_MERGE = 'MANUAL_MERGE',
}

// ==================== SYNC QUEUE TYPES ====================

export interface SyncQueueItem {
  id: string
  operation_type: OperationType
  entity_type: string // 'INSPECTION' | 'APPROVAL' | etc.
  entity_id: string   // UUID of the entity
  payload: Record<string, unknown>

  status: SyncStatus
  retry_count: number // 0-5
  last_error?: string

  created_at: Date
  last_retry_at?: Date
  next_retry_at?: Date
  synced_at?: Date
}

export interface SyncQueueStatus {
  total: number
  pending: number
  syncing: number
  synced: number
  conflicts: number
  failed: number
  dead_letter: number
}

// ==================== CONFLICT TYPES ====================

export interface ConflictRecord {
  id: string
  sync_queue_item_id: string
  entity_type: string
  entity_id: string

  conflict_type: ConflictType
  our_version: number
  server_version: number

  our_data: Record<string, unknown>
  server_data: Record<string, unknown>
  base_data?: Record<string, unknown>

  can_auto_merge: boolean
  overlapping_fields: string[]

  resolution_strategy?: ResolutionStrategy
  resolved_at?: Date

  created_at: Date
  expires_at: Date // 24h from creation
}

export interface ConflictResolutionInput {
  sync_queue_item_id: string
  resolution_strategy: ResolutionStrategy
  resolved_data?: Record<string, unknown> // For MANUAL_MERGE
}

// ==================== NETWORK TYPES ====================

export interface NetworkStatus {
  is_online: boolean
  quality: NetworkQuality
  latency_ms: number
  packet_loss_pct: number
  last_check: Date
}

export interface NetworkQualityMetrics {
  latency_ms: number
  packet_loss_pct: number
  bandwidth_estimate_mbps?: number
  last_measured: Date
}

// ==================== API REQUEST/RESPONSE TYPES ====================

export interface SyncItemRequest {
  operation_type: OperationType
  entity_id: string
  payload: Record<string, unknown>
  version?: number
  timestamp: string // ISO 8601
}

export interface SyncItemResponse {
  id: string
  sync_status: 'SYNCED' | 'CONFLICT' | 'FAILED'
  server_version: number
  synced_at: string // ISO 8601
}

export interface SyncErrorResponse {
  error: string
  details?: Record<string, unknown>
  our_version?: number
  server_version?: number
  server_data?: Record<string, unknown>
}

export interface ResolveConflictRequest {
  sync_queue_item_id: string
  resolution_strategy: ResolutionStrategy
  resolved_data?: Record<string, unknown>
}

export interface ResolveConflictResponse {
  message: string
  retry_in_seconds: number
}

export interface SyncStatusResponse {
  online: boolean
  network_quality: NetworkQuality
  queue_status: SyncQueueStatus
  last_sync?: string // ISO 8601
  estimated_completion?: string // ISO 8601
}

// ==================== INDEXEDDB TYPES ====================

export interface IDBSyncQueueItem extends Omit<SyncQueueItem, 'created_at' | 'last_retry_at' | 'next_retry_at' | 'synced_at'> {
  created_at: number // timestamp (ms)
  last_retry_at?: number
  next_retry_at?: number
  synced_at?: number
}

export interface IDBConflictRecord extends Omit<ConflictRecord, 'created_at' | 'expires_at' | 'resolved_at'> {
  created_at: number // timestamp
  expires_at: number
  resolved_at?: number
}

export interface CacheMetadata {
  store_name: 'masters' | 'inspections' | 'sync_queue'
  last_refresh: number // timestamp
  cache_version: number
  size_bytes: number
  item_count: number
}

// ==================== ERROR TYPES ====================

export class SyncError extends Error {
  constructor(
    public code: string,
    message: string,
    public details?: Record<string, unknown>
  ) {
    super(message)
    this.name = 'SyncError'
  }
}

export class ConflictError extends SyncError {
  constructor(
    public conflict: ConflictRecord,
    message: string = 'Conflict detected during sync'
  ) {
    super('CONFLICT', message, { conflict })
    this.name = 'ConflictError'
  }
}

export class ValidationError extends SyncError {
  constructor(
    public fields: Record<string, string>,
    message: string = 'Validation failed'
  ) {
    super('VALIDATION_ERROR', message, { fields })
    this.name = 'ValidationError'
  }
}

export class RetryableError extends SyncError {
  constructor(
    public retryAfterMs: number,
    message: string
  ) {
    super('RETRYABLE_ERROR', message, { retryAfterMs })
    this.name = 'RetryableError'
  }
}

// ==================== UI STATE TYPES ====================

export interface SyncUIState {
  isVisible: boolean
  queueCount: number
  conflictCount: number
  errorCount: number
  networkQuality: NetworkQuality
  isSyncing: boolean
  lastSyncTime?: Date
  estimatedNextRetry?: Date
}

export interface ConflictUIState {
  isOpen: boolean
  conflict?: ConflictRecord
  isResolving: boolean
  error?: string
}

// ==================== UTILITY TYPES ====================

export type SyncOperationResult<T = Record<string, unknown>> = {
  success: true
  data: T
  synced_at: Date
} | {
  success: false
  error: SyncError
  retry_after?: number
}

export type NetworkDetectionFn = () => Promise<NetworkStatus>

export type ConflictMergeFn = (
  ours: Record<string, unknown>,
  base: Record<string, unknown>,
  theirs: Record<string, unknown>
) => {
  canAutoMerge: boolean
  merged?: Record<string, unknown>
  conflictingFields?: string[]
}

// ==================== CONSTANTS ====================

export const BACKOFF_INTERVALS_MS = [5000, 10000, 30000, 60000, 60000] as const
export const MAX_RETRIES = 5
export const SYNC_TIMEOUT_MS = 10000
export const CONFLICT_EXPIRATION_MS = 24 * 60 * 60 * 1000 // 24 hours
export const CACHE_TTL_MS = 60 * 60 * 1000 // 1 hour
export const NETWORK_CHECK_INTERVAL_MS = 5000 // 5 seconds
export const MIN_SYNC_INTERVAL_MS = 2000 // 2 seconds between attempts
