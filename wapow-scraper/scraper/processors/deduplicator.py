"""Content deduplication to prevent duplicate entries."""

import hashlib
import logging
from typing import Optional

from pymongo.collection import Collection

from scraper.db import get_collection
from scraper.config import ARTICLES_COLLECTION, VIDEO_COLLECTION, PODCAST_COLLECTION

logger = logging.getLogger(__name__)


class Deduplicator:
    """Check for and prevent duplicate content in MongoDB."""

    def __init__(self):
        """Initialize deduplicator."""
        self._url_cache: dict[str, set[str]] = {
            ARTICLES_COLLECTION: set(),
            VIDEO_COLLECTION: set(),
            PODCAST_COLLECTION: set(),
        }
        self._cache_loaded = False

    def _load_cache(self) -> None:
        """Load existing URL hashes from MongoDB into cache."""
        if self._cache_loaded:
            return

        for collection_name in [ARTICLES_COLLECTION, VIDEO_COLLECTION, PODCAST_COLLECTION]:
            try:
                coll = get_collection(collection_name)
                # Get all existing URL hashes from scraped content
                cursor = coll.find(
                    {"_scraper_meta.url_hash": {"$exists": True}},
                    {"_scraper_meta.url_hash": 1},
                )
                for doc in cursor:
                    url_hash = doc.get("_scraper_meta", {}).get("url_hash")
                    if url_hash:
                        self._url_cache[collection_name].add(url_hash)

                logger.info(
                    f"Loaded {len(self._url_cache[collection_name])} URL hashes for {collection_name}"
                )
            except Exception as e:
                logger.warning(f"Error loading cache for {collection_name}: {e}")

        self._cache_loaded = True

    def _hash_url(self, url: str) -> str:
        """Generate a hash of the URL."""
        return hashlib.sha256(url.encode()).hexdigest()[:16]

    def is_duplicate(self, url: str, collection_name: str) -> bool:
        """
        Check if a URL already exists in the collection.

        Args:
            url: The URL to check
            collection_name: The MongoDB collection name

        Returns:
            True if duplicate, False otherwise
        """
        self._load_cache()
        url_hash = self._hash_url(url)

        # Check cache first
        if url_hash in self._url_cache.get(collection_name, set()):
            return True

        # Double-check in MongoDB (in case cache is stale)
        try:
            coll = get_collection(collection_name)
            exists = coll.find_one(
                {"_scraper_meta.url_hash": url_hash}, {"_id": 1}
            )
            if exists:
                # Update cache
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

    def filter_duplicates(
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

            if self.is_duplicate(url, collection_name):
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
        self._cache_loaded = False


# Global deduplicator instance
deduplicator = Deduplicator()
