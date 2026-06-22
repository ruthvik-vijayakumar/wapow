"""Configuration for WAPOW Scraper service."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load .env file if present
_config_dir = Path(__file__).resolve().parent.parent
load_dotenv(_config_dir / ".env")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017/wapow-data"
    mongodb_db_name: str = "wapow-data"

    # Server
    port: int = 3003
    debug: bool = False

    # Scraping settings
    scrape_interval_rss: int = 60  # minutes
    scrape_interval_web: int = 120  # minutes

    # Rate limiting
    default_rate_limit_delay: float = 1.0  # seconds between requests per domain
    respect_robots_txt: bool = True

    # Content settings
    max_items_per_source: int = 50  # Max items to fetch per source per run

    # After ingesting an article, call wapow-app to generate ai_summary (story slides)
    wapow_api_base_url: str = "http://localhost:3001"  # e.g. http://localhost:3001 (no trailing slash)
    story_convert_on_ingest: bool = True

    # LLM Settings
    gemini_api_key: str = ""
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"

    class Config:
        env_prefix = ""
        case_sensitive = False


settings = Settings()

# Content categories (must match wapow-app)
ARTICLE_CATEGORIES = [
    "sports",
    "style",
    "technology",
    "travel",
    "wellbeing",
]
ARTICLES_COLLECTION = "articles"
