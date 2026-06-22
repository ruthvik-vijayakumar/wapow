"""Content deduplication to prevent duplicate entries."""

from __future__ import annotations

import hashlib
import logging
import asyncio
from typing import Optional

from scraper.db import get_collection
from scraper.config import ARTICLES_COLLECTION

logger = logging.getLogger(__name__)


class Deduplicator:
    """Check for and prevent duplicate content in MongoDB."""

    def __init__(self):
        """Initialize deduplicator."""
        self._url_cache: dict[str, set[str]] = {
            ARTICLES_COLLECTION: set(),
        }

    def _hash_url(self, url: str) -> str:
        """Generate a hash of the URL."""
        return hashlib.sha256(url.encode()).hexdigest()[:16]

    async def is_duplicate(self, url: str, collection_name: str) -> bool:
        """
        Check if a URL already exists in the collection.

        Args:
            url: The URL to check
            collection_name: The MongoDB collection name

        Returns:
            True if duplicate, False otherwise
        """
        url_hash = self._hash_url(url)

        # Check local session cache first
        if url_hash in self._url_cache.get(collection_name, set()):
            return True

        # Double-check in MongoDB (on-demand query wrapped in thread)
        try:
            coll = get_collection(collection_name)
            exists = await asyncio.to_thread(
                lambda: coll.find_one({"_scraper_meta.url_hash": url_hash}, {"_id": 1})
            )
            if exists:
                # Update local cache
                self._url_cache.setdefault(collection_name, set()).add(url_hash)
                return True
        except Exception as e:
            logger.warning(f"Error checking duplicate in MongoDB: {e}")

        return False

    def mark_as_inserted(self, url: str, collection_name: str) -> None:
        """
        Mark a URL as inserted (update cache).

        Args:
            url: The URL that was inserted
            collection_name: The MongoDB collection name
        """
        url_hash = self._hash_url(url)
        self._url_cache.setdefault(collection_name, set()).add(url_hash)

    async def filter_duplicates(
        self, items: list[tuple[str, dict]], log_skipped: bool = True
    ) -> list[tuple[str, dict]]:
        """
        Filter out duplicate items from a list.

        Args:
            items: List of (collection_name, document) tuples
            log_skipped: Whether to log skipped duplicates

        Returns:
            Filtered list with duplicates removed
        """
        filtered = []
        skipped = 0

        for collection_name, doc in items:
            url = doc.get("canonical_url", "")
            if not url:
                # No URL to dedupe on, include it
                filtered.append((collection_name, doc))
                continue

            if await self.is_duplicate(url, collection_name):
                skipped += 1
                continue

            filtered.append((collection_name, doc))

        if log_skipped and skipped > 0:
            logger.info(f"Filtered out {skipped} duplicate items")

        return filtered

    def clear_cache(self) -> None:
        """Clear the in-memory URL cache."""
        for key in self._url_cache:
            self._url_cache[key] = set()


# Global deduplicator instance
deduplicator = Deduplicator()
