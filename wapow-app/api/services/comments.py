"""Comments service: comments + votes stored in MongoDB."""
from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection

from api.config import COMMENTS_COLLECTION, COMMENT_VOTES_COLLECTION
from api.db import get_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialize_doc(doc: dict | None) -> dict | None:
    """Convert BSON types (ObjectId, datetime) for JSON serialisation."""
    if doc is None:
        return doc
    out: dict = {}
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


def _comments_coll() -> Collection:
    return get_db()[COMMENTS_COLLECTION]


def _votes_coll() -> Collection:
    return get_db()[COMMENT_VOTES_COLLECTION]


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def create_comment(
    user_id: str,
    user_name: str,
    user_picture: str | None,
    article_id: str,
    text: str,
    parent_id: str | None = None,
) -> dict:
    """Insert a new comment (or reply when parent_id is set)."""
    now = datetime.now(timezone.utc)
    doc = {
        "article_id": article_id,
        "user_id": user_id,
        "user_name": user_name,
        "user_picture": user_picture,
        "text": text,
        "parent_id": parent_id,
        "upvotes": 0,
        "downvotes": 0,
        "created_at": now,
        "updated_at": now,
    }
    result = _comments_coll().insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize_doc(doc)


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def get_comments(
    article_id: str,
    user_id: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Fetch top-level comments with nested replies for an article.

    If *user_id* is given, each comment/reply includes a ``user_vote``
    field (``"up"`` | ``"down"`` | ``null``).
    """
    coll = _comments_coll()

    # Fetch all comments for this article (top-level + replies) in one query
    docs = list(
        coll.find({"article_id": article_id}).sort("created_at", DESCENDING)
    )

    if not docs:
        return []

    # Pre-fetch votes for the requesting user
    user_votes: dict[str, str] = {}
    if user_id:
        comment_ids = [doc["_id"] for doc in docs]
        votes = _votes_coll().find({
            "comment_id": {"$in": [str(cid) for cid in comment_ids]},
            "user_id": user_id,
        })
        for v in votes:
            user_votes[v["comment_id"]] = v["vote"]

    # Separate top-level vs replies
    top_level: list[dict] = []
    replies_map: dict[str, list[dict]] = {}

    for doc in docs:
        serialized = _serialize_doc(doc)
        serialized["user_vote"] = user_votes.get(serialized["_id"])
        pid = serialized.get("parent_id")
        if pid:
            replies_map.setdefault(pid, []).append(serialized)
        else:
            top_level.append(serialized)

    # Attach replies (sorted oldest-first so the thread reads naturally)
    for comment in top_level:
        comment["replies"] = sorted(
            replies_map.get(comment["_id"], []),
            key=lambda r: r.get("created_at", ""),
        )

    return top_level[:limit]


def get_comment_count(article_id: str) -> int:
    """Total comments (incl. replies) for an article."""
    return _comments_coll().count_documents({"article_id": article_id})


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

def delete_comment(comment_id: str, user_id: str) -> bool:
    """Delete a comment only if *user_id* is the author. Also deletes replies and associated votes."""
    coll = _comments_coll()
    # Only delete if the user owns the comment
    result = coll.delete_one({"_id": ObjectId(comment_id), "user_id": user_id})
    if result.deleted_count == 0:
        return False

    # Also delete any replies to this comment
    reply_ids = [
        str(r["_id"])
        for r in coll.find({"parent_id": comment_id}, {"_id": 1})
    ]
    if reply_ids:
        coll.delete_many({"parent_id": comment_id})
        _votes_coll().delete_many({"comment_id": {"$in": reply_ids}})

    # Delete votes on the deleted comment itself
    _votes_coll().delete_many({"comment_id": comment_id})
    return True


# ---------------------------------------------------------------------------
# Vote
# ---------------------------------------------------------------------------

def vote_comment(comment_id: str, user_id: str, vote: str | None) -> dict | None:
    """Upvote, downvote, or remove vote on a comment.

    *vote* must be ``"up"``, ``"down"``, or ``None`` (remove).
    Returns the updated comment or None if not found.
    """
    coll = _comments_coll()
    votes = _votes_coll()

    # Ensure the comment exists
    comment = coll.find_one({"_id": ObjectId(comment_id)})
    if not comment:
        return None

    # Get current vote (if any)
    existing = votes.find_one({"comment_id": comment_id, "user_id": user_id})
    old_vote = existing["vote"] if existing else None

    if old_vote == vote:
        # Same vote again → treat as toggle-off
        vote = None

    # Build the $inc update for the comment
    inc: dict[str, int] = {}
    if old_vote == "up":
        inc["upvotes"] = -1
    elif old_vote == "down":
        inc["downvotes"] = -1

    if vote == "up":
        inc["upvotes"] = inc.get("upvotes", 0) + 1
    elif vote == "down":
        inc["downvotes"] = inc.get("downvotes", 0) + 1

    # Apply vote change
    if inc:
        coll.update_one({"_id": ObjectId(comment_id)}, {"$inc": inc})

    # Upsert/remove the vote record
    if vote is None:
        votes.delete_one({"comment_id": comment_id, "user_id": user_id})
    else:
        votes.update_one(
            {"comment_id": comment_id, "user_id": user_id},
            {"$set": {"vote": vote}},
            upsert=True,
        )

    # Return the updated comment
    updated = coll.find_one({"_id": ObjectId(comment_id)})
    serialized = _serialize_doc(updated)
    serialized["user_vote"] = vote
    return serialized


# ---------------------------------------------------------------------------
# Indexes
# ---------------------------------------------------------------------------

def ensure_indexes() -> None:
    """Create MongoDB indexes for comments and votes. Call at startup."""
    comments = _comments_coll()
    comments.create_index([("article_id", ASCENDING), ("created_at", DESCENDING)])
    comments.create_index("parent_id")
    comments.create_index("user_id")

    votes = _votes_coll()
    votes.create_index(
        [("comment_id", ASCENDING), ("user_id", ASCENDING)],
        unique=True,
    )
