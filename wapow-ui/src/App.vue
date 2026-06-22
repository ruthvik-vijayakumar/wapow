<script setup lang="ts">
import { RouterView } from 'vue-router'
import { onMounted, watch } from 'vue'
import { useContentStore } from '@/stores/content'
import { useAuthStore } from '@/stores/auth'
import { tracker } from '@/lib/analytics'
import { useTheme } from '@/composables/useTheme'

// Initialize theme (applies dark/light class to <html>)
useTheme()

// Initialise auth — must happen in setup so Auth0's inject() resolves
const authStore = useAuthStore()

const contentStore = useContentStore()

// Start the analytics event tracker
tracker.start()

// Synchronize analytics tracker user ID with Auth0 user ID
watch(
  () => authStore.userId,
  (userId) => {
    if (userId) {
      tracker.setUserId(userId)
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
