<template>
  <div class="bg-black">
    <div class="flex overflow-x-scroll scrollbar-hide">
      <div class="flex space-x-2 px-4 py-3">
        <button
          v-for="category in categories"
          :key="category.id"
          class="nav-category whitespace-nowrap"
          :class="{ 'active': selectedCategory === category.id }"
          @click="selectCategory(category)"
        >
          <!-- <span class="category-emoji">{{ category.emoji }}</span> -->
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
  canonical_url: string  // Router path
  name: string
  emoji: string
}

const categories: Category[] = [
  { id: '/sports', canonical_url: '/sports', name: 'Sports', emoji: '⚽' },
  { id: '/style', canonical_url: '/style', name: 'Style', emoji: '👗' },
  // { id: '/recipes', canonical_url: '/recipes', name: 'Recipes', emoji: '🍳' },
  { id: '/technology', canonical_url: '/technology', name: 'Technology', emoji: '💻' },
  { id: '/wellbeing', canonical_url: '/wellbeing', name: 'Well Being', emoji: '🧘' },
  { id: '/travel', canonical_url: '/travel', name: 'Travel', emoji: '✈️' },
  // { id: '/podcasts', canonical_url: '/podcasts', name: 'Podcasts', emoji: '🎧' },
]

const selectedCategory = ref('/sports')

// Watch for route changes and sync selected category
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
.nav-category {
  @apply px-3 py-1.5 rounded-full text-sm transition-all duration-200;
  @apply text-gray-400 hover:text-white;
  @apply flex items-center space-x-1;
}

.nav-category.active {
  @apply bg-white text-black font-semibold;
}

.category-emoji {
  @apply text-base;
}

.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
</style> 