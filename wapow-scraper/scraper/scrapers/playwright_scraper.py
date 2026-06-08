"""Playwright-based scraper for JavaScript-heavy sites."""

import logging
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scraper.scrapers.base import BaseScraper, ScrapedItem
from scraper.models.source import WebSource
from scraper.config import settings

logger = logging.getLogger(__name__)


class PlaywrightScraper(BaseScraper):
    """Scraper using Playwright for JavaScript-rendered content."""

    def __init__(self, source: WebSource):
        """
        Initialize Playwright scraper.

        Args:
            source: Web source configuration
        """
        super().__init__(source.name, "playwright")
        self.source = source
        self.url = source.url
        self.category = source.category
        self.selectors = source.selectors
        self._browser = None
        self._playwright = None

    async def _init_browser(self):
        """Initialize Playwright browser."""
        if self._playwright is None:
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)

    async def _cleanup(self):
        """Clean up browser resources."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def scrape(self) -> list[ScrapedItem]:
        """
        Scrape content from a JavaScript-heavy web page.

        Returns:
            List of scraped items
        """
        if not await self.can_scrape(self.url):
            logger.warning(f"robots.txt disallows scraping {self.url}")
            return []

        await self.wait_for_rate_limit(self.url)

        try:
            await self._init_browser()

            page = await self._browser.new_page()
            page.set_default_timeout(30000)

            # Set user agent
            await page.set_extra_http_headers(
                {"User-Agent": "Mozilla/5.0 (compatible; WAPOWBot/1.0)"}
            )

            # Navigate to page
            response = await page.goto(self.url, wait_until="networkidle")
            if not response or response.status != 200:
                logger.error(f"Failed to load {self.url}: {response.status if response else 'no response'}")
                await page.close()
                return []

            # Wait for content to load
            article_selector = self.selectors.get("articles", "article")
            try:
                await page.wait_for_selector(article_selector, timeout=10000)
            except Exception:
                # Try fallback selectors
                for selector in ["article", ".post", ".entry", ".story"]:
                    try:
                        await page.wait_for_selector(selector, timeout=5000)
                        break
                    except Exception:
                        continue

            # Get rendered HTML
            html = await page.content()
            await page.close()

            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, "lxml")
            items = self._parse_page(soup)

            logger.info(
                f"Scraped {len(items)} items via Playwright: {self.source.name}"
            )
            return items

        except Exception as e:
            logger.error(f"Error scraping with Playwright {self.url}: {e}")
            return []
        finally:
            await self._cleanup()

    def _parse_page(self, soup: BeautifulSoup) -> list[ScrapedItem]:
        """Parse HTML page and extract articles."""
        items = []

        article_selector = self.selectors.get("articles", "article")
        articles = soup.select(article_selector)

        if not articles:
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
            desc_selector = self.selectors.get("description", "p, .description")
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
            date_selector = self.selectors.get("date", "time, .date")
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
