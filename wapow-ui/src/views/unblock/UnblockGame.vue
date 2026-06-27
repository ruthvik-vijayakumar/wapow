<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { levels, type Block, type Level } from './levels'
import BottomControls from '@/components/BottomControls.vue'

// Props for story navigation
interface Props {
  storyIndex?: number
  totalStories?: number
}

const props = withDefaults(defineProps<Props>(), {
  storyIndex: 0,
  totalStories: 1,
})

const emit = defineEmits<{
  back: []
  'next-story': []
  'prev-story': []
}>()

// ── Mode ────────────────────────────────────────────────────────────────────
// "preview" = card in the feed showing a teaser + Enter Game button.
// "playing" = fullscreen game.
const mode = ref<'preview' | 'playing'>('preview')

const enterGame = () => {
  mode.value = 'playing'
  initGame()
}

const exitGame = () => {
  mode.value = 'preview'
  clearSolver()
}

// ── Game State ──────────────────────────────────────────────────────────────
const currentLevelIndex = ref(0)
const currentLevel = computed(() => levels[currentLevelIndex.value])
const blocks = ref<Block[]>([])
const moves = ref(0)
const bestMoves = ref<Record<number, number>>({})
const undoStack = ref<string[]>([])
const redoStack = ref<string[]>([])
const hasWon = ref(false)
const hintStep = ref<{ blockId: string; direction: 'left' | 'right' | 'up' | 'down' } | null>(null)
const isSolving = ref(false)

// Canvas Confetti
const confettiCanvas = ref<HTMLCanvasElement | null>(null)
let confettiCtx: CanvasRenderingContext2D | null = null
let confettiAnimationId = 0
interface ConfettiParticle {
  x: number
  y: number
  size: number
  color: string
  vx: number
  vy: number
  rotation: number
  rotationSpeed: number
}
const confettiParticles = ref<ConfettiParticle[]>([])

// Visual variables
const boardRef = ref<HTMLElement | null>(null)
const cellSize = ref(56) // Will be updated on resize
const dragOffset = ref(0)
const activeDragBlockId = ref<string | null>(null)
let dragStartX = 0
let dragStartY = 0
let dragStartVal = 0
let dragMinVal = 0
let dragMaxVal = 0

// Web Audio API context for synthesized SFX
let audioCtx: AudioContext | null = null

const initAudio = () => {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)()
  }
}

// SFX Synthesizer
const playSound = (type: 'slide' | 'snap' | 'victory') => {
  try {
    initAudio()
    if (!audioCtx || audioCtx.state === 'suspended') {
      audioCtx?.resume()
    }
    const ctx = audioCtx!
    const osc = ctx.createOscillator()
    const gainNode = ctx.createGain()
    osc.connect(gainNode)
    gainNode.connect(ctx.destination)

    const now = ctx.currentTime

    if (type === 'slide') {
      osc.type = 'triangle'
      osc.frequency.setValueAtTime(90, now)
      osc.frequency.exponentialRampToValueAtTime(70, now + 0.15)
      gainNode.gain.setValueAtTime(0.12, now)
      gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.15)
      osc.start(now)
      osc.stop(now + 0.15)
    } else if (type === 'snap') {
      // Wood block collision snap
      osc.type = 'sine'
      osc.frequency.setValueAtTime(450, now)
      osc.frequency.exponentialRampToValueAtTime(150, now + 0.05)
      gainNode.gain.setValueAtTime(0.2, now)
      gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.05)
      osc.start(now)
      osc.stop(now + 0.05)
    } else if (type === 'victory') {
      // Cheerful fanfare C5 -> E5 -> G5 -> C6
      const notes = [523.25, 659.25, 783.99, 1046.50]
      notes.forEach((freq, idx) => {
        const noteOsc = ctx.createOscillator()
        const noteGain = ctx.createGain()
        noteOsc.connect(noteGain)
        noteGain.connect(ctx.destination)
        noteOsc.type = 'sine'
        noteOsc.frequency.setValueAtTime(freq, now + idx * 0.1)
        noteGain.gain.setValueAtTime(0.15, now + idx * 0.1)
        noteGain.gain.setValueAtTime(0.15, now + idx * 0.1 + 0.08)
        noteGain.gain.exponentialRampToValueAtTime(0.01, now + idx * 0.1 + 0.15)
        noteOsc.start(now + idx * 0.1)
        noteOsc.stop(now + idx * 0.1 + 0.18)
      })
    }
  } catch (e) {
    console.warn('Audio synthesis failed:', e)
  }
}

// Deep clone helper
const cloneBlocks = (arr: Block[]): Block[] => {
  return arr.map(b => ({ ...b }))
}

// Serialize blocks to string for state tracking
const serializeState = (arr: Block[]): string => {
  return arr.map(b => `${b.id}:${b.row}:${b.col}`).join(',')
}

// Deserialize state string
const deserializeState = (stateStr: string) => {
  const parts = stateStr.split(',')
  parts.forEach(part => {
    const [id, rStr, cStr] = part.split(':')
    const block = blocks.value.find(b => b.id === id)
    if (block) {
      block.row = parseInt(rStr, 10)
      block.col = parseInt(cStr, 10)
    }
  })
}

// ── Game Logic ──────────────────────────────────────────────────────────────
const initGame = () => {
  blocks.value = cloneBlocks(currentLevel.value.blocks)
  moves.value = 0
  undoStack.value = []
  redoStack.value = []
  hasWon.value = false
  hintStep.value = null
  stopConfetti()
  updateCellSize()
}

const resetLevel = () => {
  initGame()
  playSound('snap')
}

// Resize Board cells dynamically
const updateCellSize = () => {
  if (boardRef.value) {
    cellSize.value = boardRef.value.clientWidth / 6
  }
}

// Movement Boundary Calculations
const getMovementBounds = (block: Block, currentBlocks: Block[]) => {
  // Create occupancy grid of other blocks
  const occupied = Array.from({ length: 6 }, () => Array(6).fill(false))
  currentBlocks.forEach(b => {
    if (b.id === block.id) return
    for (let i = 0; i < b.size; i++) {
      if (b.orientation === 'h') {
        occupied[b.row][b.col + i] = true
      } else {
        occupied[b.row + i][b.col] = true
      }
    }
  })

  if (block.orientation === 'h') {
    // Left boundary
    let minCol = block.col
    while (minCol > 0 && !occupied[block.row][minCol - 1]) {
      minCol--
    }
    // Right boundary
    let maxCol = block.col
    const limit = block.isTarget ? 5 : (6 - block.size) // Red block can exit to column 5
    while (maxCol < limit && !occupied[block.row][maxCol + block.size]) {
      maxCol++
    }
    return { min: minCol, max: maxCol }
  } else {
    // Up boundary
    let minRow = block.row
    while (minRow > 0 && !occupied[minRow - 1][block.col]) {
      minRow--
    }
    // Down boundary
    let maxRow = block.row
    const limit = 6 - block.size
    while (maxRow < limit && !occupied[maxRow + block.size][block.col]) {
      maxRow++
    }
    return { min: minRow, max: maxRow }
  }
}

// ── Drag & Drop Handlers ──────────────────────────────────────────────────
const handlePointerDown = (e: PointerEvent, block: Block) => {
  if (hasWon.value) return
  initAudio()
  
  const target = e.currentTarget as HTMLElement
  target.setPointerCapture(e.pointerId)
  
  activeDragBlockId.value = block.id
  dragStartX = e.clientX
  dragStartY = e.clientY
  dragStartVal = block.orientation === 'h' ? block.col : block.row
  
  const bounds = getMovementBounds(block, blocks.value)
  dragMinVal = bounds.min
  dragMaxVal = bounds.max
  dragOffset.value = 0
  hintStep.value = null // clear hint on user action
}

const handlePointerMove = (e: PointerEvent, block: Block) => {
  if (activeDragBlockId.value !== block.id) return
  
  const delta = block.orientation === 'h' 
    ? e.clientX - dragStartX 
    : e.clientY - dragStartY
  
  const cellDelta = delta / cellSize.value
  const targetVal = dragStartVal + cellDelta
  const clampedVal = Math.max(dragMinVal, Math.min(dragMaxVal, targetVal))
  
  const newOffset = clampedVal - dragStartVal
  if (Math.abs(newOffset - dragOffset.value) > 0.05) {
    playSound('slide')
  }
  dragOffset.value = newOffset
}

const handlePointerUp = (e: PointerEvent, block: Block) => {
  if (activeDragBlockId.value !== block.id) return
  
  const target = e.currentTarget as HTMLElement
  try {
    target.releasePointerCapture(e.pointerId)
  } catch (err) {}
  
  activeDragBlockId.value = null
  const finalVal = Math.round(dragStartVal + dragOffset.value)
  dragOffset.value = 0
  
  if (finalVal !== dragStartVal) {
    // Record current state before changing
    const prevState = serializeState(blocks.value)
    undoStack.value.push(prevState)
    redoStack.value = [] // Clear redo

    // Update block
    if (block.orientation === 'h') {
      block.col = finalVal
    } else {
      block.row = finalVal
    }
    
    moves.value++
    playSound('snap')
    
    // Check Win Condition
    // Target block reaches col index 5 (which means it's partially off the board exiting)
    if (block.isTarget && finalVal === 5) {
      triggerWin()
    }
  }
}

// ── Undo / Redo ─────────────────────────────────────────────────────────────
const undo = () => {
  if (undoStack.value.length === 0 || hasWon.value) return
  const currentState = serializeState(blocks.value)
  redoStack.value.push(currentState)
  
  const prevState = undoStack.value.pop()!
  deserializeState(prevState)
  moves.value++
  playSound('snap')
}

const redo = () => {
  if (redoStack.value.length === 0 || hasWon.value) return
  const currentState = serializeState(blocks.value)
  undoStack.value.push(currentState)
  
  const nextState = redoStack.value.pop()!
  deserializeState(nextState)
  moves.value++
  playSound('snap')
}

// ── BFS Solver (Real-time Hint System) ──────────────────────────────────────
const runSolver = () => {
  if (hasWon.value || isSolving.value) return
  isSolving.value = true
  
  // BFS queue state representation:
  // Key: serializeState
  // Value: parentState string
  const startState = serializeState(blocks.value)
  
  // Quick pre-check if already solved
  const targetBlock = blocks.value.find(b => b.isTarget)!
  if (targetBlock.col === 5) {
    isSolving.value = false
    return
  }

  const queue: string[] = [startState]
  const visited = new Map<string, string | null>() // state -> parentState
  visited.set(startState, null)
  
  let solutionStateStr: string | null = null

  // Run BFS
  let safetyCounter = 0
  const maxIterations = 50000 // fail-safe limit
  
  while (queue.length > 0 && safetyCounter < maxIterations) {
    safetyCounter++
    const currStateStr = queue.shift()!
    
    // Parse current block state
    const tempBlocks = cloneBlocks(currentLevel.value.blocks)
    const parts = currStateStr.split(',')
    parts.forEach(part => {
      const [id, rStr, cStr] = part.split(':')
      const b = tempBlocks.find(x => x.id === id)!
      b.row = parseInt(rStr, 10)
      b.col = parseInt(cStr, 10)
    })

    // Check if target is solved
    const currTarget = tempBlocks.find(b => b.isTarget)!
    if (currTarget.col === 5) {
      solutionStateStr = currStateStr
      break
    }

    // Generate valid moves for this configuration
    for (let i = 0; i < tempBlocks.length; i++) {
      const b = tempBlocks[i]
      const bounds = getMovementBounds(b, tempBlocks)
      
      const currVal = b.orientation === 'h' ? b.col : b.row
      
      // Explore all coordinates within valid range
      for (let targetVal = bounds.min; targetVal <= bounds.max; targetVal++) {
        if (targetVal === currVal) continue
        
        // Clone and update
        const nextBlocks = tempBlocks.map(x => ({ ...x }))
        const nextB = nextBlocks[i]
        if (nextB.orientation === 'h') {
          nextB.col = targetVal
        } else {
          nextB.row = targetVal
        }
        
        const nextStateStr = serializeState(nextBlocks)
        if (!visited.has(nextStateStr)) {
          visited.set(nextStateStr, currStateStr)
          queue.push(nextStateStr)
        }
      }
    }
  }

  // Reconstruct path
  if (solutionStateStr) {
    const path: string[] = []
    let curr = solutionStateStr
    while (curr !== startState) {
      path.push(curr)
      curr = visited.get(curr)!
    }
    path.reverse()
    
    if (path.length > 0) {
      // Find the first move to show as a hint
      const nextStateStr = path[0]
      const nextParts = nextStateStr.split(',')
      const startParts = startState.split(',')
      
      for (let i = 0; i < nextParts.length; i++) {
        const [nId, nR, nC] = nextParts[i].split(':')
        const [sId, sR, sC] = startParts[i].split(':')
        
        const block = blocks.value.find(b => b.id === nId)!
        const nVal = parseInt(block.orientation === 'h' ? nC : nR, 10)
        const sVal = parseInt(block.orientation === 'h' ? sC : sR, 10)
        
        if (nVal !== sVal) {
          let dir: 'left' | 'right' | 'up' | 'down' = 'left'
          if (block.orientation === 'h') {
            dir = nVal > sVal ? 'right' : 'left'
          } else {
            dir = nVal > sVal ? 'down' : 'up'
          }
          
          hintStep.value = {
            blockId: nId,
            direction: dir
          }
          break
        }
      }
    }
  } else {
    // Solvable not found (e.g. invalid board state)
    alert("No path to exit found! Try resetting the level.")
  }
  
  isSolving.value = false
}

const clearSolver = () => {
  hintStep.value = null
}

// ── Victory Handling ────────────────────────────────────────────────────────
const triggerWin = () => {
  hasWon.value = ref(true).value
  playSound('victory')
  
  // Save High Score
  const currentBest = bestMoves.value[currentLevel.value.id]
  if (!currentBest || moves.value < currentBest) {
    bestMoves.value[currentLevel.value.id] = moves.value
    localStorage.setItem(`unblock-best-${currentLevel.value.id}`, String(moves.value))
  }
  
  // Trigger Canvas Confetti
  setTimeout(() => {
    startConfetti()
  }, 100)
}

const nextLevel = () => {
  if (currentLevelIndex.value < levels.length - 1) {
    currentLevelIndex.value++
    initGame()
  } else {
    // Wrap around to first level
    currentLevelIndex.value = 0
    initGame()
  }
}

// ── Particle Confetti System ────────────────────────────────────────────────
const startConfetti = () => {
  if (!confettiCanvas.value) return
  confettiCtx = confettiCanvas.value.getContext('2d')
  if (!confettiCtx) return
  
  // Set dimensions
  confettiCanvas.value.width = window.innerWidth
  confettiCanvas.value.height = window.innerHeight
  
  confettiParticles.value = []
  const colors = ['#ff007f', '#00f2fe', '#4facfe', '#00ffcd', '#ffea00', '#ff0844']
  
  // Generate particles
  for (let i = 0; i < 150; i++) {
    confettiParticles.value.push({
      x: window.innerWidth / 2 + (Math.random() - 0.5) * 80,
      y: window.innerHeight / 2 + (Math.random() - 0.5) * 80 - 100,
      size: Math.random() * 8 + 6,
      color: colors[Math.floor(Math.random() * colors.length)],
      vx: (Math.random() - 0.5) * 15,
      vy: Math.random() * -12 - 5,
      rotation: Math.random() * 360,
      rotationSpeed: (Math.random() - 0.5) * 10
    })
  }
  
  // Start animation loop
  cancelAnimationFrame(confettiAnimationId)
  confettiAnimationLoop()
}

const confettiAnimationLoop = () => {
  if (!confettiCtx || !confettiCanvas.value) return
  const ctx = confettiCtx
  const canvas = confettiCanvas.value
  
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  
  let active = false
  confettiParticles.value.forEach(p => {
    p.vy += 0.35 // gravity
    p.vx *= 0.98 // drag
    p.x += p.vx
    p.y += p.vy
    p.rotation += p.rotationSpeed
    
    // Draw
    ctx.save()
    ctx.translate(p.x, p.y)
    ctx.rotate((p.rotation * Math.PI) / 180)
    ctx.fillStyle = p.color
    ctx.shadowBlur = 6
    ctx.shadowColor = p.color
    ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size)
    ctx.restore()
    
    if (p.y < canvas.height) {
      active = true
    }
  })
  
  if (active && hasWon.value) {
    confettiAnimationId = requestAnimationFrame(confettiAnimationLoop)
  }
}

const stopConfetti = () => {
  cancelAnimationFrame(confettiAnimationId)
  if (confettiCtx && confettiCanvas.value) {
    confettiCtx.clearRect(0, 0, confettiCanvas.value.width, confettiCanvas.value.height)
  }
}

// ── Style calculations ──────────────────────────────────────────────────────
const getBlockTransform = (block: Block) => {
  const isDragging = activeDragBlockId.value === block.id
  const offset = isDragging ? dragOffset.value : 0
  
  let tx = block.col * cellSize.value
  let ty = block.row * cellSize.value
  
  if (block.orientation === 'h') {
    tx += offset * cellSize.value
  } else {
    ty += offset * cellSize.value
  }
  
  return `translate3d(${tx}px, ${ty}px, 0)`
}

// Handle local storage loads
onMounted(() => {
  levels.forEach(lvl => {
    const val = localStorage.getItem(`unblock-best-${lvl.id}`)
    if (val) {
      bestMoves.value[lvl.id] = parseInt(val, 10)
    }
  })
  window.addEventListener('resize', updateCellSize)
  updateCellSize()
})

onUnmounted(() => {
  window.removeEventListener('resize', updateCellSize)
  stopConfetti()
})

// Trigger init whenever level changes
watch(currentLevelIndex, () => {
  initGame()
})

const handleComments = () => {}
const handleShare = () => {}
</script>

<template>
  <!-- ── PREVIEW CARD ── shows in the story feed -->
  <div v-if="mode === 'preview'" class="preview-card">
    <div class="preview-header">
      <button @click="emit('back')" class="header-btn" aria-label="Back">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <span class="preview-label">Unblock Casual</span>
      <div class="header-btn story-counter">
        {{ props.storyIndex + 1 }}/{{ props.totalStories }}
      </div>
    </div>

    <div class="preview-body">
      <!-- Icon/Visual Teaser -->
      <div class="preview-board-visual">
        <div class="glowing-orb"></div>
        <div class="teaser-block horiz text-rose-400">EXIT</div>
        <div class="teaser-block vert text-cyan-400"></div>
      </div>

      <p class="preview-copy">Slide the red block out of the grid. Simple rules, infinite mind-bending puzzles.</p>

      <button class="enter-btn" @click="enterGame" aria-label="Enter game">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        Play Unblock Me
      </button>
    </div>

    <BottomControls
      :show-category="true"
      :category="'Games'"
      :article-content="{ title: 'Unblock Casual Game', type: 'game' }"
      @comments="handleComments"
      @share="handleShare"
    />
  </div>

  <!-- ── FULLSCREEN GAME ── -->
  <div v-else class="game-container">
    <!-- Confetti canvas overlay -->
    <canvas ref="confettiCanvas" class="confetti-canvas"></canvas>

    <div class="game-header">
      <button @click="exitGame" class="header-btn" aria-label="Exit game">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <div class="level-info">
        <h1 class="game-title">Unblock Casual</h1>
        <div class="level-selector">
          <button @click="currentLevelIndex = Math.max(0, currentLevelIndex - 1)" :disabled="currentLevelIndex === 0" class="level-arrow">
            &lsaquo;
          </button>
          <span class="level-name">Lvl {{ currentLevel.id }}: {{ currentLevel.name }}</span>
          <button @click="currentLevelIndex = Math.min(levels.length - 1, currentLevelIndex + 1)" :disabled="currentLevelIndex === levels.length - 1" class="level-arrow">
            &rsaquo;
          </button>
        </div>
      </div>
      <div class="header-btn story-counter">
        {{ props.storyIndex + 1 }}/{{ props.totalStories }}
      </div>
    </div>

    <!-- Gameplay Stats -->
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-label">Moves</span>
        <span class="stat-val font-semibold">{{ moves }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Best Score</span>
        <span class="stat-val font-semibold">{{ bestMoves[currentLevel.id] || '-' }}</span>
      </div>
      <div class="stat-badge" :class="currentLevel.difficulty.toLowerCase()">
        {{ currentLevel.difficulty }}
      </div>
    </div>

    <!-- Board Arena -->
    <div class="board-arena">
      <div class="board-frame">
        <div ref="boardRef" class="board-grid">
          <!-- Win overlay gate indicator -->
          <div class="exit-gate">
            <div class="exit-arrow">&rsaquo;</div>
          </div>
          
          <!-- Grid Background Cells -->
          <div class="grid-backdrop"></div>

          <!-- Dynamic Blocks -->
          <div
            v-for="block in blocks"
            :key="block.id"
            class="puzzle-block"
            :class="[
              block.isTarget && 'target-block', 
              block.orientation,
              activeDragBlockId === block.id && 'dragging',
              hintStep?.blockId === block.id && 'hint-pulsing'
            ]"
            :style="{
              transform: getBlockTransform(block),
              width: `${block.orientation === 'h' ? block.size * cellSize : cellSize - 4}px`,
              height: `${block.orientation === 'v' ? block.size * cellSize : cellSize - 4}px`,
              left: block.orientation === 'v' ? '2px' : '0px',
              top: block.orientation === 'h' ? '2px' : '0px',
            }"
            @pointerdown="handlePointerDown($event, block)"
            @pointermove="handlePointerMove($event, block)"
            @pointerup="handlePointerUp($event, block)"
            @pointercancel="handlePointerUp($event, block)"
          >
            <div class="block-inner" :class="block.color">
              <span v-if="block.isTarget" class="target-label font-franklin">EXIT</span>
              <!-- Hint Arrow -->
              <div v-if="hintStep?.blockId === block.id" class="hint-arrow" :class="hintStep.direction">
                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path v-if="hintStep.direction === 'right'" stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  <path v-if="hintStep.direction === 'left'" stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  <path v-if="hintStep.direction === 'up'" stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 10l7-7m0 0l7 7m-7-7v18" />
                  <path v-if="hintStep.direction === 'down'" stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                </svg>
              </div>
              <div class="block-grips">
                <div class="grip-line"></div>
                <div class="grip-line"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Actions Panel -->
    <div class="actions-panel">
      <button @click="resetLevel" class="action-btn" aria-label="Reset Level">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 7.89M9 11h.01M12 11h.01M15 11h.01" />
        </svg>
        Reset
      </button>

      <button @click="undo" :disabled="undoStack.length === 0" class="action-btn" aria-label="Undo move">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
        </svg>
        Undo
      </button>

      <button @click="redo" :disabled="redoStack.length === 0" class="action-btn" aria-label="Redo move">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 10H11a8 8 0 00-8 8v2M21 10l-6 6m6-6l-6-6" />
        </svg>
        Redo
      </button>

      <button @click="runSolver" :disabled="isSolving" class="action-btn hint-btn" aria-label="Get Hint">
        <svg class="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364.364l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        {{ isSolving ? 'Solving...' : 'Hint' }}
      </button>
    </div>

    <!-- Win Modal Dialog -->
    <Transition name="modal-fade">
      <div v-if="hasWon" class="win-modal-backdrop">
        <div class="win-modal-card">
          <div class="sparkle-icon">🏆</div>
          <h2 class="win-title font-postoni">Victory!</h2>
          <p class="win-copy">You solved "{{ currentLevel.name }}" in <span class="text-rose-400 font-bold">{{ moves }}</span> moves.</p>
          <div class="win-actions">
            <button @click="initGame" class="win-btn reset">Play Again</button>
            <button @click="nextLevel" class="win-btn next">Next Level</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════
   PREVIEW CARD (Feed tease)
   ═══════════════════════════════════════════════════════ */
.preview-card {
  position: relative;
  height: 100vh;
  height: calc(var(--vh, 100vh));
  width: 100%;
  display: flex;
  flex-direction: column;
  background: #121213;
  overflow: hidden;
  color: #fff;
  font-family: 'Inter', sans-serif;
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.625rem 1rem;
  border-bottom: 1px solid #222;
  flex-shrink: 0;
}

.preview-label {
  font-size: 1.125rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #fff;
}

.preview-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
  padding: 2rem 1.5rem 6rem;
}

/* Beautiful custom graphic teaser */
.preview-board-visual {
  position: relative;
  width: 160px;
  height: 160px;
  background: rgba(255, 255, 255, 0.02);
  border: 2px dashed rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.glowing-orb {
  position: absolute;
  width: 80px;
  height: 80px;
  background: radial-gradient(circle, rgba(244,63,94,0.2) 0%, transparent 70%);
  filter: blur(10px);
}

.teaser-block {
  position: absolute;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  box-shadow: 0 4px 12px rgba(0,0,0,0.5);
  backdrop-filter: blur(5px);
}

.teaser-block.horiz {
  width: 90px;
  height: 40px;
  left: 20px;
  top: 60px;
  background: linear-gradient(135deg, #ff416c, #ff4b2b);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 0 15px rgba(255, 65, 108, 0.5);
}

.teaser-block.vert {
  width: 40px;
  height: 90px;
  right: 20px;
  top: 25px;
  background: linear-gradient(135deg, #02aab0, #00cdac);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.preview-copy {
  font-size: 0.9375rem;
  color: #888;
  text-align: center;
  max-width: 250px;
  line-height: 1.45;
}

.enter-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.75rem;
  background: linear-gradient(135deg, #ff416c, #ff4b2b);
  color: #fff;
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  border: none;
  border-radius: 2rem;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(255, 65, 108, 0.35);
  transition: all 0.2s ease;
}

.enter-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 65, 108, 0.5);
}

.enter-btn:active {
  transform: translateY(0);
}

/* ═══════════════════════════════════════════════════════
   FULLSCREEN GAMEPLAY
   ═══════════════════════════════════════════════════════ */
.game-container {
  position: relative;
  height: 100vh;
  height: calc(var(--vh, 100vh));
  width: 100%;
  display: flex;
  flex-direction: column;
  background: #09090b;
  overflow: hidden;
  color: #fff;
  font-family: 'Inter', sans-serif;
}

.confetti-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 99;
}

.game-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.625rem 1rem;
  border-bottom: 1px solid #1f1f23;
  flex-shrink: 0;
}

.header-btn {
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #a1a1aa;
  background: #18181b;
  border: 1px solid #27272a;
  cursor: pointer;
  transition: all 0.2s;
}

.header-btn:hover {
  color: #fff;
  background: #27272a;
}

.level-info {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.game-title {
  font-size: 0.95rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #71717a;
}

.level-selector {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.125rem;
}

.level-arrow {
  background: transparent;
  border: none;
  color: #f43f5e;
  font-size: 1.5rem;
  font-weight: bold;
  cursor: pointer;
  padding: 0 0.5rem;
  line-height: 1;
}

.level-arrow:disabled {
  color: #3f3f46;
  cursor: not-allowed;
}

.level-name {
  font-size: 1.05rem;
  font-weight: 700;
  color: #f4f4f5;
}

.story-counter {
  font-size: 0.75rem;
  opacity: 0.6;
  width: auto;
  padding: 0 0.5rem;
}

/* Stats bar */
.stats-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2.5rem;
  padding: 0.75rem 1rem;
  background: #121214;
  border-bottom: 1px solid #1f1f23;
  flex-shrink: 0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #71717a;
}

.stat-val {
  font-size: 1.125rem;
  color: #fafafa;
}

.stat-badge {
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.stat-badge.easy { background: rgba(20, 184, 166, 0.15); color: #2dd4bf; }
.stat-badge.medium { background: rgba(245, 158, 11, 0.15); color: #fbbf24; }
.stat-badge.hard { background: rgba(239, 68, 68, 0.15); color: #f87171; }
.stat-badge.expert { background: rgba(236, 72, 153, 0.15); color: #f472b6; }

/* ── Board Arena ─────────────────────────────────────── */
.board-arena {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.25rem 0;
  min-height: 0;
}

.board-frame {
  padding: 10px;
  background: linear-gradient(135deg, #1f1f23, #18181b);
  border: 1px solid #27272a;
  border-radius: 1.5rem;
  box-shadow: 
    0 25px 50px -12px rgba(0,0,0,0.7),
    inset 0 1px 0 rgba(255,255,255,0.05);
}

.board-grid {
  position: relative;
  width: min(336px, 84vw);
  aspect-ratio: 1;
  background: #09090b;
  border-radius: 1rem;
  overflow: visible; /* Need exit to overflow visually */
  border: 1px solid #1f1f23;
  touch-action: none;
}

.grid-backdrop {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
  background-size: 16.666% 16.666%;
  border-radius: 1rem;
  pointer-events: none;
}

/* Exit Gate indicator */
.exit-gate {
  position: absolute;
  right: -10px;
  top: 33.333%; /* 3rd row */
  height: 16.666%;
  width: 14px;
  background: linear-gradient(90deg, transparent, rgba(244,63,94,0.3));
  border-radius: 0 4px 4px 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  border-right: 2px solid #f43f5e;
  box-shadow: 8px 0 15px rgba(244,63,94,0.4);
  pointer-events: none;
}

.exit-arrow {
  color: #f43f5e;
  font-size: 1rem;
  font-weight: 800;
  margin-right: -4px;
  animation: pulseRight 1s infinite alternate;
}

@keyframes pulseRight {
  from { transform: translateX(0); opacity: 0.5; }
  to { transform: translateX(3px); opacity: 1; }
}

/* Dynamic puzzle blocks */
.puzzle-block {
  position: absolute;
  box-sizing: border-box;
  padding: 2px;
  cursor: grab;
  will-change: transform;
}

.puzzle-block.dragging {
  cursor: grabbing;
  z-index: 10;
}

.block-inner {
  width: 100%;
  height: 100%;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  box-shadow: 
    0 8px 16px -4px rgba(0,0,0,0.5),
    inset 0 1px 0 rgba(255,255,255,0.15);
  border: 1px solid rgba(255,255,255,0.08);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.puzzle-block:hover .block-inner {
  border-color: rgba(255,255,255,0.2);
}

.target-block .block-inner {
  border-color: rgba(255,255,255,0.3);
}

.target-label {
  font-size: 0.7rem;
  font-weight: 900;
  letter-spacing: 0.08em;
  color: #fff;
  opacity: 0.9;
  text-shadow: 0 1px 3px rgba(0,0,0,0.5);
}

/* Block grip markers */
.block-grips {
  position: absolute;
  display: flex;
  gap: 3px;
  opacity: 0.35;
}

.horiz .block-grips {
  flex-direction: column;
}

.vert .block-grips {
  flex-direction: row;
}

.grip-line {
  background: #fff;
  border-radius: 1px;
}

.horiz .grip-line {
  width: 12px;
  height: 2px;
}

.vert .grip-line {
  width: 2px;
  height: 12px;
}

/* ── Solver Hint Pulses ────────────────────────────────── */
.puzzle-block.hint-pulsing .block-inner {
  animation: hintPulse 1.2s infinite ease-in-out;
  border-color: #fbbf24 !important;
  box-shadow: 0 0 20px rgba(251, 191, 36, 0.7) !important;
}

@keyframes hintPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.025); }
}

.hint-arrow {
  position: absolute;
  z-index: 20;
  animation: bounceArrow 0.8s infinite alternate;
  pointer-events: none;
}

.hint-arrow.right { right: -30px; }
.hint-arrow.left { left: -30px; }
.hint-arrow.up { top: -30px; }
.hint-arrow.down { bottom: -30px; }

@keyframes bounceArrow {
  from { transform: translate(0, 0); }
  to {
    transform: translate(
      var(--tx, 0),
      var(--ty, 0)
    );
  }
}
.hint-arrow.right { --tx: 6px; }
.hint-arrow.left { --tx: -6px; }
.hint-arrow.up { --ty: -6px; }
.hint-arrow.down { --ty: 6px; }

/* ── Actions Panel ───────────────────────────────────── */
.actions-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 1rem;
  background: #0c0c0e;
  border-top: 1px solid #1f1f23;
  flex-shrink: 0;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.55rem 1rem;
  background: #18181b;
  border: 1px solid #27272a;
  border-radius: 8px;
  color: #e4e4e7;
  font-size: 0.825rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover:not(:disabled) {
  background: #27272a;
  color: #fff;
  border-color: #3f3f46;
}

.action-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.hint-btn {
  border-color: rgba(251, 191, 36, 0.2);
}
.hint-btn:hover:not(:disabled) {
  background: rgba(251, 191, 36, 0.08);
  border-color: rgba(251, 191, 36, 0.4);
}

/* ── Victory Modal ────────────────────────────────────── */
.win-modal-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(8px);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
}

.win-modal-card {
  width: 100%;
  max-width: 290px;
  background: linear-gradient(135deg, #18181b, #09090b);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 1.5rem;
  padding: 2rem 1.5rem;
  text-align: center;
  box-shadow: 0 25px 50px -12px rgba(0,0,0,0.8);
}

.sparkle-icon {
  font-size: 3.5rem;
  line-height: 1;
  margin-bottom: 0.75rem;
  filter: drop-shadow(0 0 10px rgba(251,191,36,0.3));
  animation: float 2s infinite alternate ease-in-out;
}

@keyframes float {
  from { transform: translateY(0); }
  to { transform: translateY(-8px); }
}

.win-title {
  font-size: 2.25rem;
  font-weight: 800;
  color: #fafafa;
  margin-bottom: 0.5rem;
}

.win-copy {
  font-size: 0.9rem;
  color: #a1a1aa;
  margin-bottom: 1.5rem;
  line-height: 1.5;
}

.win-actions {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.win-btn {
  padding: 0.75rem 1.5rem;
  border-radius: 10px;
  font-weight: 700;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.win-btn.reset {
  background: #27272a;
  color: #f4f4f5;
  border: 1px solid #3f3f46;
}
.win-btn.reset:hover {
  background: #3f3f46;
}

.win-btn.next {
  background: linear-gradient(135deg, #ff416c, #ff4b2b);
  color: #fff;
  box-shadow: 0 4px 15px rgba(255, 65, 108, 0.35);
}
.win-btn.next:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(255, 65, 108, 0.45);
}

/* Modal fade animations */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.25s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-active .win-modal-card {
  animation: zoomIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes zoomIn {
  from { transform: scale(0.85); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

/* Small screens height adjustments */
@media (max-height: 620px) {
  .game-header { padding: 0.35rem 1rem; }
  .stats-bar { padding: 0.5rem 1rem; }
  .board-arena { padding: 0.5rem 0; }
  .actions-panel { padding: 0.75rem 1rem; }
}
</style>
