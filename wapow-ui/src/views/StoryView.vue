<template>
  <div class="story-page">
    <StoryFeed
      :initial-article="currentArticle"
      :articles="mixedCategoryContent"
      :category="currentCategory"
      @back="handleBack"
      @follow="handleFollow"  
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useContentStore } from '@/stores/videos'
import StoryFeed from '@/components/StoryFeed.vue'
import type { Article } from '@/stores/videos'
import Game from './wordle/Game.vue'

const route = useRoute()
const router = useRouter()
const contentStore = useContentStore()



// Get article ID and category from route params
const articleId = computed(() => route.params.videoId as string)
const currentCategory = computed(() => route.params.category as string || 'Technology')

// Find the current article from the store
const currentArticle = computed(() => {
  return contentStore.articles.find(article => article._id === articleId.value) || contentStore.articles[0]
})

const reccomendations = ref([])

onMounted(() => {
  console.log('Game created')
  window.addEventListener('resize', onResize)
  // set size on startup
  onResize()
})

const onResize = () => {
  // get actual vh on mobile
  document.body.style.setProperty('--vh', window.innerHeight + 'px')
}

onMounted(async () => {
  const recc = await fetchRecommendations("user_001", currentCategory.value)
  const cat_ids = recc.category_recommendations.map((item: any) => item.article_id)
  const gen_ids = recc.general_recommendations.map((item: any) => item.article_id)
  const ids = [...cat_ids, ...gen_ids]
  const response = await fetch(`${import.meta.env.VITE_ARTICLES_API || 'http://localhost:3001'}/api/articles/by-ids`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ ids: ids })
  })
  const {data} = await response.json()
  reccomendations.value = data
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
  const mixed: any[] = []
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
}
</style> 