<template>
  <div
    class="drawer-wrapper"
    :class="{ 'is-open': isOpen }"
  >
    <!-- Backdrop -->
    <div
      class="drawer-backdrop"
      @click="emit('close')"
    ></div>

    <!-- Side Panel -->
    <aside class="drawer-panel">
      <!-- Header / User Info -->
      <div class="drawer-header">
        <div class="user-profile">
          <img
            :src="userProfile.avatar"
            :alt="userProfile.name"
            class="user-avatar"
          />
          <div class="user-details">
            <h3 class="user-name">{{ userProfile.name }}</h3>
            <p class="user-email">{{ userProfile.email }}</p>
          </div>
        </div>
        <button
          class="close-btn"
          @click="emit('close')"
          aria-label="Close menu"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Navigation Links -->
      <nav class="drawer-nav">
        <button
          class="nav-link"
          :class="{ active: isDiscoverActive }"
          @click="navigate('/')"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          <span>Discover</span>
        </button>

        <button
          class="nav-link"
          :class="{ active: currentPath === '/pin-board' }"
          @click="navigate('/pin-board')"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
          </svg>
          <span>Pin Board</span>
        </button>

        <button
          class="nav-link"
          :class="{ active: currentPath === '/profile' }"
          @click="navigate('/profile')"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          <span>Profile Settings</span>
        </button>
      </nav>

      <!-- Footer / Actions -->
      <div class="drawer-footer">
        <!-- Theme Toggle -->
        <button
          class="footer-action"
          @click="toggleTheme"
        >
          <!-- Sun icon (shown in dark mode) -->
          <svg v-if="isDark" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <!-- Moon icon (shown in light mode) -->
          <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
          </svg>
          <span>{{ isDark ? 'Light Mode' : 'Dark Mode' }}</span>
        </button>

        <!-- Sign Out -->
        <button
          class="footer-action sign-out"
          @click="handleSignOut"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useTheme } from '@/composables/useTheme'

defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const { isDark, toggleTheme } = useTheme()

const currentPath = computed(() => route.path)
const isDiscoverActive = computed(() => {
  const path = currentPath.value
  return path === '/' || path.split('/').filter(Boolean).length <= 1 && path !== '/profile' && path !== '/pin-board'
})

const userProfile = computed(() => {
  const u = authStore.user
  const email = u?.email ?? ''
  return {
    name: u?.name || email.split('@')[0] || 'User',
    email: email || 'Sign in to sync your board',
    avatar: u?.picture || 'https://picsum.photos/100/100?random=user'
  }
})

const navigate = (path: string) => {
  emit('close')
  router.push(path)
}

const handleSignOut = async () => {
  emit('close')
  await authStore.signOut()
  router.push('/login')
}
</script>

<style scoped>
.drawer-wrapper {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  visibility: hidden;
  transition: visibility 0.3s;
}

.drawer-wrapper.is-open {
  visibility: visible;
}

.drawer-backdrop {
  position: absolute;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(4px);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.drawer-wrapper.is-open .drawer-backdrop {
  opacity: 1;
}

.drawer-panel {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 280px;
  background-color: var(--bg-primary);
  border-right: 1px solid var(--border-primary);
  display: flex;
  flex-direction: column;
  box-shadow: 4px 0 12px rgba(0, 0, 0, 0.15);
  transform: translateX(-100%);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.drawer-wrapper.is-open .drawer-panel {
  transform: translateX(0);
}

/* Header */
.drawer-header {
  padding: 1.5rem 1rem;
  border-bottom: 1px solid var(--border-primary);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
}

.user-avatar {
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--border-secondary);
}

.user-details {
  min-width: 0;
}

.user-name {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-email {
  font-size: 0.75rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.close-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.25rem;
  transition: color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: var(--text-primary);
}

/* Navigation Links */
.drawer-nav {
  flex: 1;
  padding: 1.5rem 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 0.75rem 0.875rem;
  border-radius: 0.5rem;
  background: transparent;
  border: none;
  cursor: pointer;
  width: 100%;
  text-align: left;
  transition: background-color 0.2s, color 0.2s;
}

.nav-link svg {
  color: var(--text-secondary);
  transition: color 0.2s;
}

.nav-link span {
  color: var(--text-primary);
  font-size: 0.95rem;
  font-weight: 500;
}

.nav-link:hover,
.nav-link.active {
  background-color: var(--bg-hover);
}

.nav-link:hover svg,
.nav-link.active svg {
  color: var(--text-primary);
}

/* Footer Action Buttons */
.drawer-footer {
  padding: 1rem 0.75rem;
  border-top: 1px solid var(--border-primary);
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.footer-action {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 0.75rem 0.875rem;
  border-radius: 0.5rem;
  background: transparent;
  border: none;
  cursor: pointer;
  width: 100%;
  text-align: left;
  transition: background-color 0.2s, color 0.2s;
}

.footer-action svg {
  color: var(--text-secondary);
  transition: color 0.2s;
}

.footer-action span {
  color: var(--text-primary);
  font-size: 0.95rem;
  font-weight: 500;
}

.footer-action:hover {
  background-color: var(--bg-hover);
}

.footer-action:hover svg {
  color: var(--text-primary);
}

.footer-action.sign-out span {
  color: #f87171;
}

.footer-action.sign-out svg {
  color: #f87171;
}

.footer-action.sign-out:hover {
  background-color: rgba(239, 68, 68, 0.08);
}
</style>
