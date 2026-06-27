"""Story-centric API endpoints backed by story_slides."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from api.services import stories as stories_service

router = APIRouter(prefix="/stories", tags=["stories"])


class StoriesByIdsBody(BaseModel):
    ids: list[str]


@router.get("")
@router.get("/")
async def list_stories(
    category: Optional[str] = Query(None, description="Filter by normalized article category"),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500),
    sort_order: str = Query("desc"),
):
    """List canonical generated story decks."""
    data, total = stories_service.list_stories(
        page=page,
        limit=limit,
        category=category,
        sort_order=sort_order,
    )
    return {
        "success": True,
        "data": data,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }


@router.post("/by-ids")
async def stories_by_ids(body: StoriesByIdsBody):
    """Fetch canonical story decks by article IDs."""
    if not body.ids:
        raise HTTPException(status_code=400, detail="Please provide a list of IDs")

    limited_ids = body.ids[:100]
    data = stories_service.get_stories_by_ids(limited_ids)
    return {
        "success": True,
        "data": data,
        "requested": len(body.ids),
        "returned": len(data),
        "limited": len(limited_ids) < len(body.ids),
    }


@router.get("/{article_id}")
async def get_story(article_id: str):
    """Fetch one canonical story deck by article ID."""
    story = stories_service.get_story(article_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return {"success": True, "data": story}
