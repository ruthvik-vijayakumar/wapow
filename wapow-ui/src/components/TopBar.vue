<template>
  <header class="top-bar px-4 py-3">
    <div class="flex items-center justify-between">
      <!-- Left side - Menu -->
      <div class="flex items-center w-12">
        <button class="top-bar-btn" @click="handleMenu">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 6h16M4 12h16M4 18h16"
            />
          </svg>
        </button>
      </div>

      <!-- Center - Brand -->
      <div class="flex items-center justify-center flex-1">
        <span class="top-bar-brand font-postoni font-bold">TunedIn</span>
      </div>

      <!-- Right side - Search -->
      <div class="flex items-center justify-end w-12">
        <button class="top-bar-btn" @click="handleSearch">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
const emit = defineEmits<{
  menu: []
  search: []
}>()

const handleMenu = () => {
  emit('menu')
}

const handleSearch = () => {
  emit('search')
}
</script>

<style scoped>
.top-bar {
  background-color: var(--bg-primary);
  border-bottom: 1px solid var(--border-primary);
  transition:
    background-color 0.3s ease,
    border-color 0.3s ease;
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
  @apply text-lg tracking-wide font-bold;
  transition: color 0.3s ease;
}
</style>
