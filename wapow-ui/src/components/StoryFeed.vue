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
      :class="{ swiping: isSwiping }"
      :style="{ transform: `translateY(${currentStoryIndex * -100 + swipeOffset}vh)` }"
    >
      <div v-for="(story, index) in stories" :key="story.id" class="story-wrapper">
        <!-- Virtual window: only render stories within ±1 of current index -->
        <template v-if="Math.abs(index - currentStoryIndex) <= 1">
          <ErrorBoundary fallback-message="Failed to load this story.">
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
          </ErrorBoundary>
        </template>
        <!-- Placeholder for off-screen stories (maintains layout positioning) -->
        <div v-else class="story-placeholder"></div>
      </div>
    </div>

    <!-- Comment Sheet (extracted component) -->
    <CommentSheet
      v-if="showComments"
      :article-id="currentArticleId"
      :article-content="currentArticleContent"
      @close="showComments = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import StoryView from './StoryView.vue'
import VerticalVideoView from './VerticalVideoView.vue'
import PodcastView from './PodcastView.vue'
import Game from '@/views/wordle/Game.vue'
import CommentSheet from './CommentSheet.vue'
import ErrorBoundary from './ErrorBoundary.vue'
import { apiFetch } from '@/lib/api'
import { useContentStore } from '@/stores/content'
import { useAnalytics } from '@/composables/useAnalytics'
import type { Video, StoryContent, Article } from '@/stores/content'

const contentStore = useContentStore()
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
  const type = story?.mediaType === 'story' ? 'article' : story?.mediaType || ''
  trackSave(id, saved, type, story?.category || '')
}

onMounted(() => {
  fetchSavedArticleIds()
})

const showComments = ref(false)
const currentArticleContent = ref<string>('')
const currentArticleId = ref<string | null>(null)

const touchStart = ref({ x: 0, y: 0 })
const touchEnd = ref({ x: 0, y: 0 })
const isSwiping = ref(false)

// Build stories list once (not in a computed — avoids re-shuffling on every state change)
const stories = ref<Story[]>([])

function buildStories(): Story[] {
  const baseStories: Story[] = []

  if (props.initialArticle && (props.initialArticle as any)._videoRef) {
    const videoData = (props.initialArticle as any)._videoRef
    baseStories.push({
      id: `video-${props.initialArticle._id}`,
      mediaType: 'video',
      video: videoData,
      category: props.category,
    })
  } else if (props.initialArticle && (props.initialArticle as any)._podcastRef) {
    const podcastData = (props.initialArticle as any)._podcastRef
    baseStories.push({
      id: `podcast-${props.initialArticle._id}`,
      mediaType: 'podcast',
      podcast: podcastData,
      category: props.category,
    })
  } else if (props.initialArticle && props.initialArticle.headlines?.basic) {
    baseStories.push({
      id: `story-${props.initialArticle._id}`,
      mediaType: 'story',
      content: convertArticleToStoryContent(props.initialArticle),
      category: props.category,
    })
  }

  if (props.articles && props.articles.length > 0) {
    props.articles.forEach((article) => {
      if (article && article.headlines?.basic && article._id !== props.initialArticle?._id) {
        baseStories.push({
          id: `story-related-${article._id}`,
          mediaType: 'story',
          content: convertArticleToStoryContent(article),
          category: getCategoryFromArticle(article),
        })
      } else if (article && (article as any).type === 'game') {
        baseStories.push({
          id: `game-${article._id}`,
          mediaType: 'game',
          content: article,
          category: 'Games',
        })
      }
    })
  }

  // Fill up to 20 stories with a rotating article → video → podcast pattern
  const targetStories = 20
  const currentStories = baseStories.length

  if (currentStories < targetStories) {
    const allArticles = contentStore.articles.filter(
      (article) =>
        article &&
        article.headlines?.basic &&
        !baseStories.some((story) => story.id === `story-${article._id}`),
    )
    const allVideos = contentStore.videos.filter(
      (video) =>
        video &&
        video.content_id &&
        !baseStories.some((story) => story.id === `video-${video.content_id}`),
    )
    const allPodcastClips = contentStore.podcastClips.filter(
      (podcast) =>
        podcast && podcast.id && !baseStories.some((story) => story.id === `podcast-${podcast.id}`),
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
      const shouldAddArticle =
        (cycle === 0 ||
          (cycle === 1 && videoIndex >= shuffledVideos.length) ||
          (cycle === 2 && podcastIndex >= shuffledPodcastClips.length)) &&
        articleIndex < shuffledArticles.length

      if (shouldAddVideo) {
        const video = shuffledVideos[videoIndex]
        baseStories.push({
          id: `video-${video.content_id}`,
          mediaType: 'video' as const,
          video: video,
          category: getCategoryFromVideo(video),
        })
        videoIndex++
      } else if (shouldAddPodcast) {
        const podcast = shuffledPodcastClips[podcastIndex]
        baseStories.push({
          id: `podcast-${podcast.id}`,
          mediaType: 'podcast' as const,
          podcast: podcast,
          category: getCategoryFromPodcast(podcast),
        })
        podcastIndex++
      } else if (shouldAddArticle) {
        const article = shuffledArticles[articleIndex]
        baseStories.push({
          id: `story-mixed-${article._id}`,
          mediaType: 'story',
          content: convertArticleToStoryContent(article),
          category: getCategoryFromArticle(article),
        })
        articleIndex++
      } else {
        break
      }
    }

    // Ensure at least one video is present if the store has any
    if (
      contentStore.videos.length > 0 &&
      !baseStories.some((story) => story.mediaType === 'video')
    ) {
      const firstVideo = contentStore.videos[0]
      baseStories.push({
        id: `forced-video-${firstVideo.content_id}`,
        mediaType: 'video' as const,
        video: firstVideo,
        category: getCategoryFromVideo(firstVideo),
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
}

// Build once on mount (and when props change)
onMounted(() => {
  stories.value = buildStories()
})

watch(
  () => [props.initialArticle, props.articles] as const,
  () => {
    stories.value = buildStories()
  },
)

const currentStory = computed(() => stories.value[currentStoryIndex.value])

watch(
  currentStory,
  (newStory, oldStory) => {
    if (oldStory) stopDwell(getStoryArticleId(oldStory))
    if (newStory) {
      const id = getStoryArticleId(newStory)
      const type = newStory.mediaType === 'story' ? 'article' : newStory.mediaType
      const cat = newStory.category || ''
      trackView(id, type, cat)
      startDwell(id, type, cat)
    }
  },
  { immediate: true },
)

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
    if (deltaY > 0) {
      prevStory()
    } else {
      nextStory()
    }
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
      const validIndex = stories.value.findIndex((s) => s.video || s.podcast || s.content)
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
      const validIndex = stories.value.findIndex((s) => s.video || s.podcast || s.content)
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
      textContent =
        story.content?.originalArticle?.content_elements
          ?.filter((el: any) => el.type === 'text')
          .map((el: any) => el.content)
          .join(' ')
          .replace(/https?:\/\/[^\s]+/g, '')
          .replace(/\s+/g, ' ')
          .trim() ?? ''
    } catch {
      /* not all content types have content_elements */
    }
  }

  currentArticleId.value = articleId
  currentArticleContent.value = textContent
  showComments.value = true
}

function convertArticleToStoryContent(article: Article): any {
  return {
    title: article.headlines?.basic || 'Untitled Article',
    description:
      article.description?.basic || article.subheadlines?.basic || 'No description available',
    thumbnail: article.promo_items?.basic?.url || 'https://picsum.photos/400/600?random=article',
    focalPoint:
      (article as any).promo_items?.basic?.focal_point || (article as any).imageFocalPoint || null,
    author: {
      name: article.credits?.by?.[0]?.name || 'Unknown Author',
      username: `@${article.credits?.by?.[0]?.name?.toLowerCase().replace(/\s+/g, '') || 'unknown'}`,
      avatar: 'https://picsum.photos/50/50?random=author',
    },
    createdAt: article.publish_date || new Date().toISOString(),
    originalArticle: article,
  }
}

function convertVideoToVerticalVideoFormat(video: Video): any {
  const mp4Streams = video.streams?.filter((stream) => stream.stream_type === 'mp4') || []
  const bestStream =
    mp4Streams.find((stream) => stream.bitrate >= 1200) ||
    mp4Streams.find((stream) => stream.bitrate >= 600) ||
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
      avatar: 'https://picsum.photos/50/50?random=wapo',
    },
    likes: Math.floor(Math.random() * 1000),
    comments: Math.floor(Math.random() * 100),
    shares: Math.floor(Math.random() * 50),
    views: Math.floor(Math.random() * 10000),
    createdAt: new Date().toISOString(),
    mediaType: 'video',
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
  return (
    article.taxonomy?.primary_section?.name ||
    article.taxonomy?.sections?.[0]?.name ||
    article.type ||
    'News'
  )
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

.story-placeholder {
  @apply h-screen w-full;
  @apply bg-black;
  @apply flex-shrink-0;
  @apply min-h-screen;
}
</style>
