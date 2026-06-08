"""Task scheduling modules."""

from scraper.tasks.scheduler import scheduler, start_scheduler, shutdown_scheduler
from scraper.tasks.jobs import (
    run_rss_scrape,
    run_web_scrape,
    run_youtube_scrape,
    run_spotify_scrape,
    run_all_scrapers,
)

__all__ = [
    "scheduler",
    "start_scheduler",
    "shutdown_scheduler",
    "run_rss_scrape",
    "run_web_scrape",
    "run_youtube_scrape",
    "run_spotify_scrape",
    "run_all_scrapers",
]
