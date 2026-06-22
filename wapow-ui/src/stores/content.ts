import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// Washington Post Article Interface based on new JSON structure
export interface Article {
  _id: string
  ai_summary: any
  additional_properties: any
  canonical_url: string
  canonical_website: string
  comments: {
    ai_prompt: {
      content: string
      display_avatar: boolean
      enabled: boolean
    }
    ai_summary: {
      enabled: boolean
    }
    display_comments: boolean
  }
  content_elements: Array<{
    _id: string
    additional_properties: {
      _id: number
      cadit_quaestio: any[]
    }
    content: string
    type: string
  }>
  content_restrictions: {
    content_code: string
  }
  copyright: string
  created_date: string
  credits: {
    audio_narrators: any[]
    audio_producers: any[]
    by: Array<{
      _id: string
      additional_properties: Record<string, any>
      description: string
      image: {
        url: string
        version: string
      }
      name: string
      org: string
      slug: string
      socialLinks: Array<{
        deprecated: boolean
        deprecation_msg: string
        site: string
        url: string
      }>
      social_links: Array<{
        site: string
        url: string
      }>
      type: string
      url: string
      version: string
    }>
  }
  description: {
    basic: string
    expanded_byline: string
  }
  display_date: string
  first_publish_date: string
  headlines: {
    apple_news: string
    basic: string
    meta_title: string
    mobile: string
    native: string
    print: string
    tablet: string
    url: string
    web: string
  }
  label: {
    basic: {
      display: boolean
      text: string
      url: string
    }
    transparency: {
      display: boolean
      text: string
      url: string
    }
  }
  label_display: {
    basic: {
      text: string
      url: string
    }
    transparency: {
      text: string
      url: string
    }
  }
  language: string
  last_updated_date: string
  location: string
  owner: {
    id: string
    name: string
  }
  promo_items?: {
    basic: {
      additional_properties: Record<string, any>
      address: {
        locality: string
        region: string
      }
      caption: string
      caption_display: string
      copyright: string
      created_date: string
      credits: {
        affiliation: any[]
        by: any[]
      }
      credits_caption_display: string
      credits_display: string
      height: number
      last_updated_date: string
      licensable: boolean
      owner: {
        id: string
      }
      related_content: {
        derivative_of: any[]
      }
      source: {
        edit_url: string
        system: string
      }
      status: string
      subtitle: string
      subtype: string
      taxonomy: Record<string, any>
      type: string
      url: string
      version: string
      width: number
      _id: string
    }
  }
  planning?: {
    budget_line: string
    scheduling?: {
      planned_publish_date: string
    }
    story_length?: {
      inch_count_actual: number
      line_count_actual: number
      word_count_actual: number
    }
  }
  publishing?: {
    audience: string
    publish_date: string
    publish_time: string
    timezone: string
  }
  related_content?: {
    basic: any[]
    clonedChildren?: any[]
    clonedFromParent?: any[]
    redirect?: any[]
  }
  revision?: {
    published: boolean
    branch?: string
    editions?: any[]
    parent_id?: string
    revision_id?: string
    user_id?: string
  }
  tracking?: {
    inURL: string
    storyID: string
    author_desk?: string
    author_id?: string
    author_name?: string
    author_subdesk?: string
    author_type?: string
    content_topics?: string
  }
  websites?: Record<string, any>
  workflow?: {
    status_code: number
  }
  publish_date: string
  slug: string
  source: {
    name: string
    source_type: string
    system: string
  }
  subheadlines: {
    basic: string
  }
  subtype: string
  syndication: {
    external_distribution: boolean
    follow: boolean
    search: boolean
  }
  taxonomy: Record<string, any>
  type: string
  version: string
  website: string
  website_url: string
}

export interface Video {
  aspect_ratio: number
  content_id: string
  canonical_url: string
  promo_image: {
    url: string
  }
  streams: Array<{
    bitrate: number
    filesize: number
    height: number
    provider: string
    stream_type: string
    url: string
    width: number
  }>
  duration: number
  tracking: {
    page_name: string
    video_category: string
    video_section: string
    video_source: string
    page_title: string
    av_name: string
    av_arc_id: string
  }
}

export interface StoryContent {
  id: string
  title: string
  description: string
  thumbnail: string
  author: {
    name: string
    avatar: string
    username: string
  }
  likes: number
  comments: number
  shares: number
  views: number
  duration: string
  createdAt: string
  aspectRatio: number
  mediaType: 'story'
  audioUrl?: string
}

export type MediaItem = Video | StoryContent

export const useContentStore = defineStore('content', () => {
  const videos = ref<Video[]>([])
  const podcastClips = ref<StoryContent[]>([])
  const articles = ref<Article[]>([])
  const isLoading = ref(false)

  // ── Infinite-scroll pagination state (articles) ──
  const ARTICLES_PAGE_SIZE = 24
  const articlesCategory = ref<string | null>(null)
  const articlesPage = ref(1)
  const articlesTotalPages = ref(1)
  const articlesLoadingMore = ref(false)
  const articlesHasMore = ref(false)

  const createArticleFromSource = (source: any): Article => {
    return {
      ...source,
      _id: source._id || '',
      ai_summary: source.ai_summary || {},
      additional_properties: source.additional_properties || {},
      canonical_url: source.canonical_url || '',
      canonical_website: source.canonical_website || 'washpost',
      comments: source.comments || {
        ai_prompt: { content: '', display_avatar: false, enabled: false },
        ai_summary: { enabled: false },
        display_comments: false,
      },
      content_elements: source.content_elements || [],
      content_restrictions: source.content_restrictions || { content_code: 'default' },
      copyright: source.copyright || 'The Washington Post',
      created_date: source.created_date || '',
      credits: source.credits || { audio_narrators: [], audio_producers: [], by: [] },
      description: source.description || { basic: '', expanded_byline: '' },
      display_date: source.display_date || '',
      first_publish_date: source.first_publish_date || '',
      headlines: source.headlines || {
        apple_news: '',
        basic: '',
        meta_title: '',
        mobile: '',
        native: '',
        print: '',
        tablet: '',
        url: '',
        web: '',
      },
      label: source.label || {
        basic: { display: false, text: '', url: '' },
        transparency: { display: false, text: '', url: '' },
      },
      label_display: source.label_display || {
        basic: { text: '', url: '' },
        transparency: { text: '', url: '' },
      },
      language: source.language || 'en',
      last_updated_date: source.last_updated_date || '',
      location: source.location || '',
      owner: source.owner || { id: 'washpost', name: 'The Washington Post' },
      promo_items: source.promo_items,
      planning: source.planning,
      publishing: source.publishing,
      related_content: source.related_content,
      revision: source.revision,
      tracking: source.tracking,
      websites: source.websites || {},
      workflow: source.workflow,
      publish_date: source.publish_date || '',
      slug: source.slug || '',
      source: source.source || {
        name: 'The Washington Post',
        source_type: 'staff',
        system: 'washpost',
      },
      subheadlines: source.subheadlines || { basic: '' },
      subtype: source.subtype || 'story',
      syndication: source.syndication || {
        external_distribution: false,
        follow: false,
        search: false,
      },
      taxonomy: source.taxonomy || {},
      type: source.type || 'story',
      version: source.version || '0.10.14',
      website: source.website || 'washpost',
      website_url: source.website_url || '',
    }
  }

  const getSectionData = async (
    category_id: string,
    opts: { page?: number; limit?: number } = {},
  ) => {
    const baseUrl = import.meta.env.VITE_ARTICLES_API || 'http://localhost:3001'

    if (category_id === '/videos' || category_id === '/podcasts') {
      const response = await fetch(`${baseUrl}/api${category_id}`, { method: 'GET' })
      return response.json()
    }

    const category = category_id.replace(/^\//, '')
    const params = new URLSearchParams()
    if (category) params.set('category', category)
    if (opts.page) params.set('page', String(opts.page))
    if (opts.limit) params.set('limit', String(opts.limit))
    const qs = params.toString()
    // Trailing slash matches the route (`@router.get("/")`) and avoids a 307 redirect.
    const url = `${baseUrl}/api/articles/${qs ? `?${qs}` : ''}`
    const response = await fetch(url, { method: 'GET' })
    return response.json()
  }

  /** Map + filter raw API article docs into typed Article objects. */
  const _mapArticles = (data: any[]): Article[] =>
    (data ?? [])
      .filter(
        (article: any) =>
          article.canonical_url &&
          article.promo_items &&
          Object.keys(article.promo_items).length > 0,
      )
      .map((article: any) => createArticleFromSource(article))

  /** Load the first page of a category, replacing the current article list. */
  const loadArticles = async (apiCategoryId: string) => {
    articlesCategory.value = apiCategoryId
    articlesPage.value = 1
    articlesLoadingMore.value = false

    const res = await getSectionData(apiCategoryId, { page: 1, limit: ARTICLES_PAGE_SIZE })
    articles.value = _mapArticles(res?.data)

    const totalPages = Number(res?.pages) || 1
    articlesTotalPages.value = totalPages
    articlesHasMore.value = articlesPage.value < totalPages
  }

  /** Append the next page of the current category (infinite scroll). */
  const loadMoreArticles = async () => {
    if (articlesLoadingMore.value || !articlesHasMore.value || !articlesCategory.value) {
      return
    }
    articlesLoadingMore.value = true
    try {
      const nextPage = articlesPage.value + 1
      const res = await getSectionData(articlesCategory.value, {
        page: nextPage,
        limit: ARTICLES_PAGE_SIZE,
      })
      const mapped = _mapArticles(res?.data)

      // Append while de-duplicating by _id (guards against overlap/race)
      const existingIds = new Set(articles.value.map((a) => String(a._id)))
      const fresh = mapped.filter((a) => !existingIds.has(String(a._id)))
      articles.value = [...articles.value, ...fresh]

      articlesPage.value = nextPage
      const totalPages = Number(res?.pages) || articlesTotalPages.value
      articlesTotalPages.value = totalPages
      // Detect pagination overlap: server returned docs but every one was a duplicate.
      // That signals an unstable page window — stop to avoid a runaway load loop.
      const overlapOnly = mapped.length > 0 && fresh.length === 0
      articlesHasMore.value = nextPage < totalPages && !overlapOnly
    } catch (e) {
      console.error('Error loading more articles:', e)
    } finally {
      articlesLoadingMore.value = false
    }
  }

  const getArticlesBySection = (section: string): Article[] => {
    return articles.value.filter(
      (article) =>
        article.taxonomy?.primary_section?.name === section ||
        article.taxonomy?.sections?.some((s: any) => s.name === section) ||
        article.type === section,
    )
  }

  const getArticlesByType = (type: string): Article[] => {
    return articles.value.filter((article) => article.type === type)
  }

  const getTrendingArticles = (limit: number = 10): Article[] => {
    return articles.value
      .sort((a, b) => new Date(b.display_date).getTime() - new Date(a.display_date).getTime())
      .slice(0, limit)
  }

  const loadVideos = async () => {
    videos.value = await generateVerticalVideos()
    podcastClips.value = await generatePodcastClips()
  }

  const generateVerticalVideos = async (): Promise<Video[]> => {
    try {
      const { data } = await getSectionData('/videos')

      return (
        data?.map((video: any) => ({
          aspect_ratio: video.aspect_ratio,
          content_id: video.content_id,
          canonical_url: video.canonical_url,
          promo_image: { url: video.promo_image?.url || '' },
          streams: video.streams || [],
          duration: 0,
          tracking: {
            page_name: '',
            video_category: 'vertical',
            video_section: '',
            video_source: 'The Washington Post',
            page_title: video.canonical_url.split('/').pop()?.replace('.html', '') || 'Video',
            av_name: '',
            av_arc_id: '',
          },
        })) || []
      )
    } catch (error) {
      console.error('Error loading videos:', error)
      return []
    }
  }

  const generatePodcastClips = async (): Promise<StoryContent[]> => {
    try {
      const { data } = await getSectionData('/podcasts')
      return (data ?? []).map((clip: any) => {
        const ap = clip.additional_properties ?? {}
        const audioUrl = clip.audioUrl || ap.audio_article_raw_url || ap.audio?.[0]?.url || ''
        const thumbnail = clip.imageUrl || clip.thumbnail || clip.promo_items?.basic?.url || ap.lead_art?.url || ''
        
        let author = {
          name: 'The Washington Post',
          username: '@washingtonpost',
          avatar: 'https://picsum.photos/50/50?random=wapo',
        }
        if (clip.author) {
          if (typeof clip.author === 'object') {
            author = {
              name: clip.author.name || 'Unknown Author',
              username: clip.author.username || '@unknown',
              avatar: clip.author.avatar || 'https://picsum.photos/50/50?random=podcast',
            }
          } else if (typeof clip.author === 'string') {
            author = {
              name: clip.author,
              username: '@' + clip.author.toLowerCase().replace(/[^a-z0-9]/g, ''),
              avatar: 'https://picsum.photos/50/50?random=podcast',
            }
          }
        }

        return {
          id: clip._id,
          title: clip.title || clip.headlines?.basic || 'Untitled Episode',
          description: clip.description || clip.description?.basic || '',
          audioUrl,
          thumbnail,
          author,
        }
      })
    } catch (error) {
      console.error('Error loading podcast clips:', error)
      return []
    }
  }

  const getAllMediaItems = computed((): MediaItem[] => {
    return [...videos.value, ...podcastClips.value]
  })

  const getMediaByType = (type: string) => {
    switch (type) {
      case 'video':
        return videos.value
      case 'podcast':
        return podcastClips.value
      default:
        return getAllMediaItems.value
    }
  }

  loadVideos()

  return {
    videos,
    podcastClips,
    articles,
    isLoading,
    // pagination / infinite scroll
    articlesLoadingMore,
    articlesHasMore,
    loadMoreArticles,
    getAllMediaItems,
    getMediaByType,
    loadArticles,
    getArticlesBySection,
    getArticlesByType,
    getTrendingArticles,
    loadVideos,
  }
})
