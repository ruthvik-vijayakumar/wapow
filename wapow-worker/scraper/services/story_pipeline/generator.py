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


def _get_first_sentences(text: str, max_chars: int = 220) -> str:
    import re
    cleaned = text.strip().replace("\n", " ")
    sentences = re.split(r'(?<=[.!?])\s+', cleaned)
    current = []
    length = 0
    for s in sentences:
        if not s:
            continue
        if length + len(s) > max_chars and current:
            break
        current.append(s)
        length += len(s) + 1
    res = " ".join(current)
    if not res:
        res = cleaned[:max_chars]
        if len(cleaned) > max_chars:
            res += "…"
    return res


def _make_content_page(body: str, image_url: str | None) -> dict:
    # Pass the full text through; the frontend scales it to fit and only
    # ellipsizes when content exceeds the container height.
    text_body = (body or "").strip()
    content = [{"type": "text", "content": text_body}]
    if image_url:
        content.append({"type": "image", "content_url": image_url})
    return {
        "page_type": "content",
        "content": content,
    }


def _takeaways_from_chunks(title: str, chunks: list[str]) -> str:
    lines = [f"• {_get_first_sentences(c, 150)}" for c in chunks[:5]]
    if not lines:
        return f"• {title}"
    return "\n".join(lines)


def build_pages(analyzed: AnalyzedArticle) -> list[dict]:
    """Produce pages array (content + overview) for ai_summary."""
    # Determine the number of content pages based on number of unique images
    num_images = len(analyzed.image_urls)
    if num_images <= 1:
        n = 1
    else:
        n = min(num_images, 5)

    chunks = _split_into_chunks(analyzed.body_text, n)
    pages: list[dict] = []
    for i, chunk in enumerate(chunks):
        img = analyzed.image_urls[i] if i < len(analyzed.image_urls) else None
        pages.append(_make_content_page(chunk, img))

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
