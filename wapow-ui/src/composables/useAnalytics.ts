/**
 * Vue composable for analytics event tracking.
 *
 * Wraps the EventTracker singleton with convenient methods
 * for common interactions and automatic dwell-time measurement.
 */

import { onUnmounted, ref } from 'vue'
import { tracker, type AnalyticsEvent } from '@/lib/analytics'

export function useAnalytics() {
  // ── Dwell-time tracking ──────────────────────────────────────────────

  const dwellTimers = ref<Map<string, { start: number; contentType: string; category: string }>>(
    new Map(),
  )

  /** Start measuring dwell time for a content item. */
  function startDwell(contentId: string, contentType = '', category = '') {
    dwellTimers.value.set(contentId, {
      start: performance.now(),
      contentType,
      category,
    })
  }

  /** Stop measuring dwell time and emit a 'dwell' event. */
  function stopDwell(contentId: string) {
    const entry = dwellTimers.value.get(contentId)
    if (!entry) return
    const dwellMs = Math.round(performance.now() - entry.start)
    dwellTimers.value.delete(contentId)

    if (dwellMs < 300) return // ignore very short dwells (accidental swipes)

    tracker.track('dwell', {
      content_id: contentId,
      content_type: entry.contentType,
      category: entry.category,
      properties: { dwell_time_ms: dwellMs },
    })
  }

  /** Stop all active dwell timers (e.g. on unmount). */
  function stopAllDwells() {
    for (const id of dwellTimers.value.keys()) {
      stopDwell(id)
    }
  }

  // ── Convenience trackers ─────────────────────────────────────────────

  function trackView(contentId: string, contentType = '', category = '') {
    tracker.track('view', {
      content_id: contentId,
      content_type: contentType,
      category,
    })
  }

  function trackLike(contentId: string, liked: boolean, contentType = '', category = '') {
    tracker.track('like', {
      content_id: contentId,
      content_type: contentType,
      category,
      properties: { liked },
    })
  }

  function trackSave(contentId: string, saved: boolean, contentType = '', category = '') {
    tracker.track('save', {
      content_id: contentId,
      content_type: contentType,
      category,
      properties: { saved },
    })
  }

  function trackShare(contentId: string, shareMethod = '', contentType = '', category = '') {
    tracker.track('share', {
      content_id: contentId,
      content_type: contentType,
      category,
      properties: { share_method: shareMethod },
    })
  }

  function trackComment(contentId: string, commentId: string, contentType = '', category = '') {
    tracker.track('comment', {
      content_id: contentId,
      content_type: contentType,
      category,
      properties: { comment_id: commentId },
    })
  }

  function trackScrollDepth(contentId: string, depthPercent: number, contentType = '', category = '') {
    tracker.track('scroll_depth', {
      content_id: contentId,
      content_type: contentType,
      category,
      properties: { depth_percent: Math.round(depthPercent) },
    })
  }

  function trackVideoProgress(
    contentId: string,
    progressPercent: number,
    watchTimeMs: number,
    category = '',
  ) {
    tracker.track('video_progress', {
      content_id: contentId,
      content_type: 'video',
      category,
      properties: {
        progress_percent: Math.round(progressPercent),
        watch_time_ms: Math.round(watchTimeMs),
      },
    })
  }

  function trackAudioProgress(
    contentId: string,
    progressPercent: number,
    listenTimeMs: number,
    category = '',
  ) {
    tracker.track('audio_progress', {
      content_id: contentId,
      content_type: 'podcast',
      category,
      properties: {
        progress_percent: Math.round(progressPercent),
        listen_time_ms: Math.round(listenTimeMs),
      },
    })
  }

  function trackNavigate(
    fromContentId: string,
    toContentId: string,
    direction: 'next' | 'prev',
  ) {
    tracker.track('navigate', {
      properties: {
        from_content_id: fromContentId,
        to_content_id: toContentId,
        direction,
      },
    })
  }

  function trackSearch(query: string, resultsCount: number) {
    tracker.track('search', {
      properties: { query, results_count: resultsCount },
    })
  }

  // ── Cleanup on unmount ───────────────────────────────────────────────

  onUnmounted(() => {
    stopAllDwells()
  })

  return {
    // raw
    track: tracker.track.bind(tracker),
    // dwell
    startDwell,
    stopDwell,
    stopAllDwells,
    // convenience
    trackView,
    trackLike,
    trackSave,
    trackShare,
    trackComment,
    trackScrollDepth,
    trackVideoProgress,
    trackAudioProgress,
    trackNavigate,
    trackSearch,
  }
}
