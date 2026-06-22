import json
import os
import urllib.request
import urllib.error
import logging

from .analyzer import AnalyzedArticle

logger = logging.getLogger(__name__)

def build_pages_with_gemini(analyzed: AnalyzedArticle) -> list[dict] | None:
    """Fallback single-pass Gemini page builder matching the single/multi image rules."""
    from scraper.config import settings
    api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
        
    unique_images = analyzed.image_urls
    num_images = len(unique_images)
    
    if num_images <= 1:
        # Prompt for single image or no image case
        img_url = unique_images[0] if unique_images else None
        prompt = f"""You are an expert mobile editor. Your task is to storyboard a mobile visual story (like Instagram/Snapchat Stories) from a news article.
Summarize the article into EXACTLY ONE content slide.

CONTENT INSTRUCTIONS:
- The summary MUST focus strictly and only on the central topic of the article.
- Strip off any unrelated, side, or tangential information. Keep it highly focused on the core theme.
- The summary must be a substantial, self-contained narrative beat — not a thin sentence.
- If a slide has an image, keep the summary text between 90 and 200 characters. If no image, between 220 and 360 characters.

Output a JSON object with:
1. "slides": A list containing EXACTLY ONE slide object. The slide object MUST contain:
   - "text": The summary text following the constraints above.
   - "image_url": The image URL provided below, or null if none is available.
2. "takeaways": A list of 3-5 short bullet points summarizing the key takeaways of the article.

IMAGE PROVIDED:
{img_url}

TITLE:
{analyzed.title}

ARTICLE_BODY:
{analyzed.body_text}
"""
    else:
        # Prompt for multiple images
        target_images = unique_images[:5]
        prompt = f"""You are an expert mobile editor. Your task is to storyboard a mobile visual story (like Instagram/Snapchat Stories) from a news article.
Summarize the article into EXACTLY {len(target_images)} content slides, corresponding to the {len(target_images)} available images in order.

CONTENT INSTRUCTIONS:
- You must generate exactly {len(target_images)} slides.
- Each slide corresponds to the image at the same index from the AVAILABLE IMAGES list.
- The summary text for each slide must be highly relevant and appropriate to the specific image shown on that slide.
- Together, the slides must explain the narrative progression of the article.
- Each slide's summary text must be concise: between 90 and 200 characters.

Output a JSON object with:
1. "slides": A list containing EXACTLY {len(target_images)} slide objects. Each slide object MUST contain:
   - "text": The summary text following the constraints above.
   - "image_url": The exact image URL from the AVAILABLE IMAGES list corresponding to this slide's index.
2. "takeaways": A list of 3-5 short bullet points summarizing the key takeaways of the whole article.

AVAILABLE IMAGES (in sequential order):
{json.dumps(target_images, indent=2)}

TITLE:
{analyzed.title}

ARTICLE_BODY:
{analyzed.body_text}
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
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
      
    try:
        logger.info(f"Calling Gemini API to generate adaptive slides for article: {analyzed.title}")
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
            res_json = json.loads(cleaned_text)
        except json.JSONDecodeError as jde:
            logger.warning(f"JSON parsing error: {jde}. Raw text: {cleaned_text[:500]}")
            return None
            
        slides = res_json.get("slides", [])
        takeaways = res_json.get("takeaways", [])
        
        pages = []
        for i, slide in enumerate(slides):
            text = slide.get("text", "").strip()
            img_url = slide.get("image_url")
            
            # If img_url is null or not valid, but we have a unique image at this index, fall back to it
            if not img_url and i < len(unique_images):
                img_url = unique_images[i]
            
            page_content = [{"type": "text", "content": text}]
            if img_url and isinstance(img_url, str):
                img_url = img_url.strip()
                page_content.append({"type": "image", "content_url": img_url})
                    
            pages.append({
                "page_type": "content",
                "content": page_content
            })
            
        # Overview/takeaways slide only when there are multiple content slides.
        if len(pages) >= 2:
            if takeaways:
                takeaways_text = "\n".join(f"• {t.strip()}" for t in takeaways)
            else:
                takeaways_text = f"• {analyzed.title}"

            pages.append({
                "page_type": "overview",
                "content": [
                    {"type": "text", "content": takeaways_text}
                ]
            })

        return pages
        
    except Exception as e:
        logger.warning(f"Error calling Gemini API: {e}")
        return None
