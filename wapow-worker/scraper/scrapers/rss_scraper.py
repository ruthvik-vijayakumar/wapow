"""RSS/Atom feed scraper using feedparser."""

from __future__ import annotations

import logging
import asyncio
from datetime import datetime
from time import mktime
from typing import Optional

import aiohttp
import feedparser

from scraper.scrapers.base import BaseScraper, ScrapedItem
from scraper.models.source import RSSSource
from scraper.config import settings
from scraper.utils.html_extractor import extract_article_content

logger = logging.getLogger(__name__)


class RSSScraper(BaseScraper):
    """Scraper for RSS and Atom feeds."""

    def __init__(self, source: RSSSource):
        """
        Initialize RSS scraper.

        Args:
            source: RSS source configuration
        """
        super().__init__(source.name, "rss")
        self.source = source
        self.url = source.url
        self.category = source.category

    async def scrape(self) -> list[ScrapedItem]:
        """
        Fetch and parse RSS feed.

        Returns:
            List of scraped items from the feed
        """
        if not await self.can_scrape(self.url):
            logger.warning(f"robots.txt disallows scraping {self.url}")
            return []

        await self.wait_for_rate_limit(self.url)

        try:
            # Fetch feed content
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.url,
                    timeout=aiohttp.ClientTimeout(total=30),
                    headers={"User-Agent": "WAPOWBot/1.0"},
                ) as response:
                    if response.status != 200:
                        logger.error(
                            f"Failed to fetch RSS feed {self.url}: {response.status}"
                        )
                        return []
                    content = await response.text()

            # Parse feed in a thread executor to prevent event loop CPU-blocking
            feed = await asyncio.to_thread(feedparser.parse, content)

            if feed.bozo and not feed.entries:
                logger.error(f"Failed to parse RSS feed {self.url}: {feed.bozo_exception}")
                return []

            # Parse feed entries concurrently, sharing browser process
            from playwright.async_api import async_playwright
            
            items = []
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                try:
                    sem = asyncio.Semaphore(4)  # Max 4 concurrent browser context tabs
                    tasks = [self._parse_entry(entry, browser, sem) for entry in feed.entries[: settings.max_items_per_source]]
                    parsed_items = await asyncio.gather(*tasks)
                    items = [item for item in parsed_items if item]
                finally:
                    await browser.close()

            logger.info(f"Scraped {len(items)} items from RSS feed: {self.source.name}")
            return items

        except Exception as e:
            logger.error(f"Error scraping RSS feed {self.url}: {e}")
            return []

    async def _parse_entry(
        self,
        entry: dict,
        browser=None,
        semaphore: Optional[asyncio.Semaphore] = None
    ) -> Optional[ScrapedItem]:
        """Parse a single feed entry into a ScrapedItem, fetching full content if allowed."""
        try:
            # Get URL
            url = entry.get("link", "")
            if not url:
                return None

            # Get title
            title = entry.get("title", "").strip()

            # Get description
            description = ""
            if "summary" in entry:
                description = entry.summary
            elif "description" in entry:
                description = entry.description
            # Strip HTML tags from description
            if description:
                from bs4 import BeautifulSoup
                # Thread executor fallback for html tags parser is not strictly required here
                # since it's short, but bs4 is quick on summaries
                description = BeautifulSoup(description, "lxml").get_text()[:500]

            # Get author
            author = ""
            if "author" in entry:
                author = entry.author
            elif "authors" in entry and entry.authors:
                author = entry.authors[0].get("name", "")

            # Get publish date
            publish_date = None
            if "published_parsed" in entry and entry.published_parsed:
                publish_date = datetime.fromtimestamp(mktime(entry.published_parsed))
            elif "updated_parsed" in entry and entry.updated_parsed:
                publish_date = datetime.fromtimestamp(mktime(entry.updated_parsed))

            # Get image URL
            image_url = ""
            if "media_content" in entry and entry.media_content:
                for media in entry.media_content:
                    if media.get("medium") == "image" or media.get("type", "").startswith(
                        "image"
                    ):
                        image_url = media.get("url", "")
                        break
            if not image_url and "media_thumbnail" in entry and entry.media_thumbnail:
                image_url = entry.media_thumbnail[0].get("url", "")
            if not image_url and "enclosures" in entry:
                for enc in entry.enclosures:
                    if enc.get("type", "").startswith("image"):
                        image_url = enc.get("href", "")
                        break

            # Now fetch full page details if allowed
            content_elements = []
            full_body_text = ""
            if url:
                if await self.can_scrape(url):
                    await self.wait_for_rate_limit(url)
                    
                    if semaphore:
                        async with semaphore:
                            article_data = await extract_article_content(url, browser=browser)
                    else:
                        article_data = await extract_article_content(url, browser=browser)
                        
                    if article_data:
                        content_elements = article_data.get("content_elements") or []
                        full_body_text = article_data.get("body_text") or ""

                        # Fallback to scraped metadata if missing in RSS feed
                        if not title and article_data.get("title"):
                            title = article_data["title"]
                        if not description and article_data.get("description"):
                            description = article_data["description"]
                        if not author and article_data.get("author"):
                            author = article_data["author"]
                        if not image_url and article_data.get("image_url"):
                            image_url = article_data["image_url"]

            if not title:
                return None

            raw_data = dict(entry)
            if content_elements:
                raw_data["content_elements"] = content_elements
            if full_body_text:
                raw_data["body_text"] = full_body_text

            return self.create_item(
                url=url,
                title=title,
                description=description,
                author=author,
                image_url=image_url,
                publish_date=publish_date,
                category=self.category,
                content_type="article",
                raw_data=raw_data,
            )

        except Exception as e:
            logger.warning(f"Error parsing RSS entry: {e}")
            return None
