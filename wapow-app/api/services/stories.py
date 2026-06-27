"""Story deck service: canonical story_slides DTOs for the frontend."""
from __future__ import annotations

from typing import Any

from bson import ObjectId

from api.config import ARTICLES_COLLECTION
from api.db import get_db
from api.services.content import _serialize_doc, _transform_content_item

STORY_SLIDES_COLLECTION = "story_slides"


def _id_candidates(id_value: Any) -> list[Any]:
    """Return ObjectId/string candidates for cross-collection ID compatibility."""
    candidates: list[Any] = []
    if id_value is None:
        return candidates

    candidates.append(id_value)
    text = str(id_value)
    if text != id_value:
        candidates.append(text)
    try:
        oid = ObjectId(text)
        if oid not in candidates:
            candidates.append(oid)
    except Exception:
        pass
    return candidates


def _usable_pages_query() -> dict[str, Any]:
    return {"pages": {"$exists": True, "$type": "array", "$ne": []}}


def _article_metadata(article_doc: dict | None) -> dict[str, Any]:
    if not article_doc:
        return {}

    transformed = _transform_content_item(article_doc)
    return {
        "title": transformed.get("title"),
        "description": transformed.get("description"),
        "author": transformed.get("author"),
        "image_url": transformed.get("imageUrl"),
        "image_focal_point": transformed.get("imageFocalPoint"),
        "category": transformed.get("category"),
        "canonical_url": transformed.get("url")
        or article_doc.get("canonical_url")
        or article_doc.get("website_url"),
        "publish_date": article_doc.get("publish_date") or transformed.get("publishDate"),
        "created_date": article_doc.get("created_date"),
    }


def _load_articles_by_ids(article_ids: list[Any]) -> dict[str, dict]:
    db = get_db()
    candidates: list[Any] = []
    for article_id in article_ids:
        candidates.extend(_id_candidates(article_id))

    if not candidates:
        return {}

    docs = list(db[ARTICLES_COLLECTION].find({"_id": {"$in": candidates}}))
    articles: dict[str, dict] = {}
    for doc in docs:
        for candidate in _id_candidates(doc.get("_id")):
            articles[str(candidate)] = doc
    return articles


def _story_dto(slides_doc: dict, article_doc: dict | None = None) -> dict[str, Any]:
    article_id = slides_doc.get("article_id")
    article_id_text = str(article_id)
    pages = slides_doc.get("pages") or []
    return {
        "id": article_id_text,
        "article_id": article_id_text,
        "pages": _serialize_doc(pages),
        "metadata": _serialize_doc(_article_metadata(article_doc)),
        "generation_timestamp": slides_doc.get("generation_timestamp"),
        "llm_model_used": slides_doc.get("llm_model_used"),
        "slide_count": slides_doc.get("slide_count") or len(pages),
    }


def get_story(article_id: str) -> dict[str, Any] | None:
    db = get_db()
    candidates = _id_candidates(article_id)
    slides_doc = db[STORY_SLIDES_COLLECTION].find_one(
        {"article_id": {"$in": candidates}, **_usable_pages_query()}
    )
    if not slides_doc:
        return None

    articles = _load_articles_by_ids([slides_doc.get("article_id")])
    article_doc = articles.get(str(slides_doc.get("article_id")))
    return _story_dto(slides_doc, article_doc)


def list_stories(
    page: int = 1,
    limit: int = 100,
    category: str | None = None,
    sort_order: str = "desc",
) -> tuple[list[dict[str, Any]], int]:
    db = get_db()
    query = _usable_pages_query()

    if category:
        article_docs = list(db[ARTICLES_COLLECTION].find({"category": category}, {"_id": 1}))
        article_ids = [doc["_id"] for doc in article_docs]
        slide_ids: list[Any] = []
        for article_id in article_ids:
            slide_ids.extend(_id_candidates(article_id))
        query = {**query, "article_id": {"$in": slide_ids or ["__none__"]}}

    sort_dir = -1 if sort_order == "desc" else 1
    sort_spec = [("generation_timestamp", sort_dir), ("_id", sort_dir)]
    skip = (page - 1) * limit

    slides = list(
        db[STORY_SLIDES_COLLECTION]
        .find(query)
        .sort(sort_spec)
        .skip(skip)
        .limit(limit)
    )
    total = db[STORY_SLIDES_COLLECTION].count_documents(query)
    articles = _load_articles_by_ids([slide.get("article_id") for slide in slides])

    stories = [
        _story_dto(slide, articles.get(str(slide.get("article_id"))))
        for slide in slides
    ]
    return stories, total


def get_stories_by_ids(article_ids: list[str]) -> list[dict[str, Any]]:
    if not article_ids:
        return []

    db = get_db()
    candidates: list[Any] = []
    for article_id in article_ids:
        candidates.extend(_id_candidates(article_id))

    slides = list(
        db[STORY_SLIDES_COLLECTION]
        .find({"article_id": {"$in": candidates}, **_usable_pages_query()})
    )
    articles = _load_articles_by_ids([slide.get("article_id") for slide in slides])

    by_id = {
        str(slide.get("article_id")): _story_dto(
            slide,
            articles.get(str(slide.get("article_id"))),
        )
        for slide in slides
    }
    return [by_id[key] for key in [str(article_id) for article_id in article_ids] if key in by_id]
