"""MongoDB-backed conversion job records for batch async processing."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from api.db import get_db

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



