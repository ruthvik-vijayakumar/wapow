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
          <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
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
          <svg class="w-[18px] h-[18px]" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
          </svg>
          <span>Discover</span>
        </button>

        <button
          class="nav-link"
          :class="{ active: currentPath === '/topics' }"
          @click="navigate('/topics')"
        >
          <svg class="w-[18px] h-[18px]" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581a1.125 1.125 0 001.591 0l7.181-7.181a1.125 1.125 0 000-1.591l-9.581-9.581A1.125 1.125 0 0011.159 3H9.57z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 6h.008v.008H6V6z" />
          </svg>
          <span>Topics</span>
        </button>

        <button
          class="nav-link"
          :class="{ active: currentPath === '/pin-board' }"
          @click="navigate('/pin-board')"
        >
          <svg class="w-[18px] h-[18px]" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
          </svg>
          <span>Pin Board</span>
        </button>

        <button
          class="nav-link"
          :class="{ active: currentPath === '/profile' }"
          @click="navigate('/profile')"
        >
          <svg class="w-[18px] h-[18px]" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
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
          <svg v-if="isDark" class="w-[18px] h-[18px]" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <!-- Moon icon (shown in light mode) -->
          <svg v-else class="w-[18px] h-[18px]" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
          </svg>
          <span>{{ isDark ? 'Light Mode' : 'Dark Mode' }}</span>
        </button>

        <!-- Sign Out -->
        <button
          class="footer-action sign-out"
          @click="handleSignOut"
        >
          <svg class="w-[18px] h-[18px]" fill="none" stroke="currentColor" stroke-width="1.75" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
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
  return path === '/' || path.split('/').filter(Boolean).length <= 1 && path !== '/profile' && path !== '/pin-board' && path !== '/topics'
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
  width: 260px;
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
  padding: 1.25rem 1rem;
  border-bottom: 1px solid var(--border-primary);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  min-width: 0;
}

.user-avatar {
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid var(--border-secondary);
}

.user-details {
  min-width: 0;
}

.user-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-email {
  font-size: 0.7rem;
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
  padding: 1rem 0.625rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.5rem 0.625rem;
  border-radius: 0.375rem;
  background: transparent;
  border: none;
  cursor: pointer;
  width: 100%;
  text-align: left;
  transition: background-color 0.15s, color 0.15s;
}

.nav-link svg {
  color: var(--text-secondary);
  transition: color 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.nav-link span {
  color: var(--text-primary);
  font-size: 0.875rem;
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
  padding: 1rem 0.625rem;
  border-top: 1px solid var(--border-primary);
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.footer-action {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.5rem 0.625rem;
  border-radius: 0.375rem;
  background: transparent;
  border: none;
  cursor: pointer;
  width: 100%;
  text-align: left;
  transition: background-color 0.15s, color 0.15s;
}

.footer-action svg {
  color: var(--text-secondary);
  transition: color 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.footer-action span {
  color: var(--text-primary);
  font-size: 0.875rem;
  font-weight: 500;
}

.footer-action:hover {
  background-color: var(--bg-hover);
}

.footer-action:hover svg {
  color: var(--text-primary);
}

.footer-action.sign-out span {
  color: #ef4444;
}

.footer-action.sign-out svg {
  color: #ef4444;
}

.footer-action.sign-out:hover {
  background-color: rgba(239, 68, 68, 0.08);
}
</style>

