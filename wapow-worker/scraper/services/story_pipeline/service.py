"""Orchestrate analyze → generate → optional LLM → persist ai_summary."""

from __future__ import annotations

import os
import logging
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from scraper.config import ARTICLES_COLLECTION
from scraper.db import get_db

from .analyzer import analyze_article
from .generator import build_pages
from .llm_optional import refine_takeaways_with_openai
from .gemini_service import build_pages_with_gemini

logger = logging.getLogger(__name__)


def find_article_doc(article_id: str) -> dict | None:
    coll = get_db()[ARTICLES_COLLECTION]
    try:
        oid = ObjectId(article_id)
    except Exception:
        oid = article_id
    doc = coll.find_one({"_id": oid})
    if doc is None and oid != article_id:
        doc = coll.find_one({"_id": article_id})
    if doc:
        # Check story_slides first
        slides = get_db()["story_slides"].find_one({"article_id": doc["_id"]})
        if slides:
            doc["ai_summary"] = {
                "pages": slides.get("pages"),
                "generation_timestamp": slides.get("generation_timestamp"),
                "llm_model_used": slides.get("llm_model_used"),
            }
    return doc


def _build_ai_summary(doc: dict, analyzed: Any, use_llm_overview: bool) -> dict[str, Any]:
    from .base import DocumentTree
    from .story_pipeline import StoryPipeline

    pages = None
    llm_model = "gemini-2.5-flash"

    try:
        tree = DocumentTree.from_mongo_doc(doc)
        pipeline = StoryPipeline()
        pages = pipeline.execute(tree)
        if pages:
            logger.info("Successfully generated slides using new StoryPipeline workflow.")
    except Exception as pipe_err:
        logger.error(f"StoryPipeline generation failed: {pipe_err}. Falling back to legacy methods.")

    if not pages:
        logger.info("Falling back to legacy gemini single-pass slide builder.")
        pages = build_pages_with_gemini(analyzed)
        
        if not pages:
            logger.info("Falling back to heuristic rule-based slide builder.")
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
        "slide_count": len(pages) if pages else 0,
    }


def convert_article_to_story(article_id: str, force: bool = False) -> dict[str, Any]:
    """Generate ai_summary and persist on the story_slides collection."""
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
    ai_summary = _build_ai_summary(doc, analyzed, use_llm_overview=True)

    # Save to the new story_slides collection
    slides_coll = get_db()["story_slides"]
    slides_coll.update_one(
        {"article_id": doc["_id"]},
        {
            "$set": {
                "article_id": doc["_id"],
                "pages": ai_summary.get("pages"),
                "generation_timestamp": ai_summary.get("generation_timestamp"),
                "llm_model_used": ai_summary.get("llm_model_used"),
            }
        },
        upsert=True
    )

    # Clean up legacy embedded summary on articles
    coll = get_db()[ARTICLES_COLLECTION]
    coll.update_one({"_id": doc["_id"]}, {"$unset": {"ai_summary": ""}})

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
    ai_summary = _build_ai_summary(doc, analyzed, use_llm_overview=True)
    return {
        "article_id": article_id,
        "ai_summary": ai_summary,
        "preview": True,
    }
