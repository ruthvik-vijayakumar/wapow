<template>
  <div class="topics-shell" :class="{ 'has-sidebar': isDesktop }">
    <!-- Desktop Layout Sidebar -->
    <DesktopSidebar v-if="isDesktop" @navigate="handleNavigation" />

    <!-- Main Content Wrapper -->
    <div class="main-wrapper">
      <!-- Desktop Header -->
      <DesktopTopHeader v-if="isDesktop" @search="handleDesktopSearch">
        <template #left>
          <div class="desktop-header-title-container">
            <h1 class="desktop-view-title font-postoni font-bold">Discover Topics</h1>
          </div>
        </template>
      </DesktopTopHeader>

      <!-- Mobile Top Bar -->
      <TopBar v-else @search="handleSearch" @menu="handleMenu" />

      <!-- Scrollable Content Area -->
      <div class="scroll-container" ref="scrollContainer">
        <div class="content-container">
          <h1 v-if="!isDesktop" class="mobile-view-title font-postoni font-bold">Discover Topics</h1>
          <p class="section-subtitle font-franklin">Explore publications and feeds curated by topic or collection.</p>

          <!-- Topics Grid Section -->
          <section class="section-container">
            <h2 class="section-heading font-postoni font-bold">Explore by Topic</h2>
            <div class="topics-grid">
              <div
                v-for="topic in topics"
                :key="topic.topicId"
                class="topic-card"
                :style="{ background: getTopicGradient(topic.topicId) }"
                @click="openFeedDetails(topic.topFeedInfo)"
              >
                <!-- Visual Background Image -->
                <img
                  v-if="topic.visual"
                  :src="topic.visual"
                  :alt="topic.topicName"
                  class="topic-card-bg"
                  @error="handleCardImageError"
                />
                
                <!-- Card Glassmorphic Overlay -->
                <div class="topic-card-overlay">
                  <div class="topic-card-info">
                    <span class="topic-tag-pill font-franklin">#{{ topic.topicId }}</span>
                    <h3 class="topic-name font-postoni font-bold">{{ capitalize(topic.topicName) }}</h3>
                    <p class="topic-top-pub font-franklin">
                      Top: {{ topic.topFeedInfo.title }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <!-- Curated Collections Section -->
          <section class="section-container border-t border-[var(--border-primary)] pt-8 mt-4">
            <div class="curated-header-wrapper">
              <h2 class="section-heading font-postoni font-bold">Curated Collections</h2>
              <div class="curated-by-badge font-franklin">
                By <span>{{ curatedCover.fullName || 'Leo Industries' }}</span>
              </div>
            </div>

            <div v-for="collection in collections" :key="collection.id" class="collection-block">
              <h3 class="collection-title font-postoni font-bold">{{ collection.label }}</h3>
              <div class="feeds-grid">
                <div
                  v-for="feed in collection.feeds"
                  :key="feed.id"
                  class="feed-card"
                  @click="openFeedDetails(feed)"
                >
                  <!-- Feed Card Header/Icon -->
                  <div class="feed-card-left">
                    <div class="feed-icon-wrapper">
                      <img
                        v-if="feed.iconUrl || feed.visualUrl"
                        :src="feed.iconUrl || feed.visualUrl"
                        :alt="feed.title"
                        class="feed-icon-img"
                        @error="handleFeedIconError"
                      />
                      <div class="feed-icon-fallback font-postoni" style="display: none;">
                        {{ getLetterAvatar(feed.title) }}
                      </div>
                    </div>
                  </div>

                  <!-- Feed Content -->
                  <div class="feed-card-body">
                    <h4 class="feed-title font-postoni font-bold">{{ feed.title }}</h4>
                    <p class="feed-desc font-franklin">{{ feed.description || 'No description available.' }}</p>
                    <div class="feed-meta font-franklin">
                      <span v-if="feed.subscribers" class="feed-meta-item">
                        {{ formatSubscribers(feed.subscribers) }} subs
                      </span>
                      <span v-if="feed.velocity" class="feed-meta-item">
                        {{ formatVelocityShort(feed.velocity) }}/wk
                      </span>
                    </div>
                  </div>

                  <!-- Arrow Icon -->
                  <div class="feed-card-arrow">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>

    <!-- Mobile Drawer Settings -->
    <NavigationDrawer v-if="!isDesktop" :isOpen="isDrawerOpen" @close="isDrawerOpen = false" />

    <!-- Beautiful Glassmorphic Details Modal -->
    <transition name="fade">
      <div v-if="selectedFeed" class="modal-backdrop" @click="closeFeedDetails">
        <div class="modal-content" @click.stop>
          <!-- Header -->
          <div class="modal-header">
            <h3 class="modal-title font-postoni font-bold">Feed Information</h3>
            <button class="modal-close-btn" @click="closeFeedDetails" aria-label="Close details">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Body -->
          <div class="modal-body scrollbar-hide">
            <div class="modal-feed-hero">
              <div class="modal-avatar-wrapper">
                <img
                  v-if="selectedFeed.logo || selectedFeed.iconUrl || selectedFeed.visualUrl"
                  :src="selectedFeed.logo || selectedFeed.iconUrl || selectedFeed.visualUrl"
                  :alt="selectedFeed.title"
                  class="modal-avatar-img"
                  @error="handleModalImageError"
                />
                <div class="modal-avatar-fallback font-postoni" style="display: none;">
                  {{ getLetterAvatar(selectedFeed.title) }}
                </div>
              </div>
              <h2 class="modal-feed-title font-postoni font-bold">{{ selectedFeed.title }}</h2>
              <span v-if="selectedFeed.language" class="language-badge font-franklin">
                {{ selectedFeed.language.toUpperCase() }}
              </span>
            </div>

            <p class="modal-feed-desc font-franklin">
              {{ selectedFeed.description || 'No description provided for this feed publication.' }}
            </p>

            <!-- Metrics stats grid -->
            <div class="modal-stats-grid">
              <div class="stat-card">
                <span class="stat-label font-franklin">Subscribers</span>
                <span class="stat-val font-postoni font-bold">{{ formatSubscribers(selectedFeed.subscribers || 0) }}</span>
              </div>
              <div class="stat-card">
                <span class="stat-label font-franklin">Posting Velocity</span>
                <span class="stat-val font-postoni font-bold">{{ formatVelocity(selectedFeed.velocity || 0) }}</span>
              </div>
            </div>

            <!-- Detailed stats/IDs -->
            <div class="modal-detail-list font-franklin">
              <div v-if="selectedFeed.website" class="detail-row">
                <span class="detail-label">Website</span>
                <a :href="selectedFeed.website" target="_blank" rel="noopener" class="detail-val link">
                  {{ cleanUrl(selectedFeed.website) }}
                  <svg class="w-3.5 h-3.5 inline ml-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              </div>
              <div v-if="selectedFeed.topics && selectedFeed.topics.length" class="detail-row">
                <span class="detail-label">Topics</span>
                <div class="detail-val tags-wrapper">
                  <span v-for="tag in selectedFeed.topics" :key="tag" class="modal-tag">
                    #{{ tag }}
                  </span>
                </div>
              </div>
              <div class="detail-row">
                <span class="detail-label">Feed ID</span>
                <span class="detail-val code-text">{{ selectedFeed.id }}</span>
              </div>
            </div>
          </div>

          <!-- Footer Actions -->
          <div class="modal-footer font-franklin">
            <button
              v-if="selectedFeed.website"
              class="btn-primary"
              @click="visitWebsite(selectedFeed.website)"
            >
              Visit Website
            </button>
            <button class="btn-secondary" @click="copyFeedId(selectedFeed.id)">
              {{ isCopied ? 'Copied!' : 'Copy Feed ID' }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import TopBar from '@/components/TopBar.vue'
import NavigationDrawer from '@/components/NavigationDrawer.vue'
import DesktopSidebar from '@/components/DesktopSidebar.vue'
import DesktopTopHeader from '@/components/DesktopTopHeader.vue'

// Import pre-packaged static data file
import topicsData from '@/data/topics.json'

interface FeedInfo {
  id: string
  title: string
  description?: string
  website?: string
  subscribers?: number
  velocity?: number
  iconUrl?: string
  visualUrl?: string
  coverUrl?: string
  logo?: string
  language?: string
  topics?: string[]
}

interface Topic {
  topicName: string
  topicId: string
  visual?: string
  updated?: number
  topFeedInfo: FeedInfo
}

interface Collection {
  label: string
  id: string
  feeds: FeedInfo[]
}

// Extract topics and collections
const topics = ref<Topic[]>(topicsData.topics as Topic[])
const curatedCover = ref(topicsData.cover || { alias: 'leoIndustries', fullName: 'Leo Industries' })
const collections = ref<Collection[]>(topicsData.collections as Collection[])

const router = useRouter()
const isDrawerOpen = ref(false)
const isDesktop = ref(false)
let mq: MediaQueryList | null = null

// Selected Feed Modal state
const selectedFeed = ref<FeedInfo | null>(null)
const isCopied = ref(false)
const scrollContainer = ref<HTMLElement | null>(null)

// Desktop breakpoint listener
const onMqChange = (e: MediaQueryListEvent) => {
  isDesktop.value = e.matches
}

onMounted(() => {
  mq = window.matchMedia('(min-width: 1024px)')
  isDesktop.value = mq.matches
  mq.addEventListener('change', onMqChange)
})

onUnmounted(() => {
  if (mq) mq.removeEventListener('change', onMqChange)
})

// Mobile drawer triggers
const handleMenu = () => {
  isDrawerOpen.value = true
}

const handleSearch = () => {
  router.push('/search')
}

// Desktop Sidebar and Header handlers
const handleNavigation = (route: string) => {
  switch (route) {
    case 'home':
      router.push('/sports')
      break
    case 'search':
      router.push('/search')
      break
    case 'ask-ai':
      router.push({ path: '/search', query: { tab: 'chat' } })
      break
    case 'games':
      console.log('Navigate to Games')
      break
    case 'profile':
      router.push('/profile')
      break
    default:
      console.log('Unknown route:', route)
  }
}

const handleDesktopSearch = (query: string) => {
  router.push({ path: '/search', query: query ? { q: query } : undefined })
}

// Modal open/close actions
const openFeedDetails = (feed: FeedInfo) => {
  selectedFeed.value = feed
  isCopied.value = false
}

const closeFeedDetails = () => {
  selectedFeed.value = null
}

const copyFeedId = async (id: string) => {
  try {
    await navigator.clipboard.writeText(id)
    isCopied.value = true
    setTimeout(() => {
      isCopied.value = false
    }, 2000)
  } catch (err) {
    console.error('Failed to copy feed ID:', err)
  }
}

const visitWebsite = (url: string) => {
  window.open(url, '_blank', 'noopener,noreferrer')
}

// Formatting helpers
const capitalize = (str: string) => {
  if (!str) return ''
  return str.split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
}

const cleanUrl = (url: string) => {
  if (!url) return ''
  return url.replace(/https?:\/\/(www\.)?/, '').replace(/\/$/, '')
}

const getLetterAvatar = (title: string) => {
  if (!title) return 'F'
  return title.trim().charAt(0).toUpperCase()
}

const formatSubscribers = (count: number) => {
  if (!count) return '0'
  if (count >= 1000000) return (count / 1000000).toFixed(1).replace(/\.0$/, '') + 'M'
  if (count >= 1000) return (count / 1000).toFixed(0) + 'K'
  return count.toString()
}

const formatVelocity = (vel: number) => {
  if (!vel) return '0 articles/week'
  return `${vel.toFixed(1)} articles/week`
}

const formatVelocityShort = (vel: number) => {
  if (!vel) return '0'
  return vel.toFixed(1).replace(/\.0$/, '')
}

// Fallback visual mapping for the 26 topics (HSL gradient meshes)
const getTopicGradient = (topicId: string) => {
  const gradientMap: Record<string, string> = {
    tech: 'linear-gradient(135deg, #1e3a8a, #3b82f6)',
    security: 'linear-gradient(135deg, #1f2937, #4b5563)',
    marketing: 'linear-gradient(135deg, #7c2d12, #ea580c)',
    business: 'linear-gradient(135deg, #064e3b, #10b981)',
    design: 'linear-gradient(135deg, #701a75, #d946ef)',
    politics: 'linear-gradient(135deg, #581c87, #8b5cf6)',
    science: 'linear-gradient(135deg, #0f172a, #0284c7)',
    comics: 'linear-gradient(135deg, #78350f, #eab308)',
    entrepreneurship: 'linear-gradient(135deg, #0369a1, #0ea5e9)',
    leadership: 'linear-gradient(135deg, #1e1b4b, #4f46e5)',
    economics: 'linear-gradient(135deg, #065f46, #34d399)',
    programming: 'linear-gradient(135deg, #0f172a, #2563eb)',
    seo: 'linear-gradient(135deg, #4c1d95, #a78bfa)',
    management: 'linear-gradient(135deg, #374151, #9ca3af)',
    photography: 'linear-gradient(135deg, #831843, #f43f5e)',
    'data science': 'linear-gradient(135deg, #1e293b, #06b6d4)',
    writing: 'linear-gradient(135deg, #451a03, #b45309)',
    creativity: 'linear-gradient(135deg, #4a044e, #ec4899)',
    'content marketing': 'linear-gradient(135deg, #7c2d12, #f97316)',
    gaming: 'linear-gradient(135deg, #991b1b, #ef4444)',
    food: 'linear-gradient(135deg, #065f46, #10b981)',
    travel: 'linear-gradient(135deg, #0f766e, #14b8a6)',
    music: 'linear-gradient(135deg, #1e3a8a, #8b5cf6)',
    culture: 'linear-gradient(135deg, #1e1b4b, #ec4899)',
    crafts: 'linear-gradient(135deg, #78350f, #f59e0b)',
    relationships: 'linear-gradient(135deg, #831843, #ec4899)'
  }

  return gradientMap[topicId.toLowerCase()] || 'linear-gradient(135deg, #374151, #4b5563)'
}

// Fallback triggers for failed images (GCP buckets offline)
const handleCardImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.opacity = '0' // Fade out the broken image to reveal the fallback CSS gradient below
}

const handleFeedIconError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
  const fallback = img.nextElementSibling as HTMLElement
  if (fallback) fallback.style.display = 'flex'
}

const handleModalImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
  const fallback = img.nextElementSibling as HTMLElement
  if (fallback) fallback.style.display = 'flex'
}
</script>

<style scoped>
.topics-shell {
  display: flex;
  min-height: 100vh;
  min-height: 100dvh;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  transition: background-color 0.3s ease, color 0.3s ease;
}

.main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
}

.scroll-container {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
}

.content-container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem 1rem 3rem;
}

.desktop-header-title-container {
  display: flex;
  align-items: center;
}

.desktop-view-title {
  font-size: 1.25rem;
  color: var(--text-primary);
}

.mobile-view-title {
  font-size: 1.75rem;
  line-height: 1.2;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.section-subtitle {
  font-size: 0.925rem;
  color: var(--text-secondary);
  margin-bottom: 1.75rem;
  padding: 0 0.125rem;
}

.section-container {
  margin-bottom: 2rem;
}

.section-heading {
  font-size: 1.35rem;
  color: var(--text-primary);
  margin-bottom: 1.25rem;
}

/* Topics Grid */
.topics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.875rem;
}

.topic-card {
  position: relative;
  height: 110px;
  border-radius: 0.75rem;
  overflow: hidden;
  cursor: pointer;
  border: 1px solid var(--border-primary);
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.25s ease, border-color 0.25s ease;
}

.topic-card-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.65;
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.topic-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
  border-color: var(--accent);
}

.topic-card:hover .topic-card-bg {
  transform: scale(1.05);
  opacity: 0.8;
}

.topic-card-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.85) 0%, rgba(0, 0, 0, 0.3) 60%, rgba(0, 0, 0, 0.15) 100%);
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 0.75rem;
}

.topic-card-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  color: #ffffff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  width: 100%;
}

.topic-tag-pill {
  font-size: 0.65rem;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(4px);
  padding: 0.125rem 0.375rem;
  border-radius: 999px;
  margin-bottom: 0.25rem;
  text-transform: lowercase;
}

.topic-name {
  font-size: 0.95rem;
  font-weight: bold;
  line-height: 1.2;
}

.topic-top-pub {
  font-size: 0.7rem;
  opacity: 0.85;
  margin-top: 0.125rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
}

/* Curated Collections */
.curated-header-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 1.5rem;
}

.curated-by-badge {
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  align-self: flex-start;
}

.curated-by-badge span {
  font-weight: bold;
  color: var(--accent-text);
}

.collection-block {
  margin-bottom: 2rem;
}

.collection-title {
  font-size: 1.15rem;
  color: var(--text-primary);
  margin-bottom: 1rem;
  padding-bottom: 0.25rem;
  border-bottom: 1px solid var(--border-primary);
}

/* Feeds list under Curated */
.feeds-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.75rem;
}

.feed-card {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 0.875rem;
  background: var(--bg-elevated);
  border: 1px solid var(--border-primary);
  border-radius: 0.75rem;
  cursor: pointer;
  transition: transform 0.2s ease, border-color 0.2s ease, background-color 0.2s ease;
}

.feed-card:hover {
  transform: translateY(-2px);
  border-color: var(--accent);
  background-color: var(--bg-hover);
}

.feed-card-left {
  flex-shrink: 0;
}

.feed-icon-wrapper {
  width: 44px;
  height: 44px;
  border-radius: 0.5rem;
  overflow: hidden;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.feed-icon-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.feed-icon-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  font-weight: bold;
  background: linear-gradient(135deg, var(--border-secondary), var(--bg-tertiary));
  color: var(--text-secondary);
}

.feed-card-body {
  flex: 1;
  min-width: 0;
}

.feed-title {
  font-size: 0.95rem;
  font-weight: bold;
  color: var(--text-primary);
  line-height: 1.3;
}

.feed-desc {
  font-size: 0.75rem;
  color: var(--text-secondary);
  line-height: 1.4;
  margin-top: 0.125rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.feed-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 0.375rem;
}

.feed-meta-item {
  font-size: 0.65rem;
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
  padding: 0.0625rem 0.375rem;
  border-radius: 4px;
}

.feed-card-arrow {
  flex-shrink: 0;
  color: var(--text-tertiary);
  opacity: 0.5;
  transition: opacity 0.2s, transform 0.2s;
}

.feed-card:hover .feed-card-arrow {
  opacity: 1;
  transform: translateX(2px);
}

/* Modal styling */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(8px);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.modal-content {
  background: var(--bg-elevated);
  border: 1px solid var(--border-primary);
  border-radius: 1rem;
  width: 100%;
  max-width: 480px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 10px 10px -5px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  animation: modalSlideUp 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes modalSlideUp {
  from {
    transform: translateY(30px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border-primary);
}

.modal-title {
  font-size: 1.1rem;
  color: var(--text-primary);
}

.modal-close-btn {
  color: var(--text-secondary);
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 50%;
  transition: background-color 0.2s, color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close-btn:hover {
  background-color: var(--bg-hover);
  color: var(--text-primary);
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.modal-feed-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  margin-bottom: 1.25rem;
}

.modal-avatar-wrapper {
  width: 72px;
  height: 72px;
  border-radius: 1rem;
  overflow: hidden;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.75rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.modal-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.modal-avatar-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: bold;
  background: linear-gradient(135deg, var(--border-secondary), var(--bg-tertiary));
  color: var(--text-secondary);
}

.modal-feed-title {
  font-size: 1.35rem;
  font-weight: bold;
  color: var(--text-primary);
  margin-bottom: 0.375rem;
  line-height: 1.2;
}

.language-badge {
  font-size: 0.65rem;
  font-weight: bold;
  color: var(--accent-text);
  background: color-mix(in srgb, var(--accent) 15%, transparent);
  padding: 0.125rem 0.5rem;
  border-radius: 999px;
  letter-spacing: 0.05em;
}

.modal-feed-desc {
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.5;
  text-align: center;
  margin-bottom: 1.5rem;
}

.modal-stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.75rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: 0.5rem;
}

.stat-label {
  font-size: 0.675rem;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}

.stat-val {
  font-size: 1.15rem;
  color: var(--text-primary);
}

.modal-detail-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-primary);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  font-size: 0.825rem;
}

.detail-label {
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.detail-val {
  color: var(--text-primary);
  text-align: right;
  word-break: break-all;
}

.detail-val.link {
  color: var(--accent-text);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}

.detail-val.link:hover {
  color: var(--accent);
  text-decoration: underline;
}

.detail-val.code-text {
  font-family: monospace;
  font-size: 0.75rem;
  background: var(--bg-secondary);
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  color: var(--text-secondary);
}

.tags-wrapper {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
  justify-content: flex-end;
}

.modal-tag {
  font-size: 0.7rem;
  font-weight: 500;
  color: var(--text-secondary);
  background: var(--bg-tertiary);
  padding: 0.0625rem 0.375rem;
  border-radius: 4px;
}

.modal-footer {
  display: flex;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  border-top: 1px solid var(--border-primary);
  background: var(--bg-secondary);
}

.modal-footer button {
  flex: 1;
  padding: 0.625rem 1rem;
  font-size: 0.875rem;
  font-weight: 600;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s, color 0.2s;
}

.btn-primary {
  background: var(--accent);
  color: #ffffff;
  border: none;
}

.btn-primary:hover {
  background: color-mix(in srgb, var(--accent) 85%, #000000);
}

.btn-secondary {
  background: transparent;
  color: var(--text-primary);
  border: 1px solid var(--border-secondary);
}

.btn-secondary:hover {
  background: var(--bg-hover);
  border-color: var(--text-secondary);
}

/* Responsive Overrides */
@media (min-width: 640px) {
  .topics-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
  }
  .feeds-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .topics-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 1.25rem;
  }
  
  .topics-shell.has-sidebar {
    height: 100vh;
    overflow: hidden;
  }
  
  .desktop-layout {
    display: flex;
  }
  
  .mobile-layout {
    display: none;
  }

  .scroll-container {
    padding: 1.5rem 2rem 3rem;
  }

  .content-container {
    padding: 0;
  }
}

/* Transition animations */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
