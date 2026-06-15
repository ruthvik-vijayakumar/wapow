"""Observability and runs tracking metrics module for WAPOW Scraper."""

import logging
import time
from datetime import datetime
from typing import Any
from scraper.db import get_collection

logger = logging.getLogger(__name__)


class ScraperRunTracker:
    """Tracks a single scraping job execution and updates metrics in MongoDB."""

    def __init__(self, job_id: str):
        self.job_id = job_id
        self.start_time = None
        self.end_time = None
        self.items_scraped = 0
        self.items_saved = 0
        self.saved_articles = []  # list of {"id": str, "title": str}
        self.errors = []
        self.run_id = None

    def start(self):
        """Register the start of a scraper run."""
        self.start_time = datetime.utcnow()
        try:
            coll = get_collection("scraper_runs")
            result = coll.insert_one({
                "job_id": self.job_id,
                "start_time": self.start_time,
                "status": "running",
                "items_scraped": 0,
                "items_saved": 0,
                "saved_articles": [],
                "errors": []
            })
            self.run_id = result.inserted_id
        except Exception as e:
            logger.error(f"Error registering run start in DB: {e}")

    def add_saved_article(self, article_id: str, title: str):
        """Record a successfully saved article."""
        self.saved_articles.append({"id": str(article_id), "title": title})
        self.items_saved += 1

    def add_error(self, error_msg: str):
        """Record an error message."""
        self.errors.append(error_msg)

    def finish(self, status: str = "success"):
        """Record the end of a scraper run."""
        self.end_time = datetime.utcnow()
        duration = (self.end_time - self.start_time).total_seconds() if self.start_time else 0.0
        try:
            if self.run_id:
                coll = get_collection("scraper_runs")
                coll.update_one(
                    {"_id": self.run_id},
                    {
                        "$set": {
                            "end_time": self.end_time,
                            "duration_seconds": duration,
                            "status": status,
                            "items_scraped": self.items_scraped,
                            "items_saved": self.items_saved,
                            "saved_articles": self.saved_articles,
                            "errors": self.errors
                        }
                    }
                )
        except Exception as e:
            logger.error(f"Error updating run finish in DB: {e}")


def update_source_status(
    source_name: str,
    source_type: str,
    url: str,
    category: str,
    enabled: bool,
    status: str,
    items_scraped: int,
    items_saved: int,
    duration: float,
    error_msg: str = ""
):
    """Update crawl statistics for a single content source in MongoDB."""
    try:
        coll = get_collection("sources_status")
        coll.update_one(
            {"url": url},
            {
                "$set": {
                    "name": source_name,
                    "type": source_type,
                    "category": category,
                    "enabled": enabled,
                    "last_scraped_at": datetime.utcnow(),
                    "last_duration_seconds": duration,
                    "last_status": status,
                    "last_items_scraped": items_scraped,
                    "last_items_saved": items_saved,
                    "last_error": error_msg
                }
            },
            upsert=True
        )
    except Exception as e:
        logger.error(f"Error updating source status: {e}")


def get_scraper_stats(limit: int = 20) -> dict[str, Any]:
    """Retrieve run statistics, source breakdown, and article list for the dashboard."""
    try:
        coll_runs = get_collection("scraper_runs")
        coll_articles = get_collection("articles")
    except Exception as e:
        logger.error(f"Error accessing database collections: {e}")
        return {
            "total_articles": 0,
            "summary": {"total_scraped": 0, "total_saved": 0, "success_rate_percent": 0.0, "total_runs": 0},
            "recent_runs": [],
            "recent_articles": [],
            "sources": []
        }

    # Get total count of articles
    try:
        total_articles = coll_articles.count_documents({})
    except Exception:
        total_articles = 0

    # Recent runs
    recent_runs = []
    try:
        raw_runs = list(coll_runs.find().sort("start_time", -1).limit(limit))
        for run in raw_runs:
            run["_id"] = str(run["_id"])
            if "start_time" in run and isinstance(run["start_time"], datetime):
                run["start_time"] = run["start_time"].isoformat()
            if "end_time" in run and isinstance(run["end_time"], datetime):
                run["end_time"] = run["end_time"].isoformat()
            recent_runs.append(run)
    except Exception as e:
        logger.error(f"Error fetching recent runs: {e}")

    # Aggregate stats over the last 100 runs
    summary_stats = {
        "total_scraped": 0,
        "total_saved": 0,
        "success_rate_percent": 100.0,
        "total_runs": 0
    }
    try:
        pipeline = [
            {"$sort": {"start_time": -1}},
            {"$limit": 100},
            {
                "$group": {
                    "_id": None,
                    "total_scraped": {"$sum": "$items_scraped"},
                    "total_saved": {"$sum": "$items_saved"},
                    "successful_runs": {"$sum": {"$cond": [{"$eq": ["$status", "success"]}, 1, 0]}},
                    "failed_runs": {"$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}},
                    "total_runs": {"$sum": 1},
                }
            }
        ]
        summary = list(coll_runs.aggregate(pipeline))
        if summary:
            s = summary[0]
            total_runs = s.get("total_runs", 0)
            successful = s.get("successful_runs", 0)
            summary_stats = {
                "total_scraped": s.get("total_scraped", 0),
                "total_saved": s.get("total_saved", 0),
                "success_rate_percent": round((successful / total_runs) * 100.0, 1) if total_runs > 0 else 100.0,
                "total_runs": total_runs
            }
    except Exception as e:
        logger.error(f"Error calculating summary stats: {e}")

    # Get last 15 saved articles
    recent_articles = []
    try:
        raw_articles = list(coll_articles.find().sort("created_date", -1).limit(15))
        for art in raw_articles:
            recent_articles.append({
                "id": str(art["_id"]),
                "title": art.get("headlines", {}).get("basic", "Untitled"),
                "category": art.get("category", "unknown"),
                "publisher": art.get("publisher") or art.get("_scraper_meta", {}).get("publisher") or "unknown",
                "url": art.get("canonical_url", ""),
                "created_date": art.get("created_date", datetime.utcnow()).isoformat() if isinstance(art.get("created_date"), datetime) else str(art.get("created_date")),
            })
    except Exception as e:
        logger.error(f"Error fetching recent articles: {e}")

    # Get all source statuses
    source_statuses = []
    try:
        coll_sources = get_collection("sources_status")
        raw_sources = list(coll_sources.find().sort("name", 1))
        for src in raw_sources:
            src["_id"] = str(src["_id"])
            if "last_scraped_at" in src and isinstance(src["last_scraped_at"], datetime):
                src["last_scraped_at"] = src["last_scraped_at"].isoformat()
            source_statuses.append(src)
    except Exception as e:
        logger.error(f"Error fetching source statuses: {e}")

    return {
        "total_articles": total_articles,
        "summary": summary_stats,
        "recent_runs": recent_runs,
        "recent_articles": recent_articles,
        "sources": source_statuses
    }
