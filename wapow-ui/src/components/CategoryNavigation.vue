<template>
  <div ref="navContainer" class="cat-nav-container">
    <div class="flex overflow-x-scroll scrollbar-hide">
      <div class="flex space-x-2 px-4 py-3">
        <button
          v-for="category in categories"
          :key="category.id"
          class="nav-category whitespace-nowrap"
          :class="{ active: selectedCategory === category.id }"
          @click="selectCategory(category)"
        >
          <span class="category-icon shrink-0">
            <svg v-if="category.id === '/sports'" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 9l3 2v3H9v-3Z" />
              <path d="M12 9V2M15 11l5.66-4M9 11L3.34 7M15 14l3.5 5.5M9 14L5.5 19.5" />
            </svg>
            <svg v-else-if="category.id === '/style'" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round">
              <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
              <path d="m5 3 1 2.5L8.5 6 6 7 5 9.5 4 7 1.5 6 4 5 5 3Z" />
              <path d="m19 17 1 2.5 2.5.5-2.5 1-1 2.5-1-2.5-2.5-1 2.5-1 1-2.5Z" />
            </svg>
            <svg v-else-if="category.id === '/technology'" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round">
              <rect x="4" y="4" width="16" height="16" rx="2" />
              <path d="M9 9h6v6H9z" />
              <path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 15h3M1 9h3M1 15h3" />
            </svg>
            <svg v-else-if="category.id === '/wellbeing'" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 3c-1.5 3-3.5 7-3.5 10 0 3 2 5 3.5 6 1.5-1 3.5-3 3.5-6 0-3-2-7-3.5-10Z" />
              <path d="M12 10c-3-1-6.5-.5-8 2-1.5 2.5-.5 5.5 2.5 6.5 2 .7 4.5-.5 5.5-2" />
              <path d="M12 10c3-1 6.5-.5 8 2 1.5 2.5.5 5.5-2.5 6.5-2 .7-4.5-.5-5.5-2" />
              <path d="M4 21c4 2 12 2 16 0" />
            </svg>
            <svg v-else-if="category.id === '/travel'" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L14 19v-5.5l8 2.5z" />
            </svg>
            <svg v-else-if="category.id === '/arts-entertainment'" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 18V5l12-2v13" />
              <circle cx="6" cy="18" r="3" />
              <circle cx="18" cy="16" r="3" />
            </svg>
            <svg v-else-if="category.id === '/business'" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="7" width="18" height="13" rx="2" />
              <path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              <path d="M3 13h18" />
            </svg>
          </span>
          <span class="category-name">{{ category.name }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const navContainer = ref<HTMLElement | null>(null)

interface Category {
  id: string
  canonical_url: string
  name: string
}

const categories: Category[] = [
  { id: '/sports', canonical_url: '/sports', name: 'Sports' },
  { id: '/style', canonical_url: '/style', name: 'Style' },
  { id: '/technology', canonical_url: '/technology', name: 'Technology' },
  { id: '/wellbeing', canonical_url: '/wellbeing', name: 'Well Being' },
  { id: '/travel', canonical_url: '/travel', name: 'Travel' },
  { id: '/arts-entertainment', canonical_url: '/arts-entertainment', name: 'Arts & Entertainment' },
  { id: '/business', canonical_url: '/business', name: 'Business' },
]

const selectedCategory = ref('/sports')

watch(
  () => route.path,
  (newPath) => {
    const matchingCategory = categories.find((cat) => cat.canonical_url === newPath)
    if (matchingCategory) {
      selectedCategory.value = matchingCategory.id
    }
  },
  { immediate: true },
)

watch(
  () => selectedCategory.value,
  async () => {
    await nextTick()
    if (navContainer.value) {
      const activeEl = navContainer.value.querySelector('.nav-category.active')
      if (activeEl) {
        activeEl.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' })
      }
    }
  }
)

const selectCategory = (category: Category) => {
  selectedCategory.value = category.id
  router.push(category.canonical_url)
}
</script>

<style scoped>
.cat-nav-container {
  background-color: var(--bg-primary);
  transition: background-color 0.3s ease;
}

.nav-category {
  @apply px-3 py-1.5 rounded-full text-sm transition-all duration-200;
  @apply flex items-center space-x-1;
  color: var(--cat-inactive-text);
}

.nav-category:hover {
  color: var(--text-primary);
}

.nav-category.active {
  background-color: var(--cat-active-bg);
  color: var(--cat-active-text);
  @apply font-semibold;
}

.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
</style>
