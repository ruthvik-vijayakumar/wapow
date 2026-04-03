<template>
  <div
    class="story-feed-container"
    @touchstart="handleTouchStart"
    @touchmove="handleTouchMove"
    @touchend="handleTouchEnd"
    @keydown="handleKeyDown"
    tabindex="0"
  >
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

        <div v-if="activeTab === 'comments'" class="comments-list" @touchstart.stop @touchmove.stop @touchend.stop>
          <div v-if="commentsLoading" class="comments-skeleton">
            <div v-for="n in 4" :key="n" class="comment-skeleton-item">
              <div class="comment-skeleton-avatar skeleton-pulse-dark"></div>
              <div class="comment-skeleton-body">
                <div class="skeleton-line-dark skeleton-pulse-dark" style="width: 40%; height: 0.6875rem;"></div>
                <div class="skeleton-line-dark skeleton-pulse-dark" style="width: 90%; height: 0.625rem; margin-top: 0.5rem;"></div>
                <div class="skeleton-line-dark skeleton-pulse-dark" style="width: 65%; height: 0.625rem; margin-top: 0.375rem;"></div>
              </div>
            </div>
          </div>
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

        <div class="input-section">
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
import { useContentStore } from '@/stores/content'
import { useAuthStore } from '@/stores/auth'
import { useAnalytics } from '@/composables/useAnalytics'
import type { Video, StoryContent, Article } from '@/stores/content'

const contentStore = useContentStore()
const authStore = useAuthStore()
const { trackView, trackSave, trackNavigate, startDwell, stopDwell } = useAnalytics()


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
    // not logged in — use local state
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

  const story = currentStory.value
  const type = story?.mediaType === 'story' ? 'article' : (story?.mediaType || '')
  trackSave(id, saved, type, story?.category || '')
}

onMounted(() => {
  fetchSavedArticleIds()
})

const showComments = ref(false)
const newComment = ref('')
const activeTab = ref('comments')
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

const comments = ref<any[]>([])

const touchStart = ref({ x: 0, y: 0 })
const touchEnd = ref({ x: 0, y: 0 })
const isSwiping = ref(false)

const stories = computed((): Story[] => {
  const baseStories: Story[] = []

  if (props.initialArticle && (props.initialArticle as any)._videoRef) {
    const videoData = (props.initialArticle as any)._videoRef
    baseStories.push({
      id: `video-${props.initialArticle._id}`,
      mediaType: 'video',
      video: videoData,
      category: props.category
    })
  } else if (props.initialArticle && (props.initialArticle as any)._podcastRef) {
    const podcastData = (props.initialArticle as any)._podcastRef
    baseStories.push({
      id: `podcast-${props.initialArticle._id}`,
      mediaType: 'podcast',
      podcast: podcastData,
      category: props.category
    })
  } else if (props.initialArticle && props.initialArticle.headlines?.basic) {
    baseStories.push({
      id: `story-${props.initialArticle._id}`,
      mediaType: 'story',
      content: convertArticleToStoryContent(props.initialArticle),
      category: props.category
    })
  }

  if (props.articles && props.articles.length > 0) {
    props.articles.forEach((article) => {
      if (article && article.headlines?.basic && article._id !== props.initialArticle?._id) {
        baseStories.push({
          id: `story-related-${article._id}`,
          mediaType: 'story',
          content: convertArticleToStoryContent(article),
          category: getCategoryFromArticle(article)
        })
      } else if (article && (article as any).type === 'game') {
        baseStories.push({
          id: `game-${article._id}`,
          mediaType: 'game',
          content: article,
          category: 'Games'
        })
      }
    })
  }

  // Fill up to 20 stories with a rotating article → video → podcast pattern
  const targetStories = 20
  const currentStories = baseStories.length

  if (currentStories < targetStories) {
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

    const shuffledArticles = [...allArticles].sort(() => Math.random() - 0.5)
    const shuffledVideos = [...allVideos].sort(() => Math.random() - 0.5)
    const shuffledPodcastClips = [...allPodcastClips].sort(() => Math.random() - 0.5)

    let articleIndex = 0
    let videoIndex = 0
    let podcastIndex = 0

    for (let i = currentStories; i < targetStories; i++) {
      const cycle = i % 3
      const shouldAddVideo = cycle === 1 && videoIndex < shuffledVideos.length
      const shouldAddPodcast = cycle === 2 && podcastIndex < shuffledPodcastClips.length
      const shouldAddArticle = (cycle === 0 || (cycle === 1 && videoIndex >= shuffledVideos.length) || (cycle === 2 && podcastIndex >= shuffledPodcastClips.length)) && articleIndex < shuffledArticles.length

      if (shouldAddVideo) {
        const video = shuffledVideos[videoIndex]
        baseStories.push({
          id: `video-${video.content_id}`,
          mediaType: 'video' as const,
          video: video,
          category: getCategoryFromVideo(video)
        })
        videoIndex++
      } else if (shouldAddPodcast) {
        const podcast = shuffledPodcastClips[podcastIndex]
        baseStories.push({
          id: `podcast-${podcast.id}`,
          mediaType: 'podcast' as const,
          podcast: podcast,
          category: getCategoryFromPodcast(podcast)
        })
        podcastIndex++
      } else if (shouldAddArticle) {
        const article = shuffledArticles[articleIndex]
        baseStories.push({
          id: `story-mixed-${article._id}`,
          mediaType: 'story',
          content: convertArticleToStoryContent(article),
          category: getCategoryFromArticle(article)
        })
        articleIndex++
      } else {
        break
      }
    }

    // Ensure at least one video is present if the store has any
    if (contentStore.videos.length > 0 && !baseStories.some(story => story.mediaType === 'video')) {
      const firstVideo = contentStore.videos[0]
      baseStories.push({
        id: `forced-video-${firstVideo.content_id}`,
        mediaType: 'video' as const,
        video: firstVideo,
        category: getCategoryFromVideo(firstVideo)
      })
    }
  }

  // Shuffle everything except the first story (the initial article)
  if (baseStories.length > 2) {
    const [initial, ...rest] = baseStories
    for (let i = rest.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[rest[i], rest[j]] = [rest[j], rest[i]]
    }
    return [initial, ...rest]
  }

  return baseStories
})

const currentStory = computed(() => stories.value[currentStoryIndex.value])

watch(currentStory, (newStory, oldStory) => {
  if (oldStory) stopDwell(getStoryArticleId(oldStory))
  if (newStory) {
    const id = getStoryArticleId(newStory)
    const type = newStory.mediaType === 'story' ? 'article' : newStory.mediaType
    const cat = newStory.category || ''
    trackView(id, type, cat)
    startDwell(id, type, cat)
  }
}, { immediate: true })

const handleTouchStart = (event: TouchEvent) => {
  touchStart.value = { x: event.touches[0].clientX, y: event.touches[0].clientY }
  isSwiping.value = false
  swipeOffset.value = 0
}

const handleTouchMove = (event: TouchEvent) => {
  const currentY = event.touches[0].clientY
  const currentX = event.touches[0].clientX
  const deltaY = currentY - touchStart.value.y
  const deltaX = currentX - touchStart.value.x

  if (Math.abs(deltaY) > 10 && Math.abs(deltaY) > Math.abs(deltaX)) {
    isSwiping.value = true
    swipeOffset.value = (deltaY / window.innerHeight) * 100
  }

  touchEnd.value = { x: currentX, y: currentY }
}

const handleTouchEnd = () => {
  if (!isSwiping.value) return

  const deltaX = touchEnd.value.x - touchStart.value.x
  const deltaY = touchEnd.value.y - touchStart.value.y
  const minSwipeDistance = 80

  if (Math.abs(deltaY) > Math.abs(deltaX) && Math.abs(deltaY) > minSwipeDistance) {
    if (deltaY > 0) { prevStory() } else { nextStory() }
  }

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
  if (currentStoryIndex.value < stories.value.length - 1) {
    const fromId = getStoryArticleId(stories.value[currentStoryIndex.value])
    currentStoryIndex.value++
    const toId = getStoryArticleId(stories.value[currentStoryIndex.value])
    trackNavigate(fromId, toId, 'next')

    const story = stories.value[currentStoryIndex.value]
    if (!story || (!story.video && !story.podcast && !story.content)) {
      const validIndex = stories.value.findIndex(s => s.video || s.podcast || s.content)
      if (validIndex !== -1) currentStoryIndex.value = validIndex
    }
  } else {
    handleStoryBack()
  }
}

const prevStory = () => {
  if (currentStoryIndex.value > 0) {
    const fromId = getStoryArticleId(stories.value[currentStoryIndex.value])
    currentStoryIndex.value--
    const toId = getStoryArticleId(stories.value[currentStoryIndex.value])
    trackNavigate(fromId, toId, 'prev')

    const story = stories.value[currentStoryIndex.value]
    if (!story || (!story.video && !story.podcast && !story.content)) {
      const validIndex = stories.value.findIndex(s => s.video || s.podcast || s.content)
      if (validIndex !== -1) currentStoryIndex.value = validIndex
    }
  }
}

const handleStoryBack = () => {
  emit('back')
}

const handleFollow = (authorId: string) => {
  emit('follow', authorId)
}

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

  let articleId: string | null = null
  let textContent = ''

  if (storyOrContent) {
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

    try {
      textContent = story.content?.originalArticle?.content_elements
        ?.filter((el: any) => el.type === 'text')
        .map((el: any) => el.content)
        .join(' ')
        .replace(/https?:\/\/[^\s]+/g, '')
        .replace(/\s+/g, ' ')
        .trim() ?? ''
    } catch { /* not all content types have content_elements */ }
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
        const parent = comments.value.find((c: any) => c._id === replyingTo.value)
        if (parent) {
          if (!parent.replies) parent.replies = []
          parent.replies.push(newDoc)
        }
      } else {
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
  if (!chatbotMessage.value.trim()) return

  const userMessageId = Math.max(...chatbotMessages.value.map(m => m.id)) + 1
  const botMessageId = userMessageId + 1
  const articleContent = currentArticleContent.value
  let responseMessage = "I'm sorry, I'm having trouble connecting to the AI service right now. Please try again later."

  try {
    const API_KEY = 'AIzaSyB-AsIIwQnGGC_y3MY9OpupF9yPsK1CSGk'
    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${API_KEY}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ parts: [{ text: `User question: ${chatbotMessage.value.trim()}\n\nArticle Content:\n${articleContent}` }] }],
          generationConfig: { temperature: 0.2, topK: 40, topP: 0.95, maxOutputTokens: 1024 },
        }),
      },
    )

    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const responseData = await response.json()
    responseMessage = responseData.candidates[0].content.parts[0].text
  } catch {
    // fall back to default error message
  }

  chatbotMessages.value.push({
    id: userMessageId,
    type: 'user',
    text: chatbotMessage.value.trim(),
    time: 'Just now'
  })

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
    originalArticle: article
  }
}

function convertVideoToVerticalVideoFormat(video: Video): any {
  const mp4Streams = video.streams?.filter(stream => stream.stream_type === 'mp4') || []
  const bestStream = mp4Streams.find(stream => stream.bitrate >= 1200) ||
                    mp4Streams.find(stream => stream.bitrate >= 600) ||
                    mp4Streams[0]

  return {
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


</script>

<style scoped>
.story-feed-container {
  @apply fixed inset-0 bg-black z-50;
  @apply overflow-hidden;
  @apply outline-none;
  @apply touch-none;
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
  @apply min-h-0;
  @apply max-h-full;
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

.comments-empty {
  @apply flex items-center justify-center py-12 text-gray-400 text-sm;
}

.comments-skeleton {
  padding: 0.5rem 0;
}

.comment-skeleton-item {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.comment-skeleton-avatar {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  flex-shrink: 0;
}

.comment-skeleton-body {
  flex: 1;
}

.skeleton-line-dark {
  border-radius: 0.25rem;
}

.skeleton-pulse-dark {
  background: rgba(255, 255, 255, 0.08);
  position: relative;
  overflow: hidden;
}

.skeleton-pulse-dark::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.06) 50%, transparent 100%);
  animation: shimmer 1.4s ease-in-out infinite;
}

@keyframes shimmer {
  0%   { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.chatbot-list {
  @apply flex-1 overflow-y-auto p-4;
  @apply space-y-4;
  @apply min-h-0;
  @apply max-h-full;
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
