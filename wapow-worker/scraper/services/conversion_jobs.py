"""MongoDB-backed conversion job records for batch async processing (Worker-side)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from bson import ObjectId

from scraper.config import ARTICLES_COLLECTION
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


def find_article(article_id: str) -> dict | None:
    coll = get_db()[ARTICLES_COLLECTION]
    try:
        oid = ObjectId(article_id)
    except Exception:
        oid = article_id
    doc = coll.find_one({"_id": oid})
    if doc is None and oid != article_id:
        doc = coll.find_one({"_id": article_id})
    return doc


def create_conversion_job(article_id: str, force: bool = False) -> dict[str, Any]:
    if not find_article(article_id):
        raise ValueError("Article not found")
    job = create_job(article_id, force=force)
    from scraper.tasks.jobs import convert_article_to_story_task

    task = convert_article_to_story_task.delay(article_id, force=force, job_id=job["job_id"])
    job["task_id"] = task.id
    return job


def retry_job(job_id: str) -> dict[str, Any]:
    job = get_job(job_id)
    if not job:
        raise ValueError("Job not found")
    if job.get("status") != "failed":
        raise ValueError("Only failed conversion jobs can be retried")
    get_db()[JOBS_COLLECTION].update_one(
        {"job_id": job_id},
        {
            "$set": {
                "status": "pending",
                "error": None,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    from scraper.tasks.jobs import convert_article_to_story_task

    task = convert_article_to_story_task.delay(
        str(job["article_id"]),
        force=bool(job.get("force", False)),
        job_id=job_id,
    )
    job = get_job(job_id) or job
    job["task_id"] = task.id
    return job


def create_batch_conversion_jobs(article_ids: list[str], force: bool = False) -> list[dict[str, Any]]:
    return [create_conversion_job(str(article_id), force=force) for article_id in article_ids]


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


def is_worker_paused() -> bool:
    """Check if the slide conversion worker is currently paused."""
    coll = get_db()["system_settings"]
    doc = coll.find_one({"_id": "worker_status"})
    return doc.get("paused", False) if doc else False


def pause_worker() -> None:
    """Pause the background slide conversion worker."""
    coll = get_db()["system_settings"]
    coll.update_one({"_id": "worker_status"}, {"$set": {"paused": True}}, upsert=True)


def resume_worker() -> None:
    """Resume the background slide conversion worker."""
    coll = get_db()["system_settings"]
    coll.update_one({"_id": "worker_status"}, {"$set": {"paused": False}}, upsert=True)
