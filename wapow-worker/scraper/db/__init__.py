"""Database module for WAPOW Scraper."""

from scraper.db.mongodb import get_client, get_db, get_collection

__all__ = ["get_client", "get_db", "get_collection"]
