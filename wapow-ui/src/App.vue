<script setup lang="ts">
import { RouterView } from 'vue-router'
import { onMounted, watch } from 'vue'
import { useContentStore } from '@/stores/videos'
import { useAuthStore } from '@/stores/auth'
import { apiFetch } from '@/lib/api'
import { tracker } from '@/lib/analytics'
import { useTheme } from '@/composables/useTheme'

// Initialize theme (applies dark/light class to <html>)
useTheme()

// Initialise auth — must happen in setup so Auth0's inject() resolves
const authStore = useAuthStore()
authStore.init()

const contentStore = useContentStore()

// Start the analytics event tracker
tracker.start()

// Keep the analytics tracker in sync with the current user ID.
// Watching userId directly avoids timing issues where isAuthenticated
// becomes true before the user profile (and thus userId) is available.
watch(
  () => authStore.userId,
  (id) => {
    tracker.setUserId(id ?? '')
  },
  { immediate: true },
)

// When the user becomes authenticated, call /api/me to upsert user document in MongoDB
watch(
  () => authStore.isAuthenticated,
  async (authenticated) => {
    if (authenticated) {
      try {
        await apiFetch('/api/me')
      } catch {
        // Non-critical — user will be created on next interaction
      }
    }
  },
  { immediate: true },
)

onMounted(async () => {
  console.log('App mounted, initializing content store...')
  await contentStore.loadVideos()
  console.log('Content store initialized')
})
</script>

<template>
  <RouterView />
</template>

<style>
/* Global styles are handled in main.css */
</style>
