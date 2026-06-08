"""YouTube Data API v3 scraper."""

import logging
from datetime import datetime
from typing import Optional

from scraper.scrapers.base import BaseScraper, ScrapedItem
from scraper.models.source import YouTubeSource
from scraper.config import settings

logger = logging.getLogger(__name__)


class YouTubeScraper(BaseScraper):
    """Scraper for YouTube channels and playlists using the Data API v3."""

    def __init__(self, source: YouTubeSource):
        """
        Initialize YouTube scraper.

        Args:
            source: YouTube source configuration
        """
        super().__init__(source.name, "youtube")
        self.source = source
        self.category = source.category
        self.channel_id = source.channel_id
        self.playlist_id = source.playlist_id
        self.max_results = source.max_results
        self._youtube = None

    def _init_client(self):
        """Initialize YouTube API client."""
        if not settings.youtube_api_key:
            raise ValueError("YOUTUBE_API_KEY not configured")

        from googleapiclient.discovery import build

        self._youtube = build(
            "youtube", "v3", developerKey=settings.youtube_api_key, cache_discovery=False
        )

    async def scrape(self) -> list[ScrapedItem]:
        """
        Fetch videos from YouTube channel or playlist.

        Returns:
            List of scraped video items
        """
        if not settings.youtube_api_key:
            logger.warning(f"YouTube API key not set, skipping {self.source.name}")
            return []

        try:
            self._init_client()

            if self.playlist_id:
                videos = self._fetch_playlist_videos()
            elif self.channel_id:
                videos = self._fetch_channel_videos()
            else:
                logger.error(f"No channel_id or playlist_id for {self.source.name}")
                return []

            items = []
            for video in videos:
                item = self._parse_video(video)
                if item:
                    items.append(item)

            logger.info(f"Scraped {len(items)} videos from YouTube: {self.source.name}")
            return items

        except Exception as e:
            logger.error(f"Error scraping YouTube {self.source.name}: {e}")
            return []

    def _fetch_channel_videos(self) -> list[dict]:
        """Fetch recent videos from a channel."""
        # First, get the channel's uploads playlist
        channel_response = (
            self._youtube.channels()
            .list(part="contentDetails", id=self.channel_id)
            .execute()
        )

        if not channel_response.get("items"):
            logger.warning(f"Channel not found: {self.channel_id}")
            return []

        uploads_playlist_id = channel_response["items"][0]["contentDetails"][
            "relatedPlaylists"
        ]["uploads"]

        return self._fetch_playlist_videos(uploads_playlist_id)

    def _fetch_playlist_videos(self, playlist_id: Optional[str] = None) -> list[dict]:
        """Fetch videos from a playlist."""
        playlist_id = playlist_id or self.playlist_id

        # Get playlist items
        playlist_response = (
            self._youtube.playlistItems()
            .list(
                part="snippet,contentDetails",
                playlistId=playlist_id,
                maxResults=min(self.max_results, 50),
            )
            .execute()
        )

        items = playlist_response.get("items", [])
        if not items:
            return []

        # Get video details (duration, etc.)
        video_ids = [item["contentDetails"]["videoId"] for item in items]
        videos_response = (
            self._youtube.videos()
            .list(part="snippet,contentDetails,statistics", id=",".join(video_ids))
            .execute()
        )

        return videos_response.get("items", [])

    def _parse_video(self, video: dict) -> Optional[ScrapedItem]:
        """Parse a YouTube video into a ScrapedItem."""
        try:
            snippet = video.get("snippet", {})
            content_details = video.get("contentDetails", {})
            video_id = video.get("id", "")

            if not video_id or not snippet.get("title"):
                return None

            # Parse duration (ISO 8601 format: PT1H2M3S)
            duration = self._parse_duration(content_details.get("duration", ""))

            # Parse publish date
            publish_date = None
            published_at = snippet.get("publishedAt")
            if published_at:
                try:
                    publish_date = datetime.fromisoformat(
                        published_at.replace("Z", "+00:00")
                    )
                except ValueError:
                    pass

            # Get best thumbnail
            thumbnails = snippet.get("thumbnails", {})
            image_url = (
                thumbnails.get("maxres", {}).get("url")
                or thumbnails.get("high", {}).get("url")
                or thumbnails.get("medium", {}).get("url")
                or thumbnails.get("default", {}).get("url")
                or ""
            )

            return self.create_item(
                url=f"https://www.youtube.com/watch?v={video_id}",
                title=snippet.get("title", ""),
                description=snippet.get("description", "")[:500],
                author=snippet.get("channelTitle", ""),
                image_url=image_url,
                publish_date=publish_date,
                category=self.category,
                content_type="video",
                duration=duration,
                raw_data={
                    "video_id": video_id,
                    "channel_id": snippet.get("channelId"),
                    "channel_title": snippet.get("channelTitle"),
                    "tags": snippet.get("tags", []),
                    "view_count": video.get("statistics", {}).get("viewCount"),
                    "like_count": video.get("statistics", {}).get("likeCount"),
                },
            )

        except Exception as e:
            logger.warning(f"Error parsing YouTube video: {e}")
            return None

    def _parse_duration(self, duration_str: str) -> Optional[int]:
        """Parse ISO 8601 duration to seconds."""
        if not duration_str:
            return None

        import re

        match = re.match(
            r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration_str
        )
        if not match:
            return None

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)

        return hours * 3600 + minutes * 60 + seconds
