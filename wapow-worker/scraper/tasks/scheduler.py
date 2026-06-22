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
        run_podcast_scrape,
    )

    # RSS feeds - every hour
    scheduler.add_job(
        run_rss_scrape,
        trigger=IntervalTrigger(minutes=settings.scrape_interval_rss),
        id="rss_feeds",
        name="RSS Feeds Scraper",
        replace_existing=True,
    )

    # Podcast feeds - every 6 hours (360 minutes)
    scheduler.add_job(
        run_podcast_scrape,
        trigger=IntervalTrigger(minutes=360),
        id="podcast_scrape",
        name="Podcast Index Scraper",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started with RSS feeds and Podcast Index scraping jobs")


def shutdown_scheduler() -> None:
    """Shutdown the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler shutdown complete")


def get_job_info() -> list[dict]:
    """Get information about all scheduled jobs."""
    from scraper.tasks.running import active_tasks
    jobs = []
    for job in scheduler.get_jobs():
        # A manual/one-off run job doesn't represent a main scraper task
        if job.id.endswith("_manual"):
            continue
        next_run = job.next_run_time
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": next_run.isoformat() if next_run else None,
            "trigger": str(job.trigger),
            "status": "paused" if next_run is None else "active",
            "running": job.id in active_tasks,
        })
    return jobs


def pause_job(job_id: str) -> bool:
    """Pause a scheduled scraping job."""
    job = scheduler.get_job(job_id)
    if job is None:
        return False
    scheduler.pause_job(job_id)
    return True


def resume_job(job_id: str) -> bool:
    """Resume a paused scheduled scraping job."""
    job = scheduler.get_job(job_id)
    if job is None:
        return False
    scheduler.resume_job(job_id)
    return True


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
