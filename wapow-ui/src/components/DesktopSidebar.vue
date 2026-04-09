<template>
  <aside class="desktop-sidebar">
    <div class="desktop-sidebar__inner">
      <button class="desktop-sidebar__brand" @click="goHome" type="button">
        <span class="desktop-sidebar__brand-text font-postoni">TunedIn</span>
      </button>

      <nav class="desktop-sidebar__nav" aria-label="Primary">
        <button class="desktop-sidebar__item" :class="{ active: isHome }" @click="goHome" type="button">
          <span class="desktop-sidebar__icon" aria-hidden="true">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
          </span>
          <span class="desktop-sidebar__label">Discover</span>
        </button>

        <button class="desktop-sidebar__item" :class="{ active: isSearch }" @click="goSearch" type="button">
          <span class="desktop-sidebar__icon" aria-hidden="true">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </span>
          <span class="desktop-sidebar__label">Search</span>
        </button>

        <button class="desktop-sidebar__item" :class="{ active: isAskAi }" @click="emit('navigate', 'ask-ai')" type="button">
          <span class="desktop-sidebar__icon" aria-hidden="true">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </span>
          <span class="desktop-sidebar__label">Ask AI</span>
        </button>

        <button class="desktop-sidebar__item" :class="{ active: isGames }" @click="emit('navigate', 'games')" type="button">
          <span class="desktop-sidebar__icon" aria-hidden="true">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </span>
          <span class="desktop-sidebar__label">Games</span>
        </button>

        <button class="desktop-sidebar__item" :class="{ active: isProfile }" @click="goProfile" type="button">
          <span class="desktop-sidebar__icon" aria-hidden="true">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
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
const isAskAi = computed(() => false)
const isGames = computed(() => false)
const isProfile = computed(() => route.path === '/profile')

const goHome = () => {
  router.push('/sports')
}
const goSearch = () => router.push('/search')
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
  padding: 1rem 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.desktop-sidebar__brand {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 0.5rem 0.5rem;
  border-radius: 0.75rem;
  color: var(--text-primary);
}

.desktop-sidebar__brand-text {
  font-size: 1.45rem;
  letter-spacing: 0.02em;
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
  gap: 0.75rem;
  width: 100%;
  padding: 0.625rem 0.75rem;
  border-radius: 0.75rem;
  color: var(--text-secondary);
  transition: background-color 0.2s ease, color 0.2s ease;
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
}

.desktop-sidebar__label {
  font-size: 0.95rem;
  font-weight: 600;
}

.desktop-sidebar__footer {
  margin-top: auto;
  padding-top: 0.5rem;
}
</style>
