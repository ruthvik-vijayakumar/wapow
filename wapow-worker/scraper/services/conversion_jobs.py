"""MongoDB-backed conversion job records for batch async processing (Worker-side)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from scraper.db import get_db

JOBS_COLLECTION = "conversion_jobs"


def ensure_conversion_jobs_indexes() -> None:
    coll = get_db()[JOBS_COLLECTION]
    coll.create_index("job_id", unique=True)
    coll.create_index("created_at")
    coll.create_index([("status", 1), ("created_at", 1)])


def create_job(article_id: str, force: bool = False) -> dict[str, Any]:
    job_id = str(uuid4())
    now = datetime.now(timezone.utc)
    doc = {
        "job_id": job_id,
        "article_id": article_id,
        "status": "pending",
        "force": force,
        "error": None,
        "ai_summary": None,
        "lease_expires_at": None,
        "created_at": now,
        "updated_at": now,
    }
    get_db()[JOBS_COLLECTION].insert_one(doc)
    return doc


def update_job(
    job_id: str,
    status: str,
    *,
    error: str | None = None,
    ai_summary: dict | None = None,
) -> None:
    patch: dict[str, Any] = {
        "status": status,
        "lease_expires_at": None,
        "updated_at": datetime.now(timezone.utc),
    }
    if error is not None:
        patch["error"] = error
    if ai_summary is not None:
        patch["ai_summary"] = ai_summary
    get_db()[JOBS_COLLECTION].update_one({"job_id": job_id}, {"$set": patch})


def get_job(job_id: str) -> dict | None:
    return get_db()[JOBS_COLLECTION].find_one({"job_id": job_id})


def serialize_job(doc: dict) -> dict:
    if not doc:
        return doc
    out = dict(doc)
    if "_id" in out:
        out["_id"] = str(out["_id"])
    for k in ("created_at", "updated_at", "lease_expires_at"):
        if k in out and hasattr(out[k], "isoformat"):
            out[k] = out[k].isoformat()
    return out


_worker_should_stop = False
_worker_paused = False


def is_worker_paused() -> bool:
    """Check if the slide conversion worker is currently paused."""
    return _worker_paused


def pause_worker() -> None:
    """Pause the background slide conversion worker."""
    global _worker_paused
    _worker_paused = True


def resume_worker() -> None:
    """Resume the background slide conversion worker."""
    global _worker_paused
    _worker_paused = False


async def start_conversion_worker() -> None:
    global _worker_should_stop
    _worker_should_stop = False
    
    import asyncio
    from datetime import datetime, timezone, timedelta
    from pymongo import ReturnDocument
    from scraper.services.story_pipeline.service import convert_article_to_story
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info("Starting worker conversion polling loop...")
    
    db = get_db()
    coll = db[JOBS_COLLECTION]
    
    while not _worker_should_stop:
        if _worker_paused:
            await asyncio.sleep(5)
            continue
        try:
            now = datetime.now(timezone.utc)
            # Atomic find and modify to acquire lease on pending or expired processing jobs
            job = coll.find_one_and_update(
                {
                    "$or": [
                        {"status": "pending"},
                        {
                            "status": "processing",
                            "lease_expires_at": {"$lt": now}
                        }
                    ]
                },
                {
                    "$set": {
                        "status": "processing",
                        "lease_expires_at": now + timedelta(minutes=5),
                        "updated_at": now
                    }
                },
                sort=[("created_at", 1)],
                return_document=ReturnDocument.AFTER
            )
            
            if job:
                logger.info(f"Worker acquired job {job['job_id']} for article {job['article_id']}")
                try:
                    loop = asyncio.get_running_loop()
                    # Execute blocking pipeline conversion in worker thread
                    result = await loop.run_in_executor(
                        None,
                        lambda: convert_article_to_story(str(job["article_id"]), force=job.get("force", False))
                    )
                    update_job(job["job_id"], "completed", ai_summary=result.get("ai_summary"))
                    logger.info(f"Worker completed job {job['job_id']}")
                except Exception as err:
                    logger.exception(f"Worker job {job['job_id']} failed with error:")
                    update_job(job["job_id"], "failed", error=str(err))
            else:
                # No jobs, wait 5 seconds
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            logger.info("Conversion worker loop cancelled.")
            break
        except Exception as ex:
            logger.error(f"Error in conversion worker loop: {ex}")
            await asyncio.sleep(5)


async def stop_conversion_worker() -> None:
    global _worker_should_stop
    _worker_should_stop = True
    import logging
    logging.getLogger(__name__).info("Signalled conversion worker loop to stop.")
