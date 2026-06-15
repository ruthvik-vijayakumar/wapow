from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
import logging
from typing import Any, List, Dict, Optional

from .base import BasePipeline, DocumentTree, SemanticBlock

logger = logging.getLogger(__name__)


class StoryPipeline(BasePipeline):
    """Concrete pipeline to segment an article and format it into visual StoryView slides."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()

    def storyboard(self, tree: DocumentTree, n_slides: int) -> Optional[Dict[str, Any]]:
        """
        Stage 1: Narrative Storyboarding.
        Asks Gemini to segment the article into exactly n_slides beats,
        providing both a short and long summary version of each beat for layout flexibility.
        """
        if not self.api_key:
            logger.warning("No Gemini API key available for StoryPipeline storyboard stage.")
            return None

        # Collect available images with captions for LLM contextual matching
        images_data = []
        for block in tree.blocks:
            if block.type == "image" and block.url:
                images_data.append({
                    "url": block.url,
                    "caption": block.content or ""
                })
        
        # Include promo image if not already present
        if tree.promo_image and not any(img["url"] == tree.promo_image for img in images_data):
            images_data.insert(0, {
                "url": tree.promo_image,
                "caption": "Promo cover/featured image"
            })

        prompt = f"""You are an expert mobile editor. Your task is to storyboard a mobile visual story (like Instagram/Snapchat Stories) from a news article.
Distill the article into exactly {n_slides} sequential narrative segments that tell a compelling, progressive story.

CRITICAL INSTRUCTIONS FOR TEXT QUALITY:
1. DO NOT copy-paste sentences or paragraphs directly from the article body. Summarize and rewrite the content in a fresh, engaging, storytelling editor-curated voice.
2. Keep the narrative progression clear, logical, and flowing smoothly across the slides.
3. Avoid dry, blocky, or academic language. Write in a punchy, active, and interesting style.
4. "short_summary" must be a highly concise, punchy slide caption. Keep it strictly MAXIMUM 100 characters (1-2 lines) for use when an image is shown.
5. "long_summary" must be a descriptive, engaging narrative paragraph (strictly between 200 and 320 characters, 2-3 sentences max) for text-only layouts.

IMAGE SELECTION:
You are provided with a list of images available in this article along with their captions.
For each segment, select the most relevant image URL from the list that fits the semantic context of that slide's beat. If no image fits, set "suggested_image_url" to null.
Each image URL should be used at most once across the story.

Output a JSON object with:
1. "segments": A list of exactly {n_slides} objects. Each segment object MUST contain:
   - "key_phrases": A list of 2-3 unique key phrases specific to this beat.
   - "short_summary": A punchy caption (max 100 characters).
   - "long_summary": A short storytelling paragraph (200-320 characters).
   - "suggested_image_url": A unique URL from the provided image list, or null.
2. "takeaways": A list of 3-5 short bullet points summarizing the key takeaways of the whole article.

AVAILABLE IMAGES:
{json.dumps(images_data, indent=2)}

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
                "responseMimeType": "application/json"
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
            logger.info(f"Calling Gemini to storyboard {n_slides} segments for: {tree.title}")
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

            return json.loads(cleaned_text)

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
        Maps each storyboard segment to a video or an image in the DocumentTree using LLM suggestions or proximity heuristics.
        """
        aligned_segments = []
        used_images = set()
        used_videos = set()

        for segment in segments:
            key_phrases = segment.get("key_phrases") or []
            short_summary = segment.get("short_summary") or ""
            long_summary = segment.get("long_summary") or ""
            suggested_img = segment.get("suggested_image_url")
            
            # 1. First, prioritize using the LLM's selected image if valid and unused
            all_images = tree.get_images()
            if suggested_img and suggested_img in all_images and suggested_img not in used_images:
                used_images.add(suggested_img)
                aligned_segments.append({
                    "short_summary": short_summary,
                    "long_summary": long_summary,
                    "video_url": None,
                    "embed_code": None,
                    "image_url": suggested_img
                })
                continue

            # 2. Otherwise, check for layout adjacent video
            match_block_idx = self._find_best_block_match(tree, key_phrases, short_summary or long_summary)
            matched_video = tree.get_adjacent_video(match_block_idx, max_distance=4)
            if matched_video and matched_video["url"] not in used_videos:
                used_videos.add(matched_video["url"])
                aligned_segments.append({
                    "short_summary": short_summary,
                    "long_summary": long_summary,
                    "video_url": matched_video["url"],
                    "embed_code": matched_video["embed_code"],
                    "image_url": None
                })
                continue

            # 3. Fallback to scanning for adjacent image in layout
            matched_image = tree.get_adjacent_image(match_block_idx, max_distance=4)
            if matched_image and matched_image not in used_images:
                used_images.add(matched_image)
            else:
                matched_image = None
                
            aligned_segments.append({
                "short_summary": short_summary,
                "long_summary": long_summary,
                "video_url": None,
                "embed_code": None,
                "image_url": matched_image
            })

        # Fallback 1: If no media was matched at all, try to assign the promo_image to the first slide
        has_any_media = bool(used_images) or bool(used_videos)
        if not has_any_media and tree.promo_image:
            aligned_segments[0]["image_url"] = tree.promo_image
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
        all_doc_images = tree.get_images()
        for img in all_doc_images:
            if img not in used_images:
                # Find the first segment without media and assign it
                for seg in aligned_segments:
                    if not seg["video_url"] and not seg["image_url"]:
                        seg["image_url"] = img
                        used_images.add(img)
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
                page_content = [
                    {"type": "text", "content": text_content},
                    {"type": "image", "content_url": img_url}
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
        # Determine number of content slides (beats)
        word_count = len(tree.get_plaintext().split())
        n_slides = 4 if word_count < 600 else 5

        # Stage 1: Storyboard
        storyboard_data = self.storyboard(tree, n_slides)
        if not storyboard_data:
            return None

        segments = storyboard_data.get("segments") or []
        takeaways = storyboard_data.get("takeaways") or []

        # Stage 2: Media Alignment
        aligned_segments = self.align_media(tree, segments)

        # Stage 3: Refine Layout
        pages = self.refine(aligned_segments, takeaways, tree)
        return pages
