"""Shared log sink for the worker dashboard live terminal."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
import os
from typing import Any

from bson import ObjectId

LOG_COLLECTION = "worker_logs"
_HANDLER_NAME = "wapow-dashboard-mongo"


class MongoLogHandler(logging.Handler):
    """Persist worker/API log records so dashboard SSE can stream across processes."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            from scraper.db import get_db

            message = self.format(record)
            get_db()[LOG_COLLECTION].insert_one(
                {
                    "created_at": datetime.now(timezone.utc),
                    "level": record.levelname,
                    "logger": record.name,
                    "process": os.getenv("HOSTNAME") or str(os.getpid()),
                    "message": message,
                }
            )
        except Exception:
            # Logging must never break scraper or Celery execution.
            pass


def _has_dashboard_handler(logger: logging.Logger) -> bool:
    return any(getattr(handler, "name", "") == _HANDLER_NAME for handler in logger.handlers)


def _make_dashboard_handler(level: int) -> MongoLogHandler:
    handler = MongoLogHandler()
    handler.name = _HANDLER_NAME
    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    return handler


def configure_dashboard_logging(level: int = logging.INFO, logger: logging.Logger | None = None) -> None:
    target_logger = logger or logging.getLogger()
    if _has_dashboard_handler(target_logger):
        return

    target_logger.addHandler(_make_dashboard_handler(level))


def ensure_log_indexes() -> None:
    from scraper.db import get_db

    coll = get_db()[LOG_COLLECTION]
    coll.create_index("created_at")
    coll.delete_many({"created_at": {"$lt": datetime.now(timezone.utc) - timedelta(days=7)}})


def serialize_log_doc(doc: dict[str, Any]) -> str:
    return str(doc.get("message") or "")


def get_recent_logs(limit: int = 100) -> list[dict[str, Any]]:
    from scraper.db import get_db

    docs = list(get_db()[LOG_COLLECTION].find().sort("_id", -1).limit(limit))
    docs.reverse()
    return docs


def get_logs_after(last_seen: ObjectId | None, limit: int = 200) -> list[dict[str, Any]]:
    from scraper.db import get_db

    query: dict[str, Any] = {}
    if last_seen is not None:
        query["_id"] = {"$gt": last_seen}
    return list(get_db()[LOG_COLLECTION].find(query).sort("_id", 1).limit(limit))
