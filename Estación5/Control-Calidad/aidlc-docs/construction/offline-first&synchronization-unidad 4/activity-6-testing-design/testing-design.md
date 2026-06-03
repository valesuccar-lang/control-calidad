# Actividad 6 — Pruebas: Diseño y Enfoques
## Unidad 4: Offline-First & Synchronization

**Fecha:** 2026-06-01  
**Versión:** 1.0  
**Estado:** Completado

---

## 1. Resumen Ejecutivo

La estrategia de pruebas para Unit 4 (Offline-First & Synchronization) se enfoca en garantizar la confiabilidad del sistema de sincronización en condiciones de red variables, manejo robusto de conflictos y persistencia de datos offline. Se implementa una pirámide de pruebas (70% unit, 20% integration, 10% E2E) con un objetivo de cobertura ≥85%.

**Componentes críticos:** Frontend sync orchestration, conflict resolution engine, queue persistence, WebSocket real-time updates, exponential backoff retry logic.

---

## 2. Pirámide de Pruebas

```
                    ▲
                   ╱ ╲
                  ╱   ╲  E2E Tests (10%)
                 ╱─────╲  Selenium, Playwright
                ╱       ╲  Critical user journeys
               ╱─────────╲
              ╱           ╲ Integration Tests (20%)
             ╱             ╲ Jest, Pytest, Supertest
            ╱───────────────╲ API endpoints, IndexedDB, SW
           ╱                 ╲
          ╱───────────────────╲ Unit Tests (70%)
         ╱ Jest, Pytest        ╲ Functions, hooks, services
        ╱───────────────────────╲
       ▼                         ▼
```

**Distribución de Pruebas:**
- **70% Unit Tests:** ~200 test cases
- **20% Integration Tests:** ~60 test cases
- **10% E2E Tests:** ~30 test cases
- **Total:** ~290 test cases
- **Cobertura Meta:** ≥85% líneas de código

---

## 3. Estrategia de Pruebas por Componente

### 3.1 Frontend - Tipos (sync.ts)

**Objetivo:** Validar que los tipos TypeScript son correctos y completos.

| Test | Tipo | Herramienta | Descripción |
|------|------|-------------|-------------|
| Type compilation | Unit | TypeScript compiler | Verificar que todos los tipos compilan sin errores |
| Enum values | Unit | Jest | Validar valores de enums (SyncStatus, OperationType, etc.) |
| Interface contracts | Unit | Jest | Verificar que interfaces tienen propiedades requeridas |
| Error classes | Unit | Jest | Validar jerarquía de errores y constructores |

**Ejemplo de test:**
```typescript
test('SyncStatus enum has correct values', () => {
  expect(SyncStatus.PENDING).toBe('PENDING')
  expect(SyncStatus.SYNCED).toBe('SYNCED')
  expect(SyncStatus.CONFLICT).toBe('CONFLICT')
  expect(SyncStatus.DEAD_LETTER).toBe('DEAD_LETTER')
})

test('ConflictError extends SyncError', () => {
  const conflict = { id: '1', sync_queue_item_id: '1' } as ConflictRecord
  const error = new ConflictError(conflict)
  expect(error).toBeInstanceOf(SyncError)
  expect(error.code).toBe('CONFLICT')
})
```

---

### 3.2 Frontend - Zustand Store (offlineStore.ts)

**Objetivo:** Validar state management, persistence, y network listeners.

| Test | Tipo | Herramienta | Descripción |
|------|------|-------------|-------------|
| Initial state | Unit | Jest | Verificar estado inicial correcto |
| Add queue item | Unit | Jest | Crear nuevo item con ID único y estado PENDING |
| Update queue item | Unit | Jest | Actualizar status, retry_count, etc. |
| Remove queue item | Unit | Jest | Eliminar item de la cola |
| Add/update/remove conflicts | Unit | Jest | Operaciones de conflictos |
| Network status updates | Unit | Jest | setOnline, setNetworkStatus |
| IndexedDB persistence | Integration | Jest + Mock | Verificar que datos persisten en IndexedDB |
| Window online/offline events | Integration | Jest + DOM | Simular eventos de red |
| Zustand subscription | Unit | Jest | Validar que subscribers reciben cambios |

**Casos de prueba críticos:**
```typescript
describe('OfflineStore', () => {
  test('addQueueItem creates item with PENDING status', () => {
    const store = useOfflineStore.getState()
    const id = store.addQueueItem({
      operation_type: OperationType.CREATE_INSPECTION,
      entity_type: 'INSPECTION',
      entity_id: 'e1',
      payload: { name: 'Test' }
    })
    const item = store.getQueueItems().find(i => i.id === id)
    expect(item?.status).toBe('PENDING')
    expect(item?.retry_count).toBe(0)
  })

  test('setOnline(true) triggers sync', async () => {
    const store = useOfflineStore.getState()
    const triggerSyncSpy = jest.spyOn(offlineStore, 'triggerSync')
    store.setOnline(true)
    expect(triggerSyncSpy).toHaveBeenCalled()
  })

  test('updateQueueItem persists to IndexedDB', async () => {
    const store = useOfflineStore.getState()
    const id = store.addQueueItem({...})
    store.updateQueueItem(id, { status: 'SYNCING' })
    // Verify in IndexedDB
    const db = await openDB()
    const item = await db.transaction('sync_queue').objectStore('sync_queue').get(id)
    expect(item.status).toBe('SYNCING')
  })

  test('queueStatus() calculates correct counts', () => {
    const store = useOfflineStore.getState()
    store.clearQueue()
    store.addQueueItem({...}) // PENDING
    store.addQueueItem({...}) // PENDING
    const status = store.queueStatus()
    expect(status.total).toBe(2)
    expect(status.pending).toBe(2)
  })
})
```

---

### 3.3 Frontend - Sync Service (syncService.ts)

**Objetivo:** Validar lógica de sincronización, conflictos, reintentos y batch processing.

| Test | Tipo | Herramienta | Descripción |
|------|------|-------------|-------------|
| startSync - offline check | Unit | Jest | Retorna si offline |
| startSync - already syncing | Unit | Jest | Retorna si ya está sincronizando |
| startSync - batch sizing | Unit | Jest | Calcula batch size basado en NetworkQuality |
| startSync - queue processing | Integration | Jest + Mock Fetch | Procesa items en batches |
| processBatch - Promise.allSettled | Unit | Jest | Maneja éxito y fallo de items |
| syncItem - POST to API | Integration | Jest + Mock Fetch | Envía item al servidor |
| syncItem - 200 response | Unit | Jest | Status SYNCED |
| syncItem - 409 conflict | Unit | Jest | Crea ConflictRecord |
| syncItem - 422 validation | Unit | Jest | Lanza ValidationError |
| syncItem - 5xx error | Unit | Jest | Marca para retry |
| syncItem - timeout | Unit | Jest | Cancela con AbortController |
| detect conflict | Unit | Jest | Compara versiones |
| 3-way merge | Unit | Jest | Realiza merge automático |
| Auto-merge success | Unit | Jest | No hay campos conflictivos |
| Auto-merge failure | Unit | Jest | Retorna null si hay overlaps |
| Schedule retry | Unit | Jest | Calcula backoff correcto |
| Max retries exceeded | Unit | Jest | Mueve a DEAD_LETTER |
| Resolve conflict API | Integration | Jest + Mock Fetch | POST a /resolve-conflict |

**Casos de prueba críticos:**
```typescript
describe('SyncService', () => {
  test('startSync returns immediately if offline', async () => {
    const store = useOfflineStore.getState()
    store.setOnline(false)
    await syncService.startSync()
    expect(store.isSyncing).toBe(false)
  })

  test('calculateBatchSize based on NetworkQuality', () => {
    expect(syncService['calculateBatchSize']('EXCELLENT')).toBe(20)
    expect(syncService['calculateBatchSize']('GOOD')).toBe(10)
    expect(syncService['calculateBatchSize']('POOR')).toBe(1)
    expect(syncService['calculateBatchSize']('OFFLINE')).toBe(0)
  })

  test('perform3WayMerge detects overlapping fields', () => {
    const conflict: ConflictRecord = {
      id: 'c1',
      sync_queue_item_id: 'i1',
      entity_type: 'INSPECTION',
      entity_id: 'e1',
      conflict_type: 'VERSION_MISMATCH',
      our_version: 2,
      server_version: 3,
      our_data: { name: 'Our Name', status: 'draft' },
      server_data: { name: 'Server Name', status: 'draft' },
      base_data: { name: 'Original', status: 'draft' },
      can_auto_merge: false,
      overlapping_fields: [],
      created_at: new Date(),
      expires_at: new Date(),
    }
    
    const merged = syncService['perform3WayMerge'](conflict)
    expect(merged).toBeNull() // name field conflicts
    expect(conflict.overlapping_fields).toContain('name')
  })

  test('perform3WayMerge succeeds without conflicts', () => {
    const conflict: ConflictRecord = {
      ...mockConflict,
      our_data: { name: 'Same', status: 'updated' },
      server_data: { name: 'Same', color: 'blue' },
      base_data: { name: 'Same', status: 'draft', color: 'red' },
    }
    
    const merged = syncService['perform3WayMerge'](conflict)
    expect(merged).toEqual({
      name: 'Same',
      status: 'updated', // our change
      color: 'blue', // their change
    })
  })

  test('scheduleRetry uses exponential backoff', () => {
    const item: SyncQueueItem = { ...mockItem, retry_count: 0 }
    syncService['scheduleRetry'](item)
    
    const updated = useOfflineStore.getState().getQueueItems('RETRY_PENDING')[0]
    expect(updated.retry_count).toBe(1)
    expect(updated.next_retry_at).toBeGreaterThan(new Date())
  })

  test('scheduleRetry moves to DEAD_LETTER after MAX_RETRIES', () => {
    const item: SyncQueueItem = { ...mockItem, retry_count: 5 }
    syncService['scheduleRetry'](item)
    
    const updated = useOfflineStore.getState().getQueueItems('DEAD_LETTER')[0]
    expect(updated.status).toBe('DEAD_LETTER')
  })

  test('syncItem cancels on timeout', async () => {
    const abortSpy = jest.spyOn(AbortController.prototype, 'abort')
    // Mock fetch to never resolve
    jest.spyOn(global, 'fetch').mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )
    
    const item = { ...mockItem }
    // This should timeout after SYNC_TIMEOUT_MS (10s)
    // In test, timeout is mocked to be shorter
    
    expect(abortSpy).toHaveBeenCalled()
  })
})
```

---

### 3.4 Frontend - React Components

#### SyncStatusBar.tsx

| Test | Tipo | Herramienta | Descripción |
|------|------|-------------|-------------|
| Render offline state | Unit | React Testing Library | Muestra "Offline" con icono rojo |
| Render syncing state | Unit | React Testing Library | Muestra "Syncing..." con spinner |
| Render conflict state | Unit | React Testing Library | Muestra contador de conflictos |
| Render synced state | Unit | React Testing Library | Muestra "Synced" con checkmark |
| Update on store change | Integration | React Testing Library | Re-renderiza al cambiar estado |
| Format last sync time | Unit | Jest | "Just now", "5 mins ago", etc. |
| Compact mode | Unit | React Testing Library | Modo compacto vs expandido |

#### ConflictResolutionModal.tsx

| Test | Tipo | Herramienta | Descripción |
|------|------|-------------|-------------|
| Render conflict details | Unit | React Testing Library | Muestra ours vs theirs |
| Strategy selection | Unit | React Testing Library | Selecciona estrategia |
| Manual merge editing | Unit | React Testing Library | Edita valores en MANUAL_MERGE |
| KEEP_LOCAL strategy | Unit | React Testing Library | Mantiene versión local |
| USE_SERVER strategy | Unit | React Testing Library | Usa versión servidor |
| AUTO_MERGE strategy | Unit | React Testing Library | Intenta merge automático |
| Resolve conflict | Integration | React Testing Library + Mock | Llama API de resolución |
| Close modal | Unit | React Testing Library | onClose callback |

**Ejemplo:**
```typescript
describe('ConflictResolutionModal', () => {
  test('renders conflict details', () => {
    const conflict: ConflictRecord = {
      id: 'c1',
      our_data: { name: 'Local' },
      server_data: { name: 'Server' },
      // ...
    }
    
    render(
      <ConflictResolutionModal
        conflict={conflict}
        isOpen={true}
        onClose={jest.fn()}
      />
    )
    
    expect(screen.getByText('Local')).toBeInTheDocument()
    expect(screen.getByText('Server')).toBeInTheDocument()
  })

  test('resolves conflict with selected strategy', async () => {
    const onResolved = jest.fn()
    const syncServiceSpy = jest.spyOn(syncService, 'resolveConflict')
    
    render(
      <ConflictResolutionModal
        conflict={mockConflict}
        isOpen={true}
        onClose={jest.fn()}
        onResolved={onResolved}
      />
    )
    
    await userEvent.click(screen.getByRole('button', { name: 'KEEP_LOCAL' }))
    await userEvent.click(screen.getByRole('button', { name: 'Resolve' }))
    
    expect(syncServiceSpy).toHaveBeenCalledWith(
      mockConflict.sync_queue_item_id,
      'KEEP_LOCAL',
      undefined
    )
    expect(onResolved).toHaveBeenCalledWith(mockConflict.id)
  })
})
```

---

### 3.5 Frontend - Hooks (useSync.ts)

| Test | Tipo | Herramienta | Descripción |
|------|------|-------------|-------------|
| Hook initialization | Unit | Jest + renderHook | Estado inicial correcto |
| addItem | Unit | Jest + renderHook | Crea queue item y dispara sync |
| removeItem | Unit | Jest + renderHook | Elimina item de cola |
| clearQueue | Unit | Jest + renderHook | Limpia toda la cola |
| startSync | Integration | Jest + renderHook | Llama a syncService |
| triggerManualSync | Unit | Jest + renderHook | Dispara sync manualmente |
| cancelSync | Unit | Jest + renderHook | Cancela item específico |
| resolveConflict | Integration | Jest + renderHook | Resuelve conflicto |
| getUnresolvedConflicts | Unit | Jest + renderHook | Retorna conflictos sin resolver |
| getDeadLetterItems | Unit | Jest + renderHook | Retorna items en DEAD_LETTER |
| Subscription updates | Unit | Jest + renderHook | Se actualiza al cambiar store |

---

### 3.6 Frontend - Service Worker (service-worker.ts)

| Test | Tipo | Herramienta | Descripción |
|------|------|-------------|-------------|
| Cache on install | Unit | Service Worker API | Cachea URLs en INSTALL |
| Clean old caches | Unit | Service Worker API | Elimina caches antiguos |
| Network-first for API | Integration | Service Worker API | Fetch API, fallback cache |
| Cache-first for assets | Integration | Service Worker API | Fetch assets, fallback cache |
| Message handling | Unit | Service Worker API | Procesa START_SYNC message |
| Periodic sync | Integration | Service Worker API | Dispara sync periódicamente |
| Push notifications | Unit | Service Worker API | Muestra notificaciones |
| Notification click | Unit | Service Worker API | Abre app en click |

---

### 3.7 Backend - Models (sync_models.py)

| Test | Tipo | Herramienta | Descripción |
|------|------|-------------|-------------|
| SyncQueueItem creation | Unit | Pytest | Crea item con valores correctos |
| Default values | Unit | Pytest | status=PENDING, retry_count=0 |
| to_dict serialization | Unit | Pytest | Convierte a dict correctamente |
| Timestamps | Unit | Pytest | created_at se asigna automáticamente |
| Enums | Unit | Pytest | OperationType, SyncStatus enums |
| Relationships | Unit | Pytest + SQLAlchemy | FK relationships |

---

### 3.8 Backend - Repositories (sync_repositories.py)

| Test | Tipo | Herramienta | Descripción |
|------|------|-------------|-------------|
| Create sync queue item | Unit | Pytest | INSERT correcto |
| Get by ID | Unit | Pytest | SELECT by PK |
| Get by status | Unit | Pytest | WHERE status = X |
| Get pending and retry | Unit | Pytest | PENDING + RETRY_PENDING |
| Get ready for retry | Unit | Pytest | next_retry_at <= NOW |
| Update status | Unit | Pytest | UPDATE status |
| Schedule retry | Unit | Pytest | Set RETRY_PENDING + retry_count |
| Mark dead letter | Unit | Pytest | Mueve a DEAD_LETTER |
| Delete | Unit | Pytest | DELETE by ID |
| Delete by status | Unit | Pytest | DELETE batch por status |
| Queue stats | Unit | Pytest | Cuenta por status |
| Create conflict | Unit | Pytest | INSERT ConflictRecord |
| Get unresolved | Unit | Pytest | resolution_strategy IS NULL |
| Get expired | Unit | Pytest | expires_at <= NOW |
| Resolve conflict | Unit | Pytest | Set resolution_strategy |
| Conflict stats | Unit | Pytest | Cuenta conflictos |

**Ejemplo:**
```python
class TestSyncQueueRepository:
    def test_create_queue_item(self, db):
        repo = SyncQueueRepository(db)
        item = repo.create(
            operation_type='CREATE_INSPECTION',
            entity_type='INSPECTION',
            entity_id='e1',
            payload={'name': 'Test'},
            user_id='u1'
        )
        
        assert item.id is not None
        assert item.status == SyncStatus.PENDING
        assert item.retry_count == 0
        
        # Verify in DB
        fetched = repo.get_by_id(item.id)
        assert fetched.payload == {'name': 'Test'}

    def test_schedule_retry_with_backoff(self, db):
        repo = SyncQueueRepository(db)
        item = repo.create(...)
        
        next_retry = datetime.utcnow() + timedelta(milliseconds=5000)
        repo.schedule_retry(item.id, 1, next_retry)
        
        updated = repo.get_by_id(item.id)
        assert updated.status == SyncStatus.RETRY_PENDING
        assert updated.retry_count == 1
        assert updated.next_retry_at == next_retry

    def test_get_queue_stats(self, db):
        repo = SyncQueueRepository(db)
        repo.create(..., 'u1')  # PENDING
        repo.create(..., 'u1')  # PENDING
        
        stats = repo.get_queue_stats('u1')
        assert stats['total'] == 2
        assert stats['pending'] == 2
        assert stats['synced'] == 0
```

---

### 3.9 Backend - Services (sync_service.py, conflict_resolution_service.py)

| Test | Tipo | Herramienta | Descripción |
|------|------|-------------|-------------|
| Process sync item | Integration | Pytest | Flujo completo de sincronización |
| Validate payload | Unit | Pytest | Verifica estructura |
| Detect conflict | Unit | Pytest | Compara versiones |
| Apply changes | Unit | Pytest | Actualiza dominio |
| Handle operations | Unit | Pytest | CREATE, UPDATE, SUBMIT, etc. |
| 3-way merge | Unit | Pytest | Merge sin conflictos |
| Merge with overlaps | Unit | Pytest | Retorna None si hay overlaps |
| Auto-resolve | Unit | Pytest | ResolutionStrategy.AUTO_MERGE |
| Manual merge | Unit | Pytest | ResolutionStrategy.MANUAL_MERGE |
| Conflict analysis | Unit | Pytest | Estadísticas de conflictos |
| Suggest resolution | Unit | Pytest | Sugiere estrategia |
| Cleanup expired | Unit | Pytest | Elimina conflictos expirados |

**Ejemplo:**
```python
class TestConflictResolutionService:
    def test_3way_merge_no_conflicts(self, db):
        service = ConflictResolutionService(db)
        
        conflict = ConflictRecord(
            our_data={'name': 'Updated', 'status': 'draft'},
            server_data={'name': 'Updated', 'color': 'blue'},
            base_data={'name': 'Original', 'status': 'draft', 'color': 'red'},
            # ...
        )
        
        merged = service.perform_3way_merge(conflict)
        assert merged == {
            'name': 'Updated',  # Both same
            'status': 'draft',  # Only we changed
            'color': 'blue',    # Only they changed
        }

    def test_3way_merge_with_conflicts(self, db):
        service = ConflictResolutionService(db)
        
        conflict = ConflictRecord(
            our_data={'name': 'Our Name'},
            server_data={'name': 'Server Name'},
            base_data={'name': 'Original'},
            # ...
        )
        
        merged = service.perform_3way_merge(conflict)
        assert merged is None  # name field conflicts
        assert 'name' in conflict.overlapping_fields
```

---

### 3.10 Backend - API Routes (sync_routes.py)

| Test | Tipo | Herramienta | Descripción |
|------|------|-------------|-------------|
| POST /sync/items | Integration | Pytest + Supertest | Envía item a cola |
| GET /sync/status | Integration | Pytest + Supertest | Obtiene estado de cola |
| GET /sync/queue | Integration | Pytest + Supertest | Lista items de usuario |
| DELETE /sync/queue/:id | Integration | Pytest + Supertest | Elimina item |
| GET /sync/conflicts | Integration | Pytest + Supertest | Lista conflictos |
| POST /sync/resolve-conflict | Integration | Pytest + Supertest | Resuelve conflicto |
| GET /sync/conflicts/:id/analysis | Integration | Pytest + Supertest | Analiza conflicto |
| Auth validation | Integration | Pytest + Supertest | Rechaza sin token |
| Authorization | Integration | Pytest + Supertest | No puede acceder items de otros |
| Error handling | Unit | Pytest | 400, 404, 422, 500 responses |

**Ejemplo:**
```python
class TestSyncRoutes:
    def test_post_sync_item(self, client, db, user_token):
        response = client.post(
            '/api/v1/sync/items',
            json={
                'operation_type': 'CREATE_INSPECTION',
                'entity_id': 'e1',
                'payload': {'name': 'Test', 'version': 1}
            },
            headers={'Authorization': f'Bearer {user_token}'}
        )
        
        assert response.status_code == 200
        assert response.json()['id'] is not None
        assert response.json()['sync_status'] == 'PENDING'

    def test_get_sync_status(self, client, user_token):
        response = client.get(
            '/api/v1/sync/status',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'queue_status' in data
        assert 'total' in data['queue_status']

    def test_resolve_conflict_manual_merge(self, client, user_token, db):
        # Create conflict first
        conflict = create_test_conflict(db)
        
        response = client.post(
            '/api/v1/sync/resolve-conflict',
            json={
                'conflict_id': conflict.id,
                'resolution_strategy': 'MANUAL_MERGE',
                'resolved_data': {'name': 'Merged', 'status': 'approved'}
            },
            headers={'Authorization': f'Bearer {user_token}'}
        )
        
        assert response.status_code == 200
        
        # Verify conflict is resolved
        updated = db.query(ConflictRecord).filter_by(id=conflict.id).first()
        assert updated.resolution_strategy == ResolutionStrategy.MANUAL_MERGE
```

---

### 3.11 Backend - WebSocket (sync_websocket.py)

| Test | Tipo | Herramienta | Descripción |
|------|------|-------------|-------------|
| Connect | Unit | Pytest + WebSocket mock | Registra conexión |
| Disconnect | Unit | Pytest + WebSocket mock | Desregistra conexión |
| Broadcast sync started | Unit | Pytest | Envía mensaje a clientes |
| Broadcast item progress | Unit | Pytest | Actualización de item |
| Broadcast conflict | Unit | Pytest | Notifica conflicto detectado |
| Broadcast sync completed | Unit | Pytest | Notifica fin de sync |
| PING/PONG | Unit | Pytest + WebSocket | Keep-alive |
| REQUEST_STATUS | Unit | Pytest + WebSocket | Solicita actualización |
| TRIGGER_SYNC | Unit | Pytest + WebSocket | Dispara sync manual |
| Multiple connections | Integration | Pytest | Maneja múltiples sockets por usuario |
| Cleanup on error | Unit | Pytest | Desconecta en error |

---

## 4. Escenarios Críticos de Prueba

### 4.1 Flujo Offline a Online
```
1. App inicia offline
   - Service Worker cachea recursos
   - IndexedDB carga estado previo
   - Queue items esperan sincronización
   
2. Usuario edita dato
   - Se agrega a SyncQueue con status PENDING
   - IndexedDB persiste cambio
   - SyncStatusBar muestra "offline"
   
3. Red se conecta
   - Event listener dispara setOnline(true)
   - triggerSync() envía mensaje a Service Worker
   - SyncService.startSync() inicia procesamiento
   
4. Sincronización exitosa
   - Items POST a /api/v1/sync/items
   - Respuesta 200 → status SYNCED
   - SyncStatusBar actualiza a "synced"
```

### 4.2 Detección y Resolución de Conflictos
```
1. Version conflict
   - Our version: 2, Server version: 3
   - syncItem recibe 409 Conflict
   - createConflictRecord() almacena conflicto
   
2. 3-way merge attempt
   - Base: {name: 'Original', status: 'draft'}
   - Ours: {name: 'Updated', status: 'draft'}
   - Theirs: {name: 'Updated', color: 'blue'}
   - Result: Merge automático exitoso
   
3. Manual merge
   - Overlapping fields: ['status']
   - User ve ConflictResolutionModal
   - Selecciona MANUAL_MERGE
   - Edita valores conflictivos
   - POST a /api/v1/sync/resolve-conflict
   - Item re-entra a RETRY_PENDING
```

### 4.3 Reintentos con Backoff Exponencial
```
Intento 1: Fail → Retry en 5s
Intento 2: Fail → Retry en 10s
Intento 3: Fail → Retry en 30s
Intento 4: Fail → Retry en 60s
Intento 5: Fail → Retry en 60s
Intento 6: Max retries → DEAD_LETTER
```

### 4.4 Batching Inteligente por Calidad de Red
```
EXCELLENT (latency < 50ms):  20 items/batch
GOOD (latency 50-150ms):     10 items/batch
POOR (latency 150-300ms):    1 item/batch, 1s delay
VERY_POOR (latency > 300ms): 1 item/batch, 1s delay
OFFLINE:                     0 items (espera conexión)
```

### 4.5 Dead Letter Queue
```
Item creado
  ↓
Validación falla → DEAD_LETTER inmediatamente
Item entra a sincronización
  ↓
Error retryable → RETRY_PENDING con backoff
  ↓
Max retries alcanzado → DEAD_LETTER
  
Dead letter items pueden ser:
- Eliminados manualmente
- Re-sincronizados después de investigación
- Reportados a administrador
```

---

## 5. Herramientas y Frameworks

### Frontend Testing Stack
```
├── Jest                    # Test runner, unit tests
├── React Testing Library   # Component testing
├── @testing-library/hooks # Hook testing (renderHook)
├── Fetch Mock            # Mock API responses
├── IndexedDB Mock        # Mock database
├── Service Worker Mock   # Service Worker testing
├── Supertest             # HTTP assertions
└── Playwright            # E2E testing
```

### Backend Testing Stack
```
├── Pytest                 # Test runner
├── Pytest-asyncio        # Async test support
├── Pytest-cov            # Coverage reporting
├── SQLAlchemy-utils      # Test utilities
├── FastAPI TestClient    # API testing
├── WebSocket-client      # WebSocket testing
└── Faker                 # Test data generation
```

---

## 6. Cobertura de Código

### Meta de Cobertura
- **Líneas:** ≥85%
- **Branches:** ≥80%
- **Functions:** ≥90%
- **Statements:** ≥85%

### Exclusiones Justificadas
- Error handling code paths que no pueden ser triggered en test
- Mock data utilities
- Type definitions (TypeScript)
- Console.log statements

### Métricas por Componente

| Componente | Líneas | Branches | Functions |
|-----------|--------|----------|-----------|
| sync.ts | 100% | 100% | 100% |
| offlineStore.ts | 90% | 85% | 95% |
| syncService.ts | 88% | 82% | 92% |
| SyncStatusBar.tsx | 92% | 88% | 95% |
| ConflictResolutionModal.tsx | 90% | 85% | 93% |
| useSync.ts | 95% | 90% | 100% |
| service-worker.ts | 85% | 80% | 88% |
| sync_models.py | 100% | 100% | 100% |
| sync_repositories.py | 88% | 85% | 90% |
| sync_service.py | 86% | 82% | 88% |
| conflict_resolution_service.py | 87% | 83% | 90% |
| sync_routes.py | 85% | 80% | 88% |
| sync_websocket.py | 84% | 79% | 87% |
| **TOTAL** | **≥85%** | **≥80%** | **≥90%** |

---

## 7. Plan de Ejecución de Pruebas

### Fase 1: Unit Tests (Semana 1-2)
- Pruebas de tipos e interfaces
- Lógica de sincronización
- Algoritmo de 3-way merge
- Reintentos y backoff
- State management

### Fase 2: Integration Tests (Semana 3)
- Store ↔ API communication
- IndexedDB persistence
- Service Worker lifecycle
- WebSocket connections
- Batch processing

### Fase 3: E2E Tests (Semana 4)
- Flujos offline → online
- Manejo de conflictos end-to-end
- Reintentos automáticos
- Real-time updates via WebSocket
- Network quality detection

### Fase 4: Performance & Load (Semana 5)
- Sincronización de 1000+ items
- Manejo de 100+ conflictos
- Consumo de memoria en IndexedDB
- WebSocket scalability

---

## 8. Criterios de Éxito

✅ **Todos los tests pasan**
- Unit tests: 100% pass rate
- Integration tests: 100% pass rate
- E2E tests: 100% pass rate

✅ **Cobertura de código**
- Líneas: ≥85%
- Branches: ≥80%

✅ **Performance**
- Sync 100 items: < 5 segundos
- Conflict resolution: < 1 segundo
- WebSocket latency: < 100ms

✅ **Confiabilidad**
- Manejo de network failures
- Recuperación de errores
- Data persistence garantizada

---

## 9. Checklist de Pruebas

### Frontend
- [ ] Types compile sin errores
- [ ] Zustand store opera correctamente
- [ ] SyncService maneja offline/online
- [ ] Conflictos se detectan y resuelven
- [ ] Service Worker cachea recursos
- [ ] Components renderizan correctamente
- [ ] Hooks funcionan con Zustand
- [ ] Network quality detection funciona

### Backend
- [ ] Modelos ORM válidos
- [ ] Repositories CRUD operan
- [ ] Sync service procesa items
- [ ] Conflict resolution 3-way merge
- [ ] API routes autenticadas
- [ ] WebSocket broadcasts funciona
- [ ] Retry logic con backoff
- [ ] Cleanup de items expirados

### Integration
- [ ] Frontend ↔ Backend API sync
- [ ] Conflict detection entre versiones
- [ ] Auto-resolution funciona
- [ ] Manual resolution funciona
- [ ] WebSocket real-time updates
- [ ] Offline persistence con IndexedDB

### E2E
- [ ] Usuario puede editar offline
- [ ] Sync ocurre automáticamente online
- [ ] Conflictos se resuelven correctamente
- [ ] Network changes se detectan
- [ ] Dead letter items se manejan
- [ ] Multiple devices sincronizan

---

## 10. Referencias y Recursos

### Documentación
- [Jest Documentation](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/react)
- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-websockets/)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)

### Testing Best Practices
- Test behavior, not implementation
- Use meaningful assertion messages
- Keep tests focused and isolated
- Use proper mocking and stubbing
- Aim for deterministic tests
- Document complex test setups

---

**Documento preparado para Actividad 6: Pruebas (Testing Design & Approaches)**  
**Unidad 4: Offline-First & Synchronization**  
**Estado: Listo para implementación**
