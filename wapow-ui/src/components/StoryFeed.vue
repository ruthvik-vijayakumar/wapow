<template>
  <div
    class="story-feed-container"
    @touchstart="handleTouchStart"
    @touchmove="handleTouchMove"
    @touchend="handleTouchEnd"
    @keydown="handleKeyDown"
    tabindex="0"
  >
    <!-- Stories Container -->
    <div
      class="stories-container"
      :class="{ 'swiping': isSwiping }"
      :style="{ transform: `translateY(${(currentStoryIndex * -100) + swipeOffset}vh)` }"
    >
      <div
        v-for="(story, index) in stories"
        :key="story.id"
        class="story-wrapper"
      >
        <!-- Dynamic Story Renderer -->
        <StoryView
          v-if="story.mediaType === 'story' && story.content"
          :content="story.content"
          :category="story.content.originalArticle.taxonomy?.primary_section?.name"
          :story-index="index"
          :total-stories="stories.length"
          :is-saved="savedArticleIds.has(getStoryArticleId(story))"
          @back="handleStoryBack"
          @follow="handleFollow"
          @next-story="nextStory"
          @prev-story="prevStory"
          @comments="toggleComments(story)"
          @save="handleSaveArticle"
        />
        <VerticalVideoView
          v-else-if="story.mediaType === 'video' && story.video"
          :video="convertVideoToVerticalVideoFormat(story.video)"
          :category="story.category"
          :story-index="index"
          :total-stories="stories.length"
          :is-saved="savedArticleIds.has(getStoryArticleId(story))"
          @back="handleStoryBack"
          @follow="handleFollow"
          @next-story="nextStory"
          @prev-story="prevStory"
          @comments="toggleComments(story)"
          @save="handleSaveArticle"
        />
        <PodcastView
          v-else-if="story.mediaType === 'podcast' && story.podcast"
          :podcast="story.podcast"
          :category="story.category"
          :story-index="index"
          :total-stories="stories.length"
          :is-saved="savedArticleIds.has(getStoryArticleId(story))"
          @back="handleStoryBack"
          @follow="handleFollow"
          @next-story="nextStory"
          @prev-story="prevStory"
          @comments="toggleComments(story)"
          @save="handleSaveArticle"
        />
        <div
          v-else-if="story.mediaType === 'game' && story.content?.type === 'game'"
          class="game-wrapper"
        >
          <Game
            :story-index="index"
            :total-stories="stories.length"
            @back="handleStoryBack"
            @next-story="nextStory"
            @prev-story="prevStory"
          />
        </div>
      </div>
    </div>

    <!-- Comments Bottom Sheet -->
    <div
      v-if="showComments"
      class="comments-overlay"
      @click="closeComments"
    >
      <div
        class="comments-sheet"
        @click.stop
        @touchstart.stop
        @touchmove.stop
        @touchend.stop
      >
        <div class="comments-header">
          <h3 class="comments-title">Discuss</h3>
          <button @click="closeComments" class="close-button">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Tabs -->
        <div class="tabs-container">
          <button
            @click="switchTab('comments')"
            class="tab-button"
            :class="{ 'active': activeTab === 'comments' }"
          >
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
            </svg>
            <span class="tab-text">Comments</span>
          </button>
          <button
            @click="switchTab('chatbot')"
            class="tab-button"
            :class="{ 'active': activeTab === 'chatbot' }"
          >
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            <span class="tab-text">AI Assistant</span>
          </button>
        </div>

        <!-- Comments Tab -->
        <div v-if="activeTab === 'comments'" class="comments-list" @touchstart.stop @touchmove.stop @touchend.stop>
          <!-- Loading state -->
          <div v-if="commentsLoading" class="comments-loading">
            <span>Loading comments...</span>
          </div>
          <!-- Empty state -->
          <div v-else-if="comments.length === 0" class="comments-empty">
            <span>No comments yet. Be the first to discuss!</span>
          </div>
          <div
            v-for="comment in comments"
            :key="comment._id"
            class="comment-item"
          >
            <div class="comment-content">
              <div class="comment-header">
                <div class="comment-author">
                  {{ comment.user_name }}
                </div>
                <div class="comment-time">{{ formatTime(comment.created_at) }}</div>
              </div>
              <div class="comment-text">{{ comment.text }}</div>
              <div class="comment-actions">
                <div class="vote-buttons">
                  <button
                    @click="voteComment(comment._id, 'up')"
                    class="vote-button upvote"
                    :class="{ 'voted': comment.user_vote === 'up' }"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
                    </svg>
                    <span>{{ comment.upvotes }}</span>
                  </button>
                  <button
                    @click="voteComment(comment._id, 'down')"
                    class="vote-button downvote"
                    :class="{ 'voted': comment.user_vote === 'down' }"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                    <span>{{ comment.downvotes }}</span>
                  </button>
                </div>
                <button class="comment-reply" @click="startReply(comment._id, comment.user_name)">Reply</button>
              </div>

              <!-- Replies -->
              <div v-if="comment.replies && comment.replies.length > 0" class="replies-container">
                <div
                  v-for="reply in comment.replies"
                  :key="reply._id"
                  class="reply-item"
                >
                  <div class="reply-content">
                    <div class="reply-header">
                      <div class="reply-author">
                        {{ reply.user_name }}
                      </div>
                      <div class="reply-time">{{ formatTime(reply.created_at) }}</div>
                    </div>
                    <div class="reply-text">{{ reply.text }}</div>
                    <div class="reply-actions">
                      <div class="vote-buttons">
                        <button
                          @click="voteComment(reply._id, 'up')"
                          class="vote-button upvote"
                          :class="{ 'voted': reply.user_vote === 'up' }"
                        >
                          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
                          </svg>
                          <span>{{ reply.upvotes }}</span>
                        </button>
                        <button
                          @click="voteComment(reply._id, 'down')"
                          class="vote-button downvote"
                          :class="{ 'voted': reply.user_vote === 'down' }"
                        >
                          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                          </svg>
                          <span>{{ reply.downvotes }}</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Chatbot Tab -->
        <div v-if="activeTab === 'chatbot'" class="chatbot-list" @touchstart.stop @touchmove.stop @touchend.stop>
          <div
            v-for="message in chatbotMessages"
            :key="message.id"
            class="chatbot-message"
            :class="{ 'user-message': message.type === 'user', 'bot-message': message.type === 'bot' }"
          >
            <div class="message-content">
              <div class="message-text">{{ message.text }}</div>
              <div class="message-time">{{ message.time }}</div>
            </div>
          </div>
        </div>

        <!-- Input Section -->
        <div class="input-section">
          <!-- Comments Input -->
          <div v-if="activeTab === 'comments'" class="comment-input">
            <div v-if="replyingTo" class="reply-indicator">
              <span>Replying to {{ replyingToName }}</span>
              <button @click="cancelReply" class="cancel-reply">&times;</button>
            </div>
            <div class="comment-input-row">
              <input
                ref="commentInputRef"
                type="text"
                :placeholder="replyingTo ? 'Write a reply...' : 'Add a comment...'"
                class="comment-field"
                v-model="newComment"
                @keyup.enter="addComment"
              />
              <button @click="addComment" class="send-button" :disabled="!newComment.trim()">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Chatbot Input -->
          <div v-if="activeTab === 'chatbot'" class="chatbot-input">
            <input
              type="text"
              placeholder="Ask me anything..."
              class="chatbot-field"
              v-model="chatbotMessage"
              @keyup.enter="sendChatbotMessage"
            />
            <button @click="sendChatbotMessage" class="send-button">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import StoryView from './StoryView.vue'
import { apiFetch } from '@/lib/api'
import VerticalVideoView from './VerticalVideoView.vue'
import PodcastView from './PodcastView.vue'
import Game from '@/views/wordle/Game.vue'
import { useContentStore } from '@/stores/videos'
import { useAuthStore } from '@/stores/auth'
import { useAnalytics } from '@/composables/useAnalytics'
import type { Video, StoryContent, Article } from '@/stores/videos'

// Add a watcher to debug store changes
const contentStore = useContentStore()
const authStore = useAuthStore()
const { trackView, trackSave, trackNavigate, startDwell, stopDwell } = useAnalytics()
watch(() => contentStore.videos, (newVideos) => {
  console.log('Videos changed in store:', newVideos.length)
}, { immediate: true })


interface Story {
  id: string
  mediaType: 'story' | 'video' | 'podcast' | 'game'
  video?: Video
  podcast?: StoryContent
  content?: StoryContent | Video | any
  category: string
}

interface Props {
  initialArticle: Article
  articles: Article[]
  category: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  back: []
  follow: [authorId: string]
}>()

const currentStoryIndex = ref(0)
const swipeOffset = ref(0)

// Saved articles - persisted via API when logged in, local-only otherwise
const savedArticleIds = ref<Set<string>>(new Set())

const getStoryArticleId = (story: Story): string => {
  if (story.mediaType === 'story' && story.content) {
    return String(story.content?.originalArticle?._id ?? story.content?._id ?? story.id)
  }
  if (story.mediaType === 'video' && story.video) {
    return String(story.video.content_id ?? story.id)
  }
  if (story.mediaType === 'podcast' && story.podcast) {
    return String(story.podcast.id ?? story.id)
  }
  return story.id
}

const fetchSavedArticleIds = async () => {
  try {
    const res = await apiFetch('/api/saved-articles/ids')
    if (res.ok) {
      const json = await res.json()
      savedArticleIds.value = new Set(json.ids ?? [])
    }
  } catch {
    // Auth not configured or not logged in - use local state
  }
}

const handleSaveArticle = (payload: { id: string; collection?: string; saved: boolean }) => {
  const { id, saved } = payload
  const set = new Set(savedArticleIds.value)
  if (saved) {
    set.add(id)
  } else {
    set.delete(id)
  }
  savedArticleIds.value = set

  // Analytics: track save/unsave
  const story = currentStory.value
  const type = story?.mediaType === 'story' ? 'article' : (story?.mediaType || '')
  trackSave(id, saved, type, story?.category || '')
}

onMounted(() => {
  fetchSavedArticleIds()
})

// Comments functionality
const showComments = ref(false)
const newComment = ref('')
const activeTab = ref('comments') // 'comments' or 'chatbot'
const chatbotMessage = ref('')
const currentArticleContent = ref<any>(null)
const currentArticleId = ref<string | null>(null)
const commentsLoading = ref(false)
const replyingTo = ref<string | null>(null)
const replyingToName = ref('')
const commentInputRef = ref<HTMLInputElement | null>(null)
const chatbotMessages = ref([
  {
    id: 1,
    type: 'bot',
    text: 'Hi! I\'m your AI assistant. How can I help you with this content?',
    time: 'Just now'
  }
])

// Comments data (fetched from API)
const comments = ref<any[]>([])




// Touch/swipe handling
const touchStart = ref({ x: 0, y: 0 })
const touchEnd = ref({ x: 0, y: 0 })
const isSwiping = ref(false)

// Generate stories from initial article, related articles, and videos
const stories = computed((): Story[] => {
  const baseStories: Story[] = []

  // Always add the initial article/video/podcast as the first story
  if (props.initialArticle && (props.initialArticle as any)._videoRef) {
    // Initial item is a video passed from saved content
    const videoData = (props.initialArticle as any)._videoRef
    console.log('Adding initial item as VIDEO story:', videoData.tracking?.page_title || videoData.title)
    baseStories.push({
      id: `video-${props.initialArticle._id}`,
      mediaType: 'video',
      video: videoData,
      category: props.category
    })
  } else if (props.initialArticle && (props.initialArticle as any)._podcastRef) {
    // Initial item is a podcast passed from saved content
    const podcastData = (props.initialArticle as any)._podcastRef
    console.log('Adding initial item as PODCAST story:', podcastData.title)
    baseStories.push({
      id: `podcast-${props.initialArticle._id}`,
      mediaType: 'podcast',
      podcast: podcastData,
      category: props.category
    })
  } else if (props.initialArticle && props.initialArticle.headlines?.basic) {
    // console.log('Adding initial article as story:', props.initialArticle.headlines.basic)
    baseStories.push({
      id: `story-${props.initialArticle._id}`,
      mediaType: 'story',
      content: convertArticleToStoryContent(props.initialArticle),
      category: props.category
    })
  } else {
    console.error('Initial article is invalid:', props.initialArticle)
  }

  // Add related articles as additional stories
  if (props.articles && props.articles.length > 0) {
    console.log('Adding related articles as stories, count:', props.articles.length)
    props.articles.forEach((article, index) => {
      if (article && article.headlines?.basic && article._id !== props.initialArticle?._id) {
        console.log('Adding article:', article.headlines.basic)
        baseStories.push({
          id: `story-related-${article._id}`,
          mediaType: 'story',
          content: convertArticleToStoryContent(article),
          category: getCategoryFromArticle(article)
        })
      } else if (article && (article as any).type === 'game') {
        console.log('Adding game to StoryFeed:', (article as any).title || 'Wordle', 'ID:', article._id)
        baseStories.push({
          id: `game-${article._id}`,
          mediaType: 'game',
          content: article,
          category: 'Games'
        })
      } else {
        console.error('Invalid related article:', article)
      }
    })
  } else {
    console.log('No related articles provided')
  }

  // Create a healthy mix of articles and videos for up to 20 scrolls
  const targetStories = 20
  const currentStories = baseStories.length

  // Debug: Check if store is still loading
  console.log('Store loading state:', contentStore.isLoading)

  console.log('ContentStore state:', {
    articlesCount: contentStore.articles.length,
    videosCount: contentStore.videos.length,
    podcastClipsCount: contentStore.podcastClips.length
  })

  // Debug: Check if videos are actually in the store
  if (contentStore.videos.length > 0) {
    console.log('First video in store:', contentStore.videos[0])
  } else {
    console.log('No videos in store!')
  }

  if (currentStories < targetStories) {
    console.log(`Adding mixed content to reach ${targetStories} stories (currently have ${currentStories})`)

    // Get all available articles, videos, and podcast clips
    const allArticles = contentStore.articles.filter(article =>
      article && article.headlines?.basic &&
      !baseStories.some(story => story.id === `story-${article._id}`)
    )

    const allVideos = contentStore.videos.filter(video =>
      video && video.content_id &&
      !baseStories.some(story => story.id === `video-${video.content_id}`)
    )

    const allPodcastClips = contentStore.podcastClips.filter(podcast =>
      podcast && podcast.id &&
      !baseStories.some(story => story.id === `podcast-${podcast.id}`)
    )

    console.log(`Available articles: ${allArticles.length}, Available videos: ${allVideos.length}, Available podcast clips: ${allPodcastClips.length}`)
    if (allVideos.length > 0) {
      console.log('Sample video:', allVideos[0])
    }
    if (allPodcastClips.length > 0) {
      console.log('Sample podcast clip:', allPodcastClips[0])
    }

    // Shuffle arrays for randomization
    const shuffledArticles = [...allArticles].sort(() => Math.random() - 0.5)
    const shuffledVideos = [...allVideos].sort(() => Math.random() - 0.5)
    const shuffledPodcastClips = [...allPodcastClips].sort(() => Math.random() - 0.5)

    // Create a pattern: article, video, podcast, article, video, podcast, etc.
    let articleIndex = 0
    let videoIndex = 0
    let podcastIndex = 0

    for (let i = currentStories; i < targetStories; i++) {
      const cycle = i % 3 // 0 = article, 1 = video, 2 = podcast
      const shouldAddVideo = cycle === 1 && videoIndex < shuffledVideos.length
      const shouldAddPodcast = cycle === 2 && podcastIndex < shuffledPodcastClips.length
      const shouldAddArticle = (cycle === 0 || (cycle === 1 && videoIndex >= shuffledVideos.length) || (cycle === 2 && podcastIndex >= shuffledPodcastClips.length)) && articleIndex < shuffledArticles.length

      if (shouldAddVideo) {
        const video = shuffledVideos[videoIndex]
        console.log(`Adding video ${videoIndex + 1}:`, video.tracking?.page_title || video.content_id)
        const videoStory = {
          id: `video-${video.content_id}`,
          mediaType: 'video' as const,
          video: video,
          category: getCategoryFromVideo(video)
        }
        baseStories.push(videoStory)
        console.log('Added video story:', videoStory)
        videoIndex++
      } else if (shouldAddPodcast) {
        const podcast = shuffledPodcastClips[podcastIndex]
        console.log(`Adding podcast clip ${podcastIndex + 1}:`, podcast.title)
        const podcastStory = {
          id: `podcast-${podcast.id}`,
          mediaType: 'podcast' as const,
          podcast: podcast,
          category: getCategoryFromPodcast(podcast)
        }
        baseStories.push(podcastStory)
        console.log('Added podcast story:', podcastStory)
        podcastIndex++
      } else if (shouldAddArticle) {
        const article = shuffledArticles[articleIndex]
        console.log(`Adding article ${articleIndex + 1}:`, article.headlines?.basic)
        baseStories.push({
          id: `story-mixed-${article._id}`,
          mediaType: 'story',
          content: convertArticleToStoryContent(article),
          category: getCategoryFromArticle(article)
        })
        articleIndex++
      } else {
        // If we run out of content, break
        console.log('No more content available')
        break
      }
    }

    console.log(`Final story count: ${baseStories.length}`)

    // Debug: Force add a video if we have videos but none were added
    if (contentStore.videos.length > 0 && !baseStories.some(story => story.mediaType === 'video')) {
      console.log('Forcing addition of a video story')
      const firstVideo = contentStore.videos[0]
      baseStories.push({
        id: `forced-video-${firstVideo.content_id}`,
        mediaType: 'video' as const,
        video: firstVideo,
        category: getCategoryFromVideo(firstVideo)
      })
      console.log('Added forced video story')
    }
  }

  console.log('Final stories array:', baseStories.length, baseStories.map(s => ({
    id: s.id,
    mediaType: s.mediaType,
    title: s.video?.tracking?.page_title || s.podcast?.title || s.content?.title
  })))

  // Randomize the stories array (except the first story which is the initial article)
  if (baseStories.length > 2) {
    const initialStory = baseStories[0]
    const remainingStories = baseStories.slice(1)

    // Shuffle the remaining stories
    for (let i = remainingStories.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[remainingStories[i], remainingStories[j]] = [remainingStories[j], remainingStories[i]]
    }

    // Reconstruct the array with initial story first, then shuffled remaining stories
    const shuffledStories = [initialStory, ...remainingStories]
    console.log('Stories after randomization:', shuffledStories.map(s => ({
      id: s.id,
      mediaType: s.mediaType,
      title: s.video?.tracking?.page_title || s.podcast?.title || s.content?.title
    })))

    return shuffledStories
  }

  return baseStories
})

const currentStory = computed(() => {
  const story = stories.value[currentStoryIndex.value]
  console.log('Current story:', currentStoryIndex.value, story?.mediaType, story?.video?.tracking?.page_title || story?.podcast?.title)
  return story
})

// ── Analytics: track view + dwell on story change ──────────────────────────
watch(currentStory, (newStory, oldStory) => {
  // Stop dwell for the previous story
  if (oldStory) {
    stopDwell(getStoryArticleId(oldStory))
  }
  // Start dwell + fire view for the new story
  if (newStory) {
    const id = getStoryArticleId(newStory)
    const type = newStory.mediaType === 'story' ? 'article' : newStory.mediaType
    const cat = newStory.category || ''
    trackView(id, type, cat)
    startDwell(id, type, cat)
  }
}, { immediate: true })

const handleTouchStart = (event: TouchEvent) => {
  console.log('Touch start detected')
  touchStart.value = {
    x: event.touches[0].clientX,
    y: event.touches[0].clientY
  }
  isSwiping.value = false
  swipeOffset.value = 0
}

const handleTouchMove = (event: TouchEvent) => {
  const currentY = event.touches[0].clientY
  const currentX = event.touches[0].clientX
  const deltaY = currentY - touchStart.value.y
  const deltaX = currentX - touchStart.value.x

  // Only start swiping if we've moved enough vertically and not horizontally
  if (Math.abs(deltaY) > 10 && Math.abs(deltaY) > Math.abs(deltaX)) {
    isSwiping.value = true
    console.log('Swiping detected, deltaY:', deltaY)

    // Calculate swipe offset as percentage of screen height
    const screenHeight = window.innerHeight
    const swipePercentage = deltaY / screenHeight
    swipeOffset.value = swipePercentage * 100 // Convert to percentage

    console.log('Swipe offset:', swipeOffset.value)
  }

  touchEnd.value = {
    x: event.touches[0].clientX,
    y: currentY
  }
}

const handleTouchEnd = () => {
  console.log('Touch end detected, isSwiping:', isSwiping.value)

  if (!isSwiping.value) return

  const deltaX = touchEnd.value.x - touchStart.value.x
  const deltaY = touchEnd.value.y - touchStart.value.y
  const minSwipeDistance = 80 // Increased threshold for better detection

  console.log('Swipe analysis - deltaX:', deltaX, 'deltaY:', deltaY, 'minDistance:', minSwipeDistance)

  // Only handle vertical swipes (vertical movement must be greater than horizontal)
  if (Math.abs(deltaY) > Math.abs(deltaX) && Math.abs(deltaY) > minSwipeDistance) {
    if (deltaY > 0) {
      // Swipe down - previous story
      console.log('Swipe down detected - going to previous story')
      prevStory()
    } else {
      // Swipe up - next story
      console.log('Swipe up detected - going to next story')
      nextStory()
    }
  } else {
    console.log('Swipe not significant enough or not vertical')
  }

  // Reset swipe state
  isSwiping.value = false
  swipeOffset.value = 0
}

const handleKeyDown = (event: KeyboardEvent) => {
  switch (event.key) {
    case 'ArrowUp':
      event.preventDefault()
      prevStory()
      break
    case 'ArrowDown':
      event.preventDefault()
      nextStory()
      break
    case 'Escape':
      event.preventDefault()
      handleStoryBack()
      break
  }
}

const nextStory = () => {
  console.log('Attempting next story. Current:', currentStoryIndex.value, 'Total:', stories.value.length)

  if (currentStoryIndex.value < stories.value.length - 1) {
    const fromId = getStoryArticleId(stories.value[currentStoryIndex.value])
    currentStoryIndex.value++
    const toId = getStoryArticleId(stories.value[currentStoryIndex.value])
    trackNavigate(fromId, toId, 'next')
    const nextStory = stories.value[currentStoryIndex.value]
    console.log('Next story:', currentStoryIndex.value, nextStory?.mediaType, nextStory?.video?.tracking?.page_title || nextStory?.podcast?.title)

    // Validate the next story has content
    if (!nextStory || (!nextStory.video && !nextStory.podcast && !nextStory.content)) {
      console.error('Invalid story at index:', currentStoryIndex.value)
      // Try to find a valid story
      const validIndex = stories.value.findIndex(s => s.video || s.podcast || s.content)
      if (validIndex !== -1) {
        currentStoryIndex.value = validIndex
      }
    }
  } else {
    console.log('No more stories, going back')
    handleStoryBack()
  }
}

const prevStory = () => {
  console.log('Attempting prev story. Current:', currentStoryIndex.value)

  if (currentStoryIndex.value > 0) {
    const fromId = getStoryArticleId(stories.value[currentStoryIndex.value])
    currentStoryIndex.value--
    const toId = getStoryArticleId(stories.value[currentStoryIndex.value])
    trackNavigate(fromId, toId, 'prev')
    const prevStory = stories.value[currentStoryIndex.value]
    console.log('Previous story:', currentStoryIndex.value, prevStory?.mediaType, prevStory?.video?.tracking?.page_title || prevStory?.podcast?.title)

    // Validate the previous story has content
    if (!prevStory || (!prevStory.video && !prevStory.podcast && !prevStory.content)) {
      console.error('Invalid story at index:', currentStoryIndex.value)
      // Try to find a valid story
      const validIndex = stories.value.findIndex(s => s.video || s.podcast || s.content)
      if (validIndex !== -1) {
        currentStoryIndex.value = validIndex
      }
    }
  }
}

const goToStory = (index: number) => {
  currentStoryIndex.value = index
}

const handleStoryBack = () => {
  emit('back')
}

const handleFollow = (authorId: string) => {
  emit('follow', authorId)
}

// --- Comments: API-backed handlers ---

const fetchComments = async (articleId: string) => {
  commentsLoading.value = true
  comments.value = []
  try {
    const res = await apiFetch(`/api/comments?article_id=${encodeURIComponent(articleId)}`)
    if (res.ok) {
      const json = await res.json()
      comments.value = json.data ?? []
    }
  } catch (e) {
    console.error('Failed to fetch comments:', e)
  } finally {
    commentsLoading.value = false
  }
}

const toggleComments = (storyOrContent?: any) => {
  if (showComments.value) {
    showComments.value = false
    return
  }

  // Resolve the article ID from whatever was passed
  let articleId: string | null = null
  let textContent = ''

  if (storyOrContent) {
    // Called from StoryView: storyOrContent is the Story object
    const story = storyOrContent as any
    if (story.content?.originalArticle?._id) {
      articleId = story.content.originalArticle._id
    } else if (story.content?._id) {
      articleId = story.content._id
    } else if (story.video?.content_id || story.video?.id) {
      articleId = story.video?.content_id ?? story.video?.id
    } else if (story.podcast?.id) {
      articleId = story.podcast.id
    } else if (story.id) {
      articleId = story.id
    }

    // Extract text content for AI chat
    try {
      textContent = story.content?.originalArticle?.content_elements
        ?.filter((el: any) => el.type === 'text')
        .map((el: any) => el.content)
        .join(' ')
        .replace(/https?:\/\/[^\s]+/g, '')
        .replace(/\s+/g, ' ')
        .trim() ?? ''
    } catch {
      // Not all content types have content_elements
    }
  }

  currentArticleId.value = articleId
  currentArticleContent.value = textContent
  showComments.value = true
  replyingTo.value = null
  replyingToName.value = ''

  if (articleId) {
    fetchComments(articleId)
  }
}

const closeComments = () => {
  showComments.value = false
  replyingTo.value = null
  replyingToName.value = ''
}

const addComment = async () => {
  const text = newComment.value.trim()
  if (!text || !currentArticleId.value) return

  const userName = authStore.user?.name || authStore.user?.email?.split('@')[0] || 'Anonymous'
  const userPicture = authStore.user?.picture || null

  try {
    const res = await apiFetch('/api/comments', {
      method: 'POST',
      body: JSON.stringify({
        article_id: currentArticleId.value,
        text,
        parent_id: replyingTo.value,
        user_name: userName,
        user_picture: userPicture,
      }),
    })
    if (res.ok) {
      const json = await res.json()
      const newDoc = json.data
      if (replyingTo.value) {
        // Add the reply to its parent comment
        const parent = comments.value.find((c: any) => c._id === replyingTo.value)
        if (parent) {
          if (!parent.replies) parent.replies = []
          parent.replies.push(newDoc)
        }
      } else {
        // Prepend top-level comment
        comments.value.unshift({ ...newDoc, replies: [] })
      }
      newComment.value = ''
      replyingTo.value = null
      replyingToName.value = ''
    }
  } catch (e) {
    console.error('Failed to add comment:', e)
  }
}

const voteComment = async (commentId: string, vote: 'up' | 'down') => {
  try {
    const res = await apiFetch(`/api/comments/${commentId}/vote`, {
      method: 'POST',
      body: JSON.stringify({ vote }),
    })
    if (res.ok) {
      const json = await res.json()
      const updated = json.data
      // Update the comment in-place (top-level or reply)
      for (const comment of comments.value) {
        if (comment._id === commentId) {
          comment.upvotes = updated.upvotes
          comment.downvotes = updated.downvotes
          comment.user_vote = updated.user_vote
          return
        }
        if (comment.replies) {
          for (const reply of comment.replies) {
            if (reply._id === commentId) {
              reply.upvotes = updated.upvotes
              reply.downvotes = updated.downvotes
              reply.user_vote = updated.user_vote
              return
            }
          }
        }
      }
    }
  } catch (e) {
    console.error('Failed to vote:', e)
  }
}

const startReply = (parentId: string, authorName: string) => {
  replyingTo.value = parentId
  replyingToName.value = authorName
  nextTick(() => {
    commentInputRef.value?.focus()
  })
}

const cancelReply = () => {
  replyingTo.value = null
  replyingToName.value = ''
}

const formatTime = (isoString: string): string => {
  if (!isoString) return ''
  const date = new Date(isoString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return 'Just now'
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24) return `${diffHr}h ago`
  const diffDay = Math.floor(diffHr / 24)
  return `${diffDay}d ago`
}

const switchTab = (tab: string) => {
  activeTab.value = tab
}

const sendChatbotMessage = async () => {
  if (chatbotMessage.value.trim()) {
    const userMessageId = Math.max(...chatbotMessages.value.map(m => m.id)) + 1
    const botMessageId = userMessageId + 1

    // Get article content for context
    const articleContent = currentArticleContent.value
    console.log('Article content:', articleContent)

    let responseMessage = "I'm sorry, I'm having trouble connecting to the AI service right now. Please try again later.";

    try {
      // You need to replace 'YOUR_GEMINI_API_KEY' with your actual API key
      const API_KEY = 'AIzaSyB-AsIIwQnGGC_y3MY9OpupF9yPsK1CSGk'; // Replace with your actual API key

      const response = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${API_KEY}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            contents: [
              {
                parts: [
                  {
                    text: `User question: ${chatbotMessage.value.trim()}\n\nArticle Content:\n${articleContent}`
                  }
                ]
              }
            ],
            generationConfig: {
              temperature: 0.2,
              topK: 40,
              topP: 0.95,
              maxOutputTokens: 1024,
            },
          }),
        },
      );

      if (!response.ok) {
        console.error('Gemini API Error:', response.status, response.statusText);
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const responseData = await response.json();
      responseMessage = responseData.candidates[0].content.parts[0].text;
    } catch (error) {
      console.error('Error calling Gemini API:', error);
    }
    // Create enhanced user message with article title
    const enhancedMessage = `${chatbotMessage.value.trim()}`

    // Add user message
    chatbotMessages.value.push({
      id: userMessageId,
      type: 'user',
      text: enhancedMessage,
      time: 'Just now'
    })

    // Simulate bot response
    setTimeout(() => {
      chatbotMessages.value.push({
        id: botMessageId,
        type: 'bot',
        text: responseMessage,
        time: 'Just now'
      })
    }, 1000)

    chatbotMessage.value = ''
  }
}

const generateBotResponse = (userMessage: string): string => {
  const message = userMessage.toLowerCase()

  // Get article content for context
  const articleContent = currentArticleContent.value

  if (message.includes('help') || message.includes('what')) {
    if (articleContent) {
      return `I can help you understand this content about "${articleContent.title || 'this article'}", answer questions, or provide additional context. What would you like to know?`
    }
    return 'I can help you understand this content, answer questions, or provide additional context. What would you like to know?'
  } else if (message.includes('explain') || message.includes('tell me')) {
    if (articleContent) {
      return `This content is about ${articleContent.title || 'current events'}. ${articleContent.description || 'I can provide more details or answer specific questions you have about it.'}`
    }
    return 'I can explain this content in detail. What specific aspect would you like me to focus on?'
  } else if (message.includes('summary') || message.includes('summarize')) {
    if (articleContent) {
      return `Here's a quick summary: ${articleContent.description || 'This content covers important information that you might find interesting.'}`
    }
    return 'I can provide a summary of this content. What would you like me to highlight?'
  } else {
    return 'I understand your question. Let me help you with that. Could you be more specific about what you\'d like to know?'
  }
}



// Function to get recommendations for a specific category
const getCategoryRecommendations = async (category: string) => {
  const userId = 'user_001' // You can make this dynamic based on user session

  try {
    const RECOMMENDATIONS_API = import.meta.env.VITE_RECOMMENDATIONS_API || 'http://localhost:5000'
    const response = await fetch(`${RECOMMENDATIONS_API}/recommendations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        category: category
      })
    })

    if (!response.ok) {
      console.error('Recommendations API Error:', response.status, response.statusText)
      return []
    }

    const recommendations = await response.json()
    console.log(`Found ${recommendations.articles?.length || 0} recommendations for ${category}`)
    return recommendations.articles || []
  } catch (error) {
    console.error('Error fetching recommendations:', error)
    return []
  }
}

const convertArticleToVideo = (article: Article): Video => {
  return {
    aspect_ratio: 16/9,
    content_id: article._id,
    canonical_url: article.canonical_url,
    promo_image: {
      url: article.promo_items?.basic?.url || ''
    },
    streams: [],
    duration: 0,
    tracking: {
      page_name: '',
      video_category: 'vertical',
      video_section: article.taxonomy?.primary_section?.name || '',
      video_source: 'The Washington Post',
      page_title: article.headlines?.basic || '',
      av_name: '',
      av_arc_id: ''
    }
  }
}

function convertArticleToStoryContent(article: Article): any {
  return {
    title: article.headlines?.basic || 'Untitled Article',
    description: article.description?.basic || article.subheadlines?.basic || 'No description available',
    thumbnail: article.promo_items?.basic?.url || 'https://picsum.photos/400/600?random=article',
    author: {
      name: article.credits?.by?.[0]?.name || 'Unknown Author',
      username: `@${article.credits?.by?.[0]?.name?.toLowerCase().replace(/\s+/g, '') || 'unknown'}`,
      avatar: 'https://picsum.photos/50/50?random=author'
    },
    createdAt: article.publish_date || new Date().toISOString(),
    // Keep the original article data for reference
    originalArticle: article
  }
}

function convertVideoToVerticalVideoFormat(video: Video): any {
  // Get the best quality MP4 stream URL (skip HLS streams)
  const mp4Streams = video.streams?.filter(stream => stream.stream_type === 'mp4') || []
  const bestStream = mp4Streams.find(stream => stream.bitrate >= 1200) ||
                    mp4Streams.find(stream => stream.bitrate >= 600) ||
                    mp4Streams[0]

  console.log('Converting video:', video.content_id)
  console.log('Available streams:', video.streams?.length || 0)
  console.log('MP4 streams:', mp4Streams.length)
  console.log('Best stream:', bestStream)

  const convertedVideo = {
    id: video._id || video.id,
    _id: video._id || video.id,
    content_id: video.content_id,
    title: video.tracking?.page_title || 'Video',
    description: `Watch this video from ${video.tracking?.video_source || 'The Washington Post'}`,
    videoUrl: bestStream?.url || '',
    thumbnail: video.promo_image?.url || '',
    aspectRatio: video.aspect_ratio,
    duration: video.duration || 0,
    author: {
      name: 'The Washington Post',
      username: '@washingtonpost',
      avatar: 'https://picsum.photos/50/50?random=wapo'
    },
    likes: Math.floor(Math.random() * 1000),
    comments: Math.floor(Math.random() * 100),
    shares: Math.floor(Math.random() * 50),
    views: Math.floor(Math.random() * 10000),
    createdAt: new Date().toISOString(),
    mediaType: 'video'
  }

  console.log('Converted video URL:', convertedVideo.videoUrl)
  return convertedVideo
}

function getCategoryFromVideo(video: Video): string {
  const title = video.tracking?.page_title?.toLowerCase() || ''
  if (title.includes('tech') || title.includes('ai')) return 'Technology'
  if (title.includes('climate') || title.includes('energy')) return 'Environment'
  if (title.includes('space') || title.includes('mars')) return 'Science'
  if (title.includes('medical') || title.includes('health')) return 'Health'
  if (title.includes('economic') || title.includes('market')) return 'Business'
  return 'News'
}

function getCategoryFromArticle(article: Article): string {
  return article.taxonomy?.primary_section?.name ||
         article.taxonomy?.sections?.[0]?.name ||
         article.type ||
         'News'
}

function getCategoryFromPodcast(podcast: StoryContent): string {
  const title = podcast.title?.toLowerCase() || ''
  if (title.includes('tech') || title.includes('ai')) return 'Technology'
  if (title.includes('climate') || title.includes('energy')) return 'Environment'
  if (title.includes('space') || title.includes('mars')) return 'Science'
  if (title.includes('medical') || title.includes('health')) return 'Health'
  if (title.includes('economic') || title.includes('market')) return 'Business'
  return 'Podcasts'
}

const generateMixedMediaStories = (): Story[] => {
  // Import store to get media data
  const contentStore = useContentStore()

  const mixedStories: Story[] = []

  // Add articles as stories
  contentStore.articles.slice(0, 4).forEach((article: Article, index: number) => {
    mixedStories.push({
      id: `article-${index}`,
      mediaType: 'story',
      content: convertArticleToStoryContent(article),
      category: getCategoryFromArticle(article)
    })
  })

  // Add some videos from the store
  contentStore.videos.slice(0, 2).forEach((video: Video, index: number) => {
    mixedStories.push({
      id: `video-${index}`,
      mediaType: 'video',
      video: video,
      category: getCategoryFromVideo(video)
    })
  })

  // Add some sample podcast clips if available
  contentStore.podcastClips.slice(0, 2).forEach((podcast: StoryContent, index: number) => {
    mixedStories.push({
      id: `podcast-${index}`,
      mediaType: 'podcast',
      podcast: podcast,
      category: getCategoryFromPodcast(podcast)
    })
  })

  return mixedStories
}

</script>

<style scoped>
.story-feed-container {
  @apply fixed inset-0 bg-black z-50;
  @apply overflow-hidden;
  @apply outline-none;
  @apply touch-none; /* Prevent default touch behaviors */
}

.stories-container {
  @apply transition-transform duration-100 ease-out;
  @apply h-full w-full;
  @apply relative;
}

.stories-container.swiping {
  @apply transition-none;
}

.story-wrapper {
  @apply h-screen w-full;
  @apply bg-black;
  @apply flex-shrink-0;
  @apply min-h-screen;
  @apply flex;
}

.game-wrapper {
  @apply h-screen w-full;
  @apply bg-black;
  @apply flex-shrink-0;
  @apply min-h-screen;
  @apply block;
}

.story-indicators {
  @apply absolute top-4 right-4 z-20;
  @apply flex flex-col space-y-2;
}

.story-indicator {
  @apply w-2 h-2 rounded-full bg-white bg-opacity-30;
  @apply cursor-pointer transition-all duration-200;
  @apply hover:bg-opacity-50;
}

.story-indicator.active {
  @apply bg-opacity-100;
}

/* Comments Bottom Sheet */
.comments-overlay {
  @apply fixed inset-0 bg-black bg-opacity-50;
  @apply flex items-end justify-center;
  @apply z-50;
}

.comments-sheet {
  @apply bg-black rounded-t-3xl;
  @apply w-full max-w-md;
  @apply max-h-[80vh] flex flex-col;
  @apply transform transition-transform duration-300 ease-out;
}

.comments-header {
  @apply flex items-center justify-between px-4 py-4;
}

.comments-title {
  @apply text-white text-lg font-semibold;
}

.close-button {
  @apply text-gray-400 hover:text-white;
  @apply transition-colors duration-200;
}

.tabs-container {
  @apply flex items-center justify-start px-4 border-b border-gray-900;
  @apply space-x-6;
}

.tab-button {
  @apply flex items-center text-gray-400 text-base font-medium transition-colors duration-200;
  @apply relative pb-3 px-2;
}

.tab-button.active {
  @apply text-white font-bold;
}

.tab-button.active::after {
  content: '';
  @apply absolute bottom-0 left-0 right-0 h-0.5 bg-white;
}

.comments-list {
  @apply flex-1 overflow-y-auto p-4;
  @apply space-y-4;
  @apply min-h-0; /* Allow flex item to shrink */
  @apply max-h-full; /* Ensure it doesn't exceed container */
}

.comment-item {
  @apply flex space-x-3 mb-6;
}

.comment-content {
  @apply flex-1;
}

.comment-header {
  @apply flex items-center justify-between mb-1;
}

.comment-author {
  @apply text-white font-medium text-sm;
  @apply flex items-center;
}

.verified-badge {
  @apply text-white bg-blue-500 text-xs font-medium ml-1 rounded-full px-2 py-0.5;
}

.flair-badge {
  @apply text-white bg-green-800 bg-opacity-30 text-xs font-medium ml-1 mb-0 rounded-full px-2 py-0.5;
}

.comment-time {
  @apply text-gray-500 text-xs;
}

.comment-text {
  @apply text-gray-300 text-sm mb-2;
}

.comment-actions {
  @apply flex items-center space-x-4;
}

.comment-like {
  @apply flex items-center space-x-1 text-gray-400 text-xs;
  @apply hover:text-white transition-colors duration-200;
}

.comment-reply {
  @apply text-blue-500 text-xs font-medium;
  @apply hover:underline cursor-pointer;
}

/* Vote Buttons */
.vote-buttons {
  @apply flex items-center space-x-2;
}

.vote-button {
  @apply flex items-center space-x-1 text-gray-400 text-xs;
  @apply hover:text-white transition-colors duration-200;
  @apply cursor-pointer;
}

.vote-button.upvote {
  @apply hover:text-green-500;
}

.vote-button.downvote {
  @apply hover:text-red-500;
}

.vote-button.voted {
  @apply font-medium;
}

.vote-button.upvote.voted {
  @apply text-green-500;
}

.vote-button.downvote.voted {
  @apply text-red-500;
}

.replies-container {
  @apply ml-6 mt-3 space-y-3;
  @apply border-l border-gray-700 pl-4;
}

.reply-item {
  @apply flex space-x-3;
}

.reply-content {
  @apply flex-1;
}

.reply-header {
  @apply flex items-center justify-between mb-1;
}

.reply-author {
  @apply text-white font-medium text-sm;
  @apply flex items-center;
}

.reply-time {
  @apply text-gray-500 text-xs;
}

.reply-text {
  @apply text-gray-400 text-sm mb-2;
}

.reply-actions {
  @apply flex items-center space-x-2;
}

.reply-like {
  @apply flex items-center space-x-1 text-gray-400 text-xs;
  @apply hover:text-white transition-colors duration-200;
}

.comment-input {
  @apply flex flex-col p-4;
  @apply border-t border-gray-700;
}

.reply-indicator {
  @apply flex items-center justify-between text-xs text-blue-400 mb-2 px-1;
}

.cancel-reply {
  @apply text-gray-400 text-lg leading-none hover:text-white;
}

.comment-input-row {
  @apply flex items-center space-x-2;
}

.comment-field {
  @apply flex-1 bg-gray-800 text-white;
  @apply px-3 py-2 rounded-full;
  @apply border border-gray-600;
  @apply focus:outline-none focus:border-blue-500;
}

.send-button {
  @apply text-blue-500 hover:text-blue-400;
  @apply transition-colors duration-200;
}

.send-button:disabled {
  @apply opacity-40 cursor-not-allowed;
}

.comments-loading,
.comments-empty {
  @apply flex items-center justify-center py-12 text-gray-400 text-sm;
}

/* Chatbot Styles */
.chatbot-list {
  @apply flex-1 overflow-y-auto p-4;
  @apply space-y-4;
  @apply min-h-0; /* Allow flex item to shrink */
  @apply max-h-full; /* Ensure it doesn't exceed container */
}

.chatbot-message {
  @apply flex;
}

.chatbot-message.user-message {
  @apply justify-end;
}

.chatbot-message.bot-message {
  @apply justify-start;
}

.message-content {
  @apply max-w-xs px-4 py-2 rounded-lg;
}

.user-message .message-content {
  @apply bg-blue-600 text-white;
}

.bot-message .message-content {
  @apply bg-gray-700 text-white;
}

.message-text {
  @apply text-sm;
}

.message-time {
  @apply text-xs opacity-70 mt-1;
}

.chatbot-input {
  @apply flex items-center space-x-2 p-4;
  @apply border-t border-gray-700;
}

.chatbot-field {
  @apply flex-1 bg-gray-800 text-white;
  @apply px-3 py-2 rounded-full;
  @apply border border-gray-600;
  @apply focus:outline-none focus:border-blue-500;
}

.input-section {
  @apply border-t border-gray-700;
}
</style>
