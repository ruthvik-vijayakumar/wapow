"""Unified articles endpoint + cross-collection by-IDs (MongoDB)."""
import asyncio
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api.db import get_db
from api.config import ALL_COLLECTIONS, ARTICLE_CATEGORIES, ARTICLES_COLLECTION
from api.services.content import _transform_content_item, _transform_video_item, _transform_podcast_item
from api.services.conversion_jobs import create_job
from api.services.story_pipeline.service import (
    convert_article_to_story,
    find_article_doc,
    preview_story_for_article,
)
from bson import ObjectId

router = APIRouter(prefix="/articles", tags=["articles"])


class ArticlesByIdsBody(BaseModel):
    ids: list[str]


class BatchConvertToStoryBody(BaseModel):
    ids: list[str]
    force: bool = False


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

    # Fetch matching story slides in a single batch query to avoid N+1 query overhead
    item_ids = [item["_id"] for item in items]
    slides_cursor = db["story_slides"].find({"article_id": {"$in": item_ids}})
    slides_map = {}
    for s in slides_cursor:
        art_id = s.get("article_id")
        if art_id:
            slides_map[str(art_id)] = s

    for item in items:
        str_id = str(item["_id"])
        if str_id in slides_map:
            slides = slides_map[str_id]
            item["ai_summary"] = {
                "pages": slides.get("pages"),
                "generation_timestamp": slides.get("generation_timestamp"),
                "llm_model_used": slides.get("llm_model_used"),
            }

    data = [_transform_content_item(item) for item in items]

    return {
        "success": True,
        "data": data,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }


@router.post("/batch-convert-to-story")
async def batch_convert_to_story(body: BatchConvertToStoryBody):
    """Queue story conversion jobs (async). Max 50 IDs. Returns 202 with job_ids."""
    if len(body.ids) > 50:
        raise HTTPException(
            status_code=400,
            detail="Maximum 50 article IDs per batch",
        )
    if not body.ids:
        raise HTTPException(status_code=400, detail="ids must not be empty")
    job_ids: list[str] = []
    for aid in body.ids:
        job = create_job(str(aid), force=body.force)
        job_ids.append(job["job_id"])
    return JSONResponse(
        status_code=202,
        content={"success": True, "job_ids": job_ids},
    )


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

    # Fetch matching story slides in a single batch query to avoid N+1 query overhead
    slides_cursor = db["story_slides"].find({"article_id": {"$in": id_list}})
    slides_map = {}
    for s in slides_cursor:
        art_id = s.get("article_id")
        if art_id:
            slides_map[str(art_id)] = s

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
        
        # Merge slides from batch map
        for doc in items:
            str_id = str(doc["_id"])
            if str_id in slides_map:
                slides = slides_map[str_id]
                doc["ai_summary"] = {
                    "pages": slides.get("pages"),
                    "generation_timestamp": slides.get("generation_timestamp"),
                    "llm_model_used": slides.get("llm_model_used"),
                }

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


@router.get("/{article_id}")
async def get_article(
    article_id: str,
    ensure_story: bool = Query(False, description="If true, generate ai_summary when missing"),
):
    """Fetch a single article from the unified articles collection by _id."""
    doc = find_article_doc(article_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Article not found")
    if ensure_story:
        ai = doc.get("ai_summary") or {}
        if not ai.get("pages"):
            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, lambda: convert_article_to_story(article_id, force=False))
                doc = find_article_doc(article_id) or doc
            except ValueError:
                pass
    data = _transform_content_item(doc)
    return {"success": True, "data": data}


@router.post("/{article_id}/convert-to-story")
async def convert_to_story(article_id: str, force: bool = Query(False)):
    """Generate StoryView-compatible ai_summary.pages and persist on the article."""
    try:
        result = convert_article_to_story(article_id, force=force)
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/{article_id}/preview-story")
async def preview_story(article_id: str):
    """Generate ai_summary without persisting (for QA)."""
    try:
        result = preview_story_for_article(article_id)
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
