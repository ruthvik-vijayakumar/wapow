<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

onMounted(async () => {
  try {
    const result = await authStore.handleRedirectCallback()
    const redirect = (result?.appState as { target?: string })?.target || '/'
    router.replace(redirect)
  } catch (error) {
    console.error('Auth callback error:', error)
    router.replace('/')
  }
})
</script>

<template>
  <div class="flex min-h-screen items-center justify-center">
    <p>Signing you in...</p>
  </div>
</template>
