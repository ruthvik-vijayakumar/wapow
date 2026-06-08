"""Utility for fetching and parsing full article contents from HTML web pages."""

import logging
from urllib.parse import urljoin
from typing import Optional, Any
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


async def fetch_html(url: str, timeout_seconds: int = 30) -> Optional[str]:
    """
    Fetch raw HTML of a URL using Playwright (Puppeteer-like) for JS rendering.

    Args:
        url: The web page URL
        timeout_seconds: Fetch timeout in seconds

    Returns:
        The raw HTML string, or None if the request fails
    """
    from playwright.async_api import async_playwright

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            page = await context.new_page()
            
            # Navigate to page and wait for DOM load event
            try:
                await page.goto(url, timeout=timeout_seconds * 1000, wait_until="load")
            except Exception as nav_err:
                logger.warning(f"Navigation timeout/error on {url}: {nav_err}")
            
            # Wait brief moment for dynamic contents to render
            try:
                await page.wait_for_timeout(1000)
            except Exception:
                pass
            
            html = await page.content()
            await browser.close()
            return html
    except Exception as e:
        logger.warning(f"Error fetching HTML with Playwright for {url}: {e}")
        return None


def extract_metadata(soup: BeautifulSoup, url: str) -> dict[str, str]:
    """
    Extract meta details (title, description, author, header image) from soup.

    Args:
        soup: BeautifulSoup object
        url: Original page URL for resolving relative links

    Returns:
        Dictionary of metadata fields
    """
    meta_data = {
        "title": "",
        "description": "",
        "author": "",
        "image_url": "",
    }

    # 1. Headline / Title
    title_tag = (
        soup.find("meta", attrs={"property": "og:title"})
        or soup.find("meta", attrs={"name": "twitter:title"})
        or soup.find("meta", attrs={"name": "title"})
    )
    if title_tag and title_tag.get("content"):
        meta_data["title"] = title_tag["content"].strip()
    elif soup.title:
        meta_data["title"] = soup.title.get_text().strip()
    elif soup.h1:
        meta_data["title"] = soup.h1.get_text().strip()

    # 2. Description
    desc_tag = (
        soup.find("meta", attrs={"property": "og:description"})
        or soup.find("meta", attrs={"name": "twitter:description"})
        or soup.find("meta", attrs={"name": "description"})
    )
    if desc_tag and desc_tag.get("content"):
        meta_data["description"] = desc_tag["content"].strip()

    # 3. Author
    author_tag = (
        soup.find("meta", attrs={"name": "author"})
        or soup.find("meta", attrs={"property": "og:author"})
        or soup.find("meta", attrs={"name": "twitter:creator"})
    )
    if author_tag and author_tag.get("content"):
        meta_data["author"] = author_tag["content"].strip()
    else:
        # Search for elements that might contain author name
        byline_el = soup.find(class_=lambda c: c and any(w in c.lower() for w in ("author", "byline")))
        if byline_el:
            meta_data["author"] = byline_el.get_text().strip()

    # 4. Header Image URL
    img_tag = (
        soup.find("meta", attrs={"property": "og:image"})
        or soup.find("meta", attrs={"name": "twitter:image"})
        or soup.find("link", attrs={"rel": "image_src"})
    )
    img_url = ""
    if img_tag:
        img_url = img_tag.get("content") or img_tag.get("href") or ""
    if img_url:
        meta_data["image_url"] = urljoin(url, img_url)

    return meta_data


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



def extract_body_elements(soup: BeautifulSoup, url: str) -> tuple[list[dict[str, Any]], str]:
    """
    Extract structured content elements (paragraphs, headers, images, videos)
    and assemble consolidated plain body text.

    Args:
        soup: BeautifulSoup object
        url: Original page URL for resolving relative links

    Returns:
        Tuple of (content_elements list, full body_text string)
    """
    body = soup.find("body") or soup

    # Make a copy of body so we don't mutate original soup for other metadata parses
    body_copy = BeautifulSoup(str(body), "lxml")

    # Clean up non-content elements
    for el in body_copy.find_all(
        ["script", "style", "head", "nav", "footer", "header", "form", "aside", "select", "noscript"]
    ):
        el.decompose()

    # Common semantic selectors for article content container
    semantic_selectors = [
        "article",
        "[itemprop='articleBody']",
        "div[class*='article-body']",
        "div[class*='article-content']",
        "div[class*='post-body']",
        "div[class*='post-content']",
        "div[class*='entry-content']",
        "div[class*='story-body']",
        "div[class*='story-content']",
    ]

    container = None
    for sel in semantic_selectors:
        elements = body_copy.select(sel)
        for el in elements:
            # Must contain at least two paragraphs or solid amount of text
            if len(el.find_all("p")) >= 2 or len(el.get_text().strip()) > 300:
                container = el
                break
        if container:
            break

    # If no semantic container matches, run tree-descending scoring heuristic
    if not container:
        container = body_copy
        while True:
            best_child = None
            best_child_score = 0
            # Search children that are candidate block containers
            for child in container.find_all(["div", "article", "section", "main"], recursive=False):
                child_score = sum(len(p.get_text().strip()) for p in child.find_all("p"))
                if child_score > best_child_score:
                    best_child_score = child_score
                    best_child = child

            current_container_score = sum(len(p.get_text().strip()) for p in container.find_all("p"))
            if best_child and best_child_score > 0.8 * current_container_score and current_container_score > 0:
                container = best_child
            else:
                break

    # Traverse child elements in order and extract structure
    content_elements = []
    seen_elements = set()
    text_blocks = []

    target_tags = ["p", "h2", "h3", "h4", "h5", "h6", "img", "iframe", "video"]
    for el in container.find_all(target_tags):
        # Prevent double-processing children of already processed containers (e.g. inline images/links inside P)
        parent = el.parent
        is_nested = False
        while parent and parent != container:
            if parent in seen_elements:
                is_nested = True
                break
            parent = parent.parent
        if is_nested:
            continue

        seen_elements.add(el)
        tag_name = el.name

        if tag_name == "p":
            text = el.get_text().strip()
            if text:
                text_blocks.append(text)
                links = []
                for a in el.find_all("a", href=True):
                    href = a["href"].strip()
                    link_text = a.get_text().strip()
                    if href and link_text:
                        links.append({
                            "url": urljoin(url, href),
                            "text": link_text,
                        })
                
                element_data = {
                    "type": "text",
                    "content": text,
                }
                if links:
                    element_data["links"] = links
                content_elements.append(element_data)

        elif tag_name in ("h2", "h3", "h4", "h5", "h6"):
            text = el.get_text().strip()
            if text:
                content_elements.append({
                    "type": "header",
                    "content": text,
                })

        elif tag_name == "img":
            src = el.get("src") or el.get("data-src") or el.get("data-lazy-src") or ""
            src = src.strip()
            if src and not src.startswith("data:"):
                resolved_url = urljoin(url, src)
                if is_valid_article_image(resolved_url):
                    caption = el.get("alt") or el.get("title") or ""
                    content_elements.append({
                        "type": "image",
                        "url": resolved_url,
                        "caption": caption.strip(),
                    })

        elif tag_name == "iframe":
            src = el.get("src") or ""
            src = src.strip()
            if "youtube.com" in src or "youtu.be" in src or "vimeo.com" in src:
                content_elements.append({
                    "type": "video",
                    "url": urljoin(url, src),
                    "embed_code": str(el),
                })

        elif tag_name == "video":
            src = el.get("src") or ""
            if not src:
                source_tag = el.find("source")
                if source_tag:
                    src = source_tag.get("src") or ""
            src = src.strip()
            if src and not src.startswith("data:"):
                content_elements.append({
                    "type": "video",
                    "url": urljoin(url, src),
                    "embed_code": str(el),
                })

    body_text = "\n\n".join(text_blocks)
    return content_elements, body_text


async def extract_article_content(url: str) -> dict[str, Any]:
    """
    Fetch the article page, extract its full body content, media elements, and metadata.

    Args:
        url: Web URL of the article

    Returns:
        A dict containing parsed metadata, content_elements list, and full body_text.
        Returns empty placeholders if fetching/parsing fails.
    """
    html = await fetch_html(url)
    if not html:
        return {}

    try:
        soup = BeautifulSoup(html, "lxml")
        metadata = extract_metadata(soup, url)
        content_elements, body_text = extract_body_elements(soup, url)

        return {
            "title": metadata["title"],
            "description": metadata["description"],
            "author": metadata["author"],
            "image_url": metadata["image_url"],
            "content_elements": content_elements,
            "body_text": body_text,
        }
    except Exception as e:
        logger.error(f"Error parsing article HTML for {url}: {e}")
        return {}
