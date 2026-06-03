# ADR-004: Monitoring & Error Tracking

**Date**: 2026-05-31  
**Status**: ACCEPTED  
**Context**: Frontend Web Unit — Small team (2-3 devs) needs visibility into production issues  
**Decision Makers**: Frontend Team + IT Operations

---

## 📋 PROBLEM STATEMENT

**Requirements:**
1. Detect production errors before users report them
2. Monitor performance (page load, photo validation, sync speed)
3. Track user behavior (which pages used, sync failures)
4. Must be lightweight (small bundle impact)
5. Must respect user privacy (internal/public data only)
6. Minimal cost (small team, small scale 10-20 users)

Options:
- **Sentry**: Full-featured error tracking (paid, $29/month minimum)
- **LogRocket**: Session replay + errors (paid, $99/month minimum)
- **Custom logging**: Build own (risky, hard to maintain)
- **Google Analytics**: Analytics + errors (free/cheap, privacy concerns)
- **Lightweight DIY**: Simple error reporting to backend + logs (custom but clean)

---

## 🎯 DECISION

**Use hybrid approach:**
- **Error tracking**: Simple custom solution (POST errors to backend)
- **Performance monitoring**: Custom metrics (Core Web Vitals)
- **User analytics**: Simple event logging (no session replay)
- **Logging**: Browser console + backend logs (free)
- **Alerting**: Slack webhook for critical errors

```
Architecture:
┌──────────────────┐
│ Browser App      │
│ (React)          │
└────────┬─────────┘
         │ Error/Log
         │ Event
         ↓
┌──────────────────────────────────────────┐
│ Error Tracking Service (Custom)          │
│ ├─ Catch uncaught errors                 │
│ ├─ Track validation failures             │
│ ├─ Measure performance (photo validation)│
│ └─ POST to /api/errors endpoint          │
└────────┬─────────────────────────────────┘
         │
         ↓
┌──────────────────────────────────────────┐
│ Backend Logging                          │
│ ├─ Store errors in database              │
│ ├─ Alert on critical errors (Slack)      │
│ └─ Dashboard: Error frequency/patterns   │
└──────────────────────────────────────────┘
```

---

## 🏗️ IMPLEMENTATION DETAILS

### Error Tracking Service

```typescript
// services/error-tracking.ts
export interface ErrorReport {
  errorId: string
  timestamp: string
  message: string
  stack?: string
  context: {
    url: string
    userRole?: string
    userId?: string
    userEmail?: string
    appVersion: string
  }
  severity: 'ERROR' | 'WARNING' | 'INFO'
  metadata?: Record<string, any>
}

class ErrorTrackingService {
  private queue: ErrorReport[] = []
  private isOnline = navigator.onLine

  constructor() {
    // Listen for online/offline
    window.addEventListener('online', () => {
      this.isOnline = true
      this.flushQueue()
    })
    window.addEventListener('offline', () => {
      this.isOnline = false
    })

    // Catch uncaught errors
    window.addEventListener('error', (event) => {
      this.captureError(
        event.message,
        event.error?.stack,
        'ERROR'
      )
    })

    // Catch unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.captureError(
        event.reason?.message || String(event.reason),
        event.reason?.stack,
        'ERROR'
      )
    })

    // Flush queue every 30 seconds
    setInterval(() => {
      if (this.isOnline && this.queue.length > 0) {
        this.flushQueue()
      }
    }, 30000)
  }

  captureError(
    message: string,
    stack?: string,
    severity: 'ERROR' | 'WARNING' = 'ERROR',
    metadata?: Record<string, any>
  ) {
    const report: ErrorReport = {
      errorId: uuid(),
      timestamp: new Date().toISOString(),
      message,
      stack,
      context: {
        url: window.location.href,
        userRole: useAuthStore.getState().user?.role,
        userId: useAuthStore.getState().user?.id,
        userEmail: useAuthStore.getState().user?.email,
        appVersion: APP_VERSION
      },
      severity,
      metadata
    }

    console.error('[ErrorTracking]', report)

    // Add to queue (will retry if offline)
    this.queue.push(report)

    // Try to send immediately (don't wait)
    if (this.isOnline) {
      this.flushQueue()
    }

    // Alert Slack for critical errors
    if (severity === 'ERROR' && useAuthStore.getState().user?.role === 'ADMIN') {
      this.alertSlack(report)
    }
  }

  private async flushQueue() {
    while (this.queue.length > 0) {
      const report = this.queue[0]

      try {
        await fetch('https://api.company.local/api/errors', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(report)
        })

        // Remove from queue on success
        this.queue.shift()

      } catch (err) {
        console.warn('[ErrorTracking] Failed to send error report:', err)
        break  // Stop trying others if one fails
      }
    }
  }

  private async alertSlack(report: ErrorReport) {
    // Only alert if critical
    try {
      await fetch('https://hooks.slack.com/...', {
        method: 'POST',
        body: JSON.stringify({
          text: `🚨 ${report.severity}: ${report.message}`,
          attachments: [{
            color: 'danger',
            fields: [
              { title: 'Error ID', value: report.errorId },
              { title: 'User', value: report.context.userEmail || 'Unknown' },
              { title: 'URL', value: report.context.url },
              { title: 'Stack', value: `\`\`\`${report.stack}\`\`\`` }
            ]
          }]
        })
      })
    } catch (err) {
      console.warn('[ErrorTracking] Failed to alert Slack:', err)
    }
  }
}

export const errorTracking = new ErrorTrackingService()

// Usage in components/services
try {
  await photoValidationService.validate(photo)
} catch (err) {
  errorTracking.captureError(
    `Photo validation failed: ${err.message}`,
    err.stack,
    'ERROR',
    { photoSize: photo.size, photoFormat: photo.type }
  )
}
```

### Performance Monitoring

```typescript
// services/performance-monitoring.ts
class PerformanceMonitor {
  captureMetrics() {
    // Core Web Vitals
    if ('web-vital' in window) {
      // LCP (Largest Contentful Paint)
      window.addEventListener('largest-contentful-paint', (entry) => {
        const lcp = entry.renderTime || entry.loadTime
        console.log(`[Performance] LCP: ${lcp}ms`)

        if (lcp > 2500) {
          errorTracking.captureError(
            `LCP exceeded threshold: ${lcp}ms`,
            null,
            'WARNING',
            { metric: 'LCP', value: lcp }
          )
        }
      })
    }

    // Photo validation timing
    const origValidate = photoValidationService.validate
    photoValidationService.validate = async (photo) => {
      const start = performance.now()
      const result = await origValidate(photo)
      const duration = performance.now() - start

      console.log(`[Performance] Photo validation: ${duration}ms`)

      if (duration > 500) {
        errorTracking.captureError(
          `Photo validation slow: ${duration}ms`,
          null,
          'WARNING',
          { metric: 'PHOTO_VALIDATION', value: duration, photoSize: photo.size }
        )
      }

      return result
    }
  }

  captureNetworkTiming(endpoint: string, method: string, durationMs: number) {
    console.log(`[Performance] ${method} ${endpoint}: ${durationMs}ms`)

    if (durationMs > 5000) {
      errorTracking.captureError(
        `API call slow: ${method} ${endpoint} (${durationMs}ms)`,
        null,
        'WARNING',
        { endpoint, method, duration: durationMs }
      )
    }
  }
}

export const performanceMonitor = new PerformanceMonitor()
performanceMonitor.captureMetrics()

// Wrap API calls
const api = axios.create({
  baseURL: 'https://api.company.local'
})

api.interceptors.request.use((config) => {
  config.metadata = { startTime: performance.now() }
  return config
})

api.interceptors.response.use(
  (response) => {
    const duration = performance.now() - response.config.metadata.startTime
    performanceMonitor.captureNetworkTiming(
      response.config.url,
      response.config.method?.toUpperCase(),
      duration
    )
    return response
  },
  (error) => {
    const duration = performance.now() - error.config.metadata.startTime
    performanceMonitor.captureNetworkTiming(
      error.config.url,
      error.config.method?.toUpperCase(),
      duration
    )
    return Promise.reject(error)
  }
)
```

### User Analytics (Simple Event Logging)

```typescript
// services/analytics.ts
export interface AnalyticsEvent {
  eventName: string
  timestamp: string
  userId?: string
  userRole?: string
  properties?: Record<string, any>
}

class Analytics {
  private queue: AnalyticsEvent[] = []

  trackEvent(
    eventName: string,
    properties?: Record<string, any>
  ) {
    const event: AnalyticsEvent = {
      eventName,
      timestamp: new Date().toISOString(),
      userId: useAuthStore.getState().user?.id,
      userRole: useAuthStore.getState().user?.role,
      properties
    }

    console.log('[Analytics]', event)
    this.queue.push(event)

    // Batch send every 60 seconds
    if (this.queue.length > 0 && this.queue.length % 50 === 0) {
      this.flush()
    }
  }

  private async flush() {
    if (this.queue.length === 0) return

    try {
      await fetch('https://api.company.local/api/analytics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ events: this.queue })
      })

      this.queue = []

    } catch (err) {
      console.warn('[Analytics] Failed to send events:', err)
    }
  }
}

export const analytics = new Analytics()

// Track key events
analytics.trackEvent('INSPECTION_CREATED', { loteId: '...' })
analytics.trackEvent('PHOTO_UPLOADED', { photoSize: 500000 })
analytics.trackEvent('SYNC_COMPLETED', { itemCount: 5 })
analytics.trackEvent('SYNC_FAILED', { retryCount: 3, error: '...' })
```

### Backend Error Logging Endpoint

```python
# backend: routes/errors.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

router = APIRouter(prefix="/api/errors")
logger = logging.getLogger(__name__)

class ErrorReport(BaseModel):
    errorId: str
    timestamp: str
    message: str
    stack: Optional[str]
    context: dict
    severity: str
    metadata: Optional[dict]

@router.post("")
async def log_error(report: ErrorReport):
    """Log frontend errors to backend for monitoring"""
    
    logger.error(f"Frontend Error [{report.severity}]: {report.message}", extra={
        "errorId": report.errorId,
        "userId": report.context.get("userId"),
        "userEmail": report.context.get("userEmail"),
        "stack": report.stack,
        "metadata": report.metadata
    })
    
    # Alert Slack if critical
    if report.severity == "ERROR":
        await slack_service.send_alert(
            f"🚨 {report.message}",
            {
                "Error ID": report.errorId,
                "User": report.context.get("userEmail", "Unknown"),
                "URL": report.context.get("url"),
                "Stack": report.stack[:500]  # Truncate
            }
        )
    
    return {"status": "logged"}
```

---

## ✅ BENEFITS

1. **Zero Cost**: No paid services (except Slack, which is cheap)
2. **Simple**: Custom solution is lightweight, focused
3. **Privacy**: No session replay, minimal data collection
4. **Actionable**: Errors + performance metrics tell clear story
5. **Real-time Alerts**: Critical errors trigger Slack notifications
6. **Local Logs**: Browser console + backend logs for debugging

---

## ⚠️ TRADEOFFS

1. **No Session Replay**: Can't see user actions before error
   - Mitigation: Not needed for small team, focus on logs + repro steps
   
2. **Manual Dashboard**: No out-of-box UI for error tracking
   - Mitigation: Build simple admin page or use Grafana
   
3. **Limited Scope**: Only captures errors we explicitly track
   - Mitigation: Global error handlers + API interceptors catch most

---

## 📊 ADMIN DASHBOARD (Optional)

```typescript
// admin/ErrorDashboard.tsx
// Simple React page showing:
// - Last 100 errors (paginated)
// - Error frequency (count)
// - Performance metrics (slow API calls, slow photo validation)
// - User impact (errors per user)
// - Filters: Date range, severity, user role

// Query backend: GET /api/admin/errors?startDate=...&endDate=...&severity=ERROR
```

---

**Status**: ✅ ACCEPTED  
**Implementation**: Custom error tracking service + performance monitoring + Slack alerts  
**Testing**: Error capture tests, performance timing tests, offline error queue tests
