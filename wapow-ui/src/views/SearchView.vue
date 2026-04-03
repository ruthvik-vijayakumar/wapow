<template>
  <div class="search-container">
    <!-- Search Header -->
    <header class="search-header">
      <div class="search-input-wrapper">
        <svg class="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          ref="searchInput"
          v-model="query"
          type="text"
          class="search-input"
          placeholder="Search articles, videos, podcasts…"
          @input="handleInput"
          @keydown.enter="executeSearch"
        />
        <button v-if="query" class="clear-button" @click="clearSearch">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </header>

    <!-- Skeleton loader -->
    <div v-if="isLoading" class="results-list">
      <div v-for="n in 8" :key="n" class="result-item skeleton-item">
        <div class="result-thumbnail skeleton-pulse"></div>
        <div class="result-content">
          <div class="skeleton-line skeleton-pulse" style="width: 85%; height: 0.875rem;"></div>
          <div class="skeleton-line skeleton-pulse" style="width: 60%; height: 0.75rem; margin-top: 0.5rem;"></div>
          <div class="skeleton-line skeleton-pulse" style="width: 35%; height: 0.625rem; margin-top: 0.375rem;"></div>
        </div>
      </div>
    </div>

    <!-- Empty query prompt -->
    <div v-else-if="!hasSearched" class="state-container">
      <svg class="state-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <p class="state-title">Find what matters</p>
      <p class="state-subtitle">Search across all articles, videos, and podcasts</p>
    </div>

    <!-- No results -->
    <div v-else-if="results.length === 0" class="state-container">
      <svg class="state-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <p class="state-title">No results found</p>
      <p class="state-subtitle">Try different keywords or check your spelling</p>
    </div>

    <!-- Results -->
    <div v-else class="results-list">
      <div
        v-for="item in results"
        :key="item.id"
        class="result-item"
        @click="handleItemClick(item)"
      >
        <div class="result-thumbnail">
          <img
            :src="getImageUrl(item)"
            :alt="getTitle(item)"
            class="thumbnail-img"
            loading="lazy"
          />
          <span class="type-badge">{{ item._type }}</span>
        </div>
        <div class="result-content">
          <h3 class="result-title">{{ getTitle(item) }}</h3>
          <p v-if="getDescription(item)" class="result-description">{{ getDescription(item) }}</p>
          <p v-if="getAuthor(item)" class="result-author">{{ getAuthor(item) }}</p>
        </div>
      </div>
    </div>

    <BottomNavigation @navigate="handleNavigation" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import BottomNavigation from '@/components/BottomNavigation.vue'
import { apiFetch } from '@/lib/api'
import { useAnalytics } from '@/composables/useAnalytics'

const router = useRouter()
const { trackSearch } = useAnalytics()

const searchInput = ref<HTMLInputElement | null>(null)
const query = ref('')
const results = ref<any[]>([])
const isLoading = ref(false)
const hasSearched = ref(false)

let debounceTimer: ReturnType<typeof setTimeout> | null = null

onMounted(() => {
  nextTick(() => searchInput.value?.focus())
})

function handleInput() {
  if (debounceTimer) clearTimeout(debounceTimer)
  if (!query.value.trim()) {
    results.value = []
    hasSearched.value = false
    return
  }
  debounceTimer = setTimeout(() => executeSearch(), 400)
}

async function executeSearch() {
  const q = query.value.trim()
  if (!q) return

  isLoading.value = true
  hasSearched.value = true

  try {
    const [articlesRes, videosRes, podcastsRes] = await Promise.all([
      apiFetch(`/api/articles?search=${encodeURIComponent(q)}&limit=20`),
      apiFetch(`/api/videos?search=${encodeURIComponent(q)}&limit=10`),
      apiFetch(`/api/podcasts?search=${encodeURIComponent(q)}&limit=10`),
    ])

    const combined: any[] = []

    if (articlesRes.ok) {
      const json = await articlesRes.json()
      const items = json.data ?? []
      items.forEach((item: any) => { item._type = 'Article' })
      combined.push(...items)
    }

    if (videosRes.ok) {
      const json = await videosRes.json()
      const items = json.data ?? []
      items.forEach((item: any) => { item._type = 'Video' })
      combined.push(...items)
    }

    if (podcastsRes.ok) {
      const json = await podcastsRes.json()
      const items = json.data ?? []
      items.forEach((item: any) => { item._type = 'Podcast' })
      combined.push(...items)
    }

    results.value = combined
    trackSearch(q, combined.length)
  } catch {
    results.value = []
  } finally {
    isLoading.value = false
  }
}

function clearSearch() {
  query.value = ''
  results.value = []
  hasSearched.value = false
  nextTick(() => searchInput.value?.focus())
}

function getTitle(item: any): string {
  return item.headlines?.basic || item.title || item.name || 'Untitled'
}

function getDescription(item: any): string {
  const desc = item.description?.basic || item.description || ''
  if (typeof desc !== 'string') return ''
  return desc.length > 120 ? desc.slice(0, 120) + '…' : desc
}

function getImageUrl(item: any): string {
  return (
    item.promo_items?.basic?.url ||
    item.imageUrl ||
    item.thumbnail ||
    item.promo_items?.basic?.additional_properties?.thumbnailResizeUrl ||
    ''
  )
}

function getAuthor(item: any): string {
  if (item.credits?.by?.[0]?.name) return item.credits.by[0].name
  if (item.author) return item.author
  return ''
}

function handleItemClick(item: any) {
  const id = item._id ?? item.id
  const category = item.category || item._type?.toLowerCase() || 'sports'
  router.push(`/story/${id}/${category}`)
}

function handleNavigation(route: string) {
  switch (route) {
    case 'home':
      router.push('/')
      break
    case 'search':
      break
    case 'profile':
      router.push('/profile')
      break
    default:
      break
  }
}
</script>

<style scoped>
.search-container {
  min-height: 100vh;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  padding-bottom: 5rem;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.search-header {
  position: sticky;
  top: 0;
  z-index: 10;
  padding: 0.75rem 1rem;
  background-color: var(--bg-primary);
  border-bottom: 1px solid var(--border-primary);
}

.search-input-wrapper {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--bg-input);
  border-radius: 0.75rem;
  padding: 0.625rem 0.875rem;
  transition: background 0.2s;
}

.search-icon {
  width: 1.25rem;
  height: 1.25rem;
  flex-shrink: 0;
  color: var(--text-tertiary);
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: 0.9375rem;
  color: var(--text-primary);
}

.search-input::placeholder {
  color: var(--text-tertiary);
}

.clear-button {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 50%;
  background: var(--bg-hover);
  color: var(--text-secondary);
  border: none;
  cursor: pointer;
  transition: background 0.2s;
}

.clear-button:hover {
  background: var(--border-secondary);
}

/* States (loading / empty / no results) */
.state-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 5rem 2rem;
  text-align: center;
}

.state-icon {
  width: 3.5rem;
  height: 3.5rem;
  color: var(--text-tertiary);
  margin-bottom: 1rem;
}

.state-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 0.375rem;
  color: var(--text-primary);
}

.state-subtitle {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.state-text {
  margin-top: 1rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

/* Skeleton loader */
.skeleton-item {
  pointer-events: none;
}

.skeleton-pulse {
  background: var(--bg-tertiary);
  border-radius: 0.25rem;
  position: relative;
  overflow: hidden;
}

.skeleton-pulse::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    var(--bg-hover) 50%,
    transparent 100%
  );
  animation: shimmer 1.4s ease-in-out infinite;
}

.skeleton-line {
  height: 0.75rem;
  border-radius: 0.25rem;
}

@keyframes shimmer {
  0%   { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

/* Results */
.results-list {
  padding: 0.75rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 0.625rem;
  background: var(--bg-elevated);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: background 0.2s;
}

.result-item:hover {
  background: var(--bg-tertiary);
}

.result-thumbnail {
  position: relative;
  flex-shrink: 0;
  width: 6rem;
  height: 4rem;
  border-radius: 0.375rem;
  overflow: hidden;
  background: var(--bg-tertiary);
}

.thumbnail-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.type-badge {
  position: absolute;
  bottom: 0.25rem;
  left: 0.25rem;
  font-size: 0.625rem;
  font-weight: 500;
  text-transform: uppercase;
  background: rgba(0, 0, 0, 0.7);
  color: #ffffff;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
}

.result-content {
  flex: 1;
  min-width: 0;
}

.result-title {
  font-size: 0.9375rem;
  font-weight: 600;
  line-height: 1.3;
  color: var(--text-primary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.result-description {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.result-author {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  margin-top: 0.25rem;
}
</style>
