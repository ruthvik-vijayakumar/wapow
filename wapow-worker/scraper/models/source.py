"""Source configuration models."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """Type of content source."""

    RSS = "rss"
    WEB = "web"


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
    """Single web page source configuration."""

    type: SourceType = SourceType.WEB
    url: str
    use_playwright: bool = True


class SourceConfig(BaseModel):
    """Complete source configuration loaded from YAML."""

    rss: list[RSSSource] = Field(default_factory=list)
    web: list[WebSource] = Field(default_factory=list)
