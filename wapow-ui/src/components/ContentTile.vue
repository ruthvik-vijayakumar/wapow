<template>
  <div
    class="content-tile group cursor-pointer relative overflow-hidden"
    @click="handleClick"
    :class="{ 'clicked': isClicked }"
  >
    <!-- Ripple effect -->
    <div
      v-if="showRipple"
      class="ripple-effect"
      :style="{
        left: rippleX + 'px',
        top: rippleY + 'px',
        width: rippleSize + 'px',
        height: rippleSize + 'px'
      }"
    ></div>

    <div class="relative overflow-hidden rounded-lg" :style="{ aspectRatio: content.subtype === 'audio' ? '1.77' : '0.67' }">
      <!-- Thumbnail with lazy loading for performance -->
      <img
        :src="content.promo_items?.basic?.url"
        :alt="content.headlines?.basic || 'Article'"
        class="w-full h-full object-cover tile-image"
        :style="tileImageStyle"
        loading="lazy"
        decoding="async"
      />

      <!-- Time to read badge -->
      <!-- <div v-if="content.additional_properties?.time_to_read" class="absolute top-2 right-2 bg-black bg-opacity-70 text-white text-xs px-2 py-1 rounded">
        {{ content.additional_properties.time_to_read }}
      </div> -->

      <!-- Audio duration badge -->
      <!-- <div v-else-if="content.additional_properties?.time_to_listen" class="absolute top-2 right-2 bg-black bg-opacity-70 text-white text-xs px-2 py-1 rounded">
        {{ content.additional_properties.time_to_listen }}
      </div> -->

      <!-- Comments count badge -->
      <!-- <div v-if="content.comments?.display_comments" class="absolute bottom-2 left-2 bg-black bg-opacity-70 text-white text-xs px-2 py-1 rounded">
        Comments enabled
      </div> -->
    </div>

    <!-- Content info -->
    <div class="mt-2 space-y-1 px-2 pb-2">

      <!-- Section/Category -->
      <div class="flex items-center space-x-1 mb-1">
        <p class="text-xs tile-text-secondary">{{ getSectionName() }}</p>
      </div>

      <!-- Title -->
      <h3 style="font-size: 1.1rem; line-height: 1.2;" class="text-xl tracking-tight font-bold tile-text-primary font-postoni">
        {{ content.headlines?.basic || 'Article Title' }}
      </h3>

      <!-- Description -->
      <!-- <p class="text-xs text-gray-400 line-clamp-4">
        {{ content.description?.basic || 'Article description' }}
      </p> -->

      <!-- Author info -->
      <div v-if="content.subtype !== 'recipe-template'" class="flex items-center space-x-2 pt-2">
        <span class="text-xs tile-text-primary" style="opacity: 0.85;">by {{ getAuthorName() }}</span>
      </div>

      <!-- Published date -->
      <div v-if="content.publish_date && content.subtype !== 'recipe-template'" class="flex items-center space-x-2">
        <span class="text-xs tile-text-secondary">{{ formatTimeAgo(content.publish_date) }}</span>
      </div>

      <!-- Recipe-specific information -->
      <div v-if="content.subtype === 'recipe-template'" class="flex items-center space-x-2 pt-1">
        <!-- Total time -->
        <div  class="flex items-center space-x-1">
          <svg class="w-3 h-3 tile-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span class="text-xs tile-text-secondary">{{ getRecipeTotalTime() }}</span>
        </div>

        <!-- Course -->
        <div class="flex items-center space-x-1">
          <span class="text-xs tile-text-secondary">&bull;</span>
          <span class="text-xs tile-text-secondary">{{  content.taxonomy.tags[0].description || '' }}</span>
        </div>
      </div>

      <!-- Display date -->
      <!-- <div class="flex items-center space-x-2">
        <span class="text-xs text-gray-400">{{ formatDate(content.display_date) }}</span>
        <span v-if="content.additional_properties?.has_published_copy" class="text-xs text-blue-400">• Published</span>
      </div> -->

      <!-- Audio article indicator -->
      <!-- <div v-if="content.additional_properties?.audio_article?.enabled" class="flex items-center space-x-1 mt-1">
        <svg class="w-3 h-3 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
        </svg>
        <span class="text-xs text-blue-400">Listen</span>
      </div> -->
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Article } from '@/stores/content'
import { useRoute } from 'vue-router'

const route = useRoute()

interface Props {
  content: Article
  index?: number
}

const props = withDefaults(defineProps<Props>(), {
  index: 0
})

const emit = defineEmits<{
  click: [content: Article]
}>()

/** Compute object-position from focal point data for tile thumbnails */
const tileImageStyle = computed(() => {
  const fp = (props.content as any)?.promo_items?.basic?.focal_point
  if (!fp || !fp.focal_x || !fp.focal_y) {
    return {}
  }
  const x = Math.round((fp.focal_x ?? 0.5) * 100)
  const y = Math.round((fp.focal_y ?? 0.5) * 100)
  return { objectPosition: `${x}% ${y}%` }
})

// Transition state
const isClicked = ref(false)
const showRipple = ref(false)
const rippleX = ref(0)
const rippleY = ref(0)
const rippleSize = ref(0)

const handleClick = (event: MouseEvent) => {
  // Create ripple effect
  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
  const size = Math.max(rect.width, rect.height)

  rippleX.value = event.clientX - rect.left - size / 2
  rippleY.value = event.clientY - rect.top - size / 2
  rippleSize.value = size

  // Show ripple
  showRipple.value = true

  // Add click animation
  isClicked.value = true

  // Emit click event
  emit('click', props.content)

  // Reset animations after delay
  setTimeout(() => {
    isClicked.value = false
  }, 150)

  setTimeout(() => {
    showRipple.value = false
  }, 600)
}

const getSectionName = (): string => {
  return props.content.taxonomy?.primary_section?.name ||
         props.content.taxonomy?.sections?.[0]?.name ||
         props.content.type ||
         'News'
}

const getAuthorName = (): string => {
  const author = props.content.credits?.by?.[0]
  if (author) {
    return author.name ||
           `${author.additional_properties?.original?.firstName || ''} ${author.additional_properties?.original?.lastName || ''}`.trim() ||
           'Unknown Author'
  }
  return 'Unknown Author'
}

const getAuthorDesk = (): string => {
  const author = props.content.credits?.by?.[0]
  if (author) {
    return author.additional_properties?.original?.newsDesk ||
           author.additional_properties?.original?.subDesk ||
           ''
  }
  return ''
}

const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

const formatDuration = (seconds: number): string => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
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

const formatTimeAgo = (dateString: string | boolean): string => {
  if (!dateString || typeof dateString === 'boolean') return ''

  const date = new Date(dateString)
  const now = new Date()
  const diffInMs = now.getTime() - date.getTime()
  const diffInSeconds = Math.floor(diffInMs / 1000)
  const diffInMinutes = Math.floor(diffInSeconds / 60)
  const diffInHours = Math.floor(diffInMinutes / 60)
  const diffInDays = Math.floor(diffInHours / 24)
  const diffInWeeks = Math.floor(diffInDays / 7)
  const diffInMonths = Math.floor(diffInDays / 30)
  const diffInYears = Math.floor(diffInDays / 365)

  if (diffInSeconds < 60) {
    return 'Just now'
  } else if (diffInMinutes < 60) {
    return `${diffInMinutes}m ago`
  } else if (diffInHours < 24) {
    return `${diffInHours}h ago`
  } else if (diffInDays < 7) {
    return `${diffInDays}d ago`
  } else if (diffInWeeks < 4) {
    return `${diffInWeeks}w ago`
  } else if (diffInMonths < 12) {
    return `${diffInMonths}mo ago`
  } else {
    return `${diffInYears}y ago`
  }
}

const getCategoryEmoji = (category: string): string => {
  const emojiMap: { [key: string]: string } = {
    'Technology': '💻',
    'Climate': '🌍',
    'Space': '🚀',
    'Health': '🏥',
    'Economy': '📈',
    'Energy': '⚡',
    'Business': '💼',
    'Transportation': '🚗',
    'Security': '🔒',
    'Food': '🍽️',
    'Environment': '🌱',
    'Finance': '💰',
    'Education': '📚',
    'Agriculture': '🌾',
    'Politics': '🏛️',
    'Sports': '⚽',
    'Entertainment': '🎭',
    'Science': '🔬',
    'Travel': '✈️',
    'Fashion': '👗',
    'Music': '🎵',
    'Movie': '🎬',
    'Gaming': '🎮',
    'Weather': '🌤️',
    'Crime': '🚔'
  }
  return emojiMap[category] || '📰'
}

const getRecipeTotalTime = (): string => {
  // Check for total time in various possible locations
  // console.log(Object.keys(props.content.additional_properties))

  const additionalProps = props.content.additional_properties['recipes-info'] as any
  const totalTime = additionalProps?.total_time
  // console.log(totalTime)

  if (!totalTime) return ''

  // If it's already a formatted string, return it
  if (typeof totalTime === 'string') {
    return totalTime
  }

  // If it's a number (minutes), format it
  if (typeof totalTime === 'number') {
    if (totalTime < 60) {
      return `${totalTime}m`
    } else {
      const hours = Math.floor(totalTime / 60)
      const minutes = totalTime % 60
      return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`
    }
  }

  return ''
}

</script>

<style scoped>
.tile-text-primary {
  color: var(--text-primary);
}

.tile-text-secondary {
  color: var(--text-secondary);
}

.content-tile {
  @apply rounded-lg overflow-hidden;
  @apply relative;
  background-color: var(--bg-elevated);
  width: 100%;
  box-sizing: border-box;
}

/* Only enable hover effects on devices that support hover (not touch) */
@media (hover: hover) {
  .content-tile {
    @apply transition-transform duration-200 ease-out;
  }
  .content-tile:hover {
    transform: scale(1.02) translateZ(0);
  }
}

.content-tile.clicked {
  transform: scale(0.98) translateZ(0);
}

.ripple-effect {
  @apply absolute rounded-full bg-white bg-opacity-20;
  @apply pointer-events-none;
  @apply z-10;
  animation: rippleExpand 0.4s ease-out forwards;
}

/* GPU-accelerated image scaling on hover */
.tile-image {
  transform: translateZ(0);
  will-change: transform;
}

@media (hover: hover) {
  .content-tile:hover .tile-image {
    transform: scale(1.03) translateZ(0);
    transition: transform 0.2s ease-out;
  }
}

@keyframes rippleExpand {
  0% {
    transform: scale(0);
    opacity: 0.5;
  }
  100% {
    transform: scale(2);
    opacity: 0;
  }
}

.line-clamp-4 {
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
