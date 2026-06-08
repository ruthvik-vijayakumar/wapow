"""FastAPI management API for WAPOW Scraper."""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from scraper.config import settings
from scraper.db.mongodb import close_client
from scraper.tasks.scheduler import (
    scheduler,
    start_scheduler,
    shutdown_scheduler,
    get_job_info,
    trigger_job,
)
from scraper.tasks.jobs import (
    load_sources,
    run_rss_scrape,
    run_web_scrape,
    run_youtube_scrape,
    run_spotify_scrape,
    run_all_scrapers,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting WAPOW Scraper service")
    start_scheduler()
    yield
    # Shutdown
    logger.info("Shutting down WAPOW Scraper service")
    shutdown_scheduler()
    close_client()


app = FastAPI(
    title="WAPOW Scraper",
    description="Content scraping and aggregation service for WAPOW",
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
        "service": "wapow-scraper",
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
    - youtube: YouTube video scraping
    - spotify: Spotify podcast scraping
    - all: Run all scrapers
    """
    # Map job IDs to functions for manual triggering
    job_map = {
        "rss_feeds": run_rss_scrape,
        "web_scrape": run_web_scrape,
        "youtube": run_youtube_scrape,
        "spotify": run_spotify_scrape,
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
        "youtube": [
            {
                "name": s.name,
                "channel_id": s.channel_id,
                "playlist_id": s.playlist_id,
                "category": s.category,
                "enabled": s.enabled,
            }
            for s in sources.youtube
        ],
        "spotify": [
            {
                "name": s.name,
                "show_id": s.show_id,
                "enabled": s.enabled,
            }
            for s in sources.spotify
        ],
        "totals": {
            "rss": len([s for s in sources.rss if s.enabled]),
            "web": len([s for s in sources.web if s.enabled]),
            "youtube": len([s for s in sources.youtube if s.enabled]),
            "spotify": len([s for s in sources.spotify if s.enabled]),
        },
    }


@app.get("/config")
async def get_config() -> dict[str, Any]:
    """Get current scraper configuration (non-sensitive)."""
    return {
        "intervals": {
            "rss_minutes": settings.scrape_interval_rss,
            "web_minutes": settings.scrape_interval_web,
            "youtube_minutes": settings.scrape_interval_youtube,
            "spotify_minutes": settings.scrape_interval_spotify,
        },
        "limits": {
            "max_items_per_source": settings.max_items_per_source,
            "rate_limit_delay": settings.default_rate_limit_delay,
        },
        "features": {
            "respect_robots_txt": settings.respect_robots_txt,
            "youtube_enabled": bool(settings.youtube_api_key),
            "spotify_enabled": bool(
                settings.spotify_client_id and settings.spotify_client_secret
            ),
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.port)
