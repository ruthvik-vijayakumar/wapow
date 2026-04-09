<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useContentStore } from '@/stores/content'
import TopBar from '@/components/TopBar.vue'
import CategoryNavigation from '@/components/CategoryNavigation.vue'
import ContentTile from '@/components/ContentTile.vue'
import BottomNavigation from '@/components/BottomNavigation.vue'
import DesktopSidebar from '@/components/DesktopSidebar.vue'
import DesktopTopHeader from '@/components/DesktopTopHeader.vue'
import VueMasonryWall from '@yeger/vue-masonry-wall'
import type { Article } from '@/stores/content'
import { computed, onMounted, onUnmounted, ref } from 'vue'

import { useRoute } from 'vue-router'

const route = useRoute()

const router = useRouter()
const contentStore = useContentStore()
const isLoading = ref(false)

// Desktop breakpoint handling (keep template logic simple)
const isDesktop = ref(false)
let mq: MediaQueryList | null = null
const onMqChange = (e: MediaQueryListEvent) => {
  isDesktop.value = e.matches
}

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

const handleDesktopSearch = (query: string) => {
  router.push({ path: '/search', query: query ? { q: query } : undefined })
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
  if (isDesktop.value) return
  if (isAnimating.value) return
  touchStartX.value = event.touches[0].clientX
}

const handleTouchEnd = (event: TouchEvent) => {
  if (isDesktop.value) return
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
    case 'search':
      router.push('/search')
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

const masonryConfig = computed(() => {
  if (isDesktop.value) {
    return {
      ssrColumns: 5,
      columnWidth: 240,
      gap: 18,
      padding: 12
    }
  }
  return {
    ssrColumns: 2,
    columnWidth: 150,
    gap: 16,
    padding: 8
  }
})

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
  mq = window.matchMedia('(min-width: 1024px)')
  isDesktop.value = mq.matches
  mq.addEventListener('change', onMqChange)

  getWapoData()
  // Watch for route changes
  router.afterEach(handleRouteChange)
})

onUnmounted(() => {
  if (mq) mq.removeEventListener('change', onMqChange)
})
</script>

<template>
  <div class="home-shell" @touchstart="handleTouchStart" @touchend="handleTouchEnd">
    <!-- Desktop layout -->
    <div class="desktop-layout" v-show="isDesktop">
      <DesktopSidebar @navigate="handleNavigation" />

      <div class="desktop-main">
        <DesktopTopHeader @search="handleDesktopSearch" />
        <div class="desktop-categories">
          <CategoryNavigation />
        </div>

        <div class="desktop-content">
          <!-- Skeleton loading state -->
          <div v-show="isLoading || contentStore.isLoading" class="skeleton-grid desktop">
            <div v-for="n in 12" :key="n" class="skeleton-tile">
              <div class="skeleton-tile-image skeleton-pulse"></div>
              <div class="skeleton-tile-body">
                <div class="skeleton-line skeleton-pulse" style="width: 90%; height: 0.75rem;"></div>
                <div class="skeleton-line skeleton-pulse" style="width: 55%; height: 0.625rem; margin-top: 0.5rem;"></div>
              </div>
            </div>
          </div>

          <!-- Content grid -->
          <div v-show="!isLoading && !contentStore.isLoading" class="content-wrapper desktop">
            <div class="content-inner">
              <div class="content-grid">
                <VueMasonryWall
                  :items="contentStore.articles"
                  :ssr-columns="masonryConfig.ssrColumns"
                  :column-width="masonryConfig.columnWidth"
                  :gap="masonryConfig.gap"
                  :padding="masonryConfig.padding"
                >
                  <template #default="{ item, index }">
                    <ContentTile :content="item" :index="index" @click="handleContentClick" />
                  </template>
                </VueMasonryWall>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Mobile layout (existing) -->
    <div class="mobile-layout" v-show="!isDesktop">
      <TopBar @search="handleSearch" @menu="handleMenu" />
      <CategoryNavigation />

      <div class="content-area">
        <!-- Skeleton loading state -->
        <div v-show="isLoading || contentStore.isLoading" class="skeleton-grid">
          <div v-for="n in 8" :key="n" class="skeleton-tile">
            <div class="skeleton-tile-image skeleton-pulse"></div>
            <div class="skeleton-tile-body">
              <div class="skeleton-line skeleton-pulse" style="width: 90%; height: 0.75rem;"></div>
              <div class="skeleton-line skeleton-pulse" style="width: 55%; height: 0.625rem; margin-top: 0.5rem;"></div>
            </div>
          </div>
        </div>

        <!-- Content Grid with Animation -->
        <div v-show="!isLoading && !contentStore.isLoading" class="content-wrapper">
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
                :ssr-columns="masonryConfig.ssrColumns"
                :column-width="masonryConfig.columnWidth"
                :gap="masonryConfig.gap"
                :padding="masonryConfig.padding"
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

      <BottomNavigation @navigate="handleNavigation" />
    </div>
  </div>
</template>

<style scoped>
.home-shell {
  @apply min-h-screen;
  height: 100vh;
  touch-action: pan-y;
  background-color: var(--bg-primary);
  transition: background-color 0.3s ease;
}

.desktop-layout {
  display: none;
}

.mobile-layout {
  @apply flex flex-col;
  height: 100vh;
}

@media (min-width: 1024px) {
  .desktop-layout {
    display: flex;
    height: 100vh;
  }
  .mobile-layout {
    display: none;
  }
}

.desktop-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.desktop-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 1rem 1.5rem 2rem;
}

.desktop-categories {
  padding: 0.25rem 1rem 0.4rem;
}

.desktop-categories :deep(.cat-nav-container) {
  background: transparent;
}

.skeleton-grid.desktop {
  grid-template-columns: repeat(5, minmax(0, 1fr));
  padding: 1.25rem;
}

.content-wrapper.desktop {
  padding-left: 1.25rem;
  padding-right: 1.25rem;
}

/* Skeleton grid */
.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  padding: 1rem;
}

.skeleton-tile {
  border-radius: 0.5rem;
  overflow: hidden;
  background: var(--bg-elevated);
}

.skeleton-tile-image {
  width: 100%;
  aspect-ratio: 9 / 16;
  background: var(--bg-tertiary);
}

.skeleton-tile-body {
  padding: 0.625rem;
}

.skeleton-line {
  border-radius: 0.25rem;
}

.skeleton-pulse {
  background: var(--bg-tertiary);
  position: relative;
  overflow: hidden;
}

.skeleton-pulse::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent 0%, var(--bg-hover) 50%, transparent 100%);
  animation: shimmer 1.4s ease-in-out infinite;
}

@keyframes shimmer {
  0%   { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
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
  animation: slideUpFromBottom 0.1s ease-out;
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
    transform: translateY(20px);
    opacity: 0;
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
