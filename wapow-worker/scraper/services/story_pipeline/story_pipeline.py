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
        self.api_key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()

    def storyboard(self, tree: DocumentTree, min_slides: int, max_slides: int) -> Optional[Dict[str, Any]]:
        """
        Stage 1: Narrative Storyboarding.
        Asks Gemini to segment the article into between min_slides and max_slides beats,
        providing both a short and long summary version of each beat for layout flexibility.
        """
        if not self.api_key:
            logger.warning("No Gemini API key available for StoryPipeline storyboard stage.")
            return None

        prompt = f"""You are an expert editor creating a mobile visual story (like Instagram/Snapchat Stories) from a news article.
Your task is to summarize the article into between {min_slides} and {max_slides} sequential narrative segments (beats) that explain the entire story.
Determine the optimal number of segments (within the range {min_slides} to {max_slides}) based on the actual complexity and length of the article.
If the article is simple or short, favor a smaller number of segments (even just {min_slides}) so that the story is concise and doesn't drag.
For each segment, you must provide both a short and long summary version to accommodate different slide layouts.

Output a JSON object with:
1. "segments": A list of the generated segment objects. Each segment object MUST contain:
   - "key_phrases": A list of 2-3 unique key phrases or keyword groups that are highly specific to this part of the article.
   - "short_summary": A highly concise summary of this segment. Keep it strictly MAXIMUM 120 characters (a single short sentence).
   - "long_summary": A detailed, descriptive summary of this segment. Keep it strictly between 250 and 450 characters (3-4 sentences) to explain the segment fully.
2. "takeaways": A list of 3-5 short bullet points summarizing the key takeaways of the whole article.

TITLE:
{tree.title}

DESCRIPTION:
{tree.description}

ARTICLE_BODY:
{tree.get_plaintext()}
"""

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
                                    "long_summary": {"type": "string"}
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
            logger.info(f"Calling Gemini to storyboard dynamic segments ({min_slides}-{max_slides}) for: {tree.title}")
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
                logger.error(f"JSON Decode Error in StoryPipeline storyboard: {jde}\nRaw text:\n{cleaned_text}")
                return None
        except Exception as e:
            logger.error(f"Error in StoryPipeline storyboard: {e}")
            return None

    def _find_best_block_match(self, tree: DocumentTree, key_phrases: List[str], segment_text: str) -> int:
        """Helper to find the sequential index of the text block that best matches this narrative beat."""
        best_idx = 0
        best_score = 0

        # Compile list of text blocks with content
        text_blocks = [(idx, b) for idx, b in enumerate(tree.blocks) if b.type in ("text", "header")]
        if not text_blocks:
            return 0

        segment_words = set(segment_text.lower().split())
        phrase_words = set()
        for phrase in key_phrases:
            phrase_words.update(phrase.lower().split())

        for idx, block in text_blocks:
            block_content_lower = block.content.lower()
            
            # Simple keyword matching score
            score = 0
            # 1. Check for key phrase match
            for word in phrase_words:
                if word in block_content_lower:
                    score += 5
            # 2. Check word overlap with the segment summary
            for word in segment_words:
                if len(word) > 3 and word in block_content_lower:
                    score += 1

            if score > best_score:
                best_score = score
                best_idx = idx

        return best_idx

    def align_media(self, tree: DocumentTree, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Stage 2: Contextual Media Alignment.
        Maps each storyboard segment to a video or an image in the DocumentTree using spatial proximity heuristics.
        """
        aligned_segments = []
        used_images = set()
        used_videos = set()

        for segment in segments:
            key_phrases = segment.get("key_phrases") or []
            short_summary = segment.get("short_summary") or ""
            long_summary = segment.get("long_summary") or ""
            
            # Find closest matching text block index in tree
            match_block_idx = self._find_best_block_match(tree, key_phrases, short_summary or long_summary)
            
            # 1. Prioritize scanning for adjacent videos in original layout
            matched_video = tree.get_adjacent_video(match_block_idx, max_distance=4)
            if matched_video and matched_video["url"] not in used_videos:
                used_videos.add(matched_video["url"])
                aligned_segments.append({
                    "short_summary": short_summary,
                    "long_summary": long_summary,
                    "video_url": matched_video["url"],
                    "embed_code": matched_video["embed_code"],
                    "image_url": None,
                    "focal_point": None,
                })
                continue

            # 2. Fallback to scanning for adjacent image (with focal point)
            matched_image_data = tree.get_adjacent_image_with_focal(match_block_idx, max_distance=4)
            matched_image = None
            focal_point = None
            if matched_image_data and matched_image_data["url"] not in used_images:
                matched_image = matched_image_data["url"]
                focal_point = matched_image_data.get("focal_point")
                used_images.add(matched_image)
                
            aligned_segments.append({
                "short_summary": short_summary,
                "long_summary": long_summary,
                "video_url": None,
                "embed_code": None,
                "image_url": matched_image,
                "focal_point": focal_point,
            })

        # Fallback 1: If no media was matched at all, try to assign the promo_image to the first slide
        has_any_media = bool(used_images) or bool(used_videos)
        if not has_any_media and tree.promo_image and aligned_segments:
            aligned_segments[0]["image_url"] = tree.promo_image
            aligned_segments[0]["focal_point"] = tree.promo_image_focal_point
            used_images.add(tree.promo_image)

        # Fallback 2: Assign remaining unused videos to segments without media
        all_doc_videos = tree.get_videos()
        for vid in all_doc_videos:
            if vid["url"] not in used_videos:
                # Find first segment without media and assign it
                for seg in aligned_segments:
                    if not seg["video_url"] and not seg["image_url"]:
                        seg["video_url"] = vid["url"]
                        seg["embed_code"] = vid["embed_code"]
                        used_videos.add(vid["url"])
                        break

        # Fallback 3: Assign remaining unused images to segments without media
        all_image_blocks = [b for b in tree.blocks if b.type == "image" and b.url]
        for block in all_image_blocks:
            if block.url not in used_images:
                # Find the first segment without media and assign it
                for seg in aligned_segments:
                    if not seg["video_url"] and not seg["image_url"]:
                        seg["image_url"] = block.url
                        seg["focal_point"] = block.focal_point
                        used_images.add(block.url)
                        break

        return aligned_segments

    def refine(self, aligned_segments: List[Dict[str, Any]], takeaways: List[str], tree: DocumentTree) -> List[Dict[str, Any]]:
        """
        Stage 3: Layout Refinement.
        Selects the appropriate summary version based on visual layout constraints and outputs the final slides list.
        """
        pages = []
        for seg in aligned_segments:
            img_url = seg.get("image_url")
            vid_url = seg.get("video_url")
            embed_code = seg.get("embed_code")
            focal_point = seg.get("focal_point")
            
            # Select appropriate content based on layout constraints (with video vs with image vs text-only)
            if vid_url:
                text_content = seg.get("short_summary") or ""
                # Enforce safety limits
                if len(text_content) > 120:
                    text_content = text_content[:117] + "..."
                page_content = [
                    {"type": "text", "content": text_content},
                    {"type": "video", "content_url": vid_url, "embed_code": embed_code or ""}
                ]
            elif img_url:
                text_content = seg.get("short_summary") or ""
                # Enforce safety limits
                if len(text_content) > 120:
                    text_content = text_content[:117] + "..."
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
                # Enforce bounds
                if len(text_content) > 500:
                    text_content = text_content[:497] + "..."
                page_content = [
                    {"type": "text", "content": text_content}
                ]
                
            pages.append({
                "page_type": "content",
                "content": page_content
            })

        # Format takeaways overview slide
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
        """Orchestrate the 3-stage visual slides generation flow."""
        # Determine number of content slides (beats) adaptively based on word count
        word_count = len(tree.get_plaintext().split())
        if word_count < 150:
            min_slides, max_slides = 1, 2
        elif word_count < 600:
            min_slides, max_slides = 2, 4
        else:
            min_slides, max_slides = 3, 5

        # Stage 1: Storyboard
        storyboard_data = self.storyboard(tree, min_slides, max_slides)
        if not storyboard_data:
            return None

        segments = storyboard_data.get("segments") or []
        takeaways = storyboard_data.get("takeaways") or []

        # Stage 2: Media Alignment
        aligned_segments = self.align_media(tree, segments)

        # Stage 3: Refine Layout
        pages = self.refine(aligned_segments, takeaways, tree)
        return pages
