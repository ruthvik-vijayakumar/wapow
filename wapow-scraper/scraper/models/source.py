"""Source configuration models."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """Type of content source."""

    RSS = "rss"
    WEB = "web"
    YOUTUBE = "youtube"
    SPOTIFY = "spotify"


class BaseSource(BaseModel):
    """Base source configuration."""

    name: str
    enabled: bool = True
    category: str = "technology"


class RSSSource(BaseSource):
    """RSS feed source configuration."""

    type: SourceType = SourceType.RSS
    url: str


class WebSource(BaseSource):
    """Web scraping source configuration."""

    type: SourceType = SourceType.WEB
    url: str
    selectors: dict[str, str] = Field(
        default_factory=lambda: {
            "articles": "article",
            "title": "h1, h2, .title",
            "description": "p, .description, .excerpt",
            "image": "img",
            "link": "a",
            "author": ".author, .byline",
            "date": "time, .date, .published",
        }
    )
    use_playwright: bool = False  # Set True for JS-heavy sites


class YouTubeSource(BaseSource):
    """YouTube channel/playlist source configuration."""

    type: SourceType = SourceType.YOUTUBE
    channel_id: Optional[str] = None
    playlist_id: Optional[str] = None
    max_results: int = 10


class SpotifySource(BaseSource):
    """Spotify podcast source configuration."""

    type: SourceType = SourceType.SPOTIFY
    show_id: str
    max_episodes: int = 10


class SourceConfig(BaseModel):
    """Complete source configuration loaded from YAML."""

    rss: list[RSSSource] = Field(default_factory=list)
    web: list[WebSource] = Field(default_factory=list)
    youtube: list[YouTubeSource] = Field(default_factory=list)
    spotify: list[SpotifySource] = Field(default_factory=list)
