# Content pipeline: worker-owned article story slides

## Overview

- Raw scrape payloads live in MongoDB (`raw_articles`) for internal provenance and debugging.
- Normalized article metadata/content lives in MongoDB (`articles` collection).
- Canonical generated story decks live in MongoDB (`story_slides` collection).
- **wapow-worker** owns scraping, ingestion, conversion job records, Celery enqueueing, Celery task execution, story generation, and `story_slides` persistence.
- **wapow-app** is a passive reader. It may include existing generated slides in article/feed responses, but it does not create conversion jobs, enqueue Celery tasks, or run story generation.

## Canonical story output

### Data shape

Worker-owned `story_slides` documents are the canonical frontend story payload:

- `article_id`: article `_id`
- `pages`: array of slides with `page_type` `content` or `overview`
- Each `content` slide includes `content[]` items such as `type: "text"` and optionally `type: "image"` with `content_url`
- `generation_timestamp`, `llm_model_used` (`heuristic-v1` or OpenAI model id), `slide_count`

wapow-app exposes these decks through `/api/stories` and `/api/stories/{article_id}`. It also maps this into the legacy response field `ai_summary.pages` for frontend compatibility only.

### Slide count

- Short articles may produce a single text-only or image-supported slide.
- Typical articles produce a few content slides plus an overview when useful.
- Total stories should stay concise, generally **5-6 slides max**.
- Images are optional. If usable article images are missing, redundant, low quality, or irrelevant, the worker generates text-only slides.

## wapow-worker: conversion control plane

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/worker/conversion-jobs` | Body: `{ "article_id": "...", "force": false }`; validates the article, creates a job, and enqueues Celery |
| `POST` | `/worker/conversion-jobs/batch` | Body: `{ "ids": ["..."], "force": false }`; max **50** ids |
| `GET` | `/worker/conversion-jobs/{job_id}` | Status: `pending` → `processing` → `completed` or `failed` |
| `POST` | `/worker/conversion-jobs/{job_id}/retry` | Requeue a failed conversion job |
| `GET` | `/worker/status` | Read conversion worker pause state |
| `POST` | `/worker/pause` | Pause conversion workers |
| `POST` | `/worker/resume` | Resume conversion workers |

Manual/admin conversion controls should be exposed through this worker API and protected by deployment network policy or an internal token.
Set `WORKER_INTERNAL_TOKEN` to require callers to send `X-Internal-Token`.

## wapow-app: passive slide reader

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/stories` | Return canonical story deck payloads from `story_slides`, with normalized article metadata from `articles` |
| `GET` | `/api/stories/{id}` | Return one canonical story deck by article id |
| `POST` | `/api/stories/by-ids` | Return canonical story decks for a batch of article ids |
| `GET` | `/api/articles/{id}` | Return article and include existing `story_slides` as `ai_summary` when present |
| `GET` | `/api/articles` | Return articles and include existing `story_slides` in batch when present |

wapow-app intentionally has no `/convert-to-story`, `/preview-story`, `/batch-convert-to-story`, or conversion job status endpoints.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `MONGODB_URI` | MongoDB connection |
| `REDIS_URL` | Celery broker/backend for wapow-worker |
| `GEMINI_API_KEY` | Optional; enables Gemini slide generation |
| `OPENAI_API_KEY` | Optional; enables fallback LLM takeaways |
| `OPENAI_MODEL` | Optional; default `gpt-4o-mini` |
| `STORY_CONVERT_ON_INGEST` | `true` for worker ingestion to auto-create conversion jobs after new article inserts |
| `WORKER_INTERNAL_TOKEN` | Optional; protects worker conversion/admin controls with `X-Internal-Token` |

### MongoDB

- Collection **`conversion_jobs`**: job documents for batch conversion (index on `job_id` created at startup).
- Collection **`story_slides`**: canonical generated slide decks.

## Docker Compose notes

- Celery workers must run the worker app: `celery -A scraper.celery_client worker --loglevel=info -E`.
- Only wapow-worker registers `tasks.convert_article_to_story`.

## Related docs

- [.kiro/specs/article-to-story-pipeline/requirements.md](../.kiro/specs/article-to-story-pipeline/requirements.md) — extended product requirements
- [docs/SCRAPER_IMPLEMENTATION.md](SCRAPER_IMPLEMENTATION.md) — scraper architecture and schedules
