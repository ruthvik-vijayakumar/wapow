"""Optional OpenAI refinement for overview text (httpx, no extra package beyond stdlib alternative)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def refine_takeaways_with_openai(title: str, body_excerpt: str) -> str | None:
    """
    If OPENAI_API_KEY is set, return bullet takeaways string; else None.
    body_excerpt should be truncated to save tokens.
    """
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    excerpt = body_excerpt[:8000]
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You write concise bullet takeaways for a mobile story. "
                "Output 3-5 bullet lines only, each starting with '• ', factual, no markdown.",
            },
            {
                "role": "user",
                "content": f"Title: {title}\n\nArticle excerpt:\n{excerpt}",
            },
        ],
        "max_tokens": 400,
        "temperature": 0.4,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
        choices = data.get("choices") or []
        if not choices:
            return None
        content = (choices[0].get("message") or {}).get("content") or ""
        return content.strip() or None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, IndexError):
        return None
