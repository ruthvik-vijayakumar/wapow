"""Saved articles API - persist to MongoDB."""
from fastapi import APIRouter, Depends

from pydantic import BaseModel, Field

from api.auth import UserClaims, get_current_user_or_dev
from api.services import user as user_service

router = APIRouter(prefix="/saved-articles", tags=["saved-articles"])


class SaveArticleBody(BaseModel):
    article_id: str = Field(..., description="Article/content ID to save")
    collection: str | None = Field(None, description="Content collection, e.g. sports, videos")


@router.get("/ids", response_model=dict)
async def list_saved_article_ids(
    user: UserClaims = Depends(get_current_user_or_dev),
):
    """List saved article IDs (for quick lookup)."""
    ids = user_service.get_saved_article_ids(user_id=user.user_id)
    return {"success": True, "ids": list(ids)}


@router.post("", response_model=dict)
async def save_article(
    body: SaveArticleBody,
    user: UserClaims = Depends(get_current_user_or_dev),
):
    """Save an article for the current user. Idempotent."""
    doc = user_service.save_article(
        user_id=user.user_id,
        article_id=body.article_id,
        collection=body.collection,
    )
    return {"success": True, "data": doc}


@router.delete("/{article_id}", response_model=dict)
async def unsave_article(
    article_id: str,
    user: UserClaims = Depends(get_current_user_or_dev),
):
    """Remove a saved article."""
    removed = user_service.unsave_article(user_id=user.user_id, article_id=article_id)
    return {"success": True, "removed": removed}


@router.get("", response_model=dict)
async def list_saved_articles(
    limit: int = 100,
    user: UserClaims = Depends(get_current_user_or_dev),
):
    """List saved articles for the current user."""
    items = user_service.get_saved_articles(user_id=user.user_id, limit=limit)
    return {"success": True, "data": items, "count": len(items)}
