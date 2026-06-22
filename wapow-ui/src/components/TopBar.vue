<template>
  <header class="top-bar px-4 py-3">
    <div class="flex items-center justify-between">
      <!-- Left side - Menu -->
      <div class="flex items-center w-12">
        <button class="top-bar-btn" @click="handleMenu">
          <svg class="w-[18px] h-[18px]" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
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
          <svg class="w-[18px] h-[18px]" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.637 10.637z"
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
  background: transparent;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
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

