"""Single-page web scraper using the shared HTML article extractor."""

import logging
from datetime import datetime
from typing import Optional

from scraper.models.source import WebSource
from scraper.scrapers.base import BaseScraper, ScrapedItem
from scraper.utils.html_extractor import extract_article_content

logger = logging.getLogger(__name__)


class WebScraper(BaseScraper):
    """Scraper for one article/documentation page URL."""

    def __init__(self, source: WebSource):
        super().__init__(source.name, "web")
        self.source = source
        self.url = source.url
        self.category = source.category

    async def scrape(self) -> list[ScrapedItem]:
        if not await self.can_scrape(self.url):
            logger.warning(f"robots.txt disallows scraping {self.url}")
            return []

        await self.wait_for_rate_limit(self.url)
        article_data = await extract_article_content(
            self.url,
            use_playwright=self.source.use_playwright,
        )
        if not article_data:
            logger.warning(f"No web content extracted from {self.url}")
            return []

        title = (article_data.get("title") or "").strip()
        body_text = (article_data.get("body_text") or "").strip()
        content_elements = article_data.get("content_elements") or []
        if not title or (not body_text and not content_elements):
            logger.warning(f"Web source missing title/content after extraction: {self.url}")
            return []

        publish_date = article_data.get("publish_date")
        if publish_date is not None and not isinstance(publish_date, datetime):
            publish_date = None

        raw_data = {
            "title": title,
            "description": article_data.get("description") or "",
            "author": article_data.get("author") or "",
            "author_link": article_data.get("author_link") or "",
            "publisher": article_data.get("publisher") or self.source.name,
            "publish_date": publish_date,
            "image_url": article_data.get("image_url") or "",
            "content_elements": content_elements,
            "body_text": body_text,
        }

        return [
            self.create_item(
                url=self.url,
                title=title,
                description=raw_data["description"],
                author=raw_data["author"],
                image_url=raw_data["image_url"],
                publish_date=publish_date,
                category=self.category,
                content_type="article",
                raw_data=raw_data,
            )
        ]
