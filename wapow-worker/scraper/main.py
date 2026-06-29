"""FastAPI management API and Operations Dashboard for WAPOW Scraper."""

import logging
import asyncio
import hmac
import uuid
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
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
    run_rss_scrape_task,
    run_web_scrape,
    run_web_scrape_task,
    run_all_scrapers,
    run_all_scrapers_task,
)
from scraper.services.conversion_jobs import (
    create_batch_conversion_jobs,
    create_conversion_job,
    get_job,
    is_worker_paused,
    pause_worker,
    retry_job,
    resume_worker,
    serialize_job,
)
from scraper.models.source import RSSSource, WebSource
from scraper.utils.metrics import get_scraper_stats
from scraper.utils.metrics import finish_run_by_id, reconcile_stale_runs
from scraper.utils.dashboard_logging import (
    configure_dashboard_logging,
    ensure_log_indexes,
    get_logs_after,
    get_recent_logs,
    serialize_log_doc,
)
from scraper.tasks.running import active_tasks


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
configure_dashboard_logging()

RSS_TASK_NAME = "tasks.run_rss_scrape"
WEB_TASK_NAME = "tasks.run_web_scrape"
ALL_TASK_NAME = "tasks.run_all_scrapers"
RSS_QUEUE_NAME = "rss"

SCRAPE_JOB_NAMES = {"rss_feeds", "web_scrape", "all"}


class ConversionJobInput(BaseModel):
    article_id: str
    force: bool = False


class BatchConversionJobInput(BaseModel):
    ids: list[str]
    force: bool = False


class PurgeQueueInput(BaseModel):
    queue: str = RSS_QUEUE_NAME


def require_internal_token(x_internal_token: str | None = Header(default=None)) -> None:
    """Protect worker admin controls when WORKER_INTERNAL_TOKEN is configured."""
    expected = settings.worker_internal_token
    if expected and not hmac.compare_digest(x_internal_token or "", expected):
        raise HTTPException(status_code=401, detail="Invalid internal token")


def _collect_celery_task_ids(task_name: str) -> set[str]:
    from scraper.celery_client import celery_app

    task_ids: set[str] = set()
    inspector = celery_app.control.inspect(timeout=1.0)
    for task_map in (inspector.active() or {}, inspector.reserved() or {}):
        for tasks in task_map.values():
            for task in tasks:
                if task.get("name") == task_name and task.get("id"):
                    task_ids.add(task["id"])

    scheduled = inspector.scheduled() or {}
    for tasks in scheduled.values():
        for entry in tasks:
            request = entry.get("request") or {}
            if request.get("name") == task_name and request.get("id"):
                task_ids.add(request["id"])
    return task_ids


def _purge_celery_queue(queue_name: str) -> int:
    from scraper.celery_client import celery_app

    with celery_app.connection_for_write() as connection:
        channel = connection.default_channel
        return int(channel.queue_purge(queue_name) or 0)


def _start_local_scrape_task(job_id: str) -> str:
    """Start a manual scrape in the API process so dashboard triggers execute without Celery."""
    if job_id in active_tasks and not active_tasks[job_id].done():
        raise HTTPException(status_code=409, detail="Scrape is already running.")

    task_id = f"local-{uuid.uuid4()}"

    async def runner() -> None:
        try:
            if job_id == "rss_feeds":
                await run_rss_scrape(task_id=task_id)
            elif job_id == "web_scrape":
                await run_web_scrape(task_id=task_id)
            elif job_id == "all":
                await run_all_scrapers()
            else:
                raise ValueError(f"Unsupported scrape job: {job_id}")
        finally:
            active_tasks.pop(job_id, None)

    task = asyncio.create_task(runner(), name=f"{job_id}:{task_id}")
    active_tasks[job_id] = task
    return task_id

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting WAPOW Scraper service")
    start_scheduler()
    
    from scraper.services.conversion_jobs import ensure_conversion_jobs_indexes
    ensure_conversion_jobs_indexes()
    ensure_log_indexes()
    
    yield
    logger.info("Shutting down WAPOW Scraper service")
    shutdown_scheduler()
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
    try:
        reconcile_stale_runs()
    except Exception as e:
        logger.warning(f"Unable to reconcile stale runs for jobs dashboard: {e}")
    jobs = get_job_info()
    from scraper.db import get_collection
    try:
        active_runs = {
            run.get("job_id"): {
                "run_id": str(run.get("_id")),
                "task_id": run.get("task_id"),
                "start_time": run.get("start_time").isoformat() if isinstance(run.get("start_time"), datetime) else run.get("start_time"),
            }
            for run in get_collection("scraper_runs").find({"status": "running"})
        }
    except Exception as e:
        logger.warning(f"Unable to load active scrape runs for jobs dashboard: {e}")
        active_runs = {}

    for local_job_id, task in list(active_tasks.items()):
        if task.done():
            active_tasks.pop(local_job_id, None)
            continue
        task_name = task.get_name()
        _, _, local_task_id = task_name.partition(":")
        active_runs[local_job_id] = {
            "run_id": local_task_id or local_job_id,
            "task_id": local_task_id or local_job_id,
            "start_time": None,
        }

    if not any(job["id"] == "web_scrape" for job in jobs):
        jobs.append({
            "id": "web_scrape",
            "name": "Web Page Scraper",
            "next_run": None,
            "next_run_time": None,
            "trigger": "manual",
            "status": "active",
            "manual": True,
        })

    for job in jobs:
        active_run = active_runs.get(job["id"])
        job["running"] = active_run is not None
        job["active_run"] = active_run
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


@app.post("/jobs/{job_id}/stop")
async def stop_job_endpoint(job_id: str) -> dict[str, Any]:
    """Stop an actively running scraping job."""
    if job_id not in {"rss_feeds", "web_scrape", "all"}:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    from scraper.celery_client import celery_app, forget_task_result
    from scraper.db import get_collection

    query_job_ids = ["rss_feeds", "web_scrape"] if job_id == "all" else [job_id]
    local_job_ids = ["rss_feeds", "web_scrape", "all"] if job_id == "all" else [job_id]
    stopped_local_tasks = []
    for local_job_id in local_job_ids:
        local_task = active_tasks.pop(local_job_id, None)
        if local_task and not local_task.done():
            local_task.cancel()
            stopped_local_tasks.append(local_job_id)

    try:
        runs = list(
            get_collection("scraper_runs").find(
                {"job_id": {"$in": query_job_ids}, "status": "running"},
                sort=[("start_time", -1)],
            )
        )
    except Exception as e:
        logger.warning(f"Unable to load active scrape runs while stopping {job_id}: {e}")
        runs = []

    task_names = {
        "rss_feeds": [RSS_TASK_NAME],
        "web_scrape": [WEB_TASK_NAME],
        "all": [RSS_TASK_NAME, WEB_TASK_NAME, ALL_TASK_NAME],
    }[job_id]
    task_ids = set()
    for task_name in task_names:
        try:
            task_ids.update(_collect_celery_task_ids(task_name))
        except Exception as e:
            logger.warning(f"Unable to inspect Celery tasks while stopping {job_id}: {e}")
    task_ids.update(str(run["task_id"]) for run in runs if run.get("task_id"))

    for task_id in task_ids:
        try:
            celery_app.control.revoke(task_id, terminate=True, signal="SIGTERM")
            forget_task_result(task_id)
        except Exception as e:
            logger.warning(f"Unable to revoke Celery task {task_id}: {e}")

    try:
        purged_messages = _purge_celery_queue(RSS_QUEUE_NAME)
    except Exception as e:
        logger.warning(f"Unable to purge Celery queue while stopping {job_id}: {e}")
        purged_messages = 0

    stopped_runs = []
    for run in runs:
        try:
            finish_run_by_id(run["_id"], "cancelled", "Run stopped from worker dashboard.")
            stopped_runs.append(str(run["_id"]))
        except Exception as e:
            logger.warning(f"Unable to mark run {run.get('_id')} cancelled: {e}")

    stopped = bool(task_ids or purged_messages or stopped_runs or stopped_local_tasks)
    if not stopped:
        return {"success": True, "stopped": False, "message": "No active or queued scrape was found."}

    logger.warning(
        f"Stopped scrape job={job_id} runs={stopped_runs} tasks={sorted(task_ids)} local={stopped_local_tasks} purged={purged_messages}"
    )
    return {
        "success": True,
        "stopped": True,
        "run_ids": stopped_runs,
        "task_ids": sorted(task_ids),
        "local_task_ids": stopped_local_tasks,
        "purged_messages": purged_messages,
    }


@app.get("/worker/status")
async def worker_status_endpoint(_: None = Depends(require_internal_token)) -> dict[str, Any]:
    """Retrieve background conversion worker pause status."""
    return {
        "paused": is_worker_paused(),
        "running": not is_worker_paused()
    }


@app.post("/worker/pause")
async def pause_worker_endpoint(_: None = Depends(require_internal_token)) -> dict[str, Any]:
    """Pause the background slide conversion worker."""
    pause_worker()
    return {"success": True, "message": "Background conversion worker paused successfully"}


@app.post("/worker/resume")
async def resume_worker_endpoint(_: None = Depends(require_internal_token)) -> dict[str, Any]:
    """Resume the background slide conversion worker."""
    resume_worker()
    return {"success": True, "message": "Background conversion worker resumed successfully"}


@app.get("/worker/celery/status")
async def celery_worker_status_endpoint() -> dict[str, Any]:
    """Check the status of the Celery workers."""
    try:
        from scraper.celery_client import celery_app
        inspector = celery_app.control.inspect(timeout=1.0)
        
        pings = inspector.ping()
        active = inspector.active()
        reserved = inspector.reserved()
        scheduled = inspector.scheduled()
        
        workers = []
        if pings:
            for w_name in pings.keys():
                active_tasks = active.get(w_name, []) if active else []
                reserved_tasks = reserved.get(w_name, []) if reserved else []
                scheduled_tasks = scheduled.get(w_name, []) if scheduled else []
                
                workers.append({
                    "name": w_name,
                    "status": "online",
                    "active_tasks_count": len(active_tasks),
                    "reserved_tasks_count": len(reserved_tasks),
                    "scheduled_tasks_count": len(scheduled_tasks),
                    "active_tasks": active_tasks,
                    "reserved_tasks": reserved_tasks,
                    "scheduled_tasks": scheduled_tasks,
                })
        
        return {
            "status": "online" if workers else "offline",
            "workers": workers,
            "count": len(workers)
        }
    except Exception as e:
        logger.error(f"Error checking Celery worker status: {e}")
        return {
            "status": "error",
            "message": str(e),
            "workers": [],
            "count": 0
        }


@app.post("/worker/celery/purge")
async def purge_celery_queue_endpoint(
    input_data: PurgeQueueInput,
    _: None = Depends(require_internal_token),
) -> dict[str, Any]:
    """Purge pending messages from a named Celery queue."""
    allowed_queues = {"rss", "conversion", "celery"}
    if input_data.queue not in allowed_queues:
        raise HTTPException(status_code=400, detail=f"Queue must be one of: {sorted(allowed_queues)}")
    purged_messages = _purge_celery_queue(input_data.queue)
    logger.warning(f"Purged Celery queue={input_data.queue} messages={purged_messages}")
    return {"success": True, "queue": input_data.queue, "purged_messages": purged_messages}


@app.post("/worker/conversion-jobs")
async def create_conversion_job_endpoint(
    input_data: ConversionJobInput,
    _: None = Depends(require_internal_token),
) -> dict[str, Any]:
    """Create and enqueue a slide conversion job for an existing article."""
    try:
        job = create_conversion_job(input_data.article_id, force=input_data.force)
        return {"success": True, "data": serialize_job(job)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error creating conversion job: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/worker/conversion-jobs/batch")
async def create_batch_conversion_jobs_endpoint(
    input_data: BatchConversionJobInput,
    _: None = Depends(require_internal_token),
) -> dict[str, Any]:
    """Create and enqueue slide conversion jobs for existing articles."""
    if len(input_data.ids) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 article IDs per batch")
    if not input_data.ids:
        raise HTTPException(status_code=400, detail="ids must not be empty")
    try:
        jobs = create_batch_conversion_jobs(input_data.ids, force=input_data.force)
        return {"success": True, "data": [serialize_job(job) for job in jobs]}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error creating batch conversion jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/worker/conversion-jobs/{job_id}")
async def get_conversion_job_endpoint(
    job_id: str,
    _: None = Depends(require_internal_token),
) -> dict[str, Any]:
    """Check the status of a worker-owned slide conversion job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"success": True, "data": serialize_job(job)}


@app.post("/worker/conversion-jobs/{job_id}/retry")
async def retry_conversion_job_endpoint(
    job_id: str,
    _: None = Depends(require_internal_token),
) -> dict[str, Any]:
    """Retry a failed slide conversion job."""
    try:
        job = retry_job(job_id)
        return {"success": True, "data": serialize_job(job)}
    except ValueError as e:
        detail = str(e)
        status_code = 404 if detail == "Job not found" else 400
        raise HTTPException(status_code=status_code, detail=detail) from e
    except Exception as e:
        logger.error(f"Error retrying conversion job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/jobs/{job_id}/trigger")
async def trigger_job_endpoint(job_id: str) -> dict[str, Any]:
    """
    Manually trigger a scraping job.

    Valid job IDs:
    - rss_feeds: RSS feed scraping
    - web_scrape: Web page scraping
    - all: Run all configured sources
    """
    job_map = {
        "rss_feeds": run_rss_scrape_task,
        "web_scrape": run_web_scrape_task,
        "all": run_all_scrapers_task,
    }

    if job_id not in job_map:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}. Valid jobs: {list(job_map.keys())}",
        )

    logger.info(f"Manually triggering job: {job_id}")

    try:
        if job_id in SCRAPE_JOB_NAMES:
            task_id = _start_local_scrape_task(job_id)
            return {
                "status": "running",
                "job_id": job_id,
                "task_id": task_id,
                "message": "Scraper job is running in the worker API process."
            }

        task = job_map[job_id].delay()
        return {
            "status": "queued",
            "job_id": job_id,
            "task_id": task.id,
            "message": "Scraper job is running in the background."
        }
    except HTTPException:
        raise
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


class SourceInput(BaseModel):
    type: str  # "rss" or "web"
    name: str
    url: str
    category: str
    enabled: bool = True
    use_playwright: bool = True


class SourceEditInput(BaseModel):
    type: str  # "rss" or "web"
    old_name: str
    name: str
    url: str
    category: str
    enabled: bool = True
    use_playwright: bool = True


class SourceToggleInput(BaseModel):
    type: str  # "rss" or "web"
    name: str


class SourceDeleteInput(BaseModel):
    type: str  # "rss" or "web"
    name: str


@app.post("/api/sources/add")
async def add_source_endpoint(input_data: SourceInput) -> dict[str, Any]:
    """Add a new RSS source to sources.yaml."""
    config = load_sources()
    
    # Check for duplicate name
    all_names = [s.name for s in config.rss] + [s.name for s in config.web]
    if input_data.name in all_names:
        raise HTTPException(status_code=400, detail=f"Source with name '{input_data.name}' already exists.")
        
    if input_data.type == "rss":
        new_src = RSSSource(
            name=input_data.name,
            url=input_data.url,
            category=input_data.category,
            enabled=input_data.enabled
        )
        config.rss.append(new_src)
    elif input_data.type == "web":
        new_src = WebSource(
            name=input_data.name,
            url=input_data.url,
            category=input_data.category,
            enabled=input_data.enabled,
            use_playwright=input_data.use_playwright,
        )
        config.web.append(new_src)
    else:
        raise HTTPException(status_code=400, detail="Invalid source type. Must be 'rss' or 'web'.")
        
    save_sources(config)
    return {"success": True, "message": f"Successfully added source '{input_data.name}'"}


@app.post("/api/sources/edit")
async def edit_source_endpoint(input_data: SourceEditInput) -> dict[str, Any]:
    """Edit properties of an existing source in sources.yaml."""
    config = load_sources()
    
    # Find and update
    found = False
    if input_data.type == "rss":
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
    elif input_data.type == "web":
        for i, s in enumerate(config.web):
            if s.name == input_data.old_name:
                config.web[i] = WebSource(
                    name=input_data.name,
                    url=input_data.url,
                    category=input_data.category,
                    enabled=input_data.enabled,
                    use_playwright=input_data.use_playwright,
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
    config = load_sources()
    
    found = False
    new_state = False
    if input_data.type == "rss":
        for s in config.rss:
            if s.name == input_data.name:
                s.enabled = not s.enabled
                new_state = s.enabled
                found = True
                break
    elif input_data.type == "web":
        for s in config.web:
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
    config = load_sources()
    
    found = False
    if input_data.type == "rss":
        for s in config.rss:
            if s.name == input_data.name:
                config.rss.remove(s)
                found = True
                break
    elif input_data.type == "web":
        for s in config.web:
            if s.name == input_data.name:
                config.web.remove(s)
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
    reconcile_stale_runs()
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
                "use_playwright": w.use_playwright,
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
async def get_runs(page: int = 1, limit: int = 10) -> dict[str, Any]:
    """Get paginated list of scraper runs."""
    from datetime import datetime
    from scraper.db import get_collection
    try:
        reconcile_stale_runs()
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
            runs.append(run)
            
        total_pages = max(1, (total + limit - 1) // limit)
        return {
            "runs": runs,
            "page": page,
            "total": total,
            "total_pages": total_pages
        }
    except Exception as e:
        logger.error(f"Error fetching runs: {e}")
        return {
            "runs": [],
            "page": page,
            "total": 0,
            "total_pages": 1
        }


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
    """Stream worker/API log messages in real-time to the dashboard via SSE."""
    async def log_generator():
        yield "data: [SYSTEM] Connected to live WAPOW scraper logs...\n\n"
        last_seen = None
        try:
            recent_logs = get_recent_logs(limit=100)
            if recent_logs:
                last_seen = recent_logs[-1].get("_id")
                yield "data: " + "\n".join(serialize_log_doc(doc) for doc in recent_logs) + "\n\n"
        except Exception as e:
            logger.error(f"Error loading recent worker logs: {e}")

        while True:
            try:
                docs = get_logs_after(last_seen, limit=200)
                if docs:
                    last_seen = docs[-1].get("_id")
                    data = "\n".join(serialize_log_doc(doc) for doc in docs)
                    yield f"data: {data}\n\n"
            except Exception as e:
                logger.error(f"Error streaming worker logs: {e}")
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
