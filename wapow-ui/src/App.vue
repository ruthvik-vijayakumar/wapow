<script setup lang="ts">
import { RouterView } from 'vue-router'
import { onMounted, watch } from 'vue'
import { useContentStore } from '@/stores/content'
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

// When the user becomes authenticated, call /api/me to upsert user document
// in MongoDB and use the returned _id for the analytics tracker.
watch(
  () => authStore.isAuthenticated,
  async (authenticated) => {
    if (authenticated) {
      try {
        const res = await apiFetch('/api/me')
        const data = await res.json()
        if (data._id) {
          authStore.setMongoId(data._id)
          tracker.setUserId(data._id)
        }
      } catch {
        // Non-critical — user will be created on next interaction
      }
    } else {
      tracker.setUserId('')
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
