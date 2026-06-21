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
        
    # Determine target range of slides (content slides) adaptively based on word count.
    # Bias toward fewer, denser slides.
    word_count = len(analyzed.body_text.split()) if analyzed.body_text else analyzed.word_count
    if word_count < 200:
        min_slides, max_slides = 1, 2
    elif word_count < 700:
        min_slides, max_slides = 2, 3
    else:
        min_slides, max_slides = 3, 4
        
    prompt = f"""You are an expert mobile editor. Your task is to storyboard a mobile visual story (like Instagram/Snapchat Stories) from a news article.
Summarize the article into between {min_slides} and {max_slides} content slides and 1 key takeaways overview slide.
Determine the optimal number of content slides (within the range {min_slides} to {max_slides}) based on the actual substance of the article.

CONTENT DENSITY (most important rule):
- Each slide MUST carry a substantial, self-contained point — never a single thin fragment that says almost nothing.
- It is far better to have FEWER, richer slides than many thin ones. Default to {min_slides} and only add a slide for a genuinely distinct development or topic shift.
- If two ideas are closely related, COMBINE them onto one slide rather than splitting them.
Ensure the slides tell an engaging, progressive narrative that explains the entire story.

CRITICAL INSTRUCTIONS FOR TEXT QUALITY:
1. DO NOT copy-paste sentences or paragraphs directly from the article body. Summarize and rewrite the content in a fresh, engaging, storytelling editor-curated voice.
2. Keep the language active, punchy, and highly readable.
3. If a slide has an accompanying image (i.e. "image_url" is set to a URL), keep its summary text concise but complete: between 90 and 200 characters (1-2 punchy sentences).
4. If a slide does NOT have an accompanying image (i.e. "image_url" is null), the summary text must be between 220 and 360 characters (2-3 short sentences) to explain this part of the story fully.

You are provided with a list of IMAGE_URLS associated with the article.
For each content slide:
- If there is an image in the provided list of IMAGE_URLS that directly matches or is highly appropriate for explaining this part of the summary, set its "image_url" to that URL.
- Each image URL from the provided list of IMAGE_URLS must be used AT MOST ONCE across all slides. If you have already used an image, do not use it again for a later slide; set its "image_url" to null instead.
- If no unique image from the list is appropriate for that part of the summary, or if the list is empty, set its "image_url" to null.
- A slide can be text-only (with "image_url" set to null) whenever an image is not appropriate or would be repeated. Do not force an image match if it's not a good fit.

Output a JSON object with:
1. "slides": A list of generated slide objects (between {min_slides} and {max_slides} objects). Each slide object MUST contain:
   - "text": The summary text following the constraints above.
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
