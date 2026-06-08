"""Build StoryView-compatible ai_summary.pages from analyzed article text."""

from __future__ import annotations

from .analyzer import AnalyzedArticle

# Target 3–4 content slides by default; expand with length; cap total story depth.
_MIN_CONTENT_SLIDES = 3
_MAX_CONTENT_SLIDES = 9
_TITLE_MAX = 100
_BODY_MAX = 2000


def _content_slide_count(word_count: int) -> int:
    if word_count < 250:
        return _MIN_CONTENT_SLIDES
    if word_count < 550:
        return 4
    extra = max(0, (word_count - 550) // 220)
    return min(_MAX_CONTENT_SLIDES, 4 + extra)


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
    snippet = body.strip().replace("\n", " ")
    title = snippet[:_TITLE_MAX] + ("…" if len(snippet) > _TITLE_MAX else "")
    if not title:
        title = "Details"
    text_body = body[:_BODY_MAX] + ("…" if len(body) > _BODY_MAX else "")
    return {
        "page_type": "content",
        "content": [
            {"type": "text", "content": text_body or title},
            {"type": "image", "content_url": image_url},
        ],
    }


def _takeaways_from_chunks(title: str, chunks: list[str]) -> str:
    lines = [f"• {c.strip().replace(chr(10), ' ')[:200]}{'…' if len(c) > 200 else ''}" for c in chunks[:5]]
    if not lines:
        return f"• {title}"
    return "\n".join(lines)


def build_pages(analyzed: AnalyzedArticle) -> list[dict]:
    """Produce pages array (content + overview) for ai_summary."""
    n = _content_slide_count(analyzed.word_count)
    chunks = _split_into_chunks(analyzed.body_text, n)
    pages: list[dict] = []
    for i, chunk in enumerate(chunks):
        img = _pick_image(analyzed.image_urls, i)
        pages.append(_make_content_page(chunk, img))

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
