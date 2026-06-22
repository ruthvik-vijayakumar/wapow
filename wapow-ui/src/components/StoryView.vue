<template>
  <div ref="storyContainerRef" class="story-container">
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
          :class="{ completed: index < currentPageIndex, current: index === currentPageIndex }"
        >
          <div
            v-if="index === currentPageIndex"
            class="progress-fill"
            :style="{
              width: `${pages.length > 1 ? (currentPageIndex / (pages.length - 1)) * 100 : 100}%`,
            }"
          ></div>
        </div>
      </div>
    </div>

    <!-- Header -->
    <div class="story-header">
      <button @click="handleBack" class="back-button">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M15 19l-7-7 7-7"
          />
        </svg>
      </button>

      <div class="header-actions">
        <!-- <button class="action-button">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button> -->

        <a
          v-if="props.content?.originalArticle?.canonical_url || props.content?.canonical_url"
          :href="props.content?.originalArticle?.canonical_url || props.content?.canonical_url"
          target="_blank"
          rel="noopener noreferrer"
          class="action-button"
          aria-label="Open original article"
          @click.stop
          @touchend.stop
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
            />
          </svg>
        </a>

        <button
          class="action-button"
          :class="{ saved: isSaved }"
          @click.stop="handleSave"
          @touchend.stop.prevent="handleSave"
          aria-label="Save article"
        >
          <svg
            class="w-5 h-5"
            :fill="isSaved ? 'currentColor' : 'none'"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
            />
          </svg>
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="story-content" @click="handleContentClick">
      <!-- Layout: Text only -->
      <template v-if="currentPage.layout === 'text-only'">
        <div class="text-only-container">
          <div class="text-section-centered">
            <p
              class="story-description text-left font-spectral leading-relaxed text-gray-100 max-w-sm mx-auto"
            >
              <template
                v-if="shouldTruncateDescription(currentPage.description) && !isDescriptionExpanded"
              >
                {{ truncateText(currentPage.description, 180) }}
                <span
                  @click.stop="isDescriptionExpanded = true"
                  class="text-blue-400 font-semibold ml-1 cursor-pointer"
                  >more</span
                >
              </template>
              <template v-else>
                {{ currentPage.description }}
                <span
                  v-if="shouldTruncateDescription(currentPage.description) && isDescriptionExpanded"
                  @click.stop="isDescriptionExpanded = false"
                  class="text-blue-400 font-semibold ml-1 cursor-pointer"
                  >less</span
                >
              </template>
            </p>
          </div>
        </div>
      </template>

      <!-- Layout: Text on top, Image on bottom -->
      <template v-else-if="currentPage.layout === 'text-top'">
        <div class="text-top-container">
          <div class="text-section">
            <p class="story-description">
              <template
                v-if="shouldTruncateDescription(currentPage.description) && !isDescriptionExpanded"
              >
                {{ truncateText(currentPage.description, 180) }}
                <span
                  @click.stop="isDescriptionExpanded = true"
                  class="text-blue-400 font-semibold ml-1 cursor-pointer"
                  >more</span
                >
              </template>
              <template v-else>
                {{ currentPage.description }}
                <span
                  v-if="shouldTruncateDescription(currentPage.description) && isDescriptionExpanded"
                  @click.stop="isDescriptionExpanded = false"
                  class="text-blue-400 font-semibold ml-1 cursor-pointer"
                  >less</span
                >
              </template>
            </p>
          </div>

          <div class="image-section" :class="{ 'image-section--contain': useContainDisplay }">
            <!-- Blurred background fill for contain mode -->
            <img
              v-if="useContainDisplay"
              :src="currentPage.thumbnail"
              :alt="''"
              class="story-image-blur-bg"
              aria-hidden="true"
            />
            <img
              :src="currentPage.thumbnail"
              :alt="currentPage.title"
              class="story-image"
              :style="{
                objectFit: imageDisplayStyle.objectFit,
                objectPosition: imageDisplayStyle.objectPosition,
              }"
            />
          </div>
        </div>
      </template>

      <!-- Layout: Image on top, Text on bottom (standard) -->
      <template v-else-if="currentPage.layout === 'image-top'">
        <div class="text-top-container">
          <div class="image-section" :class="{ 'image-section--contain': useContainDisplay }">
            <img
              v-if="useContainDisplay"
              :src="currentPage.thumbnail"
              :alt="''"
              class="story-image-blur-bg"
              aria-hidden="true"
            />
            <img
              :src="currentPage.thumbnail"
              :alt="currentPage.title"
              class="story-image"
              :style="{
                objectFit: imageDisplayStyle.objectFit,
                objectPosition: imageDisplayStyle.objectPosition,
              }"
            />
          </div>
          <div class="text-section">
            <p class="story-description">
              <template
                v-if="shouldTruncateDescription(currentPage.description) && !isDescriptionExpanded"
              >
                {{ truncateText(currentPage.description, 180) }}
                <span
                  @click.stop="isDescriptionExpanded = true"
                  class="text-blue-400 font-semibold ml-1 cursor-pointer"
                  >more</span
                >
              </template>
              <template v-else>
                {{ currentPage.description }}
                <span
                  v-if="shouldTruncateDescription(currentPage.description) && isDescriptionExpanded"
                  @click.stop="isDescriptionExpanded = false"
                  class="text-blue-400 font-semibold ml-1 cursor-pointer"
                  >less</span
                >
              </template>
            </p>
          </div>
        </div>
      </template>

      <!-- Layout: Takeaways -->
      <template v-else-if="currentPage.layout === 'takeaways'">
        <div class="takeaways-container">
          <div class="takeaways-header">
            <h1 class="takeaways-title">Key Takeaways</h1>
          </div>
          <div class="takeaways-list">
            <div v-for="(item, idx) in takeawaysItems" :key="idx" class="takeaway-item">
              <div class="takeaway-bullet">•</div>
              <div class="takeaway-text">{{ item }}</div>
            </div>
          </div>

          <div class="read-full-button">
            <button @click.stop="readFullArticle" class="full-article-btn">
              Read Full Article
            </button>
          </div>
        </div>
      </template>

      <!-- Layout: Video -->
      <template v-else-if="currentPage.layout === 'video'">
        <div class="video-slide-container">
          <!-- If iframe embed code exists, render raw HTML -->
          <div
            v-if="currentPage.embedCode"
            v-html="currentPage.embedCode"
            class="video-embed-wrapper"
          ></div>
          <!-- Else if raw video url exists, render HTML5 video tag -->
          <video
            v-else-if="currentPage.videoUrl"
            :src="currentPage.videoUrl"
            autoplay
            loop
            muted
            playsinline
            class="story-video"
          ></video>
          <!-- Transparent overlay to allow tapping/clicking for navigation -->
          <div class="video-click-overlay"></div>
          <!-- Slide caption text overlaid on top -->
          <div class="video-text-overlay">
            <p class="story-description">
              <template
                v-if="shouldTruncateDescription(currentPage.description) && !isDescriptionExpanded"
              >
                {{ truncateText(currentPage.description, 180) }}
                <span
                  @click.stop="isDescriptionExpanded = true"
                  class="text-blue-400 font-semibold ml-1 cursor-pointer"
                  >more</span
                >
              </template>
              <template v-else>
                {{ currentPage.description }}
                <span
                  v-if="shouldTruncateDescription(currentPage.description) && isDescriptionExpanded"
                  @click.stop="isDescriptionExpanded = false"
                  class="text-blue-400 font-semibold ml-1 cursor-pointer"
                  >less</span
                >
              </template>
            </p>
          </div>
        </div>
      </template>

      <!-- Layout: Standard (original) -->
      <template v-else>
        <div class="content-image" :class="{ 'content-image--contain': useContainDisplay }">
          <img
            v-if="useContainDisplay"
            :src="currentPage.thumbnail"
            :alt="''"
            class="story-image-blur-bg"
            aria-hidden="true"
          />
          <img
            :src="currentPage.thumbnail"
            :alt="currentPage.title"
            class="story-image"
            :style="{
              objectFit: imageDisplayStyle.objectFit,
              objectPosition: imageDisplayStyle.objectPosition,
            }"
          />
        </div>

        <div class="content-text">
          <h1 class="story-title">{{ currentPage.title }}</h1>
          <p class="story-description">
            <template
              v-if="shouldTruncateDescription(currentPage.description) && !isDescriptionExpanded"
            >
              {{ truncateText(currentPage.description, 180) }}
              <span
                @click.stop="isDescriptionExpanded = true"
                class="text-blue-400 font-semibold ml-1 cursor-pointer"
                >more</span
              >
            </template>
            <template v-else>
              {{ currentPage.description }}
              <span
                v-if="shouldTruncateDescription(currentPage.description) && isDescriptionExpanded"
                @click.stop="isDescriptionExpanded = false"
                class="text-blue-400 font-semibold ml-1 cursor-pointer"
                >less</span
              >
            </template>
          </p>
        </div>
      </template>
    </div>

    <!-- Gradient Overlay for Bottom Controls & Text readability -->
    <div
      class="bottom-gradient-overlay"
      :class="{ tall: currentPageIndex === 0, short: currentPageIndex > 0 }"
    ></div>

    <!-- Bottom Controls -->
    <BottomControls
      :initial-listening="isListening"
      :show-category="true"
      :show-listen="true"
      :category="category"
      :article-content="props.content"
      @listen="handleListen"
      @comments="toggleComments"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import type { StoryContent } from '@/stores/content'
import BottomControls from './BottomControls.vue'
import { apiFetch } from '@/lib/api'
import { useAnalytics } from '@/composables/useAnalytics'

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
  isSaved: false,
})

const router = useRouter()

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
  const id =
    props.content?.originalArticle?._id ??
    props.content?.originalArticle?.id ??
    props.content?._id ??
    props.content?.id
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
      const res = await apiFetch(`/api/saved-articles/${encodeURIComponent(articleId)}`, {
        method: 'DELETE',
      })
      console.log('[handleSave] Unsave response:', res.status)
      if (res.ok) {
        emit('save', { id: articleId, collection, saved: false })
      }
    } else {
      console.log('[handleSave] Saving article:', articleId, 'collection:', collection)
      const res = await apiFetch('/api/saved-articles', {
        method: 'POST',
        body: JSON.stringify({ article_id: articleId, collection }),
      })
      console.log('[handleSave] Save response:', res.status)
      if (res.ok) {
        emit('save', { id: articleId, collection, saved: true })
      }
    }
  } catch (err) {
    console.error('[handleSave] Error:', err)
  }
}

const { trackScrollDepth } = useAnalytics()

const storyContainerRef = ref<HTMLElement | null>(null)
const currentPageIndex = ref(0)
const isDescriptionExpanded = ref(false)

const shouldTruncateDescription = (_text: string | null | undefined) => {
  return false
}

const truncateText = (text: string | null | undefined, limit: number = 180) => {
  if (!text) return ''
  if (text.length <= limit) return text
  return text.substring(0, limit) + '...'
}

watch(currentPageIndex, () => {
  isDescriptionExpanded.value = false
})

const isListening = ref(false)
const autoAdvanceTimer = ref<any>(null)
const isVisible = ref(false)

// Create story pages from the content data
const pages = computed(() => {
  // Ensure we have valid content data
  if (!props.content || !props.content.title) {
    return [
      {
        title: 'Story Content',
        description: 'This story contains important information.',
        thumbnail: 'https://picsum.photos/400/600?random=fallback',
        author: {
          name: 'Unknown',
          username: '@unknown',
          avatar: 'https://picsum.photos/50/50?random=fallback',
        },
        createdAt: new Date().toISOString(),
      },
    ]
  }

  // Create author info from content
  const author = {
    name: props.content.author?.name || 'Unknown Author',
    username: props.content.author?.username || '@unknown',
    avatar: props.content.author?.avatar || 'https://picsum.photos/50/50?random=author',
  }

  const createdAt =
    props.content.createdAt || props.content.publish_date || new Date().toISOString()
  const pages_data =
    props.content.originalArticle?.ai_summary?.pages?.filter(
      (page: any) => page.page_type !== 'hero',
    ) || []

  // Single-slide story (short article): render ONE full-bleed hero using the
  // AI summary's text/image instead of a hero + a redundant split-layout slide.
  const contentPagesOnly = pages_data.filter((page: any) => page.page_type === 'content')
  const overviewPagesOnly = pages_data.filter((page: any) => page.page_type === 'overview')
  if (contentPagesOnly.length === 1 && overviewPagesOnly.length === 0) {
    const only = contentPagesOnly[0]
    const textItem = only.content?.find((item: any) => item?.type === 'text')
    const imageItem = only.content?.find((item: any) => item?.type === 'image')
    const videoItem = only.content?.find((item: any) => item?.type === 'video')
    if (!videoItem) {
      return [
        {
          ...props.content,
          title: props.content.title,
          description: textItem?.content || props.content.description,
          thumbnail: imageItem?.content_url || props.content.thumbnail,
          focalPoint:
            imageItem?.focal_point ||
            props.content.originalArticle?.promo_items?.basic?.focal_point ||
            props.content.originalArticle?.imageFocalPoint ||
            null,
          author: author,
          createdAt: createdAt,
          layout: 'standard',
        },
      ]
    }
  }

  return [
    {
      ...props.content,
      title: props.content.title,
      description: props.content.description,
      thumbnail: props.content.thumbnail,
      focalPoint:
        props.content.originalArticle?.promo_items?.basic?.focal_point ||
        props.content.originalArticle?.imageFocalPoint ||
        null,
      author: author,
      createdAt: createdAt,
      layout: 'standard', // Image on top, text on bottom`
    },
    ...pages_data
      .filter((page: any) => page.page_type === 'content')
      .map((page: any, index: number) => {
        const textItem = page.content?.find((item: any) => item?.type === 'text')
        const imageItem = page.content?.find((item: any) => item?.type === 'image')
        const videoItem = page.content?.find((item: any) => item?.type === 'video')
        if (!textItem) return null

        if (videoItem) {
          return {
            title: textItem.content,
            description: textItem.content,
            videoUrl: videoItem.content_url,
            embedCode: videoItem.embed_code,
            author: author,
            createdAt: createdAt,
            layout: 'video',
          }
        }
        return {
          title: textItem.content,
          description: textItem.content,
          thumbnail: imageItem?.content_url,
          focalPoint: imageItem?.focal_point || null,
          author: author,
          createdAt: createdAt,
          layout: !imageItem?.content_url
            ? 'text-only'
            : index % 2 === 0
              ? 'text-top'
              : 'image-top',
        }
      })
      .filter(Boolean),
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
    ...pages_data
      .filter((page: any) => page.page_type === 'overview')
      .map((page: any) => {
        const textItem = page.content?.find((item: any) => item?.type === 'text')
        if (!textItem) return null
        return {
          title: 'Key Takeaways',
          description: textItem.content,
          author: author,
          createdAt: createdAt,
          layout: 'takeaways',
        }
      })
      .filter(Boolean),
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

// Analytics: track story depth as scroll_depth (page progress within a story)
watch(currentPageIndex, (newIdx) => {
  const total = pages.value.length
  if (total <= 1) return
  const depthPercent = ((newIdx + 1) / total) * 100
  const contentId = String(
    props.content?.originalArticle?._id ?? props.content?._id ?? props.content?.id ?? '',
  )
  trackScrollDepth(contentId, depthPercent, 'article', props.category)
})

const currentPage = computed(() => {
  const page = pages.value[currentPageIndex.value]
  return page
})

/**
 * Compute the image display style based on focal point data.
 * - If focal point exists with display_mode "contain": show full image letterboxed with blur fill
 * - If focal point exists with display_mode "focal_crop": use object-position to pan to subject
 * - Otherwise: default center crop (object-fit: cover, centered)
 */
const imageDisplayStyle = computed(() => {
  const fp = currentPage.value?.focalPoint
  if (!fp) {
    return { objectFit: 'cover', objectPosition: 'center center' }
  }

  if (fp.display_mode === 'contain') {
    // Extreme aspect ratio — frontend will show letterboxed with blur background
    return { objectFit: 'contain', objectPosition: 'center center', displayMode: 'contain' }
  }

  // Focal crop: pan object-position to the subject
  const x = Math.round((fp.focal_x ?? 0.5) * 100)
  const y = Math.round((fp.focal_y ?? 0.5) * 100)
  return { objectFit: 'cover', objectPosition: `${x}% ${y}%`, displayMode: 'focal_crop' }
})

/** Whether the current page image should use the "contain" display with blurred background */
const useContainDisplay = computed(() => {
  return imageDisplayStyle.value.displayMode === 'contain'
})

const takeawaysItems = computed(() => {
  const desc = currentPage.value?.description || ''
  return desc
    .split('\n')
    .map((line: string) => line.replace(/^[•\-\*\s]+/, '').trim())
    .filter(Boolean)
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

const handleBack = () => {
  emit('back')
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
  if (props.content.originalArticle?.canonical_url) {
    const articleTitle = props.content.title || props.content.headlines?.basic || 'Article'
    const encodedUrl = encodeURIComponent(props.content.originalArticle.canonical_url)
    const encodedTitle = encodeURIComponent(articleTitle)
    router.push(`/article/${encodedUrl}/${encodedTitle}`)
  } else {
    console.log('No canonical URL available')
  }
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
  const storyContainer = storyContainerRef.value
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
      rootMargin: '0px',
    },
  )

  observer.observe(storyContainer)
}

// Set --vh CSS variable for mobile viewport handling (Android address bar fix)
const setVh = () => {
  document.documentElement.style.setProperty('--vh', `${window.innerHeight}px`)
}

onMounted(() => {
  // Setup viewport height for Android
  setVh()
  window.addEventListener('resize', setVh)
  window.addEventListener('orientationchange', setVh)
  // Setup intersection observer for auto-advance
  setupIntersectionObserver()
})

onUnmounted(() => {
  // Cleanup auto-advance timer
  stopAutoAdvance()
  // Cleanup viewport listeners
  window.removeEventListener('resize', setVh)
  window.removeEventListener('orientationchange', setVh)
})
</script>

<style scoped>
.story-container {
  @apply relative inset-0 bg-black;
  @apply flex flex-col;
  @apply touch-none;
  @apply w-full;
  /* Mobile viewport handling - layered fallbacks for Android address bar */
  height: 100vh; /* Fallback for oldest browsers */
  height: calc(var(--vh, 100vh)); /* JS-calculated actual viewport height */
  height: 100dvh; /* Modern browsers with dynamic viewport support */
  /* Prevent content from extending beyond visible area */
  max-height: 100vh;
  max-height: calc(var(--vh, 100vh));
  max-height: 100dvh;
  overflow: hidden;
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
  @apply font-spectral;
}

.content-image {
  @apply absolute inset-0;
}

.story-image {
  @apply w-full h-full object-cover;
}

.content-text {
  @apply absolute bottom-0 left-0 right-0 z-10;
  @apply px-6 pt-20;
  @apply text-white;
  /* Extra bottom padding to clear the BottomControls bar */
  padding-bottom: 5rem;
  padding-bottom: calc(7rem + env(safe-area-inset-bottom, 0px));
  /* Readable copy on busy hero images without dimming the whole slide */
  background: linear-gradient(
    to top,
    rgb(0 0 0 / 0.92) 0%,
    rgb(0 0 0 / 0.55) 38%,
    transparent 100%
  );
}

/* Text-only layout styles */
.text-only-container {
  @apply flex flex-col h-full w-full justify-center bg-black;
}

.text-section-centered {
  @apply flex items-center justify-center p-8;
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
  line-height: 1.45;
  @apply text-white;
}

.image-section {
  @apply relative h-1/2 min-h-0 w-full bg-black overflow-hidden;
}

/* Soften hard crop edges: blend into black (text band / chrome) above and below */
.image-section::before,
.image-section::after {
  content: '';
  @apply pointer-events-none absolute left-0 right-0 z-[1];
  height: 32%;
}

.image-section::before {
  @apply top-0;
  background: linear-gradient(to bottom, #000 0%, rgba(0, 0, 0, 0.45) 35%, transparent 100%);
}

.image-section::after {
  @apply bottom-0;
  background: linear-gradient(to top, #000 0%, rgba(0, 0, 0, 0.45) 35%, transparent 100%);
}

.image-section .story-image {
  @apply relative z-0 w-full h-full object-cover block;
}

/* Focal point: contain mode with blurred background fill */
.image-section--contain,
.content-image--contain {
  @apply relative;
}

.story-image-blur-bg {
  @apply absolute inset-0 w-full h-full object-cover block;
  filter: blur(20px) brightness(0.4);
  transform: scale(1.1); /* Prevent blur edge artifacts */
  z-index: 0;
}

.image-section--contain .story-image,
.content-image--contain .story-image {
  @apply relative z-[1] w-full h-full block;
  /* object-fit is set inline via :style binding */
}

/* Ensure gradients still overlay in contain mode */
.image-section--contain::before,
.image-section--contain::after {
  z-index: 2;
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
  @apply font-spectral;
  @apply text-white;
}

.text-section-bottom .story-description {
  @apply text-sm leading-relaxed;
  @apply text-gray-200;
}

/* Video layout styles */
.video-slide-container {
  @apply relative w-full h-full bg-black overflow-hidden flex items-center justify-center;
}

.video-embed-wrapper {
  @apply absolute inset-0 w-full h-full flex items-center justify-center;
}

.video-embed-wrapper :deep(iframe),
.video-embed-wrapper :deep(video) {
  @apply absolute inset-0 w-full h-full border-0 object-cover;
}

.story-video {
  @apply absolute inset-0 w-full h-full object-cover block;
}

.video-click-overlay {
  @apply absolute inset-0 z-[5];
}

.video-text-overlay {
  @apply absolute bottom-0 left-0 right-0 z-10;
  @apply px-6 pt-20;
  @apply text-white;
  /* Extra bottom padding to clear the BottomControls bar */
  padding-bottom: 5rem;
  padding-bottom: calc(7rem + env(safe-area-inset-bottom, 0px));
  background: linear-gradient(
    to top,
    rgb(0 0 0 / 0.92) 0%,
    rgb(0 0 0 / 0.55) 38%,
    transparent 100%
  );
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
  @apply font-bold;
  @apply font-spectral;
  @apply text-white;
}

.takeaways-list {
  @apply flex-1 space-y-4;
}

.takeaway-item {
  @apply flex items-start space-x-3;
}

.takeaway-bullet {
  @apply text-white font-bold;
  @apply flex-shrink-0;
  @apply mt-1;
}

.takeaway-text {
  @apply text-white leading-relaxed;
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
  @apply text-2xl font-bold mb-2;
  @apply font-spectral;
  @apply text-white;
}

.story-description {
  line-height: 1.45;
  @apply text-gray-300;
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

.bottom-gradient-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  pointer-events: none;
  z-index: 5;
  transition: height 0.3s ease;
}

.bottom-gradient-overlay.tall {
  height: 40%;
  background: linear-gradient(
    to top,
    rgba(0, 0, 0, 0.98) 0%,
    rgba(0, 0, 0, 0.88) 35%,
    rgba(0, 0, 0, 0.5) 70%,
    transparent 100%
  );
}

.bottom-gradient-overlay.short {
  height: 120px;
  background: linear-gradient(
    to top,
    rgba(0, 0, 0, 0.95) 0%,
    rgba(0, 0, 0, 0.6) 50%,
    transparent 100%
  );
}
</style>
