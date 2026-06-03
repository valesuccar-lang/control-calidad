// frontend/service-worker.ts
// Service Worker for offline support and background sync orchestration

const CACHE_NAME = 'aidlc-offline-v1'
const SYNC_TAG = 'sync-queue'

const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png',
]

interface MessageEvent {
  type: string
  [key: string]: unknown
}

// Install event: cache essential files
self.addEventListener('install', (event: ExtendableEvent) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(urlsToCache).catch((err) => {
        console.warn('Failed to cache some assets:', err)
      })
    })
  )
  self.skipWaiting()
})

// Activate event: clean up old caches
self.addEventListener('activate', (event: ExtendableEvent) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((cacheName) => cacheName !== CACHE_NAME)
          .map((cacheName) => caches.delete(cacheName))
      )
    })
  )
  self.clients.claim()
})

// Fetch event: network-first for API, cache-first for assets
self.addEventListener('fetch', (event: FetchEvent) => {
  const { request } = event
  const url = new URL(request.url)

  if (request.method !== 'GET') {
    return
  }

  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirstStrategy(request))
  } else {
    event.respondWith(cacheFirstStrategy(request))
  }
})

// Message event: handle sync triggers from app
self.addEventListener('message', (event: ExtendableMessageEvent) => {
  const data = event.data as MessageEvent

  if (data.type === 'START_SYNC') {
    handleSyncStart()
  }

  if (data.type === 'SYNC_COMPLETE') {
    notifyClients({
      type: 'SYNC_STATUS',
      status: 'COMPLETED',
      timestamp: new Date().toISOString(),
    })
  }

  if (data.type === 'SKIP_WAITING') {
    self.skipWaiting()
  }
})

// Periodic background sync (if available)
self.addEventListener('periodicsync', (event: PeriodicSyncEvent) => {
  if (event.tag === SYNC_TAG) {
    event.waitUntil(triggerQueueSync())
  }
})

// Sync event for retried sync operations
self.addEventListener('sync', (event: SyncEvent) => {
  if (event.tag === SYNC_TAG) {
    event.waitUntil(triggerQueueSync())
  }
})

async function networkFirstStrategy(request: Request): Promise<Response> {
  try {
    const response = await fetch(request)
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME)
      cache.put(request, response.clone())
    }
    return response
  } catch (error) {
    const cached = await caches.match(request)
    if (cached) {
      return cached
    }
    return new Response('Offline - No cached response available', {
      status: 503,
      statusText: 'Service Unavailable',
    })
  }
}

async function cacheFirstStrategy(request: Request): Promise<Response> {
  const cached = await caches.match(request)
  if (cached) {
    return cached
  }

  try {
    const response = await fetch(request)
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME)
      cache.put(request, response.clone())
    }
    return response
  } catch (error) {
    return new Response('Offline - No cached response available', {
      status: 503,
      statusText: 'Service Unavailable',
    })
  }
}

async function triggerQueueSync(): Promise<void> {
  try {
    notifyClients({
      type: 'SYNC_STARTED',
      timestamp: new Date().toISOString(),
    })

    const response = await fetch('/api/v1/sync/status')
    if (!response.ok) {
      throw new Error('Failed to get sync status')
    }

    const data = await response.json() as Record<string, unknown>
    const queueStatus = data.queue_status as Record<string, unknown>

    if (typeof queueStatus === 'object' && queueStatus !== null) {
      const pending = (queueStatus as Record<string, unknown>).pending as number
      if (pending > 0) {
        await fetch('/api/v1/sync/items', { method: 'POST' })
      }
    }

    notifyClients({
      type: 'SYNC_PROGRESS',
      message: 'Sync completed',
      timestamp: new Date().toISOString(),
    })
  } catch (error) {
    console.error('Sync trigger failed:', error)
    notifyClients({
      type: 'SYNC_ERROR',
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString(),
    })
  }
}

function notifyClients(message: Record<string, unknown>): void {
  self.clients.matchAll().then((clients) => {
    clients.forEach((client) => {
      client.postMessage(message)
    })
  })
}

// Handle push notifications for sync updates
self.addEventListener('push', (event: PushEvent) => {
  if (!event.data) return

  const data = event.data.json() as Record<string, unknown>

  if (data.type === 'SYNC_COMPLETE') {
    const options: NotificationOptions = {
      icon: '/icon-192.png',
      badge: '/badge-72.png',
      tag: 'sync-notification',
    }

    event.waitUntil(
      self.registration.showNotification('Sync Complete', {
        ...options,
        body: `${(data.synced_count as number) || 0} items synced successfully`,
      })
    )
  }

  if (data.type === 'SYNC_CONFLICT') {
    const options: NotificationOptions = {
      icon: '/icon-192.png',
      badge: '/badge-72.png',
      tag: 'conflict-notification',
    }

    event.waitUntil(
      self.registration.showNotification('Sync Conflict Detected', {
        ...options,
        body: `${(data.conflict_count as number) || 0} conflicts need resolution`,
        actions: [
          {
            action: 'resolve',
            title: 'Resolve',
          },
        ],
      })
    )
  }
})

// Handle notification clicks
self.addEventListener('notificationclick', (event: NotificationEvent) => {
  event.notification.close()

  event.waitUntil(
    self.clients.matchAll({ type: 'window' }).then((clientList) => {
      for (const client of clientList) {
        if (client.url === '/' && 'focus' in client) {
          return (client as WindowClient).focus()
        }
      }

      if (self.clients.openWindow) {
        return self.clients.openWindow('/')
      }
    })
  )
})

declare const self: ServiceWorkerGlobalScope
