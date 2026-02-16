"""WAPOW API: FastAPI app combining MongoDB content API + Neo4j recommendations."""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.config import PORT
from api.db import get_client
from api.routers import content as content_routers
from api.routers.articles import router as articles_router
from api.routers.recommendations import router as recommendations_router
from api.routers.saved_articles import router as saved_articles_router
from api.routers.comments import router as comments_router
from api.config import (
    AUTH_ENABLED,
    VIDEO_COLLECTION,
    PODCAST_COLLECTION,
)
from api.auth import get_current_user, get_current_user_or_dev, UserClaims
from api.services import user as user_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure MongoDB client is created
    get_client()
    from api.services import user as user_service
    from api.services import comments as comments_service
    user_service.ensure_indexes()
    comments_service.ensure_indexes()
    yield
    # Shutdown: close MongoDB client if needed
    # (PyMongo client is global; optional: close here)


app = FastAPI(
    title="WAPOW API",
    description="MongoDB content API + Neo4j recommendations",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Content routers for videos and podcasts (separate collections)
app.include_router(
    content_routers._make_router(VIDEO_COLLECTION, "Video", is_video=True, is_podcast=False),
    prefix="/api/videos",
)
app.include_router(
    content_routers._make_router(PODCAST_COLLECTION, "Podcast", is_video=False, is_podcast=True),
    prefix="/api/podcasts",
)

app.include_router(articles_router, prefix="/api")
app.include_router(recommendations_router, prefix="/api")
app.include_router(saved_articles_router, prefix="/api")
app.include_router(comments_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "🚀 Welcome to WAPOW API",
        "version": "1.0.0",
        "endpoints": {
            "articles": "GET /api/articles?category=sports|style|technology|travel|wellbeing",
            "articles_by_ids": "POST /api/articles/by-ids",
            "videos": "/api/videos",
            "podcasts": "/api/podcasts",
            "recommendations": "POST /api/recommendations",
            "me": "GET /api/me (requires Bearer token when Auth0 is configured)",
            "saved_articles": "GET/POST/DELETE /api/saved-articles (save/list/unsave)",
            "comments": "GET/POST/DELETE /api/comments (list/create/delete/vote)",
        },
        "database": "wapo_data (MongoDB) + Neo4j",
        "auth": "enabled" if AUTH_ENABLED else "disabled (set AUTH0_DOMAIN and AUTH0_AUDIENCE to enable)",
    }


@app.get("/health")
async def health():
    try:
        client = get_client()
        client.admin.command("ping")
        db_status = "Connected"
    except Exception:
        db_status = "Disconnected"
    return {
        "status": "OK",
        "database": db_status,
    }


@app.post("/api/test-json")
async def test_json(request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return {"success": True, "received": body, "headers": headers}


# Protected route: returns current user info and upserts into users collection
@app.get("/api/me", response_model=dict)
async def me(user: UserClaims = Depends(get_current_user_or_dev)):
    """Current user from JWT. Upserts user document in MongoDB on every call."""
    doc = user_service.get_or_create_user(user_id=user.user_id)
    return {
        "user_id": user.user_id,
        "sub": user.sub,
        "scope": user.scope,
        "permissions": user.permissions,
        **{k: doc.get(k) for k in ("name", "email", "picture", "created_at") if doc.get(k)},
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=PORT, reload=True)
