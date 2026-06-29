"""MongoDB connection and helpers."""

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

from scraper.config import settings

_client: MongoClient | None = None


def get_client() -> MongoClient:
    """Get or create MongoDB client singleton."""
    global _client
    if _client is None:
        _client = MongoClient(
            settings.mongodb_uri,
            authSource="admin",
            retryWrites=True,
            w="majority",
            serverSelectionTimeoutMS=settings.mongodb_server_selection_timeout_ms,
        )
    return _client


def get_db() -> Database:
    """Get the WAPOW database."""
    return get_client()[settings.mongodb_db_name]


def get_collection(name: str) -> Collection:
    """Get a collection by name."""
    return get_db()[name]


def close_client() -> None:
    """Close the MongoDB client connection."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
