"""Content normalizer to transform scraped items to MongoDB schemas."""

import hashlib
from datetime import datetime
from typing import Any

from scraper.scrapers.base import ScrapedItem
from scraper.config import ARTICLES_COLLECTION, VIDEO_COLLECTION, PODCAST_COLLECTION


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
        if item.content_type == "video":
            return VIDEO_COLLECTION, self._normalize_video(item)
        elif item.content_type == "podcast":
            return PODCAST_COLLECTION, self._normalize_podcast(item)
        else:
            return ARTICLES_COLLECTION, self._normalize_article(item)

    def _normalize_article(self, item: ScrapedItem) -> dict[str, Any]:
        """
        Normalize to article schema matching _transform_content_item.

        Schema fields:
        - category: technology|sports|travel|style|wellbeing
        - headlines.basic: title
        - description.basic: description
        - credits.by: author list
        - promo_items.basic.url: image URL
        - canonical_url: article URL
        - publish_date: datetime
        - created_date: datetime
        - isActive: True
        - content_elements: article body paragraphs and elements
        - _scraper_meta: scraper metadata
        """
        now = datetime.utcnow()

        content_elements = item.raw_data.get("content_elements") or []
        if not content_elements and (item.description or item.title):
            content_elements = [
                {
                    "type": "text",
                    "content": item.description or item.title,
                }
            ]

        # Capitalize categories for UI compatibility
        category_map = {
            "technology": "Technology",
            "sports": "Sports",
            "travel": "Travel",
            "style": "Style",
            "wellbeing": "Health",
        }
        display_category = category_map.get(item.category.lower(), item.category.capitalize())

        sections = [{"name": display_category}]
        
        # Parse subcategories from tags if present in RSS entry
        tags = item.raw_data.get("tags", []) if isinstance(item.raw_data, dict) else []
        seen_sections = {display_category.lower()}
        for tag in tags:
            if isinstance(tag, dict) and tag.get("term"):
                term = tag.get("term").strip()
                if term and term.lower() not in seen_sections:
                    sections.append({"name": term})
                    seen_sections.add(term.lower())

        return {
            "type": "story",
            "category": item.category,
            "taxonomy": {
                "primary_section": {
                    "name": display_category,
                },
                "sections": sections,
            },
            "headlines": {"basic": item.title},
            "description": {"basic": item.description},
            "credits": {"by": [{"name": item.author}] if item.author else []},
            "promo_items": {"basic": {"url": item.image_url}} if item.image_url else {},
            "canonical_url": item.url,
            "publish_date": item.publish_date or now,
            "created_date": now,
            "isActive": True,
            "content_elements": content_elements,
            "_scraper_meta": {
                "source": item.source_name,
                "source_type": item.source_type,
                "scraped_at": now,
                "url_hash": self._hash_url(item.url),
            },
        }

    def _normalize_video(self, item: ScrapedItem) -> dict[str, Any]:
        """
        Normalize to video schema matching _transform_video_item.

        Schema fields:
        - tracking.page_title: title
        - tracking.video_section: category
        - tracking.video_category: category
        - tracking.av_name: description
        - promo_image.url: thumbnail URL
        - content_id: unique ID
        - canonical_url: video URL
        - duration: duration in seconds
        - isActive: True
        - _scraper_meta: scraper metadata
        """
        now = datetime.utcnow()
        content_id = self._generate_content_id(item.url)

        return {
            "tracking": {
                "page_title": item.title,
                "video_section": item.category,
                "video_category": item.category,
                "av_name": item.description,
            },
            "promo_image": {"url": item.image_url} if item.image_url else {},
            "content_id": content_id,
            "canonical_url": item.url,
            "duration": item.duration,
            "publish_date": item.publish_date or now,
            "created_date": now,
            "isActive": True,
            "_scraper_meta": {
                "source": item.source_name,
                "source_type": item.source_type,
                "scraped_at": now,
                "url_hash": self._hash_url(item.url),
                "raw_data": item.raw_data,
            },
        }

    def _normalize_podcast(self, item: ScrapedItem) -> dict[str, Any]:
        """
        Normalize to podcast schema matching _transform_podcast_item.

        Schema fields:
        - title: episode title
        - additional_properties.page_title: title
        - additional_properties.description: description
        - additional_properties.lead_art.url: image URL
        - additional_properties.series_meta.name: show name
        - duration: duration in seconds
        - isActive: True
        - _scraper_meta: scraper metadata
        """
        now = datetime.utcnow()

        # Use author field as show name for podcasts
        show_name = item.author or item.source_name

        return {
            "title": item.title,
            "additional_properties": {
                "page_title": item.title,
                "description": item.description,
                "lead_art": {"url": item.image_url} if item.image_url else {},
                "series_meta": {"name": show_name},
            },
            "canonical_url": item.url,
            "duration": item.duration,
            "publish_date": item.publish_date or now,
            "created_date": now,
            "isActive": True,
            "_scraper_meta": {
                "source": item.source_name,
                "source_type": item.source_type,
                "scraped_at": now,
                "url_hash": self._hash_url(item.url),
                "raw_data": item.raw_data,
            },
        }

    def _hash_url(self, url: str) -> str:
        """Generate a hash of the URL for deduplication."""
        return hashlib.sha256(url.encode()).hexdigest()[:16]

    def _generate_content_id(self, url: str) -> str:
        """Generate a unique content ID from the URL."""
        return f"scraped_{hashlib.sha256(url.encode()).hexdigest()[:12]}"
