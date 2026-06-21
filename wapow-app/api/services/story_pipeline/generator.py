"""Build StoryView-compatible ai_summary.pages from analyzed article text."""

from __future__ import annotations

from .analyzer import AnalyzedArticle

# Target few, substantial content slides. A typical article should become a lead
# slide (with image) + one consolidated body slide, not a string of thin cards.
_MIN_CONTENT_SLIDES = 1
_MAX_CONTENT_SLIDES = 5
_TITLE_MAX = 100
_BODY_MAX = 2000


def _content_slide_count(word_count: int) -> int:
    # ~1 content slide per ~450 words; bias low so short/medium articles stay tight.
    if word_count < 220:
        return 1
    if word_count < 650:
        return 2
    if word_count < 1100:
        return 3
    extra = max(0, (word_count - 1100) // 500)
    return min(_MAX_CONTENT_SLIDES, 3 + extra)


def _split_into_chunks(text: str, n_chunks: int) -> list[str]:
    text = text.strip()
    if not text:
        return ["No additional text available."] * max(1, n_chunks)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text]
    if len(paragraphs) <= n_chunks:
        chunks = list(paragraphs)
        while len(chunks) < n_chunks:
            chunks.append(chunks[-1] if chunks else text)
        return chunks[:n_chunks]

    # Merge paragraphs into n_chunks groups
    total_len = sum(len(p) for p in paragraphs)
    chunks: list[str] = []
    target = total_len / n_chunks
    current: list[str] = []
    acc = 0
    for p in paragraphs:
        if acc + len(p) > target * 1.2 and current and len(chunks) < n_chunks - 1:
            chunks.append("\n\n".join(current))
            current = [p]
            acc = len(p)
        else:
            current.append(p)
            acc += len(p)
    if current:
        chunks.append("\n\n".join(current))
    while len(chunks) < n_chunks:
        chunks.append(chunks[-1])
    return chunks[:n_chunks]


def _pick_image(urls: list[str], index: int) -> str:
    if not urls:
        return "https://picsum.photos/800/1200?random=story"
    return urls[min(index, len(urls) - 1)]


def _make_content_page(body: str, image_url: str) -> dict:
    # Pass the full text through; the frontend scales it to fit and only
    # ellipsizes when content exceeds the container height.
    text_body = (body or "").strip()
    if not text_body:
        text_body = "Details"
    return {
        "page_type": "content",
        "content": [
            {"type": "text", "content": text_body},
            {"type": "image", "content_url": image_url},
        ],
    }


def _takeaways_from_chunks(title: str, chunks: list[str]) -> str:
    lines = [f"• {c.strip().replace(chr(10), ' ')[:200]}{'…' if len(c) > 200 else ''}" for c in chunks[:5]]
    if not lines:
        return f"• {title}"
    return "\n".join(lines)


def _make_video_page(video: dict, caption: str = "") -> dict:
    """Build a video slide page."""
    content = [
        {"type": "video", "content_url": video["url"], "embed_code": video.get("embed_code") or ""},
    ]
    if caption:
        content.insert(0, {"type": "text", "content": caption})
    return {
        "page_type": "content",
        "content": content,
    }


def build_pages(analyzed: AnalyzedArticle) -> list[dict]:
    """Produce pages array (content + overview) for ai_summary."""
    n = _content_slide_count(analyzed.word_count)
    chunks = _split_into_chunks(analyzed.body_text, n)
    pages: list[dict] = []
    for i, chunk in enumerate(chunks):
        img = _pick_image(analyzed.image_urls, i)
        pages.append(_make_content_page(chunk, img))

    # Inject video slides after the first content slide (one per unique video, max 2)
    if analyzed.video_items:
        video_slides = []
        for video in analyzed.video_items[:2]:
            video_slides.append(_make_video_page(video))
        # Insert after first content slide (index 1), before remaining content
        pages = pages[:1] + video_slides + pages[1:]

    # Takeaways slide only when there are multiple content slides to summarize.
    if len(pages) >= 2:
        takeaways = _takeaways_from_chunks(analyzed.title, chunks)
        pages.append(
            {
                "page_type": "overview",
                "content": [
                    {"type": "text", "content": takeaways},
                ],
            }
        )
    return pages
