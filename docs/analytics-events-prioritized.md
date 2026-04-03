# WAPOW Frontend Analytics Events - Prioritized Tracking Plan

**Generated:** March 2, 2026  
**Purpose:** Comprehensive list of all user interactions that can be logged as analytics events

---

## ✅ ALREADY IMPLEMENTED (11 event types)

### Content Engagement
- `view` - Content views
- `dwell` - Time spent on content (>300ms threshold)
- `like` - Like/unlike actions
- `save` - Save/unsave content
- `share` - Share actions with method tracking
- `comment` - Comment posted

### Content Consumption
- `scroll_depth` - Article scroll progress (0-100%)
- `video_progress` - Video watch progress (25%, 50%, 75%, 100%)
- `audio_progress` - Podcast listen progress (25%, 50%, 75%, 100%)

### Navigation
- `navigate` - Navigation between stories (next/prev)
- `search` - Search query executed

---

## 🔴 HIGH PRIORITY - Missing Critical Events

### 1. Authentication & User Lifecycle
- `session_start` - User session begins (first page load)
- `session_end` - User session ends (page unload/visibility hidden)
- `login` - User signs in (with OAuth provider)
- `logout` - User signs out
- `signup` - New user registration
- `auth_callback` - OAuth callback completion

**Business Value:** Essential for user lifecycle analysis, retention metrics, and authentication funnel tracking.

### 2. Navigation & Routing
- `page_view` - Route change (track page name, from/to routes)
- `tab_click` - Bottom navigation tab selection (home, search, games, profile)
- `category_change` - Category selection/switch
- `back_button` - Back navigation

**Business Value:** Critical for understanding user navigation patterns, popular sections, and user journey mapping.

### 3. Content Discovery
- `content_tile_click` - Grid tile clicked (from home/category view)
- `recommendation_shown` - Recommendations displayed
- `recommendation_clicked` - Recommendation selected
- `trending_view` - Trending content viewed

**Business Value:** Essential for measuring recommendation engine effectiveness and content discovery patterns.

### 4. Feed Interactions
- `swipe` - Swipe gesture (direction: up/down/left/right)
- `story_complete` - User reached end of story
- `feed_scroll` - Scroll in feed/category view

**Business Value:** Core engagement metrics for the story-style feed interface.

---

## 🟡 MEDIUM PRIORITY - Important Engagement Events

### 5. Media Player Interactions
- `video_play` - Video playback started
- `video_pause` - Video playback paused
- `video_seek` - Video scrubbed/seeked
- `video_mute` - Video muted/unmuted
- `video_complete` - Video watched to end
- `audio_play` - Podcast playback started
- `audio_pause` - Podcast playback paused
- `audio_seek` - Podcast scrubbed/seeked
- `audio_complete` - Podcast listened to end

**Business Value:** Detailed media consumption analytics for video and podcast content optimization.

### 6. Article Reading
- `article_open` - Full article view opened
- `article_read_complete` - Article read to end (scroll depth 90%+)
- `page_turn` - Story page navigation (left/right)
- `poll_vote` - Poll option selected

**Business Value:** Understand article engagement depth and interactive element usage.

### 7. Social & Community
- `comments_open` - Comments sheet opened
- `comments_close` - Comments sheet closed
- `comment_vote` - Comment upvote/downvote
- `comment_reply` - Reply to comment started
- `ai_chat_open` - AI assistant tab opened
- `ai_message_sent` - Message sent to AI chatbot

**Business Value:** Measure community engagement and AI assistant adoption.

### 8. Search & Discovery
- `search_focus` - Search input focused
- `search_clear` - Search cleared
- `search_result_click` - Search result selected
- `search_no_results` - Search returned no results

**Business Value:** Optimize search functionality and understand search patterns.

### 9. Profile & Settings
- `profile_view` - Profile page viewed
- `theme_toggle` - Dark/light mode switched
- `reading_settings_open` - Reading settings accessed
- `categories_manage` - Category preferences opened
- `saved_view` - Saved content page viewed
- `pin_board_view` - Pin board accessed

**Business Value:** Track feature adoption and user preference patterns.

---

## 🟢 LOW PRIORITY - Nice to Have

### 10. Pin Board (Pinterest Feature)
- `pin_add` - Content pinned to board
- `pin_remove` - Content unpinned
- `pin_board_create` - New board created
- `pin_board_edit` - Board edited

**Business Value:** Measure Pinterest-style feature adoption and usage.

### 11. Games (Wordle)
- `game_start` - Game started
- `game_guess` - Guess submitted
- `game_complete` - Game finished (win/loss)
- `game_share` - Game result shared

**Business Value:** Track game engagement and viral sharing potential.

### 12. Content Metadata
- `category_follow` - Category followed
- `category_unfollow` - Category unfollowed
- `author_click` - Author name clicked
- `related_content_click` - Related content selected

**Business Value:** Understand content preferences and discovery patterns.

### 13. Error & Performance
- `error_occurred` - Client-side error
- `api_error` - API request failed
- `content_load_error` - Content failed to load
- `page_load_time` - Page load performance
- `api_response_time` - API latency tracking

**Business Value:** Monitor application health and identify technical issues.

### 14. Engagement Quality
- `bounce` - User left without interaction
- `rage_click` - Multiple rapid clicks (frustration)
- `dead_click` - Click on non-interactive element
- `scroll_depth_milestone` - 25%, 50%, 75%, 100% scroll

**Business Value:** Identify UX issues and engagement quality metrics.

### 15. User Preferences
- `notification_settings` - Notification preferences changed
- `privacy_settings` - Privacy settings accessed
- `account_settings` - Account settings changed
- `reading_history_view` - Reading history accessed

**Business Value:** Track settings usage and user customization patterns.

---

## 📊 SUMMARY BY PRIORITY

| Priority | Categories | Event Count | Business Value |
|----------|-----------|-------------|----------------|
| ✅ Implemented | 3 | 11 | Baseline tracking |
| 🔴 High | 4 | ~25 | Critical for recommendations & analytics |
| 🟡 Medium | 6 | ~35 | Important for engagement insights |
| 🟢 Low | 6 | ~30 | Nice to have for complete picture |

**Total Trackable Events:** ~100+

---

## 🎯 RECOMMENDED IMPLEMENTATION ORDER

### Phase 1 (Week 1) - Foundation
**Focus:** Authentication + Navigation  
**Events:** `session_start`, `session_end`, `login`, `logout`, `signup`, `page_view`, `tab_click`, `category_change`, `back_button`

**Why First:** These events provide the foundation for all other analytics. Session tracking enables cohort analysis, and navigation events are essential for understanding user journeys.

### Phase 2 (Week 2) - Content Discovery
**Focus:** Content Discovery + Feed Interactions  
**Events:** `content_tile_click`, `recommendation_shown`, `recommendation_clicked`, `swipe`, `story_complete`, `feed_scroll`

**Why Second:** These events directly measure the effectiveness of your recommendation engine and content discovery mechanisms.

### Phase 3 (Week 3) - Media Consumption
**Focus:** Media Player Interactions  
**Events:** `video_play`, `video_pause`, `video_complete`, `audio_play`, `audio_pause`, `audio_complete`, `video_seek`, `audio_seek`, `video_mute`

**Why Third:** Detailed media consumption metrics help optimize video and podcast content strategy.

### Phase 4 (Week 4) - Social & Search
**Focus:** Social Features + Search Refinements  
**Events:** `comments_open`, `comment_vote`, `comment_reply`, `ai_chat_open`, `ai_message_sent`, `search_focus`, `search_result_click`, `search_no_results`

**Why Fourth:** These events measure community engagement and search effectiveness.

### Phase 5 (Ongoing) - Polish & Monitoring
**Focus:** Error Tracking, Performance, Nice-to-haves  
**Events:** Error events, performance metrics, pin board, games, engagement quality

**Why Last:** These provide additional insights but aren't critical for core analytics.

---

## 🏗️ IMPLEMENTATION NOTES

### Existing Infrastructure
- **Event Tracker:** `lib/analytics.ts` - Batched event sending with backoff
- **Composable:** `composables/useAnalytics.ts` - Vue composable with convenience methods
- **Session Management:** Session ID persisted in sessionStorage
- **User Tracking:** User ID set when authenticated via Auth0

### Event Schema
```typescript
interface AnalyticsEvent {
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
```

### Backend Storage
- **Database:** ClickHouse
- **Table:** `wapow_analytics.events`
- **Materialized Views:** 
  - `content_engagement_hourly` - Content metrics aggregated by hour
  - `user_activity_daily` - User metrics aggregated by day

### Best Practices
1. Use `useAnalytics()` composable for consistency
2. Include `content_id`, `content_type`, and `category` when applicable
3. Use `properties` object for event-specific metadata
4. Keep event names lowercase with underscores
5. Track both success and failure states for critical actions

---

## 📈 EXPECTED IMPACT

### Immediate Benefits (Phase 1-2)
- Complete user journey mapping
- Session-based cohort analysis
- Recommendation engine effectiveness measurement
- Category preference insights

### Medium-term Benefits (Phase 3-4)
- Content consumption optimization
- Media engagement patterns
- Community feature adoption
- Search quality improvements

### Long-term Benefits (Phase 5)
- Proactive error detection
- Performance monitoring
- Feature adoption tracking
- UX issue identification

---

## 🔗 RELATED DOCUMENTATION

- Analytics Collector: `wapow-collector/main.py`
- Event Models: `wapow-collector/models.py`
- ClickHouse Schema: `wapow-app/migrations/001_events.sh`
- Frontend Analytics: `wapow-ui/src/lib/analytics.ts`
- Analytics Composable: `wapow-ui/src/composables/useAnalytics.ts`
