# WAPOW Content Scraping & Aggregation System

## Overview

The `wapow-scraper` service fetches articles, videos, and podcasts from multiple web sources and aggregates them into the existing MongoDB collections.

**Scope**: Full stack scraping (RSS, web scraping, YouTube API, Spotify API)
**Deployment**: Docker service in docker-compose
**Port**: 3003
**Sources**: Popular news/media sources across 5 categories

For optional **story slide generation** after article ingest (`WAPOW_API_BASE_URL`, `STORY_CONVERT_ON_INGEST`), see [CONTENT_PIPELINE.md](CONTENT_PIPELINE.md).

---

## Architecture

```
wapow-scraper/
├── scraper/
│   ├── main.py                 # FastAPI management API
│   ├── config.py               # Configuration + env vars
│   ├── db/
│   │   └── mongodb.py          # MongoDB connection
│   ├── models/
│   │   └── source.py           # Source config models
│   ├── scrapers/
│   │   ├── base.py             # Abstract base scraper
│   │   ├── rss_scraper.py      # RSS/Atom feed parser (feedparser)
│   │   ├── web_scraper.py      # BeautifulSoup scraper
│   │   ├── playwright_scraper.py # JS-heavy sites
│   │   └── api_scrapers/
│   │       ├── youtube.py      # YouTube Data API v3
│   │       └── spotify.py      # Spotify Podcast API
│   ├── processors/
│   │   ├── normalizer.py       # Transform to MongoDB schemas
│   │   └── deduplicator.py     # URL/content deduplication
│   ├── tasks/
│   │   ├── scheduler.py        # APScheduler setup
│   │   └── jobs.py             # Scraping job definitions
│   ├── utils/
│   │   ├── rate_limiter.py     # Per-domain rate limiting
│   │   └── robots.py           # robots.txt compliance
│   └── sources/
│       └── sources.yaml        # Source configurations
├── Dockerfile
├── requirements.txt
├── pyproject.toml
└── .env.example
```

---

## Current State

- MongoDB stores content in: `articles`, `videos`, `podcasts` collections
- Existing schemas defined in `/wapow-app/api/services/content.py`
- `wapow-collector` handles analytics events only (ClickHouse), not content collection
- Scraper integrates with existing content API - scraped content appears via `/api/articles`, `/api/videos`, `/api/podcasts`

---

## Data Schemas

### Articles (matches `_transform_content_item`)

```python
{
    "category": "technology|sports|travel|style|wellbeing",
    "headlines": {"basic": "Article Title"},
    "description": {"basic": "Article description..."},
    "credits": {"by": [{"name": "Author Name"}]},
    "promo_items": {"basic": {"url": "https://image.url/..."}},
    "canonical_url": "https://source.com/article",
    "publish_date": datetime,
    "created_date": datetime,
    "isActive": True,
    "_scraper_meta": {
        "source": "TechCrunch",
        "source_type": "rss",
        "scraped_at": datetime,
        "url_hash": "abc123..."
    }
}
```

### Videos (matches `_transform_video_item`)

```python
{
    "tracking": {
        "page_title": "Video Title",
        "video_section": "technology",
        "video_category": "technology",
        "av_name": "Video description..."
    },
    "promo_image": {"url": "https://thumbnail.url/..."},
    "content_id": "scraped_abc123",
    "canonical_url": "https://youtube.com/watch?v=...",
    "duration": 360,  # seconds
    "publish_date": datetime,
    "created_date": datetime,
    "isActive": True,
    "_scraper_meta": {...}
}
```

### Podcasts (matches `_transform_podcast_item`)

```python
{
    "title": "Episode Title",
    "additional_properties": {
        "page_title": "Episode Title",
        "description": "Episode description...",
        "lead_art": {"url": "https://cover.url/..."},
        "series_meta": {"name": "Podcast Show Name"}
    },
    "canonical_url": "https://open.spotify.com/episode/...",
    "duration": 1800,  # seconds
    "publish_date": datetime,
    "created_date": datetime,
    "isActive": True,
    "_scraper_meta": {...}
}
```

---

## Scraping Schedule

| Source Type | Interval | Job ID |
|-------------|----------|--------|
| RSS Feeds | Every 1 hour | `rss_feeds` |
| Web Scraping | Every 2 hours | `web_scrape` |
| YouTube | Every 6 hours | `youtube` |
| Spotify Podcasts | Every 12 hours | `spotify` |

---

## API Endpoints

### Health Check
```bash
GET /health
```
Returns service status and scheduler state.

### List Scheduled Jobs
```bash
GET /jobs
```
Returns all scheduled jobs with next run times.

### Trigger Manual Scrape
```bash
POST /jobs/{job_id}/trigger
```
Valid job IDs: `rss_feeds`, `web_scrape`, `youtube`, `spotify`, `all`

### List Configured Sources
```bash
GET /sources
```
Returns all sources from `sources.yaml` with enabled status.

### Get Configuration
```bash
GET /config
```
Returns current intervals, limits, and feature flags.

---

## Configured Sources

### RSS Feeds (Articles)

| Name | Category | URL |
|------|----------|-----|
| TechCrunch | technology | https://techcrunch.com/feed/ |
| The Verge | technology | https://www.theverge.com/rss/index.xml |
| Wired | technology | https://www.wired.com/feed/rss |
| ESPN | sports | https://www.espn.com/espn/rss/news |
| Bleacher Report | sports | https://bleacherreport.com/articles/feed |
| Lonely Planet | travel | https://www.lonelyplanet.com/blog/feed |
| Travel + Leisure | travel | https://www.travelandleisure.com/feeds/all |
| Vogue | style | https://www.vogue.com/feed/rss |
| GQ | style | https://www.gq.com/feed/rss |
| Well+Good | wellbeing | https://www.wellandgood.com/feed/ |
| Healthline | wellbeing | https://www.healthline.com/rss/nutrition |

### YouTube Channels (Videos)

| Name | Category | Channel ID |
|------|----------|------------|
| TED | technology | UCAuUUnT6oDeKwE6v1US1Llw |
| ESPN | sports | UCiWLfSweyRNmLpgEHekhoAg |
| Vogue | style | UCF9EzMZ8eFv4c4tYtUmTONg |
| National Geographic | travel | UCpVm7bg6pXKo1Pr6k5kxG9A |

### Spotify Podcasts

| Name | Show ID |
|------|---------|
| TED Talks Daily | 1VXcH8QHkjRcTCEd88U3ti |
| The Daily | 3IM0lmZxpFAY7CwMuv9H4g |
| Science Vs | 5lY4b5PGOvMuOYOjOVEYeB |
| The Mindset Mentor | 1FDkz8IOwDITGFzX1T7R14 |

---

## Environment Variables

```bash
# MongoDB (required)
MONGODB_URI=mongodb://mongo:27017/wapow-data

# YouTube Data API v3 (optional)
YOUTUBE_API_KEY=your_api_key

# Spotify Web API (optional)
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret

# Server
PORT=3003
DEBUG=false

# Scraping intervals (minutes)
SCRAPE_INTERVAL_RSS=60
SCRAPE_INTERVAL_WEB=120
SCRAPE_INTERVAL_YOUTUBE=360
SCRAPE_INTERVAL_SPOTIFY=720

# Rate limiting
DEFAULT_RATE_LIMIT_DELAY=1.0
RESPECT_ROBOTS_TXT=true
MAX_ITEMS_PER_SOURCE=50
```

---

## API Keys Setup

### YouTube Data API v3

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "YouTube Data API v3"
4. Create credentials → API Key
5. Set `YOUTUBE_API_KEY` in environment

### Spotify Web API

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Copy Client ID and Client Secret
4. Set `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` in environment

---

## Docker Integration

### Development

```yaml
# docker-compose.yml
scraper:
  build: ./wapow-scraper
  container_name: wapow-scraper
  ports:
    - "3003:3003"
  environment:
    - MONGODB_URI=${MONGODB_URI:-mongodb://mongo:27017/wapow-data}
    - YOUTUBE_API_KEY=${YOUTUBE_API_KEY:-}
    - SPOTIFY_CLIENT_ID=${SPOTIFY_CLIENT_ID:-}
    - SPOTIFY_CLIENT_SECRET=${SPOTIFY_CLIENT_SECRET:-}
  depends_on:
    mongo:
      condition: service_healthy
  restart: unless-stopped
```

### Production

```yaml
# docker-compose.prod.yml
scraper:
  image: ${REGISTRY_PREFIX}/wapow-scraper:latest
  container_name: wapow-scraper
  environment:
    - MONGODB_URI=${MONGODB_URI:-mongodb://mongo:27017/wapow-data}
    - YOUTUBE_API_KEY=${YOUTUBE_API_KEY:-}
    - SPOTIFY_CLIENT_ID=${SPOTIFY_CLIENT_ID:-}
    - SPOTIFY_CLIENT_SECRET=${SPOTIFY_CLIENT_SECRET:-}
  depends_on:
    - mongo
  restart: unless-stopped
```

---

## Verification Steps

### 1. Build and Start

```bash
docker-compose up --build scraper
```

### 2. Check Health

```bash
curl http://localhost:3003/health
# {"status":"healthy","service":"wapow-scraper","scheduler":"running"}
```

### 3. List Jobs

```bash
curl http://localhost:3003/jobs
```

### 4. Trigger Manual Scrape

```bash
# Scrape RSS feeds
curl -X POST http://localhost:3003/jobs/rss_feeds/trigger

# Scrape all sources
curl -X POST http://localhost:3003/jobs/all/trigger
```

### 5. Verify in MongoDB

```javascript
// Connect to MongoDB
db.articles.find({"_scraper_meta": {$exists: true}}).limit(5)
db.videos.find({"_scraper_meta": {$exists: true}}).limit(5)
db.podcasts.find({"_scraper_meta": {$exists: true}}).limit(5)
```

### 6. Check Frontend

Scraped content should appear in the existing UI via the standard API endpoints:
- `/api/articles`
- `/api/videos`
- `/api/podcasts`

---

## Adding New Sources

Edit `wapow-scraper/scraper/sources/sources.yaml`:

### Add RSS Feed

```yaml
rss:
  - name: "New Source"
    url: "https://example.com/feed.xml"
    category: "technology"  # technology|sports|travel|style|wellbeing
    enabled: true
```

### Add YouTube Channel

```yaml
youtube:
  - name: "Channel Name"
    channel_id: "UCxxxxxxxxxx"  # From channel URL
    category: "technology"
    max_results: 10
    enabled: true
```

### Add Spotify Podcast

```yaml
spotify:
  - name: "Podcast Name"
    show_id: "xxxxxxxxxx"  # From Spotify show URL
    max_episodes: 10
    enabled: true
```

### Add Web Scraping Source

```yaml
web:
  - name: "Site Name"
    url: "https://example.com/news"
    category: "technology"
    enabled: true
    use_playwright: false  # Set true for JS-heavy sites
    selectors:
      articles: "article"
      title: "h2"
      description: "p.excerpt"
      image: "img"
      link: "a"
      author: ".author"
      date: "time"
```

---

## Troubleshooting

### Scraper not starting
- Check MongoDB is running and accessible
- Verify `MONGODB_URI` is correct

### YouTube/Spotify not scraping
- Check API keys are set correctly
- Verify keys have proper permissions
- Check `/config` endpoint for feature status

### Duplicates appearing
- Deduplication uses URL hashes stored in `_scraper_meta.url_hash`
- Clear duplicates: `db.articles.deleteMany({"_scraper_meta.url_hash": "hash_value"})`

### Rate limiting issues
- Increase `DEFAULT_RATE_LIMIT_DELAY` (default: 1 second)
- Check robots.txt compliance with `RESPECT_ROBOTS_TXT=true`

### Logs
```bash
docker logs wapow-scraper -f
```
