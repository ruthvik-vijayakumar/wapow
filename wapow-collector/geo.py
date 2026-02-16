"""Lightweight IP-to-geo lookup using MaxMind GeoLite2.

If the database file is not available, lookups silently return empty strings.
"""

from __future__ import annotations
import os
from typing import Optional

_reader = None


def _get_reader():
    global _reader
    if _reader is not None:
        return _reader

    db_path = os.getenv("MAXMIND_DB_PATH", "")
    if not db_path or not os.path.isfile(db_path):
        return None

    try:
        import geoip2.database
        _reader = geoip2.database.Reader(db_path)
    except Exception:
        _reader = None
    return _reader


def lookup(ip: str) -> dict:
    """Return {"country": ..., "city": ...} for the given IP.

    Returns empty strings if the lookup fails or the DB is unavailable.
    """
    reader = _get_reader()
    if reader is None:
        return {"country": "", "city": ""}

    try:
        resp = reader.city(ip)
        return {
            "country": resp.country.iso_code or "",
            "city": resp.city.name or "",
        }
    except Exception:
        return {"country": "", "city": ""}
