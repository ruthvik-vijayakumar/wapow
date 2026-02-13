<template>
  <div class="saved-container">
    <header class="saved-header">
      <button class="back-button" @click="handleBack">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="saved-title">Saved Content</h1>
      <div class="header-spacer"></div>
    </header>

    <div v-if="isLoading" class="loading-state">
      <div class="loading-spinner"></div>
      <p class="loading-text">Loading saved content...</p>
    </div>

    <div v-else-if="items.length === 0" class="empty-state">
      <svg class="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
      </svg>
      <p class="empty-title">Nothing saved yet</p>
      <p class="empty-subtitle">Save articles, videos, and podcasts to find them here</p>
    </div>

    <div v-else class="saved-list">
      <div
        v-for="item in items"
        :key="item.id"
        class="saved-item"
        @click="handleItemClick(item)"
      >
        <div class="item-thumbnail">
          <img
            :src="item.imageUrl || item.promo_items?.basic?.url || 'https://via.placeholder.com/120x80?text=No+image'"
            :alt="item.title"
            class="thumbnail-img"
          />
          <span class="collection-badge">{{ formatCollection(item.collection) }}</span>
        </div>
        <div class="item-content">
          <h3 class="item-title">{{ item.title }}</h3>
          <p v-if="item.author" class="item-author">by {{ item.author }}</p>
        </div>
        <button
          class="unsave-button"
          :class="{ 'saving': unsavingId === item.id }"
          :disabled="unsavingId === item.id"
          @click.stop="handleUnsave(item)"
          aria-label="Remove from saved"
        >
          <svg class="w-5 h-5" fill="currentColor" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
          </svg>
        </button>
      </div>
    </div>

    <BottomNavigation @navigate="handleNavigation" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import BottomNavigation from '@/components/BottomNavigation.vue'
import { apiFetch } from '@/lib/api'

const router = useRouter()
const isLoading = ref(true)
const items = ref<any[]>([])
const unsavingId = ref<string | null>(null)

const formatCollection = (coll: string) => {
  if (!coll) return 'Content'
  if (coll === 'videos') return 'Video'
  if (coll === 'podcasts') return 'Podcast'
  return coll.charAt(0).toUpperCase() + coll.slice(1)
}

const loadSaved = async () => {
  isLoading.value = true
  try {
    const savedRes = await apiFetch('/api/saved-articles')
    if (!savedRes.ok) {
      items.value = []
      return
    }
    const savedJson = await savedRes.json()
    const savedList = savedJson.data ?? []
    if (savedList.length === 0) {
      items.value = []
      return
    }
    const ids = savedList.map((s: { article_id: string }) => s.article_id)
    const byIdsRes = await apiFetch('/api/articles/by-ids', {
      method: 'POST',
      body: JSON.stringify({ ids }),
    })
    if (!byIdsRes.ok) {
      items.value = []
      return
    }
    const byIdsJson = await byIdsRes.json()
    const fetchedItems = byIdsJson.data ?? []
    const savedOrder = new Map(savedList.map((s: { article_id: string }, i: number) => [s.article_id, i]))
    items.value = fetchedItems.sort((a: any, b: any) => {
      const ai = savedOrder.get(String(a.id ?? a._id)) ?? 999
      const bi = savedOrder.get(String(b.id ?? b._id)) ?? 999
      return ai - bi
    })
  } catch {
    items.value = []
  } finally {
    isLoading.value = false
  }
}

const handleBack = () => router.push('/profile')
const handleNavigation = (route: string) => {
  switch (route) {
    case 'home':
      router.push('/')
      break
    case 'profile':
      router.push('/profile')
      break
    case 'pin-board':
      router.push('/pin-board')
      break
    default:
      break
  }
}

const handleItemClick = (item: any) => {
  const id = item.id ?? item._id
  const category = item.collection ?? 'sports'
  router.push(`/story/${id}/${category}`)
}

const handleUnsave = async (item: any) => {
  const id = String(item.id ?? item._id ?? '')
  if (!id) return
  unsavingId.value = id
  try {
    const res = await apiFetch(`/api/saved-articles/${encodeURIComponent(id)}`, { method: 'DELETE' })
    if (res.ok) {
      items.value = items.value.filter((i) => String(i.id ?? i._id) !== id)
    }
  } finally {
    unsavingId.value = null
  }
}

onMounted(() => loadSaved())
</script>

<style scoped>
.saved-container {
  min-height: 100vh;
  background-color: #000;
  color: white;
  padding-bottom: 5rem;
}

.saved-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #1f2937;
}

.back-button {
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
}

.saved-title {
  font-size: 1.125rem;
  font-weight: 600;
  @apply font-postoni;
}

.header-spacer {
  width: 2.5rem;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  text-align: center;
}

.loading-spinner {
  width: 3rem;
  height: 3rem;
  border: 2px solid #374151;
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  margin-top: 1rem;
  color: #9ca3af;
  font-size: 0.875rem;
}

.empty-icon {
  width: 4rem;
  height: 4rem;
  color: #4b5563;
  margin-bottom: 1rem;
}

.empty-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.empty-subtitle {
  color: #9ca3af;
  font-size: 0.875rem;
}

.saved-list {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.saved-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  background: #111;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: background 0.2s;
}

.saved-item:hover {
  background: #1a1a1a;
}

.item-thumbnail {
  position: relative;
  flex-shrink: 0;
  width: 6rem;
  height: 4rem;
  border-radius: 0.375rem;
  overflow: hidden;
  background: #1f2937;
}

.thumbnail-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.collection-badge {
  position: absolute;
  bottom: 0.25rem;
  left: 0.25rem;
  font-size: 0.625rem;
  font-weight: 500;
  text-transform: uppercase;
  background: rgba(0, 0, 0, 0.7);
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-size: 0.9375rem;
  font-weight: 600;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-author {
  font-size: 0.75rem;
  color: #9ca3af;
  margin-top: 0.25rem;
}

.unsave-button {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  color: #2563eb;
  background: transparent;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: color 0.2s, opacity 0.2s;
}

.unsave-button:hover:not(:disabled) {
  color: #3b82f6;
}

.unsave-button:disabled,
.unsave-button.saving {
  opacity: 0.6;
  cursor: not-allowed;
}

.unsave-button.saved {
  color: #2563eb;
}
</style>
