<template>
  <nav class="bottom-nav">
    <div class="flex justify-between items-center h-16 px-2">
      <!-- Home -->
      <button
        class="nav-item"
        :class="{ active: currentRoute === 'home' }"
        @click="navigateTo('home')"
      >
        <svg class="w-[18px] h-[18px]" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25"
          />
        </svg>
        <span class="text-[10px] mt-1 font-medium">Home</span>
      </button>

      <!-- Search -->
      <button
        class="nav-item"
        :class="{ active: currentRoute === 'search' }"
        @click="navigateTo('search')"
      >
        <svg class="w-[18px] h-[18px]" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.637 10.637z"
          />
        </svg>
        <span class="text-[10px] mt-1 font-medium">Search</span>
      </button>

      <!-- Games -->
      <button
        class="nav-item"
        :class="{ active: currentRoute === 'games' }"
        @click="navigateTo('games')"
      >
        <svg class="w-[18px] h-[18px]" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M15.59 14.37a6 6 0 01-7.18 0M3 12a9 9 0 1118 0 9 9 0 01-18 0z"
          />
        </svg>
        <span class="text-[10px] mt-1 font-medium">Games</span>
      </button>

      <!-- Profile -->
      <button
        class="nav-item"
        :class="{ active: currentRoute === 'profile' }"
        @click="navigateTo('profile')"
      >
        <svg class="w-[18px] h-[18px]" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"
          />
        </svg>
        <span class="text-[10px] mt-1 font-medium">Profile</span>
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
  if (path === '/search') return 'search'
  if (path === '/games') return 'games'
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
  @apply z-50;
  background-color: var(--bg-primary);
  border-top: 1px solid var(--border-primary);
  transition:
    background-color 0.3s ease,
    border-color 0.3s ease;
}

.nav-item {
  @apply flex flex-col items-center justify-center;
  @apply px-2 py-2;
  @apply transition-colors;
  @apply min-w-0 flex-1;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  cursor: pointer;
}

.nav-item:hover {
  color: var(--text-primary);
}

.nav-item.active {
  color: var(--accent-text);
}

.nav-item svg {
  @apply transition-colors;
}
</style>

