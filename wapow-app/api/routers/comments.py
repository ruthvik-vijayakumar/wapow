"""Comments API — CRUD + voting, persisted in MongoDB."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.auth import UserClaims, get_current_user_or_dev
from api.services import comments as comments_service

router = APIRouter(prefix="/comments", tags=["comments"])


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------

class CreateCommentBody(BaseModel):
    article_id: str = Field(..., description="Content ID being commented on")
    text: str = Field(..., min_length=1, max_length=2000, description="Comment text")
    parent_id: str | None = Field(None, description="Parent comment ID for replies")
    user_name: str | None = Field(None, description="Display name of commenter")
    user_picture: str | None = Field(None, description="Avatar URL of commenter")


class VoteBody(BaseModel):
    vote: str | None = Field(
        ...,
        description="'up', 'down', or null to remove vote",
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=dict)
async def list_comments(
    article_id: str = Query(..., description="Article/content ID"),
    limit: int = Query(50, ge=1, le=200),
    user: UserClaims = Depends(get_current_user_or_dev),
):
    """List comments (with nested replies) for an article."""
    items = comments_service.get_comments(
        article_id=article_id,
        user_id=user.user_id,
        limit=limit,
    )
    return {"success": True, "data": items, "count": len(items)}


@router.get("/count", response_model=dict)
async def comment_count(
    article_id: str = Query(..., description="Article/content ID"),
):
    """Get comment count for an article (no auth required)."""
    count = comments_service.get_comment_count(article_id=article_id)
    return {"success": True, "count": count}


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_comment(
    body: CreateCommentBody,
    user: UserClaims = Depends(get_current_user_or_dev),
):
    """Create a comment or reply."""
    doc = comments_service.create_comment(
        user_id=user.user_id,
        user_name=body.user_name or "Anonymous",
        user_picture=body.user_picture,
        article_id=body.article_id,
        text=body.text,
        parent_id=body.parent_id,
    )
    return {"success": True, "data": doc}


@router.delete("/{comment_id}", response_model=dict)
async def delete_comment(
    comment_id: str,
    user: UserClaims = Depends(get_current_user_or_dev),
):
    """Delete own comment (and its replies)."""
    removed = comments_service.delete_comment(
        comment_id=comment_id,
        user_id=user.user_id,
    )
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found or you are not the author",
        )
    return {"success": True, "removed": True}


@router.post("/{comment_id}/vote", response_model=dict)
async def vote_comment(
    comment_id: str,
    body: VoteBody,
    user: UserClaims = Depends(get_current_user_or_dev),
):
    """Upvote, downvote, or remove vote on a comment."""
    if body.vote not in ("up", "down", None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="vote must be 'up', 'down', or null",
        )
    updated = comments_service.vote_comment(
        comment_id=comment_id,
        user_id=user.user_id,
        vote=body.vote,
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )
    return {"success": True, "data": updated}
