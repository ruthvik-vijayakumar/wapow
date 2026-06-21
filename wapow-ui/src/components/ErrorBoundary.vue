<template>
  <slot v-if="!hasError" />
  <div v-else class="error-boundary">
    <div class="error-boundary-content">
      <svg class="error-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
        />
      </svg>
      <p class="error-title">Something went wrong</p>
      <p class="error-message">{{ errorMessage }}</p>
      <button class="retry-button" @click="reset">Try Again</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue'

interface Props {
  fallbackMessage?: string
}

const props = withDefaults(defineProps<Props>(), {
  fallbackMessage: 'An unexpected error occurred while loading this content.',
})

const hasError = ref(false)
const errorMessage = ref(props.fallbackMessage)

onErrorCaptured((err: Error) => {
  hasError.value = true
  errorMessage.value = props.fallbackMessage
  console.error('[ErrorBoundary] Caught error:', err)
  return false // prevent propagation
})

const reset = () => {
  hasError.value = false
  errorMessage.value = props.fallbackMessage
}
</script>

<style scoped>
.error-boundary {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  min-height: 200px;
  background-color: var(--bg-primary, #000);
  color: var(--text-primary, #fff);
}

.error-boundary-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 2rem;
  max-width: 320px;
}

.error-icon {
  width: 3rem;
  height: 3rem;
  color: var(--text-tertiary, #6b7280);
  margin-bottom: 1rem;
}

.error-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--text-primary, #fff);
}

.error-message {
  font-size: 0.875rem;
  color: var(--text-secondary, #9ca3af);
  margin-bottom: 1.5rem;
  line-height: 1.4;
}

.retry-button {
  padding: 0.5rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #fff;
  background-color: var(--accent, #3b82f6);
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: opacity 0.2s;
}

.retry-button:hover {
  opacity: 0.85;
}
</style>
