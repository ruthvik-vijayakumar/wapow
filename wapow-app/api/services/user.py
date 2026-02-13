"""User data service: users collection with embedded saved content (MongoDB)."""
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo.collection import Collection

from api.config import USERS_COLLECTION
from api.db import get_db


def _serialize_doc(doc: dict | None) -> dict | None:
    """Convert BSON types for JSON."""
    if doc is None:
        return doc
    out = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            out[k] = str(v)
        elif isinstance(v, datetime):
            out[k] = v.isoformat()
        elif isinstance(v, dict):
            out[k] = _serialize_doc(v)
        elif isinstance(v, list):
            out[k] = [_serialize_doc(x) if isinstance(x, dict) else x for x in v]
        else:
            out[k] = v
    return out


def _get_users_collection() -> Collection:
    return get_db()[USERS_COLLECTION]


def get_or_create_user(
    user_id: str,
    profile: dict | None = None,
) -> dict:
    """Get or create user by user_id. Optionally update name/email/picture. Create saved: [] if new."""
    coll = _get_users_collection()
    now = datetime.now(timezone.utc)
    update: dict = {"updated_at": now}
    if profile:
        for key in ("name", "email", "picture"):
            if key in profile and profile[key] is not None:
                update[key] = profile[key]
    result = coll.find_one_and_update(
        {"user_id": user_id},
        {
            "$set": update,
            "$setOnInsert": {"user_id": user_id, "saved": [], "created_at": now},
        },
        upsert=True,
        return_document=True,
    )
    return _serialize_doc(result)


def save_article(user_id: str, article_id: str, collection: str | None = None) -> dict:
    """Save an article for a user. Idempotent. Two-step: ensure user exists, then pull+push."""
    coll = _get_users_collection()
    now = datetime.now(timezone.utc)
    saved_item = {
        "article_id": article_id,
        "collection": collection or "unknown",
        "created_at": now,
    }
    # Step 1: Ensure user document exists
    coll.update_one(
        {"user_id": user_id},
        {
            "$setOnInsert": {"user_id": user_id, "saved": [], "created_at": now},
            "$set": {"updated_at": now},
        },
        upsert=True,
    )
    # Step 2: Remove any existing entry for this article_id (dedup)
    coll.update_one(
        {"user_id": user_id},
        {"$pull": {"saved": {"article_id": article_id}}},
    )
    # Step 3: Push the new saved item
    coll.update_one(
        {"user_id": user_id},
        {"$push": {"saved": saved_item}},
    )
    return _serialize_doc(saved_item)


def unsave_article(user_id: str, article_id: str) -> bool:
    """Remove a saved article. Returns True if removed."""
    coll = _get_users_collection()
    result = coll.update_one(
        {"user_id": user_id},
        {"$pull": {"saved": {"article_id": article_id}}, "$set": {"updated_at": datetime.now(timezone.utc)}},
    )
    return result.modified_count > 0


def get_saved_articles(user_id: str, limit: int = 100) -> list[dict]:
    """Get saved articles for a user, newest first. Returns list of {article_id, collection, created_at}."""
    coll = _get_users_collection()
    user = coll.find_one({"user_id": user_id}, {"saved": 1})
    if not user or not user.get("saved"):
        return []
    saved = user["saved"]
    # Sort by created_at descending, limit
    sorted_saved = sorted(saved, key=lambda x: x.get("created_at", datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
    limited = sorted_saved[:limit]
    return [_serialize_doc(s) for s in limited]


def get_saved_article_ids(user_id: str) -> set[str]:
    """Get set of article IDs saved by user."""
    coll = _get_users_collection()
    user = coll.find_one({"user_id": user_id}, {"saved.article_id": 1})
    if not user or not user.get("saved"):
        return set()
    return {str(s.get("article_id", "")) for s in user["saved"] if s.get("article_id")}


def is_article_saved(user_id: str, article_id: str) -> bool:
    """Check if user has saved an article."""
    return article_id in get_saved_article_ids(user_id)


def ensure_indexes() -> None:
    """Create indexes for users. Call at startup."""
    coll = _get_users_collection()
    coll.create_index("user_id", unique=True)
