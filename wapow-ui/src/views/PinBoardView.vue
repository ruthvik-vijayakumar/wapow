<template>
  <div class="pin-board-container">
    <TopBar @menu="handleMenu" @notification="handleNotification" />

    <!-- Pin Board Bar -->
    <div class="nav-bar">
      <div class="nav-right">
        <button class="grid-button">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
          </svg>
        </button>
        <button class="options-button">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Search Bar -->
    <div class="search-container">
      <div class="search-bar">
        <svg class="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input 
          v-model="searchQuery" 
          type="search" 
          placeholder="Search your articles"
          class="search-input"
          aria-label="Search your articles"
        />
        <button 
          v-if="searchQuery" 
          type="button" 
          class="search-clear"
          aria-label="Clear search"
          @click="searchQuery = ''"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="content-area">
      <!-- Article Groups -->
      <div v-for="group in filteredGroups" :key="group.name" class="article-group">
        <div class="group-header">
          <div class="group-indicator" :style="{ backgroundColor: group.color }"></div>
          <div class="group-name">{{ group.name }}</div>
          <button class="group-options">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
            </svg>
          </button>
        </div>
        
        <div class="group-articles">
          <div 
            v-for="(article, index) in group.articles.slice(0, 4)" 
            :key="article._id"
            class="article-preview"
            @click="handleArticleClick(article)"
          >
            <div class="preview-icon">
              <div class="icon-placeholder">{{ getArticleIcon(article) }}</div>
            </div>
          </div>
          <div v-if="group.articles.length > 4" class="more-indicator">
            +{{ group.articles.length - 4 }}
          </div>
          <div v-for="i in Math.max(0, 4 - group.articles.length)" :key="`empty-${i}`" class="empty-slot"></div>
        </div>
      </div>

      <!-- Individual Articles -->
      <div 
        v-for="article in individualArticles" 
        :key="article._id"
        class="individual-article"
        @click="handleArticleClick(article)"
      >
        <div class="article-header">
          <div class="article-icon">
            <div class="icon-placeholder">{{ getArticleIcon(article) }}</div>
          </div>
          <div class="article-title">{{ getArticleTitle(article) }}</div>
          <button class="close-button" @click.stop="closeArticle(article)">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div class="article-content">
          <div class="content-preview">
            <div class="preview-text">{{ getArticlePreview(article) }}</div>
            <div class="preview-meta">
              <span class="meta-item">{{ getArticleAuthor(article) }}</span>
              <span class="meta-item">{{ formatDate(article.display_date) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <BottomNavigation @navigate="handleNavigation" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useContentStore } from '@/stores/videos'
import type { Article } from '@/stores/videos'
import TopBar from '@/components/TopBar.vue'
import BottomNavigation from '@/components/BottomNavigation.vue'

const router = useRouter()
const contentStore = useContentStore()

const handleMenu = () => {
  router.push('/')
}

const handleNotification = () => {
  console.log('Notification clicked')
}

const handleNavigation = (route: string) => {
  switch (route) {
    case 'home':
      router.push('/')
      break
    case 'ask-ai':
      console.log('Navigate to Ask AI')
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

// State
const searchQuery = ref('')

// Mock data for groups (in a real app, this would come from the store)
const groups = ref([
  {
    name: 'Technology',
    color: '#EC4899', // Pink like Wharton PM
    articles: contentStore.articles.filter(a => a.taxonomy?.primary_section?.name === 'Technology').slice(0, 6)
  },
  {
    name: 'Health',
    color: '#9CA3AF', // Light gray like UVA PM
    articles: contentStore.articles.filter(a => a.taxonomy?.primary_section?.name === 'Health').slice(0, 4)
  }
])

// Computed
const individualArticles = computed(() => {
  return contentStore.articles.filter(article => 
    !groups.value.some(group => 
      group.articles.some(groupArticle => groupArticle._id === article._id)
    )
  ).slice(0, 10)
})

const filteredGroups = computed(() => {
  if (!searchQuery.value) return groups.value
  
  return groups.value.map(group => ({
    ...group,
    articles: group.articles.filter(article => 
      article.headlines?.basic?.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      article.description?.basic?.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  })).filter(group => group.articles.length > 0)
})

// Methods
const handleArticleClick = (article: Article) => {
  const category = getCategoryFromArticle(article)
  router.push(`/story/${article._id}/${category}`)
}

const closeArticle = (article: Article) => {
  // In a real app, this would remove the article from the pin board
  console.log('Close article:', article.headlines?.basic)
}

const getCategoryFromArticle = (article: Article): string => {
  return article.taxonomy?.primary_section?.name || 
         article.taxonomy?.sections?.[0]?.name || 
         article.type || 
         'News'
}

const getArticleIcon = (article: Article): string => {
  const section = article.taxonomy?.primary_section?.name || ''
  const icons: { [key: string]: string } = {
    'Technology': '💻',
    'Health': '🏥',
    'Politics': '🏛️',
    'Sports': '⚽',
    'Entertainment': '🎭',
    'Business': '💼',
    'Science': '🔬',
    'Education': '📚'
  }
  return icons[section] || '📰'
}

const getArticleTitle = (article: Article): string => {
  return article.headlines?.basic || 'Untitled Article'
}

const getArticlePreview = (article: Article): string => {
  return article.description?.basic || 'No description available'
}

const getArticleAuthor = (article: Article): string => {
  return article.credits?.by?.[0]?.name || 'Unknown Author'
}

const formatDate = (dateString: string): string => {
  if (!dateString) return ''
  
  const date = new Date(dateString)
  const now = new Date()
  const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)
  
  if (diffInHours < 1) {
    return 'Just now'
  } else if (diffInHours < 24) {
    return `${Math.floor(diffInHours)}h ago`
  } else if (diffInHours < 48) {
    return 'Yesterday'
  } else {
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    })
  }
}
</script>

<style scoped>
.pin-board-container {
  min-height: 100vh;
  height: 100vh;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  @apply flex flex-col;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.nav-bar {
  @apply flex items-center justify-end px-4 py-3;
  background-color: var(--bg-primary);
}

.nav-right {
  @apply flex items-center space-x-2;
}

.grid-button, .options-button {
  @apply p-2 rounded-lg transition-colors;
  color: var(--text-primary);
}

.grid-button:hover, .options-button:hover {
  background-color: var(--bg-hover);
}

.search-container {
  @apply px-4 py-3;
  background-color: var(--bg-primary);
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: 0.5rem;
  background-color: var(--bg-input);
  border: 1px solid var(--border-primary);
  transition: border-color 0.15s ease, box-shadow 0.15s ease, background-color 0.3s ease;
}

.search-bar:focus-within {
  border-color: var(--border-secondary);
  box-shadow: 0 0 0 1px var(--border-secondary);
}

.search-icon {
  flex-shrink: 0;
  width: 1.25rem;
  height: 1.25rem;
  color: var(--text-tertiary);
}

.search-input {
  flex: 1;
  min-width: 0;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 0.9375rem;
  outline: none;
}

.search-input::placeholder {
  color: var(--text-tertiary);
}

.search-clear {
  flex-shrink: 0;
  padding: 0.25rem;
  border-radius: 0.25rem;
  color: var(--text-tertiary);
  transition: color 0.15s ease, background-color 0.15s ease;
}

.search-clear:hover {
  color: var(--text-primary);
  background-color: var(--bg-hover);
}

.content-area {
  @apply flex-1 px-4 pb-4;
  @apply space-y-4;
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

.article-group {
  @apply rounded-lg p-4;
  background-color: var(--bg-elevated);
}

.group-header {
  @apply flex items-center space-x-3 mb-3;
}

.group-indicator {
  @apply w-3 h-3 rounded-full;
}

.group-name {
  @apply flex-1 font-medium;
  color: var(--text-primary);
}

.group-options {
  @apply p-1 rounded transition-colors;
  color: var(--text-secondary);
}

.group-options:hover {
  color: var(--text-primary);
  background-color: var(--bg-hover);
}

.group-articles {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.5rem;
}

.article-preview {
  @apply rounded cursor-pointer transition-colors;
  @apply flex items-center justify-center;
  background-color: var(--bg-tertiary);
}
.article-preview:hover {
  background-color: var(--bg-hover);
}

.preview-icon {
  @apply text-xl;
  color: var(--text-primary);
}

.more-indicator {
  @apply rounded flex items-center justify-center text-xs;
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
  aspect-ratio: 1 / 1;
  min-height: 0;
}

.empty-slot {
  @apply rounded;
  background-color: var(--bg-tertiary);
  aspect-ratio: 1 / 1;
  min-height: 0;
}

.individual-article {
  @apply rounded-lg p-4 cursor-pointer transition-colors;
  background-color: var(--bg-elevated);
}
.individual-article:hover {
  background-color: var(--bg-tertiary);
}

.article-header {
  @apply flex items-center space-x-3 mb-3;
}

.article-icon {
  @apply w-8 h-8 rounded flex items-center justify-center;
  background-color: var(--bg-tertiary);
}

.icon-placeholder {
  @apply text-sm;
  color: var(--text-primary);
}

.article-title {
  @apply flex-1 font-medium truncate;
  color: var(--text-primary);
}

.close-button {
  @apply p-1 rounded transition-colors;
  color: var(--text-secondary);
}

.close-button:hover {
  color: var(--text-primary);
  background-color: var(--bg-hover);
}

.article-content {
  @apply space-y-2;
}

.content-preview {
  @apply space-y-1;
}

.preview-text {
  @apply text-sm line-clamp-2;
  color: var(--text-secondary);
}

.preview-meta {
  @apply flex items-center space-x-2 text-xs;
  color: var(--text-tertiary);
}

.meta-item {
  @apply flex items-center;
}

.meta-item:not(:last-child)::after {
  content: '•';
  @apply ml-2;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style> 