<template>
  <nav class="bottom-nav">
    <div class="flex justify-between items-center h-16 px-2">
      <!-- Home -->
      <button 
        class="nav-item"
        :class="{ 'active': currentRoute === 'home' }"
        @click="navigateTo('home')"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
        <span class="text-xs mt-1">Home</span>
      </button>

      <!-- Pin Board -->
      <button 
        class="nav-item"
        :class="{ 'active': currentRoute === 'pin-board' }"
        @click="navigateTo('pin-board')"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
        </svg>
        <span class="text-xs mt-1">Pin Board</span>
      </button>

      <!-- Ask AI -->
      <button
        class="nav-item"
        :class="{ 'active': currentRoute === 'ask-ai' }"
        @click="navigateTo('ask-ai')"
      >
        <div class="w-5 h-5 flex items-center justify-center">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>
        <span class="text-xs mt-1">Ask AI</span>
      </button>

      <!-- Games -->
      <button 
        class="nav-item"
        :class="{ 'active': currentRoute === 'games' }"
        @click="navigateTo('games')"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span class="text-xs mt-1">Games</span>
      </button>

      <!-- Profile -->
      <button 
        class="nav-item"
        :class="{ 'active': currentRoute === 'profile' }"
        @click="navigateTo('profile')"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
        <span class="text-xs mt-1">Profile</span>
      </button>

    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const currentRoute = computed(() => {
  const path = route.path
  if (path === '/profile') return 'profile'
  if (path === '/pin-board') return 'pin-board'
  // Story/article views: keep home active when reading content
  if (path.startsWith('/story/') || path.startsWith('/article/')) return 'home'
  // Category routes and root: /, /sports, /style, /technology, etc.
  if (path === '/' || path.split('/').filter(Boolean).length <= 1) return 'home'
  return ''
})

const emit = defineEmits<{
  navigate: [route: string]
}>()

const navigateTo = (navRoute: string) => {
  emit('navigate', navRoute)
}
</script>

<style scoped>
.bottom-nav {
  @apply fixed bottom-0 left-0 right-0;
  @apply bg-gray-900 border-t border-gray-700;
  @apply z-50;
  background-color: black;
}

.nav-item {
  @apply flex flex-col items-center justify-center;
  @apply px-2 py-1 rounded-lg;
  @apply text-gray-400 hover:text-white transition-colors;
  @apply min-w-0 flex-1;
}

.nav-item.active {
  @apply text-blue-400;
}

.nav-item svg {
  @apply transition-colors;
}
</style> 