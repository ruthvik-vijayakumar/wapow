<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'

// Interface definitions
interface Job {
  id: string
  name: string
  trigger: string
  next_run_time: string | null
  status: 'active' | 'paused'
  manual?: boolean
  running?: boolean
  active_run?: {
    run_id: string
    task_id?: string
    start_time?: string
  } | null
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
  status: 'success' | 'failed' | 'running' | 'cancelled'
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
const jobs = ref<Job[]>([])
const celeryWorkers = ref<any[]>([])
const celeryStatus = ref<string>('offline')

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
const stoppingJobId = ref<string | null>(null)

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
    await fetchSources()
  }
}

async function fetchSources() {
  try {
    const res = await fetch('/sources')
    if (!res.ok) throw new Error('Failed to fetch sources')
    const data = await res.json()
    sources.value = [
      ...(data.rss || []).map((s: Source) => ({ ...s, type: 'rss' as const, last_status: s.last_status || 'never run' })),
      ...(data.web || []).map((s: Source) => ({ ...s, type: 'web' as const, last_status: s.last_status || 'never run' })),
    ]
  } catch (err) {
    console.error('Error fetching sources:', err)
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

async function fetchJobs() {
  try {
    const res = await fetch('/jobs')
    if (!res.ok) throw new Error('Failed to fetch jobs')
    const data = await res.json()
    jobs.value = data.jobs || []

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
      showToast(`Queued ${jobId} crawl task ${String(result.task_id || '').substring(0, 8)}.`)
      await fetchJobs()
      await fetchRuns(1)
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

async function stopJob(jobId: string) {
  stoppingJobId.value = jobId
  try {
    const response = await fetch(`/jobs/${jobId}/stop`, { method: 'POST' })
    const result = await response.json()
    if (response.ok) {
      showToast(result.stopped ? `Stopped ${jobId} crawl.` : result.message)
      await fetchJobs()
      await fetchRuns(runsPage.value)
      await fetchStats()
    } else {
      showToast(`Stop failed: ${result.detail || 'Unknown error'}`, true)
    }
  } catch (err: any) {
    showToast(`Stop failed: ${err.message}`, true)
  } finally {
    stoppingJobId.value = null
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

// Celery Status Monitor
async function fetchCeleryStatus() {
  try {
    const res = await fetch('/worker/celery/status')
    if (!res.ok) throw new Error('Failed to fetch celery status')
    const data = await res.json()
    celeryWorkers.value = data.workers || []
    celeryStatus.value = data.status || 'offline'
  } catch (err) {
    console.error('Error fetching Celery status:', err)
    celeryStatus.value = 'error'
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


// Periodic auto-sync statistics
let syncInterval: ReturnType<typeof setInterval> | null = null

onMounted(async () => {
  await fetchStats()
  await fetchJobs()
  await fetchCeleryStatus()
  await fetchRuns(1)
  connectLogsStream()

  syncInterval = setInterval(async () => {
    await fetchStats()
    await fetchJobs()
    await fetchCeleryStatus()
    await fetchRuns(runsPage.value)
  }, 6000)
})

onUnmounted(() => {
  if (syncInterval) clearInterval(syncInterval)
  if (eventSource) eventSource.close()
})
</script>

<template>
  <div class="h-full flex flex-col antialiased bg-[#1c1c1c] text-[#ededed] font-sans selection:bg-[#3ecf8e]/30 selection:text-white">
    <!-- Supabase-like Top Navbar -->
    <header class="flex-shrink-0 bg-[#161616] border-b border-[#2e2e2e] px-6 py-3 flex items-center justify-between">
      <div class="flex items-center gap-6">
        <!-- Supabase logo green triangle or icon -->
        <div class="flex items-center gap-2.5">
          <svg class="h-6 w-6 text-[#3ecf8e]" fill="currentColor" viewBox="0 0 100 100">
            <polygon points="50,15 90,85 10,85" />
          </svg>
          <span class="text-sm font-semibold tracking-tight text-white font-mono">WAPOW! Ops Control</span>
        </div>
        <div class="hidden sm:flex items-center gap-2 text-xs">
          <span class="text-[#888]">ruthvik-vijayakumar</span>
          <span class="text-[#333]">/</span>
          <span class="font-medium text-[#c0c0c0]">wapow-worker</span>
          <span class="ml-2 bg-[#1c1c1c] text-[10px] font-mono text-[#3ecf8e] px-2 py-0.5 rounded border border-[#3ecf8e]/20">production</span>
        </div>
      </div>
      <div class="flex items-center gap-4">
        <span class="text-[11px] text-[#666666] font-mono">{{ lastUpdated }}</span>
        <div :class="[
          'flex items-center gap-2 px-3 py-1 rounded border text-xs font-medium bg-[#111]',
          schedulerActive 
            ? 'border-[#3ecf8e]/20 text-[#3ecf8e] bg-[#3ecf8e]/5' 
            : 'border-rose-900/30 text-rose-400 bg-rose-500/5'
        ]">
          <span :class="[
            'h-1.5 w-1.5 rounded-full',
            schedulerActive ? 'bg-[#3ecf8e] animate-pulse' : 'bg-rose-500'
          ]"></span>
          <span class="font-mono text-[11px]">Scheduler: {{ schedulerActive ? 'active' : 'inactive' }}</span>
        </div>
      </div>
    </header>

    <!-- Main Split-Screen Workspace -->
    <main class="flex-grow p-6 overflow-hidden flex flex-col lg:flex-row gap-6 max-w-[1600px] w-full mx-auto">
      
      <!-- Left Pane: Control Panel (lg:w-7/12) -->
      <div class="lg:w-7/12 flex flex-col space-y-6 overflow-y-auto custom-scroll pr-0 lg:pr-2">
        
        <!-- Supabase Styled KPI Grid -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="bg-[#161616] border border-[#2e2e2e] hover:border-[#3ecf8e]/40 p-4 rounded-lg flex flex-col transition duration-200">
            <span class="text-[10px] font-bold tracking-wider text-[#888] uppercase">Total Stories</span>
            <span class="text-2xl font-bold font-mono mt-2 text-white tracking-tight">{{ totalArticles.toLocaleString() }}</span>
          </div>
          <div class="bg-[#161616] border border-[#2e2e2e] hover:border-[#3ecf8e]/40 p-4 rounded-lg flex flex-col transition duration-200">
            <span class="text-[10px] font-bold tracking-wider text-[#888] uppercase">Scrape Runs</span>
            <span class="text-2xl font-bold font-mono mt-2 text-white tracking-tight">{{ totalRuns }}</span>
          </div>
          <div class="bg-[#161616] border border-[#2e2e2e] hover:border-[#3ecf8e]/40 p-4 rounded-lg flex flex-col transition duration-200">
            <span class="text-[10px] font-bold tracking-wider text-[#888] uppercase">Success Rate</span>
            <span class="text-2xl font-bold font-mono mt-2 text-[#3ecf8e] tracking-tight">{{ successRatePercent }}%</span>
          </div>
          <div class="bg-[#161616] border border-[#2e2e2e] hover:border-[#3ecf8e]/40 p-4 rounded-lg flex flex-col transition duration-200">
            <span class="text-[10px] font-bold tracking-wider text-[#888] uppercase">Scraped / Saved</span>
            <span class="text-2xl font-bold font-mono mt-2 text-white tracking-tight">{{ totalScraped }} / {{ totalSaved }}</span>
          </div>
        </div>

        <!-- Scheduler & Crawl Triggers -->
        <div class="bg-[#161616] border border-[#2e2e2e] rounded-lg overflow-hidden">
          <div class="p-4 border-b border-[#2e2e2e] bg-[#111] flex items-center justify-between">
            <div>
              <h2 class="text-xs font-bold text-white uppercase tracking-wider">Scheduled Crawlers & Triggers</h2>
              <p class="text-[10px] text-[#888] mt-0.5">Manage scheduled scraping tasks and execute crawls instantly</p>
            </div>
            <div class="flex items-center gap-2">
              <button 
                @click="triggerJob('all')" 
                :disabled="triggeringJob" 
                class="bg-[#3ecf8e] text-black hover:bg-[#3ac084] font-semibold text-[10px] py-1 px-3 rounded transition duration-200 cursor-pointer disabled:bg-neutral-800 disabled:text-neutral-500 font-mono"
              >
                Crawl All
              </button>
              <button
                @click="triggerJob('web_scrape')"
                :disabled="triggeringJob"
                class="bg-[#1c1c1c] text-[#aaa] hover:text-white hover:bg-neutral-900 border border-[#333] font-semibold text-[10px] py-1 px-3 rounded transition duration-200 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed font-mono"
              >
                Crawl Web
              </button>
              <button 
                @click="fetchStats" 
                class="bg-[#1c1c1c] text-[#888] hover:text-white px-2 py-1 rounded border border-[#333] transition flex items-center justify-center cursor-pointer"
                title="Refresh Stats"
              >
                <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 8H18.2M7 9a4 4 0 110-8h1.5" />
                </svg>
              </button>
            </div>
          </div>
          <div class="divide-y divide-[#2e2e2e]">
            <div v-for="job in jobs" :key="job.id" class="p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div class="space-y-1">
                <div class="flex items-center gap-2">
                  <h3 class="text-xs font-bold text-white font-mono uppercase tracking-wider">{{ job.name }}</h3>
                  <span :class="[
                    'inline-flex border px-2 py-0.5 rounded text-[9px] font-mono tracking-wider lowercase',
                    job.running
                      ? 'border-amber-500/20 bg-amber-500/10 text-amber-400'
                      : job.status === 'paused' 
                      ? 'border-rose-900/30 bg-rose-500/10 text-rose-400' 
                      : 'border-[#3ecf8e]/20 bg-[#3ecf8e]/10 text-[#3ecf8e]'
                  ]">{{ job.running ? 'running' : job.status }}</span>
                </div>
                <p class="text-xs text-[#888]">
                  Frequency: <span class="font-mono text-white">{{ job.trigger }}</span>
                  <span v-if="!job.manual">
                    | Next: <span class="font-mono text-[#aaa]">{{ job.next_run_time || 'Paused' }}</span>
                  </span>
                  <span v-if="job.running && job.active_run?.task_id">
                    | Task: <span class="font-mono text-amber-400">{{ job.active_run.task_id.substring(0, 8) }}</span>
                  </span>
                </p>
              </div>
              <div class="flex items-center gap-2">
                <button 
                  v-if="!job.manual"
                  @click="handleToggleJob(job.id, job.status === 'paused')"
                  :disabled="job.running"
                  :class="[
                    'text-xs font-semibold px-3 py-1.5 rounded transition cursor-pointer font-mono',
                    job.running
                      ? 'bg-neutral-900 text-[#555] border border-[#333] cursor-not-allowed'
                      :
                    job.status === 'paused'
                      ? 'bg-[#3ecf8e]/15 hover:bg-[#3ecf8e]/25 text-[#3ecf8e] border border-[#3ecf8e]/30'
                      : 'bg-rose-500/15 hover:bg-rose-500/25 text-rose-400 border border-rose-500/30'
                  ]"
                >
                  {{ job.status === 'paused' ? 'Resume' : 'Pause' }}
                </button>
                <button 
                  @click="triggerJob(job.id)"
                  :disabled="triggeringJob || job.running"
                  class="bg-transparent hover:bg-neutral-900 border border-[#444] text-white text-xs font-semibold px-3 py-1.5 rounded transition cursor-pointer font-mono disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Run
                </button>
                <button
                  v-if="job.running"
                  @click="stopJob(job.id)"
                  :disabled="stoppingJobId === job.id"
                  class="bg-rose-500/15 hover:bg-rose-500/25 border border-rose-500/30 text-rose-400 text-xs font-semibold px-3 py-1.5 rounded transition cursor-pointer font-mono disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {{ stoppingJobId === job.id ? 'Stopping' : 'Stop' }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Celery Task Workers Monitor -->
        <div class="bg-[#161616] border border-[#2e2e2e] rounded-lg overflow-hidden">
          <div class="p-4 border-b border-[#2e2e2e] bg-[#111] flex items-center justify-between">
            <h2 class="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              Celery Worker Pools
              <span :class="[
                'inline-flex border px-2 py-0.5 rounded text-[9px] font-mono tracking-wider lowercase',
                celeryStatus === 'online' 
                  ? 'border-[#3ecf8e]/20 bg-[#3ecf8e]/10 text-[#3ecf8e]' 
                  : 'border-rose-900/30 bg-rose-500/10 text-rose-400'
              ]">{{ celeryStatus }}</span>
            </h2>
            <button 
              @click="fetchCeleryStatus" 
              class="bg-[#1c1c1c] text-[10px] text-[#888] hover:text-white px-2 py-1 rounded border border-[#333] transition cursor-pointer font-mono"
            >
              Inspect
            </button>
          </div>
          <div class="divide-y divide-[#2e2e2e]">
            <div v-if="celeryWorkers.length === 0" class="p-4 text-center text-[#666] text-xs font-mono">
              No task workers online. Connecting to Redis broker...
            </div>
            <div v-for="worker in celeryWorkers" :key="worker.name" class="p-4 space-y-3">
              <div class="flex items-center justify-between gap-4">
                <div class="flex items-center gap-2 truncate">
                  <span class="h-2 w-2 rounded-full bg-[#3ecf8e] animate-pulse"></span>
                  <span class="text-xs font-bold text-white font-mono truncate">{{ worker.name }}</span>
                </div>
                <div class="flex items-center gap-2 flex-shrink-0">
                  <span class="bg-[#111] border border-[#222] text-[10px] text-[#aaa] px-2 py-0.5 rounded font-mono">
                    Active: {{ worker.active_tasks_count }}
                  </span>
                  <span class="bg-[#111] border border-[#222] text-[10px] text-[#aaa] px-2 py-0.5 rounded font-mono">
                    Reserved: {{ worker.reserved_tasks_count }}
                  </span>
                </div>
              </div>
              
              <!-- Active Tasks list -->
              <div v-if="worker.active_tasks && worker.active_tasks.length > 0" class="bg-black/60 border border-[#2e2e2e] rounded p-2.5 text-xs space-y-1.5">
                <div class="text-[9px] font-bold uppercase tracking-wider text-[#555] font-mono">Executing Tasks:</div>
                <ul class="space-y-1 divide-y divide-[#111] font-mono text-[#aaa] text-[10px]">
                  <li v-for="task in worker.active_tasks" :key="task.id" class="pt-1 first:pt-0 flex items-center justify-between gap-4">
                    <span class="text-[#3ecf8e] truncate">{{ task.name }}</span>
                    <span class="text-[#555] text-[9px]">id: {{ task.id.substring(0,8) }}</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <!-- Sources Management Section -->
        <div class="bg-[#161616] border border-[#2e2e2e] rounded-lg overflow-hidden">
          <div class="p-4 border-b border-[#2e2e2e] bg-[#111] flex items-center justify-between">
            <h2 class="text-xs font-bold text-white uppercase tracking-wider">Crawl Sources Registry</h2>
            <div class="flex items-center gap-2">
              <button @click="openAddSourceModal" class="bg-[#3ecf8e] text-black hover:bg-[#3ac084] font-bold text-[10px] py-1 px-2.5 rounded transition cursor-pointer font-mono">
                + Register Source
              </button>
              <select v-model="sourceFilter" class="bg-[#111] border border-[#333] text-[10px] text-white rounded px-2 py-1 focus:outline-none cursor-pointer">
                <option value="all">All</option>
                <option value="success">Success</option>
                <option value="failed">Failed</option>
                <option value="never run">Never Run</option>
                <option value="disabled">Disabled</option>
              </select>
            </div>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs text-[#ccc]">
              <thead class="text-[10px] uppercase bg-black/40 text-[#888] border-b border-[#2e2e2e] font-mono">
                <tr>
                  <th class="py-2.5 px-4 font-semibold">Name</th>
                  <th class="py-2.5 px-4 font-semibold">Type</th>
                  <th class="py-2.5 px-4 font-semibold">Category</th>
                  <th class="py-2.5 px-4 font-semibold">Crawl URL</th>
                  <th class="py-2.5 px-4 font-semibold">Last crawl</th>
                  <th class="py-2.5 px-4 font-semibold">Status</th>
                  <th class="py-2.5 px-4 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[#2e2e2e] font-mono text-[11px]">
                <tr v-if="filteredSources.length === 0">
                  <td colspan="7" class="py-6 text-center text-[#666]">No sources found</td>
                </tr>
                <tr v-for="src in filteredSources" :key="src.name" class="hover:bg-black/20 transition duration-150">
                  <td class="py-2.5 px-4 font-semibold text-white truncate max-w-[120px]">{{ src.name }}</td>
                  <td class="py-2.5 px-4">
                    <span :class="[
                      'inline-flex border px-1.5 py-0.5 rounded text-[9px] uppercase tracking-wider',
                      src.type === 'web'
                        ? 'border-blue-500/20 bg-blue-500/10 text-blue-300'
                        : 'border-[#3ecf8e]/20 bg-[#3ecf8e]/10 text-[#3ecf8e]'
                    ]">{{ src.type }}</span>
                  </td>
                  <td class="py-2.5 px-4 text-[#888]">{{ src.category }}</td>
                  <td class="py-2.5 px-4 max-w-[160px] truncate">
                    <a :href="src.url" target="_blank" class="text-blue-400 hover:underline">{{ src.url }}</a>
                  </td>
                  <td class="py-2.5 px-4 text-[#666] text-[10px]">{{ src.last_scraped_at ? new Date(src.last_scraped_at).toLocaleTimeString() : 'Never' }}</td>
                  <td class="py-2.5 px-4">
                    <span v-if="!src.enabled" class="text-[#666]">disabled</span>
                    <span v-else-if="src.last_status === 'success'" class="text-[#3ecf8e]">success</span>
                    <span v-else-if="src.last_status === 'failed'" class="text-rose-500">failed</span>
                    <span v-else class="text-[#888]">never</span>
                  </td>
                  <td class="py-2.5 px-4 space-x-2 text-[10px]">
                    <button @click="toggleSource(src.type, src.name)" class="text-[#888] hover:text-white transition">{{ src.enabled ? 'Disable' : 'Enable' }}</button>
                    <button @click="openEditSourceModal(src.type, src.name)" class="text-[#3ecf8e] hover:underline">Edit</button>
                    <button @click="deleteSource(src.type, src.name)" class="text-rose-500 hover:underline">Delete</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Ingested Stories collapsible feed -->
        <div class="bg-[#161616] border border-[#2e2e2e] rounded-lg overflow-hidden">
          <div class="p-4 border-b border-[#2e2e2e] bg-[#111]">
            <h2 class="text-xs font-bold text-white uppercase tracking-wider">Ingested Stories Log</h2>
          </div>
          <div class="divide-y divide-[#2e2e2e] max-h-[350px] overflow-y-auto custom-scroll">
            <div v-if="recentArticles.length === 0" class="p-6 text-center text-[#666] text-xs">No articles ingested.</div>
            <div v-for="art in recentArticles" :key="art.id" class="p-3.5 hover:bg-black/10">
              <div 
                @click="toggleArticleJSON(art.id, `left-pane-${art.id}`)" 
                class="flex items-center justify-between gap-4 cursor-pointer group"
              >
                <div class="truncate space-y-1">
                  <div class="text-xs font-semibold text-white group-hover:text-[#3ecf8e] transition truncate flex items-center gap-1.5">
                    <svg 
                      :class="[
                        'w-3 h-3 text-[#555] group-hover:text-[#3ecf8e] transition-transform duration-200 flex-shrink-0',
                        expandedArticles.has(`left-pane-${art.id}`) ? 'rotate-90' : ''
                      ]"
                      fill="none" 
                      viewBox="0 0 24 24" 
                      stroke="currentColor"
                    >
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                    </svg>
                    <span>{{ art.title }}</span>
                  </div>
                  <div class="flex items-center gap-2 text-[10px] text-[#666] font-mono">
                    <span class="text-[#3ecf8e]">{{ art.publisher }}</span>
                    <span>•</span>
                    <span class="capitalize">{{ art.category }}</span>
                  </div>
                </div>
                <span class="text-[10px] bg-[#111] px-1.5 py-0.5 rounded font-mono text-[#888] border border-[#222] flex-shrink-0">{{ art.id.substring(0,8) }}</span>
              </div>
              
              <!-- Collapsible JSON view -->
              <div v-if="expandedArticles.has(`left-pane-${art.id}`)" class="mt-3">
                <div class="relative bg-black border border-[#2e2e2e] rounded overflow-hidden">
                  <div class="flex items-center justify-between px-3 py-1 bg-[#111] border-b border-[#2e2e2e]">
                    <span class="text-[9px] font-mono text-[#555]">database record json</span>
                    <button @click="copyArticleJSON(art.id)" class="text-[9px] bg-[#1c1c1c] text-[#3ecf8e] px-2 py-0.5 rounded font-mono border border-[#3ecf8e]/20 hover:bg-[#3ecf8e]/10">Copy</button>
                  </div>
                  <pre class="p-3 text-[10px] font-mono text-[#888] overflow-x-auto max-h-[160px] custom-scroll select-text">{{ loadedArticleJSONs[art.id] }}</pre>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- Right Pane: Real-Time Logger & Runs (lg:w-5/12) -->
      <div class="lg:w-5/12 flex flex-col space-y-6 overflow-y-auto custom-scroll">
        
        <!-- Live Console Stream -->
        <div class="bg-[#161616] border border-[#2e2e2e] rounded-lg p-5 flex flex-col flex-shrink-0 h-[480px]">
          <div class="flex items-center justify-between border-b border-[#2e2e2e] pb-3 mb-3">
            <div>
              <h2 class="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                Worker Live Terminal
                <span :class="[
                  'text-[9px] px-1.5 py-0.5 rounded font-mono uppercase tracking-wider border font-semibold',
                  loggerConnStatus === 'Live Stream Active' 
                    ? 'bg-[#3ecf8e]/10 text-[#3ecf8e] border-[#3ecf8e]/20' 
                    : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                ]">{{ loggerConnStatus === 'Live Stream Active' ? 'active' : 'offline' }}</span>
              </h2>
            </div>
            <button @click="clearConsole" class="text-[10px] bg-transparent text-[#aaa] border border-[#444] hover:text-white px-2 py-1 rounded transition cursor-pointer font-mono">
              Clear
            </button>
          </div>
          <!-- Terminal logs container -->
          <div ref="logsConsole" class="font-mono text-[11px] bg-black border border-[#2e2e2e] p-4 rounded overflow-y-auto flex-grow custom-scroll space-y-1 text-[#888] select-text">
            <div v-if="logLines.length === 0" class="text-[#555] font-mono">[READY] Live logs stream connected. Waiting for tasks...</div>
            <div 
              v-for="(line, idx) in logLines" 
              :key="idx"
              :class="[
                'font-mono whitespace-pre-wrap break-all',
                line.type === 'error' ? 'text-rose-500 font-semibold' : '',
                line.type === 'warn' ? 'text-amber-500' : '',
                line.type === 'system' ? 'text-white font-semibold' : '',
                line.type === 'success' ? 'text-[#3ecf8e]' : '',
                line.type === 'info' ? 'text-[#888]' : ''
              ]"
            >{{ line.text }}</div>
          </div>
        </div>

        <!-- Recent Runs History -->
        <div class="bg-[#161616] border border-[#2e2e2e] rounded-lg overflow-hidden flex flex-col flex-grow">
          <div class="p-4 border-b border-[#2e2e2e] bg-[#111]">
            <h2 class="text-xs font-bold text-white uppercase tracking-wider">Crawl Executions Log</h2>
          </div>
          <div class="overflow-x-auto flex-grow">
            <table class="w-full text-left text-xs text-[#ccc]">
              <thead class="text-[10px] uppercase bg-black/40 text-[#888] border-b border-[#2e2e2e] font-mono">
                <tr>
                  <th class="py-2.5 px-4 font-semibold">Job</th>
                  <th class="py-2.5 px-4 font-semibold">Duration</th>
                  <th class="py-2.5 px-4 font-semibold">Status</th>
                  <th class="py-2.5 px-4 font-semibold">Saved</th>
                  <th class="py-2.5 px-4 font-semibold">Trace details</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[#2e2e2e] font-mono text-[11px]">
                <tr v-if="recentRuns.length === 0">
                  <td colspan="5" class="py-6 text-center text-[#666]">No executions recorded.</td>
                </tr>
                <tr v-for="run in recentRuns" :key="run._id || run.start_time" class="hover:bg-black/10 align-top">
                  <td class="py-2.5 px-4 text-white truncate max-w-[80px]">{{ run.job_id }}</td>
                  <td class="py-2.5 px-4 text-[#888]">{{ run.duration_seconds ? `${run.duration_seconds.toFixed(1)}s` : '-' }}</td>
                  <td class="py-2.5 px-4">
                    <span v-if="run.status === 'success'" class="text-[#3ecf8e]">success</span>
                    <span v-else-if="run.status === 'failed'" class="text-rose-500">failed</span>
                    <span v-else-if="run.status === 'cancelled'" class="text-[#888]">cancelled</span>
                    <span v-else class="text-amber-500 animate-pulse">running</span>
                  </td>
                  <td class="py-2.5 px-4 text-white">{{ run.items_saved }}</td>
                  <td class="py-2.5 px-4 max-w-[180px]">
                    <div v-if="run.saved_articles && run.saved_articles.length > 0" class="text-[10px] text-[#888] truncate">
                      Ingested: {{ run.saved_articles.map(a => a.title).join(', ') }}
                    </div>
                    <div v-if="run.errors && run.errors.length > 0" class="text-[10px] text-rose-500 truncate font-semibold">
                      Errors: {{ run.errors.join(', ') }}
                    </div>
                    <span v-if="(!run.saved_articles || run.saved_articles.length === 0) && (!run.errors || run.errors.length === 0)" class="text-[#555]">-</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <!-- Pagination -->
          <div class="flex items-center justify-between border-t border-[#2e2e2e] bg-[#111] px-4 py-3 flex-shrink-0 font-mono text-[10px]">
            <div class="text-[#666]">
              Pg {{ runsPage }}/{{ totalRunsPages }}
            </div>
            <div class="flex items-center gap-1.5">
              <button 
                @click="fetchRuns(runsPage - 1)" 
                :disabled="runsPage <= 1"
                class="bg-[#1c1c1c] hover:bg-neutral-900 border border-[#2e2e2e] text-[#aaa] hover:text-white px-2 py-1 rounded disabled:opacity-30 disabled:hover:bg-[#111] transition cursor-pointer disabled:cursor-not-allowed"
              >
                &lt;
              </button>
              <button 
                @click="fetchRuns(runsPage + 1)" 
                :disabled="runsPage >= totalRunsPages"
                class="bg-[#1c1c1c] hover:bg-neutral-900 border border-[#2e2e2e] text-[#aaa] hover:text-white px-2 py-1 rounded disabled:opacity-30 disabled:hover:bg-[#111] transition cursor-pointer disabled:cursor-not-allowed"
              >
                &gt;
              </button>
            </div>
          </div>
        </div>

      </div>
    </main>

    <!-- Source Modal (Add/Edit) -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      <div class="bg-[#161616] border border-[#2e2e2e] w-full max-w-lg rounded-lg overflow-hidden shadow-2xl flex flex-col font-sans">
        <div class="p-5 border-b border-[#2e2e2e] flex items-center justify-between bg-[#111]">
          <h2 class="text-xs font-bold text-white uppercase tracking-wider font-mono">{{ modalMode === 'add' ? 'Register New Source' : 'Edit Source Settings' }}</h2>
          <button @click="showModal = false" class="text-[#666] hover:text-white transition cursor-pointer text-lg font-bold">&times;</button>
        </div>

        <div class="p-5 space-y-4 text-xs">
          <div class="grid grid-cols-2 gap-4">
            <div class="flex flex-col space-y-1">
              <label class="text-[10px] font-bold text-[#888] uppercase font-mono">Source Type</label>
              <select v-model="sourceForm.type" class="bg-black border border-[#2e2e2e] text-white rounded px-3 py-2 focus:outline-none focus:border-[#3ecf8e] transition font-mono">
                <option value="rss">RSS Feed</option>
                <option value="web">Web Page</option>
              </select>
            </div>
            <div class="flex flex-col space-y-1">
              <label class="text-[10px] font-bold text-[#888] uppercase font-mono">Category</label>
              <input v-model="sourceForm.category" type="text" placeholder="e.g. technology, sports" class="bg-black border border-[#2e2e2e] text-white rounded px-3 py-2 focus:outline-none focus:border-[#3ecf8e] transition" />
            </div>
          </div>

          <div class="flex flex-col space-y-1">
            <label class="text-[10px] font-bold text-[#888] uppercase font-mono">Source Name</label>
            <input v-model="sourceForm.name" type="text" placeholder="e.g. TechCrunch" class="bg-black border border-[#2e2e2e] text-white rounded px-3 py-2 focus:outline-none focus:border-[#3ecf8e] transition" />
          </div>

          <div class="flex flex-col space-y-1">
            <label class="text-[10px] font-bold text-[#888] uppercase font-mono">Crawl / Feed URL</label>
            <input v-model="sourceForm.url" type="text" placeholder="e.g. https://techcrunch.com/feed/" class="bg-black border border-[#2e2e2e] text-white rounded px-3 py-2 focus:outline-none focus:border-[#3ecf8e] transition" />
          </div>

          <div class="flex items-center gap-2 pt-1.5">
            <input v-model="sourceForm.enabled" id="source-enabled" type="checkbox" class="h-4 w-4 rounded bg-black border-[#2e2e2e] text-[#3ecf8e] accent-[#3ecf8e] cursor-pointer" />
            <label for="source-enabled" class="text-xs text-white font-medium cursor-pointer selection:bg-transparent">Enable immediately for scheduled triggers</label>
          </div>

          <div v-if="sourceForm.type === 'web'" class="flex items-center gap-2 pt-1.5">
            <input v-model="sourceForm.use_playwright" id="source-use-playwright" type="checkbox" class="h-4 w-4 rounded bg-black border-[#2e2e2e] text-[#3ecf8e] accent-[#3ecf8e] cursor-pointer" />
            <label for="source-use-playwright" class="text-xs text-white font-medium cursor-pointer selection:bg-transparent">Render page with Playwright</label>
          </div>
        </div>

        <div class="p-5 border-t border-[#2e2e2e] flex items-center justify-end gap-3 bg-[#111]">
          <button @click="showModal = false" class="bg-transparent hover:bg-neutral-900 border border-[#333] text-white text-xs font-semibold px-4 py-2 rounded transition cursor-pointer font-mono">
            Cancel
          </button>
          <button @click="handleSaveSource" class="bg-[#3ecf8e] hover:bg-[#3ac084] text-black text-xs font-bold px-4 py-2 rounded transition cursor-pointer font-mono">
            Save Source
          </button>
        </div>
      </div>
    </div>

    <!-- Supabase Toast style banner -->
    <div :class="[
      'fixed bottom-6 right-6 px-5 py-3.5 rounded shadow-2xl flex items-center gap-3 z-50 transition-all duration-300 bg-[#161616]',
      toastIsError ? 'border border-rose-800/60' : 'border border-[#3ecf8e]/30',
      toastVisible ? 'translate-y-0 opacity-100' : 'translate-y-36 opacity-0 pointer-events-none'
    ]">
      <div :class="[
        'h-2 w-2 rounded-full',
        toastIsError ? 'bg-rose-500 animate-pulse' : 'bg-[#3ecf8e] animate-pulse'
      ]"></div>
      <p class="text-xs font-medium text-white font-mono">{{ toastMsg }}</p>
    </div>
  </div>
</template>
