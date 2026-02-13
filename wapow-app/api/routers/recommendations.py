"""Neo4j-based recommendations API (from grapow)."""
from datetime import datetime
from fastapi import APIRouter, HTTPException

from pydantic import BaseModel, Field

from api.db import Neo4jQuery

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


class RecommendationsRequest(BaseModel):
    user_id: str = Field(..., description="Target user ID")
    category: str = Field(..., description="Category (e.g. technology, travel)")
    current_hour: int | None = Field(None, description="Hour 0-23; defaults to current hour")
    limit: int = Field(10, ge=1, le=100, description="Max recommendations per list")
    time_window: int = Field(2, ge=0, le=12, description="Hours before/after for time-based recs")


@router.get("")
async def recommendations_info():
    """List recommendations endpoint: POST with JSON body (user_id, category, etc.)."""
    return {
        "endpoint": "POST /api/recommendations",
        "description": "Neo4j collaborative filtering: category + time-based recommendations",
        "body": {
            "user_id": "string (required)",
            "category": "string (required, e.g. technology, travel)",
            "current_hour": "int 0-23 (optional, defaults to now)",
            "limit": "int (optional, default 10)",
            "time_window": "int (optional, default 2)",
        },
    }


@router.post("", response_model=dict)
async def get_recommendations(req: RecommendationsRequest):
    """
    Get category-based and time-based collaborative filtering recommendations from Neo4j.
    """
    current_hour = req.current_hour
    if current_hour is None:
        current_hour = datetime.now().hour
    if not (0 <= current_hour <= 23):
        raise HTTPException(status_code=400, detail="current_hour must be between 0-23")

    try:
        with Neo4jQuery() as db_query:
            category_result = db_query.get_category_collaborative_recommendations(
                target_user_id=req.user_id,
                target_category=req.category,
                limit=req.limit,
            )
            category_recommendations = category_result.get("recommendations", [])

            time_result = db_query.get_collaborative_recommendations(
                target_user_id=req.user_id,
                current_hour=current_hour,
                limit=req.limit * 2,
                time_window=req.time_window,
            )
            time_recommendations = time_result.get("recommendations", [])

            category_article_ids = {rec["article_id"] for rec in category_recommendations}
            general_recommendations = [
                rec for rec in time_recommendations if rec["article_id"] not in category_article_ids
            ][: req.limit]

            return {
                "user_id": req.user_id,
                "category": req.category,
                "category_recommendations": category_recommendations,
                "general_recommendations": general_recommendations,
                "status": "success",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendations error: {str(e)}") from e
