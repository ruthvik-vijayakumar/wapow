<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useContentStore } from '@/stores/videos'
import TopBar from '@/components/TopBar.vue'
import CategoryNavigation from '@/components/CategoryNavigation.vue'
import ContentTile from '@/components/ContentTile.vue'
import BottomNavigation from '@/components/BottomNavigation.vue'
import VueMasonryWall from '@yeger/vue-masonry-wall'
import type { Article } from '@/stores/videos'
import { onMounted, ref } from 'vue'

import { useRoute } from 'vue-router'

const route = useRoute()

const router = useRouter()
const contentStore = useContentStore()
const isLoading = ref(false)

// Swipe functionality
const touchStartX = ref(0)
const touchEndX = ref(0)
const currentCategoryIndex = ref(0)
const isAnimating = ref(false)
const slideDirection = ref<'left' | 'right' | null>(null)

const categories = [
  '/sports',
  '/style',
  // '/recipes',
  '/technology',
  '/wellbeing',
  '/travel',
  // '/podcasts'
]

const handleSearch = () => {
  console.log('Search clicked')
  // TODO: Implement search functionality
}

const handleMenu = () => {
  console.log('Menu clicked')
  // TODO: Implement menu functionality
}

const handleCategoryChange = async (categoryId: string) => {
  console.log('Category changed:', categoryId)
  currentCategoryIndex.value = categories.indexOf(categoryId)
  await loadCategoryData(categoryId)
}

// Watch for route changes to sync with CategoryNavigation
const handleRouteChange = async () => {
  const currentPath = router.currentRoute.value.path
  const categoryIndex = categories.findIndex(cat => cat === currentPath)
  if (categoryIndex !== -1 && categoryIndex !== currentCategoryIndex.value) {
    currentCategoryIndex.value = categoryIndex
    await loadCategoryData(categories[categoryIndex])
  }
}

const handleSwipe = async (direction: 'left' | 'right') => {
  if (isAnimating.value) return // Prevent multiple swipes during animation

  if (direction === 'left' && currentCategoryIndex.value < categories.length - 1) {
    // Swipe left - go to next category
    slideDirection.value = 'left'
    isAnimating.value = true
    currentCategoryIndex.value++
    const nextCategory = categories[currentCategoryIndex.value]
    await handleCategoryChange(nextCategory)
    setTimeout(() => {
      slideDirection.value = null
      isAnimating.value = false
    }, 300)
  } else if (direction === 'right' && currentCategoryIndex.value > 0) {
    // Swipe right - go to previous category
    slideDirection.value = 'right'
    isAnimating.value = true
    currentCategoryIndex.value--
    const prevCategory = categories[currentCategoryIndex.value]
    await handleCategoryChange(prevCategory)
    setTimeout(() => {
      slideDirection.value = null
      isAnimating.value = false
    }, 300)
  }
}

const handleTouchStart = (event: TouchEvent) => {
  if (isAnimating.value) return
  touchStartX.value = event.touches[0].clientX
}

const handleTouchEnd = (event: TouchEvent) => {
  if (isAnimating.value) return
  touchEndX.value = event.changedTouches[0].clientX
  const swipeThreshold = 50 // Minimum distance for a swipe

  const swipeDistance = touchEndX.value - touchStartX.value

  if (Math.abs(swipeDistance) > swipeThreshold) {
    if (swipeDistance > 0) {
      // Swipe right
      handleSwipe('right')
    } else {
      // Swipe left
      handleSwipe('left')
    }
  }
}

const loadCategoryData = async (categoryId: string) => {
  try {
    isLoading.value = true
    await contentStore.loadArticles(categoryId)
  } catch (error) {
    console.error('Error loading category data:', error)
  } finally {
    isLoading.value = false
  }
}

const handleContentClick = (content: Article) => {
  const cat = route.path.split('/')[1]
  // console.log('Content clicked:', content.headlines?.basic)
  // const category = getCategoryFromContent(content)
  router.push(`/story/${content._id}/${cat}`)
}



const handleNavigation = (route: string) => {
  console.log('Navigation:', route)

  switch (route) {
    case 'home':
      // Already on home page
      break
    case 'ask-ai':
      // TODO: Navigate to AI chat page
      console.log('Navigate to Ask AI')
      break
    case 'games':
      // TODO: Navigate to games page
      console.log('Navigate to Games')
      break
    case 'profile':
      router.push('/profile')
      break
    default:
      console.log('Unknown route:', route)
  }
}

const getCategoryFromContent = (content: Article): string => {
  // Use section from taxonomy or fallback to type
  return content.taxonomy?.primary_section?.name ||
         content.taxonomy?.sections?.[0]?.name ||
         content.type ||
         'News'
}

const getWapoData = async () => {
  try {
    isLoading.value = true
    // Get current route or default to sports
    const currentPath = router.currentRoute.value.path
    const defaultCategory = categories.includes(currentPath) ? currentPath : '/sports'
    await contentStore.loadArticles(defaultCategory)
  } catch (error) {
    console.error('Error loading initial data:', error)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  getWapoData()
  // Watch for route changes
  router.afterEach(handleRouteChange)
})
</script>

<template>
  <div
    class="home-container"
    @touchstart="handleTouchStart"
    @touchend="handleTouchEnd"
  >
    <!-- Top Bar -->
    <TopBar @search="handleSearch" @menu="handleMenu" />

    <!-- Category Navigation -->
    <CategoryNavigation />

    <!-- Main Content -->
    <div class="content-area">
      <!-- Loading state -->
        <div v-if="isLoading || contentStore.isLoading" class="flex justify-center items-center py-20">
        <div class="loading-spinner">
          <div class="animate-spin rounded-full h-12 w-12 spinner-ring"></div>
          <p class="mt-4 spinner-text text-sm">Loading articles...</p>
        </div>
      </div>

      <!-- Content Grid with Animation -->
      <div v-else class="content-wrapper">
        <div class="content-inner">
          <div
            class="content-grid"
            :class="{
              'slide-left': slideDirection === 'left',
              'slide-right': slideDirection === 'right',
              'swipe-hint': !isAnimating && !isLoading,
              'slide-up': !isAnimating && !isLoading && contentStore.articles.length > 0
            }"
          >
            <VueMasonryWall
              :items="contentStore.articles"
              :ssr-columns="2"
              :column-width="150"
              :gap="16"
              :padding="8"
            >
              <template #default="{ item, index }">
                <ContentTile :content="item" :index="index" @click="handleContentClick" />
              </template>
            </VueMasonryWall>
          </div>
        </div>

        <!-- Swipe Indicators -->
        <div class="swipe-indicators">
          <div
            v-if="currentCategoryIndex > 0"
            class="swipe-indicator left"
            :class="{ 'pulse': slideDirection === 'right' }"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
          </div>
          <div
            v-if="currentCategoryIndex < categories.length - 1"
            class="swipe-indicator right"
            :class="{ 'pulse': slideDirection === 'left' }"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Navigation -->
    <BottomNavigation @navigate="handleNavigation" />
  </div>
</template>

<style scoped>
.home-container {
  @apply min-h-screen;
  @apply flex flex-col;
  height: 100vh;
  touch-action: pan-y;
  background-color: var(--bg-primary);
  transition: background-color 0.3s ease;
}

.spinner-ring {
  border-bottom: 2px solid var(--spinner-accent);
}

.spinner-text {
  color: var(--text-secondary);
}

.content-area {
  @apply flex-1;
  @apply pb-20;
  height: calc(100vh - 120px);
  overflow-y: scroll;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  scrollbar-color: transparent transparent;
}

.content-area::-webkit-scrollbar {
  width: 7px;
  background: transparent;
}

.content-area::-webkit-scrollbar-thumb {
  background-color: var(--scrollbar-thumb);
  border-radius: 10px;
}

.content-wrapper {
  @apply relative py-2;
  width: 100%;
  box-sizing: border-box;
  padding-left: 1rem;
  padding-right: 1rem;
}

.content-inner {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  /* Ensure inner content uses full available width */
  margin: 0;
  padding: 0;
}

.content-grid {
  @apply transition-all duration-300 ease-in-out;
  @apply transform;
}

.slide-left {
  @apply translate-x-4 opacity-50;
  animation: slideInLeft 0.3s ease-out;
}

.slide-right {
  @apply -translate-x-4 opacity-50;
  animation: slideInRight 0.3s ease-out;
}

.slide-up {
  animation: slideUpFromBottom 0.6s ease-out;
}

.swipe-indicators {
  @apply fixed top-1/2 transform -translate-y-1/2;
  @apply pointer-events-none;
  @apply z-10;
  @apply w-full;
  @apply flex justify-between;
  @apply px-4;
}

.swipe-indicator {
  @apply w-12 h-12;
  @apply rounded-full;
  @apply flex items-center justify-center;
  @apply transition-all duration-200;
  @apply opacity-0;
  background-color: rgba(0, 0, 0, 0.5);
  color: #ffffff;
}

.swipe-indicator.left {
  @apply left-4;
}

.swipe-indicator.right {
  @apply right-4;
}

.swipe-indicator.pulse {
  @apply opacity-100;
  animation: pulse 0.6s ease-in-out;
}

.loading-spinner {
  @apply flex flex-col items-center;
}

@keyframes slideInLeft {
  0% {
    transform: translateX(100%);
    opacity: 0;
  }
  100% {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slideInRight {
  0% {
    transform: translateX(-100%);
    opacity: 0;
  }
  100% {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slideUpFromBottom {
  0% {
    transform: translateY(100%);
    opacity: 0;
  }
  50% {
    opacity: 0.5;
  }
  100% {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes subtleBounce {
  0%, 100% {
    transform: translateX(0);
  }
  50% {
    transform: translateX(2px);
  }
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 0.5;
  }
  50% {
    transform: scale(1.1);
    opacity: 1;
  }
  100% {
    transform: scale(1);
    opacity: 0.5;
  }
}
</style>
