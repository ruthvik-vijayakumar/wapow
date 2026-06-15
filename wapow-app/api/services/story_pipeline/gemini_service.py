import json
import os
import urllib.request
import urllib.error
import logging

from .analyzer import AnalyzedArticle

logger = logging.getLogger(__name__)

def build_pages_with_gemini(analyzed: AnalyzedArticle) -> list[dict] | None:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
        
    # Determine target range of slides (content slides) adaptively based on word count
    word_count = len(analyzed.body_text.split()) if analyzed.body_text else analyzed.word_count
    if word_count < 150:
        min_slides, max_slides = 1, 2
    elif word_count < 600:
        min_slides, max_slides = 2, 4
    else:
        min_slides, max_slides = 3, 5
        
    prompt = f"""You are an expert editor creating a mobile visual story (like Instagram/Snapchat Stories) from a news article.
Your task is to summarize the article into between {min_slides} and {max_slides} content slides and 1 key takeaways overview slide.
Determine the optimal number of content slides (within the range {min_slides} to {max_slides}) based on the actual complexity and length of the article.
If the article is simple or short, favor a smaller number of slides (even just {min_slides}) so that the story is concise and doesn't drag.
Ensure the slides flow logically to explain the entire narrative of the article.
Flag layout templates accordingly.

You are provided with a list of IMAGE_URLS associated with the article.
For each content slide:
- If there is an image in the provided list of IMAGE_URLS that directly matches or is highly appropriate for explaining this part of the summary, set its "image_url" to that URL.
- Each image URL from the provided list of IMAGE_URLS must be used AT MOST ONCE across all slides. If you have already used an image, do not use it again for a later slide; set its "image_url" to null instead.
- If no unique image from the list is appropriate for that part of the summary, or if the list is empty, set its "image_url" to null.
- A slide can be text-only (with "image_url" set to null) whenever an image is not appropriate or would be repeated. Do not force an image match if it's not a good fit.

Text character limit constraints:
- If a slide has an accompanying image (i.e. "image_url" is set to a URL), keep its summary text highly concise: MAXIMUM 120 characters (a single short sentence).
- If a slide does NOT have an accompanying image (i.e. "image_url" is null), the summary text MUST be significantly longer and more detailed: between 250 and 450 characters (3-4 sentences) to explain this part of the narrative fully. Do not make it short.

Output a JSON object with:
1. "slides": A list of generated slide objects (between {min_slides} and {max_slides} objects). Each slide object MUST contain:
   - "text": The summary text following the character limit constraints above.
   - "image_url": The matched unique image URL from the provided list, or null if no unique image is appropriate or available.
2. "takeaways": A list of 3-5 short bullet points summarizing the key takeaways of the whole article.

IMAGE_URLS:
{json.dumps(analyzed.image_urls, indent=2)}

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
        logger.info(f"Calling Gemini API to generate adaptive slides ({min_slides}-{max_slides}) for article: {analyzed.title}")
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
        used_image_urls = set()
        for i, slide in enumerate(slides):
            text = slide.get("text", "").strip()
            img_url = slide.get("image_url")
            
            page_content = [{"type": "text", "content": text}]
            if img_url and isinstance(img_url, str):
                img_url = img_url.strip()
                if img_url in analyzed.image_urls and img_url not in used_image_urls:
                    page_content.append({"type": "image", "content_url": img_url})
                    used_image_urls.add(img_url)
                    
            pages.append({
                "page_type": "content",
                "content": page_content
            })
            
        # Append overview slide
        if takeaways:
            takeaways_text = "\n".join(f"• {t.strip()}" for t in takeaways)
        else:
            # Fallback
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
