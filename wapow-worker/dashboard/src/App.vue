<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'

// Interface definitions
interface Job {
  id: string
  name: string
  trigger: string
  next_run_time: string | null
  status: 'active' | 'paused'
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

interface SourceSelectors {
  articles: string
  title: string
  description: string
  image: string
  link: string
  author: string
  date: string
}

interface Source {
  name: string
  url: string
  type: 'rss' | 'web'
  category: string
  enabled: boolean
  use_playwright?: boolean
  selectors?: SourceSelectors
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

// Runs History
const recentRuns = ref<ScraperRun[]>([])
const runsPage = ref<number>(1)
const runsLimit = ref<number>(10)
const totalRunsPages = ref<number>(1)

// Sources Telemetry
const sources = ref<Source[]>([])
const sourceFilter = ref<'all' | 'success' | 'failed' | 'never run' | 'disabled'>('all')

// Ingested Articles list
const recentArticles = ref<IngestedArticle[]>([])

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
  type: 'rss' as 'rss' | 'web',
  name: '',
  url: '',
  category: '',
  enabled: true,
  use_playwright: false,
  selectors: {
    articles: 'article',
    title: 'h1, h2, .title',
    description: 'p, .description, .excerpt',
    image: 'img',
    link: 'a',
    author: '.author, .byline',
    date: 'time, .date, .published'
  }
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
    if (runsPage.value === 1) {
      recentRuns.value = data.recent_runs || []
    }
    recentArticles.value = data.recent_articles || []
    sources.value = data.sources || []

    lastUpdated.value = `Last synced: ${new Date().toLocaleTimeString()}`
  } catch (err: any) {
    console.error('Error fetching stats:', err)
  }
}

async function fetchRuns(page: number) {
  try {
    const res = await fetch(`/api/runs?page=${page}&limit=${runsLimit.value}`)
    if (!res.ok) throw new Error('Failed to fetch runs')
    const data = await res.json()
    recentRuns.value = data.runs || []
    runsPage.value = data.page || 1
    totalRuns.value = data.total || 0
    totalRunsPages.value = data.total_pages || 1
  } catch (err) {
    console.error('Error fetching runs:', err)
  }
}

const visibleRunsPages = computed(() => {
  const current = runsPage.value
  const total = totalRunsPages.value
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }
  const pages: (number | string)[] = []
  pages.push(1)
  
  if (current > 3) {
    pages.push('...')
  }
  
  const start = Math.max(2, current - 1)
  const end = Math.min(total - 1, current + 1)
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  
  if (current < total - 2) {
    pages.push('...')
  }
  
  pages.push(total)
  return pages
})

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

// Modal Form handling
function openAddSourceModal() {
  modalMode.value = 'add'
  oldSourceName.value = ''
  sourceForm.value = {
    type: 'rss',
    name: '',
    url: '',
    category: '',
    enabled: true,
    use_playwright: false,
    selectors: {
      articles: 'article',
      title: 'h1, h2, .title',
      description: 'p, .description, .excerpt',
      image: 'img',
      link: 'a',
      author: '.author, .byline',
      date: 'time, .date, .published'
    }
  }
  showModal.value = true
}

function openEditSourceModal(type: 'rss' | 'web', name: string) {
  modalMode.value = 'edit'
  oldSourceName.value = name
  const existing = sources.value.find(s => s.type === type && s.name === name)

  if (existing) {
    sourceForm.value = {
      type: existing.type,
      name: existing.name,
      url: existing.url,
      category: existing.category,
      enabled: existing.enabled,
      use_playwright: existing.use_playwright || false,
      selectors: existing.selectors ? { ...existing.selectors } : {
        articles: 'article',
        title: 'h1, h2, .title',
        description: 'p, .description, .excerpt',
        image: 'img',
        link: 'a',
        author: '.author, .byline',
        date: 'time, .date, .published'
      }
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
const filteredSources = computed(() => {
  if (sourceFilter.value === 'all') return sources.value
  return sources.value.filter(s => {
    if (sourceFilter.value === 'disabled') return !s.enabled
    return s.enabled && s.last_status === sourceFilter.value
  })
})

const activeSourcesCount = computed(() => {
  return sources.value.length
})

// Periodic auto-sync statistics
let syncInterval: ReturnType<typeof setInterval> | null = null

onMounted(async () => {
  await fetchStats()
  await fetchJobs()
  await fetchRuns(1)
  connectLogsStream()

  syncInterval = setInterval(async () => {
    await fetchStats()
    await fetchJobs()
    await fetchRuns(runsPage.value)
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
        <!-- Vercel logo style triangle -->
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

        <!-- Manual Scrape Actions -->
        <div class="bg-[#0a0a0a] border border-[#1f1f1f] rounded-lg p-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div class="space-y-1">
            <h2 class="text-base font-bold text-white">Manual Deployment & Crawl Control</h2>
            <p class="text-xs text-[#a1a1a1]">Instantly trigger and sync the WAPOW worker crawler instances for any enabled sources</p>
          </div>
          <div class="flex flex-wrap gap-3">
            <button 
              @click="triggerJob('rss_feeds')" 
              :disabled="triggeringJob" 
              class="bg-white text-black hover:bg-[#e0e0e0] font-medium text-xs py-2 px-4 rounded transition duration-200 cursor-pointer disabled:bg-neutral-800 disabled:text-neutral-500"
            >
              Run RSS Feeds
            </button>
            <button 
              @click="triggerJob('web_scrape')" 
              :disabled="triggeringJob" 
              class="bg-transparent text-white hover:bg-neutral-900 font-medium text-xs py-2 px-4 rounded border border-[#333333] transition duration-200 cursor-pointer disabled:bg-neutral-800 disabled:text-neutral-500"
            >
              Run Web Page Scraper
            </button>
            <button 
              @click="triggerJob('all')" 
              :disabled="triggeringJob" 
              class="bg-transparent text-[#e5e5e5] hover:bg-neutral-900 font-medium text-xs py-2 px-4 rounded border border-[#1f1f1f] transition duration-200 cursor-pointer disabled:bg-neutral-800 disabled:text-neutral-500"
            >
              Run All Scrapers
            </button>
            <button 
              @click="fetchStats" 
              class="bg-[#1f1f1f] text-[#a1a1a1] hover:text-white px-3 py-2 rounded border border-[#333333] transition flex items-center justify-center cursor-pointer"
            >
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 8H18.2M7 9a4 4 0 110-8h1.5" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Scheduler & Worker Control -->
        <div class="bg-[#0a0a0a] border border-[#1f1f1f] rounded-lg overflow-hidden">
          <div class="p-6 border-b border-[#1f1f1f]">
            <h2 class="text-base font-bold text-white">Scheduler & Worker Control</h2>
            <p class="text-xs text-[#666666] mt-0.5">Pause/resume scheduled crawling jobs and background slide conversion tasks</p>
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
                      ? 'border-rose-500/20 bg-rose-500/10 text-rose-400' 
                      : 'border-emerald-500/20 bg-emerald-500/10 text-emerald-400'
                  ]">{{ job.status }}</span>
                </div>
                <p class="text-xs text-[#a1a1a1]">Trigger interval: <span class="font-mono text-white">{{ job.trigger }}</span></p>
                <p class="text-[11px] text-[#666666]">Next Run: <span class="font-mono text-[#888]">{{ job.next_run_time || 'Paused' }}</span></p>
              </div>
              <div class="flex items-center gap-2">
                <button 
                  @click="handleToggleJob(job.id, job.status === 'paused')"
                  :class="[
                    'text-xs font-semibold px-3 py-1.5 rounded transition cursor-pointer',
                    job.status === 'paused'
                      ? 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20'
                      : 'bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20'
                  ]"
                >
                  {{ job.status === 'paused' ? 'Resume' : 'Pause' }}
                </button>
                <button 
                  @click="triggerJob(job.id)"
                  class="bg-transparent hover:bg-neutral-900 border border-[#333333] text-white text-xs font-semibold px-3 py-1.5 rounded transition cursor-pointer"
                >
                  Run Now
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
                      ? 'border-rose-500/20 bg-rose-500/10 text-rose-400' 
                      : 'border-emerald-500/20 bg-emerald-500/10 text-emerald-400'
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
                  <th class="py-3.5 px-6 font-semibold">Saved Articles & Error Logs</th>
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
                    <!-- Articles Ingested in this run -->
                    <div v-if="run.saved_articles && run.saved_articles.length > 0" class="text-[11px] bg-black p-3 rounded border border-[#1f1f1f] mt-2 space-y-1 max-w-[450px]">
                      <strong class="text-[#666666] font-semibold uppercase text-[9px] tracking-wider block mb-1">Ingested ({{ run.saved_articles.length }}):</strong>
                      <ul class="space-y-1 max-h-[200px] overflow-y-auto custom-scroll font-mono text-[10px] text-[#888888] divide-y divide-[#111]">
                        <li v-for="art in run.saved_articles" :key="art.id" class="py-1.5 first:pt-0 last:pb-0 text-left">
                          <div 
                            @click="toggleArticleJSON(art.id, `run-${run._id || run.start_time}-${art.id}`)" 
                            class="flex items-center justify-between gap-3 cursor-pointer group py-1.5 px-2 -mx-2 rounded hover:bg-neutral-900/40 transition duration-150"
                          >
                            <div class="text-left truncate flex items-center gap-1.5 text-[#a1a1a1] group-hover:text-blue-400 transition-colors">
                              <svg 
                                :class="[
                                  'w-3 h-3 text-[#555] group-hover:text-blue-400 transition-transform duration-200 flex-shrink-0',
                                  expandedArticles.has(`run-${run._id || run.start_time}-${art.id}`) ? 'rotate-90' : ''
                                ]"
                                fill="none" 
                                viewBox="0 0 24 24" 
                                stroke="currentColor"
                              >
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                              </svg>
                              <span class="truncate">{{ art.title }}</span>
                            </div>
                            <span class="text-[9px] text-[#444444] group-hover:text-white flex-shrink-0 transition-colors">{{ art.id }}</span>
                          </div>
                          <!-- Expandable MongoDB json -->
                          <div v-if="expandedArticles.has(`run-${run._id || run.start_time}-${art.id}`)" class="mt-2">
                            <div class="relative bg-black border border-[#1f1f1f] rounded overflow-hidden">
                              <div class="flex items-center justify-between px-2.5 py-1 border-b border-[#1f1f1f] bg-[#050505]">
                                <span class="text-[9px] font-mono text-[#555]">database record json</span>
                                <button @click="copyArticleJSON(art.id)" class="text-[9px] bg-[#111] border border-[#333333] hover:bg-neutral-900 text-white px-1.5 py-0.5 rounded transition cursor-pointer">
                                  Copy
                                </button>
                              </div>
                              <pre class="p-2.5 overflow-x-auto text-[10px] font-mono text-[#888] bg-black max-h-[180px] custom-scroll whitespace-pre-wrap select-text font-mono">
                                {{ loadedArticleJSONs[art.id] }}
                              </pre>
                            </div>
                          </div>
                        </li>
                      </ul>
                    </div>

                    <!-- Errors during this run -->
                    <div v-if="run.errors && run.errors.length > 0" class="text-[11px] border border-rose-950/40 bg-rose-950/5 text-rose-400 p-3 rounded mt-2">
                      <strong class="text-[9px] uppercase font-semibold tracking-wider block mb-1">Errors:</strong>
                      <ul class="space-y-1 list-disc pl-4 max-h-[100px] overflow-y-auto custom-scroll font-mono text-[10px]">
                        <li v-for="(err, idx) in run.errors" :key="idx">{{ err }}</li>
                      </ul>
                    </div>

                    <span v-if="(!run.saved_articles || run.saved_articles.length === 0) && (!run.errors || run.errors.length === 0)" class="text-[#444444] italic text-xs">None</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <!-- Runs Pagination Footer -->
          <div class="flex items-center justify-between border-t border-[#1f1f1f] bg-[#050505] px-6 py-4 flex-shrink-0">
            <div class="flex items-center text-xs text-[#666666]">
              Showing page <span class="text-white font-mono mx-1 font-semibold">{{ runsPage }}</span> of <span class="text-white font-mono mx-1 font-semibold">{{ totalRunsPages }}</span> (<span class="text-white font-mono mx-1 font-semibold">{{ totalRuns }}</span> total runs)
            </div>
            <div class="flex items-center gap-2">
              <button 
                @click="fetchRuns(runsPage - 1)" 
                :disabled="runsPage <= 1"
                class="bg-[#111] hover:bg-neutral-900 border border-[#1f1f1f] text-[#a1a1a1] hover:text-white text-xs px-3 py-1.5 rounded disabled:opacity-30 disabled:hover:bg-[#111] disabled:text-[#444] transition cursor-pointer disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <template v-for="(p, idx) in visibleRunsPages" :key="idx">
                <span v-if="p === '...'" class="text-[#444] px-1 text-xs select-none">...</span>
                <button 
                  v-else
                  @click="fetchRuns(p as number)"
                  :class="[
                    'text-xs font-mono px-3 py-1.5 rounded border transition cursor-pointer',
                    p === runsPage 
                      ? 'bg-white text-black border-white font-bold' 
                      : 'bg-[#111] hover:bg-neutral-900 border-[#1f1f1f] text-[#a1a1a1] hover:text-white'
                  ]"
                >
                  {{ p }}
                </button>
              </template>
              <button 
                @click="fetchRuns(runsPage + 1)" 
                :disabled="runsPage >= totalRunsPages"
                class="bg-[#111] hover:bg-neutral-900 border border-[#1f1f1f] text-[#a1a1a1] hover:text-white text-xs px-3 py-1.5 rounded disabled:opacity-30 disabled:hover:bg-[#111] disabled:text-[#444] transition cursor-pointer disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- TAB 2: SOURCES TELEMETRY -->
      <div v-if="activeTab === 'sources'" class="space-y-8">
        <div class="bg-[#0a0a0a] border border-[#1f1f1f] rounded-lg overflow-hidden">
          <div class="p-6 border-b border-[#1f1f1f] flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h2 class="text-base font-bold text-white">Sources Configuration Status</h2>
              <p class="text-xs text-[#a1a1a1] mt-0.5">Crawler statistics and statuses per RSS feed and Web Page mapping</p>
            </div>
            <div class="flex items-center gap-3">
              <button @click="openAddSourceModal" class="bg-white text-black hover:bg-[#e0e0e0] font-medium text-xs py-1.5 px-3 rounded transition duration-200 cursor-pointer">
                + Add Source
              </button>
              <span class="text-xs text-[#666666]">Filter:</span>
              <select v-model="sourceFilter" class="bg-black border border-[#333333] text-xs text-[#fafafa] rounded px-3 py-1.5 focus:outline-none focus:border-[#444] cursor-pointer">
                <option value="all">All Sources</option>
                <option value="success">Success</option>
                <option value="failed">Failed</option>
                <option value="never run">Never Run</option>
                <option value="disabled">Disabled</option>
              </select>
            </div>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left text-sm text-[#e5e5e5]">
              <thead class="text-xs uppercase bg-[#000] text-[#888888] border-b border-[#1f1f1f]">
                <tr>
                  <th class="py-3.5 px-6 font-semibold">Source Name</th>
                  <th class="py-3.5 px-6 font-semibold">Type</th>
                  <th class="py-3.5 px-6 font-semibold">Category</th>
                  <th class="py-3.5 px-6 font-semibold">Last Crawl Time</th>
                  <th class="py-3.5 px-6 font-semibold">Duration</th>
                  <th class="py-3.5 px-6 font-semibold">Scraped / Saved</th>
                  <th class="py-3.5 px-6 font-semibold">Status</th>
                  <th class="py-3.5 px-6 font-semibold">Crawl URL / Errors</th>
                  <th class="py-3.5 px-6 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[#1f1f1f]">
                <tr v-if="filteredSources.length === 0">
                  <td colspan="9" class="py-8 text-center text-[#666666]">No sources match criteria.</td>
                </tr>
                <tr v-for="src in filteredSources" :key="src.name" class="hover:bg-[#0a0a0a] transition duration-150">
                  <td class="py-3.5 px-6 font-medium text-white max-w-[180px] truncate" :title="src.name">{{ src.name }}</td>
                  <td class="py-3.5 px-6 text-xs font-mono text-[#888888] uppercase">{{ src.type }}</td>
                  <td class="py-3.5 px-6 text-xs text-[#888888] capitalize">{{ src.category }}</td>
                  <td class="py-3.5 px-6 text-xs text-[#888888]">{{ src.last_scraped_at ? new Date(src.last_scraped_at).toLocaleString() : 'Never' }}</td>
                  <td class="py-3.5 px-6 text-xs font-mono text-[#888888]">{{ src.last_duration_seconds ? `${src.last_duration_seconds.toFixed(2)}s` : '-' }}</td>
                  <td class="py-3.5 px-6 text-xs font-mono text-white">
                    {{ src.last_items_scraped ?? 0 }} / <span class="text-blue-500">{{ src.last_items_saved ?? 0 }}</span>
                  </td>
                  <td class="py-3.5 px-6">
                    <span v-if="!src.enabled" class="inline-flex border px-2 py-0.5 rounded text-[10px] font-medium tracking-wider lowercase bg-[#111] text-[#666666] border-[#1f1f1f]">
                      disabled
                    </span>
                    <span v-else-if="src.last_status === 'success'" class="inline-flex border px-2 py-0.5 rounded text-[10px] font-medium tracking-wider lowercase bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
                      success
                    </span>
                    <span v-else-if="src.last_status === 'failed'" class="inline-flex border px-2 py-0.5 rounded text-[10px] font-medium tracking-wider lowercase bg-rose-500/10 text-rose-400 border-rose-500/20">
                      failed
                    </span>
                    <span v-else class="inline-flex border px-2 py-0.5 rounded text-[10px] font-medium tracking-wider lowercase bg-[#111] text-[#888888] border-[#333333]">
                      never run
                    </span>
                  </td>
                  <td class="py-3.5 px-6 text-xs max-w-[240px]">
                    <a :href="src.url" target="_blank" class="text-blue-500 hover:underline block truncate font-mono text-[11px]" :title="src.url">{{ src.url }}</a>
                    <div v-if="src.last_error" class="text-[10px] text-rose-500 max-w-[200px] truncate cursor-help mt-1 font-mono" :title="src.last_error">
                      {{ src.last_error }}
                    </div>
                  </td>
                  <td class="py-3.5 px-6 text-xs flex gap-2">
                    <button @click="toggleSource(src.type, src.name)" class="text-[#a1a1a1] hover:text-white transition cursor-pointer font-medium">
                      {{ src.enabled ? 'Disable' : 'Enable' }}
                    </button>
                    <span class="text-[#333333]">|</span>
                    <button @click="openEditSourceModal(src.type, src.name)" class="text-blue-500 hover:text-blue-400 transition cursor-pointer font-medium">
                      Edit
                    </button>
                    <span class="text-[#333333]">|</span>
                    <button @click="deleteSource(src.type, src.name)" class="text-rose-500 hover:text-rose-400 transition cursor-pointer font-medium">
                      Delete
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
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
        </div>
      </div>
    </main>

    <!-- Source Modal (Add/Edit) -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      <div class="bg-[#0a0a0a] border border-[#1f1f1f] w-full max-w-2xl rounded-lg overflow-hidden shadow-2xl flex flex-col">
        <div class="p-6 border-b border-[#1f1f1f] flex items-center justify-between">
          <h2 class="text-base font-bold text-white">{{ modalMode === 'add' ? 'Add New Scraping Source' : 'Edit Scraping Source' }}</h2>
          <button @click="showModal = false" class="text-[#666] hover:text-white transition cursor-pointer">
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="p-6 overflow-y-auto max-h-[60vh] space-y-4 custom-scroll">
          <div class="grid grid-cols-2 gap-4">
            <div class="flex flex-col space-y-1.5">
              <label class="text-xs font-semibold text-[#888]">Source Type</label>
              <select v-model="sourceForm.type" :disabled="modalMode === 'edit'" class="bg-black border border-[#333] text-sm text-white rounded px-3 py-2 focus:outline-none focus:border-white transition cursor-pointer">
                <option value="rss">RSS Feed</option>
                <option value="web">Web Scraper</option>
              </select>
            </div>
            <div class="flex flex-col space-y-1.5">
              <label class="text-xs font-semibold text-[#888]">Category</label>
              <input v-model="sourceForm.category" type="text" placeholder="e.g. tech, news, business" class="bg-black border border-[#333] text-sm text-white rounded px-3 py-2 focus:outline-none focus:border-white transition" />
            </div>
          </div>

          <div class="flex flex-col space-y-1.5">
            <label class="text-xs font-semibold text-[#888]">Source Name</label>
            <input v-model="sourceForm.name" type="text" placeholder="e.g. TechCrunch" class="bg-black border border-[#333] text-sm text-white rounded px-3 py-2 focus:outline-none focus:border-white transition" />
          </div>

          <div class="flex flex-col space-y-1.5">
            <label class="text-xs font-semibold text-[#888]">Target Crawl URL</label>
            <input v-model="sourceForm.url" type="text" placeholder="e.g. https://techcrunch.com/feed/" class="bg-black border border-[#333] text-sm text-white rounded px-3 py-2 focus:outline-none focus:border-white transition" />
          </div>

          <div class="flex items-center gap-2 pt-2">
            <input v-model="sourceForm.enabled" id="source-enabled" type="checkbox" class="h-4 w-4 rounded bg-black border-[#333] text-white accent-white cursor-pointer" />
            <label for="source-enabled" class="text-xs text-white font-medium cursor-pointer">Enable immediately for scheduled crawlers</label>
          </div>

          <!-- Web Specific configuration fields -->
          <div v-if="sourceForm.type === 'web'" class="border-t border-[#1f1f1f] pt-4 mt-2 space-y-4">
            <h3 class="text-xs font-bold uppercase tracking-wider text-[#666666]">Web CSS Scraper Specific Configs</h3>
            
            <div class="flex items-center gap-2">
              <input v-model="sourceForm.use_playwright" id="source-playwright" type="checkbox" class="h-4 w-4 rounded bg-black border-[#333] text-white accent-white cursor-pointer" />
              <label for="source-playwright" class="text-xs text-white font-medium cursor-pointer">Use Playwright (Headless Browser execution for JavaScript-heavy targets)</label>
            </div>

            <div class="grid grid-cols-2 gap-4 bg-black/40 p-4 rounded border border-[#1f1f1f]">
              <div class="flex flex-col space-y-1.5 col-span-2">
                <label class="text-xs font-semibold text-[#888]">Parent Articles Container CSS Selector</label>
                <input v-model="sourceForm.selectors.articles" type="text" placeholder="article, .post-item" class="bg-black border border-[#333] text-xs text-white rounded px-3 py-1.5 focus:outline-none focus:border-white transition" />
              </div>
              <div class="flex flex-col space-y-1.5">
                <label class="text-xs font-semibold text-[#888]">Title Selector</label>
                <input v-model="sourceForm.selectors.title" type="text" placeholder="h2, .title" class="bg-black border border-[#333] text-xs text-white rounded px-3 py-1.5 focus:outline-none focus:border-white transition" />
              </div>
              <div class="flex flex-col space-y-1.5">
                <label class="text-xs font-semibold text-[#888]">Description Selector</label>
                <input v-model="sourceForm.selectors.description" type="text" placeholder="p, .excerpt" class="bg-black border border-[#333] text-xs text-white rounded px-3 py-1.5 focus:outline-none focus:border-white transition" />
              </div>
              <div class="flex flex-col space-y-1.5">
                <label class="text-xs font-semibold text-[#888]">Link/Anchor Selector</label>
                <input v-model="sourceForm.selectors.link" type="text" placeholder="a" class="bg-black border border-[#333] text-xs text-white rounded px-3 py-1.5 focus:outline-none focus:border-white transition" />
              </div>
              <div class="flex flex-col space-y-1.5">
                <label class="text-xs font-semibold text-[#888]">Image Selector</label>
                <input v-model="sourceForm.selectors.image" type="text" placeholder="img" class="bg-black border border-[#333] text-xs text-white rounded px-3 py-1.5 focus:outline-none focus:border-white transition" />
              </div>
              <div class="flex flex-col space-y-1.5">
                <label class="text-xs font-semibold text-[#888]">Author Selector</label>
                <input v-model="sourceForm.selectors.author" type="text" placeholder=".author" class="bg-black border border-[#333] text-xs text-white rounded px-3 py-1.5 focus:outline-none focus:border-white transition" />
              </div>
              <div class="flex flex-col space-y-1.5">
                <label class="text-xs font-semibold text-[#888]">Published Date Selector</label>
                <input v-model="sourceForm.selectors.date" type="text" placeholder="time, .date" class="bg-black border border-[#333] text-xs text-white rounded px-3 py-1.5 focus:outline-none focus:border-white transition" />
              </div>
            </div>
          </div>
        </div>

        <div class="p-6 border-t border-[#1f1f1f] flex items-center justify-end gap-3 bg-[#050505]">
          <button @click="showModal = false" class="bg-transparent hover:bg-neutral-900 border border-[#333333] text-white text-xs font-semibold px-4 py-2 rounded transition cursor-pointer">
            Cancel
          </button>
          <button @click="handleSaveSource" class="bg-white hover:bg-[#e0e0e0] text-black text-xs font-semibold px-4 py-2 rounded transition cursor-pointer">
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
      <p class="text-xs font-medium text-[#fafafa]">{{ toastMsg }}</p>
    </div>
  </div>
</template>
