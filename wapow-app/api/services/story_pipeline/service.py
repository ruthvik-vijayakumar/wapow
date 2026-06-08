"""Orchestrate analyze → generate → optional LLM → persist ai_summary."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from api.config import ARTICLES_COLLECTION
from api.db import get_db

from .analyzer import analyze_article
from .generator import build_pages
from .llm_optional import refine_takeaways_with_openai
from .gemini_service import build_pages_with_gemini


def find_article_doc(article_id: str) -> dict | None:
    coll = get_db()[ARTICLES_COLLECTION]
    try:
        oid = ObjectId(article_id)
    except Exception:
        oid = article_id
    doc = coll.find_one({"_id": oid})
    if doc is None and oid != article_id:
        doc = coll.find_one({"_id": article_id})
    return doc


def _build_ai_summary(analyzed, use_llm_overview: bool) -> dict[str, Any]:
    pages = build_pages_with_gemini(analyzed)
    llm_model = "gemini-2.5-flash"
    
    if not pages:
        pages = build_pages(analyzed)
        llm_model = "heuristic-v1"
        if use_llm_overview and pages and pages[-1].get("page_type") == "overview":
            excerpt = (analyzed.body_text or analyzed.description)[:8000]
            refined = refine_takeaways_with_openai(analyzed.title, excerpt)
            if refined:
                pages[-1]["content"] = [{"type": "text", "content": refined}]
                llm_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                
    return {
        "pages": pages,
        "generation_timestamp": datetime.now(timezone.utc).isoformat(),
        "llm_model_used": llm_model,
        "slide_count": len(pages),
    }


def convert_article_to_story(article_id: str, force: bool = False) -> dict[str, Any]:
    """Generate ai_summary and persist on the article document."""
    doc = find_article_doc(article_id)
    if not doc:
        raise ValueError("Article not found")

    existing = doc.get("ai_summary") or {}
    if existing.get("pages") and not force:
        return {
            "article_id": article_id,
            "ai_summary": existing,
            "cached": True,
        }

    analyzed = analyze_article(doc)
    ai_summary = _build_ai_summary(analyzed, use_llm_overview=True)

    coll = get_db()[ARTICLES_COLLECTION]
    coll.update_one({"_id": doc["_id"]}, {"$set": {"ai_summary": ai_summary}})

    return {
        "article_id": article_id,
        "ai_summary": ai_summary,
        "cached": False,
    }


def preview_story_for_article(article_id: str) -> dict[str, Any]:
    """Generate ai_summary in memory (no DB write)."""
    doc = find_article_doc(article_id)
    if not doc:
        raise ValueError("Article not found")
    analyzed = analyze_article(doc)
    ai_summary = _build_ai_summary(analyzed, use_llm_overview=True)
    return {
        "article_id": article_id,
        "ai_summary": ai_summary,
        "preview": True,
    }
