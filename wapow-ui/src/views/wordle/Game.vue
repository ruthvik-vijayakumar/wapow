<script setup lang="ts">
import { onUnmounted } from 'vue'
import { getWordOfTheDay, allWords } from './words'
import Keyboard from './Keyboard.vue'
import BottomControls from '@/components/BottomControls.vue'
import { LetterState } from './types'
import { ref, computed } from 'vue'

// Props for story navigation
interface Props {
  storyIndex?: number
  totalStories?: number
}

const props = withDefaults(defineProps<Props>(), {
  storyIndex: 0,
  totalStories: 1
})

const emit = defineEmits<{
  back: []
  'next-story': []
  'prev-story': []
}>()

// Get word of the day
const answer = getWordOfTheDay()

// Board state. Each tile is represented as { letter, state }
const board = ref(
  Array.from({ length: 6 }, () =>
    Array.from({ length: 5 }, () => ({
      letter: '',
      state: LetterState.INITIAL
    }))
  )
)

// Current active row.
let currentRowIndex = ref(0)
const currentRow = computed(() => board.value[currentRowIndex.value])

// Feedback state: message and shake
let message = ref('')
let grid = ref('')
let shakeRowIndex = ref(-1)
let success = ref(false)

// Keep track of revealed letters for the virtual keyboard
const letterStates = ref<Record<string, LetterState>>({})

// Handle keyboard input.
let allowInput = true

const onKeyup = (e: KeyboardEvent) => onKey(e.key)

window.addEventListener('keyup', onKeyup)

onUnmounted(() => {
  window.removeEventListener('keyup', onKeyup)
})

function onKey(key: string) {
  if (!allowInput) return
  if (/^[a-zA-Z]$/.test(key)) {
    fillTile(key.toLowerCase())
  } else if (key === 'Backspace') {
    clearTile()
  } else if (key === 'Enter') {
    completeRow()
  }
}

function fillTile(letter: string) {
  for (const tile of currentRow.value) {
    if (!tile.letter) {
      tile.letter = letter
      break
    }
  }
}

function clearTile() {
  for (const tile of [...currentRow.value].reverse()) {
    if (tile.letter) {
      tile.letter = ''
      break
    }
  }
}

function completeRow() {
  if (currentRow.value.every((tile) => tile.letter)) {
    const guess = currentRow.value.map((tile) => tile.letter).join('')
    if (!allWords.includes(guess) && guess !== answer) {
      shake()
      showMessage(`Not in word list`)
      return
    }

    const answerLetters: (string | null)[] = answer.split('')
    // first pass: mark correct ones
    currentRow.value.forEach((tile, i) => {
      if (answerLetters[i] === tile.letter) {
        tile.state = letterStates.value[tile.letter] = LetterState.CORRECT
        answerLetters[i] = null
      }
    })
    // second pass: mark the present
    currentRow.value.forEach((tile) => {
      if (!tile.state && answerLetters.includes(tile.letter)) {
        tile.state = LetterState.PRESENT
        answerLetters[answerLetters.indexOf(tile.letter)] = null
        if (!letterStates.value[tile.letter]) {
          letterStates.value[tile.letter] = LetterState.PRESENT
        }
      }
    })
    // 3rd pass: mark absent
    currentRow.value.forEach((tile) => {
      if (!tile.state) {
        tile.state = LetterState.ABSENT
        if (!letterStates.value[tile.letter]) {
          letterStates.value[tile.letter] = LetterState.ABSENT
        }
      }
    })

    allowInput = false
    if (currentRow.value.every((tile) => tile.state === LetterState.CORRECT)) {
      // yay!
      setTimeout(() => {
        grid.value = genResultGrid()
        showMessage(
          ['Genius', 'Magnificent', 'Impressive', 'Splendid', 'Great', 'Phew'][
            currentRowIndex.value
          ],
          -1
        )
        success.value = true
      }, 1600)
    } else if (currentRowIndex.value < board.value.length - 1) {
      // go the next row
      currentRowIndex.value++
      setTimeout(() => {
        allowInput = true
      }, 1600)
    } else {
      // game over :(
      setTimeout(() => {
        showMessage(answer.toUpperCase(), -1)
      }, 1600)
    }
  } else {
    shake()
    showMessage('Not enough letters')
  }
}

function showMessage(msg: string, time = 1000) {
  message.value = msg
  if (time > 0) {
    setTimeout(() => {
      message.value = ''
    }, time)
  }
}

function shake() {
  shakeRowIndex.value = currentRowIndex.value
  setTimeout(() => {
    shakeRowIndex.value = -1
  }, 1000)
}

const icons = {
  [LetterState.CORRECT]: '🟩',
  [LetterState.PRESENT]: '🟨',
  [LetterState.ABSENT]: '⬜',
  [LetterState.INITIAL]: null
}

function genResultGrid() {
  return board.value
    .slice(0, currentRowIndex.value + 1)
    .map((row) => {
      return row.map((tile) => icons[tile.state]).join('')
    })
    .join('\n')
}

// BottomControls event handlers
const handleLike = (liked: boolean) => {
  console.log('Game liked:', liked)
}

const handleComments = (articleContent?: any) => {
  console.log('Comments requested for game:', articleContent)
}

const handleShare = () => {
  console.log('Share requested for game')
}
</script>

<template>
  <div class="game-container">
    <!-- Toast message -->
    <Transition name="toast">
      <div class="toast" v-if="message">
        {{ message }}
        <pre v-if="grid" class="toast-grid">{{ grid }}</pre>
      </div>
    </Transition>

    <!-- Header -->
    <div class="game-header">
      <button @click="emit('back')" class="header-btn">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>

      <h1 class="game-title">Wordle</h1>

      <div class="header-btn story-counter">
        {{ props.storyIndex + 1 }}/{{ props.totalStories }}
      </div>
    </div>

    <!-- Board -->
    <div class="board-wrapper">
      <div id="board">
        <div
          v-for="(row, rowIdx) in board"
          :key="rowIdx"
          :class="[
            'row',
            shakeRowIndex === rowIdx && 'shake',
            success && currentRowIndex === rowIdx && 'jump'
          ]"
        >
          <div
            v-for="(tile, tileIdx) in row"
            :key="tileIdx"
            :class="['tile', tile.letter && 'filled', tile.state && 'revealed']"
          >
            <div class="front" :style="{ transitionDelay: `${tileIdx * 300}ms` }">
              {{ tile.letter }}
            </div>
            <div
              :class="['back', tile.state]"
              :style="{
                transitionDelay: `${tileIdx * 300}ms`,
                animationDelay: `${tileIdx * 100}ms`
              }"
            >
              {{ tile.letter }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Keyboard -->
    <Keyboard @key="onKey" :letter-states="letterStates" />

    <!-- Bottom Controls -->
    <BottomControls
      :show-category="true"
      :category="'Games'"
      :article-content="{ title: 'Wordle Game', type: 'game' }"
      @like="handleLike"
      @comments="handleComments"
      @share="handleShare"
    />
  </div>
</template>

<style scoped>
/* ── Container ─────────────────────────────────────── */
.game-container {
  position: relative;
  height: 100vh;
  height: calc(var(--vh, 100vh));
  width: 100%;
  display: flex;
  flex-direction: column;
  background: #121213;
  overflow: hidden;
  color: #fff;
  font-family: 'Helvetica Neue', Arial, sans-serif;
}

/* ── Header ────────────────────────────────────────── */
.game-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.625rem 1rem;
  border-bottom: 1px solid #3a3a3c;
  flex-shrink: 0;
}

.header-btn {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background 0.2s;
}
.header-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.game-title {
  font-size: 1.375rem;
  font-weight: 700;
  letter-spacing: 0.15em;
  text-transform: uppercase;
}

.story-counter {
  font-size: 0.75rem;
  font-weight: 500;
  opacity: 0.5;
  width: auto;
  padding: 0 0.25rem;
}

/* ── Toast ─────────────────────────────────────────── */
.toast {
  position: absolute;
  left: 50%;
  top: 4rem;
  transform: translateX(-50%);
  z-index: 20;
  color: #fff;
  background: #fff;
  color: #121213;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-weight: 700;
  font-size: 0.875rem;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
  white-space: nowrap;
}
.toast-grid {
  margin-top: 0.5rem;
  font-size: 1.25rem;
  line-height: 1.6;
  text-align: center;
}
.toast-enter-active { animation: toast-in 0.15s ease-out; }
.toast-leave-active { animation: toast-out 0.25s ease-in forwards; }
@keyframes toast-in { from { opacity: 0; transform: translateX(-50%) translateY(-8px); } to { opacity: 1; transform: translateX(-50%) translateY(0); } }
@keyframes toast-out { to { opacity: 0; } }

/* ── Board ─────────────────────────────────────────── */
.board-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem 0;
  min-height: 0;
}

#board {
  display: grid;
  grid-template-rows: repeat(6, 1fr);
  gap: 5px;
  width: min(330px, 80vw);
  max-height: min(396px, calc(var(--vh, 100vh) - 280px));
  aspect-ratio: 5 / 6;
}

.row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 5px;
}

.tile {
  width: 100%;
  aspect-ratio: 1;
  font-size: clamp(1.25rem, 5vw, 2rem);
  line-height: 1;
  font-weight: 700;
  text-transform: uppercase;
  user-select: none;
  position: relative;
  border-radius: 4px;
  overflow: hidden;
}

.tile .front,
.tile .back {
  box-sizing: border-box;
  display: flex;
  justify-content: center;
  align-items: center;
  position: absolute;
  inset: 0;
  transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  border-radius: 4px;
}

.tile .front {
  background: transparent;
  border: 2px solid #3a3a3c;
  color: #fff;
}
.tile.filled .front {
  border-color: #565758;
  animation: pop 0.1s ease-in-out;
}

.tile .back {
  transform: rotateX(180deg);
}
.tile.revealed .front {
  transform: rotateX(180deg);
}
.tile.revealed .back {
  transform: rotateX(0deg);
}

/* ── State colours ─────────────────────────────────── */
.correct,
.present,
.absent {
  color: #fff !important;
  font-weight: 700;
}
.correct {
  background: #538d4e !important;
}
.present {
  background: #b59f3b !important;
}
.absent {
  background: #3a3a3c !important;
}

/* ── Animations ────────────────────────────────────── */
@keyframes pop {
  0%   { transform: scale(1); }
  50%  { transform: scale(1.12); }
  100% { transform: scale(1); }
}

.shake {
  animation: shake 0.5s cubic-bezier(0.36, 0, 0.66, 1);
}
@keyframes shake {
  10%, 90% { transform: translateX(-1px); }
  20%, 80% { transform: translateX(2px); }
  30%, 50%, 70% { transform: translateX(-4px); }
  40%, 60% { transform: translateX(4px); }
}

.jump .tile .back {
  animation: bounce 1s ease;
}
@keyframes bounce {
  0%, 20% { transform: translateY(0); }
  40%     { transform: translateY(-30px); }
  50%     { transform: translateY(5px); }
  60%     { transform: translateY(-15px); }
  80%     { transform: translateY(2px); }
  100%    { transform: translateY(0); }
}

/* ── Small screens ─────────────────────────────────── */
@media (max-height: 600px) {
  .game-header { padding: 0.375rem 1rem; }
  .game-title { font-size: 1.125rem; }
  .board-wrapper { padding: 0.5rem 0; }
}
</style>
