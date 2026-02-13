<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { isAuth0Configured } from '@/lib/auth0'

const route = useRoute()
const authStore = useAuthStore()

const handleLogin = () => {
  const redirect = (route.query.redirect as string) || '/'
  authStore.loginWithRedirect({ appState: { target: redirect } })
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-illustration-wrap">
        <img
          src="@/assets/login-illustration.png"
          alt=""
          class="login-illustration"
        />
      </div>
      <h1 class="login-title">Welcome to WAPOW</h1>
      <p class="login-subtitle">Articles, videos, and stories—curated around what you care about</p>
      <p v-if="!isAuth0Configured" class="login-error">
        Auth0 is not configured. Set VITE_AUTH0_DOMAIN, VITE_AUTH0_CLIENT_ID, and VITE_AUTH0_AUDIENCE.
      </p>
      <button
        v-else
        type="button"
        class="login-button"
        :disabled="authStore.isAuthenticated"
        @click="handleLogin"
      >
        Sign in
      </button>
      <p v-if="authStore.isAuthenticated" class="login-status">You are signed in. Redirecting...</p>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  min-height: 100vh;
  background: #000;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.login-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.25rem;
  max-width: 400px;
  width: 100%;
}

.login-illustration-wrap {
  width: 100%;
  display: flex;
  justify-content: center;
  padding: 0 1rem;
}

.login-illustration {
  filter: invert(1);
  max-width: 200px;
  width: 100%;
  height: auto;
  object-fit: contain;
}

.login-title {
  font-size: 1.5rem;
  font-weight: 600;
  @apply font-postoni;
}

.login-subtitle {
  font-size: 0.95rem;
  color: #9ca3af;
  text-align: center;
  margin: -0.4rem 0 0;
}

.login-error {
  font-size: 0.875rem;
  color: #f59e0b;
  text-align: center;
}

.login-button {
  padding: 0.5rem 1.5rem;
  font-size: 1rem;
  font-weight: 500;
  color: white;
  background-color: #2563eb;
  border: none;
  border-radius: 25px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.login-button:hover:not(:disabled) {
  background-color: #1d4ed8;
}

.login-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.login-status {
  font-size: 0.875rem;
  color: #9ca3af;
}
</style>
