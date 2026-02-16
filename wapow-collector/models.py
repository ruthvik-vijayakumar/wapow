"""Pydantic models for the event collector."""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class EventPayload(BaseModel):
    """A single analytics event sent from the frontend."""

    event_type: str = Field(..., min_length=1, max_length=64)
    user_id: str = ""
    session_id: str = ""
    content_id: str = ""
    content_type: str = ""  # article, video, podcast, game
    category: str = ""
    timestamp: Optional[str] = None  # ISO-8601; server fills if missing
    properties: dict = Field(default_factory=dict)

    # Context (optional — server can enrich)
    referrer: str = ""


class CollectRequest(BaseModel):
    """Batch of events sent by the frontend SDK."""

    events: list[EventPayload] = Field(..., min_length=1, max_length=200)
