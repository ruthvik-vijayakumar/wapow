"""Per-domain rate limiting for polite scraping."""

import asyncio
import time
from urllib.parse import urlparse
from typing import Optional

from scraper.config import settings


class RateLimiter:
    """Rate limiter that enforces delays between requests to the same domain."""

    def __init__(self, default_delay: float = None):
        """
        Initialize rate limiter.

        Args:
            default_delay: Default delay in seconds between requests to same domain.
                          Uses config setting if not specified.
        """
        self.default_delay = default_delay or settings.default_rate_limit_delay
        self._last_request: dict[str, float] = {}
        self._domain_delays: dict[str, float] = {}
        self._lock = asyncio.Lock()

    def set_domain_delay(self, domain: str, delay: float) -> None:
        """Set a custom delay for a specific domain."""
        self._domain_delays[domain] = delay

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return parsed.netloc.lower()

    def _get_delay(self, domain: str) -> float:
        """Get the delay for a domain."""
        return self._domain_delays.get(domain, self.default_delay)

    async def wait(self, url: str) -> None:
        """
        Wait if necessary before making a request to the URL.

        This ensures proper rate limiting per domain.
        """
        domain = self._get_domain(url)
        delay = self._get_delay(domain)

        async with self._lock:
            last = self._last_request.get(domain, 0)
            elapsed = time.time() - last
            wait_time = delay - elapsed

            if wait_time > 0:
                await asyncio.sleep(wait_time)

            self._last_request[domain] = time.time()

    def record_request(self, url: str) -> None:
        """Record that a request was made (for sync contexts)."""
        domain = self._get_domain(url)
        self._last_request[domain] = time.time()

    def time_until_allowed(self, url: str) -> float:
        """Get time in seconds until a request to this URL is allowed."""
        domain = self._get_domain(url)
        delay = self._get_delay(domain)
        last = self._last_request.get(domain, 0)
        elapsed = time.time() - last
        return max(0, delay - elapsed)


# Global rate limiter instance
rate_limiter = RateLimiter()
