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
from api.config import (
    AUTH_ENABLED,
    CONTENT_COLLECTIONS,
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
    user_service.ensure_indexes()
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

# Content routers: /api/sports, /api/style, etc.
for coll in CONTENT_COLLECTIONS:
    name = coll.capitalize()
    r = content_routers._make_router(coll, name, is_video=False, is_podcast=False)
    app.include_router(r, prefix=f"/api/{coll}", tags=[name])

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


@app.get("/")
async def root():
    return {
        "message": "🚀 Welcome to WAPOW API",
        "version": "1.0.0",
        "endpoints": {
            "sports": "/api/sports",
            "style": "/api/style",
            "technology": "/api/technology",
            "travel": "/api/travel",
            "wellbeing": "/api/wellbeing",
            "videos": "/api/videos",
            "podcasts": "/api/podcasts",
            "articles_by_ids": "POST /api/articles/by-ids",
            "recommendations": "POST /api/recommendations",
            "me": "GET /api/me (requires Bearer token when Auth0 is configured)",
            "saved_articles": "GET/POST/DELETE /api/saved-articles (save/list/unsave)",
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
