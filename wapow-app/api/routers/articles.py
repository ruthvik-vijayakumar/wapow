"""Cross-collection articles by IDs (MongoDB)."""
from fastapi import APIRouter, HTTPException
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

    for coll_name in ALL_COLLECTIONS:
        if coll_name in ARTICLE_CATEGORIES:
            coll = db[ARTICLES_COLLECTION]
            query = {"_id": {"$in": id_list}, "category": coll_name}
        else:
            coll = db[coll_name]
            query = {"_id": {"$in": id_list}}
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
