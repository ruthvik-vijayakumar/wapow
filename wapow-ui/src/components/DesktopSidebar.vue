<template>
  <aside class="desktop-sidebar">
    <div class="desktop-sidebar__inner">
      <button class="desktop-sidebar__brand" @click="goHome" type="button">
        <svg class="w-5 h-5 text-current mr-2 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
          <path d="M4 10v4M8 6v12M12 4v16M16 8v8M20 11v2" />
        </svg>
        <span class="desktop-sidebar__brand-text font-postoni font-bold">TunedIn</span>
      </button>

      <nav class="desktop-sidebar__nav" aria-label="Primary">
        <button class="desktop-sidebar__item" :class="{ active: isHome }" @click="goHome" type="button">
          <span class="desktop-sidebar__icon" aria-hidden="true">
            <svg class="w-[18px] h-[18px]" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
            </svg>
          </span>
          <span class="desktop-sidebar__label">Discover</span>
        </button>

        <button class="desktop-sidebar__item" :class="{ active: isSearch }" @click="goSearch" type="button">
          <span class="desktop-sidebar__icon" aria-hidden="true">
            <svg class="w-[18px] h-[18px]" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.637 10.637z" />
            </svg>
          </span>
          <span class="desktop-sidebar__label">Search</span>
        </button>

        <button class="desktop-sidebar__item" :class="{ active: isTopics }" @click="goTopics" type="button">
          <span class="desktop-sidebar__icon" aria-hidden="true">
            <svg class="w-[18px] h-[18px]" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581a1.125 1.125 0 001.591 0l7.181-7.181a1.125 1.125 0 000-1.591l-9.581-9.581A1.125 1.125 0 0011.159 3H9.57z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 6h.008v.008H6V6z" />
            </svg>
          </span>
          <span class="desktop-sidebar__label">Topics</span>
        </button>

        <button class="desktop-sidebar__item" :class="{ active: isGames }" @click="emit('navigate', 'games')" type="button">
          <span class="desktop-sidebar__icon" aria-hidden="true">
            <svg class="w-[18px] h-[18px]" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.59 14.37a6 6 0 01-7.18 0M3 12a9 9 0 1118 0 9 9 0 01-18 0z" />
            </svg>
          </span>
          <span class="desktop-sidebar__label">Games</span>
        </button>

        <button class="desktop-sidebar__item" :class="{ active: isProfile }" @click="goProfile" type="button">
          <span class="desktop-sidebar__icon" aria-hidden="true">
            <svg class="w-[18px] h-[18px]" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
            </svg>
          </span>
          <span class="desktop-sidebar__label">Profile</span>
        </button>
      </nav>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const emit = defineEmits<{
  navigate: [route: string]
}>()

const router = useRouter()
const route = useRoute()

const isHome = computed(() => route.path === '/' || route.path.split('/').filter(Boolean).length <= 1)
const isSearch = computed(() => route.path === '/search')
const isTopics = computed(() => route.path === '/topics')
const isGames = computed(() => false)
const isProfile = computed(() => route.path === '/profile')

const goHome = () => {
  router.push('/sports')
}
const goSearch = () => router.push('/search')
const goTopics = () => router.push('/topics')
const goProfile = () => router.push('/profile')
</script>

<style scoped>
.desktop-sidebar {
  width: 240px;
  background: var(--bg-primary);
  border-right: 1px solid var(--border-primary);
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.desktop-sidebar__inner {
  position: sticky;
  top: 0;
  height: 100vh;
  padding: 1.5rem 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.desktop-sidebar__brand {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 0.25rem 0.5rem;
  border-radius: 0.375rem;
  color: var(--text-primary);
  background: transparent;
  border: none;
  cursor: pointer;
  width: 100%;
}

.desktop-sidebar__brand-text {
  font-size: 1.25rem;
  letter-spacing: -0.015em;
  font-weight: bold;
}

.desktop-sidebar__nav {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.desktop-sidebar__item,
.desktop-sidebar__more {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  width: 100%;
  padding: 0.5rem 0.625rem;
  border-radius: 0.375rem;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.desktop-sidebar__item:hover,
.desktop-sidebar__more:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.desktop-sidebar__item.active {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.desktop-sidebar__icon {
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  color: inherit;
}

.desktop-sidebar__label {
  font-size: 0.875rem;
  font-weight: 500;
}

.desktop-sidebar__footer {
  margin-top: auto;
  padding-top: 0.5rem;
}
</style>

