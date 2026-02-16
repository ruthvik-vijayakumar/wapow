/**
 * WaPOW Event Tracker — batched analytics event sender.
 *
 * Collects user interaction events into a buffer and flushes them
 * to the collector service periodically or when the buffer is full.
 * Uses `navigator.sendBeacon` on page hide for reliability.
 */

const COLLECTOR_URL =
  import.meta.env.VITE_COLLECTOR_URL || 'http://localhost:3002'

const FLUSH_INTERVAL_MS = 5_000
const FLUSH_BUFFER_SIZE = 20

// Backoff: stop trying for a while after repeated failures
const MAX_CONSECUTIVE_FAILURES = 3
const BACKOFF_MS = 60_000 // 1 minute cooldown after failures

// ── Types ────────────────────────────────────────────────────────────────────

export interface AnalyticsEvent {
  event_type: string
  user_id?: string
  session_id?: string
  content_id?: string
  content_type?: string // 'article' | 'video' | 'podcast' | 'game'
  category?: string
  timestamp?: string
  properties?: Record<string, unknown>
  referrer?: string
}

// ── Session ID ───────────────────────────────────────────────────────────────

function getSessionId(): string {
  const key = 'wapow_session_id'
  let id = sessionStorage.getItem(key)
  if (!id) {
    id = crypto.randomUUID()
    sessionStorage.setItem(key, id)
  }
  return id
}

// ── Singleton Tracker ────────────────────────────────────────────────────────

class EventTracker {
  private buffer: AnalyticsEvent[] = []
  private flushTimer: ReturnType<typeof setInterval> | null = null
  private sessionId: string
  private userId: string = ''
  private started = false
  private consecutiveFailures = 0
  private backoffUntil = 0

  constructor() {
    this.sessionId = getSessionId()
  }

  /** Initialise the tracker. Call once in App.vue setup. */
  start(): void {
    if (this.started) return
    this.started = true

    this.flushTimer = setInterval(() => this.flush(), FLUSH_INTERVAL_MS)

    // Flush on page hide / beforeunload via sendBeacon
    document.addEventListener('visibilitychange', this.handleVisibility)
    window.addEventListener('beforeunload', this.handleUnload)
  }

  /** Stop the tracker and flush remaining events. */
  stop(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer)
      this.flushTimer = null
    }
    document.removeEventListener('visibilitychange', this.handleVisibility)
    window.removeEventListener('beforeunload', this.handleUnload)
    this.flush()
    this.started = false
  }

  /** Set the authenticated user ID (call when auth state changes). */
  setUserId(id: string): void {
    this.userId = id
  }

  /** Track an event. */
  track(eventType: string, data: Partial<AnalyticsEvent> = {}): void {
    const event: AnalyticsEvent = {
      event_type: eventType,
      timestamp: new Date().toISOString(),
      referrer: document.referrer,
      ...data,
      // Always use tracker-owned identity — never let callers override
      user_id: this.userId,
      session_id: this.sessionId,
    }
    this.buffer.push(event)

    if (this.buffer.length >= FLUSH_BUFFER_SIZE) {
      this.flush()
    }
  }

  /** Flush the buffer to the collector. */
  flush(): void {
    if (this.buffer.length === 0) return

    // If the collector is unreachable, skip until backoff expires
    if (this.consecutiveFailures >= MAX_CONSECUTIVE_FAILURES) {
      if (Date.now() < this.backoffUntil) return
      // Backoff expired — reset and try again
      this.consecutiveFailures = 0
    }

    const events = this.buffer.splice(0)
    const body = JSON.stringify({ events })

    // Prefer sendBeacon when the page is hidden (more reliable)
    if (document.visibilityState === 'hidden') {
      navigator.sendBeacon(`${COLLECTOR_URL}/collect/beacon`, body)
      return
    }

    fetch(`${COLLECTOR_URL}/collect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
      keepalive: true,
    })
      .then(() => {
        this.consecutiveFailures = 0
      })
      .catch(() => {
        this.consecutiveFailures++
        if (this.consecutiveFailures >= MAX_CONSECUTIVE_FAILURES) {
          this.backoffUntil = Date.now() + BACKOFF_MS
        }
        // Silently drop — analytics should never break the app
      })
  }

  // ── Internal handlers ────────────────────────────────────────────────

  private handleVisibility = (): void => {
    if (document.visibilityState === 'hidden') {
      this.flush()
    }
  }

  private handleUnload = (): void => {
    this.flush()
  }
}

// ── Singleton instance ───────────────────────────────────────────────────────

export const tracker = new EventTracker()
