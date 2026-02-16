"""WaPOW Event Collector — lightweight FastAPI service that ingests
analytics events from the frontend and writes them to ClickHouse.
"""

from __future__ import annotations

import json
import logging
import re
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import config
from models import CollectRequest, EventPayload
from writer import ClickHouseWriter
import geo

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("collector")

writer = ClickHouseWriter()


# ── App lifecycle ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await writer.start()
    yield
    await writer.stop()


app = FastAPI(title="WaPOW Event Collector", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ────────────────────────────────────────────────────────────────────

_MOBILE_RE = re.compile(r"Mobile|Android|iPhone|iPad", re.IGNORECASE)
_TABLET_RE = re.compile(r"iPad|Tablet", re.IGNORECASE)


def _detect_device(ua: str) -> str:
    if _TABLET_RE.search(ua):
        return "tablet"
    if _MOBILE_RE.search(ua):
        return "mobile"
    return "desktop"


def _extract_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return ""


def _enrich_event(event: EventPayload, request: Request) -> dict:
    """Turn a raw EventPayload into a dict ready for the ClickHouse writer."""
    ip = _extract_ip(request)
    ua = request.headers.get("user-agent", "")
    geo_info = geo.lookup(ip)

    return {
        "event_type": event.event_type,
        "user_id": event.user_id,
        "session_id": event.session_id,
        "content_id": event.content_id,
        "content_type": event.content_type,
        "category": event.category,
        "timestamp": event.timestamp or datetime.now(timezone.utc).isoformat(),
        "properties": event.properties,
        "ip": ip,
        "user_agent": ua,
        "device_type": _detect_device(ua),
        "country": geo_info["country"],
        "city": geo_info["city"],
        "referrer": event.referrer,
    }


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "service": "wapow-collector",
        "version": "1.0.0",
        "endpoints": {
            "collect": "POST /collect",
            "beacon": "POST /collect/beacon",
            "health": "GET /health",
        },
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/collect")
async def collect(body: CollectRequest, request: Request):
    """Ingest a batch of analytics events (JSON body)."""
    count = 0
    for event in body.events:
        row = _enrich_event(event, request)
        await writer.add(row)
        count += 1
    return {"accepted": count}


@app.post("/collect/beacon")
async def collect_beacon(request: Request):
    """Ingest events via navigator.sendBeacon (plain-text body)."""
    raw = await request.body()
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return JSONResponse({"error": "invalid JSON"}, status_code=400)

    events_raw = payload.get("events", [])
    if not isinstance(events_raw, list):
        return JSONResponse({"error": "events must be an array"}, status_code=400)

    count = 0
    for evt in events_raw:
        try:
            event = EventPayload(**evt)
            row = _enrich_event(event, request)
            await writer.add(row)
            count += 1
        except Exception:
            continue  # skip malformed events silently

    return {"accepted": count}


# ── Analytics Query Endpoints ──────────────────────────────────────────────────

def _query_ch(sql: str, params: dict | None = None) -> list[dict]:
    """Run a ClickHouse query and return rows as dicts."""
    if not writer._client:
        return []
    result = writer._client.query(sql, parameters=params or {})
    columns = result.column_names
    return [dict(zip(columns, row)) for row in result.result_rows]


@app.get("/analytics/content/{content_id}")
async def analytics_content(content_id: str, hours: int = 168):
    """Engagement stats for a single content item (default: last 7 days)."""
    rows = _query_ch(
        """
        SELECT
            content_id,
            content_type,
            category,
            sum(views)          AS views,
            sum(likes)          AS likes,
            sum(saves)          AS saves,
            sum(shares)         AS shares,
            sum(comments)       AS comments,
            sum(total_dwell_ms) AS total_dwell_ms,
            sum(event_count)    AS event_count
        FROM content_engagement_hourly
        WHERE content_id = {cid:String}
          AND hour >= now() - INTERVAL {hrs:UInt32} HOUR
        GROUP BY content_id, content_type, category
        """,
        {"cid": content_id, "hrs": hours},
    )
    if not rows:
        return {"content_id": content_id, "data": None}
    return {"content_id": content_id, "data": rows[0]}


@app.get("/analytics/trending")
async def analytics_trending(hours: int = 24, limit: int = 20):
    """Trending content by engagement score in the last N hours."""
    rows = _query_ch(
        """
        SELECT
            content_id,
            content_type,
            category,
            sum(views)          AS views,
            sum(likes)          AS likes,
            sum(saves)          AS saves,
            sum(shares)         AS shares,
            sum(comments)       AS comments,
            sum(total_dwell_ms) AS total_dwell_ms,
            (sum(views) + sum(likes) * 3 + sum(saves) * 5 + sum(shares) * 4 + sum(comments) * 2) AS score
        FROM content_engagement_hourly
        WHERE hour >= now() - INTERVAL {hrs:UInt32} HOUR
          AND content_id != ''
        GROUP BY content_id, content_type, category
        ORDER BY score DESC
        LIMIT {lim:UInt32}
        """,
        {"hrs": hours, "lim": limit},
    )
    return {"hours": hours, "data": rows}


@app.get("/analytics/user/{user_id}/summary")
async def analytics_user_summary(user_id: str, days: int = 30):
    """User engagement summary for the last N days."""
    rows = _query_ch(
        """
        SELECT
            user_id,
            sum(views)          AS views,
            sum(likes)          AS likes,
            sum(saves)          AS saves,
            sum(shares)         AS shares,
            sum(comments)       AS comments,
            sum(total_dwell_ms) AS total_dwell_ms,
            sum(sessions)       AS sessions,
            sum(event_count)    AS event_count,
            min(day)            AS first_active,
            max(day)            AS last_active,
            count()             AS active_days
        FROM user_activity_daily
        WHERE user_id = {uid:String}
          AND day >= today() - {d:UInt32}
        GROUP BY user_id
        """,
        {"uid": user_id, "d": days},
    )
    if not rows:
        return {"user_id": user_id, "data": None}
    data = rows[0]
    # Convert date objects to strings for JSON
    for k in ("first_active", "last_active"):
        if k in data and hasattr(data[k], "isoformat"):
            data[k] = data[k].isoformat()
    return {"user_id": user_id, "data": data}


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT, reload=True)
