<template>
  <header class="top-bar px-4 py-3">
    <div class="flex items-center justify-between">
      <!-- Left side - Menu -->
      <div class="flex items-center w-12">
        <button 
          class="top-bar-btn"
          @click="handleMenu"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </div>

      <!-- Center - Brand -->
      <div class="flex items-center justify-center flex-1">
        <span class="top-bar-brand font-postoni">WaPOW</span>
      </div>

      <!-- Right side - Notification -->
      <div class="flex items-center justify-end w-12">
        <button 
          class="top-bar-btn"
          @click="handleNotification"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 15V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v4c0 .386-.146.735-.405 1.005L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
        </button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">

const emit = defineEmits<{
  menu: []
  notification: []
}>()

const handleMenu = () => {
  emit('menu')
}

const handleNotification = () => {
  emit('notification')
}
</script>

<style scoped>
.top-bar {
  background-color: var(--bg-primary);
  border-bottom: 1px solid var(--border-primary);
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.top-bar-btn {
  color: var(--text-primary);
  transition: color 0.2s;
}

.top-bar-btn:hover {
  color: var(--text-secondary);
}

.top-bar-brand {
  color: var(--text-primary);
  @apply text-xl tracking-wide;
  transition: color 0.3s ease;
}
</style>
