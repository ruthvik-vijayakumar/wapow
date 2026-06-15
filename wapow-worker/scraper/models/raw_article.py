"""Raw article model for database persistence before normalization."""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class RawArticle(BaseModel):
    """Represents a raw scraped article saved in the database before normalization."""

    source_name: str
    source_type: str
    url: str
    title: str
    description: str = ""
    author: str = ""
    image_url: str = ""
    publish_date: Optional[datetime] = None
    category: str = "technology"
    content_type: str = "article"
    duration: Optional[int] = None
    raw_data: dict[str, Any] = Field(default_factory=dict)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
