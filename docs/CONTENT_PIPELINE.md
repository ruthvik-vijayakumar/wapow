# Content pipeline: DB articles → story slides (v1) + scraper hook (v2)

## Overview

- **v1:** Articles live in MongoDB (`articles` collection). The **wapow-app** API generates `ai_summary.pages` (StoryView-compatible slides) from each article’s text and images, then stores the result on the same document.
- **v2:** **wapow-scraper** ingests RSS/web items, normalizes them into the same article shape, upserts into MongoDB, and can optionally call the API to run conversion immediately after each new insert.

## wapow-app: story generation

### Data shape

`ai_summary` on an article document:

- `pages`: array of slides with `page_type` `content` or `overview`
- Each `content` slide includes `content[]` with `type: "text"` and `type: "image"` (`content_url`) — matches [wapow-ui/src/components/StoryView.vue](wapow-ui/src/components/StoryView.vue)
- `generation_timestamp`, `llm_model_used` (`heuristic-v1` or OpenAI model id), `slide_count`

### Slide count (v1 heuristic)

- Targets **3–4** content slides for short articles; adds slides as word count grows (cap **9** content slides), plus **one** `overview` (takeaways) slide.
- If **`OPENAI_API_KEY`** is set, the overview text is refined via the Chat Completions API; otherwise bullets are derived from chunked text.

### HTTP endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/articles/{id}?ensure_story=true` | Return article; generate `ai_summary` if missing |
| `POST` | `/api/articles/{id}/convert-to-story?force=false` | Generate and persist slides (skip if already present unless `force=true`) |
| `POST` | `/api/articles/{id}/preview-story` | Same as convert but **does not** write to MongoDB |
| `POST` | `/api/articles/batch-convert-to-story` | Body: `{ "ids": ["..."], "force": false }` — max **50** ids; returns **202** with `job_ids` |
| `GET` | `/api/conversion-jobs/{job_id}` | Status: `pending` → `processing` → `completed` or `failed` |

### Environment variables (wapow-app)

| Variable | Purpose |
|----------|---------|
| `MONGODB_URI` | MongoDB connection (existing) |
| `OPENAI_API_KEY` | Optional; enables LLM takeaways |
| `OPENAI_MODEL` | Optional; default `gpt-4o-mini` |

### MongoDB

- Collection **`conversion_jobs`**: job documents for batch conversion (index on `job_id` created at startup).

## wapow-scraper: post-ingest story conversion

After a successful **`insert_one`** into the articles collection, the scraper can fire an async HTTP `POST` to wapow-app.

### Environment variables (wapow-scraper)

| Variable | Purpose |
|----------|---------|
| `WAPOW_API_BASE_URL` | Base URL of wapow-app, e.g. `http://localhost:3001` or `http://api:3001` in Compose |
| `STORY_CONVERT_ON_INGEST` | `true` to enable the POST after each new article insert |

Requirements:

- wapow-app must be reachable from the scraper container/process.
- Same MongoDB database so the new article `_id` exists when the API runs.

## Docker Compose notes

- Point `WAPOW_API_BASE_URL` at the API service name and internal port (e.g. `http://wapow-app:3001` if that matches your service name).
- Start API before or with scraper so conversion requests succeed.

## Related docs

- [.kiro/specs/article-to-story-pipeline/requirements.md](../.kiro/specs/article-to-story-pipeline/requirements.md) — extended product requirements
- [docs/SCRAPER_IMPLEMENTATION.md](SCRAPER_IMPLEMENTATION.md) — scraper architecture and schedules
