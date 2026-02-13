<template>
  <div class="vertical-video-container" ref="videoContainer">
    <!-- Header (matches StoryView) -->
    <div class="video-header">
      <button @click="handleBack" class="back-button">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>

      <div class="header-actions">
        <button
          class="action-button"
          :class="{ 'saved': isSaved }"
          @click.stop="handleSave"
          @touchend.stop.prevent="handleSave"
          aria-label="Save video"
        >
          <svg class="w-5 h-5" :fill="isSaved ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="video-content">
      <!-- Video Player -->
      <div class="video-player-container" :class="{ 'horizontal-video': isHorizontalVideo }" @click="togglePlay">
        <video 
          ref="videoPlayer"
          class="video-player"
          :class="{ 'horizontal-video': isHorizontalVideo }"
          :src="video.videoUrl"
          :poster="video.thumbnail"
          :muted="isMuted"
          @timeupdate="handleTimeUpdate"
          @loadedmetadata="handleVideoLoaded"
          @loadeddata="handleVideoDataLoaded"
          playsinline
        >
          Your browser does not support the video tag.
        </video>
        
        <!-- Play/Pause Overlay -->
        <div v-if="!isPlaying" class="play-overlay" @click.stop="togglePlay">
          <svg class="w-16 h-16" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z"/>
          </svg>
        </div>
        
        <!-- Video Controls -->
        <div class="video-controls" @click.stop>
          <div class="progress-container">
            <div 
              class="progress-bar-video"
              @click="handleSeek"
              ref="progressBar"
            >
              <div class="progress-fill-video" :style="{ width: videoProgress + '%' }"></div>
            </div>
          </div>
          
          <div class="controls-row">
            <button @click.stop="togglePlay" class="control-button">
              <svg v-if="isPlaying" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
              </svg>
              <svg v-else class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5v14l11-7z" />
              </svg>
            </button>
            <div class="flex items-center space-x-2">
              <button @click.stop="toggleMute" class="control-button">
                <svg v-if="!isMuted" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                </svg>
                <svg v-else class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
                </svg>
              </button>
              
              <span class="time-display">{{ currentTime }} / {{ duration }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Video Info Overlay -->
      <!-- <div class="video-info-overlay">
        <h2 class="video-title">{{ video.title }}</h2>
        <p class="video-description">{{ video.description }}</p>
      </div> -->
    </div>

    <!-- Bottom Controls -->
    <BottomControls 
      :initial-liked="isLiked"
      :article-content="props.video"
      @like="handleLike"
      @comments="handleComment"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import type { Video } from '@/stores/videos'
import BottomControls from './BottomControls.vue'
import { apiFetch } from '@/lib/api'

interface Props {
  video: any
  category: string
  storyIndex?: number
  totalStories?: number
  isSaved?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  storyIndex: 0,
  totalStories: 1,
  isSaved: false
})

const emit = defineEmits<{
  back: []
  follow: [authorId: string]
  nextStory: []
  prevStory: []
  comments: []
  save: [content: { id: string; collection?: string; saved: boolean }]
}>()

const isSaved = computed(() => props.isSaved)

const handleSave = async () => {
  const id = props.video?.id ?? props.video?._id ?? props.video?.contentId ?? props.video?.content_id
  if (!id) return
  const collection = props.video?.collection ?? props.category ?? 'videos'
  const currentlySaved = props.isSaved
  try {
    if (currentlySaved) {
      const res = await apiFetch(`/api/saved-articles/${encodeURIComponent(id)}`, { method: 'DELETE' })
      if (res.ok) emit('save', { id, collection, saved: false })
    } else {
      const res = await apiFetch('/api/saved-articles', {
        method: 'POST',
        body: JSON.stringify({ article_id: id, collection })
      })
      if (res.ok) emit('save', { id, collection, saved: true })
    }
  } catch {
    emit('save', { id, collection, saved: !currentlySaved })
  }
}

const isPlaying = ref(false)
const currentTime = ref('0:00')
const duration = ref('0:00')
const videoProgress = ref(0)
const isLiked = ref(false)
const isVisible = ref(false)
const isMuted = ref(false) // Start muted for autoplay compliance
const videoAspectRatio = ref(16/9) // Default aspect ratio
const isHorizontalVideo = computed(() => videoAspectRatio.value > 1)

const videoPlayer = ref<HTMLVideoElement>()
const progressBar = ref<HTMLDivElement>()
const videoContainer = ref<HTMLDivElement>()

// Intersection Observer for visibility detection
let intersectionObserver: IntersectionObserver | null = null

const handleBack = () => {
  emit('back')
}

const handleFollow = () => {
  emit('follow', props.video.author.username)
}

const togglePlay = () => {
  if (!videoPlayer.value) return
  
  if (isPlaying.value) {
    videoPlayer.value.pause()
  } else {
    videoPlayer.value.play()
  }
  isPlaying.value = !isPlaying.value
}

const playVideo = () => {
  if (!videoPlayer.value) return
  videoPlayer.value.play()
  isPlaying.value = true
}

const pauseVideo = () => {
  if (!videoPlayer.value) return
  videoPlayer.value.pause()
  isPlaying.value = false
}

const handleTimeUpdate = () => {
  if (!videoPlayer.value) return
  
  const current = videoPlayer.value.currentTime
  const total = videoPlayer.value.duration
  
  if (total > 0) {
    videoProgress.value = (current / total) * 100
    currentTime.value = formatTime(current)
  }
}

const handleVideoLoaded = () => {
  if (!videoPlayer.value) return
  duration.value = formatTime(videoPlayer.value.duration)
}

const handleVideoDataLoaded = () => {
  if (!videoPlayer.value) return
  
  console.log('Video data loaded:', {
    src: videoPlayer.value.src,
    videoWidth: videoPlayer.value.videoWidth,
    videoHeight: videoPlayer.value.videoHeight,
    duration: videoPlayer.value.duration
  })
  
  // Calculate aspect ratio
  const video = videoPlayer.value
  if (video.videoWidth && video.videoHeight) {
    videoAspectRatio.value = video.videoWidth / video.videoHeight
  }
}

const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const handleLike = () => {
  isLiked.value = !isLiked.value
}

const handleComment = (articleContent?: any) => {
  emit('comments')
  console.log('Comments event emitted from VerticalVideoView with content:', articleContent)
}

const handleShare = () => {
  console.log('Share clicked')
}

const handleSeek = (event: MouseEvent) => {
  if (!videoPlayer.value || !progressBar.value) return

  const rect = progressBar.value.getBoundingClientRect()
  const clickX = event.clientX - rect.left
  const width = rect.width

  const seekTime = (clickX / width) * videoPlayer.value.duration
  videoPlayer.value.currentTime = seekTime
}

const toggleMute = () => {
  if (!videoPlayer.value) return
  isMuted.value = !isMuted.value
  videoPlayer.value.muted = isMuted.value
}

// Visibility detection
const setupIntersectionObserver = () => {
  if (!videoContainer.value) return

  intersectionObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          // Video is visible - play it
          isVisible.value = true
          nextTick(() => {
            playVideo()
          })
        } else {
          // Video is not visible - pause it
          isVisible.value = false
          pauseVideo()
        }
      })
    },
    {
      threshold: 0.5, // Trigger when 50% of video is visible
      rootMargin: '0px'
    }
  )

  intersectionObserver.observe(videoContainer.value)
}

onMounted(() => {
  if (videoPlayer.value) {
    videoPlayer.value.addEventListener('play', () => isPlaying.value = true)
    videoPlayer.value.addEventListener('pause', () => isPlaying.value = false)
  }
  
  // Setup intersection observer for autoplay
  setupIntersectionObserver()
})

onUnmounted(() => {
  if (videoPlayer.value) {
    videoPlayer.value.removeEventListener('play', () => isPlaying.value = true)
    videoPlayer.value.removeEventListener('pause', () => isPlaying.value = false)
  }
  
  // Cleanup intersection observer
  if (intersectionObserver) {
    intersectionObserver.disconnect()
  }
})
</script>

<style scoped>
.vertical-video-container {
  @apply relative inset-0 bg-black;
  @apply flex flex-col;
  @apply touch-none;
  @apply h-full w-full;
  /* Mobile viewport handling */
  height: 100vh;
  height: 100dvh; /* Dynamic viewport height for mobile */
  min-height: -webkit-fill-available;
  /* Safe area insets for notched devices */
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
}

.video-header {
  @apply absolute top-0 left-0 right-0 z-10;
  @apply flex items-center justify-between px-4 pt-6 pb-2;
}

.back-button {
  @apply w-8 h-8 rounded-full bg-black bg-opacity-50;
  @apply flex items-center justify-center text-white;
  @apply hover:bg-opacity-70 transition-colors;
}

.header-actions {
  @apply flex items-center space-x-2;
}

.action-button {
  @apply w-8 h-8 rounded-full bg-black bg-opacity-50;
  @apply flex items-center justify-center text-white;
  @apply hover:bg-opacity-70 transition-colors;
  touch-action: manipulation;
}

.action-button.saved {
  @apply text-blue-400;
}

.video-content {
  @apply flex-1 relative;
  @apply flex items-center justify-center;
}

.video-player-container {
  @apply relative w-full h-full;
  @apply flex items-center justify-center;
  @apply bg-black;
}

.video-player-container.horizontal-video {
  @apply max-w-full max-h-full;
  @apply mx-auto;
}

.video-player {
  @apply w-full h-full object-cover;
  @apply bg-black;
}

.video-player.horizontal-video {
  @apply object-contain;
  @apply max-w-full max-h-full;
  @apply mx-auto;
}

.play-overlay {
  @apply absolute inset-0;
  @apply flex items-center justify-center;
  @apply bg-black bg-opacity-30;
  @apply text-white;
  @apply cursor-pointer;
}

.video-controls {
  @apply absolute bottom-0 left-0 right-0;
  @apply bg-gradient-to-t from-black to-transparent;
  @apply p-4;
  /* Mobile safe area handling */
  padding-bottom: calc(1rem + env(safe-area-inset-bottom));
  bottom: env(safe-area-inset-bottom);
}

.progress-container {
  @apply mb-4;
}

.progress-bar-video {
  @apply w-full h-1 bg-gray-600 bg-opacity-30 rounded-full;
  @apply overflow-hidden;
  @apply cursor-pointer;
  @apply hover:bg-opacity-50 transition-all duration-200;
}

.progress-fill-video {
  @apply h-full bg-white;
  @apply transition-all duration-100 ease-out;
  @apply relative;
}

.progress-fill-video::after {
  @apply absolute right-0 top-1/2 transform -translate-y-1/2;
  @apply w-3 h-3 bg-white rounded-full;
  @apply opacity-0 transition-opacity duration-200;
  content: '';
}

.progress-bar-video:hover .progress-fill-video::after {
  @apply opacity-100;
}

.controls-row {
  @apply flex items-center justify-between;
}

.control-button {
  @apply text-white hover:text-gray-300 transition-colors;
}

.time-display {
  @apply text-white text-sm;
}

.video-info-overlay {
  @apply absolute bottom-20 left-4 right-4;
  @apply text-white;
}

.video-title {
  @apply text-3xl font-bold mb-2 font-postoni;
}

.video-description {
  @apply text-base text-gray-300;
}

.video-bottom {
  @apply flex items-center justify-between px-6 pb-6;
  @apply relative z-10;
}

.bottom-left {
  @apply flex flex-col items-start space-x-2 space-y-4;
}

.category-tag {
  @apply px-3 py-1 rounded-full;
  @apply text-white text-sm font-medium;
}

.decorative-text {
  @apply text-gray-400 text-sm;
}

.video-actions {
  @apply flex items-start space-x-4;
}

.video-action-btn {
  @apply flex items-center space-x-1 text-white;
  @apply cursor-pointer;
}

.video-action-btn.active {
  @apply text-accent;
}

.action-text {
  @apply font-medium text-base;
}

.follow-button {
  @apply flex items-center px-3 py-1.5 bg-accent rounded-full;
  @apply text-white text-sm font-medium;
  @apply hover:bg-opacity-90 transition-colors;
}
</style> 