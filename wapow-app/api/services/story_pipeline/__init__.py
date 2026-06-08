"""Article → story slides pipeline (StoryView-compatible ai_summary)."""

from api.services.story_pipeline.service import (
    convert_article_to_story,
    preview_story_for_article,
)

__all__ = ["convert_article_to_story", "preview_story_for_article"]
