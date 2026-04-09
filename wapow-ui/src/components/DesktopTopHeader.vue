<template>
  <header class="desktop-header">
    <div class="desktop-header__inner">
      <div class="desktop-header__left">
        <slot name="left" />
      </div>

      <div class="desktop-header__center">
        <form class="desktop-header__search" role="search" @submit.prevent="submit">
          <svg class="desktop-header__search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            v-model="query"
            class="desktop-header__search-input"
            type="search"
            placeholder="Search"
            autocomplete="off"
          />
        </form>
      </div>

      <div class="desktop-header__right">
        <!-- intentionally empty to keep centered search layout -->
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  search: [query: string]
}>()

const query = ref('')

const submit = () => {
  emit('search', query.value.trim())
}
</script>

<style scoped>
.desktop-header {
  position: sticky;
  top: 0;
  z-index: 40;
  background: color-mix(in srgb, var(--bg-primary) 85%, transparent);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border-primary);
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.desktop-header__inner {
  display: grid;
  grid-template-columns: 1fr minmax(360px, 520px) 1fr;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1.25rem;
}

.desktop-header__left {
  min-width: 0;
}
.desktop-header__center {
  display: flex;
  justify-content: center;
}
.desktop-header__right {
  min-height: 1px;
}

.desktop-header__search {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: 999px;
  background: var(--bg-input);
  border: 1px solid var(--border-primary);
}

.desktop-header__search-icon {
  width: 18px;
  height: 18px;
  color: var(--text-tertiary);
}

.desktop-header__search-input {
  width: 100%;
  background: transparent;
  outline: none;
  color: var(--text-primary);
  font-size: 0.95rem;
}
.desktop-header__search-input::placeholder {
  color: var(--text-tertiary);
}

</style>
