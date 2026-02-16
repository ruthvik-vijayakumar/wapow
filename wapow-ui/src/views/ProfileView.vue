<template>
  <div class="profile-container">
    <TopBar @menu="handleMenu" @notification="handleNotification" />

    <!-- Profile Info -->
    <div class="profile-info">
      <p v-if="apiError" class="text-amber-500 text-sm mb-2">{{ apiError }}</p>
      <div class="profile-avatar">
        <img
          :src="userProfile.avatar"
          :alt="userProfile.name"
          class="avatar-image"
        />
      </div>

      <div class="profile-details">
        <h2 class="user-name">{{ userProfile.name }}</h2>
        <p v-if="userProfile.email" class="user-email">{{ userProfile.email }}</p>
        <p v-if="userProfile.username && userProfile.username !== '@user'" class="user-username">{{ userProfile.username }}</p>
      </div>

      <!-- Theme Toggle -->
      <button class="theme-toggle" @click="toggleTheme" :title="isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'">
        <!-- Sun icon (shown in dark mode → click to switch to light) -->
        <svg v-if="isDark" class="toggle-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
        <!-- Moon icon (shown in light mode → click to switch to dark) -->
        <svg v-else class="toggle-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
      </button>
    </div>

    <!-- Menu Sections -->
    <div class="profile-menu">
      <!-- Reading Preferences -->
      <div class="menu-section">
        <h3 class="section-title">Reading Preferences</h3>
        <div class="menu-items">
          <button class="menu-item" @click="handleReadingPreferences">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <span>Reading Settings</span>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>

          <button class="menu-item" @click="handleCategories">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
            <span>Followed Categories</span>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Saved Content -->
      <div class="menu-section">
        <h3 class="section-title">Saved Content</h3>
        <div class="menu-items">
          <button class="menu-item" @click="handleSavedArticles">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
            </svg>
            <span>Saved Articles</span>
            <span class="badge">{{ userProfile.savedArticles }}</span>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>

          <button class="menu-item" @click="handlePinBoard">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
            </svg>
            <span>Pin Board</span>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>

          <button class="menu-item" @click="handleReadingHistory">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Reading History</span>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Account Settings -->
      <div class="menu-section">
        <h3 class="section-title">Account</h3>
        <div class="menu-items">
          <button class="menu-item" @click="handleAccountSettings">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span>Account Settings</span>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>

          <button class="menu-item" @click="handleNotifications">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-5 5v-5zM4.83 2.606a1 1 0 01.707-.293L9.414 2H20a1 1 0 011 1v12a1 1 0 01-1 1H5a1 1 0 01-1-1V3a1 1 0 01.83-.394z" />
            </svg>
            <span>Notifications</span>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>

          <button class="menu-item" @click="handlePrivacy">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            <span>Privacy & Security</span>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Sign Out -->
      <div class="menu-section">
        <button class="sign-out-btn" @click="handleSignOut">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          <span>Sign Out</span>
        </button>
      </div>
    </div>

    <BottomNavigation @navigate="handleNavigation" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import TopBar from '@/components/TopBar.vue'
import BottomNavigation from '@/components/BottomNavigation.vue'
import { useAuthStore } from '@/stores/auth'
import { apiFetch } from '@/lib/api'
import { useTheme } from '@/composables/useTheme'

const router = useRouter()
const authStore = useAuthStore()
const { isDark, toggleTheme } = useTheme()

const apiUser = ref<{ user_id?: string; sub?: string } | null>(null)
const apiError = ref<string | null>(null)
const savedArticlesCount = ref(0)

const userProfile = computed(() => {
  const u = authStore.user
  const email = u?.email ?? ''
  const sub = u?.sub ?? apiUser.value?.user_id ?? apiUser.value?.sub ?? ''
  const username = email ? `@${email.split('@')[0]}` : (sub ? `@${(sub.split('|').pop() ?? 'user').slice(0, 12)}` : '@user')
  return {
    name: u?.name ?? email.split('@')[0] ?? 'User',
    email,
    username,
    avatar: u?.picture ?? 'https://picsum.photos/100/100?random=user',
    savedArticles: savedArticlesCount.value,
  }
})

onMounted(async () => {
  try {
    const [meRes, savedRes] = await Promise.all([
      apiFetch('/api/me'),
      apiFetch('/api/saved-articles'),
    ])
    if (meRes.ok) {
      apiUser.value = await meRes.json()
    }
    if (savedRes.ok) {
      const savedJson = await savedRes.json()
      savedArticlesCount.value = savedJson.count ?? savedJson.data?.length ?? 0
    }
  } catch (e) {
    apiError.value = e instanceof Error ? e.message : 'Failed to fetch profile'
  }
})

const handleMenu = () => {
  router.push('/')
}

const handleNotification = () => {
  console.log('Notification clicked')
}

const handleNavigation = (route: string) => {
  switch (route) {
    case 'home':
      router.push('/')
      break
    case 'ask-ai':
      console.log('Navigate to Ask AI')
      break
    case 'games':
      console.log('Navigate to Games')
      break
    case 'profile':
      router.push('/profile')
      break
    default:
      console.log('Unknown route:', route)
  }
}

const handleReadingPreferences = () => {
  console.log('Reading preferences clicked')
}

const handleCategories = () => {
  console.log('Categories clicked')
}

const handleSavedArticles = () => {
  router.push('/saved')
}

const handlePinBoard = () => {
  router.push('/pin-board')
}

const handleReadingHistory = () => {
  console.log('Reading history clicked')
}

const handleAccountSettings = () => {
  console.log('Account settings clicked')
}

const handleNotifications = () => {
  console.log('Notifications clicked')
}

const handlePrivacy = () => {
  console.log('Privacy clicked')
}

const handleSignOut = async () => {
  await authStore.signOut()
  router.push('/login')
}
</script>

<style scoped>
.profile-container {
  min-height: 100vh;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  @apply flex flex-col;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.profile-info {
  @apply flex items-center space-x-4 px-4 py-6;
}

.profile-avatar {
  @apply flex-shrink-0;
}

.avatar-image {
  @apply w-20 h-20 rounded-full object-cover;
  border: 2px solid var(--border-secondary);
}

.profile-details {
  @apply flex-1;
}

.user-name {
  @apply text-2xl font-bold font-postoni;
  color: var(--text-primary);
}

.user-email {
  @apply text-sm;
  color: var(--text-secondary);
}

.user-username {
  @apply text-sm;
  color: var(--accent-text);
}

/* Theme Toggle Button */
.theme-toggle {
  @apply flex-shrink-0 p-2.5 rounded-full transition-all duration-300;
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
}

.theme-toggle:hover {
  background-color: var(--bg-hover);
  color: var(--text-primary);
}

.toggle-icon {
  @apply w-5 h-5;
}

.profile-menu {
  @apply flex-1 px-4 py-6;
  @apply space-y-6;
}

.menu-section {
  @apply space-y-3;
}

.section-title {
  @apply text-sm tracking-wide font-medium uppercase;
  color: var(--text-secondary);
}

.menu-items {
  @apply space-y-0;
}

.menu-item {
  @apply flex items-center justify-between w-full text-base;
  @apply px-0 py-3;
  @apply transition-colors duration-200;
  @apply text-left;
}

.menu-item svg:first-child {
  color: var(--text-secondary);
}

.menu-item span:nth-child(2) {
  @apply flex-1 ml-3 text-base;
  color: var(--text-primary);
}

.badge {
  line-height: 0;
  @apply text-white text-xs mr-1;
  @apply px-2 py-0.5 rounded-full;
  @apply font-medium;
  background-color: var(--accent);
}

.menu-item svg:last-child {
  color: var(--text-tertiary);
}

.sign-out-btn {
  @apply flex items-center w-full text-base;
  @apply px-0 py-3;
  @apply transition-colors duration-200;
  @apply text-red-400;
}

.sign-out-btn span {
  @apply ml-3;
}
</style>
