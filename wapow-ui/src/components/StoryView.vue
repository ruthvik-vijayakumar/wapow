<template>
  <div 
    class="story-container"
  >
    <!-- Debug info (temporary) -->
    <!-- <div class="debug-info">
      <p>Story Index: {{ storyIndex }} / {{ totalStories }}</p>
      <p>Page: {{ currentPageIndex + 1 }} / {{ pages.length }}</p>
      <p>Title: {{ currentPage?.title }}</p>
    </div> -->

    <!-- Progress Bars -->
    <div class="progress-container">
      <div class="progress-bars">
        <div 
          v-for="(page, index) in pages" 
          :key="index"
          class="progress-bar"
          :class="{ 'completed': index < currentPageIndex, 'current': index === currentPageIndex }"
        >
          <div 
            v-if="index === currentPageIndex"
            class="progress-fill"
            :style="{ width: `${(currentPageIndex / (pages.length - 1)) * 100}%` }"
          ></div>
        </div>
      </div>
    </div>

    <!-- Header -->
    <div class="story-header">
      <button @click="handleBack" class="back-button">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      
      <div class="header-actions">
        <!-- <button class="action-button">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button> -->
        
        <button
          class="action-button"
          :class="{ 'saved': isSaved }"
          @click.stop="handleSave"
          @touchend.stop.prevent="handleSave"
          aria-label="Save article"
        >
          <svg class="w-5 h-5" :fill="isSaved ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="story-content" :class="{ 'has-padding': currentPage.layout === 'text-top' || currentPage.layout === 'image-top' }" @click="handleContentClick">
      <!-- Layout: Text on top, Image on bottom -->
      <template v-if="currentPage.layout === 'text-top'">
        <div class="text-top-container">
          <div class="text-section">
            <p class="story-description">{{ currentPage.description }}</p>
          </div>
          
          <div class="image-section">
            <img :src="currentPage.thumbnail" :alt="currentPage.title" class="story-image" />
          </div>
        </div>
      </template>

      <!-- Layout: Image on top, Text on bottom (standard) -->
      <template v-else-if="currentPage.layout === 'image-top'">
        <div class="text-top-container mb-2">
          <div class="image-section">
            <img :src="currentPage.thumbnail" :alt="currentPage.title" class="story-image" />
          </div>
          <div class="text-section">
            <p class="story-description">{{ currentPage.description }}</p>
          </div>
          
          
        </div>
      </template>

      <!-- Layout: Takeaways -->
      <template v-else-if="currentPage.layout === 'takeaways'">
        <div class="takeaways-container">
          <div class="takeaways-header">
            <h1 class="takeaways-title">Key Takeaways</h1>
          </div>
          <div class="takeaways-description">{{ currentPage.description }}</div>
          <!-- <div class="takeaways-list">
            <div class="takeaway-item">
              <div class="takeaway-bullet">•</div>
              <div class="takeaway-text">The situation has evolved rapidly with new developments</div>
            </div>
            <div class="takeaway-item">
              <div class="takeaway-bullet">•</div>
              <div class="takeaway-text">Key stakeholders have responded to the changes</div>
            </div>
            <div class="takeaway-item">
              <div class="takeaway-bullet">•</div>
              <div class="takeaway-text">Experts predict significant future implications</div>
            </div>
            <div class="takeaway-item">
              <div class="takeaway-bullet">•</div>
              <div class="takeaway-text">The broader impact extends beyond initial expectations</div>
            </div>
          </div> -->
          
          <div class="poll-section">
            <div class="poll-question">What's your take on this story?</div>
            <div class="poll-options">
              <div class="poll-option" @click.stop="selectPollOption(1)" :class="{ 'voted': hasVoted }">
                <div class="poll-radio" :class="{ 'selected': selectedPollOption === 1 }"></div>
                <div class="poll-text">Very interesting</div>
                <div v-if="hasVoted" class="poll-percentage">
                  <div class="percentage-bar" :style="{ width: getPollPercentage(1) + '%' }"></div>
                  <span class="percentage-text">{{ getPollPercentage(1) }}%</span>
                </div>
              </div>
              <div class="poll-option" @click.stop="selectPollOption(2)" :class="{ 'voted': hasVoted }">
                <div class="poll-radio" :class="{ 'selected': selectedPollOption === 2 }"></div>
                <div class="poll-text">Somewhat relevant</div>
                <div v-if="hasVoted" class="poll-percentage">
                  <div class="percentage-bar" :style="{ width: getPollPercentage(2) + '%' }"></div>
                  <span class="percentage-text">{{ getPollPercentage(2) }}%</span>
                </div>
              </div>
              <div class="poll-option" @click.stop="selectPollOption(3)" :class="{ 'voted': hasVoted }">
                <div class="poll-radio" :class="{ 'selected': selectedPollOption === 3 }"></div>
                <div class="poll-text">Not my interest</div>
                <div v-if="hasVoted" class="poll-percentage">
                  <div class="percentage-bar" :style="{ width: getPollPercentage(3) + '%' }"></div>
                  <span class="percentage-text">{{ getPollPercentage(3) }}%</span>
                </div>
              </div>
              <div class="poll-option" @click.stop="selectPollOption(4)" :class="{ 'voted': hasVoted }">
                <div class="poll-radio" :class="{ 'selected': selectedPollOption === 4 }"></div>
                <div class="poll-text">Need more info</div>
                <div v-if="hasVoted" class="poll-percentage">
                  <div class="percentage-bar" :style="{ width: getPollPercentage(4) + '%' }"></div>
                  <span class="percentage-text">{{ getPollPercentage(4) }}%</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="read-full-button">
            <button @click.stop="readFullArticle" class="full-article-btn">
              Read Full Article
            </button>
          </div>
        </div>
      </template>

      <!-- Layout: Standard (original) -->
      <template v-else>
        <div class="content-image">
          <img :src="currentPage.thumbnail" :alt="currentPage.title" class="story-image" />
          <div class="image-overlay"></div>
        </div>
        
        <div class="content-text">
          <!-- Recommendation Badge -->
          <div v-if="recommendationReason" class="recommendation-badge">
            <span class="badge-icon">{{ recommendationIcon }}</span>
            <span class="badge-text">{{ recommendationReason }}</span>
          </div>
          
          <h1 class="story-title">{{ currentPage.title }}</h1>
          <p class="story-description">{{ currentPage.description }}</p>
        </div>
      </template>
    </div>

    <!-- Bottom Controls -->
    <BottomControls 
      :initial-liked="isLiked"
      :initial-listening="isListening"
      :show-category="true"
      :show-reactions="true"
      :show-listen="true"
      :category="category"
      :article-content="props.content"
      @like="handleLike"
      @listen="handleListen"
      @comments="toggleComments"
      @reaction="selectReaction"
    />

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import type { StoryContent } from '@/stores/videos'
import BottomControls from './BottomControls.vue'
import { apiFetch } from '@/lib/api'

interface Props {
  content: StoryContent | any
  category: string
  storyIndex?: number
  totalStories?: number
  isSaved?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  storyIndex: 0,
  totalStories: 1,
  isSaved: false
})

const router = useRouter()

// Debug props
console.log('StoryView props:', {
  content: props.content,
  category: props.category,
  storyIndex: props.storyIndex,
  totalStories: props.totalStories
})

const emit = defineEmits<{
  back: []
  follow: [authorId: string]
  nextStory: []
  prevStory: []
  comments: []
  save: [content: { id: string; collection?: string; saved: boolean }]
}>()

const isSaved = computed(() => props.isSaved)

const handleSave = async () => {
  const id = props.content?.originalArticle?._id ?? props.content?.originalArticle?.id ?? props.content?._id ?? props.content?.id
  console.log('[handleSave] content keys:', props.content ? Object.keys(props.content) : 'null')
  console.log('[handleSave] resolved id:', id, 'isSaved:', props.isSaved)
  if (!id) {
    console.warn('[handleSave] No article ID found, skipping save')
    return
  }
  const articleId = String(id)
  const collection = props.content?.collection ?? props.category ?? 'articles'
  const currentlySaved = props.isSaved

  try {
    if (currentlySaved) {
      console.log('[handleSave] Unsaving article:', articleId)
      const res = await apiFetch(`/api/saved-articles/${encodeURIComponent(articleId)}`, { method: 'DELETE' })
      console.log('[handleSave] Unsave response:', res.status)
      if (res.ok) {
        emit('save', { id: articleId, collection, saved: false })
      }
    } else {
      console.log('[handleSave] Saving article:', articleId, 'collection:', collection)
      const res = await apiFetch('/api/saved-articles', {
        method: 'POST',
        body: JSON.stringify({ article_id: articleId, collection })
      })
      console.log('[handleSave] Save response:', res.status)
      if (res.ok) {
        emit('save', { id: articleId, collection, saved: true })
      }
    }
  } catch (err) {
    console.error('[handleSave] Error:', err)
    emit('save', { id: articleId, collection, saved: !currentlySaved })
  }
}

const currentPageIndex = ref(0)
const isLiked = ref(false)
const isListening = ref(false)
const showReactions = ref(false)
const selectedReaction = ref('')
const likeHoldTimer = ref<number | null>(null)
const reactionHoldTimer = ref<number | null>(null)
const autoAdvanceTimer = ref<NodeJS.Timeout | null>(null)
const isVisible = ref(false)
const selectedPollOption = ref<number | null>(null)
const pollResults = ref<{ [key: number]: number }>({
  1: 45, // Very interesting
  2: 28, // Somewhat relevant
  3: 15, // Not my interest
  4: 12  // Need more info
})
const hasVoted = ref(false)

// Create story pages from the content data
const pages = computed(() => {
  // Ensure we have valid content data
  if (!props.content || !props.content.title) {
    return [{
      title: "Story Content",
      description: "This story contains important information.",
      thumbnail: "https://picsum.photos/400/600?random=fallback",
      author: { name: 'Unknown', username: '@unknown', avatar: 'https://picsum.photos/50/50?random=fallback' },
      createdAt: new Date().toISOString()
    }]
  }

  // Create author info from content
  const author = {
    name: props.content.author?.name || 'Unknown Author',
    username: props.content.author?.username || '@unknown',
    avatar: props.content.author?.avatar || 'https://picsum.photos/50/50?random=author'
  }

  const createdAt = props.content.createdAt || props.content.publish_date || new Date().toISOString()
  const pages_data  = props.content.originalArticle.ai_summary?.pages?.filter((page: any) => page.page_type !=='hero') || []
  console.log('🔮🗓️pages', pages_data)
  return [
    {
      ...props.content,
      title: props.content.title,
      description: props.content.description,
      thumbnail: props.content.thumbnail,
      author: author,
      createdAt: createdAt,
      layout: 'standard' // Image on top, text on bottom`
    },
    ...pages_data.filter((page: any) => page.page_type === 'content').map((page: any, index: number) => ({
      title: page.content.filter((item: any) => item && item['type'] === 'text')[0].content,
      description: page.content.filter((item: any) => item && item['type'] === 'text')[0].content,
      thumbnail: page.content.filter((item: any) => item && item['type'] === 'image')[0].content_url,
      author: author,
      createdAt: createdAt,
      layout: index % 2 === 0 ? 'text-top' : 'image-top' // Image on top, text on bottom
    })),
    // {
    //   title: "Breaking News",
    //   description: "This story continues with additional details and insights about the latest developments. The situation has evolved rapidly, with new information coming to light that changes our understanding of the events. Key stakeholders have responded, and the implications are far-reaching.",
    //   thumbnail: "https://picsum.photos/400/600?random=story1",
    //   author: author,
    //   createdAt: createdAt,
    //   layout: 'text-top' // Text on top, image on bottom
    // },
    // {
    //   title: "Expert Analysis",
    //   description: "Industry experts weigh in on the implications and future impact of this development. Their insights provide valuable context for understanding the broader implications and what this means for the future.",
    //   thumbnail: "https://picsum.photos/400/600?random=story2",
    //   author: author,
    //   createdAt: createdAt,
    //   layout: 'image-top' // Image on top, text on bottom
    // },
    ...pages_data.filter((page: any) => page.page_type === 'overview').map((page: any, index: number) => ({
      title: "Key Takeaways",
      description: page.content.filter((item: any) => item && item['type'] === 'text')[0].content,
      // thumbnail: page.content.filter((item: any) => item && item['type'] === 'image')[0].content_url,
      author: author,
      createdAt: createdAt,
      layout: 'takeaways' // Image on top, text on bottom
    })),
    // {
    //   title: "Key Takeaways",
    //   description: "Here are the main points to remember from this story.",
    //   thumbnail: "https://picsum.photos/400/600?random=story3",
    //   author: author,
    //   createdAt: createdAt,
    //   layout: 'takeaways' // Key takeaways layout
    // }
  ]
})

const currentPage = computed(() => {
  const page = pages.value[currentPageIndex.value]
  console.log('🔮🗓️currentPage', page)
  // Ensure we always have valid content
  // if (!page || !page.title || !page.thumbnail) {
  //   return {
  //     title: "Story Content",
  //     description: "This story contains important information.",
  //     thumbnail: "https://picsum.photos/400/600?random=fallback",
  //     author: { name: 'Unknown', username: '@unknown', avatar: 'https://picsum.photos/50/50?random=fallback' },
  //     createdAt: new Date().toISOString()
  //   }
  // }
  
  return page
})

// Recommendation badge logic
const recommendationReason = computed(() => {
  // Determine why this story is recommended based on category and other factors
  const category = props.category.toLowerCase()
  
  // Check if user follows this category
  if (category.includes('sports')) {
    return 'Because you follow Sports'
  }
  if (category.includes('politics') || category.includes('news')) {
    return 'Because you follow Politics'
  }
  if (category.includes('technology') || category.includes('tech')) {
    return 'Because you follow Technology'
  }
  if (category.includes('entertainment')) {
    return 'Because you follow Entertainment'
  }
  if (category.includes('business')) {
    return 'Because you follow Business'
  }
  
  // Check if it's trending/hot news
  if (Math.random() > 0.7) {
    return 'Hot News'
  }
  
  // Check if it's latest news
  if (Math.random() > 0.5) {
    return 'Latest News'
  }
  
  // Default recommendation
  return 'Recommended for you'
})

const recommendationIcon = computed(() => {
  const reason = recommendationReason.value
  
  if (reason.includes('Sports')) return '⚽'
  if (reason.includes('Politics')) return '🏛️'
  if (reason.includes('Technology')) return '💻'
  if (reason.includes('Entertainment')) return '🎭'
  if (reason.includes('Business')) return '💰'
  if (reason.includes('Hot News')) return '🔥'
  if (reason.includes('Latest News')) return '📰'
  
  return '✨'
})

const handleContentClick = (event: MouseEvent) => {
  const target = event.currentTarget as HTMLElement
  const rect = target?.getBoundingClientRect()
  if (!rect) return

  const clickX = event.clientX - rect.left
  const width = rect.width

  // Determine click area
  if (clickX < width * 0.5) {
    // Left side - previous page
    prevPage()
  } else {
    // Right side - next page
    nextPage()
  }
}

const nextPage = () => {
  if (currentPageIndex.value < pages.value.length - 1) {
    currentPageIndex.value++
  } else {
    // Move to next story if available
    if (props.storyIndex < props.totalStories - 1) {
      emit('nextStory')
    } else {
      handleBack()
    }
  }
}

const prevPage = () => {
  if (currentPageIndex.value > 0) {
    currentPageIndex.value--
  }
}

// Touch handling for reactions
const startLikeHold = () => {
  likeHoldTimer.value = window.setTimeout(() => {
    showReactions.value = true
  }, 500)
}

const endLikeHold = () => {
  if (likeHoldTimer.value) {
    clearTimeout(likeHoldTimer.value)
    likeHoldTimer.value = null
  }
}

const selectReaction = (reaction: string) => {
  selectedReaction.value = reaction
  showReactions.value = false
  // You can emit the reaction to parent component if needed
  console.log('Selected reaction:', reaction)
}

const handleBack = () => {
  emit('back')
}

const handleLike = () => {
  isLiked.value = !isLiked.value
  console.log('Story liked:', isLiked.value)
}

const handleListen = () => {
  isListening.value = !isListening.value
  console.log('Story listening:', isListening.value)
}

const toggleComments = (articleContent?: any) => {
  emit('comments')
  console.log('Comments event emitted to parent with content:', articleContent)
}

const readFullArticle = () => {
  // Navigate to the article view with the canonical URL
  if (props.content.originalArticle.canonical_url) {
    const articleTitle = props.content.title || props.content.headlines?.basic || 'Article'
    const encodedUrl = encodeURIComponent(props.content.originalArticle.canonical_url)
    const encodedTitle = encodeURIComponent(articleTitle)
    router.push(`/article/${encodedUrl}/${encodedTitle}`)
  } else {
    console.log('No canonical URL available')
  }
}

const selectPollOption = (option: number) => {
  selectedPollOption.value = option
  hasVoted.value = true
  
  // Update poll results (simulate voting)
  pollResults.value[option] = (pollResults.value[option] || 0) + 1
  
  // Prevent auto-advance when poll is voted
  stopAutoAdvance()
  
  console.log('Selected poll option:', option)
}

const getPollPercentage = (option: number): number => {
  const total = Object.values(pollResults.value).reduce((sum, count) => sum + count, 0)
  const percentage = total > 0 ? Math.round((pollResults.value[option] || 0) / total * 100) : 0
  return percentage
}

// Auto-advance functionality
const startAutoAdvance = () => {
  if (autoAdvanceTimer.value) {
    clearTimeout(autoAdvanceTimer.value)
  }
  
  // Auto-advance to next page after 5 seconds
  autoAdvanceTimer.value = setTimeout(() => {
    if (currentPageIndex.value < pages.value.length - 1) {
      currentPageIndex.value++
      startAutoAdvance() // Restart timer for next page
    }
  }, 5000)
}

const stopAutoAdvance = () => {
  if (autoAdvanceTimer.value) {
    clearTimeout(autoAdvanceTimer.value)
    autoAdvanceTimer.value = null
  }
}

// Intersection observer for visibility-based autoplay
const setupIntersectionObserver = () => {
  const storyContainer = document.querySelector('.story-container') as HTMLElement
  if (!storyContainer) return

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          // Story is visible - start auto-advance
          isVisible.value = true
          // startAutoAdvance()
        } else {
          // Story is not visible - stop auto-advance
          isVisible.value = false
          // stopAutoAdvance()
        }
      })
    },
    {
      threshold: 0.5,
      rootMargin: '0px'
    }
  )

  observer.observe(storyContainer)
}

onMounted(() => {
  // Setup intersection observer for auto-advance
  setupIntersectionObserver()
})

onUnmounted(() => {
  // Cleanup auto-advance timer
  stopAutoAdvance()
})
</script>

<style scoped>
.story-container {
  @apply relative inset-0 bg-black;
  @apply flex flex-col;
  @apply touch-none;
  @apply w-full;
  /* Mobile viewport handling */
  height: 100vh;
  height: 100dvh; /* Dynamic viewport height for mobile */
  min-height: -webkit-fill-available;
  /* Safe area insets for notched devices */
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
}

/* Debug info */
.debug-info {
  @apply absolute top-4 left-4 z-50;
  @apply bg-black bg-opacity-70 p-2 rounded-md text-white text-xs;
}

/* Progress Bars */
.progress-container {
  @apply absolute top-0 left-0 right-0 z-10;
  @apply px-4 pt-2;
}

.progress-bars {
  @apply flex space-x-1;
}

.progress-bar {
  @apply flex-1 h-0.5 bg-gray-600 rounded-full overflow-hidden;
  @apply transition-all duration-300;
}

.progress-bar.completed {
  @apply bg-white;
}

.progress-bar.current {
  @apply bg-white;
}

.progress-fill {
  @apply h-full bg-white transition-all duration-100 ease-out;
}

/* Header */
.story-header {
  @apply flex items-center justify-between px-4 pt-6 pb-2;
  @apply relative z-10;
}

.back-button {
  @apply w-8 h-8 rounded-full bg-black bg-opacity-50;
  @apply flex items-center justify-center text-white;
  @apply hover:bg-opacity-70 transition-colors;
}

.header-actions {
  @apply flex items-center space-x-2;
}

.action-button {
  @apply w-8 h-8 rounded-full bg-black bg-opacity-50;
  @apply flex items-center justify-center text-white;
  @apply hover:bg-opacity-70 transition-colors;
  touch-action: manipulation; /* Ensure tap triggers click on touch devices */
}

.action-button.saved {
  @apply text-blue-400;
}

/* Main Content */
.story-content {
  @apply flex-1 relative;
  @apply cursor-pointer;
  @apply h-full w-full;
  @apply overflow-hidden;
}

/* Add padding for text-top and image-top layouts */
.story-content.has-padding {
  @apply p-4;
}

.content-image {
  @apply absolute inset-0;
}

.story-image {
  @apply w-full h-full object-cover;
}

.image-overlay {
  @apply absolute inset-0;
  @apply bg-gradient-to-t from-black via-transparent to-transparent;
}

.content-text {
  @apply absolute bottom-0 left-0 right-0 p-6;
  @apply text-white;
}

/* Text-top layout styles */
.text-top-container {
  @apply flex flex-col h-full w-full;
}

.text-section {
  @apply flex-1 bg-black bg-opacity-90;
  @apply flex items-center p-6;
}

.text-section .story-description {
  @apply text-lg leading-relaxed;
  @apply text-white;
}

.image-section {
  @apply h-1/2 bg-gray-900;
  @apply flex items-center justify-center;
}

.image-section .story-image {
  @apply max-h-full max-w-full object-cover;
  @apply block;
}

/* Image-top layout styles */
.image-top-container {
  @apply flex flex-col h-full w-full;
}

.image-section-top {
  @apply flex-1 bg-gray-900;
  @apply flex items-center justify-center p-4;
}

.image-section-top .story-image {
  @apply max-h-full max-w-full object-contain;
  @apply block;
  @apply rounded-lg;
}

.text-section-bottom {
  @apply flex-1 bg-black bg-opacity-90;
  @apply flex flex-col justify-center p-6;
}

.text-section-bottom .story-title {
  @apply text-2xl font-bold mb-3;
  @apply font-postoni;
  @apply text-white;
}

.text-section-bottom .story-description {
  @apply text-base leading-relaxed;
  @apply text-gray-200;
}

/* Takeaways layout styles */
.takeaways-container {
  @apply flex flex-col h-full w-full;
  @apply bg-black bg-opacity-95;
  @apply p-6;
}

.takeaways-header {
  @apply mb-6;
}

.takeaways-title {
  @apply text-2xl font-bold;
  @apply font-postoni;
  @apply text-white;
}

.takeaways-list {
  @apply flex-1 space-y-4;
}

.takeaway-item {
  @apply flex items-start space-x-3;
}

.takeaway-bullet {
  @apply text-white text-xl font-bold;
  @apply flex-shrink-0;
  @apply mt-1;
}

.takeaway-text {
  @apply text-white text-base leading-relaxed;
}

.author-info {
  @apply flex items-center space-x-3;
  @apply mb-6;
  @apply p-4;
  @apply bg-gray-800 bg-opacity-50;
  @apply rounded-lg;
}

.author-avatar {
  @apply flex-shrink-0;
}

.author-img {
  @apply w-12 h-12 rounded-full;
  @apply object-cover;
}

.author-details {
  @apply flex flex-col;
}

.author-name {
  @apply text-white font-medium;
}

.author-username {
  @apply text-gray-300 text-sm;
}

/* Poll styles */
.poll-section {
  @apply mt-4;
}

.poll-question {
  @apply text-white font-medium font-postoni text-xl;
  @apply mb-4;
}

.poll-options {
  @apply space-y-3;
}

.poll-option {
  @apply flex items-center space-x-3;
  @apply cursor-pointer;
  @apply p-3;
  @apply bg-gray-800 bg-opacity-50;
  @apply rounded-lg;
  @apply transition-colors duration-200;
}

.poll-option:hover {
  @apply bg-gray-700 bg-opacity-70;
}

.poll-radio {
  @apply w-5 h-5;
  @apply border-2 border-gray-400;
  @apply rounded-full;
  @apply flex-shrink-0;
  @apply transition-all duration-200;
}

.poll-radio.selected {
  @apply border-blue-500;
  @apply bg-blue-500;
  @apply relative;
}

.poll-radio.selected::after {
  content: '';
  @apply absolute;
  @apply w-2 h-2;
  @apply bg-white;
  @apply rounded-full;
  @apply top-1/2 left-1/2;
  @apply transform -translate-x-1/2 -translate-y-1/2;
}

.poll-text {
  @apply text-white text-base;
  @apply flex-1;
}

.poll-option.voted {
  @apply relative;
  @apply overflow-hidden;
}

.poll-percentage {
  @apply absolute inset-0;
  @apply flex items-center justify-between;
  @apply px-3;
  @apply pointer-events-none;
}

.percentage-bar {
  @apply absolute left-0 top-0 bottom-0;
  @apply bg-blue-500 bg-opacity-20;
  @apply transition-all duration-1000 ease-out;
  @apply z-0;
}

.percentage-text {
  @apply text-white text-sm font-medium;
  @apply z-10;
  @apply relative;
}

.poll-option.voted .poll-radio,
.poll-option.voted .poll-text {
  @apply opacity-0;
  @apply transition-opacity duration-300;
}

.read-full-button {
  @apply flex justify-center mt-6;
}

.full-article-btn {
  @apply bg-gray-800 hover:bg-gray-900;
  @apply text-white font-medium;
  @apply px-4 py-2 rounded-full;
  @apply transition-colors duration-200;
  @apply text-center;
}

.story-title {
  @apply text-3xl font-bold mb-2;
  @apply font-postoni;
}

.story-description {
  line-height: 1.2rem;
  @apply text-base;
  @apply text-gray-200;
}

/* Recommendation Badge */
.recommendation-badge {
  @apply flex items-center space-x-2 mb-3;
  @apply bg-white bg-opacity-20 backdrop-blur-sm;
  @apply px-3 py-1 rounded-full;
  @apply text-white text-sm font-medium;
  @apply w-fit;
}

.badge-icon {
  @apply text-xs;
}

.badge-text {
  @apply font-medium;
}

/* Bottom Controls */
.story-bottom {
  @apply flex items-end justify-between px-6 pb-6;
  @apply relative z-10; /* Extra margin to account for bottom navigation */
}

.bottom-left {
  @apply flex flex-col items-start space-x-2 space-y-4;
}

.category-tag {
  @apply px-3 py-1 rounded-full;
  @apply text-white text-sm font-medium;
}

.decorative-text {
  @apply text-gray-400 text-sm;
}

.story-actions {
  @apply flex items-start space-x-4;
}

.like-button-container {
  @apply relative;
  @apply select-none;
}

.story-action-btn {
  @apply flex items-center space-x-1 text-white;
  @apply cursor-pointer;
  @apply select-none;
}

.story-action-btn.active {
  @apply text-accent;
}

.follow-button {
  @apply flex items-center px-3 py-1.5 bg-accent rounded-full;
  @apply text-white text-sm font-medium;
  @apply hover:bg-opacity-90 transition-colors;
}

/* Navigation Dots */
.navigation-dots {
  @apply absolute bottom-20 left-1/2 transform -translate-x-1/2;
  @apply flex space-x-2;
}

.nav-dot {
  @apply w-2 h-2 rounded-full bg-white bg-opacity-50;
  @apply transition-all duration-200;
}

.nav-dot.active {
  @apply bg-opacity-100;
}

/* Story Navigation Hints */
.story-nav-hints {
  @apply absolute inset-0 pointer-events-none;
}

.nav-hint {
  @apply absolute left-1/2 transform -translate-x-1/2;
  @apply w-12 h-12 rounded-full bg-black bg-opacity-50;
  @apply flex items-center justify-center text-white;
  @apply animate-pulse;
}

.nav-hint-up {
  @apply top-4;
}

.nav-hint-down {
  @apply bottom-20;
}

/* Reaction Popup */
.reactions-popup {
  @apply absolute bg-black bg-opacity-80 p-2 rounded-full;
  @apply flex space-x-1;
  @apply shadow-lg;
  z-index: 10;
  @apply select-none;
  /* Position above the button, centered */
  bottom: 100%;
  left: 50%;
  transform: translateX(-10%);
  margin-bottom: 8px;
}

.reaction-item {
  @apply flex flex-col items-center cursor-pointer;
  @apply text-white text-xs;
  @apply p-1.5 rounded-full;
  @apply hover:bg-gray-700;
  @apply select-none;
}

.reaction-emoji {
  @apply text-2xl mb-1;
}

.reaction-text {
  @apply font-medium;
}

/* Comments Bottom Sheet */
.comments-overlay {
  @apply fixed inset-0 bg-black bg-opacity-50;
  @apply flex items-end justify-center;
  @apply z-50;
}

.comments-sheet {
  @apply bg-gray-900 rounded-t-3xl;
  @apply w-full max-w-md;
  @apply max-h-[80vh] flex flex-col;
  @apply transform transition-transform duration-300 ease-out;
}

.comments-header {
  @apply flex items-center justify-between p-4;
  @apply border-b border-gray-700;
}

.comments-title {
  @apply text-white text-lg font-semibold;
}

.close-button {
  @apply text-gray-400 hover:text-white;
  @apply transition-colors duration-200;
}

.comments-list {
  @apply flex-1 overflow-y-auto p-4;
  @apply space-y-4;
}

.comment-item {
  @apply flex space-x-3;
}

.comment-avatar {
  @apply flex-shrink-0;
}

.comment-content {
  @apply flex-1;
}

.comment-author {
  @apply text-white font-medium text-sm;
}

.comment-text {
  @apply text-gray-300 text-sm mt-1;
}

.comment-meta {
  @apply flex items-center space-x-4 mt-2;
}

.comment-time {
  @apply text-gray-500 text-xs;
}

.comment-like {
  @apply flex items-center space-x-1 text-gray-400;
  @apply hover:text-white transition-colors duration-200;
}

.comment-input {
  @apply flex items-center space-x-2 p-4;
  @apply border-t border-gray-700;
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
</style> 