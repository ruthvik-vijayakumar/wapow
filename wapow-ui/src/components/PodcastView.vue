<template>
  <div class="podcast-container" ref="podcastContainer">
    <!-- Header (matches StoryView) -->
    <div class="podcast-header">
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
          aria-label="Save podcast"
        >
          <svg class="w-5 h-5" :fill="isSaved ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="podcast-content">
      <!-- Album Art -->
      <div class="album-art-container">
        <img
          :src="props.podcast.thumbnail"
          :alt="props.podcast.title"
          class="album-art"
        />

        <!-- Play/Pause Overlay -->
        <div v-if="!isPlaying" class="play-overlay" @click="togglePlay">
          <svg class="w-16 h-16" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z"/>
          </svg>
        </div>
      </div>

      <!-- Audio Controls -->
      <div class="audio-controls">
        <div class="progress-container">
          <div class="progress-bar-audio">
            <div class="progress-fill-audio" :style="{ width: audioProgress + '%' }"></div>
          </div>
        </div>

        <div class="controls-row">
          <button @click="togglePlay" class="control-button">
            <svg v-if="isPlaying" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
            </svg>
            <svg v-else class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5v14l11-7z" />
            </svg>
          </button>

          <span class="time-display">{{ currentTime }} / {{ duration }}</span>
        </div>
      </div>

      <!-- Podcast Info -->
      <div class="podcast-info">
        <h2 class="podcast-title">{{ props.podcast.title }}</h2>
        <p class="podcast-artist">{{ props.podcast.author?.name || 'Unknown Artist' }}</p>
        <p class="podcast-album ellipsis-2">{{ props.podcast.description }}</p>
      </div>

      <!-- Lyrics Display -->
      <div class="lyrics-container">
        <div ref="lyricsScrollRef" class="lyrics-scroll">
          <div
            v-for="(lyric, index) in props.podcast.lyrics || []"
            :key="index"
            class="lyric-line"
            :class="{
              'active': currentLyricIndex === index,
              'completed': currentLyricIndex > index
            }"
          >
            {{ lyric }}
          </div>
        </div>
      </div>
    </div>

    <!-- Comments Bottom Sheet -->
    <BottomControls
      :initial-liked="isLiked"
      :article-content="props.podcast"
      @like="handleLike"
      @comments="handleComment"
    />

    <!-- Hidden Audio Element -->
    <audio
      ref="audioPlayer"
      :src="props.podcast.audioUrl"
      @timeupdate="handleTimeUpdate"
      @loadedmetadata="handleAudioLoaded"
      @ended="handleAudioEnded"
      :muted="false"
    ></audio>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import BottomControls from './BottomControls.vue'
import { apiFetch } from '@/lib/api'
import { useAnalytics } from '@/composables/useAnalytics'

interface Props {
  podcast: any
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

const { trackAudioProgress } = useAnalytics()
const isSaved = computed(() => props.isSaved)

// Audio progress tracking — fire at 25%, 50%, 75%, 100% milestones
const _firedAudioMilestones = new Set<number>()
let _audioStartTime = 0

const handleSave = async () => {
  const id = props.podcast?.id ?? props.podcast?._id
  if (!id) return
  const collection = props.podcast?.collection ?? props.category ?? 'podcasts'
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
const audioProgress = ref(0)
const isLiked = ref(false)
const currentLyricIndex = ref(0)
const isVisible = ref(false)

const audioPlayer = ref<HTMLAudioElement>()
const lyricsScrollRef = ref<HTMLDivElement>()
const podcastContainer = ref<HTMLDivElement>()
let intersectionObserver: IntersectionObserver | null = null

const handleBack = () => {
  emit('back')
}

const handleFollow = () => {
  emit('follow', props.podcast.author?.username ?? '')
}

const playPodcast = () => {
  if (!audioPlayer.value) return
  audioPlayer.value.play().catch(error => {
    console.log('Play failed:', error)
  })
  isPlaying.value = true
  if (!_audioStartTime) _audioStartTime = performance.now()
}

const pausePodcast = () => {
  if (!audioPlayer.value) return
  audioPlayer.value.pause()
  isPlaying.value = false
}

const togglePlay = () => {
  if (!audioPlayer.value) return

  if (isPlaying.value) {
    pausePodcast()
  } else {
    playPodcast()
  }
}

const handleTimeUpdate = () => {
  if (!audioPlayer.value) return

  const current = audioPlayer.value.currentTime
  const total = audioPlayer.value.duration

  if (total > 0) {
    audioProgress.value = (current / total) * 100
    currentTime.value = formatTime(current)

    // Analytics: fire at 25/50/75/100% milestones
    const pct = Math.floor(audioProgress.value)
    for (const milestone of [25, 50, 75, 100]) {
      if (pct >= milestone && !_firedAudioMilestones.has(milestone)) {
        _firedAudioMilestones.add(milestone)
        const podcastId = String(props.podcast?.id ?? props.podcast?._id ?? '')
        const listenMs = _audioStartTime ? Math.round(performance.now() - _audioStartTime) : Math.round(current * 1000)
        trackAudioProgress(podcastId, milestone, listenMs, props.category)
      }
    }

    // Update lyric index based on progress
    // const lyrics = props.podcast.lyrics
    // const progressPerLyric = 100 / lyrics.length
    // const newLyricIndex = Math.floor(audioProgress.value / progressPerLyric)

    // if (newLyricIndex !== currentLyricIndex.value) {
    //   currentLyricIndex.value = newLyricIndex
    //   scrollToActiveLyric()
    // }
  }
}

const scrollToActiveLyric = () => {
  if (!lyricsScrollRef.value) return

  const activeElement = lyricsScrollRef.value.children[currentLyricIndex.value] as HTMLElement
  if (!activeElement) return

  const container = lyricsScrollRef.value
  const containerRect = container.getBoundingClientRect()
  const elementRect = activeElement.getBoundingClientRect()

  // Calculate the scroll position to center the active lyric
  const scrollTop = activeElement.offsetTop - container.offsetTop - (containerRect.height / 2) + (elementRect.height / 2)

  container.scrollTo({
    top: scrollTop,
    behavior: 'smooth'
  })
}

const handleAudioLoaded = () => {
  if (!audioPlayer.value) return
  duration.value = formatTime(audioPlayer.value.duration)
}

const handleAudioEnded = () => {
  isPlaying.value = false
  currentLyricIndex.value = 0
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
  console.log('Comments event emitted from PodcastView with content:', articleContent)
}

const handleShare = () => {
  console.log('Share clicked')
}

// Visibility detection for autoplay
const setupIntersectionObserver = () => {
  if (!podcastContainer.value) return

  intersectionObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          // Podcast is visible - play it
          isVisible.value = true
          nextTick(() => {
            playPodcast()
          })
        } else {
          // Podcast is not visible - pause it
          isVisible.value = false
          pausePodcast()
        }
      })
    },
    {
      threshold: 0.5, // Trigger when 50% of podcast is visible
      rootMargin: '0px'
    }
  )

  intersectionObserver.observe(podcastContainer.value)
}

onMounted(() => {
  console.log('PodcastView mounted', props.podcast)
  if (audioPlayer.value) {
    audioPlayer.value.addEventListener('play', () => {
      isPlaying.value = true
      scrollToActiveLyric()
    })
    audioPlayer.value.addEventListener('pause', () => {
      isPlaying.value = false
    })
  }

  // Scroll to active lyric on mount
  nextTick(() => {
    scrollToActiveLyric()
  })

  // Setup intersection observer for autoplay
  setupIntersectionObserver()
})

onUnmounted(() => {
  if (audioPlayer.value) {
    audioPlayer.value.removeEventListener('play', () => isPlaying.value = true)
    audioPlayer.value.removeEventListener('pause', () => isPlaying.value = false)
  }

  // Cleanup intersection observer
  if (intersectionObserver) {
    intersectionObserver.disconnect()
  }
})
</script>

<style scoped>
.podcast-container {
  @apply relative inset-0 bg-black;
  @apply flex flex-col;
  @apply touch-none;
  @apply h-full w-full;
  /* Mobile browser navigation bar handling */
  height: 100vh;
  height: 100dvh; /* Dynamic viewport height */
  min-height: -webkit-fill-available;
  /* Safe area insets for notched devices */
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
}

.podcast-header {
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

.podcast-content {
  @apply flex-1 relative;
  @apply flex flex-col items-center justify-center;
  @apply px-6;
}

.album-art-container {
  @apply relative flex justify-center items-center mt-16;
  @apply mb-6;
}

.album-art {
  @apply w-48 h-48;
  @apply rounded-lg;
  @apply object-cover;
  @apply shadow-lg;
}

.play-overlay {
  @apply absolute inset-0;
  @apply flex items-center justify-center;
  @apply bg-black bg-opacity-50;
  @apply rounded-lg;
  @apply cursor-pointer;
  @apply transition-opacity duration-200;
}

.play-overlay:hover {
  @apply bg-opacity-70;
}

.audio-controls {
  @apply w-full max-w-md mb-8;
}

.progress-container {

}

.progress-bar-audio {
  @apply w-full h-1 bg-gray-600 bg-opacity-30 rounded-full;
  @apply overflow-hidden;
}

.progress-fill-audio {
  @apply h-full bg-white;
  @apply transition-all duration-100 ease-out;
}

.controls-row {
  @apply flex items-center justify-between mt-2;
}

.control-button {
  @apply text-white hover:text-gray-300 transition-colors;
}

.time-display {
  @apply text-white text-sm;
}

.podcast-info {
  @apply text-center mb-3;
}

.podcast-title {
  @apply text-3xl font-bold text-white font-postoni
}

.podcast-artist {
  @apply text-lg text-gray-300;
}

.podcast-album {
  @apply text-sm text-gray-400;
}

.podcast-description {
  @apply text-sm text-gray-300;
  @apply max-w-md;
}

.lyrics-container {
  @apply w-full max-w-xl;
  @apply max-h-36 overflow-y-auto;
  @apply relative;
  scrollbar-width: 0px;
  -ms-overflow-style: none;
}

.lyrics-container::-webkit-scrollbar {
  display: none;
}

.lyrics-scroll {
  @apply space-y-2;
  @apply h-full overflow-y-auto;
  @apply scroll-smooth;
  @apply py-4;
}

.lyric-line {
  @apply text-center text-base;
  @apply transition-all duration-500 ease-out;
  @apply text-gray-400;
  @apply flex items-center justify-center;
}

.lyric-line.active {
  @apply text-white text-base font-semibold;
  @apply scale-125;
}

.lyric-line.completed {
  @apply text-gray-500;
  @apply scale-95;
}

.podcast-bottom {
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

.podcast-actions {
  @apply flex items-start space-x-4;
}

.podcast-action-btn {
  @apply flex items-center space-x-1 text-white;
  @apply cursor-pointer;
}

.podcast-action-btn.active {
  @apply text-accent;
}

.action-text {
  @apply font-medium text-sm;
}

.follow-button {
  @apply flex items-center px-3 py-1.5 bg-accent rounded-full;
  @apply text-white text-sm font-medium;
  @apply hover:bg-opacity-90 transition-colors;
}
</style>
