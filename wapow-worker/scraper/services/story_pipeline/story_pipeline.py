from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
import logging
from typing import Any, Dict, List, Optional

from .base import BasePipeline, DocumentTree

logger = logging.getLogger(__name__)


class StoryPipeline(BasePipeline):
    """Concrete pipeline to segment an article and format it into visual StoryView slides."""

    def __init__(self, api_key: Optional[str] = None):
        from scraper.config import settings
        self.api_key = (api_key or settings.gemini_api_key or os.getenv("GEMINI_API_KEY", "")).strip()

    def storyboard_single(self, tree: DocumentTree, unique_images: List[str]) -> Optional[Dict[str, Any]]:
        """
        Stage 1: Narrative Storyboarding (Single/No Image Case).
        Generates exactly one content segment focusing strictly on the central topic, stripping out unrelated details.
        """
        if not self.api_key:
            logger.warning("No Gemini API key available for StoryPipeline storyboard_single stage.")
            return None

        img_url = unique_images[0] if unique_images else None
        prompt = f"""You are an expert editor creating a mobile visual story (like Instagram/Snapchat Stories) from a news article.
Your task is to summarize the article into EXACTLY ONE content segment.

CONTENT INSTRUCTIONS:
- The summary MUST focus strictly and only on the central topic of the article.
- Strip off any unrelated, side, or tangential information. Keep it highly focused on the core theme.
- The summary must be a substantial, self-contained narrative beat — not a thin sentence.

For this segment, you must provide both a short and long summary version to accommodate different slide layouts.

Output a JSON object with:
1. "segments": A list containing EXACTLY ONE segment object. The segment object MUST contain:
   - "key_phrases": A list of 2-3 unique key phrases or keywords specific to the central topic.
   - "short_summary": A concise summary of the central topic. Keep it strictly between 90 and 200 characters (1-2 punchy sentences).
   - "long_summary": A detailed, descriptive summary of the central topic. Keep it strictly between 220 and 360 characters (2-3 sentences) to explain the core topic fully.
   - "suggested_image_url": The image URL provided below, or null if none is available.
2. "takeaways": A list of 3-5 short bullet points summarizing the key takeaways of the article (for metadata/fallback purposes).

IMAGE PROVIDED:
{img_url}

TITLE:
{tree.title}

DESCRIPTION:
{tree.description}

ARTICLE_BODY:
{tree.get_plaintext()}
"""
        logger.info(f"Calling Gemini to storyboard single-segment central topic for: {tree.title}")
        return self._call_gemini_api(prompt)

    def storyboard_multiple(self, tree: DocumentTree, target_images: List[str]) -> Optional[Dict[str, Any]]:
        """
        Stage 1: Narrative Storyboarding (Multiple Images Case).
        Generates exactly one content segment per unique image.
        """
        if not self.api_key:
            logger.warning("No Gemini API key available for StoryPipeline storyboard_multiple stage.")
            return None

        prompt = f"""You are an expert editor creating a mobile visual story (like Instagram/Snapchat Stories) from a news article.
Your task is to storyboard the article into EXACTLY {len(target_images)} content segments, corresponding to the {len(target_images)} available images in order.

CONTENT INSTRUCTIONS:
- You must generate exactly {len(target_images)} segments.
- Each segment corresponds to the image at the same index from the AVAILABLE IMAGES list.
- The text (both short and long summaries) for each segment must be highly relevant and appropriate to the specific image shown on that slide.
- Together, the segments must explain the narrative progression of the article.
- Each segment must be a substantial, self-contained narrative beat.

Output a JSON object with:
1. "segments": A list containing EXACTLY {len(target_images)} segment objects. Each segment object MUST contain:
   - "key_phrases": A list of 2-3 unique key phrases or keywords specific to this segment.
   - "short_summary": A concise summary of this segment. Keep it strictly between 90 and 200 characters (1-2 punchy sentences).
   - "long_summary": A detailed, descriptive summary of this segment. Keep it strictly between 220 and 360 characters (2-3 sentences).
   - "suggested_image_url": The exact image URL from the AVAILABLE IMAGES list corresponding to this segment's index.
2. "takeaways": A list of 3-5 short bullet points summarizing the key takeaways of the whole article.

AVAILABLE IMAGES (in sequential order):
{json.dumps(target_images, indent=2)}

TITLE:
{tree.title}

DESCRIPTION:
{tree.description}

ARTICLE_BODY:
{tree.get_plaintext()}
"""
        logger.info(f"Calling Gemini to storyboard {len(target_images)} segments for multi-image story: {tree.title}")
        return self._call_gemini_api(prompt)

    def _call_gemini_api(self, prompt: str) -> Optional[Dict[str, Any]]:
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "object",
                    "properties": {
                        "segments": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "key_phrases": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "short_summary": {"type": "string"},
                                    "long_summary": {"type": "string"},
                                    "suggested_image_url": {"type": "string"}
                                },
                                "required": ["key_phrases", "short_summary", "long_summary"]
                            }
                        },
                        "takeaways": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["segments", "takeaways"]
                }
            }
        }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                raw_data = json.loads(resp.read().decode("utf-8"))

            candidates = raw_data.get("candidates") or []
            if not candidates:
                return None

            text_content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            if not text_content:
                return None

            cleaned_text = text_content.strip()
            if cleaned_text.startswith("```"):
                lines = cleaned_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned_text = "\n".join(lines).strip()

            try:
                return json.loads(cleaned_text)
            except json.JSONDecodeError as jde:
                logger.error(f"JSON Decode Error in StoryPipeline: {jde}\nRaw text:\n{cleaned_text}")
                return None
        except Exception as e:
            logger.error(f"Error in StoryPipeline API call: {e}")
            return None

    def align_media_new(self, tree: DocumentTree, segments: List[Dict[str, Any]], unique_images: List[str]) -> List[Dict[str, Any]]:
        """
        Stage 2: Contextual Media Alignment.
        Maps each storyboard segment to its corresponding matched image.
        If suggested_image_url is null or not valid, falls back to the unique image at that index.
        """
        aligned_segments = []
        for i, segment in enumerate(segments):
            short_summary = segment.get("short_summary") or ""
            long_summary = segment.get("long_summary") or ""
            suggested_img = segment.get("suggested_image_url")
            
            # Index fallback if the model returned null
            if not suggested_img and i < len(unique_images):
                suggested_img = unique_images[i]

            # Find focal point from the SemanticBlock if it exists
            focal_point = None
            if suggested_img:
                for block in tree.blocks:
                    if block.type == "image" and block.url == suggested_img:
                        focal_point = block.focal_point
                        break
                if not focal_point and suggested_img == tree.promo_image:
                    focal_point = tree.promo_image_focal_point

            aligned_segments.append({
                "short_summary": short_summary,
                "long_summary": long_summary,
                "image_url": suggested_img,
                "focal_point": focal_point,
            })

        return aligned_segments

    def refine_new(self, aligned_segments: List[Dict[str, Any]], takeaways: List[str], tree: DocumentTree) -> List[Dict[str, Any]]:
        """
        Stage 3: Layout Refinement.
        Formats the segments into content and overview slides.
        """
        pages = []
        for seg in aligned_segments:
            img_url = seg.get("image_url")
            focal_point = seg.get("focal_point")
            
            if img_url:
                text_content = seg.get("short_summary") or ""
                image_item: Dict[str, Any] = {"type": "image", "content_url": img_url}
                if focal_point:
                    image_item["focal_point"] = focal_point
                page_content = [
                    {"type": "text", "content": text_content},
                    image_item,
                ]
            else:
                text_content = seg.get("long_summary") or ""
                if not text_content:
                    text_content = seg.get("short_summary") or ""
                page_content = [
                    {"type": "text", "content": text_content}
                ]
                
            pages.append({
                "page_type": "content",
                "content": page_content
            })

        # Overview/takeaways slide only when there are multiple content slides to summarize.
        # For a single-slide (short) article, skip it entirely.
        if len(pages) >= 2:
            if takeaways:
                takeaways_text = "\n".join(f"• {t.strip()}" for t in takeaways)
            else:
                takeaways_text = f"• {tree.title}"

            pages.append({
                "page_type": "overview",
                "content": [
                    {"type": "text", "content": takeaways_text}
                ]
            })

        return pages

    def execute(self, tree: DocumentTree) -> Optional[List[Dict[str, Any]]]:
        """Orchestrate the single/multiple images visual slides generation flow."""
        unique_images = tree.get_images()
        num_images = len(unique_images)
        logger.info(f"Starting StoryPipeline slide generation. Unique images: {num_images}")

        if num_images <= 1:
            # Stage 1: Single slide for central topic
            storyboard_data = self.storyboard_single(tree, unique_images)
        else:
            # Stage 1: One content slide per image, up to 5
            target_images = unique_images[:5]
            storyboard_data = self.storyboard_multiple(tree, target_images)

        if not storyboard_data:
            logger.warning("Storyboard generation returned no data.")
            return None

        segments = storyboard_data.get("segments") or []
        takeaways = storyboard_data.get("takeaways") or []

        # Stage 2: Contextual Media Alignment
        aligned_segments = self.align_media_new(tree, segments, unique_images)

        # Stage 3: Refine Layout (skip stitching to enforce strict image mapping)
        pages = self.refine_new(aligned_segments, takeaways, tree)
        return pages

    # ==========================================
    # ARCHIVED LEGACY CONVERSION WORKFLOW METHODS
    # ==========================================

    def storyboard(self, tree: DocumentTree, min_slides: int, max_slides: int) -> Optional[Dict[str, Any]]:
        """Archived legacy Stage 1 storyboard method."""
        if not self.api_key:
            return None
        images_data = []
        for b in tree.blocks:
            if b.type == "image" and b.url:
                images_data.append({"url": b.url, "caption": b.content or ""})
        if tree.promo_image and not any(img["url"] == tree.promo_image for img in images_data):
            images_data.append({"url": tree.promo_image, "caption": tree.title or ""})

        prompt = f"""Archived Legacy Prompt..."""
        # (Omitted legacy implementation details for brevity/archival reference only)
        return None

    def align_media(self, tree: DocumentTree, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Archived legacy Stage 2 align_media method."""
        return []

    def refine(self, aligned_segments: List[Dict[str, Any]], takeaways: List[str], tree: DocumentTree) -> List[Dict[str, Any]]:
        """Archived legacy Stage 3 refine method."""
        return []

    def stitch_segments(self, aligned_segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Archived legacy stitch_segments method."""
        return []

    def _find_best_block_match(self, tree: DocumentTree, key_phrases: List[str], segment_text: str) -> int:
        """Archived legacy block matcher helper."""
        return 0
