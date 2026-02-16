"""Async batch writer for ClickHouse.

Accumulates rows in an internal buffer and flushes them to ClickHouse
either when the buffer reaches `FLUSH_BATCH_SIZE` or every
`FLUSH_INTERVAL_SECONDS`, whichever comes first.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

import clickhouse_connect

from config import (
    CLICKHOUSE_DB,
    CLICKHOUSE_HOST,
    CLICKHOUSE_PASSWORD,
    CLICKHOUSE_PORT,
    CLICKHOUSE_USER,
    FLUSH_BATCH_SIZE,
    FLUSH_INTERVAL_SECONDS,
)

logger = logging.getLogger("collector.writer")

# Column order must match the INSERT
_COLUMNS = [
    "event_type",
    "user_id",
    "session_id",
    "content_id",
    "content_type",
    "category",
    "timestamp",
    "properties",
    "ip",
    "user_agent",
    "device_type",
    "country",
    "city",
    "referrer",
]


class ClickHouseWriter:
    """Buffered ClickHouse batch writer."""

    def __init__(self) -> None:
        self._buffer: list[list[Any]] = []
        self._lock = asyncio.Lock()
        self._client = None
        self._flush_task: asyncio.Task | None = None

    # ── lifecycle ──────────────────────────────────────────────────────

    async def start(self) -> None:
        """Connect to ClickHouse and start the periodic flush loop."""
        try:
            self._client = clickhouse_connect.get_client(
                host=CLICKHOUSE_HOST,
                port=CLICKHOUSE_PORT,
                database=CLICKHOUSE_DB,
                username=CLICKHOUSE_USER,
                password=CLICKHOUSE_PASSWORD,
            )
            logger.info(
                "Connected to ClickHouse at %s:%s/%s",
                CLICKHOUSE_HOST,
                CLICKHOUSE_PORT,
                CLICKHOUSE_DB,
            )
        except Exception:
            logger.warning(
                "Could not connect to ClickHouse at %s:%s — events will be buffered and dropped",
                CLICKHOUSE_HOST,
                CLICKHOUSE_PORT,
            )
            self._client = None
        self._flush_task = asyncio.create_task(self._periodic_flush())

    async def stop(self) -> None:
        """Flush remaining events and close the connection."""
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        await self.flush()
        if self._client:
            self._client.close()
            logger.info("ClickHouse connection closed")

    # ── public API ─────────────────────────────────────────────────────

    async def add(self, row: dict) -> None:
        """Add a single enriched event row to the buffer."""
        ordered = [row.get(col, "") for col in _COLUMNS]
        # Serialize properties dict → JSON string
        idx_props = _COLUMNS.index("properties")
        if isinstance(ordered[idx_props], dict):
            ordered[idx_props] = json.dumps(ordered[idx_props])
        elif not ordered[idx_props]:
            ordered[idx_props] = "{}"

        # Ensure timestamp is a datetime
        idx_ts = _COLUMNS.index("timestamp")
        ts = ordered[idx_ts]
        if isinstance(ts, str) and ts:
            try:
                ordered[idx_ts] = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                ordered[idx_ts] = datetime.now(timezone.utc)
        elif not ts:
            ordered[idx_ts] = datetime.now(timezone.utc)

        async with self._lock:
            self._buffer.append(ordered)

        if len(self._buffer) >= FLUSH_BATCH_SIZE:
            await self.flush()

    async def flush(self) -> None:
        """Write the current buffer to ClickHouse."""
        async with self._lock:
            if not self._buffer:
                return
            batch = self._buffer[:]
            self._buffer.clear()

        if not self._client:
            logger.warning("Cannot flush — no ClickHouse client")
            return

        try:
            self._client.insert(
                "events",
                batch,
                column_names=_COLUMNS,
            )
            logger.info("Flushed %d events to ClickHouse", len(batch))
        except Exception:
            logger.exception("Failed to flush %d events", len(batch))
            # Put them back so we retry next flush
            async with self._lock:
                self._buffer = batch + self._buffer

    # ── internal ───────────────────────────────────────────────────────

    async def _periodic_flush(self) -> None:
        """Periodically flush the buffer."""
        while True:
            await asyncio.sleep(FLUSH_INTERVAL_SECONDS)
            await self.flush()
