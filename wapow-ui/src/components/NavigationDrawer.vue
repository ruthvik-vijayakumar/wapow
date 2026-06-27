<template>
  <div
    class="fixed inset-0 z-[100] flex transition-[visibility] duration-300"
    :class="isOpen ? 'visible' : 'invisible'"
  >
    <!-- Backdrop -->
    <div
      class="absolute inset-0 bg-black/45 backdrop-blur-[4px] transition-opacity duration-300 ease-out"
      :class="isOpen ? 'opacity-100' : 'opacity-0'"
      @click="emit('close')"
    ></div>

    <!-- Side Panel -->
    <aside
      class="absolute top-0 bottom-0 left-0 w-[260px] bg-[var(--bg-primary)] border-r border-[var(--border-primary)] flex flex-col shadow-[4px_0_12px_rgba(0,0,0,0.15)] transition-transform duration-300 ease-[cubic-bezier(0.4,0,0.2,1)]"
      :class="isOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <!-- Header / User Info -->
      <div class="py-5 px-4 border-b border-[var(--border-primary)] flex items-center justify-between">
        <div class="flex items-center gap-2.5 min-w-0">
          <img
            :src="userProfile.avatar"
            :alt="userProfile.name"
            class="w-9 h-9 rounded-full object-cover border border-[var(--border-secondary)]"
          />
          <div class="min-w-0">
            <h3 class="text-[0.9rem] font-semibold text-[var(--text-primary)] truncate">{{ userProfile.name }}</h3>
            <p class="text-[0.7rem] text-[var(--text-secondary)] truncate">{{ userProfile.email }}</p>
          </div>
        </div>
        <button
          class="bg-transparent border-none text-[var(--text-secondary)] cursor-pointer p-1 transition-colors duration-200 flex items-center justify-center hover:text-[var(--text-primary)]"
          @click="emit('close')"
          aria-label="Close menu"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Navigation Links -->
      <nav class="flex-1 py-4 px-2.5 flex flex-col gap-1">
        <button
          class="group flex items-center gap-2.5 py-2 px-2.5 rounded-md bg-transparent border-none cursor-pointer w-full text-left transition-all duration-150"
          :class="isDiscoverActive ? 'bg-[var(--bg-hover)]' : 'hover:bg-[var(--bg-hover)]'"
          @click="navigate('/')"
        >
          <svg
            class="w-[18px] h-[18px] transition-colors duration-150 flex items-center justify-center shrink-0"
            :class="isDiscoverActive ? 'text-[var(--text-primary)]' : 'text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]'"
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
          </svg>
          <span class="text-[var(--text-primary)] text-sm font-medium">Discover</span>
        </button>

        <button
          class="group flex items-center gap-2.5 py-2 px-2.5 rounded-md bg-transparent border-none cursor-pointer w-full text-left transition-all duration-150"
          :class="currentPath === '/topics' ? 'bg-[var(--bg-hover)]' : 'hover:bg-[var(--bg-hover)]'"
          @click="navigate('/topics')"
        >
          <svg
            class="w-[18px] h-[18px] transition-colors duration-150 flex items-center justify-center shrink-0"
            :class="currentPath === '/topics' ? 'text-[var(--text-primary)]' : 'text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]'"
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581a1.125 1.125 0 001.591 0l7.181-7.181a1.125 1.125 0 000-1.591l-9.581-9.581A1.125 1.125 0 0011.159 3H9.57z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 6h.008v.008H6V6z" />
          </svg>
          <span class="text-[var(--text-primary)] text-sm font-medium">Topics</span>
        </button>

        <button
          class="group flex items-center gap-2.5 py-2 px-2.5 rounded-md bg-transparent border-none cursor-pointer w-full text-left transition-all duration-150"
          :class="currentPath === '/games' ? 'bg-[var(--bg-hover)]' : 'hover:bg-[var(--bg-hover)]'"
          @click="navigate('/games')"
        >
          <svg
            class="w-[18px] h-[18px] transition-colors duration-150 flex items-center justify-center shrink-0"
            :class="currentPath === '/games' ? 'text-[var(--text-primary)]' : 'text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]'"
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.59 14.37a6 6 0 01-7.18 0M3 12a9 9 0 1118 0 9 9 0 01-18 0z" />
          </svg>
          <span class="text-[var(--text-primary)] text-sm font-medium">Games</span>
        </button>

        <button
          class="group flex items-center gap-2.5 py-2 px-2.5 rounded-md bg-transparent border-none cursor-pointer w-full text-left transition-all duration-150"
          :class="currentPath === '/pin-board' ? 'bg-[var(--bg-hover)]' : 'hover:bg-[var(--bg-hover)]'"
          @click="navigate('/pin-board')"
        >
          <svg
            class="w-[18px] h-[18px] transition-colors duration-150 flex items-center justify-center shrink-0"
            :class="currentPath === '/pin-board' ? 'text-[var(--text-primary)]' : 'text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]'"
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
          </svg>
          <span class="text-[var(--text-primary)] text-sm font-medium">Pin Board</span>
        </button>

        <button
          class="group flex items-center gap-2.5 py-2 px-2.5 rounded-md bg-transparent border-none cursor-pointer w-full text-left transition-all duration-150"
          :class="currentPath === '/profile' ? 'bg-[var(--bg-hover)]' : 'hover:bg-[var(--bg-hover)]'"
          @click="navigate('/profile')"
        >
          <svg
            class="w-[18px] h-[18px] transition-colors duration-150 flex items-center justify-center shrink-0"
            :class="currentPath === '/profile' ? 'text-[var(--text-primary)]' : 'text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]'"
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
          </svg>
          <span class="text-[var(--text-primary)] text-sm font-medium">Profile Settings</span>
        </button>
      </nav>

      <!-- Footer / Actions -->
      <div class="py-4 px-2.5 border-t border-[var(--border-primary)] flex flex-col gap-1">
        <!-- Theme Toggle -->
        <button
          class="group flex items-center gap-2.5 py-2 px-2.5 rounded-md bg-transparent border-none cursor-pointer w-full text-left transition-all duration-150 hover:bg-[var(--bg-hover)]"
          @click="toggleTheme"
        >
          <!-- Sun icon (shown in dark mode) -->
          <svg
            v-if="isDark"
            class="w-[18px] h-[18px] text-[var(--text-secondary)] transition-colors duration-150 flex items-center justify-center shrink-0 group-hover:text-[var(--text-primary)]"
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <!-- Moon icon (shown in light mode) -->
          <svg
            v-else
            class="w-[18px] h-[18px] text-[var(--text-secondary)] transition-colors duration-150 flex items-center justify-center shrink-0 group-hover:text-[var(--text-primary)]"
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
          </svg>
          <span class="text-[var(--text-primary)] text-sm font-medium">{{ isDark ? 'Light Mode' : 'Dark Mode' }}</span>
        </button>

        <!-- Sign Out -->
        <button
          class="group flex items-center gap-2.5 py-2 px-2.5 rounded-md bg-transparent border-none cursor-pointer w-full text-left transition-all duration-150 hover:bg-red-500/10"
          @click="handleSignOut"
        >
          <svg
            class="w-[18px] h-[18px] text-red-500 transition-colors duration-150 flex items-center justify-center shrink-0"
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          <span class="text-red-500 text-sm font-medium">Sign Out</span>
        </button>
      </div>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useTheme } from '@/composables/useTheme'

defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const { isDark, toggleTheme } = useTheme()

const currentPath = computed(() => route.path)
const isDiscoverActive = computed(() => {
  const path = currentPath.value
  return path === '/' || path.split('/').filter(Boolean).length <= 1 && path !== '/profile' && path !== '/pin-board' && path !== '/topics'
})

const userProfile = computed(() => {
  const u = authStore.user
  const email = u?.email ?? ''
  return {
    name: u?.name || email.split('@')[0] || 'User',
    email: email || 'Sign in to sync your board',
    avatar: u?.picture || 'https://picsum.photos/100/100?random=user'
  }
})

const navigate = (path: string) => {
  emit('close')
  router.push(path)
}

const handleSignOut = async () => {
  emit('close')
  await authStore.signOut()
  router.push('/login')
}
</script>
