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
    <Transition>
      <div class="message" v-if="message">
        {{ message }}
        <pre v-if="grid">{{ grid }}</pre>
      </div>
    </Transition>
    <div class="game-header">
      <button @click="emit('back')" class="back-button">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      
      <div class="header-actions">
        <div class="story-indicator">
          {{ props.storyIndex + 1 }} / {{ props.totalStories }}
        </div>
      </div>
    </div>
    <div id="board">
      <div
        v-for="(row, index) in board"
        :class="[
          'row',
          shakeRowIndex === index && 'shake',
          success && currentRowIndex === index && 'jump'
        ]"
      >
        <div
          v-for="(tile, index) in row"
          :class="['tile', tile.letter && 'filled', tile.state && 'revealed']"
        >
          <div class="front" :style="{ transitionDelay: `${index * 300}ms` }">
            {{ tile.letter }}
          </div>
          <div
            :class="['back', tile.state]"
            :style="{
              transitionDelay: `${index * 300}ms`,
              animationDelay: `${index * 100}ms`
            }"
          >
            {{ tile.letter }}
          </div>
        </div>
      </div>
    </div>
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
.game-container {
  @apply relative h-screen w-full;
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
  @apply flex flex-col;
  overflow: hidden;
}

#board {
  display: grid;
  grid-template-rows: repeat(6, 1fr);
  grid-gap: 6px;
  padding: 20px;
  padding-top: 64px;
  box-sizing: border-box;
  --height: min(380px, calc(var(--vh, 100vh) - 310px));
  height: var(--height);
  width: min(320px, calc(var(--height) / 6 * 5));
  margin: 0px auto;
  @apply flex-1;
  position: relative;
}

#board::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at center, rgba(255, 255, 255, 0.05) 0%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}
.message {
  position: absolute;
  left: 50%;
  top: 80px;
  color: #fff;
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.9) 0%, rgba(26, 26, 46, 0.95) 100%);
  padding: 20px 24px;
  z-index: 2;
  border-radius: 12px;
  transform: translateX(-50%);
  transition: all 0.3s ease-out;
  font-weight: 600;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}
.message.v-leave-to {
  opacity: 0;
}
.row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  grid-gap: 6px;
  position: relative;
  z-index: 1;
}
.tile {
  width: 100%;
  font-size: 2rem;
  line-height: 2rem;
  font-weight: bold;
  vertical-align: middle;
  text-transform: uppercase;
  user-select: none;
  position: relative;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
}
.tile.filled {
  animation: zoom 0.2s;
}
.tile .front,
.tile .back {
  box-sizing: border-box;
  display: inline-flex;
  justify-content: center;
  align-items: center;
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  border-radius: 8px;
}
.tile .front {
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}
.tile.filled .front {
  border-color: rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.15);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}
.tile .back {
  transform: rotateX(180deg);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
}
.tile.revealed .front {
  transform: rotateX(180deg);
}
.tile.revealed .back {
  transform: rotateX(0deg);
}

@keyframes zoom {
  0% {
    transform: scale(1.1);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
  }
}

.shake {
  animation: shake 0.6s cubic-bezier(0.36, 0, 0.66, 1);
}

@keyframes shake {
  0% {
    transform: translate(1px);
  }
  10% {
    transform: translate(-2px);
  }
  20% {
    transform: translate(2px);
  }
  30% {
    transform: translate(-2px);
  }
  40% {
    transform: translate(2px);
  }
  50% {
    transform: translate(-2px);
  }
  60% {
    transform: translate(2px);
  }
  70% {
    transform: translate(-2px);
  }
  80% {
    transform: translate(2px);
  }
  90% {
    transform: translate(-2px);
  }
  100% {
    transform: translate(1px);
  }
}

.jump .tile .back {
  animation: jump 0.8s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

@keyframes jump {
  0% {
    transform: translateY(0px);
  }
  20% {
    transform: translateY(5px);
  }
  60% {
    transform: translateY(-25px);
  }
  90% {
    transform: translateY(3px);
  }
  100% {
    transform: translateY(0px);
  }
}

@media (max-height: 680px) {
  .tile {
    font-size: 2.5vh;
  }
}

.game-header {
  @apply absolute top-0 left-0 right-0 z-10;
  @apply flex items-center justify-between p-4;
}

.back-button {
  @apply w-8 h-8 rounded-full bg-black bg-opacity-50;
  @apply flex items-center justify-center text-white;
  @apply hover:bg-opacity-70 transition-colors;
}

.header-actions {
  @apply flex items-center space-x-2;
}

.story-indicator {
  @apply text-sm text-white;
  @apply font-medium;
  @apply bg-black bg-opacity-50;
  @apply px-3 py-1;
  @apply rounded-full;
}

#source-link {
  position: absolute;
  right: 1em;
  top: 0.5em;
}

.correct,
.present,
.absent {
  color: #fff !important;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.correct {
  background: #10b981 !important;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.present {
  background: #f59e0b !important;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
}

.absent {
  background: #6b7280 !important;
  box-shadow: 0 4px 12px rgba(107, 114, 128, 0.3);
}
</style>
