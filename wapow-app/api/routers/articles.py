"""Unified articles endpoint + cross-collection by-IDs (MongoDB)."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from api.db import get_db
from api.config import ALL_COLLECTIONS, ARTICLE_CATEGORIES, ARTICLES_COLLECTION
from api.services.content import _transform_content_item, _transform_video_item, _transform_podcast_item
from bson import ObjectId

router = APIRouter(prefix="/articles", tags=["articles"])


class ArticlesByIdsBody(BaseModel):
    ids: list[str]


COLLECTION_MAP = {
    "sports": ("articles", False, False),
    "style": ("articles", False, False),
    "technology": ("articles", False, False),
    "travel": ("articles", False, False),
    "wellbeing": ("articles", False, False),
    "videos": ("videos", True, False),
    "podcasts": ("podcasts", False, True),
}


def _transform_item(item: dict, collection: str) -> dict:
    coll_name, is_video, is_podcast = COLLECTION_MAP.get(collection, (collection, False, False))
    if is_podcast:
        return _transform_podcast_item(item)
    if is_video:
        return _transform_video_item(item)
    return _transform_content_item(item)


@router.get("/")
async def list_articles(
    category: Optional[str] = Query(None, description="Filter by category (e.g. sports, technology)"),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500),
    sort_by: str = Query("created_date"),
    sort_order: str = Query("desc"),
):
    """List articles from the unified articles collection, optionally filtered by category."""
    db = get_db()
    coll = db[ARTICLES_COLLECTION]

    query: dict = {}
    if category:
        query["category"] = category

    sort_dir = -1 if sort_order == "desc" else 1
    sort_field = sort_by
    if sort_by in ("createdAt", "created_date"):
        sort_field = "created_date"
    elif sort_by in ("publishDate", "publish_date"):
        sort_field = "publish_date"

    skip = (page - 1) * limit
    cursor = coll.find(query).sort(sort_field, sort_dir).skip(skip).limit(limit)
    items = list(cursor)
    total = coll.count_documents(query)

    data = [_transform_content_item(item) for item in items]

    return {
        "success": True,
        "data": data,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }


@router.post("/by-ids")
async def articles_by_ids(body: ArticlesByIdsBody):
    """Fetch articles by IDs across articles (by category), videos, podcasts."""
    ids = body.ids
    if not ids:
        raise HTTPException(
            status_code=400,
            detail="Please provide a list of IDs in the request body",
        )
    max_ids = 100
    limited_ids = ids[:max_ids]

    id_list = []
    for i in limited_ids:
        try:
            id_list.append(ObjectId(i))
        except Exception:
            id_list.append(i)

    db = get_db()
    all_results = []
    grouped = {}

    # Keep raw string IDs for fallback searches (e.g. content_id on videos)
    string_ids = [str(i) for i in limited_ids]

    for coll_name in ALL_COLLECTIONS:
        if coll_name in ARTICLE_CATEGORIES:
            coll = db[ARTICLES_COLLECTION]
            query = {"_id": {"$in": id_list}, "category": coll_name}
        else:
            coll = db[coll_name]
            # For videos/podcasts, also search by content_id (legacy saved items may use it)
            query = {"$or": [
                {"_id": {"$in": id_list}},
                {"content_id": {"$in": string_ids}},
            ]}
        cursor = coll.find(query)
        items = list(cursor)
        transformed = [_transform_item(doc, coll_name) for doc in items]
        # Tag with collection name (videos vs video, etc.)
        key = "videos" if coll_name == "videos" else "podcasts" if coll_name == "podcasts" else coll_name
        grouped[key] = transformed
        for t in transformed:
            t["collection"] = key
            all_results.append(t)

    summary = {k: len(v) for k, v in grouped.items()}

    return {
        "success": True,
        "data": all_results,
        "grouped": grouped,
        "count": len(all_results),
        "requested": len(ids),
        "returned": len(all_results),
        "limited": len(limited_ids) < len(ids),
        "summary": summary,
    }
