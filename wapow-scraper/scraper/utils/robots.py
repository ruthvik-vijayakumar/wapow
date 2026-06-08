"""robots.txt compliance checker."""

import asyncio
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from typing import Optional

import aiohttp

from scraper.config import settings


class RobotsChecker:
    """Check robots.txt rules before scraping."""

    USER_AGENT = "WAPOWBot/1.0"

    def __init__(self):
        """Initialize robots checker."""
        self._parsers: dict[str, RobotFileParser] = {}
        self._fetch_errors: set[str] = set()
        self._lock = asyncio.Lock()

    def _get_robots_url(self, url: str) -> str:
        """Get the robots.txt URL for a given URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    def _get_domain_key(self, url: str) -> str:
        """Get domain key for caching."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    async def _fetch_robots(self, url: str) -> Optional[RobotFileParser]:
        """Fetch and parse robots.txt for a domain."""
        robots_url = self._get_robots_url(url)
        domain_key = self._get_domain_key(url)

        # Check if we already have it cached or failed before
        if domain_key in self._parsers:
            return self._parsers[domain_key]
        if domain_key in self._fetch_errors:
            return None

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    robots_url,
                    timeout=aiohttp.ClientTimeout(total=10),
                    headers={"User-Agent": self.USER_AGENT},
                ) as response:
                    if response.status == 200:
                        content = await response.text()
                        parser = RobotFileParser()
                        parser.parse(content.splitlines())
                        self._parsers[domain_key] = parser
                        return parser
                    else:
                        # No robots.txt or error - allow all
                        self._fetch_errors.add(domain_key)
                        return None
        except Exception:
            # Network error - allow but don't cache
            self._fetch_errors.add(domain_key)
            return None

    async def can_fetch(self, url: str) -> bool:
        """
        Check if we're allowed to fetch a URL according to robots.txt.

        Args:
            url: The URL to check

        Returns:
            True if fetching is allowed, False otherwise
        """
        if not settings.respect_robots_txt:
            return True

        async with self._lock:
            parser = await self._fetch_robots(url)

        if parser is None:
            # No robots.txt or error fetching - allow
            return True

        return parser.can_fetch(self.USER_AGENT, url)

    def get_crawl_delay(self, url: str) -> Optional[float]:
        """Get the crawl delay specified in robots.txt, if any."""
        domain_key = self._get_domain_key(url)
        parser = self._parsers.get(domain_key)

        if parser is None:
            return None

        try:
            delay = parser.crawl_delay(self.USER_AGENT)
            return float(delay) if delay else None
        except Exception:
            return None


# Global robots checker instance
robots_checker = RobotsChecker()
