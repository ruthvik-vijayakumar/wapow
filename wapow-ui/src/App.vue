<script setup lang="ts">
import { RouterView } from 'vue-router'
import { onMounted, watch } from 'vue'
import { useContentStore } from '@/stores/videos'
import { useAuthStore } from '@/stores/auth'
import { apiFetch } from '@/lib/api'

// Initialise auth — must happen in setup so Auth0's inject() resolves
const authStore = useAuthStore()
authStore.init()

const contentStore = useContentStore()

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
