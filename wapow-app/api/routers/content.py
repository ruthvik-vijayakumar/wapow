"""Generic content router: list, get by id, meta (categories, stats, authors), by-ids."""
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from api.services.content import (
    get_collection,
    list_items,
    get_by_id,
    get_categories,
    get_stats,
    get_authors,
    get_by_ids,
)
from api.config import (
    CONTENT_COLLECTIONS,
    VIDEO_COLLECTION,
    PODCAST_COLLECTION,
    ALL_COLLECTIONS,
)

# Build one router per collection by mounting the same logic with different collection name


class ByIdsBody(BaseModel):
    ids: list[str]


def _make_router(collection_name: str, model_name: str, is_video: bool = False, is_podcast: bool = False) -> APIRouter:
    router = APIRouter(prefix="", tags=[model_name])

    @router.get("/")
    async def list_collection(
        page: int = Query(1, ge=1),
        limit: int = Query(100, ge=1, le=500),
        category: str | None = None,
        search: str | None = None,
        sortBy: str = Query("created_date", alias="sortBy"),
        sortOrder: str = Query("desc", alias="sortOrder"),
    ):
        items, total = list_items(
            collection_name,
            page=page,
            limit=limit,
            category=category,
            search=search,
            sort_by=sortBy,
            sort_order=sortOrder,
            is_video=is_video,
            is_podcast=is_podcast,
        )
        return {
            "success": True,
            "data": items,
            "pagination": {
                "currentPage": page,
                "totalPages": (total + limit - 1) // limit if limit else 0,
                "totalItems": total,
                "itemsPerPage": limit,
            },
        }

    @router.get("/meta/categories")
    async def meta_categories():
        data = get_categories(collection_name)
        return {"success": True, "data": data}

    @router.get("/meta/stats")
    async def meta_stats():
        data = get_stats(collection_name)
        return {"success": True, "data": data}

    @router.get("/meta/authors")
    async def meta_authors():
        data = get_authors(collection_name)
        return {"success": True, "data": data}

    @router.get("/{id}")
    async def get_item(id: str):
        item = get_by_id(collection_name, id)
        if item is None:
            raise HTTPException(status_code=404, detail=f"{model_name} item not found")
        return {"success": True, "data": item}

    @router.post("/by-ids")
    async def post_by_ids(body: ByIdsBody):
        ids = body.ids
        if not ids:
            raise HTTPException(
                status_code=400,
                detail="Please provide a list of IDs in the request body",
            )
        items, requested, returned, limited = get_by_ids(
            collection_name,
            ids,
            transform_content=True,
            is_video=is_video,
            is_podcast=is_podcast,
        )
        return {
            "success": True,
            "data": items,
            "count": returned,
            "requested": requested,
            "returned": returned,
            "limited": limited,
        }

    return router
