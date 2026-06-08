"""Content processors for normalization and deduplication."""

from scraper.processors.normalizer import ContentNormalizer
from scraper.processors.deduplicator import Deduplicator

__all__ = ["ContentNormalizer", "Deduplicator"]
