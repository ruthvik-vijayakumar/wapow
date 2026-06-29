"""Content normalizer to transform scraped items to MongoDB schemas."""

import hashlib
from datetime import datetime
from typing import Any

from scraper.scrapers.base import ScrapedItem
from scraper.config import ARTICLES_COLLECTION


class ContentNormalizer:
    """Transform scraped items into MongoDB document schemas."""

    def normalize(self, item: ScrapedItem) -> tuple[str, dict[str, Any]]:
        """
        Normalize a scraped item to the appropriate MongoDB schema.

        Args:
            item: The scraped item to normalize

        Returns:
            Tuple of (collection_name, document)
        """
        return ARTICLES_COLLECTION, self._normalize_article(item)

    def _normalize_article(self, item: ScrapedItem) -> dict[str, Any]:
        """
        Normalize to article schema matching WAPOW's rich content model.
        """
        now = datetime.utcnow()

        # Extract values with fallbacks from raw_data (which is populated by html_extractor)
        raw = item.raw_data or {}
        headline = raw.get("title") or item.title
        sub_title = raw.get("description") or item.description
        author = raw.get("author") or item.author
        author_link = raw.get("author_link") or ""
        publisher = raw.get("publisher") or item.source_name
        publish_date = raw.get("publish_date") or item.publish_date or now
        image_url = raw.get("image_url") or item.image_url

        content_elements = raw.get("content_elements")
        if not content_elements:
            content_elements = item.raw_data.get("content_elements") or []
        if not content_elements and (sub_title or headline):
            content_elements = [
                {
                    "type": "text",
                    "content": sub_title or headline,
                }
            ]

        # Capitalize categories for UI compatibility
        category_map = {
            "technology": "Technology",
            "sports": "Sports",
            "travel": "Travel",
            "style": "Style",
            "wellbeing": "Health",
            "arts-entertainment": "Arts & Entertainment",
            "business": "Business",
        }
        display_category = category_map.get(item.category.lower(), item.category.capitalize())

        sections = [{"name": display_category}]
        
        # Parse subcategories from tags if present in RSS entry
        tags = raw.get("tags", []) if isinstance(raw, dict) else []
        seen_sections = {display_category.lower()}
        for tag in tags:
            if isinstance(tag, dict) and tag.get("term"):
                term = tag.get("term").strip()
                if term and term.lower() not in seen_sections:
                    sections.append({"name": term})
                    seen_sections.add(term.lower())

        by_credits = []
        if author:
            author_credit = {"name": author}
            if author_link:
                author_credit["url"] = author_link
            by_credits.append(author_credit)

        return {
            "type": "story",
            "category": item.category,
            "taxonomy": {
                "primary_section": {
                    "name": display_category,
                },
                "sections": sections,
            },
            "headlines": {"basic": headline},
            "sub_title": sub_title,
            "description": {"basic": sub_title},
            "credits": {"by": by_credits},
            "publisher": publisher,
            "promo_items": {"basic": {"url": image_url}} if image_url else {},
            "canonical_url": item.url,
            "publish_date": publish_date,
            "created_date": now,
            "isActive": True,
            "content_elements": content_elements,
            "_scraper_meta": {
                "source": item.source_name,
                "source_type": item.source_type,
                "publisher": publisher,
                "scraped_at": now,
                "url_hash": self._hash_url(item.url),
            },
        }

    def _hash_url(self, url: str) -> str:
        """Generate a hash of the URL for deduplication."""
        return hashlib.sha256(url.encode()).hexdigest()[:16]
