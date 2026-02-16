<script setup lang="ts">
import { LetterState } from './types'

defineProps<{
  letterStates: Record<string, LetterState>
}>()

defineEmits<{
  (e: 'key', key: string): void
}>()

const rows = [
  'qwertyuiop'.split(''),
  'asdfghjkl'.split(''),
  ['Enter', ...'zxcvbnm'.split(''), 'Backspace']
]
</script>

<template>
  <div id="keyboard">
    <div class="row" v-for="(row, i) in rows" :key="i">
      <div class="spacer" v-if="i === 1"></div>
      <button
        v-for="key in row"
        :key="key"
        :class="[key.length > 1 && 'big', letterStates[key]]"
        @click="$emit('key', key)"
      >
        <span v-if="key !== 'Backspace'">{{ key }}</span>
        <svg
          v-else
          xmlns="http://www.w3.org/2000/svg"
          height="20"
          viewBox="0 0 24 24"
          width="20"
        >
          <path
            fill="currentColor"
            d="M22 3H7c-.69 0-1.23.35-1.59.88L0 12l5.41 8.11c.36.53.9.89 1.59.89h15c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H7.07L2.4 12l4.66-7H22v14zm-11.59-2L14 13.41 17.59 17 19 15.59 15.41 12 19 8.41 17.59 7 14 10.59 10.41 7 9 8.41 12.59 12 9 15.59z"
          ></path>
        </svg>
      </button>
      <div class="spacer" v-if="i === 1"></div>
    </div>
  </div>
</template>

<style scoped>
#keyboard {
  padding: 0 6px;
  padding-bottom: max(env(safe-area-inset-bottom, 0px), 0.5rem);
  margin-bottom: 0.25rem;
  user-select: none;
  flex-shrink: 0;
}

.row {
  display: flex;
  width: 100%;
  margin: 0 auto 6px;
  touch-action: manipulation;
  gap: 5px;
}

.spacer {
  flex: 0.5;
}

button {
  font-family: inherit;
  font-weight: 700;
  font-size: 0.8rem;
  letter-spacing: 0.02em;
  border: 0;
  padding: 0;
  height: 52px;
  border-radius: 4px;
  cursor: pointer;
  user-select: none;
  background-color: #818384;
  color: #fff;
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  text-transform: uppercase;
  -webkit-tap-highlight-color: transparent;
  transition: background-color 0.15s, transform 0.1s;
}

button:active {
  transform: scale(0.95);
}

button.big {
  flex: 1.5;
  font-size: 0.7rem;
}

/* State colours matching the board */
button.correct {
  background-color: #538d4e;
  color: #fff;
}
button.present {
  background-color: #b59f3b;
  color: #fff;
}
button.absent {
  background-color: #3a3a3c;
  color: #fff;
}

@media (max-height: 600px) {
  button { height: 44px; font-size: 0.7rem; }
  .row { gap: 4px; margin-bottom: 4px; }
}
</style>
