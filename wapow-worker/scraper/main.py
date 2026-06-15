"""FastAPI management API and Operations Dashboard for WAPOW Scraper."""

import logging
import queue
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse

from scraper.config import settings
from scraper.db.mongodb import close_client
from scraper.tasks.scheduler import (
    scheduler,
    start_scheduler,
    shutdown_scheduler,
    get_job_info,
)
from scraper.tasks.jobs import (
    load_sources,
    run_rss_scrape,
    run_web_scrape,
    run_all_scrapers,
)
from scraper.utils.metrics import get_scraper_stats

# Configure logging memory queue for real-time dashboard streaming
log_queue = queue.Queue(maxsize=1500)


class LogQueueHandler(logging.Handler):
    """Thread-safe logging handler that directs application log messages to an in-memory queue."""

    def emit(self, record):
        try:
            msg = self.format(record)
            if log_queue.full():
                try:
                    log_queue.get_nowait()
                except Exception:
                    pass
            log_queue.put_nowait(msg)
        except Exception:
            pass


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Attach Queue Logger Handler to root logger
queue_handler = LogQueueHandler()
queue_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] (%(name)s) %(message)s", datefmt="%H:%M:%S")
queue_handler.setFormatter(formatter)
logging.getLogger().addHandler(queue_handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting WAPOW Scraper service")
    start_scheduler()
    
    from scraper.services.conversion_jobs import (
        ensure_conversion_jobs_indexes,
        start_conversion_worker,
        stop_conversion_worker,
    )
    ensure_conversion_jobs_indexes()
    asyncio.create_task(start_conversion_worker())
    
    yield
    logger.info("Shutting down WAPOW Scraper service")
    shutdown_scheduler()
    await stop_conversion_worker()
    close_client()


app = FastAPI(
    title="WAPOW Worker",
    description="Content scraping, aggregation, and AI processing service for WAPOW",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "wapow-worker",
        "scheduler": "running" if scheduler.running else "stopped",
    }


@app.get("/jobs")
async def list_jobs() -> dict[str, Any]:
    """List all scheduled jobs."""
    jobs = get_job_info()
    return {
        "jobs": jobs,
        "scheduler_running": scheduler.running,
    }


@app.post("/jobs/{job_id}/trigger")
async def trigger_job_endpoint(job_id: str) -> dict[str, Any]:
    """
    Manually trigger a scraping job.

    Valid job IDs:
    - rss_feeds: RSS feed scraping
    - web_scrape: Web scraping
    - all: Run all scrapers
    """
    job_map = {
        "rss_feeds": run_rss_scrape,
        "web_scrape": run_web_scrape,
        "all": run_all_scrapers,
    }

    if job_id not in job_map:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}. Valid jobs: {list(job_map.keys())}",
        )

    logger.info(f"Manually triggering job: {job_id}")

    try:
        result = await job_map[job_id]()
        return {
            "status": "completed",
            "job_id": job_id,
            "result": result,
        }
    except Exception as e:
        logger.error(f"Error running job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error running job: {str(e)}",
        )


@app.get("/sources")
async def list_sources() -> dict[str, Any]:
    """List all configured content sources."""
    sources = load_sources()

    return {
        "rss": [
            {
                "name": s.name,
                "url": s.url,
                "category": s.category,
                "enabled": s.enabled,
            }
            for s in sources.rss
        ],
        "web": [
            {
                "name": s.name,
                "url": s.url,
                "category": s.category,
                "enabled": s.enabled,
                "use_playwright": s.use_playwright,
            }
            for s in sources.web
        ],
        "totals": {
            "rss": len([s for s in sources.rss if s.enabled]),
            "web": len([s for s in sources.web if s.enabled]),
        },
    }


@app.get("/config")
async def get_config() -> dict[str, Any]:
    """Get current scraper configuration (non-sensitive)."""
    return {
        "intervals": {
            "rss_minutes": settings.scrape_interval_rss,
            "web_minutes": settings.scrape_interval_web,
        },
        "limits": {
            "max_items_per_source": settings.max_items_per_source,
            "rate_limit_delay": settings.default_rate_limit_delay,
        },
        "features": {
            "respect_robots_txt": settings.respect_robots_txt,
        },
    }


@app.get("/api/stats")
async def get_stats() -> dict[str, Any]:
    """Get scraper runs metrics, sources crawl breakdown, and recent articles."""
    stats = get_scraper_stats()
    
    # Cross-reference with YAML configurations to show all sources (including disabled / never run ones)
    try:
        sources_config = load_sources()
        db_sources = {s.get("url"): s for s in stats.get("sources", [])}
        
        combined_sources = []
        for r in sources_config.rss:
            status_info = db_sources.get(r.url, {})
            combined_sources.append({
                "name": r.name,
                "url": r.url,
                "type": "rss",
                "category": r.category,
                "enabled": r.enabled,
                "last_scraped_at": status_info.get("last_scraped_at"),
                "last_duration_seconds": status_info.get("last_duration_seconds"),
                "last_status": status_info.get("last_status", "never run"),
                "last_items_scraped": status_info.get("last_items_scraped", 0),
                "last_items_saved": status_info.get("last_items_saved", 0),
                "last_error": status_info.get("last_error", "")
            })
            
        for w in sources_config.web:
            status_info = db_sources.get(w.url, {})
            combined_sources.append({
                "name": w.name,
                "url": w.url,
                "type": "web",
                "category": w.category,
                "enabled": w.enabled,
                "last_scraped_at": status_info.get("last_scraped_at"),
                "last_duration_seconds": status_info.get("last_duration_seconds"),
                "last_status": status_info.get("last_status", "never run"),
                "last_items_scraped": status_info.get("last_items_scraped", 0),
                "last_items_saved": status_info.get("last_items_saved", 0),
                "last_error": status_info.get("last_error", "")
            })
            
        stats["sources"] = combined_sources
    except Exception as e:
        logger.error(f"Error merging sources details: {e}")
        
    return stats


@app.get("/api/articles/{article_id}")
async def get_article_json(article_id: str) -> dict[str, Any]:
    """Retrieve full database JSON document of an article by ID."""
    from bson import ObjectId
    from scraper.db import get_collection
    try:
        coll = get_collection("articles")
        # Try finding by string ID first, since article IDs are stored as strings
        doc = coll.find_one({"_id": article_id})
        if not doc and ObjectId.is_valid(article_id):
            # Fallback to ObjectId query if valid format
            doc = coll.find_one({"_id": ObjectId(article_id)})
            
        if not doc:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Serialize ObjectId and datetime objects recursively
        def serialize_doc(d):
            if isinstance(d, dict):
                return {k: serialize_doc(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [serialize_doc(x) for x in d]
            elif isinstance(d, datetime):
                return d.isoformat()
            elif isinstance(d, ObjectId):
                return str(d)
            return d

        return serialize_doc(doc)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=f"Error retrieving article: {str(e)}")


@app.get("/api/logs/stream")
async def stream_logs():
    """Stream application log messages in real-time to the dashboard via SSE."""
    async def log_generator():
        # Send a connection confirmation
        yield "data: [SYSTEM] Connected to live WAPOW scraper logs...\n\n"
        while True:
            lines = []
            while not log_queue.empty():
                try:
                    lines.append(log_queue.get_nowait())
                except Exception:
                    break
            if lines:
                data = "\n".join(lines)
                yield f"data: {data}\n\n"
            await asyncio.sleep(0.5)

    return StreamingResponse(log_generator(), media_type="text/event-stream")


@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard() -> HTMLResponse:
    """Operations dashboard for WAPOW Scraper styled like a premium, sleek Vercel UI using Tailwind CSS v4."""
    from pathlib import Path
    template_path = Path(__file__).resolve().parent / "templates" / "dashboard.html"
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dashboard template not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.port)
