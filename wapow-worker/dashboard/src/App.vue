<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'

// Interface definitions
interface Job {
  id: string
  name: string
  trigger: string
  next_run: string | null
  status: 'active' | 'paused'
  running?: boolean
}

interface RunArticle {
  id: string
  title: string
}

interface ScraperRun {
  _id?: string
  job_id: string
  start_time: string
  duration_seconds: number | null
  status: 'success' | 'failed' | 'running'
  items_scraped: number
  items_saved: number
  saved_articles?: RunArticle[]
  errors?: string[]
}

interface Source {
  name: string
  url: string
  type: 'rss'
  category: string
  enabled: boolean
  last_scraped_at?: string | null
  last_duration_seconds?: number | null
  last_status?: string
  last_items_scraped?: number
  last_items_saved?: number
  last_error?: string
}

interface IngestedArticle {
  id: string
  title: string
  publisher: string
  category: string
  created_date: string
  url: string
}

// ----------------------------------------------------
// State Management
// ----------------------------------------------------
const activeTab = ref<'overview' | 'sources' | 'logs' | 'articles'>('overview')
const lastUpdated = ref<string>('Syncing...')

// Stats KPIs
const totalArticles = ref<number>(0)
const totalRuns = ref<number>(0)
const successRatePercent = ref<number>(0)
const totalScraped = ref<number>(0)
const totalSaved = ref<number>(0)

// Scheduler and Worker State
const schedulerActive = ref<boolean>(false)
const workerPaused = ref<boolean>(false)
const jobs = ref<Job[]>([])

// Runs History & Pagination
const recentRuns = ref<ScraperRun[]>([])
const runsPage = ref<number>(1)
const runsLimit = ref<number>(10)
const runsTotalPages = ref<number>(1)
const runsTotal = ref<number>(0)

// Sources Telemetry configuration
const sources = ref<Source[]>([])
const sourceFilter = ref<'all' | 'success' | 'failed' | 'never run' | 'disabled'>('all')
const selectedCategory = ref<string>('all')
const sourceSearchQuery = ref<string>('')
const viewMode = ref<'table' | 'grid'>('grid')

// Ingested Articles list & Pagination
const recentArticles = ref<IngestedArticle[]>([])
const articlesPage = ref<number>(1)
const articlesLimit = ref<number>(10)
const articlesTotalPages = ref<number>(1)
const articlesTotal = ref<number>(0)

// Expanded items (JSON viewers)
const expandedArticles = ref<Set<string>>(new Set())
const loadedArticleJSONs = ref<Record<string, string>>({})

// SSE Logging Console State
const logsConsole = ref<HTMLDivElement | null>(null)
const logLines = ref<{ text: string; type: 'info' | 'error' | 'warn' | 'system' | 'success' }[]>([])
const loggerConnStatus = ref<'Connecting...' | 'Live Stream Active' | 'Offline'>('Connecting...')
let eventSource: EventSource | null = null

// Modal Dialog state for Adding/Editing Source
const showModal = ref<boolean>(false)
const modalMode = ref<'add' | 'edit'>('add')
const oldSourceName = ref<string>('')
const sourceForm = ref({
  type: 'rss' as 'rss',
  name: '',
  url: '',
  category: '',
  enabled: true
})

// Toast notification banner state
const toastMsg = ref<string>('')
const toastIsError = ref<boolean>(false)
const toastVisible = ref<boolean>(false)
let toastTimeout: ReturnType<typeof setTimeout> | null = null

// Loading indicator
const triggeringJob = ref<boolean>(false)

// ----------------------------------------------------
// Utility Actions
// ----------------------------------------------------
function showToast(message: string, isError = false) {
  if (toastTimeout) clearTimeout(toastTimeout)
  toastMsg.value = message
  toastIsError.value = isError
  toastVisible.value = true
  toastTimeout = setTimeout(() => {
    toastVisible.value = false
  }, 4000)
}

function clearConsole() {
  logLines.value = []
}

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text)
    .then(() => showToast('Copied to clipboard.'))
    .catch(() => showToast('Failed to copy.', true))
}

// ----------------------------------------------------
// API Requests
// ----------------------------------------------------
async function fetchStats() {
  try {
    const res = await fetch('/api/stats')
    if (!res.ok) throw new Error('Failed to fetch statistics')
    const data = await res.json()

    totalArticles.value = data.total_articles || 0
    totalRuns.value = data.summary?.total_runs || 0
    successRatePercent.value = data.summary?.success_rate_percent || 0
    totalScraped.value = data.summary?.total_scraped || 0
    totalSaved.value = data.summary?.total_saved || 0
    sources.value = data.sources || []

    lastUpdated.value = `Last synced: ${new Date().toLocaleTimeString()}`
  } catch (err: any) {
    console.error('Error fetching stats:', err)
  }
}

async function fetchRuns(page: number = 1) {
  try {
    const res = await fetch(`/api/runs?page=${page}&limit=${runsLimit.value}`)
    if (!res.ok) {
      if (res.status === 404) {
        // Fallback to legacy endpoint from /api/stats if individual paginated endpoint 404s
        const statsRes = await fetch('/api/stats')
        if (statsRes.ok) {
          const statsData = await statsRes.json()
          const allRuns = statsData.recent_runs || []
          recentRuns.value = allRuns.slice(0, runsLimit.value)
          runsPage.value = 1
          runsTotalPages.value = 1
          runsTotal.value = allRuns.length
          return
        }
      }
      throw new Error(`Failed to fetch runs: Status ${res.status}`)
    }
    const data = await res.json()
    recentRuns.value = data.runs || []
    runsPage.value = data.page || 1
    runsTotalPages.value = data.total_pages || 1
    runsTotal.value = data.total || 0
  } catch (err: any) {
    console.error('Error fetching runs:', err)
  }
}

async function fetchArticles(page: number = 1) {
  try {
    const res = await fetch(`/api/articles?page=${page}&limit=${articlesLimit.value}`)
    if (!res.ok) {
      if (res.status === 404) {
        // Fallback to legacy endpoint from /api/stats if individual paginated endpoint 404s
        const statsRes = await fetch('/api/stats')
        if (statsRes.ok) {
          const statsData = await statsRes.json()
          const allArticles = statsData.recent_articles || []
          recentArticles.value = allArticles.slice(0, articlesLimit.value)
          articlesPage.value = 1
          articlesTotalPages.value = 1
          articlesTotal.value = allArticles.length
          return
        }
      }
      throw new Error(`Failed to fetch articles: Status ${res.status}`)
    }
    const data = await res.json()
    recentArticles.value = data.articles || []
    articlesPage.value = data.page || 1
    articlesTotalPages.value = data.total_pages || 1
    articlesTotal.value = data.total || 0
  } catch (err: any) {
    console.error('Error fetching articles:', err)
  }
}

async function handleManualRefresh() {
  showToast('Syncing statistics and runs...')
  await fetchStats()
  await fetchJobs()
  await fetchRuns(runsPage.value)
  await fetchArticles(articlesPage.value)
}

async function fetchJobs() {
  try {
    const res = await fetch('/jobs')
    if (!res.ok) throw new Error('Failed to fetch jobs')
    const data = await res.json()
    jobs.value = data.jobs || []
    workerPaused.value = data.worker_paused ?? false

    const healthRes = await fetch('/health')
    if (healthRes.ok) {
      const healthData = await healthRes.json()
      schedulerActive.value = healthData.scheduler === 'running'
    }
  } catch (err) {
    console.error('Error fetching jobs:', err)
  }
}

// Manually trigger a crawler
async function triggerJob(jobId: string) {
  triggeringJob.value = true
  showToast(`Scraper job [${jobId}] triggered...`)
  activeTab.value = 'logs'

  try {
    const response = await fetch(`/jobs/${jobId}/trigger`, { method: 'POST' })
    const result = await response.json()
    if (response.ok) {
      const saved = result.result?.saved ?? result.result?.total_saved ?? 0
      showToast(`Synced ${saved} new articles.`)
    } else {
      showToast(`Error: ${result.detail || 'Scraper run failed'}`, true)
    }
  } catch (err: any) {
    showToast(`Trigger failed: ${err.message}`, true)
  } finally {
    triggeringJob.value = false
    await fetchStats()
  }
}

// Manually stop a running job
async function stopJob(jobId: string) {
  showToast(`Stopping job [${jobId}]...`)
  try {
    const response = await fetch(`/jobs/${jobId}/stop`, { method: 'POST' })
    const result = await response.json()
    if (response.ok) {
      showToast(`Job ${jobId} stop signal sent successfully.`)
    } else {
      showToast(`Stop failed: ${result.detail || 'Unknown error'}`, true)
    }
  } catch (err: any) {
    showToast(`Stop request failed: ${err.message}`, true)
  } finally {
    await fetchJobs()
    await fetchStats()
  }
}

// Job Controls
async function handleToggleJob(jobId: string, isPaused: boolean) {
  const endpoint = `/jobs/${jobId}/${isPaused ? 'resume' : 'pause'}`
  try {
    const res = await fetch(endpoint, { method: 'POST' })
    if (res.ok) {
      showToast(`Scheduler job ${jobId} successfully ${isPaused ? 'resumed' : 'paused'}.`)
      await fetchJobs()
    } else {
      const err = await res.json()
      showToast(`Action failed: ${err.detail || 'Unknown error'}`, true)
    }
  } catch (err: any) {
    showToast(`Connection failed: ${err.message}`, true)
  }
}

// Conversion Worker Controls
async function handleToggleWorker(isCurrentlyPaused: boolean) {
  const endpoint = `/worker/${isCurrentlyPaused ? 'resume' : 'pause'}`
  try {
    const res = await fetch(endpoint, { method: 'POST' })
    if (res.ok) {
      showToast(`Background conversion worker successfully ${isCurrentlyPaused ? 'resumed' : 'paused'}.`)
      await fetchJobs()
    } else {
      const err = await res.json()
      showToast(`Action failed: ${err.detail || 'Unknown error'}`, true)
    }
  } catch (err: any) {
    showToast(`Connection failed: ${err.message}`, true)
  }
}

// ----------------------------------------------------
// Source CRUD Operations
// ----------------------------------------------------
async function toggleSource(type: string, name: string) {
  try {
    const res = await fetch('/api/sources/toggle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type, name })
    })
    const data = await res.json()
    if (res.ok) {
      showToast(data.message)
      await fetchStats()
    } else {
      showToast(`Error: ${data.detail || 'Failed to toggle source'}`, true)
    }
  } catch (err: any) {
    showToast(`Connection failed: ${err.message}`, true)
  }
}

async function deleteSource(type: string, name: string) {
  if (!confirm(`Are you sure you want to delete the scraping source '${name}'?`)) return
  try {
    const res = await fetch('/api/sources/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type, name })
    })
    const data = await res.json()
    if (res.ok) {
      showToast(data.message)
      await fetchStats()
    } else {
      showToast(`Error: ${data.detail || 'Failed to delete source'}`, true)
    }
  } catch (err: any) {
    showToast(`Connection failed: ${err.message}`, true)
  }
}

async function disableAllFailing() {
  if (failedSources.value.length === 0) return
  if (!confirm(`Are you sure you want to disable all failing sources?`)) return
  showToast("Disabling all failing sources...")
  try {
    await Promise.all(failedSources.value.map(async (src) => {
      const res = await fetch('/api/sources/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: src.type, name: src.name })
      })
      if (!res.ok) throw new Error(`Failed to toggle ${src.name}`)
    }))
    showToast("Successfully disabled all failing sources.")
    await fetchStats()
  } catch (err: any) {
    showToast(`Failed: ${err.message}`, true)
  }
}

async function disableAllActive() {
  if (activeSources.value.length === 0) return
  if (!confirm(`Are you sure you want to disable all active sources?`)) return
  showToast("Disabling all active sources...")
  try {
    await Promise.all(activeSources.value.map(async (src) => {
      const res = await fetch('/api/sources/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: src.type, name: src.name })
      })
      if (!res.ok) throw new Error(`Failed to toggle ${src.name}`)
    }))
    showToast("Successfully disabled all active sources.")
    await fetchStats()
  } catch (err: any) {
    showToast(`Failed: ${err.message}`, true)
  }
}

async function enableAllDisabled() {
  if (disabledSources.value.length === 0) return
  if (!confirm(`Are you sure you want to enable all disabled sources?`)) return
  showToast("Enabling all disabled sources...")
  try {
    await Promise.all(disabledSources.value.map(async (src) => {
      const res = await fetch('/api/sources/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: src.type, name: src.name })
      })
      if (!res.ok) throw new Error(`Failed to toggle ${src.name}`)
    }))
    showToast("Successfully enabled all disabled sources.")
    await fetchStats()
  } catch (err: any) {
    showToast(`Failed: ${err.message}`, true)
  }
}

async function deleteAllDisabled() {
  if (disabledSources.value.length === 0) return
  if (!confirm(`Are you sure you want to delete all disabled sources?`)) return
  showToast("Deleting all disabled sources...")
  try {
    await Promise.all(disabledSources.value.map(async (src) => {
      const res = await fetch('/api/sources/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: src.type, name: src.name })
      })
      if (!res.ok) throw new Error(`Failed to delete ${src.name}`)
    }))
    showToast("Successfully deleted all disabled sources.")
    await fetchStats()
  } catch (err: any) {
    showToast(`Failed: ${err.message}`, true)
  }
}

// Modal Form handling
function openAddSourceModal() {
  modalMode.value = 'add'
  oldSourceName.value = ''
  sourceForm.value = {
    type: 'rss',
    name: '',
    url: '',
    category: '',
    enabled: true
  }
  showModal.value = true
}

function openEditSourceModal(type: 'rss', name: string) {
  modalMode.value = 'edit'
  oldSourceName.value = name
  const existing = sources.value.find(s => s.type === type && s.name === name)

  if (existing) {
    sourceForm.value = {
      type: existing.type,
      name: existing.name,
      url: existing.url,
      category: existing.category,
      enabled: existing.enabled
    }
    showModal.value = true
  } else {
    showToast('Source not found in cache.', true)
  }
}

async function handleSaveSource() {
  // Simple validation
  if (!sourceForm.value.name.trim() || !sourceForm.value.url.trim() || !sourceForm.value.category.trim()) {
    showToast('Please fill out name, URL, and category fields.', true)
    return
  }

  const endpoint = modalMode.value === 'add' ? '/api/sources/add' : '/api/sources/edit'
  const payload = modalMode.value === 'add'
    ? { ...sourceForm.value }
    : { ...sourceForm.value, old_name: oldSourceName.value }

  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    const data = await res.json()
    if (res.ok) {
      showToast(data.message)
      showModal.value = false
      await fetchStats()
    } else {
      showToast(`Error: ${data.detail || 'Save failed'}`, true)
    }
  } catch (err: any) {
    showToast(`Connection failed: ${err.message}`, true)
  }
}

// Collapsible MongoDB JSON article renderer helper
async function toggleArticleJSON(articleId: string, containerKey: string) {
  const isExpanded = expandedArticles.value.has(containerKey)
  if (!isExpanded) {
    expandedArticles.value.add(containerKey)
    if (!loadedArticleJSONs.value[articleId]) {
      loadedArticleJSONs.value[articleId] = 'Fetching document from MongoDB articles collection...'
      try {
        const res = await fetch(`/api/articles/${articleId}`)
        if (!res.ok) throw new Error(`Status ${res.status}`)
        const data = await res.json()
        loadedArticleJSONs.value[articleId] = JSON.stringify(data, null, 2)
      } catch (err: any) {
        loadedArticleJSONs.value[articleId] = `Failed to retrieve document from MongoDB.\n\nDetails:\n${err.message}`
      }
    }
  } else {
    expandedArticles.value.delete(containerKey)
  }
}

function copyArticleJSON(articleId: string) {
  const text = loadedArticleJSONs.value[articleId]
  if (!text) return
  navigator.clipboard.writeText(text)
    .then(() => showToast('Copied JSON document to clipboard.'))
    .catch(() => showToast('Failed to copy JSON.', true))
}

// ----------------------------------------------------
// SSE Connection setup
// ----------------------------------------------------
function connectLogsStream() {
  if (eventSource) {
    eventSource.close()
  }

  loggerConnStatus.value = 'Connecting...'
  try {
    eventSource = new EventSource('/api/logs/stream')
    eventSource.onopen = () => {
      loggerConnStatus.value = 'Live Stream Active'
    }
    eventSource.onmessage = (event) => {
      const data = event.data
      if (!data) return
      const lines = data.split('\n')
      lines.forEach((line: string) => {
        if (!line.trim()) return
        
        let type: 'info' | 'error' | 'warn' | 'system' | 'success' = 'info'
        if (line.includes('[ERROR]')) type = 'error'
        else if (line.includes('[WARNING]') || line.includes('[warn]')) type = 'warn'
        else if (line.includes('[SYSTEM]')) type = 'system'
        else if (line.includes('Successfully extracted article') || line.includes('Scraped') || line.includes('Saved')) type = 'success'

        logLines.value.push({ text: line, type })
      })

      // Cap at 1500 logs to prevent memory leaks
      if (logLines.value.length > 1500) {
        logLines.value = logLines.value.slice(logLines.value.length - 1000)
      }

      // Autoscroll
      nextTick(() => {
        if (logsConsole.value) {
          logsConsole.value.scrollTop = logsConsole.value.scrollHeight
        }
      })
    }
    eventSource.onerror = () => {
      loggerConnStatus.value = 'Offline'
    }
  } catch (err) {
    console.error('SSE Error:', err)
    loggerConnStatus.value = 'Offline'
  }
}

// ----------------------------------------------------
// Computed & Watchers
// ----------------------------------------------------
const uniqueCategories = computed(() => {
  const cats = new Set<string>()
  sources.value.forEach(s => {
    if (s.category) cats.add(s.category)
  })
  return Array.from(cats).sort()
})

const filteredSources = computed(() => {
  return sources.value.filter(s => {
    // 1. Filter by category sidebar
    if (selectedCategory.value !== 'all' && s.category !== selectedCategory.value) {
      return false
    }
    // 2. Filter by status dropdown
    if (sourceFilter.value !== 'all') {
      if (sourceFilter.value === 'disabled') {
        if (s.enabled) return false
      } else {
        if (!s.enabled || s.last_status !== sourceFilter.value) return false
      }
    }
    // 3. Filter by search input
    if (sourceSearchQuery.value.trim()) {
      const q = sourceSearchQuery.value.toLowerCase()
      const nameMatch = s.name.toLowerCase().includes(q)
      const urlMatch = s.url.toLowerCase().includes(q)
      if (!nameMatch && !urlMatch) return false
    }
    return true
  })
})

const failedSources = computed(() => {
  return filteredSources.value.filter(s => s.enabled && s.last_status === 'failed')
})

const activeSources = computed(() => {
  return filteredSources.value.filter(s => s.enabled && s.last_status !== 'failed')
})

const disabledSources = computed(() => {
  return filteredSources.value.filter(s => !s.enabled)
})

const activeSourcesCount = computed(() => {
  return sources.value.length
})

// Periodic auto-sync statistics
let syncInterval: ReturnType<typeof setInterval> | null = null

onMounted(async () => {
  await fetchStats()
  await fetchJobs()
  await fetchRuns(runsPage.value)
  await fetchArticles(articlesPage.value)
  connectLogsStream()

  syncInterval = setInterval(async () => {
    await fetchStats()
    await fetchJobs()
    await fetchRuns(runsPage.value)
    await fetchArticles(articlesPage.value)
  }, 6000)
})

onUnmounted(() => {
  if (syncInterval) clearInterval(syncInterval)
  if (eventSource) eventSource.close()
})
</script>

<template>
  <div class="h-full flex flex-col antialiased selection:bg-[#333333] selection:text-white">
    <!-- Top Navbar -->
    <header class="flex-shrink-0 bg-black border-b border-[#1f1f1f] px-8 py-3 flex items-center justify-between">
      <div class="flex items-center gap-6">
        <svg class="h-5 w-5 text-white" fill="currentColor" viewBox="0 0 100 100">
          <polygon points="50,15 90,85 10,85" />
        </svg>
        <div class="flex items-center gap-2 text-sm">
          <span class="text-[#a1a1a1]">ruthvik-vijayakumar</span>
          <span class="text-[#333333]">/</span>
          <span class="font-medium text-white">wapow-worker</span>
          <span class="ml-2 bg-[#1f1f1f] text-xs font-mono text-[#a1a1a1] px-2 py-0.5 rounded border border-[#333333]">production</span>
        </div>
      </div>
      <div class="flex items-center gap-4">
        <span class="text-xs text-[#666666]">{{ lastUpdated }}</span>
        <div :class="[
          'flex items-center gap-2 px-3 py-1 rounded border text-xs font-medium bg-black',
          schedulerActive 
            ? 'border-emerald-900/30 text-emerald-400' 
            : 'border-rose-900/30 text-rose-400'
        ]">
          <span :class="[
            'h-1.5 w-1.5 rounded-full',
            schedulerActive ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'
          ]"></span>
          <span>Scheduler: {{ schedulerActive ? 'active' : 'inactive' }}</span>
        </div>
      </div>
    </header>

    <!-- Sub-navigation Tabs -->
    <div class="bg-black border-b border-[#1f1f1f] px-8 flex-shrink-0">
      <div class="flex gap-6 text-sm">
        <button 
          @click="activeTab = 'overview'" 
          :class="[
            'py-3 border-b-2 font-medium focus:outline-none transition cursor-pointer flex items-center gap-2',
            activeTab === 'overview' ? 'border-white text-white' : 'border-transparent text-[#a1a1a1] hover:text-white'
          ]"
        >
          Overview
        </button>
        <button 
          @click="activeTab = 'sources'" 
          :class="[
            'py-3 border-b-2 focus:outline-none transition cursor-pointer flex items-center gap-2',
            activeTab === 'sources' ? 'border-white text-white' : 'border-transparent text-[#a1a1a1] hover:text-white'
          ]"
        >
          Sources Telemetry
          <span class="bg-[#1f1f1f] text-xs text-[#a1a1a1] px-1.5 py-0.2 rounded font-mono font-medium border border-[#333333]">{{ activeSourcesCount }}</span>
        </button>
        <button 
          @click="activeTab = 'logs'" 
          :class="[
            'py-3 border-b-2 focus:outline-none transition cursor-pointer flex items-center gap-2',
            activeTab === 'logs' ? 'border-white text-white' : 'border-transparent text-[#a1a1a1] hover:text-white'
          ]"
        >
          <span class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
          Live Console
        </button>
        <button 
          @click="activeTab = 'articles'" 
          :class="[
            'py-3 border-b-2 focus:outline-none transition cursor-pointer flex items-center gap-2',
            activeTab === 'articles' ? 'border-white text-white' : 'border-transparent text-[#a1a1a1] hover:text-white'
          ]"
        >
          Ingested Stories
        </button>
      </div>
    </div>

    <!-- Main Container Area -->
    <main class="flex-grow p-8 overflow-y-auto custom-scroll flex flex-col space-y-8 max-w-7xl w-full mx-auto">
      
      <!-- TAB 1: OVERVIEW -->
      <div v-if="activeTab === 'overview'" class="space-y-8">
        <!-- Vercel Grid KPI counters -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div class="bg-[#0a0a0a] border border-[#1f1f1f] p-6 rounded-lg flex flex-col">
            <span class="text-xs font-semibold tracking-wider text-[#666666] uppercase">Total Ingested Articles</span>
            <span class="text-3xl font-bold font-mono mt-3 text-white tracking-tight">{{ totalArticles.toLocaleString() }}</span>
          </div>
          <div class="bg-[#0a0a0a] border border-[#1f1f1f] p-6 rounded-lg flex flex-col">
            <span class="text-xs font-semibold tracking-wider text-[#666666] uppercase">Runs Recorded (100)</span>
            <span class="text-3xl font-bold font-mono mt-3 text-white tracking-tight">{{ totalRuns }}</span>
          </div>
          <div class="bg-[#0a0a0a] border border-[#1f1f1f] p-6 rounded-lg flex flex-col">
            <span class="text-xs font-semibold tracking-wider text-[#666666] uppercase">Scrape Success Rate</span>
            <span class="text-3xl font-bold font-mono mt-3 text-white tracking-tight">{{ successRatePercent }}%</span>
          </div>
          <div class="bg-[#0a0a0a] border border-[#1f1f1f] p-6 rounded-lg flex flex-col">
            <span class="text-xs font-semibold tracking-wider text-[#666666] uppercase">Scraped / Saved Items</span>
            <span class="text-3xl font-bold font-mono mt-3 text-white tracking-tight">{{ totalScraped }} / {{ totalSaved }}</span>
          </div>
        </div>

        <!-- Scheduler & Worker Control -->
        <div class="bg-[#0a0a0a] border border-[#1f1f1f] rounded-lg overflow-hidden">
          <div class="p-6 border-b border-[#1f1f1f] flex items-center justify-between">
            <div class="space-y-1">
              <h2 class="text-base font-bold text-white">Scheduler & Worker Control</h2>
              <p class="text-xs text-[#a1a1a1]">Pause/resume scheduled crawling jobs and background slide conversion tasks</p>
            </div>
            <!-- Sync/refresh button in card header -->
            <button 
              @click="handleManualRefresh" 
              :disabled="triggeringJob" 
              class="bg-[#1f1f1f] text-[#a1a1a1] hover:text-white px-3 py-2 rounded border border-[#333333] transition flex items-center justify-center cursor-pointer disabled:opacity-40"
              title="Sync stats and jobs"
            >
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 8H18.2M7 9a4 4 0 110-8h1.5" />
              </svg>
            </button>
          </div>
          <div class="divide-y divide-[#1f1f1f]">
            <!-- Dynamic scheduler jobs list -->
            <div v-for="job in jobs" :key="job.id" class="p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div class="space-y-1">
                <div class="flex items-center gap-2">
                  <h3 class="text-sm font-semibold text-white font-mono">{{ job.name }}</h3>
                  <span :class="[
                    'inline-flex border px-2 py-0.5 rounded text-[10px] font-medium tracking-wider lowercase',
                    job.status === 'paused' 
                      ? 'border-rose-500/20 bg-rose-500/10 text-rose-450' 
                      : 'border-emerald-500/20 bg-emerald-500/10 text-emerald-450'
                  ]">{{ job.status }}</span>
                </div>
                <p class="text-xs text-[#a1a1a1]">Instantly trigger or terminate WAPOW aggregator runs for all enabled RSS feed sources</p>
                <div class="flex flex-wrap gap-x-4 gap-y-1 mt-1 text-[11px] text-[#666666]">
                  <span>Trigger interval: <span class="font-mono text-white">{{ job.trigger }}</span></span>
                  <span>Next Run: <span class="font-mono text-[#888]">{{ job.next_run ? new Date(job.next_run).toLocaleString() : 'Paused' }}</span></span>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <button 
                  @click="handleToggleJob(job.id, job.status === 'paused')"
                  :disabled="job.running"
                  :class="[
                    'text-xs font-semibold px-3 py-1.5 rounded transition cursor-pointer',
                    job.running
                      ? 'opacity-40 cursor-not-allowed bg-neutral-800 text-neutral-500 border border-neutral-700'
                      : job.status === 'paused'
                        ? 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20'
                        : 'bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20'
                  ]"
                >
                  {{ job.status === 'paused' ? 'Resume' : 'Pause' }}
                </button>
                <button 
                  v-if="!job.running"
                  @click="triggerJob(job.id)"
                  :disabled="triggeringJob"
                  class="bg-white hover:bg-[#e0e0e0] text-black text-xs font-semibold px-3 py-1.5 rounded transition cursor-pointer disabled:bg-neutral-800 disabled:text-neutral-500"
                >
                  Run Now
                </button>
                <button 
                  v-else
                  @click="stopJob(job.id)"
                  class="bg-rose-950/20 hover:bg-rose-900/40 border border-rose-900/30 hover:border-rose-800 text-rose-400 text-xs font-semibold px-3 py-1.5 rounded transition cursor-pointer animate-pulse"
                >
                  Stop
                </button>
              </div>
            </div>

            <!-- Background AI conversion worker control -->
            <div class="p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div class="space-y-1">
                <div class="flex items-center gap-2">
                  <h3 class="text-sm font-semibold text-white">Background Conversion Worker</h3>
                  <span :class="[
                    'inline-flex border px-2 py-0.5 rounded text-[10px] font-medium tracking-wider lowercase',
                    workerPaused 
                      ? 'border-rose-500/20 bg-rose-500/10 text-rose-455' 
                      : 'border-emerald-500/20 bg-emerald-500/10 text-emerald-455'
                  ]">{{ workerPaused ? 'paused' : 'running' }}</span>
                </div>
                <p class="text-xs text-[#a1a1a1]">Processes raw scraped documents in MongoDB and triggers the Gemini AI slide deck generation pipeline</p>
              </div>
              <div class="flex items-center gap-2">
                <button 
                  @click="handleToggleWorker(workerPaused)"
                  :class="[
                    'text-xs font-semibold px-3 py-1.5 rounded transition cursor-pointer',
                    workerPaused
                      ? 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20'
                      : 'bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20'
                  ]"
                >
                  {{ workerPaused ? 'Resume Worker' : 'Pause Worker' }}
                </button>
              </div>
            </div>
          </div>
        </div>


        <!-- Job Executions Log -->
        <div class="bg-[#0a0a0a] border border-[#1f1f1f] rounded-lg overflow-hidden">
          <div class="p-6 border-b border-[#1f1f1f]">
            <h2 class="text-base font-bold text-white">Worker Execution Runs</h2>
            <p class="text-xs text-[#666666] mt-0.5">Historical logs and runtime traces for worker triggers</p>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left text-sm text-[#e5e5e5]">
              <thead class="text-xs uppercase bg-[#000] text-[#888888] border-b border-[#1f1f1f]">
                <tr>
                  <th class="py-3.5 px-6 font-semibold">Job Name</th>
                  <th class="py-3.5 px-6 font-semibold">Start Time</th>
                  <th class="py-3.5 px-6 font-semibold">Duration</th>
                  <th class="py-3.5 px-6 font-semibold">Status</th>
                  <th class="py-3.5 px-6 font-semibold">Scraped</th>
                  <th class="py-3.5 px-6 font-semibold">Saved</th>
                  <th class="py-3.5 px-6 font-semibold">Error Logs</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[#1f1f1f]">
                <tr v-if="recentRuns.length === 0">
                  <td colspan="7" class="py-8 text-center text-[#666666]">No runs recorded yet.</td>
                </tr>
                <tr v-for="run in recentRuns" :key="run._id || run.start_time" class="align-top hover:bg-[#0a0a0a] transition duration-150">
                  <td class="py-4 px-6 font-semibold font-mono text-xs text-white">{{ run.job_id }}</td>
                  <td class="py-4 px-6 text-xs text-[#888888]">{{ new Date(run.start_time).toLocaleString() }}</td>
                  <td class="py-4 px-6 text-xs font-mono text-[#888888]">{{ run.duration_seconds ? `${run.duration_seconds.toFixed(1)}s` : '-' }}</td>
                  <td class="py-4 px-6">
                    <span v-if="run.status === 'success'" class="inline-flex border border-emerald-500/20 bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded text-[10px] font-medium lowercase">success</span>
                    <span v-else-if="run.status === 'failed'" class="inline-flex border border-rose-500/20 bg-rose-500/10 text-rose-400 px-2 py-0.5 rounded text-[10px] font-medium lowercase">failed</span>
                    <span v-else class="inline-flex border border-amber-500/20 bg-amber-500/10 text-amber-400 px-2 py-0.5 rounded text-[10px] font-medium lowercase animate-pulse">running</span>
                  </td>
                  <td class="py-4 px-6 text-xs font-mono text-[#888888]">{{ run.items_scraped }}</td>
                  <td class="py-4 px-6 text-xs font-mono text-white font-medium">{{ run.items_saved }}</td>
                  <td class="py-4 px-6">
                    <!-- Errors during this run -->
                    <div v-if="run.errors && run.errors.length > 0" class="text-[11px] border border-rose-950/40 bg-rose-950/5 text-rose-400 p-3 rounded">
                      <strong class="text-[9px] uppercase font-semibold tracking-wider block mb-1">Errors:</strong>
                      <ul class="space-y-1 list-disc pl-4 max-h-[100px] overflow-y-auto custom-scroll font-mono text-[10px]">
                        <li v-for="(err, idx) in run.errors" :key="idx">{{ err }}</li>
                      </ul>
                    </div>

                    <span v-if="!run.errors || run.errors.length === 0" class="text-[#444444] italic text-xs">None</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <!-- Pagination Controls for Runs -->
          <div class="flex items-center justify-between border-t border-[#1f1f1f] bg-black px-6 py-4">
            <div class="text-xs text-[#a1a1a1]">
              Showing <span class="font-mono font-medium text-white">{{ runsTotal > 0 ? (runsPage - 1) * runsLimit + 1 : 0 }}</span> to
              <span class="font-mono font-medium text-white">{{ Math.min(runsPage * runsLimit, runsTotal) }}</span> of
              <span class="font-mono font-medium text-white">{{ runsTotal }}</span> runs
            </div>
            <div class="flex items-center gap-2">
              <button
                @click="fetchRuns(runsPage - 1)"
                :disabled="runsPage === 1"
                class="bg-[#111] hover:bg-neutral-900 border border-[#333333] disabled:opacity-40 disabled:hover:bg-[#111] text-white text-xs font-semibold px-3 py-1.5 rounded transition cursor-pointer"
              >
                Previous
              </button>
              <span class="text-xs text-[#a1a1a1] font-mono mx-2">Page {{ runsPage }} of {{ runsTotalPages }}</span>
              <button
                @click="fetchRuns(runsPage + 1)"
                :disabled="runsPage === runsTotalPages"
                class="bg-[#111] hover:bg-neutral-900 border border-[#333333] disabled:opacity-40 disabled:hover:bg-[#111] text-white text-xs font-semibold px-3 py-1.5 rounded transition cursor-pointer"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- TAB 2: SOURCES CONFIGURATION & TELEMETRY -->
      <div v-if="activeTab === 'sources'" class="flex flex-col lg:flex-row gap-8 items-start">
        
        <!-- Category Left Sidebar -->
        <aside class="w-full lg:w-64 flex-shrink-0 bg-[#0a0a0a] border border-[#1f1f1f] rounded-lg p-4 space-y-1">
          <div class="px-3 py-2 text-xs font-bold uppercase tracking-wider text-[#666666] mb-2">Categories</div>
          
          <button 
            @click="selectedCategory = 'all'" 
            :class="[
              'w-full text-left px-3 py-2 rounded-lg text-xs font-semibold flex items-center justify-between transition cursor-pointer',
              selectedCategory === 'all' 
                ? 'bg-[#161616] text-white border-l-2 border-white pl-2' 
                : 'text-[#888] hover:text-white hover:bg-[#0f0f0f]'
            ]"
          >
            <span>All Sources</span>
            <span class="bg-[#1a1a1a] text-[10px] text-[#888] px-2 py-0.5 rounded border border-[#2c2c2c] font-mono">{{ sources.length }}</span>
          </button>

          <button 
            v-for="cat in uniqueCategories" 
            :key="cat"
            @click="selectedCategory = cat" 
            :class="[
              'w-full text-left px-3 py-2 rounded-lg text-xs font-semibold flex items-center justify-between transition cursor-pointer capitalize',
              selectedCategory === cat 
                ? 'bg-[#161616] text-white border-l-2 border-white pl-2' 
                : 'text-[#888] hover:text-white hover:bg-[#0f0f0f]'
            ]"
          >
            <span>{{ cat }}</span>
            <span class="bg-[#1a1a1a] text-[10px] text-[#888] px-2 py-0.5 rounded border border-[#2c2c2c] font-mono">
              {{ sources.filter(s => s.category === cat).length }}
            </span>
          </button>
        </aside>

        <!-- Main Sources Telemetry Dashboard -->
        <div class="flex-grow w-full space-y-8">
          <!-- Filter / Control Bar -->
          <div class="bg-[#0a0a0a] border border-[#1f1f1f] rounded-lg p-5 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div class="flex-grow max-w-md relative">
              <input 
                v-model="sourceSearchQuery" 
                type="text" 
                placeholder="Search sources by name or URL..." 
                class="w-full bg-black border border-[#2c2c2c] hover:border-[#3c3c3c] focus:border-white text-xs text-[#fafafa] rounded px-3 py-2 focus:outline-none transition font-medium"
              />
              <span v-if="sourceSearchQuery" @click="sourceSearchQuery = ''" class="absolute right-3 top-2 text-neutral-500 hover:text-white cursor-pointer text-xs">✕</span>
            </div>
            
            <div class="flex items-center gap-3 justify-end flex-wrap">
              <select 
                v-model="sourceFilter" 
                class="bg-black border border-[#2c2c2c] text-xs text-[#fafafa] rounded px-3 py-2 focus:outline-none focus:border-white cursor-pointer font-medium"
              >
                <option value="all">All Statuses</option>
                <option value="success">Success Only</option>
                <option value="failed">Failed Only</option>
                <option value="never run">Never Run</option>
                <option value="disabled">Disabled Only</option>
              </select>

              <!-- Vercel-style Layout Toggle -->
              <div class="flex items-center border border-[#2c2c2c] rounded p-0.5 bg-black">
                <button
                  @click="viewMode = 'table'"
                  :class="[
                    'px-3 py-1 rounded text-xs font-semibold cursor-pointer transition',
                    viewMode === 'table' ? 'bg-[#1f1f1f] text-white' : 'text-[#888] hover:text-white'
                  ]"
                >
                  Table
                </button>
                <button
                  @click="viewMode = 'grid'"
                  :class="[
                    'px-3 py-1 rounded text-xs font-semibold cursor-pointer transition',
                    viewMode === 'grid' ? 'bg-[#1f1f1f] text-white' : 'text-[#888] hover:text-white'
                  ]"
                >
                  Cards
                </button>
              </div>

              <button 
                @click="openAddSourceModal" 
                class="bg-white hover:bg-[#e6e6e6] text-black font-semibold text-xs py-2 px-4 rounded transition duration-200 cursor-pointer flex items-center gap-1.5"
              >
                <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4" />
                </svg>
                Add RSS Feed
              </button>
            </div>
          </div>
          <!-- Filtered Sources Lists Grouped by Category -->
          <div v-if="filteredSources.length > 0" class="space-y-10">
            
            <!-- SECTION 1: Needs Attention -->
            <div v-if="failedSources.length > 0" class="space-y-4">
              <div class="flex items-center justify-between border-b border-[#1f1f1f] pb-2">
                <div class="flex items-center gap-2">
                  <span class="h-2 w-2 rounded-full bg-rose-500 animate-pulse"></span>
                  <h2 class="text-xs font-bold text-rose-500 uppercase tracking-wider font-mono">Needs Attention ({{ failedSources.length }})</h2>
                </div>
                <button
                  @click="disableAllFailing"
                  class="bg-rose-950/15 hover:bg-rose-900/30 border border-rose-900/30 text-rose-400 text-[10px] font-semibold px-2.5 py-1 rounded transition cursor-pointer"
                >
                  Disable All Failing
                </button>
              </div>

              <!-- Table View -->
              <div v-if="viewMode === 'table'" class="overflow-x-auto border border-[#1f1f1f] rounded-lg bg-[#0a0a0a]">
                <table class="w-full text-left text-sm text-[#e5e5e5]">
                  <thead class="text-xs uppercase bg-[#000] text-[#888888] border-b border-[#1f1f1f]">
                    <tr>
                      <th class="py-3.5 px-6 font-semibold">Source Name</th>
                      <th class="py-3.5 px-6 font-semibold">Category</th>
                      <th class="py-3.5 px-6 font-semibold">Last Crawl</th>
                      <th class="py-3.5 px-6 font-semibold">Stats</th>
                      <th class="py-3.5 px-6 font-semibold">Status</th>
                      <th class="py-3.5 px-6 font-semibold">URL</th>
                      <th class="py-3.5 px-6 font-semibold text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-[#1f1f1f]">
                    <tr v-for="src in failedSources" :key="src.name" class="hover:bg-neutral-900/10 transition duration-150 align-middle">
                      <td class="py-4 px-6 font-bold text-white max-w-[180px] truncate" :title="src.name">{{ src.name }}</td>
                      <td class="py-4 px-6 text-xs">
                        <span class="bg-[#111] border border-[#222] px-2 py-0.5 rounded text-[10px] text-[#888] font-semibold uppercase tracking-wide font-mono">
                          {{ src.category }}
                        </span>
                      </td>
                      <td class="py-4 px-6 text-xs font-mono text-[#888]">
                        {{ src.last_scraped_at ? new Date(src.last_scraped_at).toLocaleString() : 'Never' }}
                      </td>
                      <td class="py-4 px-6 text-xs font-mono text-[#888]">
                        {{ src.last_items_scraped ?? 0 }} scr / <span class="text-blue-400 font-semibold">{{ src.last_items_saved ?? 0 }} sav</span>
                        <span class="text-[10px] text-neutral-600 block">({{ src.last_duration_seconds ? `${src.last_duration_seconds.toFixed(1)}s` : '-' }})</span>
                      </td>
                      <td class="py-4 px-6">
                        <span class="inline-flex border border-rose-900/30 bg-rose-500/10 text-rose-400 px-2 py-0.5 rounded text-[10px] font-semibold lowercase animate-pulse">failed</span>
                        <div v-if="src.last_error" class="text-[10px] text-rose-400 mt-1 max-w-[200px] truncate font-mono" :title="src.last_error">
                          {{ src.last_error }}
                        </div>
                      </td>
                      <td class="py-4 px-6 text-xs max-w-[240px] truncate">
                        <a :href="src.url" target="_blank" class="text-blue-500 hover:underline font-mono text-[11px]" :title="src.url">{{ src.url }}</a>
                      </td>
                      <td class="py-4 px-6 text-right">
                        <div class="flex items-center justify-end gap-2 text-xs">
                          <button @click="toggleSource(src.type, src.name)" class="bg-[#111] hover:bg-neutral-900 border border-[#333] text-white text-xs font-semibold px-2 py-1 rounded transition cursor-pointer">
                            Disable
                          </button>
                          <button @click="openEditSourceModal('rss', src.name)" class="bg-[#111] hover:bg-neutral-900 border border-[#333] text-white text-xs font-semibold px-2 py-1 rounded transition cursor-pointer">
                            Edit
                          </button>
                          <button @click="deleteSource(src.type, src.name)" class="bg-rose-955/15 hover:bg-rose-900/30 border border-rose-900/30 text-rose-400 text-xs font-semibold px-2 py-1 rounded transition cursor-pointer">
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- Grid View -->
              <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                <div 
                  v-for="src in failedSources" 
                  :key="src.name" 
                  class="bg-[#0a0a0a] border border-rose-955/40 rounded-lg p-5 flex flex-col justify-between transition duration-200 hover:border-rose-900/80 shadow-lg"
                >
                  <div class="flex items-start justify-between gap-3">
                    <div class="truncate">
                      <h3 class="text-sm font-bold text-white truncate" :title="src.name">{{ src.name }}</h3>
                      <span class="inline-block mt-1 bg-[#111] border border-[#222] px-2 py-0.5 rounded text-[10px] text-[#888] font-semibold uppercase tracking-wide font-mono">{{ src.category }}</span>
                    </div>
                    <span class="text-[10px] px-2.5 py-1 rounded font-bold uppercase tracking-wider border bg-rose-500/10 text-rose-450 border-rose-500/20">
                      Failed
                    </span>
                  </div>
                  <div class="mt-4 space-y-3 flex-grow flex flex-col justify-end">
                    <div class="flex items-center justify-between gap-2 bg-black border border-[#1a1a1a] rounded px-2.5 py-1.5">
                      <a :href="src.url" target="_blank" class="text-blue-500 hover:underline font-mono text-[10px] truncate" :title="src.url">
                        {{ src.url }}
                      </a>
                      <button @click="copyToClipboard(src.url)" class="text-[#666] hover:text-white transition flex-shrink-0" title="Copy URL">
                        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                        </svg>
                      </button>
                    </div>
                    <div class="bg-black/35 border border-[#161616] rounded p-3 space-y-2 text-xs">
                      <div class="flex justify-between items-center text-[#888]">
                        <span>Last Crawl:</span>
                        <span class="text-white font-mono text-[10px]">{{ src.last_scraped_at ? new Date(src.last_scraped_at).toLocaleString() : 'Never' }}</span>
                      </div>
                      <div class="flex justify-between items-center text-[#888]">
                        <span>Saved Items:</span>
                        <span class="text-white font-mono">{{ src.last_items_scraped ?? 0 }} scraped / <span class="text-blue-400 font-bold">{{ src.last_items_saved ?? 0 }} saved</span></span>
                      </div>
                      <div class="flex justify-between items-center text-[#888]">
                        <span>Crawl Duration:</span>
                        <span class="text-white font-mono">{{ src.last_duration_seconds ? `${src.last_duration_seconds.toFixed(2)}s` : '-' }}</span>
                      </div>
                    </div>
                    <div v-if="src.last_error" class="bg-rose-955/10 border border-rose-900/20 rounded p-2 text-[10px] text-rose-400 font-mono break-all max-h-[70px] overflow-y-auto custom-scroll" :title="src.last_error">
                      <strong>Trace:</strong> {{ src.last_error }}
                    </div>
                  </div>
                  <div class="mt-4 pt-4 border-t border-[#1a1a1a] flex items-center justify-between gap-3 flex-shrink-0">
                    <button @click="toggleSource(src.type, src.name)" class="bg-[#111] hover:bg-neutral-900 border border-[#333] text-white text-xs font-semibold px-3 py-1.5 rounded transition cursor-pointer flex-grow text-center">
                      Disable
                    </button>
                    <button @click="openEditSourceModal('rss', src.name)" class="bg-[#111] hover:bg-neutral-900 border border-[#333] text-white text-xs font-semibold px-3 py-1.5 rounded transition cursor-pointer flex-grow text-center">
                      Edit
                    </button>
                    <button @click="deleteSource(src.type, src.name)" class="bg-rose-955/15 hover:bg-rose-900/30 border border-rose-900/20 text-rose-400 text-xs font-semibold px-3 py-1.5 rounded transition cursor-pointer flex-grow text-center">
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- SECTION 2: Active Sources -->
            <div v-if="activeSources.length > 0" class="space-y-4">
              <div class="flex items-center justify-between border-b border-[#1f1f1f] pb-2">
                <div class="flex items-center gap-2">
                  <span class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
                  <h2 class="text-xs font-bold text-white uppercase tracking-wider font-mono">Active Sources ({{ activeSources.length }})</h2>
                </div>
                <button
                  @click="disableAllActive"
                  class="bg-[#111] hover:bg-neutral-900 border border-[#333] text-white text-[10px] font-semibold px-2.5 py-1 rounded transition cursor-pointer"
                >
                  Disable All Active
                </button>
              </div>

              <!-- Table View -->
              <div v-if="viewMode === 'table'" class="overflow-x-auto border border-[#1f1f1f] rounded-lg bg-[#0a0a0a]">
                <table class="w-full text-left text-sm text-[#e5e5e5]">
                  <thead class="text-xs uppercase bg-[#000] text-[#888888] border-b border-[#1f1f1f]">
                    <tr>
                      <th class="py-3.5 px-6 font-semibold">Source Name</th>
                      <th class="py-3.5 px-6 font-semibold">Category</th>
                      <th class="py-3.5 px-6 font-semibold">Last Crawl</th>
                      <th class="py-3.5 px-6 font-semibold">Stats</th>
                      <th class="py-3.5 px-6 font-semibold">Status</th>
                      <th class="py-3.5 px-6 font-semibold">URL</th>
                      <th class="py-3.5 px-6 font-semibold text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-[#1f1f1f]">
                    <tr v-for="src in activeSources" :key="src.name" class="hover:bg-neutral-900/10 transition duration-150 align-middle">
                      <td class="py-4 px-6 font-bold text-white max-w-[180px] truncate" :title="src.name">{{ src.name }}</td>
                      <td class="py-4 px-6 text-xs">
                        <span class="bg-[#111] border border-[#222] px-2 py-0.5 rounded text-[10px] text-[#888] font-semibold uppercase tracking-wide font-mono">
                          {{ src.category }}
                        </span>
                      </td>
                      <td class="py-4 px-6 text-xs font-mono text-[#888]">
                        {{ src.last_scraped_at ? new Date(src.last_scraped_at).toLocaleString() : 'Never' }}
                      </td>
                      <td class="py-4 px-6 text-xs font-mono text-[#888]">
                        {{ src.last_items_scraped ?? 0 }} scr / <span class="text-blue-400 font-semibold">{{ src.last_items_saved ?? 0 }} sav</span>
                        <span class="text-[10px] text-neutral-600 block">({{ src.last_duration_seconds ? `${src.last_duration_seconds.toFixed(1)}s` : '-' }})</span>
                      </td>
                      <td class="py-4 px-6">
                        <span v-if="src.last_status === 'success'" class="inline-flex border border-emerald-900/30 bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded text-[10px] font-semibold lowercase">success</span>
                        <span v-else class="inline-flex border border-neutral-800 bg-[#111] text-[#888888] px-2 py-0.5 rounded text-[10px] font-semibold lowercase">never run</span>
                      </td>
                      <td class="py-4 px-6 text-xs max-w-[240px] truncate">
                        <a :href="src.url" target="_blank" class="text-blue-500 hover:underline font-mono text-[11px]" :title="src.url">{{ src.url }}</a>
                      </td>
                      <td class="py-4 px-6 text-right">
                        <div class="flex items-center justify-end gap-2 text-xs">
                          <button @click="toggleSource(src.type, src.name)" class="bg-[#111] hover:bg-neutral-900 border border-[#333] text-white text-xs font-semibold px-2 py-1 rounded transition cursor-pointer">
                            Disable
                          </button>
                          <button @click="openEditSourceModal('rss', src.name)" class="bg-[#111] hover:bg-neutral-900 border border-[#333] text-white text-xs font-semibold px-2 py-1 rounded transition cursor-pointer">
                            Edit
                          </button>
                          <button @click="deleteSource(src.type, src.name)" class="bg-rose-955/15 hover:bg-rose-900/30 border border-rose-900/20 text-rose-450 text-xs font-semibold px-2 py-1 rounded transition cursor-pointer">
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- Grid View -->
              <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                <div 
                  v-for="src in activeSources" 
                  :key="src.name" 
                  class="bg-[#0a0a0a] border border-[#1f1f1f] rounded-lg p-5 flex flex-col justify-between transition duration-200 hover:border-neutral-600 shadow-lg"
                >
                  <div class="flex items-start justify-between gap-3">
                    <div class="truncate">
                      <h3 class="text-sm font-bold text-white truncate" :title="src.name">{{ src.name }}</h3>
                      <span class="inline-block mt-1 bg-[#111] border border-[#222] px-2 py-0.5 rounded text-[10px] text-[#888] font-semibold uppercase tracking-wide font-mono">{{ src.category }}</span>
                    </div>
                    <span 
                      :class="[
                        'text-[10px] px-2.5 py-1 rounded font-bold uppercase tracking-wider border',
                        src.last_status === 'success' 
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                          : 'bg-neutral-800 text-neutral-400 border border-neutral-700'
                      ]"
                    >
                      {{ src.last_status === 'success' ? 'Success' : 'Active' }}
                    </span>
                  </div>
                  <div class="mt-4 space-y-3 flex-grow flex flex-col justify-end">
                    <div class="flex items-center justify-between gap-2 bg-black border border-[#1a1a1a] rounded px-2.5 py-1.5">
                      <a :href="src.url" target="_blank" class="text-blue-500 hover:underline font-mono text-[10px] truncate" :title="src.url">
                        {{ src.url }}
                      </a>
                      <button @click="copyToClipboard(src.url)" class="text-[#666] hover:text-white transition flex-shrink-0" title="Copy URL">
                        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                        </svg>
                      </button>
                    </div>
                    <div class="bg-black/35 border border-[#161616] rounded p-3 space-y-2 text-xs">
                      <div class="flex justify-between items-center text-[#888]">
                        <span>Last Crawl:</span>
                        <span class="text-white font-mono text-[10px]">{{ src.last_scraped_at ? new Date(src.last_scraped_at).toLocaleString() : 'Never' }}</span>
                      </div>
                      <div class="flex justify-between items-center text-[#888]">
                        <span>Saved Items:</span>
                        <span class="text-white font-mono">{{ src.last_items_scraped ?? 0 }} scraped / <span class="text-blue-400 font-bold">{{ src.last_items_saved ?? 0 }} saved</span></span>
                      </div>
                      <div class="flex justify-between items-center text-[#888]">
                        <span>Crawl Duration:</span>
                        <span class="text-white font-mono">{{ src.last_duration_seconds ? `${src.last_duration_seconds.toFixed(2)}s` : '-' }}</span>
                      </div>
                    </div>
                  </div>
                  <div class="mt-4 pt-4 border-t border-[#1a1a1a] flex items-center justify-between gap-3 flex-shrink-0">
                    <button @click="toggleSource(src.type, src.name)" class="bg-[#111] hover:bg-neutral-900 border border-[#333] text-white text-xs font-semibold px-3 py-1.5 rounded transition cursor-pointer flex-grow text-center">
                      Disable
                    </button>
                    <button @click="openEditSourceModal('rss', src.name)" class="bg-[#111] hover:bg-neutral-900 border border-[#333] text-white text-xs font-semibold px-3 py-1.5 rounded transition cursor-pointer flex-grow text-center">
                      Edit
                    </button>
                    <button @click="deleteSource(src.type, src.name)" class="bg-rose-955/15 hover:bg-rose-900/30 border border-rose-900/20 text-rose-450 text-xs font-semibold px-3 py-1.5 rounded transition cursor-pointer flex-grow text-center">
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- SECTION 3: Disabled Sources -->
            <div v-if="disabledSources.length > 0" class="space-y-4">
              <div class="flex items-center justify-between border-b border-[#1f1f1f] pb-2">
                <div class="flex items-center gap-2">
                  <span class="h-2 w-2 rounded-full bg-neutral-700"></span>
                  <h2 class="text-xs font-bold text-[#666] uppercase tracking-wider font-mono">Disabled Sources ({{ disabledSources.length }})</h2>
                </div>
                <div class="flex items-center gap-2">
                  <button
                    @click="enableAllDisabled"
                    class="bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 text-emerald-400 text-[10px] font-semibold px-2.5 py-1 rounded transition cursor-pointer"
                  >
                    Enable All
                  </button>
                  <button
                    @click="deleteAllDisabled"
                    class="bg-rose-955/15 hover:bg-rose-900/30 border border-rose-900/20 text-rose-450 hover:text-rose-400 text-[10px] font-semibold px-2.5 py-1 rounded transition cursor-pointer"
                  >
                    Delete All
                  </button>
                </div>
              </div>

              <!-- Table View -->
              <div v-if="viewMode === 'table'" class="overflow-x-auto border border-[#1f1f1f] rounded-lg bg-[#0a0a0a] opacity-70 hover:opacity-100 transition-opacity">
                <table class="w-full text-left text-sm text-[#e5e5e5]">
                  <thead class="text-xs uppercase bg-[#000] text-[#888888] border-b border-[#1f1f1f]">
                    <tr>
                      <th class="py-3.5 px-6 font-semibold">Source Name</th>
                      <th class="py-3.5 px-6 font-semibold">Category</th>
                      <th class="py-3.5 px-6 font-semibold">Last Crawl</th>
                      <th class="py-3.5 px-6 font-semibold">Stats</th>
                      <th class="py-3.5 px-6 font-semibold">Status</th>
                      <th class="py-3.5 px-6 font-semibold">URL</th>
                      <th class="py-3.5 px-6 font-semibold text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-[#1f1f1f]">
                    <tr v-for="src in disabledSources" :key="src.name" class="hover:bg-neutral-900/10 transition duration-150 align-middle">
                      <td class="py-4 px-6 font-bold text-[#888] max-w-[180px] truncate" :title="src.name">{{ src.name }}</td>
                      <td class="py-4 px-6 text-xs">
                        <span class="bg-[#111] border border-[#222] px-2 py-0.5 rounded text-[10px] text-[#666] font-semibold uppercase tracking-wide font-mono">
                          {{ src.category }}
                        </span>
                      </td>
                      <td class="py-4 px-6 text-xs font-mono text-[#666]">
                        {{ src.last_scraped_at ? new Date(src.last_scraped_at).toLocaleString() : 'Never' }}
                      </td>
                      <td class="py-4 px-6 text-xs font-mono text-[#666]">
                        {{ src.last_items_scraped ?? 0 }} scr / {{ src.last_items_saved ?? 0 }} sav
                        <span class="text-[10px] text-neutral-700 block">({{ src.last_duration_seconds ? `${src.last_duration_seconds.toFixed(1)}s` : '-' }})</span>
                      </td>
                      <td class="py-4 px-6">
                        <span class="inline-flex border border-neutral-850 bg-[#111] text-neutral-500 px-2 py-0.5 rounded text-[10px] font-semibold lowercase">disabled</span>
                      </td>
                      <td class="py-4 px-6 text-xs max-w-[240px] truncate">
                        <a :href="src.url" target="_blank" class="text-neutral-600 hover:text-blue-500 hover:underline font-mono text-[11px]" :title="src.url">{{ src.url }}</a>
                      </td>
                      <td class="py-4 px-6 text-right">
                        <div class="flex items-center justify-end gap-2 text-xs">
                          <button @click="toggleSource(src.type, src.name)" class="bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 text-emerald-400 text-xs font-semibold px-2 py-1 rounded transition cursor-pointer">
                            Enable
                          </button>
                          <button @click="openEditSourceModal('rss', src.name)" class="bg-[#111] hover:bg-neutral-900 border border-[#333] text-white text-xs font-semibold px-2 py-1 rounded transition cursor-pointer">
                            Edit
                          </button>
                          <button @click="deleteSource(src.type, src.name)" class="bg-rose-955/15 hover:bg-rose-900/30 border border-rose-900/20 text-rose-455 text-xs font-semibold px-2 py-1 rounded transition cursor-pointer">
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- Grid View -->
              <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                <div 
                  v-for="src in disabledSources" 
                  :key="src.name" 
                  class="bg-[#0a0a0a] border border-[#1f1f1f] rounded-lg p-5 flex flex-col justify-between transition duration-200 hover:border-neutral-650 opacity-70 hover:opacity-100 shadow-lg"
                >
                  <div class="flex items-start justify-between gap-3">
                    <div class="truncate">
                      <h3 class="text-sm font-bold text-[#888] truncate" :title="src.name">{{ src.name }}</h3>
                      <span class="inline-block mt-1 bg-[#111] border border-[#222] px-2 py-0.5 rounded text-[10px] text-[#666] font-semibold uppercase tracking-wide font-mono">{{ src.category }}</span>
                    </div>
                    <span class="text-[10px] px-2.5 py-1 rounded font-bold uppercase tracking-wider border bg-neutral-800 text-neutral-450 border-neutral-700">
                      Disabled
                    </span>
                  </div>
                  <div class="mt-4 space-y-3 flex-grow flex flex-col justify-end">
                    <div class="flex items-center justify-between gap-2 bg-black border border-[#1a1a1a] rounded px-2.5 py-1.5">
                      <a :href="src.url" target="_blank" class="text-neutral-500 hover:underline font-mono text-[10px] truncate" :title="src.url">
                        {{ src.url }}
                      </a>
                      <button @click="copyToClipboard(src.url)" class="text-[#666] hover:text-white transition flex-shrink-0" title="Copy URL">
                        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                        </svg>
                      </button>
                    </div>
                    <div class="bg-black/35 border border-[#161616] rounded p-3 space-y-2 text-xs">
                      <div class="flex justify-between items-center text-[#666]">
                        <span>Last Crawl:</span>
                        <span class="text-[#888] font-mono text-[10px]">{{ src.last_scraped_at ? new Date(src.last_scraped_at).toLocaleString() : 'Never' }}</span>
                      </div>
                      <div class="flex justify-between items-center text-[#666]">
                        <span>Saved Items:</span>
                        <span class="text-[#888] font-mono">{{ src.last_items_scraped ?? 0 }} scraped / {{ src.last_items_saved ?? 0 }} saved</span>
                      </div>
                      <div class="flex justify-between items-center text-[#666]">
                        <span>Crawl Duration:</span>
                        <span class="text-[#888] font-mono">{{ src.last_duration_seconds ? `${src.last_duration_seconds.toFixed(2)}s` : '-' }}</span>
                      </div>
                    </div>
                  </div>
                  <div class="mt-4 pt-4 border-t border-[#1a1a1a] flex items-center justify-between gap-3 flex-shrink-0">
                    <button @click="toggleSource(src.type, src.name)" class="bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 text-emerald-450 text-xs font-semibold px-3 py-1.5 rounded transition cursor-pointer flex-grow text-center">
                      Enable
                    </button>
                    <button @click="openEditSourceModal('rss', src.name)" class="bg-[#111] hover:bg-neutral-900 border border-[#333] text-white text-xs font-semibold px-3 py-1.5 rounded transition cursor-pointer flex-grow text-center">
                      Edit
                    </button>
                    <button @click="deleteSource(src.type, src.name)" class="bg-rose-955/15 hover:bg-rose-900/30 border border-rose-900/20 text-rose-400 text-xs font-semibold px-3 py-1.5 rounded transition cursor-pointer flex-grow text-center">
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            </div>

          </div>

          <!-- Empty State -->
          <div v-else class="bg-[#0a0a0a] border border-[#1f1f1f] rounded-lg p-12 text-center text-[#666666] flex flex-col items-center justify-center space-y-3">
            <svg class="h-8 w-8 text-[#444]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <p class="text-sm font-medium">No configuration sources match the selected query or filters.</p>
          </div>
        </div>
      </div>

      <!-- TAB 3: LIVE PROCESS LOGGER -->
      <div v-show="activeTab === 'logs'" class="flex flex-col space-y-6 flex-grow">
        <div class="bg-[#0a0a0a] border border-[#1f1f1f] rounded-lg p-6 flex flex-col flex-grow">
          <div class="flex items-center justify-between border-b border-[#1f1f1f] pb-4 mb-4">
            <div>
              <h2 class="text-base font-bold text-white flex items-center gap-2">
                Worker Live Output Stream
                <span :class="[
                  'text-[10px] px-2 py-0.5 rounded font-normal uppercase tracking-wider border',
                  loggerConnStatus === 'Live Stream Active' 
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                    : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                ]">{{ loggerConnStatus }}</span>
              </h2>
              <p class="text-xs text-[#666666] mt-0.5">Live standard logging trace events streamed straight from the worker container</p>
            </div>
            <div>
              <button @click="clearConsole" class="text-xs bg-transparent text-white border border-[#333333] hover:bg-neutral-900 px-3 py-1.5 rounded transition cursor-pointer">
                Clear Terminal
              </button>
            </div>
          </div>
          <!-- Real-time code panel -->
          <div ref="logsConsole" class="font-mono text-xs bg-black border border-[#1f1f1f] p-5 rounded overflow-y-auto h-[550px] leading-relaxed custom-scroll space-y-1 text-[#a1a1a1]">
            <div v-if="logLines.length === 0" class="text-[#888888]">[READY] Live logs stream connected. Ready to crawl...</div>
            <div 
              v-for="(line, idx) in logLines" 
              :key="idx"
              :class="[
                'font-mono whitespace-pre-wrap break-all',
                line.type === 'error' ? 'text-rose-500 font-semibold' : '',
                line.type === 'warn' ? 'text-amber-500' : '',
                line.type === 'system' ? 'text-white font-semibold' : '',
                line.type === 'success' ? 'text-emerald-400' : '',
                line.type === 'info' ? 'text-[#888888]' : ''
              ]"
            >{{ line.text }}</div>
          </div>
        </div>
      </div>

      <!-- TAB 4: RECENTLY SCRAPED STORIES -->
      <div v-if="activeTab === 'articles'" class="space-y-6">
        <div class="bg-[#0a0a0a] border border-[#1f1f1f] rounded-lg p-6">
          <h2 class="text-base font-bold text-white mb-4 border-b border-[#1f1f1f] pb-3">Recently Ingested Stories</h2>
          <div class="divide-y divide-[#1f1f1f]">
            <div v-if="recentArticles.length === 0" class="py-6 text-center text-[#666666]">No articles ingested yet.</div>
            <div v-for="art in recentArticles" :key="art.id" class="py-4 border-b border-[#1f1f1f] last:border-0 text-left">
              <div 
                @click="toggleArticleJSON(art.id, `articles-tab-${art.id}`)" 
                class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 cursor-pointer hover:bg-neutral-900/40 p-2 -m-2 rounded transition duration-200 group"
              >
                <div class="space-y-1 bg-transparent">
                  <div class="text-sm font-semibold text-white group-hover:text-blue-400 transition text-left flex items-center gap-2 leading-snug">
                    <svg 
                      :class="[
                        'w-4 h-4 text-[#666] group-hover:text-blue-400 transition-transform duration-200 flex-shrink-0',
                        expandedArticles.has(`articles-tab-${art.id}`) ? 'rotate-90' : ''
                      ]"
                      fill="none" 
                      viewBox="0 0 24 24" 
                      stroke="currentColor"
                    >
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                    </svg>
                    <span>{{ art.title }}</span>
                  </div>
                  <div class="flex flex-wrap gap-2 items-center text-xs pl-6">
                    <span class="px-2 py-0.5 bg-[#111] border border-[#333333] text-white rounded font-mono text-[10px]">{{ art.publisher }}</span>
                    <span class="px-2 py-0.5 bg-[#111] border border-[#1f1f1f] text-[#888888] rounded font-normal text-[10px] capitalize">{{ art.category }}</span>
                    <span class="text-[#666666] text-[11px]">Ingested: {{ new Date(art.created_date).toLocaleString() }}</span>
                  </div>
                </div>
                <div class="flex-shrink-0 flex items-center gap-3 pl-6 sm:pl-0">
                  <span class="text-[10px] font-mono text-[#666666] bg-black border border-[#1f1f1f] group-hover:border-[#333] group-hover:text-white px-2 py-1 rounded transition">ID: {{ art.id }}</span>
                  <a :href="art.url" target="_blank" @click.stop class="bg-black hover:bg-neutral-900 text-white px-3 py-1.5 rounded text-xs border border-[#333333] font-medium transition cursor-pointer">
                    Source
                  </a>
                </div>
              </div>
              
              <!-- Collapsible JSON Document view -->
              <div v-if="expandedArticles.has(`articles-tab-${art.id}`)" class="mt-4 pl-6">
                <div class="relative bg-[#050505] border border-[#1f1f1f] rounded-lg overflow-hidden">
                  <div class="flex items-center justify-between px-4 py-2 border-b border-[#1f1f1f] bg-black">
                    <span class="text-[10px] font-mono text-[#555]">database record json</span>
                    <button @click="copyArticleJSON(art.id)" class="text-[10px] bg-[#111] border border-[#333333] hover:bg-neutral-900 text-white px-2.5 py-1 rounded transition cursor-pointer">
                      Copy JSON
                    </button>
                  </div>
                  <pre class="p-4 overflow-x-auto text-xs font-mono text-[#a1a1a1] bg-black max-h-[450px] custom-scroll whitespace-pre-wrap select-text font-mono">
                    {{ loadedArticleJSONs[art.id] }}
                  </pre>
                </div>
              </div>
            </div>
          </div>
          <!-- Pagination Controls for Articles -->
          <div class="flex items-center justify-between border-t border-[#1f1f1f] bg-black pt-6">
            <div class="text-xs text-[#a1a1a1]">
              Showing <span class="font-mono font-medium text-white">{{ articlesTotal > 0 ? (articlesPage - 1) * articlesLimit + 1 : 0 }}</span> to
              <span class="font-mono font-medium text-white">{{ Math.min(articlesPage * articlesLimit, articlesTotal) }}</span> of
              <span class="font-mono font-medium text-white">{{ articlesTotal }}</span> articles
            </div>
            <div class="flex items-center gap-2">
              <button
                @click="fetchArticles(articlesPage - 1)"
                :disabled="articlesPage === 1"
                class="bg-[#111] hover:bg-neutral-900 border border-[#333333] disabled:opacity-40 disabled:hover:bg-[#111] text-white text-xs font-semibold px-3 py-1.5 rounded transition cursor-pointer"
              >
                Previous
              </button>
              <span class="text-xs text-[#a1a1a1] font-mono mx-2">Page {{ articlesPage }} of {{ articlesTotalPages }}</span>
              <button
                @click="fetchArticles(articlesPage + 1)"
                :disabled="articlesPage === articlesTotalPages"
                class="bg-[#111] hover:bg-neutral-900 border border-[#333333] disabled:opacity-40 disabled:hover:bg-[#111] text-white text-xs font-semibold px-3 py-1.5 rounded transition cursor-pointer"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Source Modal (Add/Edit) -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      <div class="bg-[#0a0a0a] border border-[#1f1f1f] w-full max-w-md rounded-lg overflow-hidden shadow-2xl flex flex-col">
        <div class="p-6 border-b border-[#1f1f1f] flex items-center justify-between bg-black">
          <h2 class="text-base font-bold text-white">{{ modalMode === 'add' ? 'Add New RSS Feed' : 'Edit RSS Feed' }}</h2>
          <button @click="showModal = false" class="text-[#666] hover:text-white transition cursor-pointer">
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="p-6 space-y-4">
          <div class="flex flex-col space-y-1.5">
            <label class="text-xs font-bold text-[#888] uppercase tracking-wide">Source Name</label>
            <input v-model="sourceForm.name" type="text" placeholder="e.g. TechCrunch" class="bg-black border border-[#2c2c2c] hover:border-[#3c3c3c] focus:border-white text-sm text-white rounded px-3 py-2 focus:outline-none transition font-medium" />
          </div>

          <div class="flex flex-col space-y-1.5">
            <label class="text-xs font-bold text-[#888] uppercase tracking-wide">Feed Target URL</label>
            <input v-model="sourceForm.url" type="text" placeholder="e.g. https://techcrunch.com/feed/" class="bg-black border border-[#2c2c2c] hover:border-[#3c3c3c] focus:border-white text-sm text-white rounded px-3 py-2 focus:outline-none transition font-medium" />
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="flex flex-col space-y-1.5">
              <label class="text-xs font-bold text-[#888] uppercase tracking-wide">Category</label>
              <input v-model="sourceForm.category" type="text" placeholder="e.g. technology, sports" class="bg-black border border-[#2c2c2c] hover:border-[#3c3c3c] focus:border-white text-sm text-white rounded px-3 py-2 focus:outline-none transition font-medium capitalize" />
            </div>
            <div class="flex flex-col justify-end pb-2.5">
              <div class="flex items-center gap-2">
                <input v-model="sourceForm.enabled" id="source-enabled" type="checkbox" class="h-4 w-4 rounded bg-black border-[#2c2c2c] text-white accent-white cursor-pointer" />
                <label for="source-enabled" class="text-xs text-white font-semibold cursor-pointer select-none">Enable Immediately</label>
              </div>
            </div>
          </div>
        </div>

        <div class="p-6 border-t border-[#1f1f1f] flex items-center justify-end gap-3 bg-[#050505]">
          <button @click="showModal = false" class="bg-transparent hover:bg-neutral-900 border border-[#2c2c2c] text-white text-xs font-semibold px-4 py-2 rounded transition cursor-pointer">
            Cancel
          </button>
          <button @click="handleSaveSource" class="bg-white hover:bg-[#e6e6e6] text-black text-xs font-semibold px-4 py-2 rounded transition cursor-pointer">
            Save Source
          </button>
        </div>
      </div>
    </div>

    <!-- Vercel Toast Notification style -->
    <div :class="[
      'fixed bottom-6 right-6 px-5 py-3.5 rounded shadow-2xl flex items-center gap-3 z-50 transition-all duration-300 bg-black',
      toastIsError ? 'border border-rose-800/60' : 'border border-neutral-800',
      toastVisible ? 'translate-y-0 opacity-100' : 'translate-y-36 opacity-0 pointer-events-none'
    ]">
      <div :class="[
        'h-2 w-2 rounded-full',
        toastIsError ? 'bg-rose-500 animate-pulse' : 'bg-white'
      ]"></div>
      <p class="text-xs font-semibold text-[#fafafa] font-mono text-xs">{{ toastMsg }}</p>
    </div>
  </div>
</template>

<style>
/* Custom styled scrolls */
.custom-scroll::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
.custom-scroll::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scroll::-webkit-scrollbar-thumb {
  background: #1f1f1f;
  border-radius: 3px;
}
.custom-scroll::-webkit-scrollbar-thumb:hover {
  background: #333333;
}
</style>
