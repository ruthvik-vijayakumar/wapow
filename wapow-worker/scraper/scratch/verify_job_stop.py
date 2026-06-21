import sys
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

# Add wapow-worker directory to sys.path to resolve imports
WORKER_DIR = Path("/Users/coderuth/Desktop/wapow/wapow-worker")
sys.path.insert(0, str(WORKER_DIR))

# Mock dependencies to prevent MongoDB connection attempts
sys.modules['scraper.db'] = MagicMock()
sys.modules['scraper.db.mongodb'] = MagicMock()

async def test_job_cancellation():
    from scraper.tasks.running import active_tasks
    from scraper.tasks.jobs import run_rss_scrape

    print("Testing RSS Scrape Job Cancellation...")

    # Mock load_sources
    mock_source = MagicMock()
    mock_source.name = "Test RSS"
    mock_source.url = "http://testrss.com"
    mock_source.category = "tech"
    mock_source.enabled = True

    mock_sources = MagicMock()
    mock_sources.rss = [mock_source]

    # Mock RSSScraper
    # We want scrape to sleep for 5 seconds to give us time to cancel it
    async def slow_scrape():
        print("Scraper starting slow scrape...")
        try:
            await asyncio.sleep(5)
            print("Scraper finished slow scrape without cancellation (should not happen in this test!)")
            return []
        except asyncio.CancelledError:
            print("Scraper received CancelledError inside mock scraper!")
            raise

    # Setup patches
    with patch("scraper.tasks.jobs.load_sources", return_value=mock_sources), \
         patch("scraper.tasks.jobs.RSSScraper") as mock_scraper_class, \
         patch("scraper.tasks.jobs._save_raw_articles", new_callable=AsyncMock), \
         patch("scraper.tasks.jobs._save_items", new_callable=AsyncMock), \
         patch("scraper.tasks.jobs.update_source_status") as mock_update_status, \
         patch("scraper.tasks.jobs.ScraperRunTracker") as mock_tracker_class:

        # Mock the scraper instance
        mock_scraper_inst = MagicMock()
        mock_scraper_inst.scrape = slow_scrape
        mock_scraper_class.return_value = mock_scraper_inst

        # Run scrape in the background
        scrape_task = asyncio.create_task(run_rss_scrape())

        # Give it a moment to start and register
        await asyncio.sleep(0.5)

        # Assert task is registered
        assert "rss_feeds" in active_tasks, "Job was not registered in active_tasks!"
        print("Successfully verified job registered in active_tasks.")

        # Cancel the task
        print("Cancelling the job task...")
        active_tasks["rss_feeds"].cancel()

        # Await the task, expecting a CancelledError
        try:
            await scrape_task
            print("ERROR: Job completed successfully without raising CancelledError!")
            assert False, "Job did not raise CancelledError"
        except asyncio.CancelledError:
            print("Successfully caught CancelledError in main test loop!")

        # Verify task is cleaned up
        assert "rss_feeds" not in active_tasks, "Job task was not removed from active_tasks after cancellation!"
        print("Successfully verified job task removed from active_tasks.")
        
        # Verify status update was called with 'cancelled'
        # update_source_status is called in the finally block
        cancelled_calls = [call for call in mock_update_status.call_args_list if call.kwargs.get("status") == "cancelled"]
        assert len(cancelled_calls) > 0, "update_source_status was not called with status='cancelled'"
        print("Successfully verified source status updated to 'cancelled'.")

        print("\nAll cancellation tests passed!")

if __name__ == "__main__":
    asyncio.run(test_job_cancellation())
