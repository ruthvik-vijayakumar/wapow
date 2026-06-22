"""Podcast scraper using Podcast Index API search and RSS parsing."""

import logging
import asyncio
from datetime import datetime
import time
from typing import Optional
import aiohttp
import feedparser

from scraper.scrapers.base import BaseScraper, ScrapedItem

logger = logging.getLogger(__name__)

# Map app categories to search terms for the keyless Podcast Index API
CATEGORY_SEARCH_MAP = {
    "sports": "sports",
    "style": "fashion style",
    "technology": "technology",
    "wellbeing": "wellness wellbeing",
    "travel": "travel guide"
}


class PodcastScraper(BaseScraper):
    """Scraper for fetching podcasts and episodes from Podcast Index and RSS feeds."""

    def __init__(self):
        super().__init__("Podcast Index", "podcast_index")
        self.search_url = "https://api.podcastindex.org/search"
        self.user_agent = "WAPOWPodcastApp/1.0"

    async def scrape(self) -> list[ScrapedItem]:
        """
        Iterate over categories, search for podcasts, parse RSS feeds, and return episodes.
        
        Returns:
            List of ScrapedItem containing podcast episodes.
        """
        all_episodes = []
        for category, query in CATEGORY_SEARCH_MAP.items():
            try:
                logger.info(f"Searching Podcast Index for category '{category}' with query '{query}'")
                feeds = await self._search_podcasts(query)
                logger.info(f"Found {len(feeds)} feeds for category '{category}'")

                # Parse top 2 feeds for each category
                for feed_info in feeds[:2]:
                    feed_url = feed_info.get("feedUrl")
                    if not feed_url:
                        continue
                    
                    logger.info(f"Parsing podcast feed: {feed_info.get('collectionName')} -> {feed_url}")
                    episodes = await self._parse_feed_episodes(feed_url, feed_info, category)
                    all_episodes.extend(episodes)
                    
            except Exception as e:
                logger.error(f"Error scraping podcasts for category '{category}': {e}")
                
        return all_episodes

    async def _search_podcasts(self, query: str) -> list[dict]:
        """Search the Podcast Index keyless search API."""
        try:
            params = {"term": query}
            headers = {"User-Agent": self.user_agent}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.search_url,
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status != 200:
                        logger.error(f"Podcast Index search failed with status {response.status}")
                        return []
                    data = await response.json()
                    return data.get("results") or []
        except Exception as e:
            logger.error(f"Error querying Podcast Index search API: {e}")
            return []

    async def _parse_feed_episodes(self, feed_url: str, feed_info: dict, category: str) -> list[ScrapedItem]:
        """Fetch and parse the episodes from the podcast RSS feed."""
        episodes = []
        try:
            # Check robots.txt and wait for rate limit
            if not await self.can_scrape(feed_url):
                logger.warning(f"robots.txt disallows scraping podcast feed: {feed_url}")
                return []
                
            await self.wait_for_rate_limit(feed_url)
            
            headers = {"User-Agent": self.user_agent}
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    feed_url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to fetch podcast feed {feed_url}: {response.status}")
                        return []
                    content = await response.text()
            
            # Parse feed in thread executor to prevent event loop blocking
            feed = await asyncio.to_thread(feedparser.parse, content)
            
            if feed.bozo and not feed.entries:
                logger.warning(f"Error parsing podcast feed XML {feed_url}: {feed.bozo_exception}")
                return []
                
            # Default artwork/thumbnail
            podcast_image = feed_info.get("artworkUrl600") or feed_info.get("artworkUrl100") or ""
            if not podcast_image and "image" in feed.feed:
                podcast_image = feed.feed.image.get("href") or ""
                
            podcast_author = feed_info.get("artistName") or feed.feed.get("author") or "Unknown Podcast"
            podcast_title = feed_info.get("collectionName") or feed.feed.get("title") or "Podcast"

            # Parse top 5 episodes
            for entry in feed.entries[:5]:
                # Locate audio enclosure URL
                audio_url = ""
                duration_sec = None
                if "enclosures" in entry:
                    for enc in entry.enclosures:
                        if enc.get("type", "").startswith("audio/"):
                            audio_url = enc.get("href") or ""
                            # Length can sometimes contain duration in seconds
                            try:
                                duration_sec = int(enc.get("length", 0))
                            except Exception:
                                pass
                            break
                            
                if not audio_url:
                    continue  # Skip episodes without audio
                    
                # Title & description
                title = entry.get("title", "").strip() or "Untitled Episode"
                description = entry.get("summary") or entry.get("description") or ""
                if description:
                    from bs4 import BeautifulSoup
                    description = BeautifulSoup(description, "lxml").get_text()[:600]

                # Publish Date
                publish_date = None
                if "published_parsed" in entry and entry.published_parsed:
                    publish_date = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                elif "updated_parsed" in entry and entry.updated_parsed:
                    publish_date = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
                else:
                    publish_date = datetime.utcnow()

                # Episode specific image
                episode_image = podcast_image
                if "image" in entry:
                    episode_image = entry.image.get("href") or podcast_image

                # Construct raw_data dictionary matching the expected structure
                raw_data = {
                    "audioUrl": audio_url,
                    "imageUrl": episode_image,
                    "thumbnail": episode_image,
                    "audio_article_raw_url": audio_url,
                    "author": {
                        "name": podcast_author,
                        "username": "@" + "".join([c for c in podcast_author.lower() if c.isalnum()]),
                        "avatar": podcast_image or "https://picsum.photos/50/50?random=podcast"
                    },
                    "additional_properties": {
                        "audio_article_raw_url": audio_url,
                        "description": description,
                        "lead_art": {
                            "url": episode_image
                        },
                        "page_title": title
                    },
                    "source": {
                        "name": podcast_title,
                        "source_type": "podcast",
                        "system": "podcast_index"
                    }
                }

                item = self.create_item(
                    url=entry.get("link") or feed_url,
                    title=title,
                    description=description,
                    author=podcast_author,
                    image_url=episode_image,
                    publish_date=publish_date,
                    category=category,
                    content_type="podcast",
                    duration=duration_sec,
                    raw_data=raw_data
                )
                episodes.append(item)
                
        except Exception as e:
            logger.error(f"Error parsing episodes from feed {feed_url}: {e}")
            
        return episodes
