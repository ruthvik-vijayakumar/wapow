import os
import sys
from pathlib import Path

# Add scraper path to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper.services.story_pipeline.service import _build_ai_summary
from scraper.services.story_pipeline.analyzer import analyze_article

# Mock article mongo document
mock_doc = {
    "title": "Article Title",
    "description": "Article description detailing central topic.",
    "content_elements": [
        {"type": "text", "content": "This is paragraph 1 of the article. It talks about the central topic."},
        {"type": "text", "content": "This is paragraph 2 of the article. It has some other info."},
    ],
    "promo_items": {
        "basic": {
            "url": "http://example.com/promo.jpg"
        }
    }
}

analyzed = analyze_article(mock_doc)
summary = _build_ai_summary(mock_doc, analyzed, use_llm_overview=True)
print("Fallback builder summary output:")
print(summary)

assert summary["slide_count"] == 1
assert summary["llm_model_used"] == "heuristic-v1"
print("Service integration test: PASSED")
