"""Spotify Podcast API scraper using spotipy."""

import logging
from datetime import datetime
from typing import Optional

from scraper.scrapers.base import BaseScraper, ScrapedItem
from scraper.models.source import SpotifySource
from scraper.config import settings

logger = logging.getLogger(__name__)


class SpotifyScraper(BaseScraper):
    """Scraper for Spotify podcasts using the Web API."""

    def __init__(self, source: SpotifySource):
        """
        Initialize Spotify scraper.

        Args:
            source: Spotify source configuration
        """
        super().__init__(source.name, "spotify")
        self.source = source
        self.show_id = source.show_id
        self.max_episodes = source.max_episodes
        self._spotify = None

    def _init_client(self):
        """Initialize Spotify API client."""
        if not settings.spotify_client_id or not settings.spotify_client_secret:
            raise ValueError("Spotify credentials not configured")

        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials

        auth_manager = SpotifyClientCredentials(
            client_id=settings.spotify_client_id,
            client_secret=settings.spotify_client_secret,
        )
        self._spotify = spotipy.Spotify(auth_manager=auth_manager)

    async def scrape(self) -> list[ScrapedItem]:
        """
        Fetch podcast episodes from Spotify.

        Returns:
            List of scraped podcast items
        """
        if not settings.spotify_client_id or not settings.spotify_client_secret:
            logger.warning(f"Spotify credentials not set, skipping {self.source.name}")
            return []

        try:
            self._init_client()

            # Get show details
            show = self._spotify.show(self.show_id, market="US")
            if not show:
                logger.error(f"Show not found: {self.show_id}")
                return []

            show_name = show.get("name", "Unknown Show")
            show_image = ""
            if show.get("images"):
                show_image = show["images"][0].get("url", "")

            # Get episodes
            episodes_data = self._spotify.show_episodes(
                self.show_id, limit=min(self.max_episodes, 50), market="US"
            )

            items = []
            for episode in episodes_data.get("items", []):
                item = self._parse_episode(episode, show_name, show_image)
                if item:
                    items.append(item)

            logger.info(
                f"Scraped {len(items)} episodes from Spotify: {self.source.name}"
            )
            return items

        except Exception as e:
            logger.error(f"Error scraping Spotify {self.source.name}: {e}")
            return []

    def _parse_episode(
        self, episode: dict, show_name: str, show_image: str
    ) -> Optional[ScrapedItem]:
        """Parse a Spotify episode into a ScrapedItem."""
        try:
            episode_id = episode.get("id", "")
            if not episode_id:
                return None

            title = episode.get("name", "")
            if not title:
                return None

            # Get episode image or fall back to show image
            image_url = ""
            if episode.get("images"):
                image_url = episode["images"][0].get("url", "")
            if not image_url:
                image_url = show_image

            # Parse release date
            publish_date = None
            release_date = episode.get("release_date")
            if release_date:
                try:
                    # Spotify uses YYYY-MM-DD format
                    publish_date = datetime.strptime(release_date, "%Y-%m-%d")
                except ValueError:
                    try:
                        # Some may be just YYYY
                        publish_date = datetime.strptime(release_date, "%Y")
                    except ValueError:
                        pass

            # Duration is in milliseconds
            duration_ms = episode.get("duration_ms", 0)
            duration = duration_ms // 1000 if duration_ms else None

            # Get external URL
            external_urls = episode.get("external_urls", {})
            url = external_urls.get("spotify", f"https://open.spotify.com/episode/{episode_id}")

            return self.create_item(
                url=url,
                title=title,
                description=episode.get("description", "")[:500],
                author=show_name,
                image_url=image_url,
                publish_date=publish_date,
                category="podcast",
                content_type="podcast",
                duration=duration,
                raw_data={
                    "episode_id": episode_id,
                    "show_id": self.show_id,
                    "show_name": show_name,
                    "explicit": episode.get("explicit", False),
                    "language": episode.get("language"),
                    "html_description": episode.get("html_description"),
                },
            )

        except Exception as e:
            logger.warning(f"Error parsing Spotify episode: {e}")
            return None
