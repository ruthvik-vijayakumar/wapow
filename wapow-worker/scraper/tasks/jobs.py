"""Scraping job definitions with observability and metrics tracking."""

import asyncio
from datetime import datetime
import logging
import time
from pathlib import Path
from typing import Any

import aiohttp
from pymongo import UpdateOne
import yaml

from scraper.config import ARTICLES_COLLECTION, settings
from scraper.db import get_collection
from scraper.models import (
    SourceConfig,
    RSSSource,
    WebSource,
    RawArticle,
)
from scraper.scrapers.base import ScrapedItem
from scraper.scrapers.rss_scraper import RSSScraper
from scraper.scrapers.web_scraper import WebScraper
from scraper.scrapers.playwright_scraper import PlaywrightScraper
from scraper.processors.normalizer import ContentNormalizer
from scraper.processors.deduplicator import deduplicator
from scraper.utils.metrics import ScraperRunTracker, update_source_status

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

        # Parse into typed models (rss and web only)
        config = SourceConfig(
            rss=[RSSSource(**s) for s in data.get("rss", [])],
            web=[WebSource(**s) for s in data.get("web", [])],
        )
        return config

    except Exception as e:
        logger.error(f"Error loading sources: {e}")
        return SourceConfig()


def save_sources(config: SourceConfig) -> None:
    """Save source configuration back to the YAML file."""
    try:
        data = {
            "rss": [
                {
                    "name": s.name,
                    "url": s.url,
                    "category": s.category,
                    "enabled": s.enabled,
                }
                for s in config.rss
            ],
            "web": [
                {
                    "name": s.name,
                    "url": s.url,
                    "category": s.category,
                    "enabled": s.enabled,
                    "use_playwright": s.use_playwright,
                    "selectors": s.selectors,
                }
                for s in config.web
            ]
        }
        with open(SOURCES_PATH, "w") as f:
            yaml.safe_dump(data, f, sort_keys=False, default_flow_style=False)
        logger.info(f"Successfully saved updated sources configuration to {SOURCES_PATH}")
    except Exception as e:
        logger.error(f"Error saving sources: {e}")
        raise e


async def _save_items(items: list[tuple[str, dict[str, Any]]]) -> list[tuple[str, str]]:
    """
    Save normalized items to MongoDB.

    Args:
        items: List of (collection_name, document) tuples

    Returns:
        List of (inserted_id, title) tuples of saved items
    """
    saved = []
    convert_ids = []
    for collection_name, doc in items:
        try:
            coll = get_collection(collection_name)
            result = coll.insert_one(doc)
            if result.inserted_id:
                inserted_id_str = str(result.inserted_id)
                title = doc.get("headlines", {}).get("basic") or doc.get("title") or "Untitled"
                saved.append((inserted_id_str, title))
                # Update deduplication cache
                url = doc.get("canonical_url", "")
                if url:
                    deduplicator.mark_as_inserted(url, collection_name)
                
                # Collect IDs for batch conversion
                if collection_name == ARTICLES_COLLECTION:
                    convert_ids.append(inserted_id_str)
        except Exception as e:
            logger.error(f"Error saving to {collection_name}: {e}")

    # Trigger batch conversion directly via DB queue if enabled and we have valid articles
    if convert_ids and settings.story_convert_on_ingest:
        from scraper.services.conversion_jobs import create_job
        for aid in convert_ids:
            try:
                create_job(str(aid), force=False)
                logger.info(f"Queued background conversion job for article: {aid}")
            except Exception as e:
                logger.error(f"Error queuing background conversion job for article {aid}: {e}")

    return saved


def sanitize_for_bson(val: Any) -> Any:
    """Recursively convert non-BSON-serializable types (like time.struct_time) to serializable types."""
    import time
    if isinstance(val, dict):
        return {k: sanitize_for_bson(v) for k, v in val.items()}
    elif isinstance(val, time.struct_time):
        try:
            return datetime(*val[:6])
        except ValueError:
            return None
    elif isinstance(val, list):
        return [sanitize_for_bson(x) for x in val]
    elif isinstance(val, tuple):
        return [sanitize_for_bson(x) for x in val]
    return val


async def _save_raw_articles(items: list[ScrapedItem]) -> None:
    """Save raw scraped items to MongoDB raw_articles collection before normalization."""
    if not items:
        return

    coll = get_collection("raw_articles")
    now = datetime.utcnow()
    operations = []

    for item in items:
        sanitized_raw = sanitize_for_bson(item.raw_data or {})
        raw_article = RawArticle(
            source_name=item.source_name,
            source_type=item.source_type,
            url=item.url,
            title=item.title,
            description=item.description or "",
            author=item.author or "",
            image_url=item.image_url or "",
            publish_date=item.publish_date,
            category=item.category,
            content_type=item.content_type,
            duration=item.duration,
            raw_data=sanitized_raw,
            scraped_at=now
        )
        doc = raw_article.dict()
        operations.append(UpdateOne({"url": doc["url"]}, {"$set": doc}, upsert=True))

    if operations:
        try:
            coll.bulk_write(operations)
            logger.info(f"Saved {len(items)} raw articles to MongoDB raw_articles collection")
        except Exception as e:
            logger.error(f"Error bulk saving raw articles to MongoDB: {e}")


async def run_rss_scrape() -> dict[str, Any]:
    """Run RSS feed scraping job with observability tracking."""
    logger.info("Starting RSS scrape job")
    tracker = ScraperRunTracker("rss_feeds")
    tracker.start()

    sources = load_sources()
    normalizer = ContentNormalizer()

    total_scraped = 0
    total_saved = 0

    try:
        for source in sources.rss:
            if not source.enabled:
                continue

            start_src_time = time.time()
            src_status = "success"
            src_items_scraped = 0
            src_items_saved = 0
            src_error = ""
            try:
                scraper = RSSScraper(source)
                items = await scraper.scrape()
                src_items_scraped = len(items)
                total_scraped += src_items_scraped

                # Save raw articles before normalization
                await _save_raw_articles(items)

                # Normalize items
                normalized = [(normalizer.normalize(item)) for item in items]

                # Filter duplicates
                unique = deduplicator.filter_duplicates(normalized)

                # Save to MongoDB
                saved_info = await _save_items(unique)
                src_items_saved = len(saved_info)
                total_saved += src_items_saved
                for item_id, item_title in saved_info:
                    tracker.add_saved_article(item_id, item_title)

                logger.info(
                    f"RSS {source.name}: scraped={len(items)}, unique={len(unique)}, saved={len(saved_info)}"
                )

            except Exception as e:
                src_status = "failed"
                src_error = str(e)
                err_msg = f"Error in RSS scrape for {source.name}: {e}"
                logger.error(err_msg)
                tracker.add_error(err_msg)
            finally:
                src_duration = time.time() - start_src_time
                update_source_status(
                    source_name=source.name,
                    source_type="rss",
                    url=source.url,
                    category=source.category,
                    enabled=source.enabled,
                    status=src_status,
                    items_scraped=src_items_scraped,
                    items_saved=src_items_saved,
                    duration=src_duration,
                    error_msg=src_error
                )

        tracker.items_scraped = total_scraped
        tracker.finish("success")
    except Exception as e:
        err_msg = f"Fatal error in RSS scrape: {e}"
        logger.error(err_msg)
        tracker.add_error(err_msg)
        tracker.finish("failed")

    logger.info(f"RSS scrape complete: total_scraped={total_scraped}, total_saved={total_saved}")
    return {"scraped": total_scraped, "saved": total_saved}


async def run_web_scrape() -> dict[str, Any]:
    """Run web scraping job with observability tracking."""
    logger.info("Starting web scrape job")
    tracker = ScraperRunTracker("web_scrape")
    tracker.start()

    sources = load_sources()
    normalizer = ContentNormalizer()

    total_scraped = 0
    total_saved = 0

    try:
        for source in sources.web:
            if not source.enabled:
                continue

            start_src_time = time.time()
            src_status = "success"
            src_items_scraped = 0
            src_items_saved = 0
            src_error = ""
            try:
                # Use Playwright for JS-heavy sites
                if source.use_playwright:
                    scraper = PlaywrightScraper(source)
                else:
                    scraper = WebScraper(source)

                items = await scraper.scrape()
                src_items_scraped = len(items)
                total_scraped += src_items_scraped

                # Save raw articles before normalization
                await _save_raw_articles(items)

                # Normalize items
                normalized = [(normalizer.normalize(item)) for item in items]

                # Filter duplicates
                unique = deduplicator.filter_duplicates(normalized)

                # Save to MongoDB
                saved_info = await _save_items(unique)
                src_items_saved = len(saved_info)
                total_saved += src_items_saved
                for item_id, item_title in saved_info:
                    tracker.add_saved_article(item_id, item_title)

                logger.info(
                    f"Web {source.name}: scraped={len(items)}, unique={len(unique)}, saved={len(saved_info)}"
                )

            except Exception as e:
                src_status = "failed"
                src_error = str(e)
                err_msg = f"Error in web scrape for {source.name}: {e}"
                logger.error(err_msg)
                tracker.add_error(err_msg)
            finally:
                src_duration = time.time() - start_src_time
                update_source_status(
                    source_name=source.name,
                    source_type="web",
                    url=source.url,
                    category=source.category,
                    enabled=source.enabled,
                    status=src_status,
                    items_scraped=src_items_scraped,
                    items_saved=src_items_saved,
                    duration=src_duration,
                    error_msg=src_error
                )

        tracker.items_scraped = total_scraped
        tracker.finish("success")
    except Exception as e:
        err_msg = f"Fatal error in web scrape: {e}"
        logger.error(err_msg)
        tracker.add_error(err_msg)
        tracker.finish("failed")

    logger.info(f"Web scrape complete: total_scraped={total_scraped}, total_saved={total_saved}")
    return {"scraped": total_scraped, "saved": total_saved}


async def run_all_scrapers() -> dict[str, Any]:
    """Run all scrapers sequentially."""
    logger.info("Starting full scrape of all sources")

    results = {
        "rss": await run_rss_scrape(),
        "web": await run_web_scrape(),
    }

    total_scraped = sum(r.get("scraped", 0) for r in results.values())
    total_saved = sum(r.get("saved", 0) for r in results.values())

    logger.info(f"Full scrape complete: total_scraped={total_scraped}, total_saved={total_saved}")

    return {
        "results": results,
        "total_scraped": total_scraped,
        "total_saved": total_saved,
    }
