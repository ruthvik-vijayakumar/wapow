<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import TopBar from '@/components/TopBar.vue'
import NavigationDrawer from '@/components/NavigationDrawer.vue'
import DesktopSidebar from '@/components/DesktopSidebar.vue'
import DesktopTopHeader from '@/components/DesktopTopHeader.vue'

// Import game components
import WordleGame from '@/views/wordle/Game.vue'
import UnblockGame from '@/views/unblock/UnblockGame.vue'

const router = useRouter()
const isDrawerOpen = ref(false)
const isDesktop = ref(false)
let mq: MediaQueryList | null = null

// Selected game state: 'wordle' | 'unblock' | null
const selectedGame = ref<'wordle' | 'unblock' | null>(null)

// Desktop breakpoint listener
const onMqChange = (e: MediaQueryListEvent) => {
  isDesktop.value = e.matches
}

onMounted(() => {
  mq = window.matchMedia('(min-width: 1024px)')
  isDesktop.value = mq.matches
  mq.addEventListener('change', onMqChange)
})

onUnmounted(() => {
  if (mq) mq.removeEventListener('change', onMqChange)
})

// Mobile drawer triggers
const handleMenu = () => {
  isDrawerOpen.value = true
}

const handleSearch = () => {
  router.push('/search')
}

// Navigation handler for sidebar
const handleNavigation = (route: string) => {
  switch (route) {
    case 'home':
      router.push('/sports')
      break
    case 'search':
      router.push('/search')
      break
    case 'ask-ai':
      router.push({ path: '/search', query: { tab: 'chat' } })
      break
    case 'games':
      selectedGame.value = null // reset to hub
      break
    case 'profile':
      router.push('/profile')
      break
    default:
      console.log('Unknown route:', route)
  }
}

const handleDesktopSearch = (query: string) => {
  router.push({ path: '/search', query: query ? { q: query } : undefined })
}
</script>

<template>
  <div class="games-shell" :class="{ 'has-sidebar': isDesktop, 'playing-active': selectedGame !== null }">
    <!-- Desktop Layout Sidebar (Only show if not currently playing a game fullscreen on mobile) -->
    <DesktopSidebar v-if="isDesktop" @navigate="handleNavigation" />

    <!-- Main Content Wrapper -->
    <div class="main-wrapper">
      <!-- Headers (Only show when not playing a game) -->
      <template v-if="selectedGame === null">
        <!-- Desktop Header -->
        <DesktopTopHeader v-if="isDesktop" @search="handleDesktopSearch">
          <template #left>
            <div class="desktop-header-title-container">
              <h1 class="desktop-view-title font-postoni font-bold">TunedIn Games</h1>
            </div>
          </template>
        </DesktopTopHeader>

        <!-- Mobile Top Bar -->
        <TopBar v-else @search="handleSearch" @menu="handleMenu" />
      </template>

      <!-- Fullscreen Game Render Area -->
      <div v-if="selectedGame !== null" class="active-game-wrapper">
        <WordleGame v-if="selectedGame === 'wordle'" :total-stories="1" :story-index="0" @back="selectedGame = null" />
        <UnblockGame v-else-if="selectedGame === 'unblock'" :total-stories="1" :story-index="0" @back="selectedGame = null" />
      </div>

      <!-- Games Hub Portal Dashboard -->
      <div v-else class="scroll-container">
        <div class="content-container">
          <h1 v-if="!isDesktop" class="mobile-view-title font-postoni font-bold">TunedIn Games</h1>
          <p class="section-subtitle font-franklin">Challenge your mind with our collections of daily interactive puzzles.</p>

          <div class="games-grid">
            <!-- Game Card 1: Unblock Casual -->
            <div class="game-card unblock-theme" @click="selectedGame = 'unblock'">
              <div class="game-card-visual">
                <div class="glow-orb rose"></div>
                <!-- Teaser layout representing sliding blocks -->
                <div class="puzzle-teaser">
                  <div class="t-block t-red">EXIT</div>
                  <div class="t-block t-teal"></div>
                  <div class="t-block t-indigo"></div>
                </div>
              </div>
              <div class="game-card-info">
                <span class="game-badge font-franklin">New</span>
                <h3 class="game-title font-postoni font-bold">Unblock Casual</h3>
                <p class="game-desc font-franklin">Slide the red block out of the grid by moving blockades. 5 difficulty levels.</p>
                <button class="play-btn font-franklin">Play Game &rsaquo;</button>
              </div>
            </div>

            <!-- Game Card 2: Wordle -->
            <div class="game-card wordle-theme" @click="selectedGame = 'wordle'">
              <div class="game-card-visual">
                <div class="glow-orb emerald"></div>
                <!-- Teaser layout representing Wordle letters -->
                <div class="wordle-teaser">
                  <div class="t-tile correct">W</div>
                  <div class="t-tile present">O</div>
                  <div class="t-tile absent">R</div>
                  <div class="t-tile correct">D</div>
                  <div class="t-tile correct">S</div>
                </div>
              </div>
              <div class="game-card-info">
                <span class="game-badge font-franklin">Daily</span>
                <h3 class="game-title font-postoni font-bold">Wordle</h3>
                <p class="game-desc font-franklin">Guess today's hidden five-letter word in six attempts with color-coded clues.</p>
                <button class="play-btn font-franklin">Play Game &rsaquo;</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Mobile Drawer Settings -->
    <NavigationDrawer v-if="!isDesktop && selectedGame === null" :isOpen="isDrawerOpen" @close="isDrawerOpen = false" />
  </div>
</template>

<style scoped>
.games-shell {
  display: flex;
  min-height: 100vh;
  min-height: 100dvh;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  transition: background-color 0.3s ease, color 0.3s ease;
}

.main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
}

.active-game-wrapper {
  flex: 1;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.scroll-container {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
}

.content-container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem 1rem 3rem;
}

.desktop-header-title-container {
  display: flex;
  align-items: center;
}

.desktop-view-title {
  font-size: 1.25rem;
  color: var(--text-primary);
}

.mobile-view-title {
  font-size: 1.75rem;
  line-height: 1.2;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.section-subtitle {
  font-size: 0.925rem;
  color: var(--text-secondary);
  margin-bottom: 2rem;
  padding: 0 0.125rem;
}

/* Games Grid */
.games-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.5rem;
}

@media (min-width: 768px) {
  .games-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.game-card {
  display: flex;
  flex-direction: column;
  background: var(--bg-elevated);
  border: 1px solid var(--border-primary);
  border-radius: 1.25rem;
  overflow: hidden;
  cursor: pointer;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.25s ease, border-color 0.25s ease;
}

.game-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
  border-color: var(--accent);
}

.game-card-visual {
  position: relative;
  height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.unblock-theme .game-card-visual {
  background: linear-gradient(135deg, #18181b, #09090b);
}

.wordle-theme .game-card-visual {
  background: linear-gradient(135deg, #18122b, #0c0817);
}

.glow-orb {
  position: absolute;
  width: 140px;
  height: 140px;
  filter: blur(25px);
  opacity: 0.25;
  border-radius: 50%;
}

.glow-orb.rose {
  background: radial-gradient(circle, #ff0844 0%, transparent 70%);
}

.glow-orb.emerald {
  background: radial-gradient(circle, #00cdac 0%, transparent 70%);
}

.game-card-info {
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  flex: 1;
}

.game-badge {
  font-size: 0.65rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  margin-bottom: 0.5rem;
}

.unblock-theme .game-badge {
  background: rgba(244, 63, 94, 0.15);
  color: #f43f5e;
}

.wordle-theme .game-badge {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.game-title {
  font-size: 1.25rem;
  color: var(--text-primary);
  margin-bottom: 0.35rem;
}

.game-desc {
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.45;
  margin-bottom: 1.25rem;
  flex: 1;
}

.play-btn {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--accent-text);
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0;
  transition: transform 0.2s;
}

.game-card:hover .play-btn {
  transform: translateX(4px);
}

/* Unblock Teaser Elements */
.puzzle-teaser {
  position: relative;
  width: 120px;
  height: 120px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 8px;
}

.t-block {
  position: absolute;
  border-radius: 4px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.3);
}

.t-red {
  width: 60px;
  height: 28px;
  left: 10px;
  top: 46px;
  background: linear-gradient(135deg, #ff416c, #ff4b2b);
  border: 1px solid rgba(255,255,255,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.55rem;
  font-weight: 900;
  color: #fff;
  letter-spacing: 0.05em;
  box-shadow: 0 0 10px rgba(255, 65, 108, 0.4);
}

.t-teal {
  width: 28px;
  height: 60px;
  right: 15px;
  top: 10px;
  background: linear-gradient(135deg, #02aab0, #00cdac);
}

.t-indigo {
  width: 60px;
  height: 28px;
  left: 20px;
  bottom: 12px;
  background: linear-gradient(135deg, #8a2be2, #4a00e0);
}

/* Wordle Teaser Elements */
.wordle-teaser {
  display: flex;
  gap: 4px;
}

.t-tile {
  width: 26px;
  height: 26px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: bold;
  color: #fff;
  text-shadow: 0 1px 1px rgba(0,0,0,0.5);
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.t-tile.correct { background-color: #538d4e; }
.t-tile.present { background-color: #b59f3b; }
.t-tile.absent { background-color: #3a3a3c; }

/* Playing active overrides */
.playing-active .main-wrapper {
  background-color: #000;
}
</style>
