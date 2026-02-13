<template>
  <div class="podcast-bottom">
    <div class="flex flex-col gap-y-4 flex-1">
      <div v-if="showCategory" class="category-tag-container">
        <span class="category-tag">{{ category }}</span>
        <span class="decorative-text">
          <svg class="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Follow
        </span>
      </div>

      <div class="bottom-left">      
        <!-- Action Buttons -->
        <div class="podcast-actions">
          <!-- Simple Like Button -->
          <button @click="handleLike" class="podcast-action-btn" :class="{ 'active': isLiked, 'active-heart': isLiked }">
            <svg v-if="!isLiked" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
            <svg v-else class="w-6 h-6" fill="currentColor" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
            <span class="action-text">{{ isLiked ? 'Liked' : 'Like' }}</span>
          </button>
          
          <!-- Listen Button -->
          <button v-if="showListen" @click="handleListen" class="podcast-action-btn" :class="{ 'active': isListening }">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
            </svg>
            <span class="action-text">{{ isListening ? 'Listening' : 'Listen' }}</span>
          </button>
          
          <!-- Share Button -->
          <button @click="handleShare" class="podcast-action-btn">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
            </svg>
            <span class="action-text">Share</span>
          </button>
        </div>
      </div>
    </div>
    
    <div class="bottom-right">
      <button @click="handleComments" class="follow-button">
        <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
        </svg>
        Discuss
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import html2canvas from 'html2canvas'

interface Props {
  initialLiked?: boolean
  initialListening?: boolean
  showCategory?: boolean
  showListen?: boolean
  category?: string
  articleContent?: any
}

const props = withDefaults(defineProps<Props>(), {
  initialLiked: false,
  initialListening: false,
  showCategory: false,
  showListen: false,
  category: '',
  articleContent: null
})

const emit = defineEmits<{
  like: [liked: boolean]
  listen: [listening: boolean]
  comments: [articleContent?: any]
  share: []
}>()

const isLiked = ref(props.initialLiked)
const isListening = ref(props.initialListening)

const categoryEmoji = computed(() => {
  const category = props.category.toLowerCase()
  
  if (category.includes('news') || category.includes('politics')) return '📰'
  if (category.includes('sports')) return '⚽'
  if (category.includes('entertainment') || category.includes('celebrity')) return '🎭'
  if (category.includes('technology') || category.includes('tech')) return '💻'
  if (category.includes('business') || category.includes('finance')) return '💰'
  if (category.includes('health') || category.includes('medical')) return '🏥'
  if (category.includes('science')) return '🔬'
  if (category.includes('travel')) return '✈️'
  if (category.includes('food') || category.includes('cooking')) return '🍽️'
  if (category.includes('fashion') || category.includes('style')) return '👗'
  if (category.includes('music')) return '🎵'
  if (category.includes('movie') || category.includes('film')) return '🎬'
  if (category.includes('gaming') || category.includes('game')) return '🎮'
  if (category.includes('education') || category.includes('learning')) return '📚'
  if (category.includes('weather')) return '🌤️'
  if (category.includes('crime') || category.includes('police')) return '🚔'
  if (category.includes('environment') || category.includes('climate')) return '🌍'
  
  // Default emoji
  return '📰'
})



const handleLike = () => {
  isLiked.value = !isLiked.value
  emit('like', isLiked.value)
}

const handleListen = () => {
  isListening.value = !isListening.value
  emit('listen', isListening.value)
}

const handleComments = () => {
  emit('comments', props.articleContent)
}

const handleShare = async () => {
  try {
    // Find the main content container to screenshot
    const contentElement = document.querySelector('.story-container, .vertical-video-container, .podcast-container')
    
    if (!contentElement) {
      console.error('Content element not found for screenshot')
      emit('share')
      return
    }

    // Capture screenshot of the content
    const canvas = await html2canvas(contentElement as HTMLElement, {
      useCORS: true,
      allowTaint: true,
      scale: 2, // Higher quality screenshot
      // backgroundColor: '#000000',
      width: contentElement.clientWidth,
      height: contentElement.clientHeight,
      ignoreElements: (element) => {
        // Ignore certain elements like controls, buttons, etc.
        return element.classList.contains('podcast-bottom') || 
               element.classList.contains('video-controls') ||
               element.classList.contains('story-header') ||
               element.classList.contains('progress-container') ||
               element.classList.contains('controls-row') ||
               element.classList.contains('back-button') ||
               element.classList.contains('action-button') ||
               element.classList.contains('header-actions') ||
               element.tagName === 'BUTTON'
      }
    })
    

    // Convert canvas to blob
    canvas.toBlob(async (blob) => {
      if (!blob) {
        console.error('Failed to create blob from canvas')
        emit('share')
        return
      }

      await shareImageAsset(blob)
    }, 'image/png', 0.9)

  } catch (error) {
    console.error('Error capturing screenshot:', error)
    // Fallback to regular share
    emit('share')
  }
}

const shareImageAsset = async (blobImageAsset: Blob): Promise<boolean> => {
  try {
    // Get title from the current content
    const titleElement = document.querySelector('.story-title, .video-title, .podcast-title')
    const title = titleElement?.textContent || 'Washington Post Content'
    
    const filesArray = [
      new File([blobImageAsset], `${title}.png`, {
        type: 'image/png',
        lastModified: new Date().getTime(),
      }),
    ]
    
    const shareData = {
      title: `${title}`,
      files: filesArray,
    }

    if (navigator.canShare && navigator.canShare(shareData)) {
      await navigator.share(shareData)
      return true
    } else {
      // Fallback: create download link if Web Share API is not supported
      const url = URL.createObjectURL(blobImageAsset)
      const link = document.createElement('a')
      link.href = url
      link.download = `${title}.png`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      return true
    }
  } catch (error) {
    console.error('Error sharing image:', error)
    return false
  }
}


</script>

<style scoped>
.podcast-bottom {
  @apply absolute bottom-0 left-0 right-0;
  @apply flex items-center px-6;
  @apply relative z-10;
  /* Mobile safe area handling with fallback */
  padding-bottom: 1.5rem;
  padding-bottom: calc(1.5rem + env(safe-area-inset-bottom, 0px));
  /* Ensure it's above any mobile browser UI */
  bottom: 0;
  bottom: env(safe-area-inset-bottom, 0px);
  /* Fallback for browsers without env() support */
  @supports not (bottom: env(safe-area-inset-bottom)) {
    padding-bottom: 2rem;
  }
}

.bottom-left {
  @apply flex flex-col space-y-4;
}

.category-tag-container {
  @apply flex items-center space-x-2;
}

.category-tag {
  @apply text-white text-base font-medium;
  @apply pr-2.5 py-1;
  @apply truncate;
}

.decorative-text {
  @apply px-3 flex items-center text-white text-sm bg-accent py-1 rounded-full;
}

.podcast-actions {
  @apply flex flex-row gap-x-4;
}

.podcast-action-btn {
  @apply flex items-center space-x-1 select-none;
  @apply text-white;
  @apply transition-colors duration-200;
}

.podcast-action-btn:hover {
  @apply text-gray-300;
}

.podcast-action-btn.active {
  @apply transition-transform duration-200;
}

/* Red color and scaling for heart icon */
.podcast-action-btn.active-heart {
  @apply text-red-500;
  /* @apply scale-110; */
}

.action-text {
  @apply font-medium text-base;
}

.bottom-right {
  @apply flex items-end h-full;
}

.follow-button {
  @apply flex items-center px-4 py-2;
  @apply bg-white bg-opacity-10;
  @apply text-white text-sm font-medium;
  @apply rounded-full;
  @apply backdrop-blur-sm;
  @apply transition-all duration-200;
  @apply hover:bg-opacity-20;
}


</style> 