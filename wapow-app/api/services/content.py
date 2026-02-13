"""Content service: shared MongoDB query logic for all collections."""
from typing import Any

from bson import ObjectId
from pymongo.collection import Collection

from api.db import get_db
from api.config import ARTICLE_CATEGORIES, ARTICLES_COLLECTION


def _serialize_doc(doc: dict) -> dict:
    """Convert BSON types for JSON (e.g. ObjectId -> str)."""
    if doc is None:
        return doc
    out = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            out[k] = str(v)
        elif isinstance(v, dict):
            out[k] = _serialize_doc(v)
        elif isinstance(v, list):
            out[k] = [
                _serialize_doc(x) if isinstance(x, dict) else x
                for x in v
            ]
        else:
            out[k] = v
    return out


def _transform_content_item(item: dict) -> dict:
    """Normalize content item for API response (content collections)."""
    headlines = item.get("headlines") or {}
    description = item.get("description")
    if isinstance(description, dict):
        desc_text = description.get("basic") or description.get("") or ""
    else:
        desc_text = description or ""
    credits = item.get("credits") or {}
    by_list = credits.get("by") or []
    author = by_list[0].get("name") if by_list else item.get("author") or "Unknown"
    lead_art = item.get("lead_art") or {}
    promo = item.get("promo_items") or {}
    basic_promo = promo.get("basic") or {}
    image_url = (
        lead_art.get("url")
        or basic_promo.get("url")
        or item.get("imageUrl")
    )
    taxonomy = item.get("taxonomy") or {}
    primary = taxonomy.get("primary_section") or {}
    category = (
        item.get("category")
        or primary.get("name")
        or (item.get("tracking") or {}).get("video_section")
        or ((item.get("additional_properties") or {}).get("series_meta") or {}).get("name")
    )
    _id = item.get("_id")
    return {
        "id": str(_id) if isinstance(_id, ObjectId) else _id,
        "title": headlines.get("basic") or item.get("title") or "Untitled",
        "description": desc_text,
        "author": author,
        "imageUrl": image_url,
        "publishDate": item.get("publish_date") or item.get("created_date"),
        "category": category,
        "url": item.get("canonical_url") or item.get("website_url"),
        "isActive": item.get("isActive"),
        **_serialize_doc(item),
    }


def _transform_video_item(item: dict) -> dict:
    """Normalize video item for API response."""
    tracking = item.get("tracking") or {}
    promo = item.get("promo_image") or {}
    _id = item.get("_id")
    return {
        "id": str(_id) if isinstance(_id, ObjectId) else _id,
        "title": tracking.get("page_title") or item.get("title") or "Untitled Video",
        "description": tracking.get("av_name") or "",
        "imageUrl": promo.get("url") or item.get("imageUrl"),
        "videoSection": tracking.get("video_section") or item.get("category") or "Unknown",
        "videoCategory": tracking.get("video_category") or "Unknown",
        "duration": item.get("duration"),
        "aspectRatio": item.get("aspect_ratio"),
        "canonicalUrl": item.get("canonical_url"),
        "contentId": item.get("content_id"),
        "streams": item.get("streams"),
        "isActive": item.get("isActive"),
        **_serialize_doc(item),
    }


def _transform_podcast_item(item: dict) -> dict:
    """Normalize podcast item for API response."""
    add_props = item.get("additional_properties") or {}
    _id = item.get("_id")
    return {
        "id": str(_id) if isinstance(_id, ObjectId) else _id,
        "title": add_props.get("page_title") or item.get("title") or "Untitled",
        "description": add_props.get("description") or "",
        "imageUrl": (add_props.get("lead_art") or {}).get("url") or item.get("imageUrl"),
        "isActive": item.get("isActive"),
        **_serialize_doc(item),
    }


def get_collection(collection_name: str) -> Collection:
    """Return MongoDB collection. Article categories use the unified 'articles' collection."""
    if collection_name in ARTICLE_CATEGORIES:
        return get_db()[ARTICLES_COLLECTION]
    return get_db()[collection_name]


def list_items(
    collection_name: str,
    page: int = 1,
    limit: int = 100,
    category: str | None = None,
    search: str | None = None,
    sort_by: str = "created_date",
    sort_order: str = "desc",
    is_video: bool = False,
    is_podcast: bool = False,
) -> tuple[list[dict], int]:
    """Query collection with filters, sort, pagination. Returns (items, total)."""
    coll = get_collection(collection_name)
    query: dict[str, Any] = {}

    # Article categories: filter by top-level 'category' field (sports, style, etc.)
    if collection_name in ARTICLE_CATEGORIES:
        query["category"] = collection_name

    if category:
        query["$or"] = [
            {"category": {"$regex": category, "$options": "i"}},
            {"taxonomy.primary_section.name": {"$regex": category, "$options": "i"}},
            {"tracking.video_section": {"$regex": category, "$options": "i"}},
            {"additional_properties.series_meta.name": {"$regex": category, "$options": "i"}},
        ]

    if search:
        search_or = [
            {"headlines.basic": {"$regex": search, "$options": "i"}},
            {"title": {"$regex": search, "$options": "i"}},
            {"description.basic": {"$regex": search, "$options": "i"}},
            {"content": {"$regex": search, "$options": "i"}},
        ]
        if query:
            query = {"$and": [query, {"$or": search_or}]}
        else:
            query["$or"] = search_or

    sort_field = sort_by
    if sort_by in ("createdAt", "created_date"):
        sort_field = "created_date"
    elif sort_by in ("publishDate", "publish_date"):
        sort_field = "publish_date"
    elif sort_by == "title":
        sort_field = "headlines.basic"

    sort_dir = -1 if sort_order == "desc" else 1
    sort_spec: list[tuple[str, int]] = [(sort_field, sort_dir)]
    if sort_field not in ("created_date", "publish_date"):
        sort_spec.append(("created_date", -1))

    skip = (page - 1) * limit
    cursor = coll.find(query).sort(sort_spec).skip(skip).limit(limit)
    items = list(cursor)
    total = coll.count_documents(query)

    if is_podcast:
        transform = _transform_podcast_item
    elif is_video:
        transform = _transform_video_item
    else:
        transform = _transform_content_item

    return [transform(i) for i in items], total


def get_by_id(collection_name: str, id_value: str) -> dict | None:
    """Get a single document by _id (string or ObjectId)."""
    coll = get_collection(collection_name)
    try:
        oid = ObjectId(id_value)
    except Exception:
        oid = id_value
    doc = coll.find_one({"_id": oid})
    if doc is None and id_value != oid:
        doc = coll.find_one({"_id": id_value})
    return _serialize_doc(doc) if doc else None


def _article_category_query(collection_name: str) -> dict | None:
    """Base query for article categories (filter by top-level category field)."""
    if collection_name in ARTICLE_CATEGORIES:
        return {"category": collection_name}
    return None


def get_categories(collection_name: str) -> list[str]:
    """Get distinct categories from various fields."""
    coll = get_collection(collection_name)
    base = _article_category_query(collection_name) or {}
    a = set(coll.distinct("category", base))
    b = set(coll.distinct("taxonomy.primary_section.name", base))
    c = set(coll.distinct("tracking.video_section", base))
    d = set(coll.distinct("additional_properties.series_meta.name", base))
    combined = [x for x in (a | b | c | d) if x and (x.strip() if isinstance(x, str) else True)]
    return sorted(set(combined))


def get_stats(collection_name: str) -> dict:
    """Get total count and category counts."""
    coll = get_collection(collection_name)
    base = _article_category_query(collection_name) or {}
    total = coll.count_documents(base)
    match1 = {**base, "category": {"$exists": True, "$ne": None, "$ne": ""}} if base else {"category": {"$exists": True, "$ne": None, "$ne": ""}}
    pipelines = [
        {"$match": match1},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    cat1 = list(coll.aggregate(pipelines))
    match_tax = {**base, "taxonomy.primary_section.name": {"$exists": True, "$ne": None, "$ne": ""}} if base else {"taxonomy.primary_section.name": {"$exists": True, "$ne": None, "$ne": ""}}
    pipelines2 = [
        {"$match": match_tax},
        {"$group": {"_id": "$taxonomy.primary_section.name", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    cat2 = list(coll.aggregate(pipelines2))
    match_track = {**base, "tracking.video_section": {"$exists": True, "$ne": None, "$ne": ""}} if base else {"tracking.video_section": {"$exists": True, "$ne": None, "$ne": ""}}
    pipelines3 = [
        {"$match": match_track},
        {"$group": {"_id": "$tracking.video_section", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    cat3 = list(coll.aggregate(pipelines3))
    merged: dict[str, int] = {}
    for row in cat1 + cat2 + cat3:
        key = row["_id"]
        merged[key] = merged.get(key, 0) + row["count"]
    category_counts = [{"_id": k, "count": v} for k, v in sorted(merged.items(), key=lambda x: -x[1])]
    return {"totalItems": total, "categoryCounts": category_counts}


def get_authors(collection_name: str) -> list[str]:
    """Get distinct authors."""
    coll = get_collection(collection_name)
    base = _article_category_query(collection_name) or {}
    simple = set(coll.distinct("author", base))
    match = {**base, "credits.by": {"$exists": True, "$ne": []}} if base else {"credits.by": {"$exists": True, "$ne": []}}
    pipeline = [
        {"$match": match},
        {"$unwind": "$credits.by"},
        {"$group": {"_id": "$credits.by.name", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    nested = list(coll.aggregate(pipeline))
    for row in nested:
        if row.get("_id") and (row["_id"].strip() if isinstance(row["_id"], str) else True):
            simple.add(row["_id"])
    return sorted(simple)


def get_by_ids(
    collection_name: str,
    ids: list[str],
    max_ids: int = 100,
    transform_content: bool = True,
    is_video: bool = False,
    is_podcast: bool = False,
) -> tuple[list[dict], int, int, bool]:
    """Fetch documents by _id list. Returns (items, requested, returned, limited)."""
    coll = get_collection(collection_name)
    limited = ids[:max_ids]
    id_list: list[Any] = []
    for i in limited:
        try:
            id_list.append(ObjectId(i))
        except Exception:
            id_list.append(i)
    query: dict = {"_id": {"$in": id_list}}
    base = _article_category_query(collection_name)
    if base:
        query = {"$and": [query, base]}
    items = list(coll.find(query))
    if transform_content:
        if is_podcast:
            transform = _transform_podcast_item
        elif is_video:
            transform = _transform_video_item
        else:
            transform = _transform_content_item
        items = [transform(i) for i in items]
    else:
        items = [_serialize_doc(i) for i in items]
    return items, len(ids), len(items), len(limited) < len(ids)
