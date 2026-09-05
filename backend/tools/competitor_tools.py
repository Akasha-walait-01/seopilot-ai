# This file is our Competitor Analysis tool
# Reuses the same crawler from Phase 2 to fetch competitor pages,
# then builds a simplified summary (titles, headings, topics) that
# can be compared against our own website later.

from backend.tools.crawler import crawl_website

# competitor crawling is kept smaller than a full site audit,
# since we only need enough pages to understand topic coverage
COMPETITOR_MAX_PAGES = 5


def analyze_competitor(competitor_url: str) -> list[dict]:
    """
    Crawl a competitor's website and return simplified page summaries.
    Uses the same crawler as our own site audit, but limits pages crawled.
    """
    crawled_pages = crawl_website(competitor_url, max_pages=COMPETITOR_MAX_PAGES)

    summaries = []
    for page in crawled_pages:
        # skip pages that failed to load, they carry no useful topic data
        if page["status_code"] == 0 or page["status_code"] >= 400:
            continue

        summaries.append({
            "url": page["url"],
            "title": page["title"],
            "h1": page["h1_text"],
            "word_count": page["word_count"],
        })

    return summaries