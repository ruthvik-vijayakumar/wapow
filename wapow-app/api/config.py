"""Configuration for WAPOW API (MongoDB + Neo4j)."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env.dev if present (dev overrides), then .env as fallback
_config_dir = Path(__file__).resolve().parent.parent
load_dotenv(_config_dir / ".env.dev", override=True)
# load_dotenv(_config_dir / ".env")

# MongoDB
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    os.getenv("MONGODB_LOCAL_URI", "mongodb://localhost:27017/wapow-data"),
)
MONGODB_DB_NAME = "wapow-data"

# Neo4j (default: local/Docker; set NEO4J_URI in .env for Aura or remote)
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "wapow-neo4j")

# Server
PORT = int(os.getenv("PORT", "3001"))

# Auth (optional – leave empty to run without auth)
# Auth0: create an API in the dashboard, set identifier as AUTH0_AUDIENCE
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "").rstrip("/")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "")
AUTH_ENABLED = bool(AUTH0_DOMAIN and AUTH0_AUDIENCE)

# Content collections (MongoDB)
# Article categories are stored in a single "articles" collection with a "category" field
ARTICLE_CATEGORIES = [
    "sports",
    "style",
    "technology",
    "travel",
    "wellbeing",
]
ARTICLES_COLLECTION = "articles"
VIDEO_COLLECTION = "videos"
PODCAST_COLLECTION = "podcasts"
CONTENT_COLLECTIONS = ARTICLE_CATEGORIES  # Alias for backward compat
ALL_COLLECTIONS = ARTICLE_CATEGORIES + [VIDEO_COLLECTION, PODCAST_COLLECTION]

# User data collections (MongoDB)
USERS_COLLECTION = "users"
SAVED_ARTICLES_COLLECTION = "saved_articles"  # Legacy; migrated to users.saved
