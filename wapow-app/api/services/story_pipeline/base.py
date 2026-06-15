from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field

from .analyzer import is_valid_article_image, _strip_html

logger = logging.getLogger(__name__)


class SemanticBlock(BaseModel):
    """Represents a structured block of content from the article."""
    type: str  # "text", "header", "image", "video"
    subtype: Optional[str] = None  # "blockquote", "list_item", etc.
    content: str  # Text content, header text, or image caption
    url: Optional[str] = None  # Image or video URL
    level: Optional[int] = None  # Header level (2-6)
    original_index: int  # Original sequential index in the document elements list


class DocumentTree(BaseModel):
    """Holds metadata and structured content blocks of a document."""
    title: str
    description: str
    author: str = ""
    author_link: str = ""
    publisher: str = ""
    publish_date: Optional[datetime] = None
    promo_image: str = ""
    blocks: List[SemanticBlock] = Field(default_factory=list)

    @classmethod
    def from_mongo_doc(cls, doc: dict) -> DocumentTree:
        """Parse article document from MongoDB into a structured DocumentTree."""
        # Extract title
        headlines = doc.get("headlines") or {}
        title = (headlines.get("basic") or doc.get("title") or "Article").strip()

        # Extract description
        desc_obj = doc.get("description")
        if isinstance(desc_obj, dict):
            description = _strip_html(desc_obj.get("basic") or "")
        else:
            description = _strip_html(str(desc_obj or ""))

        # Extract author & publisher metadata
        author = doc.get("author") or ""
        author_link = doc.get("author_link") or ""
        publisher = doc.get("publisher") or ""
        
        publish_date = doc.get("publish_date")
        if isinstance(publish_date, str):
            # Parse it if standard method is available
            try:
                from scraper.utils.html_extractor import parse_date_string as pds
                publish_date = pds(publish_date)
            except Exception:
                publish_date = None

        promo_image = doc.get("image_url") or doc.get("promo_image") or ""
        promo_items = doc.get("promo_items") or {}
        basic = promo_items.get("basic") or {}
        if isinstance(basic, dict) and basic.get("url"):
            promo_image = basic["url"]
        
        # Build SemanticBlocks list
        blocks: List[SemanticBlock] = []
        content_field = doc.get("content_elements") or doc.get("content") or []
        
        if isinstance(content_field, list):
            for idx, el in enumerate(content_field):
                if not isinstance(el, dict):
                    continue
                typ = (el.get("type") or "").lower()
                
                if typ in ("text", "raw_html"):
                    content = _strip_html(el.get("content") or el.get("text") or "")
                    if content:
                        blocks.append(SemanticBlock(
                            type="text",
                            subtype=el.get("subtype"),
                            content=content,
                            original_index=idx
                        ))
                elif typ == "header":
                    content = _strip_html(el.get("content") or el.get("text") or "")
                    if content:
                        blocks.append(SemanticBlock(
                            type="header",
                            content=content,
                            level=el.get("level") or 2,
                            original_index=idx
                        ))
                elif typ in ("image", "gallery"):
                    # Resolve URL
                    url = el.get("url") or el.get("content_url")
                    if not url:
                        ap = el.get("additional_properties") or {}
                        url = ap.get("fullSizeResizeUrl") or ap.get("url")
                    if url and isinstance(url, str) and url.startswith("http") and is_valid_article_image(url):
                        caption = _strip_html(el.get("caption") or el.get("content") or "")
                        blocks.append(SemanticBlock(
                            type="image",
                            content=caption,
                            url=url,
                            original_index=idx
                        ))
                elif typ == "video":
                    url = el.get("url") or el.get("content_url")
                    if url:
                        blocks.append(SemanticBlock(
                            type="video",
                            content=el.get("embed_code") or "",
                            url=url,
                            original_index=idx
                        ))
        elif isinstance(content_field, str) and content_field.strip():
            # If content is a flat string, split by paragraphs
            paragraphs = [p.strip() for p in content_field.split("\n\n") if p.strip()]
            for idx, p in enumerate(paragraphs):
                blocks.append(SemanticBlock(
                    type="text",
                    content=_strip_html(p),
                    original_index=idx
                ))

        # If we didn't find any content block, fallback to using the description
        if not blocks and description:
            blocks.append(SemanticBlock(
                type="text",
                content=description,
                original_index=0
            ))

        return cls(
            title=title,
            description=description,
            author=author,
            author_link=author_link,
            publisher=publisher,
            publish_date=publish_date,
            promo_image=promo_image,
            blocks=blocks
        )

    def get_plaintext(self) -> str:
        """Return the compiled clean plaintext of the entire document tree."""
        parts = []
        for b in self.blocks:
            if b.type in ("text", "header"):
                parts.append(b.content)
        return "\n\n".join(parts)

    def get_images(self) -> List[str]:
        """Return all valid unique image URLs in the document in sequential order."""
        urls = []
        seen = set()
        if self.promo_image and self.promo_image.startswith("http") and is_valid_article_image(self.promo_image):
            urls.append(self.promo_image)
            seen.add(self.promo_image)
        for b in self.blocks:
            if b.type == "image" and b.url and b.url not in seen:
                urls.append(b.url)
                seen.add(b.url)
        return urls

    def get_adjacent_image(self, block_index: int, max_distance: int = 3) -> Optional[str]:
        """
        Scan blocks sequentially before and after the target block_index to find the
        closest image URL within max_distance blocks.
        """
        num_blocks = len(self.blocks)
        for dist in range(1, max_distance + 1):
            # Check previous blocks
            prev_idx = block_index - dist
            if prev_idx >= 0:
                block = self.blocks[prev_idx]
                if block.type == "image" and block.url:
                    return block.url
            # Check next blocks
            next_idx = block_index + dist
            if next_idx < num_blocks:
                block = self.blocks[next_idx]
                if block.type == "image" and block.url:
                    return block.url
        return None

    def get_videos(self) -> List[dict]:
        """Return all valid unique videos in the document in sequential order."""
        videos = []
        seen = set()
        for b in self.blocks:
            if b.type == "video" and b.url and b.url not in seen:
                videos.append({
                    "url": b.url,
                    "embed_code": b.content
                })
                seen.add(b.url)
        return videos

    def get_adjacent_video(self, block_index: int, max_distance: int = 3) -> Optional[dict]:
        """
        Scan blocks sequentially before and after the target block_index to find the
        closest video block within max_distance blocks.
        """
        num_blocks = len(self.blocks)
        for dist in range(1, max_distance + 1):
            # Check previous blocks
            prev_idx = block_index - dist
            if prev_idx >= 0:
                block = self.blocks[prev_idx]
                if block.type == "video" and block.url:
                    return {"url": block.url, "embed_code": block.content}
            # Check next blocks
            next_idx = block_index + dist
            if next_idx < num_blocks:
                block = self.blocks[next_idx]
                if block.type == "video" and block.url:
                    return {"url": block.url, "embed_code": block.content}
        return None


class BasePipeline:
    """Abstract base class establishing the 3-stage generation pipeline workflow."""
    
    def storyboard(self, *args, **kwargs) -> Any:
        """Stage 1: Narrative Storyboarding (Segmentation)."""
        raise NotImplementedError("Storyboard stage must be implemented.")

    def align_media(self, *args, **kwargs) -> Any:
        """Stage 2: Contextual Media Alignment."""
        raise NotImplementedError("Align Media stage must be implemented.")

    def refine(self, *args, **kwargs) -> Any:
        """Stage 3: Layout Refinement & Formatting."""
        raise NotImplementedError("Refine stage must be implemented.")

    def execute(self, *args, **kwargs) -> Any:
        """Orchestrates the lifecycle of all stages sequentially."""
        raise NotImplementedError("Execute orchestration must be implemented.")
