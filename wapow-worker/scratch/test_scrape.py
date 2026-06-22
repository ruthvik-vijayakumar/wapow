import os
import sys
import asyncio
from pathlib import Path

# Add scraper path to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

async def main():
    # Load settings to make sure keys etc. are populated
    from scraper.config import settings
    # Set logging to debug
    import logging
    logging.basicConfig(level=logging.INFO)
    
    from scraper.tasks.jobs import run_rss_scrape
    res = await run_rss_scrape()
    print("Scrape results:", res)

if __name__ == "__main__":
    asyncio.run(main())
