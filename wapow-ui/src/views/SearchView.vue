<template>
  <div class="search-container">
    <!-- Search Header -->
    <header class="search-header">
      <div class="header-content">
        <button class="back-btn" @click="goBack" aria-label="Go back">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 19l-7-7 7-7"
            />
          </svg>
        </button>
        <div class="search-input-wrapper">
          <svg class="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            ref="searchInput"
            v-model="query"
            type="text"
            class="search-input"
            :placeholder="
              activeTab === 'results' ? 'Search articles, videos, podcasts…' : 'Ask AI anything…'
            "
            @input="handleInput"
            @keydown.enter="executeSearch"
          />
          <button v-if="query" class="clear-button" @click="clearSearch">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>
    </header>

    <!-- Tab Navigation -->
    <div class="tabs-container">
      <button
        class="tab-button"
        :class="{ active: activeTab === 'results' }"
        @click="activeTab = 'results'"
      >
        Search Results
      </button>
      <button
        class="tab-button"
        :class="{ active: activeTab === 'chat' }"
        @click="activeTab = 'chat'"
      >
        Ask AI Chat
      </button>
    </div>

    <!-- Tab 1: Search Results -->
    <div v-if="activeTab === 'results'" class="results-tab-content">
      <!-- AI Overview Section -->
      <div
        v-if="hasSearched && !isLoading && (isOverviewLoading || overviewText || overviewError)"
        class="ai-overview-card"
      >
        <div class="ai-overview-header">
          <div class="ai-icon-wrapper">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
          </div>
          <span class="ai-overview-title">AI Overview</span>
        </div>

        <div v-if="isOverviewLoading" class="ai-overview-shimmer">
          <div class="ai-loading-text">AI is generating summary...</div>
          <div class="ai-shimmer-line skeleton-pulse" style="width: 100%"></div>
          <div class="ai-shimmer-line skeleton-pulse" style="width: 90%; margin-top: 0.25rem"></div>
          <div class="ai-shimmer-line skeleton-pulse" style="width: 75%; margin-top: 0.25rem"></div>
        </div>

        <div v-else-if="overviewError" class="state-text">
          Failed to generate AI Overview. Please try again.
        </div>

        <div v-else-if="overviewText" class="ai-overview-content-wrapper">
          <div class="ai-overview-content" v-html="formatMarkdown(overviewText)"></div>
          <div class="ai-overview-actions">
            <button class="ai-chat-btn" @click="startFollowUpChat">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
              Chat with AI
            </button>
          </div>
        </div>
      </div>

      <!-- Skeleton loader -->
      <div v-if="isLoading" class="results-list">
        <div v-for="n in 8" :key="n" class="result-item skeleton-item">
          <div class="result-thumbnail skeleton-pulse"></div>
          <div class="result-content">
            <div class="skeleton-line skeleton-pulse" style="width: 85%; height: 0.875rem"></div>
            <div
              class="skeleton-line skeleton-pulse"
              style="width: 60%; height: 0.75rem; margin-top: 0.5rem"
            ></div>
            <div
              class="skeleton-line skeleton-pulse"
              style="width: 35%; height: 0.625rem; margin-top: 0.375rem"
            ></div>
          </div>
        </div>
      </div>

      <!-- Empty query prompt -->
      <div v-else-if="!hasSearched" class="state-container">
        <svg class="state-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <p class="state-title">Find what matters</p>
        <p class="state-subtitle">Search across all articles, videos, and podcasts</p>
      </div>

      <!-- No results -->
      <div v-else-if="results.length === 0" class="state-container">
        <svg class="state-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <p class="state-title">No results found</p>
        <p class="state-subtitle">Try different keywords or check your spelling</p>
      </div>

      <!-- Results -->
      <div v-else class="results-list">
        <div
          v-for="item in results"
          :key="item.id"
          class="result-item"
          @click="handleItemClick(item)"
        >
          <div class="result-thumbnail">
            <img
              :src="getImageUrl(item)"
              :alt="getTitle(item)"
              class="thumbnail-img"
              loading="lazy"
            />
            <span class="type-badge">{{ item._type }}</span>
          </div>
          <div class="result-content">
            <h3 class="result-title">{{ getTitle(item) }}</h3>
            <p v-if="getDescription(item)" class="result-description">{{ getDescription(item) }}</p>
            <p v-if="getAuthor(item)" class="result-author">{{ getAuthor(item) }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab 2: Ask AI Chat -->
    <div v-else class="ai-chat-view">
      <div ref="chatListRef" class="chat-messages-list">
        <!-- Welcome State -->
        <div v-if="chatMessages.length === 0" class="chat-welcome-state">
          <svg class="chat-welcome-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
            />
          </svg>
          <h3 class="chat-welcome-title">Ask TunedIn AI</h3>
          <p class="chat-welcome-subtitle">
            Ask questions about news, topics, or ask for a summary of search results.
          </p>
        </div>

        <!-- Messages -->
        <div v-for="msg in chatMessages" :key="msg.id" class="chat-message-item" :class="msg.type">
          <div class="message-bubble" v-html="formatMarkdown(msg.text)"></div>
          <div class="message-time-stamp">{{ msg.time }}</div>
        </div>

        <!-- Bot Typing Indicator -->
        <div v-if="isChatLoading" class="chat-message-item bot">
          <div class="message-bubble">
            <div class="bot-typing-indicator">
              <span class="typing-dot"></span>
              <span class="typing-dot"></span>
              <span class="typing-dot"></span>
            </div>
          </div>
        </div>
      </div>

      <!-- Chat Input Bar -->
      <div class="chat-input-bar">
        <div class="chat-input-field-wrapper">
          <input
            v-model="chatInput"
            type="text"
            class="chat-input-field"
            placeholder="Ask AI a question..."
            @keyup.enter="() => sendChatMessage()"
          />
        </div>
        <button
          class="chat-send-btn"
          :disabled="!chatInput.trim() || isChatLoading"
          @click="() => sendChatMessage()"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
            />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { apiFetch } from '@/lib/api'
import { useAnalytics } from '@/composables/useAnalytics'

const router = useRouter()
const route = useRoute()
const { trackSearch } = useAnalytics()

const searchInput = ref<HTMLInputElement | null>(null)
const query = ref('')
const results = ref<any[]>([])
const isLoading = ref(false)
const hasSearched = ref(false)

// Tabs State
const activeTab = ref<'results' | 'chat'>('results')

// AI Overview State
const overviewText = ref('')
const isOverviewLoading = ref(false)
const overviewError = ref(false)
const API_KEY = import.meta.env.VITE_GEMINI_API_KEY || 'AIzaSyB-AsIIwQnGGC_y3MY9OpupF9yPsK1CSGk'

// AI Chat State
interface ChatMessage {
  id: number
  type: 'user' | 'bot'
  text: string
  time: string
}
const chatMessages = ref<ChatMessage[]>([])
const chatInput = ref('')
const isChatLoading = ref(false)
const chatListRef = ref<HTMLElement | null>(null)

let debounceTimer: ReturnType<typeof setTimeout> | null = null

onMounted(() => {
  // Read query parameters on mount
  if (route.query.tab === 'chat') {
    activeTab.value = 'chat'
  }
  if (route.query.q) {
    query.value = String(route.query.q)
    executeSearch()
  }
  nextTick(() => searchInput.value?.focus())
})

// Watch route query params for navigation changes
watch(
  () => route.query,
  (newQuery) => {
    if (newQuery.tab === 'chat') {
      activeTab.value = 'chat'
    } else {
      activeTab.value = 'results'
    }
    if (newQuery.q) {
      query.value = String(newQuery.q)
      executeSearch()
    }
  },
)

function handleInput() {
  if (debounceTimer) clearTimeout(debounceTimer)

  // Only auto-search results tab
  if (activeTab.value === 'chat') return

  if (!query.value.trim()) {
    results.value = []
    hasSearched.value = false
    overviewText.value = ''
    return
  }
  debounceTimer = setTimeout(() => executeSearch(), 400)
}

async function executeSearch() {
  const q = query.value.trim()
  if (!q) return

  if (activeTab.value === 'chat') {
    startChatWithQuery(q)
    return
  }

  isLoading.value = true
  hasSearched.value = true
  overviewText.value = ''
  overviewError.value = false

  try {
    const [articlesRes, videosRes, podcastsRes] = await Promise.all([
      apiFetch(`/api/articles?search=${encodeURIComponent(q)}&limit=20`),
      apiFetch(`/api/videos?search=${encodeURIComponent(q)}&limit=10`),
      apiFetch(`/api/podcasts?search=${encodeURIComponent(q)}&limit=10`),
    ])

    const combined: any[] = []

    if (articlesRes.ok) {
      const json = await articlesRes.json()
      const items = json.data ?? []
      items.forEach((item: any) => {
        item._type = 'Article'
      })
      combined.push(...items)
    }

    if (videosRes.ok) {
      const json = await videosRes.json()
      const items = json.data ?? []
      items.forEach((item: any) => {
        item._type = 'Video'
      })
      combined.push(...items)
    }

    if (podcastsRes.ok) {
      const json = await podcastsRes.json()
      const items = json.data ?? []
      items.forEach((item: any) => {
        item._type = 'Podcast'
      })
      combined.push(...items)
    }

    results.value = combined
    trackSearch(q, combined.length)

    // Trigger AI overview generation
    generateAIOverview()
  } catch {
    results.value = []
  } finally {
    isLoading.value = false
  }
}

async function generateAIOverview() {
  const q = query.value.trim()
  if (!q) return

  isOverviewLoading.value = true
  overviewError.value = false
  overviewText.value = ''

  try {
    const resultsSummary = results.value
      .slice(0, 5)
      .map((r, idx) => {
        const title = getTitle(r)
        const desc = getDescription(r)
        return `${idx + 1}. [${r._type}] ${title}: ${desc}`
      })
      .join('\n')

    const prompt = `You are TunedIn AI, a helpful news assistant. The user searched for: "${q}".
Here are the top matching search results from our database:
${resultsSummary || 'No matching local articles found.'}

Please write a concise, professional AI Overview summarizing the answer to the user's search query. Focus on delivering direct answers using both the search results and your general knowledge. Keep it to 2-3 short, engaging paragraphs. Do not use title headings or markdown bold on every sentence, but use normal bullet points or formatting if it makes readability better.`

    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${API_KEY}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }],
          generationConfig: { temperature: 0.3, topK: 40, topP: 0.95, maxOutputTokens: 1024 },
        }),
      },
    )

    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const responseData = await response.json()
    overviewText.value = responseData.candidates[0].content.parts[0].text
  } catch (err) {
    console.error('Error generating AI overview:', err)
    overviewError.value = true
  } finally {
    isOverviewLoading.value = false
  }
}

function clearSearch() {
  query.value = ''
  results.value = []
  hasSearched.value = false
  overviewText.value = ''
  nextTick(() => searchInput.value?.focus())
}

function startChatWithQuery(q: string) {
  chatMessages.value = []
  query.value = ''
  sendChatMessage(q)
}

async function sendChatMessage(customText?: string) {
  const text = (customText || chatInput.value).trim()
  if (!text) return

  if (!customText) {
    chatInput.value = ''
  }

  const userMsgId = Date.now()
  chatMessages.value.push({
    id: userMsgId,
    type: 'user',
    text,
    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  })

  scrollToBottom()
  isChatLoading.value = true

  try {
    // Construct Gemini contents array
    const contents = chatMessages.value.map((msg) => ({
      role: msg.type === 'user' ? 'user' : 'model',
      parts: [{ text: msg.text }],
    }))

    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${API_KEY}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents,
          generationConfig: { temperature: 0.4, topK: 40, topP: 0.95, maxOutputTokens: 1024 },
        }),
      },
    )

    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const responseData = await response.json()
    const replyText = responseData.candidates[0].content.parts[0].text

    chatMessages.value.push({
      id: Date.now() + 1,
      type: 'bot',
      text: replyText,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    })
  } catch (err) {
    console.error('Error in AI Chat:', err)
    chatMessages.value.push({
      id: Date.now() + 1,
      type: 'bot',
      text: "I'm sorry, I'm having trouble connecting to the AI assistant. Please try again.",
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    })
  } finally {
    isChatLoading.value = false
    scrollToBottom()
  }
}

function startFollowUpChat() {
  if (!query.value.trim() || !overviewText.value) return

  chatMessages.value = [
    {
      id: Date.now(),
      type: 'user',
      text: query.value.trim(),
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
    {
      id: Date.now() + 1,
      type: 'bot',
      text: overviewText.value,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]

  activeTab.value = 'chat'
  query.value = ''
  scrollToBottom()
}

function scrollToBottom() {
  nextTick(() => {
    if (chatListRef.value) {
      chatListRef.value.scrollTop = chatListRef.value.scrollHeight
    }
  })
}

function formatMarkdown(text: string): string {
  if (!text) return ''
  // Escape HTML to prevent XSS
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')

  // Convert Bold (**text**)
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')

  // Convert bullet lists (lines starting with * or -)
  const lines = html.split('\n')
  let inList = false
  const formattedLines = lines.map((line) => {
    const trimmed = line.trim()
    if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
      const content = trimmed.substring(2)
      let listLine = `<li>${content}</li>`
      if (!inList) {
        inList = true
        listLine = `<ul class="list-disc pl-5 my-2">${listLine}`
      }
      return listLine
    } else {
      if (inList) {
        inList = false
        return `</ul><p class="my-2">${line}</p>`
      }
      return `<p class="my-2">${line}</p>`
    }
  })

  let result = formattedLines.join('\n')
  if (inList) {
    result += '</ul>'
  }
  return result
}

function getTitle(item: any): string {
  return item.headlines?.basic || item.title || item.name || 'Untitled'
}

function getDescription(item: any): string {
  const desc = item.description?.basic || item.description || ''
  if (typeof desc !== 'string') return ''
  return desc.length > 120 ? desc.slice(0, 120) + '…' : desc
}

function getImageUrl(item: any): string {
  return (
    item.promo_items?.basic?.url ||
    item.imageUrl ||
    item.thumbnail ||
    item.promo_items?.basic?.additional_properties?.thumbnailResizeUrl ||
    ''
  )
}

function getAuthor(item: any): string {
  if (item.credits?.by?.[0]?.name) return item.credits.by[0].name
  if (item.author) return item.author
  return ''
}

function handleItemClick(item: any) {
  const id = item._id ?? item.id
  const category = item.category || item._type?.toLowerCase() || 'sports'
  router.push(`/story/${id}/${category}`)
}

function goBack() {
  router.push('/')
}
</script>

<style scoped>
.search-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  padding-bottom: 1rem;
  transition:
    background-color 0.3s ease,
    color 0.3s ease;
}

.search-header {
  position: sticky;
  top: 0;
  z-index: 10;
  padding: 0.75rem 1rem;
  background-color: var(--bg-primary);
  border-bottom: 1px solid var(--border-primary);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-primary);
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  flex-shrink: 0;
  transition: color 0.2s;
}

.back-btn:hover {
  color: var(--text-secondary);
}

.search-input-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--bg-input);
  border-radius: 0.75rem;
  padding: 0.625rem 0.875rem;
  transition: background 0.2s;
}

.search-icon {
  width: 1.25rem;
  height: 1.25rem;
  flex-shrink: 0;
  color: var(--text-tertiary);
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: 0.9375rem;
  color: var(--text-primary);
}

.search-input::placeholder {
  color: var(--text-tertiary);
}

.clear-button {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 50%;
  background: var(--bg-hover);
  color: var(--text-secondary);
  border: none;
  cursor: pointer;
  transition: background 0.2s;
}

.clear-button:hover {
  background: var(--border-secondary);
}

/* Tabs styles */
.tabs-container {
  display: flex;
  justify-content: center;
  border-bottom: 1px solid var(--border-primary);
  background: var(--bg-primary);
}

.tab-button {
  flex: 1;
  padding: 0.875rem 1rem;
  font-size: 0.9375rem;
  font-weight: 600;
  text-align: center;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  cursor: pointer;
  position: relative;
  transition: color 0.2s;
}

.tab-button:hover {
  color: var(--text-primary);
}

.tab-button.active {
  color: var(--accent-text);
}

.tab-button.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 2px;
  background-color: var(--accent);
}

.results-tab-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* AI Overview Card */
.ai-overview-card {
  margin: 0.75rem 1rem;
  padding: 1rem;
  border-radius: 0.75rem;
  background: linear-gradient(135deg, var(--bg-elevated) 0%, var(--bg-secondary) 100%);
  border: 1px solid var(--border-primary);
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
}

.dark .ai-overview-card {
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
}

.ai-overview-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(to bottom, #8b5cf6, #3b82f6);
}

.ai-overview-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.ai-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 50%;
  background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 100%);
  color: #ffffff;
}

.ai-overview-title {
  font-size: 0.875rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: linear-gradient(to right, #8b5cf6, #3b82f6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.ai-overview-content {
  font-size: 0.9375rem;
  line-height: 1.5;
  color: var(--text-primary);
}

.ai-overview-content :deep(p) {
  margin-bottom: 0.75rem;
}

.ai-overview-content :deep(p:last-child) {
  margin-bottom: 0;
}

.ai-overview-content :deep(ul),
.ai-overview-content :deep(ol) {
  margin-left: 1.25rem;
  margin-bottom: 0.75rem;
  list-style-type: disc;
}

.ai-overview-content :deep(li) {
  margin-bottom: 0.25rem;
}

.ai-overview-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 0.75rem;
}

.ai-chat-btn {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.875rem;
  font-size: 0.8125rem;
  font-weight: 600;
  border-radius: 0.5rem;
  background: var(--bg-hover);
  color: var(--text-primary);
  border: none;
  cursor: pointer;
  transition:
    background 0.2s,
    transform 0.1s;
}

.ai-chat-btn:hover {
  background: var(--border-secondary);
  transform: translateY(-1px);
}

.ai-chat-btn:active {
  transform: translateY(0);
}

.ai-overview-shimmer {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.ai-shimmer-line {
  height: 0.75rem;
  border-radius: 0.25rem;
  background: var(--bg-hover);
}

.ai-loading-text {
  font-size: 0.875rem;
  color: var(--text-secondary);
  animation: pulse 1.5s infinite ease-in-out;
}

/* States (loading / empty / no results) */
.state-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 5rem 2rem;
  text-align: center;
}

.state-icon {
  width: 3.5rem;
  height: 3.5rem;
  color: var(--text-tertiary);
  margin-bottom: 1rem;
}

.state-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 0.375rem;
  color: var(--text-primary);
}

.state-subtitle {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.state-text {
  margin-top: 1rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

/* Skeleton loader */
.skeleton-item {
  pointer-events: none;
}

.skeleton-pulse {
  background: var(--bg-tertiary);
  border-radius: 0.25rem;
  position: relative;
  overflow: hidden;
}

.skeleton-pulse::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent 0%, var(--bg-hover) 50%, transparent 100%);
  animation: shimmer 1.4s ease-in-out infinite;
}

.skeleton-line {
  height: 0.75rem;
  border-radius: 0.25rem;
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

/* Results */
.results-list {
  padding: 0.75rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 0.625rem;
  background: var(--bg-elevated);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: background 0.2s;
}

.result-item:hover {
  background: var(--bg-tertiary);
}

.result-thumbnail {
  position: relative;
  flex-shrink: 0;
  width: 6rem;
  height: 4rem;
  border-radius: 0.375rem;
  overflow: hidden;
  background: var(--bg-tertiary);
}

.thumbnail-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.type-badge {
  position: absolute;
  bottom: 0.25rem;
  left: 0.25rem;
  font-size: 0.625rem;
  font-weight: 500;
  text-transform: uppercase;
  background: rgba(0, 0, 0, 0.7);
  color: #ffffff;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
}

.result-content {
  flex: 1;
  min-width: 0;
}

.result-title {
  font-size: 0.9375rem;
  font-weight: 600;
  line-height: 1.3;
  color: var(--text-primary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.result-description {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.result-author {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  margin-top: 0.25rem;
}

/* AI Chat View */
.ai-chat-view {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 130px); /* Expanded height without bottom nav */
  background: var(--bg-primary);
}

.chat-messages-list {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.chat-message-item {
  display: flex;
  flex-direction: column;
  max-width: 85%;
  animation: messageIn 0.25s ease-out;
}

@keyframes messageIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.chat-message-item.user {
  align-self: flex-end;
}

.chat-message-item.bot {
  align-self: flex-start;
}

.message-bubble {
  padding: 0.75rem 1rem;
  border-radius: 1rem;
  font-size: 0.9375rem;
  line-height: 1.45;
}

.chat-message-item.user .message-bubble {
  background-color: var(--accent);
  color: #ffffff;
  border-bottom-right-radius: 0.25rem;
}

.chat-message-item.bot .message-bubble {
  background-color: var(--bg-elevated);
  color: var(--text-primary);
  border: 1px solid var(--border-primary);
  border-bottom-left-radius: 0.25rem;
}

.chat-message-item.bot .message-bubble :deep(p) {
  margin-bottom: 0.5rem;
}
.chat-message-item.bot .message-bubble :deep(p:last-child) {
  margin-bottom: 0;
}
.chat-message-item.bot .message-bubble :deep(ul),
.chat-message-item.bot .message-bubble :deep(ol) {
  margin-left: 1.25rem;
  margin-bottom: 0.5rem;
}

.message-time-stamp {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  margin-top: 0.25rem;
  padding: 0 0.25rem;
}

.chat-message-item.user .message-time-stamp {
  text-align: right;
}

/* Chat Welcome State */
.chat-welcome-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 2rem;
  text-align: center;
  margin-top: auto;
  margin-bottom: auto;
}

.chat-welcome-icon {
  width: 3rem;
  height: 3rem;
  color: #8b5cf6;
  margin-bottom: 1rem;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-6px);
  }
}

.chat-welcome-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 0.375rem;
  color: var(--text-primary);
}

.chat-welcome-subtitle {
  color: var(--text-secondary);
  font-size: 0.875rem;
  max-width: 280px;
}

/* Chat Input Bar */
.chat-input-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--border-primary);
  background-color: var(--bg-primary);
}

.chat-input-field-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  background: var(--bg-input);
  border-radius: 1.25rem;
  padding: 0.5rem 1rem;
  border: 1px solid var(--border-primary);
}

.chat-input-field {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: 0.9375rem;
  color: var(--text-primary);
  padding: 0.125rem 0;
}

.chat-input-field::placeholder {
  color: var(--text-tertiary);
}

.chat-send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 50%;
  background: var(--accent);
  color: #ffffff;
  border: none;
  cursor: pointer;
  transition:
    opacity 0.2s,
    transform 0.1s;
}

.chat-send-btn:hover:not(:disabled) {
  opacity: 0.9;
  transform: scale(1.05);
}

.chat-send-btn:disabled {
  background: var(--bg-hover);
  color: var(--text-tertiary);
  cursor: not-allowed;
}

/* Typing indicator */
.bot-typing-indicator {
  display: flex;
  gap: 0.375rem;
  padding: 0.5rem 0.75rem;
}

.typing-dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background-color: var(--text-tertiary);
  animation: typingBounce 1.4s infinite ease-in-out both;
}

.typing-dot:nth-child(1) {
  animation-delay: -0.32s;
}
.typing-dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typingBounce {
  0%,
  80%,
  100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

@keyframes pulse {
  0%,
  100% {
    opacity: 0.6;
  }
  50% {
    opacity: 1;
  }
}
</style>
