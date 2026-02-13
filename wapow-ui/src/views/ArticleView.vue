<template>
  <div class="article-view-container">
    <!-- Header with back button -->
    <div class="article-header">
      <button @click="handleBack" class="back-button">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        <span class="back-text">Back to Story</span>
      </button>
    </div>


    <!-- Iframe container -->
    <div class="iframe-container">
      <iframe
        :src="`https://washingtonpost.com/${articleUrl}`"
        class="article-iframe"
        @load="handleIframeLoad"
        frameborder="0"
        allowfullscreen
      ></iframe>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

// Reactive state
const isLoading = ref(true)
const hasError = ref(false)
const errorMessage = ref('')
const iframeLoaded = ref(false)

// Get article URL from route params
const articleUrl = computed(() => {
  return route.params.url as string || ''
})

// Get article title from route params or use default
const articleTitle = computed(() => {
  return route.params.title as string || 'Article'
})

// Handle back button click
const handleBack = () => {
  router.back()
}

// Handle iframe load success
const handleIframeLoad = () => {
  isLoading.value = false
  iframeLoaded.value = true
  console.log('Article iframe loaded successfully')
}

// Handle iframe load error
const handleIframeError = () => {
  isLoading.value = false
  hasError.value = true
  errorMessage.value = 'Failed to load the article. Please check your internet connection and try again.'
  console.error('Article iframe failed to load')
}

// Retry loading the article
const retryLoad = () => {
  isLoading.value = true
  hasError.value = false
  errorMessage.value = ''
  iframeLoaded.value = false
}

// Initialize component
onMounted(() => {
  console.log('ArticleView mounted with URL:', articleUrl.value)
  
  // Set a timeout to show error if iframe doesn't load
  setTimeout(() => {
    if (isLoading.value) {
      isLoading.value = false
      hasError.value = true
      errorMessage.value = 'The article is taking too long to load. Please try again.'
    }
  }, 10000) // 10 second timeout
})
</script>

<style scoped>
.article-view-container {
  @apply flex flex-col h-screen bg-white;
  /* Mobile safe area handling */
  height: 100vh;
  height: 100dvh;
  min-height: -webkit-fill-available;
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
}

.article-header {
  @apply flex items-center justify-between;
  @apply px-4 py-3;
  @apply bg-white border-b border-gray-200;
  @apply shadow-sm;
  @apply z-10;
}

.back-button {
  @apply flex items-center space-x-2;
  @apply text-gray-600 hover:text-gray-800;
  @apply transition-colors duration-200;
  @apply font-medium;
}

.back-text {
  @apply text-sm;
}

.article-title {
  @apply flex-1;
  @apply text-center;
}

.article-title h1 {
  @apply text-lg font-semibold;
  @apply text-gray-900;
  @apply truncate;
  @apply max-w-xs;
}

.loading-container {
  @apply flex flex-col items-center justify-center;
  @apply flex-1;
  @apply p-8;
}

.loading-spinner {
  @apply w-8 h-8;
  @apply border-4 border-gray-200 border-t-blue-600;
  @apply rounded-full;
  @apply animate-spin;
  @apply mb-4;
}

.loading-text {
  @apply text-gray-600;
  @apply text-sm;
}

.error-container {
  @apply flex flex-col items-center justify-center;
  @apply flex-1;
  @apply p-8;
  @apply text-center;
}

.error-icon {
  @apply text-red-500;
  @apply mb-4;
}

.error-title {
  @apply text-xl font-semibold;
  @apply text-gray-900;
  @apply mb-2;
}

.error-message {
  @apply text-gray-600;
  @apply mb-6;
  @apply max-w-md;
}

.retry-button {
  @apply bg-blue-600 hover:bg-blue-700;
  @apply text-white font-medium;
  @apply px-6 py-3 rounded-lg;
  @apply transition-colors duration-200;
}

.iframe-container {
  @apply flex-1;
  @apply relative;
  @apply overflow-hidden;
}

.article-iframe {
  @apply w-full h-full;
  @apply border-0;
}
</style>
