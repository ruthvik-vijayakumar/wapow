/**
 * Auth store — single source of truth for authentication.
 *
 * Wraps Auth0 behind a Pinia store so auth state and actions are available
 * everywhere: components, router guards, API calls, event handlers.
 *
 * Call `authStore.init()` once from App.vue's setup (where Auth0's inject() is valid).
 * After that, the store can be used from any context without inject() issues.
 */
import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { useAuth0, type Auth0VueClient } from '@auth0/auth0-vue'
import { isAuth0Configured } from '@/lib/auth0'

export interface AuthUser {
  id: string
  sub?: string
  email?: string
  name?: string
  picture?: string
}

export const useAuthStore = defineStore('auth', () => {
  /* ─── reactive state ─── */
  const user = ref<AuthUser | null>(null)
  const isAuthenticated = ref(false)
  const isLoading = ref(true)

  /* ─── derived ─── */
  const userId = computed(() => user.value?.id ?? user.value?.sub ?? null)

  /* ─── cached Auth0 client (set once during init) ─── */
  let _client: Auth0VueClient | null = null

  /**
   * Initialise auth state. **Must** be called from a component's `<script setup>`
   * (e.g. App.vue) so that `useAuth0()`'s `inject()` resolves correctly.
   * Safe to call more than once — subsequent calls are no-ops.
   */
  function init() {
    if (!isAuth0Configured) {
      isAuthenticated.value = false
      isLoading.value = false
      return
    }

    // Already initialised — skip
    if (_client) return

    _client = useAuth0()

    // Keep store in sync with Auth0 SDK reactivity
    watch(
      [
        () => (_client as Auth0VueClient).isAuthenticated.value,
        () => (_client as Auth0VueClient).isLoading.value,
        () => (_client as Auth0VueClient).user.value,
      ],
      ([authenticated, loading, auth0User]) => {
        isAuthenticated.value = !!authenticated
        isLoading.value = !!loading

        if (auth0User) {
          user.value = {
            id: (auth0User as Record<string, string>).sub ?? '',
            sub: (auth0User as Record<string, string>).sub,
            email: (auth0User as Record<string, string>).email,
            name: (auth0User as Record<string, string>).name,
            picture: (auth0User as Record<string, string>).picture,
          }
        } else {
          user.value = null
        }
      },
      { immediate: true },
    )
  }

  /* ─── actions ─── */

  async function signIn(options?: Parameters<Auth0VueClient['loginWithRedirect']>[0]) {
    if (_client) {
      await _client.loginWithRedirect(options)
    }
  }

  async function loginWithRedirect(options?: Parameters<Auth0VueClient['loginWithRedirect']>[0]) {
    if (_client) {
      await _client.loginWithRedirect(options)
    }
  }

  async function signInWithOAuth(provider: 'google' | 'github' | 'twitter') {
    if (_client) {
      await _client.loginWithRedirect({
        authorizationParams: { connection: provider },
      })
    }
  }

  async function signOut() {
    if (_client) {
      const returnTo =
        typeof window !== 'undefined'
          ? `${window.location.origin}/login`
          : undefined
      await _client.logout({ logoutParams: { returnTo } })
    }
  }

  async function getAccessToken(): Promise<string | null> {
    if (!_client) return null
    try {
      return (await _client.getAccessTokenSilently()) ?? null
    } catch {
      return null
    }
  }

  async function handleRedirectCallback(url?: string) {
    if (_client) {
      return await _client.handleRedirectCallback(url)
    }
    return null
  }

  return {
    // State
    user,
    isAuthenticated,
    isLoading,
    userId,
    // Lifecycle
    init,
    // Actions
    signIn,
    loginWithRedirect,
    signInWithOAuth,
    signOut,
    getAccessToken,
    handleRedirectCallback,
  }
})
