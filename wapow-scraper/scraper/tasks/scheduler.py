"""APScheduler setup for periodic scraping jobs."""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from scraper.config import settings

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    """Start the scheduler with configured jobs."""
    from scraper.tasks.jobs import (
        run_rss_scrape,
        run_web_scrape,
        run_youtube_scrape,
        run_spotify_scrape,
    )

    # RSS feeds - every hour
    scheduler.add_job(
        run_rss_scrape,
        trigger=IntervalTrigger(minutes=settings.scrape_interval_rss),
        id="rss_feeds",
        name="RSS Feeds Scraper",
        replace_existing=True,
    )

    # Web scraping - every 2 hours
    scheduler.add_job(
        run_web_scrape,
        trigger=IntervalTrigger(minutes=settings.scrape_interval_web),
        id="web_scrape",
        name="Web Scraper",
        replace_existing=True,
    )

    # YouTube - every 6 hours
    scheduler.add_job(
        run_youtube_scrape,
        trigger=IntervalTrigger(minutes=settings.scrape_interval_youtube),
        id="youtube",
        name="YouTube Scraper",
        replace_existing=True,
    )

    # Spotify podcasts - every 12 hours
    scheduler.add_job(
        run_spotify_scrape,
        trigger=IntervalTrigger(minutes=settings.scrape_interval_spotify),
        id="spotify",
        name="Spotify Podcast Scraper",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started with all jobs")


def shutdown_scheduler() -> None:
    """Shutdown the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler shutdown complete")


def get_job_info() -> list[dict]:
    """Get information about all scheduled jobs."""
    jobs = []
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": next_run.isoformat() if next_run else None,
            "trigger": str(job.trigger),
        })
    return jobs


def trigger_job(job_id: str) -> bool:
    """
    Manually trigger a job to run immediately.

    Args:
        job_id: The job ID to trigger

    Returns:
        True if job was triggered, False if not found
    """
    job = scheduler.get_job(job_id)
    if job is None:
        return False

    # Run the job function immediately
    scheduler.add_job(
        job.func,
        id=f"{job_id}_manual",
        replace_existing=True,
    )
    return True
