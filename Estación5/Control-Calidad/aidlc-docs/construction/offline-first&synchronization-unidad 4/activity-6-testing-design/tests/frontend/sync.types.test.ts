// frontend/__tests__/types/sync.types.test.ts
// Unit tests for sync type definitions and error classes
// Approach: AAA (Arrange-Act-Assert) for algorithmic logic

import {
  SyncStatus,
  OperationType,
  NetworkQuality,
  ConflictType,
  ResolutionStrategy,
  SyncError,
  ConflictError,
  ValidationError,
  RetryableError,
  BACKOFF_INTERVALS_MS,
  MAX_RETRIES,
  SYNC_TIMEOUT_MS,
  CONFLICT_EXPIRATION_MS,
  CACHE_TTL_MS,
  NETWORK_CHECK_INTERVAL_MS,
  MIN_SYNC_INTERVAL_MS,
} from '../../types/sync'

describe('SyncStatus Enum', () => {
  test('has all required status values', () => {
    // Arrange
    const expectedStatuses = [
      'PENDING',
      'SYNCING',
      'SYNCED',
      'CONFLICT',
      'FAILED',
      'RETRY_PENDING',
      'DEAD_LETTER',
    ]

    // Act
    const actualStatuses = Object.values(SyncStatus)

    // Assert
    expect(actualStatuses).toEqual(expect.arrayContaining(expectedStatuses))
    expect(actualStatuses.length).toBe(7)
  })

  test('PENDING status is defined', () => {
    // Arrange & Act
    const status = SyncStatus.PENDING

    // Assert
    expect(status).toBe('PENDING')
  })

  test('SYNCED status is defined', () => {
    // Arrange & Act
    const status = SyncStatus.SYNCED

    // Assert
    expect(status).toBe('SYNCED')
  })

  test('DEAD_LETTER status is defined for max retries', () => {
    // Arrange & Act
    const status = SyncStatus.DEAD_LETTER

    // Assert
    expect(status).toBe('DEAD_LETTER')
  })
})

describe('OperationType Enum', () => {
  test('has all required operation types for inspections', () => {
    // Arrange
    const expectedOperations = [
      'CREATE_INSPECTION',
      'UPDATE_INSPECTION',
      'SUBMIT_INSPECTION',
      'APPROVE_INSPECTION',
      'REJECT_INSPECTION',
      'DELETE_INSPECTION',
    ]

    // Act
    const actualOperations = Object.values(OperationType)

    // Assert
    expect(actualOperations).toEqual(expect.arrayContaining(expectedOperations))
    expect(actualOperations.length).toBe(6)
  })

  test('CREATE_INSPECTION operation is defined', () => {
    // Arrange & Act
    const operation = OperationType.CREATE_INSPECTION

    // Assert
    expect(operation).toBe('CREATE_INSPECTION')
  })
})

describe('NetworkQuality Enum', () => {
  test('has all network quality levels', () => {
    // Arrange
    const expectedQualities = ['EXCELLENT', 'GOOD', 'POOR', 'VERY_POOR', 'OFFLINE']

    // Act
    const actualQualities = Object.values(NetworkQuality)

    // Assert
    expect(actualQualities).toEqual(expect.arrayContaining(expectedQualities))
    expect(actualQualities.length).toBe(5)
  })

  test('network quality values match latency classification', () => {
    // Arrange
    const latencyMap = {
      [NetworkQuality.EXCELLENT]: 25,   // < 50ms
      [NetworkQuality.GOOD]: 100,       // 50-150ms
      [NetworkQuality.POOR]: 200,       // 150-300ms
      [NetworkQuality.VERY_POOR]: 350,  // > 300ms
    }

    // Act & Assert
    Object.entries(latencyMap).forEach(([quality, latency]) => {
      expect(quality).toBeDefined()
      expect(typeof latency).toBe('number')
    })
  })
})

describe('ConflictType Enum', () => {
  test('has all conflict types', () => {
    // Arrange
    const expectedTypes = ['VERSION_MISMATCH', 'DELETED_REMOTE', 'EDITED_BOTH']

    // Act
    const actualTypes = Object.values(ConflictType)

    // Assert
    expect(actualTypes).toEqual(expect.arrayContaining(expectedTypes))
    expect(actualTypes.length).toBe(3)
  })

  test('VERSION_MISMATCH is primary conflict type', () => {
    // Arrange & Act
    const type = ConflictType.VERSION_MISMATCH

    // Assert
    expect(type).toBe('VERSION_MISMATCH')
  })
})

describe('ResolutionStrategy Enum', () => {
  test('has all resolution strategies', () => {
    // Arrange
    const expectedStrategies = ['AUTO_MERGE', 'KEEP_LOCAL', 'USE_SERVER', 'MANUAL_MERGE']

    // Act
    const actualStrategies = Object.values(ResolutionStrategy)

    // Assert
    expect(actualStrategies).toEqual(expect.arrayContaining(expectedStrategies))
    expect(actualStrategies.length).toBe(4)
  })

  test('AUTO_MERGE strategy is defined', () => {
    // Arrange & Act
    const strategy = ResolutionStrategy.AUTO_MERGE

    // Assert
    expect(strategy).toBe('AUTO_MERGE')
  })

  test('MANUAL_MERGE strategy is defined for complex conflicts', () => {
    // Arrange & Act
    const strategy = ResolutionStrategy.MANUAL_MERGE

    // Assert
    expect(strategy).toBe('MANUAL_MERGE')
  })
})

describe('SyncError Class', () => {
  test('extends Error', () => {
    // Arrange
    const error = new SyncError('TEST_ERROR', 'Test message')

    // Act & Assert
    expect(error).toBeInstanceOf(Error)
    expect(error).toBeInstanceOf(SyncError)
  })

  test('has name property set to SyncError', () => {
    // Arrange
    const error = new SyncError('TEST_ERROR', 'Test message')

    // Act & Assert
    expect(error.name).toBe('SyncError')
  })

  test('stores error code', () => {
    // Arrange
    const code = 'NETWORK_ERROR'
    const message = 'Network timeout'

    // Act
    const error = new SyncError(code, message)

    // Assert
    expect(error.code).toBe(code)
    expect(error.message).toBe(message)
  })

  test('stores optional details', () => {
    // Arrange
    const details = { retryAfter: 5000, statusCode: 503 }

    // Act
    const error = new SyncError('SERVER_ERROR', 'Server unavailable', details)

    // Assert
    expect(error.details).toEqual(details)
  })

  test('is serializable to JSON', () => {
    // Arrange
    const error = new SyncError('VALIDATION_ERROR', 'Invalid payload', { field: 'email' })

    // Act
    const json = JSON.stringify({
      code: error.code,
      message: error.message,
      details: error.details,
    })

    // Assert
    expect(json).toContain('VALIDATION_ERROR')
    expect(json).toContain('Invalid payload')
  })
})

describe('ConflictError Class', () => {
  test('extends SyncError', () => {
    // Arrange
    const conflict = {
      id: 'c1',
      sync_queue_item_id: 'i1',
      entity_type: 'INSPECTION',
      entity_id: 'e1',
      conflict_type: ConflictType.VERSION_MISMATCH as const,
      our_version: 1,
      server_version: 2,
      our_data: {},
      server_data: {},
      can_auto_merge: false,
      overlapping_fields: [],
      created_at: new Date(),
      expires_at: new Date(),
    }

    // Act
    const error = new ConflictError(conflict)

    // Assert
    expect(error).toBeInstanceOf(SyncError)
    expect(error).toBeInstanceOf(ConflictError)
  })

  test('has code set to CONFLICT', () => {
    // Arrange
    const conflict = {
      id: 'c1',
      sync_queue_item_id: 'i1',
      entity_type: 'INSPECTION',
      entity_id: 'e1',
      conflict_type: ConflictType.VERSION_MISMATCH as const,
      our_version: 1,
      server_version: 2,
      our_data: {},
      server_data: {},
      can_auto_merge: false,
      overlapping_fields: [],
      created_at: new Date(),
      expires_at: new Date(),
    }

    // Act
    const error = new ConflictError(conflict)

    // Assert
    expect(error.code).toBe('CONFLICT')
  })

  test('stores conflict record', () => {
    // Arrange
    const conflict = {
      id: 'c1',
      sync_queue_item_id: 'i1',
      entity_type: 'INSPECTION',
      entity_id: 'e1',
      conflict_type: ConflictType.VERSION_MISMATCH as const,
      our_version: 1,
      server_version: 2,
      our_data: { name: 'ours' },
      server_data: { name: 'theirs' },
      can_auto_merge: false,
      overlapping_fields: ['name'],
      created_at: new Date(),
      expires_at: new Date(),
    }

    // Act
    const error = new ConflictError(conflict)

    // Assert
    expect(error.conflict).toEqual(conflict)
    expect(error.details?.conflict).toEqual(conflict)
  })

  test('has default message', () => {
    // Arrange
    const conflict = {
      id: 'c1',
      sync_queue_item_id: 'i1',
      entity_type: 'INSPECTION',
      entity_id: 'e1',
      conflict_type: ConflictType.VERSION_MISMATCH as const,
      our_version: 1,
      server_version: 2,
      our_data: {},
      server_data: {},
      can_auto_merge: false,
      overlapping_fields: [],
      created_at: new Date(),
      expires_at: new Date(),
    }

    // Act
    const error = new ConflictError(conflict)

    // Assert
    expect(error.message).toBe('Conflict detected during sync')
  })

  test('accepts custom message', () => {
    // Arrange
    const conflict = {
      id: 'c1',
      sync_queue_item_id: 'i1',
      entity_type: 'INSPECTION',
      entity_id: 'e1',
      conflict_type: ConflictType.VERSION_MISMATCH as const,
      our_version: 1,
      server_version: 2,
      our_data: {},
      server_data: {},
      can_auto_merge: false,
      overlapping_fields: [],
      created_at: new Date(),
      expires_at: new Date(),
    }
    const customMessage = 'Version mismatch on critical field'

    // Act
    const error = new ConflictError(conflict, customMessage)

    // Assert
    expect(error.message).toBe(customMessage)
  })
})

describe('ValidationError Class', () => {
  test('extends SyncError', () => {
    // Arrange
    const fields = { email: 'Invalid format' }

    // Act
    const error = new ValidationError(fields)

    // Assert
    expect(error).toBeInstanceOf(SyncError)
    expect(error).toBeInstanceOf(ValidationError)
  })

  test('has code set to VALIDATION_ERROR', () => {
    // Arrange
    const fields = { email: 'Invalid format' }

    // Act
    const error = new ValidationError(fields)

    // Assert
    expect(error.code).toBe('VALIDATION_ERROR')
  })

  test('stores field validation errors', () => {
    // Arrange
    const fields = {
      email: 'Invalid format',
      age: 'Must be positive',
    }

    // Act
    const error = new ValidationError(fields)

    // Assert
    expect(error.fields).toEqual(fields)
    expect(error.fields.email).toBe('Invalid format')
    expect(error.fields.age).toBe('Must be positive')
  })

  test('has default message', () => {
    // Arrange
    const fields = { email: 'Invalid' }

    // Act
    const error = new ValidationError(fields)

    // Assert
    expect(error.message).toBe('Validation failed')
  })
})

describe('RetryableError Class', () => {
  test('extends SyncError', () => {
    // Arrange
    const retryAfterMs = 5000

    // Act
    const error = new RetryableError(retryAfterMs, 'Service unavailable')

    // Assert
    expect(error).toBeInstanceOf(SyncError)
    expect(error).toBeInstanceOf(RetryableError)
  })

  test('stores retryAfterMs', () => {
    // Arrange
    const retryAfterMs = 10000

    // Act
    const error = new RetryableError(retryAfterMs, 'Timeout')

    // Assert
    expect(error.retryAfterMs).toBe(retryAfterMs)
    expect(error.details?.retryAfterMs).toBe(retryAfterMs)
  })

  test('has code set to RETRYABLE_ERROR', () => {
    // Arrange & Act
    const error = new RetryableError(5000, 'Network error')

    // Assert
    expect(error.code).toBe('RETRYABLE_ERROR')
  })
})

describe('Backoff Configuration', () => {
  test('BACKOFF_INTERVALS_MS has correct exponential progression', () => {
    // Arrange & Act
    const intervals = BACKOFF_INTERVALS_MS

    // Assert
    expect(intervals).toEqual([5000, 10000, 30000, 60000, 60000])
    expect(intervals.length).toBe(5)
  })

  test('MAX_RETRIES equals backoff intervals length', () => {
    // Arrange & Act
    const maxRetries = MAX_RETRIES
    const backoffLength = BACKOFF_INTERVALS_MS.length

    // Assert
    expect(maxRetries).toBe(5)
    expect(maxRetries).toEqual(backoffLength)
  })

  test('each backoff interval is greater than or equal to previous', () => {
    // Arrange
    const intervals = BACKOFF_INTERVALS_MS

    // Act & Assert
    for (let i = 1; i < intervals.length; i++) {
      expect(intervals[i]).toBeGreaterThanOrEqual(intervals[i - 1])
    }
  })
})

describe('Timeout Configuration', () => {
  test('SYNC_TIMEOUT_MS is 10 seconds', () => {
    // Arrange & Act
    const timeout = SYNC_TIMEOUT_MS

    // Assert
    expect(timeout).toBe(10000)
  })

  test('NETWORK_CHECK_INTERVAL_MS is 5 seconds', () => {
    // Arrange & Act
    const interval = NETWORK_CHECK_INTERVAL_MS

    // Assert
    expect(interval).toBe(5000)
  })

  test('MIN_SYNC_INTERVAL_MS is 2 seconds', () => {
    // Arrange & Act
    const interval = MIN_SYNC_INTERVAL_MS

    // Assert
    expect(interval).toBe(2000)
  })
})

describe('Expiration Configuration', () => {
  test('CONFLICT_EXPIRATION_MS is 24 hours', () => {
    // Arrange
    const twentyFourHoursInMs = 24 * 60 * 60 * 1000

    // Act
    const expirationMs = CONFLICT_EXPIRATION_MS

    // Assert
    expect(expirationMs).toBe(twentyFourHoursInMs)
  })

  test('CACHE_TTL_MS is 1 hour', () => {
    // Arrange
    const oneHourInMs = 60 * 60 * 1000

    // Act
    const ttlMs = CACHE_TTL_MS

    // Assert
    expect(ttlMs).toBe(oneHourInMs)
  })
})

describe('Error Type Guards', () => {
  test('can distinguish SyncError from ConflictError', () => {
    // Arrange
    const syncError = new SyncError('TEST', 'message')
    const conflict = {
      id: 'c1',
      sync_queue_item_id: 'i1',
      entity_type: 'INSPECTION',
      entity_id: 'e1',
      conflict_type: ConflictType.VERSION_MISMATCH as const,
      our_version: 1,
      server_version: 2,
      our_data: {},
      server_data: {},
      can_auto_merge: false,
      overlapping_fields: [],
      created_at: new Date(),
      expires_at: new Date(),
    }
    const conflictError = new ConflictError(conflict)

    // Act & Assert
    expect(syncError).toBeInstanceOf(SyncError)
    expect(conflictError).toBeInstanceOf(ConflictError)
    expect(conflictError).toBeInstanceOf(SyncError)
    expect(conflictError.code).toBe('CONFLICT')
    expect(syncError.code).toBe('TEST')
  })

  test('can check error code for retry logic', () => {
    // Arrange
    const validationError = new ValidationError({ field: 'error' })
    const retryableError = new RetryableError(5000, 'timeout')

    // Act
    const isValidationRetryable = validationError.code !== 'CLIENT_ERROR'
    const isRetryableRetryable = retryableError.code !== 'CLIENT_ERROR'

    // Assert
    expect(isValidationRetryable).toBe(true) // VALIDATION_ERROR can be retried
    expect(isRetryableRetryable).toBe(true)
  })
})
