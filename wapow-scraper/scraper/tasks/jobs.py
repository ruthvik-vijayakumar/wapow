"""Scraping job definitions."""

import asyncio
import logging
from pathlib import Path
from typing import Any

import aiohttp
import yaml

from scraper.config import ARTICLES_COLLECTION, settings
from scraper.db import get_collection
from scraper.models.source import (
    SourceConfig,
    RSSSource,
    WebSource,
    YouTubeSource,
    SpotifySource,
)
from scraper.scrapers.rss_scraper import RSSScraper
from scraper.scrapers.web_scraper import WebScraper
from scraper.scrapers.playwright_scraper import PlaywrightScraper
from scraper.scrapers.api_scrapers.youtube import YouTubeScraper
from scraper.scrapers.api_scrapers.spotify import SpotifyScraper
from scraper.processors.normalizer import ContentNormalizer
from scraper.processors.deduplicator import deduplicator

logger = logging.getLogger(__name__)

# Path to sources configuration
SOURCES_PATH = Path(__file__).parent.parent / "sources" / "sources.yaml"


def load_sources() -> SourceConfig:
    """Load source configuration from YAML file."""
    if not SOURCES_PATH.exists():
        logger.warning(f"Sources file not found: {SOURCES_PATH}")
        return SourceConfig()

    try:
        with open(SOURCES_PATH) as f:
            data = yaml.safe_load(f) or {}

        # Parse into typed models
        config = SourceConfig(
            rss=[RSSSource(**s) for s in data.get("rss", [])],
            web=[WebSource(**s) for s in data.get("web", [])],
            youtube=[YouTubeSource(**s) for s in data.get("youtube", [])],
            spotify=[SpotifySource(**s) for s in data.get("spotify", [])],
        )
        return config

    except Exception as e:
        logger.error(f"Error loading sources: {e}")
        return SourceConfig()


async def _trigger_story_convert(article_id: str) -> None:
    """POST to wapow-app to persist StoryView-compatible ai_summary on new articles."""
    base = settings.wapow_api_base_url.strip().rstrip("/")
    if not base:
        return
    url = f"{base}/api/articles/{article_id}/convert-to-story"
    timeout = aiohttp.ClientTimeout(total=120)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, params={"force": "false"}) as resp:
                if resp.status not in (200, 404):
                    body = await resp.text()
                    logger.warning(
                        "Story convert HTTP %s for %s: %s",
                        resp.status,
                        article_id,
                        body[:300],
                    )
    except Exception as e:  # noqa: BLE001
        logger.warning("Story convert request failed for %s: %s", article_id, e)


async def _save_items(items: list[tuple[str, dict[str, Any]]]) -> int:
    """
    Save normalized items to MongoDB.

    Args:
        items: List of (collection_name, document) tuples

    Returns:
        Number of items saved
    """
    saved = 0
    for collection_name, doc in items:
        try:
            coll = get_collection(collection_name)
            result = coll.insert_one(doc)
            if result.inserted_id:
                saved += 1
                # Update deduplication cache
                url = doc.get("canonical_url", "")
                if url:
                    deduplicator.mark_as_inserted(url, collection_name)
                if (
                    collection_name == ARTICLES_COLLECTION
                    and settings.story_convert_on_ingest
                    and settings.wapow_api_base_url.strip()
                ):
                    asyncio.create_task(_trigger_story_convert(str(result.inserted_id)))
        except Exception as e:
            logger.error(f"Error saving to {collection_name}: {e}")

    return saved


async def run_rss_scrape() -> dict[str, Any]:
    """Run RSS feed scraping job."""
    logger.info("Starting RSS scrape job")
    sources = load_sources()
    normalizer = ContentNormalizer()

    total_scraped = 0
    total_saved = 0

    for source in sources.rss:
        if not source.enabled:
            continue

        try:
            scraper = RSSScraper(source)
            items = await scraper.scrape()
            total_scraped += len(items)

            # Normalize items
            normalized = [(normalizer.normalize(item)) for item in items]

            # Filter duplicates
            unique = deduplicator.filter_duplicates(normalized)

            # Save to MongoDB
            saved = await _save_items(unique)
            total_saved += saved

            logger.info(
                f"RSS {source.name}: scraped={len(items)}, unique={len(unique)}, saved={saved}"
            )

        except Exception as e:
            logger.error(f"Error in RSS scrape for {source.name}: {e}")

    logger.info(f"RSS scrape complete: total_scraped={total_scraped}, total_saved={total_saved}")
    return {"scraped": total_scraped, "saved": total_saved}


async def run_web_scrape() -> dict[str, Any]:
    """Run web scraping job."""
    logger.info("Starting web scrape job")
    sources = load_sources()
    normalizer = ContentNormalizer()

    total_scraped = 0
    total_saved = 0

    for source in sources.web:
        if not source.enabled:
            continue

        try:
            # Use Playwright for JS-heavy sites
            if source.use_playwright:
                scraper = PlaywrightScraper(source)
            else:
                scraper = WebScraper(source)

            items = await scraper.scrape()
            total_scraped += len(items)

            # Normalize items
            normalized = [(normalizer.normalize(item)) for item in items]

            # Filter duplicates
            unique = deduplicator.filter_duplicates(normalized)

            # Save to MongoDB
            saved = await _save_items(unique)
            total_saved += saved

            logger.info(
                f"Web {source.name}: scraped={len(items)}, unique={len(unique)}, saved={saved}"
            )

        except Exception as e:
            logger.error(f"Error in web scrape for {source.name}: {e}")

    logger.info(f"Web scrape complete: total_scraped={total_scraped}, total_saved={total_saved}")
    return {"scraped": total_scraped, "saved": total_saved}


async def run_youtube_scrape() -> dict[str, Any]:
    """Run YouTube scraping job."""
    logger.info("Starting YouTube scrape job")
    sources = load_sources()
    normalizer = ContentNormalizer()

    total_scraped = 0
    total_saved = 0

    for source in sources.youtube:
        if not source.enabled:
            continue

        try:
            scraper = YouTubeScraper(source)
            items = await scraper.scrape()
            total_scraped += len(items)

            # Normalize items
            normalized = [(normalizer.normalize(item)) for item in items]

            # Filter duplicates
            unique = deduplicator.filter_duplicates(normalized)

            # Save to MongoDB
            saved = await _save_items(unique)
            total_saved += saved

            logger.info(
                f"YouTube {source.name}: scraped={len(items)}, unique={len(unique)}, saved={saved}"
            )

        except Exception as e:
            logger.error(f"Error in YouTube scrape for {source.name}: {e}")

    logger.info(
        f"YouTube scrape complete: total_scraped={total_scraped}, total_saved={total_saved}"
    )
    return {"scraped": total_scraped, "saved": total_saved}


async def run_spotify_scrape() -> dict[str, Any]:
    """Run Spotify podcast scraping job."""
    logger.info("Starting Spotify scrape job")
    sources = load_sources()
    normalizer = ContentNormalizer()

    total_scraped = 0
    total_saved = 0

    for source in sources.spotify:
        if not source.enabled:
            continue

        try:
            scraper = SpotifyScraper(source)
            items = await scraper.scrape()
            total_scraped += len(items)

            # Normalize items
            normalized = [(normalizer.normalize(item)) for item in items]

            # Filter duplicates
            unique = deduplicator.filter_duplicates(normalized)

            # Save to MongoDB
            saved = await _save_items(unique)
            total_saved += saved

            logger.info(
                f"Spotify {source.name}: scraped={len(items)}, unique={len(unique)}, saved={saved}"
            )

        except Exception as e:
            logger.error(f"Error in Spotify scrape for {source.name}: {e}")

    logger.info(
        f"Spotify scrape complete: total_scraped={total_scraped}, total_saved={total_saved}"
    )
    return {"scraped": total_scraped, "saved": total_saved}


async def run_all_scrapers() -> dict[str, Any]:
    """Run all scrapers sequentially."""
    logger.info("Starting full scrape of all sources")

    results = {
        "rss": await run_rss_scrape(),
        "web": await run_web_scrape(),
        "youtube": await run_youtube_scrape(),
        "spotify": await run_spotify_scrape(),
    }

    total_scraped = sum(r.get("scraped", 0) for r in results.values())
    total_saved = sum(r.get("saved", 0) for r in results.values())

    logger.info(f"Full scrape complete: total_scraped={total_scraped}, total_saved={total_saved}")

    return {
        "results": results,
        "total_scraped": total_scraped,
        "total_saved": total_saved,
    }
