"""Web scraper using BeautifulSoup and aiohttp."""

import logging
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup

from scraper.scrapers.base import BaseScraper, ScrapedItem
from scraper.models.source import WebSource
from scraper.config import settings
from scraper.utils.html_extractor import extract_article_content

logger = logging.getLogger(__name__)


class WebScraper(BaseScraper):
    """Web scraper using BeautifulSoup for HTML parsing."""

    def __init__(self, source: WebSource):
        """
        Initialize web scraper.

        Args:
            source: Web source configuration with CSS selectors
        """
        super().__init__(source.name, "web")
        self.source = source
        self.url = source.url
        self.category = source.category
        self.selectors = source.selectors

    async def scrape(self) -> list[ScrapedItem]:
        """
        Scrape content from a web page.

        Returns:
            List of scraped items
        """
        if not await self.can_scrape(self.url):
            logger.warning(f"robots.txt disallows scraping {self.url}")
            return []

        await self.wait_for_rate_limit(self.url)

        try:
            html = await self._fetch_page(self.url)
            if not html:
                return []

            soup = BeautifulSoup(html, "lxml")
            raw_items = self._parse_page(soup)

            items = []
            for item in raw_items:
                if item.url:
                    if await self.can_scrape(item.url):
                        await self.wait_for_rate_limit(item.url)
                        article_data = await extract_article_content(item.url)
                        if article_data:
                            item.raw_data["content_elements"] = article_data.get("content_elements") or []
                            item.raw_data["body_text"] = article_data.get("body_text") or ""
                            
                            # Fallback if fields are missing in listing
                            if not item.title and article_data.get("title"):
                                item.title = article_data["title"]
                            if not item.description and article_data.get("description"):
                                item.description = article_data["description"]
                            if not item.author and article_data.get("author"):
                                item.author = article_data["author"]
                            if not item.image_url and article_data.get("image_url"):
                                item.image_url = article_data["image_url"]
                    items.append(item)

            logger.info(f"Scraped {len(items)} items from web: {self.source.name}")
            return items

        except Exception as e:
            logger.error(f"Error scraping web page {self.url}: {e}")
            return []

    async def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch HTML content from a URL."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=30),
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; WAPOWBot/1.0)",
                        "Accept": "text/html,application/xhtml+xml",
                        "Accept-Language": "en-US,en;q=0.9",
                    },
                ) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch {url}: {response.status}")
                        return None
                    return await response.text()
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def _parse_page(self, soup: BeautifulSoup) -> list[ScrapedItem]:
        """Parse HTML page and extract articles."""
        items = []

        # Find article containers
        article_selector = self.selectors.get("articles", "article")
        articles = soup.select(article_selector)

        if not articles:
            # Fallback to common patterns
            articles = soup.select("article, .post, .entry, .story, .card")

        for article in articles[: settings.max_items_per_source]:
            item = self._parse_article(article)
            if item:
                items.append(item)

        return items

    def _parse_article(self, article: BeautifulSoup) -> Optional[ScrapedItem]:
        """Parse a single article element."""
        try:
            # Get link
            link_selector = self.selectors.get("link", "a")
            link_elem = article.select_one(link_selector)
            if not link_elem or not link_elem.get("href"):
                # Try finding any link with href
                link_elem = article.find("a", href=True)
            if not link_elem:
                return None

            url = link_elem.get("href", "")
            if url and not url.startswith("http"):
                url = urljoin(self.url, url)
            if not url:
                return None

            # Get title
            title_selector = self.selectors.get("title", "h1, h2, h3, .title")
            title_elem = article.select_one(title_selector)
            if not title_elem:
                title_elem = article.find(["h1", "h2", "h3"])
            title = title_elem.get_text(strip=True) if title_elem else ""
            if not title:
                return None

            # Get description
            desc_selector = self.selectors.get("description", "p, .description, .excerpt")
            desc_elem = article.select_one(desc_selector)
            if not desc_elem:
                desc_elem = article.find("p")
            description = desc_elem.get_text(strip=True)[:500] if desc_elem else ""

            # Get image
            img_selector = self.selectors.get("image", "img")
            img_elem = article.select_one(img_selector)
            if not img_elem:
                img_elem = article.find("img")
            image_url = ""
            if img_elem:
                image_url = (
                    img_elem.get("src")
                    or img_elem.get("data-src")
                    or img_elem.get("data-lazy-src")
                    or ""
                )
                if image_url and not image_url.startswith("http"):
                    image_url = urljoin(self.url, image_url)

            # Get author
            author_selector = self.selectors.get("author", ".author, .byline")
            author_elem = article.select_one(author_selector)
            author = author_elem.get_text(strip=True) if author_elem else ""

            # Get date
            date_selector = self.selectors.get("date", "time, .date, .published")
            date_elem = article.select_one(date_selector)
            publish_date = None
            if date_elem:
                datetime_attr = date_elem.get("datetime")
                if datetime_attr:
                    try:
                        publish_date = datetime.fromisoformat(
                            datetime_attr.replace("Z", "+00:00")
                        )
                    except ValueError:
                        pass

            return self.create_item(
                url=url,
                title=title,
                description=description,
                author=author,
                image_url=image_url,
                publish_date=publish_date,
                category=self.category,
                content_type="article",
            )

        except Exception as e:
            logger.warning(f"Error parsing article: {e}")
            return None
