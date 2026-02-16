<template>
  <div class="saved-container">
    <header class="saved-header">
      <button class="back-button" @click="handleBack">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="saved-title">Saved Content</h1>
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

    // Build lookup: article_id -> index for ordering, and reverse lookup to tag items
    const savedOrder = new Map<string, number>()
    const savedIdMap = new Map<string, string>() // maps fetched item key -> original article_id
    savedList.forEach((s: { article_id: string; collection?: string }, i: number) => {
      savedOrder.set(s.article_id, i)
    })

    // Resolve each fetched item's saved article_id and ordering
    const resolveArticleId = (item: any): string | undefined => {
      const candidates = [
        String(item.id ?? ''),
        String(item._id ?? ''),
        String(item.contentId ?? item.content_id ?? ''),
      ].filter(Boolean)
      return candidates.find(c => savedOrder.has(c))
    }

    for (const item of fetchedItems) {
      const matched = resolveArticleId(item)
      if (matched) {
        item._savedArticleId = matched
      } else {
        item._savedArticleId = String(item.id ?? item._id ?? '')
      }
    }

    items.value = fetchedItems.sort((a: any, b: any) => {
      const ai = savedOrder.get(a._savedArticleId) ?? 999
      const bi = savedOrder.get(b._savedArticleId) ?? 999
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
    default:
      break
  }
}

const handleItemClick = (item: any) => {
  const id = item._id ?? item.id
  const category = item.collection ?? 'sports'
  // Pass the full item via router state so StoryView can use it even if not in the store
  router.push({
    path: `/story/${id}/${category}`,
    state: { savedItem: JSON.parse(JSON.stringify(item)) },
  })
}

const handleUnsave = async (item: any) => {
  // Use the original saved article_id (may be content_id for videos)
  const id = String(item._savedArticleId ?? item.id ?? item._id ?? '')
  if (!id) return
  unsavingId.value = String(item.id ?? item._id)
  try {
    const res = await apiFetch(`/api/saved-articles/${encodeURIComponent(id)}`, { method: 'DELETE' })
    if (res.ok) {
      items.value = items.value.filter((i) => i !== item)
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
  background-color: var(--bg-primary);
  color: var(--text-primary);
  padding-bottom: 5rem;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.saved-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border-primary);
}

.back-button {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-primary);
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
}

.saved-title {
  font-size: 1.125rem;
  font-weight: 400;
  color: var(--text-primary);
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
  border: 2px solid var(--spinner-border);
  border-top-color: var(--spinner-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  margin-top: 1rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.empty-icon {
  width: 4rem;
  height: 4rem;
  color: var(--text-tertiary);
  margin-bottom: 1rem;
}

.empty-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--text-primary);
}

.empty-subtitle {
  color: var(--text-secondary);
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
  background: var(--bg-elevated);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: background 0.2s;
}

.saved-item:hover {
  background: var(--bg-tertiary);
}

.item-thumbnail {
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

.collection-badge {
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

.item-content {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-size: 0.9375rem;
  font-weight: 600;
  line-height: 1.3;
  color: var(--text-primary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-author {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
}

.unsave-button {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  color: var(--accent);
  background: transparent;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: color 0.2s, opacity 0.2s;
}

.unsave-button:hover:not(:disabled) {
  color: var(--accent-text);
}

.unsave-button:disabled,
.unsave-button.saving {
  opacity: 0.6;
  cursor: not-allowed;
}

.unsave-button.saved {
  color: var(--accent);
}
</style>
