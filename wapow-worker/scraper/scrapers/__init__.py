"""Scraper modules for different content sources."""

from scraper.scrapers.base import BaseScraper, ScrapedItem
from scraper.scrapers.rss_scraper import RSSScraper
from scraper.scrapers.web_scraper import WebScraper

__all__ = [
    "BaseScraper",
    "ScrapedItem",
    "RSSScraper",
    "WebScraper",
]
