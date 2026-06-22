import os
import sys
from pathlib import Path

# Add scraper path to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper.services.story_pipeline.analyzer import AnalyzedArticle
from scraper.services.story_pipeline.generator import build_pages

# Test single image / no image case
single_article = AnalyzedArticle(
    title="Central Topic Article",
    description="This is an article description.",
    body_text="Here is the body text of the article. It talks about the central topic. It has some unrelated side details that should be ignored.",
    word_count=50,
    image_urls=["http://example.com/promo.jpg"],
    video_items=[]
)

pages_single = build_pages(single_article)
print(f"Single image pages count: {len(pages_single)}")
for i, p in enumerate(pages_single):
    print(f"  Page {i} type: {p['page_type']}, content items: {len(p['content'])}")
    for item in p['content']:
        print(f"    - {item['type']}: {item.get('content') or item.get('content_url')}")

# Test multiple images case
multi_article = AnalyzedArticle(
    title="Multiple Images Article",
    description="This is an article description.",
    body_text="Here is the body text of the article. It talks about a couple of things.",
    word_count=150,
    image_urls=["http://example.com/1.jpg", "http://example.com/2.jpg", "http://example.com/3.jpg"],
    video_items=[]
)

pages_multi = build_pages(multi_article)
print(f"Multiple images pages count: {len(pages_multi)}")
for i, p in enumerate(pages_multi):
    print(f"  Page {i} type: {p['page_type']}, content items: {len(p['content'])}")
    for item in p['content']:
        print(f"    - {item['type']}: {item.get('content') or item.get('content_url')}")

assert len(pages_single) == 1, "Expected exactly 1 slide for single image"
assert pages_single[0]['page_type'] == 'content', "Expected content page type"

assert len(pages_multi) == 4, "Expected 3 content slides + 1 overview slide"
print("Unit test assertions: PASSED")
