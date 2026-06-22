import os
import sys
from pathlib import Path

# Add scraper path to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from scraper.utils.html_extractor import extract_article_content
    from scraper.services.story_pipeline.analyzer import analyze_article
    from scraper.services.story_pipeline.story_pipeline import StoryPipeline
    from scraper.services.story_pipeline.gemini_service import build_pages_with_gemini
    from scraper.services.story_pipeline.generator import build_pages
    print("Python import and syntax check: SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Python import and syntax check: FAILED - {e}")
    sys.exit(1)
