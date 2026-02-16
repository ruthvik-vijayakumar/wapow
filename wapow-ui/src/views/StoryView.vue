<template>
  <div class="story-page">
    <!-- Loading state while content is being fetched -->
    <div v-if="isLoading" class="loading-container">
      <div class="loading-spinner" />
    </div>
    <StoryFeed
      v-else-if="currentArticle"
      :initial-article="currentArticle"
      :articles="mixedCategoryContent"
      :category="currentCategory"
      @back="handleBack"
      @follow="handleFollow"
    />
    <div v-else class="loading-container">
      <p style="color: #aaa;">Content not found</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useContentStore } from '@/stores/videos'
import StoryFeed from '@/components/StoryFeed.vue'
import type { Article } from '@/stores/videos'
import Game from './wordle/Game.vue'

const route = useRoute()
const router = useRouter()
const contentStore = useContentStore()

const isLoading = ref(true)
const fetchedArticle = ref<any>(null)

// Retrieve item data passed via router state (from SavedView)
const savedItem = (window.history.state?.savedItem as Record<string, any>) ?? null

// Get article ID and category from route params
const articleId = computed(() => route.params.videoId as string)
const currentCategory = computed(() => route.params.category as string || 'Technology')

// Determine if the navigated item is a video or podcast (from saved page or store)
const resolvedVideo = computed(() => {
  const id = articleId.value
  if (savedItem && savedItem.collection === 'videos') return savedItem
  return contentStore.videos.find(
    (v: any) => String(v._id) === id || v.content_id === id || String(v.id) === id,
  ) ?? null
})

const resolvedPodcast = computed(() => {
  const id = articleId.value
  if (savedItem && savedItem.collection === 'podcasts') return savedItem
  return contentStore.podcastClips.find(
    (p: any) => String(p._id) === id || String(p.id) === id,
  ) ?? null
})

// Find the current article from the store (search articles, videos, and podcasts)
const currentArticle = computed(() => {
  const id = articleId.value

  if (resolvedVideo.value) {
    return {
      _id: id,
      type: 'video',
      headlines: { basic: resolvedVideo.value.tracking?.page_title || resolvedVideo.value.title || 'Video' },
      _videoRef: resolvedVideo.value,
    } as any
  }

  if (resolvedPodcast.value) {
    return {
      _id: id,
      type: 'podcast',
      headlines: { basic: resolvedPodcast.value.title || 'Podcast' },
      _podcastRef: resolvedPodcast.value,
    } as any
  }

  if (savedItem && savedItem.headlines?.basic) return savedItem as any

  const article = contentStore.articles.find(a => a._id === id || String(a._id) === id)
  if (article) return article

  // Use article fetched directly by ID from the API
  if (fetchedArticle.value) return fetchedArticle.value

  // Only fall back to first article if articles are loaded
  if (contentStore.articles.length > 0) return contentStore.articles[0]

  return null
})

const reccomendations = ref([])

onMounted(() => {
  window.addEventListener('resize', onResize)
  onResize()
  document.body.style.overflow = 'hidden'
})

onUnmounted(() => {
  document.body.style.overflow = ''
  window.removeEventListener('resize', onResize)
})

const onResize = () => {
  document.body.style.setProperty('--vh', window.innerHeight + 'px')
}

// Fetch the specific article by ID from the API (for page refresh scenarios)
async function fetchArticleById(id: string) {
  try {
    const response = await fetch(`${import.meta.env.VITE_ARTICLES_API || 'http://localhost:3001'}/api/articles/by-ids`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids: [id] })
    })
    const { data } = await response.json()
    if (data && data.length > 0) {
      fetchedArticle.value = data[0]
    }
  } catch (e) {
    console.error('Failed to fetch article by ID:', e)
  }
}

onMounted(async () => {
  const id = articleId.value

  // If the store is empty and we have no savedItem, fetch the article directly
  const needsDirectFetch = !savedItem && contentStore.articles.length === 0

  // Start all fetches in parallel
  const promises: Promise<any>[] = []

  // Always fetch recommendations
  promises.push(
    fetchRecommendations("user_001", currentCategory.value).then(async (recc) => {
      if (!recc) return
      const cat_ids = (recc.category_recommendations ?? []).map((item: any) => item.article_id)
      const gen_ids = (recc.general_recommendations ?? []).map((item: any) => item.article_id)
      const ids = [...cat_ids, ...gen_ids]
      if (ids.length === 0) return
      const response = await fetch(`${import.meta.env.VITE_ARTICLES_API || 'http://localhost:3001'}/api/articles/by-ids`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids })
      })
      const { data } = await response.json()
      reccomendations.value = data
    })
  )

  // If we need a direct fetch for this article (page was refreshed)
  if (needsDirectFetch && id) {
    promises.push(fetchArticleById(id))
  }

  // Wait for the content store's videos/podcasts to load (they init on store creation)
  // Give it a short wait so resolvedVideo/resolvedPodcast can resolve
  promises.push(
    new Promise<void>((resolve) => {
      if (contentStore.videos.length > 0 || contentStore.podcastClips.length > 0) {
        resolve()
        return
      }
      const unwatch = watch(
        () => contentStore.videos.length + contentStore.podcastClips.length,
        (total) => {
          if (total > 0) { unwatch(); resolve() }
        },
        { immediate: true }
      )
      // Timeout so we don't wait forever if store truly has no data
      setTimeout(() => { unwatch(); resolve() }, 3000)
    })
  )

  await Promise.all(promises)
  isLoading.value = false
})

// Recommendations API fetch function
const fetchRecommendations = async (userId: string, category: string) => {
  try {
    const response = await fetch(`${import.meta.env.VITE_CONTENT_API}/recommendations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        category: category
      })
    })

    if (!response.ok) {
      console.error('Recommendations API Error:', response.status, response.statusText)
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const data = await response.json()
    console.log('❤️Recommendations data:', data)
    return data
  } catch (error) {
    console.error('Error fetching recommendations:', error)
    return null
  }
}

// Create a healthy mix of articles, videos, podcast clips, and games for the current category
const mixedCategoryContent = computed(() => {
  const mixed: any[] = []

  // Filter articles by category
  const articles = reccomendations.value.filter((article: any) => {
    const articleCategory = article.taxonomy?.primary_section?.name ||
      article.taxonomy?.sections?.[0]?.name ||
      article.type || 'News'
    return articleCategory.toLowerCase() === currentCategory.value.toLowerCase()
  })

  // Get some videos (optionally filter by category if you have that info)
  const videos = contentStore.videos.slice(0, 10)
  // Get some podcast clips
  const podcastClips = contentStore.podcastClips.slice(0, 5)

  // Interleave articles, videos, and podcast clips
  const maxLen = Math.max(articles.length, videos.length, podcastClips.length)
  for (let i = 0; i < maxLen; i++) {
    if (articles[i]) mixed.push(articles[i])
    if (videos[i]) mixed.push(videos[i])
    if (podcastClips[i]) mixed.push(podcastClips[i])
  }

  // Add game content to the mix
  const gameContent = {
    _id: 'wordle-game',
    type: 'game',
    title: 'Wordle',
    component: 'Game'
  }

  mixed.push(gameContent)

  console.log('Mixed content:', mixed.length, mixed.map(item => item.type || 'article'))

  return mixed
})

const handleBack = () => {
  router.back()
}

const handleFollow = (authorId: string) => {
  console.log('Follow clicked for:', authorId)
  // TODO: Implement follow functionality
}
</script>

<style scoped>
.story-page {
  @apply fixed inset-0 bg-black;
  overflow: hidden;
}

.loading-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  width: 100%;
}

.loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid rgba(255, 255, 255, 0.15);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
