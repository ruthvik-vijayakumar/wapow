"""Utility for fetching and parsing full article contents from HTML web pages using readability-lxml and custom parser fallbacks."""

import logging
import json
import re
from urllib.parse import urljoin, urlparse
from typing import Optional, Any
from datetime import datetime
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


async def fetch_html(url: str, timeout_seconds: int = 30) -> Optional[str]:
    """
    Fetch raw HTML of a URL using Playwright for JS rendering.

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


def parse_date_string(date_str: str) -> Optional[datetime]:
    """Helper to parse a date string into a datetime object."""
    if not date_str:
        return None
    date_str = date_str.strip()
    # Try ISO format formats
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            s = date_str
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    # Try fromisoformat as fallback
    try:
        s = date_str
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except ValueError:
        pass
    return None


def extract_json_ld(soup: BeautifulSoup) -> dict[str, Any]:
    """Extract metadata from JSON-LD block if it is an article/story."""
    metadata = {}
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, list):
                graphs = data
            elif isinstance(data, dict):
                if "@graph" in data:
                    graphs = data["@graph"]
                else:
                    graphs = [data]
            else:
                continue

            for item in graphs:
                if not isinstance(item, dict):
                    continue
                type_ = item.get("@type", "")
                if isinstance(type_, list):
                    is_article = any("Article" in t or "NewsArticle" in t or "BlogPosting" in t for t in type_)
                else:
                    is_article = isinstance(type_, str) and ("Article" in type_ or "NewsArticle" in type_ or "BlogPosting" in type_)

                if is_article:
                    if "headline" in item:
                        metadata["headline"] = item["headline"]
                    if "description" in item:
                        metadata["sub_title"] = item["description"]
                    if "datePublished" in item:
                        metadata["publish_date"] = item["datePublished"]
                    
                    # Author
                    author_data = item.get("author")
                    if isinstance(author_data, list) and author_data:
                        author_data = author_data[0]
                    if isinstance(author_data, dict):
                        metadata["author"] = author_data.get("name")
                        metadata["author_link"] = author_data.get("url")
                    elif isinstance(author_data, str):
                        metadata["author"] = author_data

                    # Publisher
                    pub_data = item.get("publisher")
                    if isinstance(pub_data, dict):
                        metadata["publisher"] = pub_data.get("name")

                    # Image
                    img_data = item.get("image")
                    if isinstance(img_data, dict):
                        metadata["promo_image"] = img_data.get("url")
                    elif isinstance(img_data, list) and img_data:
                        if isinstance(img_data[0], dict):
                            metadata["promo_image"] = img_data[0].get("url")
                        else:
                            metadata["promo_image"] = img_data[0]
                    elif isinstance(img_data, str):
                        metadata["promo_image"] = img_data
        except Exception:
            pass
    return metadata


def extract_metadata(soup: BeautifulSoup, url: str) -> dict[str, Any]:
    """
    Extract meta details (headline, sub_title, publish_date, author, author_link, publisher, promo_image) from soup.

    Args:
        soup: BeautifulSoup object
        url: Original page URL for resolving relative links

    Returns:
        Dictionary of metadata fields
    """
    meta_data = {
        "headline": "",
        "sub_title": "",
        "publish_date": None,
        "author": "",
        "author_link": "",
        "publisher": "",
        "promo_image": "",
    }

    # 1. Parse JSON-LD if available
    json_ld = extract_json_ld(soup)
    for k, v in json_ld.items():
        if v:
            meta_data[k] = v

    # 2. Headline / Title fallback
    if not meta_data["headline"]:
        title_tag = (
            soup.find("meta", attrs={"property": "og:title"})
            or soup.find("meta", attrs={"name": "twitter:title"})
            or soup.find("meta", attrs={"name": "title"})
        )
        if title_tag and title_tag.get("content"):
            meta_data["headline"] = title_tag["content"].strip()
        elif soup.title:
            meta_data["headline"] = soup.title.get_text().strip()
        elif soup.h1:
            meta_data["headline"] = soup.h1.get_text().strip()

    # 3. Sub-title / Description fallback
    if not meta_data["sub_title"]:
        desc_tag = (
            soup.find("meta", attrs={"property": "og:description"})
            or soup.find("meta", attrs={"name": "twitter:description"})
            or soup.find("meta", attrs={"name": "description"})
        )
        if desc_tag and desc_tag.get("content"):
            meta_data["sub_title"] = desc_tag["content"].strip()

    # 4. Publish date fallback
    if not meta_data["publish_date"]:
        for name in (
            "article:published_time",
            "published_time",
            "og:published_time",
            "dc.date",
            "dc.date.issued",
            "pubdate",
            "date",
            "pubDate",
            "sailthru.date",
        ):
            tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
            if tag and tag.get("content"):
                meta_data["publish_date"] = tag["content"].strip()
                break
        
        if not meta_data["publish_date"]:
            time_tag = soup.find("time")
            if time_tag:
                meta_data["publish_date"] = time_tag.get("datetime") or time_tag.get_text()

    # Convert publish_date from string to datetime
    if isinstance(meta_data["publish_date"], str):
        meta_data["publish_date"] = parse_date_string(meta_data["publish_date"])

    # 5. Author fallback
    if not meta_data["author"]:
        author_tag = (
            soup.find("meta", attrs={"name": "author"})
            or soup.find("meta", attrs={"property": "og:author"})
            or soup.find("meta", attrs={"name": "twitter:creator"})
            or soup.find("meta", attrs={"property": "article:author"})
        )
        if author_tag and author_tag.get("content"):
            meta_data["author"] = author_tag["content"].strip()
        else:
            byline_el = soup.find(class_=lambda c: c and any(w in c.lower() for w in ("author", "byline", "creator")))
            if byline_el:
                meta_data["author"] = byline_el.get_text().strip()

    # 6. Author link fallback
    if not meta_data["author_link"] and meta_data["author"]:
        author_el = soup.find(class_=lambda c: c and any(w in c.lower() for w in ("author", "byline", "creator")))
        if author_el:
            if author_el.name == "a" and author_el.get("href"):
                meta_data["author_link"] = urljoin(url, author_el["href"].strip())
            else:
                a_tag = author_el.find("a", href=True)
                if a_tag:
                    meta_data["author_link"] = urljoin(url, a_tag["href"].strip())

    # 7. Publisher fallback
    if not meta_data["publisher"]:
        pub_tag = (
            soup.find("meta", attrs={"property": "og:site_name"})
            or soup.find("meta", attrs={"name": "dc.publisher"})
            or soup.find("meta", attrs={"name": "publisher"})
        )
        if pub_tag and pub_tag.get("content"):
            meta_data["publisher"] = pub_tag["content"].strip()
        else:
            parsed = urlparse(url)
            domain = parsed.netloc
            if domain.startswith("www."):
                domain = domain[4:]
            meta_data["publisher"] = domain

    # 8. Promo image fallback
    if not meta_data["promo_image"]:
        img_tag = (
            soup.find("meta", attrs={"property": "og:image"})
            or soup.find("meta", attrs={"name": "twitter:image"})
            or soup.find("link", attrs={"rel": "image_src"})
        )
        if img_tag:
            img_url = img_tag.get("content") or img_tag.get("href") or ""
            if img_url:
                meta_data["promo_image"] = urljoin(url, img_url.strip())

    return meta_data


def is_valid_article_image(url: str) -> bool:
    """Validate if an image URL is likely a high-quality article body image rather than UI element."""
    if not url or not isinstance(url, str):
        return False
    url_lower = url.lower()
    
    # Exclude data URIs
    if url_lower.startswith("data:"):
        return False
        
    # Exclude SVG vector graphics
    if url_lower.endswith(".svg") or ".svg?" in url_lower:
        return False
        
    # Check for small size dimensions in URL query params or path (e.g. w=90, w_120, h=80)
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


def extract_elements_from_container(container: BeautifulSoup, url: str) -> tuple[list[dict[str, Any]], str]:
    """
    Traverse a container BeautifulSoup element and sequentially extract structured text, headers, images, and videos.
    """
    content_elements = []
    seen_elements = set()
    text_blocks = []

    target_tags = ["p", "blockquote", "li", "h2", "h3", "h4", "h5", "h6", "img", "iframe", "video"]
    for el in container.find_all(target_tags):
        # Prevent double-processing children of already processed containers
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

        if tag_name in ("p", "blockquote", "li"):
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
                if tag_name == "blockquote":
                    element_data["subtype"] = "blockquote"
                elif tag_name == "li":
                    element_data["subtype"] = "list_item"
                
                if links:
                    element_data["links"] = links
                content_elements.append(element_data)

        elif tag_name in ("h2", "h3", "h4", "h5", "h6"):
            text = el.get_text().strip()
            if text:
                content_elements.append({
                    "type": "header",
                    "content": text,
                    "level": int(tag_name[1]),
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


def extract_body_elements(soup: BeautifulSoup, url: str) -> tuple[list[dict[str, Any]], str]:
    """
    Extract structured content elements using a block container scoring heuristic.
    This serves as a fallback when readability-lxml returns empty content.
    """
    body = soup.find("body") or soup

    # Make a copy of body so we don't mutate original soup
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
            if len(el.find_all("p")) >= 2 or len(el.get_text().strip()) > 300:
                container = el
                break
        if container:
            break

    if not container:
        container = body_copy
        while True:
            best_child = None
            best_child_score = 0
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

    return extract_elements_from_container(container, url)


async def extract_article_content(url: str) -> dict[str, Any]:
    """
    Fetch the article page, extract its full body content, media elements, and metadata.
    Attempts to use readability-lxml first, falling back to a custom scoring parser if it fails.

    Args:
        url: Web URL of the article

    Returns:
        A dict containing parsed metadata, content_elements list, and full body_text.
    """
    html = await fetch_html(url)
    if not html:
        return {}

    try:
        soup = BeautifulSoup(html, "lxml")
        metadata = extract_metadata(soup, url)
        
        content_elements = []
        body_text = ""
        readability_success = False
        
        try:
            from readability import Document
            doc = Document(html)
            summary_html = doc.summary()
            if summary_html:
                summary_soup = BeautifulSoup(summary_html, "lxml")
                elements, text = extract_elements_from_container(summary_soup, url)
                if len(text.strip()) > 150:
                    content_elements = elements
                    body_text = text
                    readability_success = True
                    logger.info(f"Successfully extracted article using Readability-lxml: {url}")
        except Exception as read_err:
            logger.warning(f"Readability parsing error, falling back to custom block parser: {read_err}")
            
        if not readability_success:
            logger.info(f"Using fallback custom block parser for: {url}")
            content_elements, body_text = extract_body_elements(soup, url)

        # Fallback for promo_image to first body image if missing
        if not metadata.get("promo_image") or metadata.get("promo_image") == "":
            for elem in content_elements:
                if elem.get("type") == "image" and elem.get("url"):
                    metadata["promo_image"] = elem["url"]
                    break

        return {
            "title": metadata["headline"],
            "description": metadata["sub_title"],
            "author": metadata["author"],
            "author_link": metadata["author_link"],
            "publisher": metadata["publisher"],
            "publish_date": metadata["publish_date"],
            "image_url": metadata["promo_image"],
            "content_elements": content_elements,
            "body_text": body_text,
        }
    except Exception as e:
        logger.error(f"Error parsing article HTML for {url}: {e}")
        return {}
