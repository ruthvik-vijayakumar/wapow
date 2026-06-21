"""Extract plain text and image URLs from MongoDB article documents."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    if not text:
        return ""
    plain = _HTML_TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", plain).strip()


@dataclass
class AnalyzedArticle:
    title: str
    description: str
    body_text: str
    word_count: int
    image_urls: list[str] = field(default_factory=list)
    video_items: list[dict] = field(default_factory=list)  # [{url, embed_code}]


def _dedupe_urls(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for u in urls:
        if not u or not isinstance(u, str):
            continue
        u = u.strip()
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _collect_from_content_elements(elements: list) -> tuple[str, list[str], list[dict]]:
    parts: list[str] = []
    images: list[str] = []
    videos: list[dict] = []
    seen_video_urls: set[str] = set()
    if not elements:
        return "", images, videos
    for el in elements:
        if not isinstance(el, dict):
            continue
        typ = (el.get("type") or "").lower()
        if typ in ("text", "header", "raw_html", "oembed_response"):
            raw = el.get("content") or ""
            if isinstance(raw, str) and raw:
                parts.append(_strip_html(raw))
        elif typ in ("image", "gallery"):
            ap = el.get("additional_properties") or {}
            url = el.get("url")
            if not url and isinstance(ap, dict):
                url = ap.get("fullSizeResizeUrl") or ap.get("url")
            if not url:
                promo = el.get("promo_items") or {}
                basic = (promo.get("basic") or {}) if isinstance(promo, dict) else {}
                url = basic.get("url")
            if isinstance(url, str) and url.startswith("http"):
                images.append(url)
        elif typ == "video":
            url = el.get("url") or el.get("content_url") or ""
            embed_code = el.get("embed_code") or el.get("content") or ""
            if url and url not in seen_video_urls:
                seen_video_urls.add(url)
                videos.append({"url": url, "embed_code": embed_code})
    return "\n\n".join(p for p in parts if p), images, videos


def is_valid_article_image(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    url_lower = url.lower()
    
    # Exclude data URIs
    if url_lower.startswith("data:"):
        return False
        
    # Exclude SVG vector graphics (usually logos, icons, badges)
    if url_lower.endswith(".svg") or ".svg?" in url_lower:
        return False
        
    # Check for small size dimensions in URL query params or path (e.g. w=90, w_120, h=80)
    # We look for w, width, h, height followed by = or _ and then digits
    import re
    size_matches = re.findall(r'(?:[?&_]w(?:idth)?|[?&_]h(?:eight)?)[=_](\d+)', url_lower)
    for size_str in size_matches:
        try:
            size = int(size_str)
            if size < 180:
                return False
        except ValueError:
            pass
            
    # Extract filename and path components
    path_parts = url_lower.split("/")
    filename = path_parts[-1] if path_parts else ""
    if "?" in filename:
        filename = filename.split("?")[0]
        
    # Exclude common tracking, ads, layout directories
    layout_keywords = ["icon", "logo", "avatar", "sprite", "pixel", "button", "badge", "loader"]
    for part in path_parts[:-1]:
        if any(kw in part for kw in layout_keywords):
            return False
            
    # Exclude common UI icon/social share filename patterns
    filename_keywords = [
        "share", "check", "checked", "logo", "avatar", "pixel", 
        "spacer", "loader", "sprite", "placeholder", "button", 
        "loading", "arrow", "badge", "newsletter", "subscribe",
        "icon", "fb-", "twitter-", "instagram-", "social"
    ]
    if any(kw in filename for kw in filename_keywords):
        return False
        
    return True



def analyze_article(doc: dict) -> AnalyzedArticle:
    """Parse article document from Mongo (WAPO-like or scraper-normalized)."""
    headlines = doc.get("headlines") or {}
    title = (headlines.get("basic") or doc.get("title") or "Article").strip()

    desc_obj = doc.get("description")
    if isinstance(desc_obj, dict):
        description = _strip_html(desc_obj.get("basic") or "")
    else:
        description = _strip_html(str(desc_obj or ""))

    content_field = doc.get("content") or doc.get("content_elements") or []
    if isinstance(content_field, str):
        body_from_content = _strip_html(content_field)
        ce_images: list[str] = []
        ce_videos: list[dict] = []
    else:
        body_from_content, ce_images, ce_videos = _collect_from_content_elements(
            content_field if isinstance(content_field, list) else []
        )

    if not body_from_content:
        body_from_content = description or title

    full_text = f"{title}\n\n{description}\n\n{body_from_content}".strip()
    word_count = len(full_text.split())

    images: list[str] = []
    promo = doc.get("promo_items") or {}
    basic = promo.get("basic") or {}
    if isinstance(basic, dict) and basic.get("url"):
        images.append(basic["url"])
    lead = doc.get("lead_art") or {}
    if isinstance(lead, dict) and lead.get("url"):
        images.append(lead["url"])
    images.extend(ce_images)
    images = [u for u in images if is_valid_article_image(u)]
    images = _dedupe_urls(images)

    return AnalyzedArticle(
        title=title,
        description=description,
        body_text=body_from_content,
        word_count=word_count,
        image_urls=images,
        video_items=ce_videos,
    )

