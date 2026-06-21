import asyncio
from typing import Dict

# Dictionary mapping job ID (e.g. 'rss_feeds') to its running asyncio.Task instance
active_tasks: Dict[str, asyncio.Task] = {}
