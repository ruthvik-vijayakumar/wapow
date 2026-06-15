"""Abstract base scraper class."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional
from dataclasses import dataclass, field

from scraper.utils.rate_limiter import rate_limiter
from scraper.utils.robots import robots_checker


@dataclass
class ScrapedItem:
    """Represents a scraped content item before normalization."""

    source_name: str
    source_type: str
    url: str
    title: str
    description: str = ""
    author: str = ""
    image_url: str = ""
    publish_date: Optional[datetime] = None
    category: str = "technology"
    content_type: str = "article"  # article, video, podcast
    duration: Optional[int] = None  # For videos/podcasts, in seconds
    raw_data: dict = field(default_factory=dict)  # Original data from source


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    def __init__(self, source_name: str, source_type: str):
        """
        Initialize base scraper.

        Args:
            source_name: Human-readable name of the source
            source_type: Type identifier (rss, web, youtube, spotify)
        """
        self.source_name = source_name
        self.source_type = source_type
        self.rate_limiter = rate_limiter
        self.robots_checker = robots_checker

    @abstractmethod
    async def scrape(self) -> list[ScrapedItem]:
        """
        Scrape content from the source.

        Returns:
            List of scraped items
        """
        pass

    async def can_scrape(self, url: str) -> bool:
        """Check if we're allowed to scrape a URL."""
        return await self.robots_checker.can_fetch(url)

    async def wait_for_rate_limit(self, url: str) -> None:
        """Wait for rate limit before making a request."""
        await self.rate_limiter.wait(url)

    def create_item(
        self,
        url: str,
        title: str,
        description: str = "",
        author: str = "",
        image_url: str = "",
        publish_date: Optional[datetime] = None,
        category: str = "technology",
        content_type: str = "article",
        duration: Optional[int] = None,
        raw_data: Optional[dict] = None,
    ) -> ScrapedItem:
        """Create a ScrapedItem with common fields filled in."""
        return ScrapedItem(
            source_name=self.source_name,
            source_type=self.source_type,
            url=url,
            title=title,
            description=description,
            author=author,
            image_url=image_url,
            publish_date=publish_date,
            category=category,
            content_type=content_type,
            duration=duration,
            raw_data=raw_data or {},
        )
