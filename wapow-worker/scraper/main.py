"""FastAPI management API and Operations Dashboard for WAPOW Scraper."""

import logging
import queue
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os

from scraper.config import settings
from scraper.db.mongodb import close_client
from scraper.tasks.scheduler import (
    scheduler,
    start_scheduler,
    shutdown_scheduler,
    get_job_info,
    pause_job,
    resume_job,
)
from scraper.tasks.jobs import (
    load_sources,
    save_sources,
    run_rss_scrape,
    run_all_scrapers,
)
from scraper.services.conversion_jobs import (
    is_worker_paused,
    pause_worker,
    resume_worker,
)
from scraper.models.source import RSSSource, WebSource
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

# Mount static files for Vue frontend dashboard assets
dist_assets_dir = os.path.join(os.path.dirname(__file__), "dist", "assets")
os.makedirs(dist_assets_dir, exist_ok=True)
app.mount("/assets", StaticFiles(directory=dist_assets_dir), name="assets")


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
        "worker_paused": is_worker_paused(),
    }


@app.post("/jobs/{job_id}/pause")
async def pause_job_endpoint(job_id: str) -> dict[str, Any]:
    """Pause a scheduled scraping job."""
    if pause_job(job_id):
        return {"success": True, "message": f"Job {job_id} paused successfully"}
    raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")


@app.post("/jobs/{job_id}/resume")
async def resume_job_endpoint(job_id: str) -> dict[str, Any]:
    """Resume a paused scheduled scraping job."""
    if resume_job(job_id):
        return {"success": True, "message": f"Job {job_id} resumed successfully"}
    raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")


@app.get("/worker/status")
async def worker_status_endpoint() -> dict[str, Any]:
    """Retrieve background conversion worker pause status."""
    return {
        "paused": is_worker_paused(),
        "running": not is_worker_paused()
    }


@app.post("/worker/pause")
async def pause_worker_endpoint() -> dict[str, Any]:
    """Pause the background slide conversion worker."""
    pause_worker()
    return {"success": True, "message": "Background conversion worker paused successfully"}


@app.post("/worker/resume")
async def resume_worker_endpoint() -> dict[str, Any]:
    """Resume the background slide conversion worker."""
    resume_worker()
    return {"success": True, "message": "Background conversion worker resumed successfully"}


@app.post("/jobs/{job_id}/trigger")
async def trigger_job_endpoint(job_id: str) -> dict[str, Any]:
    """
    Manually trigger a scraping job.

    Valid job IDs:
    - rss_feeds: RSS feed scraping
    - all: Run active scrapers (RSS only)
    """
    job_map = {
        "rss_feeds": run_rss_scrape,
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


@app.post("/jobs/{job_id}/stop")
async def stop_job_endpoint(job_id: str) -> dict[str, Any]:
    """Stop a running scraping job."""
    from scraper.tasks.running import active_tasks
    task = active_tasks.get(job_id)
    if not task:
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} is not currently running.",
        )
    task.cancel()
    logger.info(f"Cancellation signal sent to running job task: {job_id}")
    return {"success": True, "message": f"Stop request sent to job {job_id}."}


@app.get("/sources")
async def list_sources() -> dict[str, Any]:
    """List all configured content sources (RSS only)."""
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
        "web": [],
        "totals": {
            "rss": len([s for s in sources.rss if s.enabled]),
            "web": 0,
        },
    }


from pydantic import BaseModel
from typing import Optional

class SourceInput(BaseModel):
    type: str  # "rss" or "web"
    name: str
    url: str
    category: str
    enabled: bool = True
    use_playwright: bool = False
    selectors: dict[str, str] = {
        "articles": "article",
        "title": "h1, h2, .title",
        "description": "p, .description, .excerpt",
        "image": "img",
        "link": "a",
        "author": ".author, .byline",
        "date": "time, .date, .published",
    }


class SourceEditInput(BaseModel):
    type: str  # "rss" or "web"
    old_name: str
    name: str
    url: str
    category: str
    enabled: bool = True
    use_playwright: bool = False
    selectors: Optional[dict[str, str]] = None


class SourceToggleInput(BaseModel):
    type: str  # "rss" or "web"
    name: str


class SourceDeleteInput(BaseModel):
    type: str  # "rss" or "web"
    name: str


@app.post("/api/sources/add")
async def add_source_endpoint(input_data: SourceInput) -> dict[str, Any]:
    """Add a new RSS source to sources.yaml."""
    if input_data.type != "rss":
        raise HTTPException(status_code=400, detail="Only RSS sources are supported.")
        
    config = load_sources()
    
    # Check for duplicate name
    all_names = [s.name for s in config.rss + config.web]
    if input_data.name in all_names:
        raise HTTPException(status_code=400, detail=f"Source with name '{input_data.name}' already exists.")
        
    new_src = RSSSource(
        name=input_data.name,
        url=input_data.url,
        category=input_data.category,
        enabled=input_data.enabled
    )
    config.rss.append(new_src)
    save_sources(config)
    return {"success": True, "message": f"Successfully added source '{input_data.name}'"}


@app.post("/api/sources/edit")
async def edit_source_endpoint(input_data: SourceEditInput) -> dict[str, Any]:
    """Edit properties of an existing source in sources.yaml."""
    if input_data.type != "rss":
        raise HTTPException(status_code=400, detail="Only RSS sources are supported.")
        
    config = load_sources()
    
    # Find and update
    found = False
    for i, s in enumerate(config.rss):
        if s.name == input_data.old_name:
            config.rss[i] = RSSSource(
                name=input_data.name,
                url=input_data.url,
                category=input_data.category,
                enabled=input_data.enabled
            )
            found = True
            break
                
    if not found:
        raise HTTPException(status_code=404, detail=f"Source '{input_data.old_name}' not found.")
        
    save_sources(config)
    return {"success": True, "message": f"Successfully updated source '{input_data.name}'"}


@app.post("/api/sources/toggle")
async def toggle_source_endpoint(input_data: SourceToggleInput) -> dict[str, Any]:
    """Toggle enabled status of a source in sources.yaml."""
    if input_data.type != "rss":
        raise HTTPException(status_code=400, detail="Only RSS sources are supported.")
        
    config = load_sources()
    
    found = False
    new_state = False
    for s in config.rss:
        if s.name == input_data.name:
            s.enabled = not s.enabled
            new_state = s.enabled
            found = True
            break
                
    if not found:
        raise HTTPException(status_code=404, detail=f"Source '{input_data.name}' not found.")
        
    save_sources(config)
    state_str = "enabled" if new_state else "disabled"
    return {"success": True, "message": f"Source '{input_data.name}' is now {state_str}"}


@app.post("/api/sources/delete")
async def delete_source_endpoint(input_data: SourceDeleteInput) -> dict[str, Any]:
    """Delete a source from sources.yaml."""
    if input_data.type != "rss":
        raise HTTPException(status_code=400, detail="Only RSS sources are supported.")
        
    config = load_sources()
    
    found = False
    for s in config.rss:
        if s.name == input_data.name:
            config.rss.remove(s)
            found = True
            break
                
    if not found:
        raise HTTPException(status_code=404, detail=f"Source '{input_data.name}' not found.")
        
    save_sources(config)
    return {"success": True, "message": f"Successfully deleted source '{input_data.name}'"}


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
            
        stats["sources"] = combined_sources
    except Exception as e:
        logger.error(f"Error merging sources details: {e}")
        
    return stats


@app.get("/api/runs")
async def get_runs_endpoint(page: int = 1, limit: int = 10) -> dict[str, Any]:
    """Retrieve paginated scraper runs."""
    from scraper.db import get_collection
    import math
    try:
        coll_runs = get_collection("scraper_runs")
        total = coll_runs.count_documents({})
        skip = (page - 1) * limit
        raw_runs = list(coll_runs.find().sort("start_time", -1).skip(skip).limit(limit))
        runs = []
        for run in raw_runs:
            run["_id"] = str(run["_id"])
            if "start_time" in run and isinstance(run["start_time"], datetime):
                run["start_time"] = run["start_time"].isoformat()
            if "end_time" in run and isinstance(run["end_time"], datetime):
                run["end_time"] = run["end_time"].isoformat()
            # Omit saved_articles as requested: "saved articles and error logs should have just the error logs if any"
            if "saved_articles" in run:
                run.pop("saved_articles", None)
            runs.append(run)
            
        total_pages = math.ceil(total / limit) if limit > 0 else 0
        return {
            "runs": runs,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }
    except Exception as e:
        logger.error(f"Error fetching runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/articles")
async def get_articles_endpoint(page: int = 1, limit: int = 10) -> dict[str, Any]:
    """Retrieve paginated ingested articles."""
    from scraper.db import get_collection
    import math
    try:
        coll_articles = get_collection("articles")
        total = coll_articles.count_documents({})
        skip = (page - 1) * limit
        raw_articles = list(coll_articles.find().sort("created_date", -1).skip(skip).limit(limit))
        articles = []
        for art in raw_articles:
            articles.append({
                "id": str(art["_id"]),
                "title": art.get("headlines", {}).get("basic", "Untitled"),
                "category": art.get("category", "unknown"),
                "publisher": art.get("publisher") or art.get("_scraper_meta", {}).get("publisher") or "unknown",
                "url": art.get("canonical_url", ""),
                "created_date": art.get("created_date", datetime.utcnow()).isoformat() if isinstance(art.get("created_date"), datetime) else str(art.get("created_date")),
            })
            
        total_pages = math.ceil(total / limit) if limit > 0 else 0
        return {
            "articles": articles,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }
    except Exception as e:
        logger.error(f"Error fetching articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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


@app.get("/dashboard")
async def get_dashboard():
    """Operations dashboard for WAPOW Scraper. Serves the Vue SPA if built, falling back to legacy template."""
    from pathlib import Path
    dist_index = Path(__file__).resolve().parent / "dist" / "index.html"
    if dist_index.exists():
        return FileResponse(dist_index)
        
    # Fallback to legacy single-file dashboard
    template_path = Path(__file__).resolve().parent / "templates" / "dashboard.html"
    try:
        return FileResponse(template_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dashboard template not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.port)
