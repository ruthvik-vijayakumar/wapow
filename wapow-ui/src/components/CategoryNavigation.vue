<template>
  <div class="cat-nav-container">
    <div class="flex overflow-x-scroll scrollbar-hide">
      <div class="flex space-x-2 px-4 py-3">
        <button
          v-for="category in categories"
          :key="category.id"
          class="nav-category whitespace-nowrap"
          :class="{ 'active': selectedCategory === category.id }"
          @click="selectCategory(category)"
        >
          <span class="category-name">{{ category.name }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

interface Category {
  id: string
  canonical_url: string
  name: string
  emoji: string
}

const categories: Category[] = [
  { id: '/sports', canonical_url: '/sports', name: 'Sports', emoji: '' },
  { id: '/style', canonical_url: '/style', name: 'Style', emoji: '' },
  { id: '/technology', canonical_url: '/technology', name: 'Technology', emoji: '' },
  { id: '/wellbeing', canonical_url: '/wellbeing', name: 'Well Being', emoji: '' },
  { id: '/travel', canonical_url: '/travel', name: 'Travel', emoji: '' },
]

const selectedCategory = ref('/sports')

watch(() => route.path, (newPath) => {
  const matchingCategory = categories.find(cat => cat.canonical_url === newPath)
  if (matchingCategory) {
    selectedCategory.value = matchingCategory.id
  }
}, { immediate: true })

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
