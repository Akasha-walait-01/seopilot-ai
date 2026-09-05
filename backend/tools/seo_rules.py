# This file is our deterministic SEO Rule Engine (spec section 16)
# The LLM does NOT decide these facts. Plain Python logic checks them.
#
# UPDATE: fixed a confusing overlap where a blank/empty page and a real
# noindex directive were easy to mix up - they are now two SEPARATE,
# clearly worded issues. Added Mobile Friendliness, Freshness, E-E-A-T
# (author signal), and Crawlability (sitemap/robots.txt) checks.

from datetime import datetime, timezone
from dateutil import parser as date_parser

# recommended length ranges (commonly used SEO guidelines)
TITLE_MIN = 30
TITLE_MAX = 60
META_DESC_MIN = 70
META_DESC_MAX = 160
MIN_WORD_COUNT = 300
EMPTY_CONTENT_WORD_THRESHOLD = 50  # below this, treat as "no real content" not just "thin"
FRESHNESS_STALE_MONTHS = 18  # content older than this gets a freshness note
SLOW_LOAD_TIME_MS = 5000  # crawler-measured load time heuristic, not a real Lighthouse score


def _parse_date_safe(date_string: str | None):
    if not date_string:
        return None
    try:
        parsed = date_parser.parse(date_string)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except (ValueError, TypeError):
        return None


def audit_single_page(page: dict) -> list[dict]:
    """
    Run all deterministic checks on one page.
    Returns a list of issues, each with type, severity, and recommendation.
    """
    issues = []

    # broken page / server error
    if page["status_code"] == 0:
        issues.append({
            "issue_type": "broken_page",
            "severity": "critical",
            "message": f"Page could not be loaded: {page.get('error', 'unknown error')}",
            "recommendation": "Check if the URL is correct and the server is responding.",
        })
        return issues  # no point checking other things on a broken page

    if page["status_code"] >= 400:
        issues.append({
            "issue_type": "http_error",
            "severity": "critical",
            "message": f"Page returned status code {page['status_code']}.",
            "recommendation": "Fix the broken link or set up a proper redirect.",
        })

    # --- EMPTY / NO-CONTENT CHECK (separate from noindex, see below) ---
    # This is reported on its own, clearly worded, so it is never confused
    # with the noindex check further down - they are two different problems
    # that can each be true independently.
    if page["word_count"] < EMPTY_CONTENT_WORD_THRESHOLD:
        issues.append({
            "issue_type": "empty_content_detected",
            "severity": "critical",
            "message": (
                f"This page rendered with almost no visible text ({page['word_count']} words). "
                f"This is a separate issue from indexability - a page can be indexable (no noindex "
                f"tag) and still have no real content, or vice versa."
            ),
            "recommendation": (
                "Open this page in a browser and check if content is actually missing, or if it "
                "loads slowly/via JavaScript that this crawler could not fully capture. If the "
                "page IS genuinely empty, add real content or remove/redirect the page."
            ),
        })
    elif page["word_count"] < MIN_WORD_COUNT:
        issues.append({
            "issue_type": "thin_content",
            "severity": "low",
            "message": f"Page has only {page['word_count']} words.",
            "recommendation": "Consider expanding content to cover the topic more thoroughly.",
        })

    # title checks
    if not page["title"]:
        issues.append({
            "issue_type": "missing_title",
            "severity": "high",
            "message": "Page has no title tag.",
            "recommendation": "Add a unique, descriptive title tag between 30-60 characters.",
        })
    else:
        title_len = len(page["title"])
        if title_len < TITLE_MIN or title_len > TITLE_MAX:
            issues.append({
                "issue_type": "title_length",
                "severity": "medium",
                "message": f"Title is {title_len} characters (recommended {TITLE_MIN}-{TITLE_MAX}).",
                "recommendation": "Rewrite the title to fit the recommended length.",
            })

    # meta description checks
    if not page["meta_description"]:
        issues.append({
            "issue_type": "missing_meta_description",
            "severity": "high",
            "message": "Page has no meta description.",
            "recommendation": "Add a compelling meta description between 70-160 characters.",
        })
    else:
        desc_len = len(page["meta_description"])
        if desc_len < META_DESC_MIN or desc_len > META_DESC_MAX:
            issues.append({
                "issue_type": "meta_description_length",
                "severity": "low",
                "message": f"Meta description is {desc_len} characters (recommended {META_DESC_MIN}-{META_DESC_MAX}).",
                "recommendation": "Adjust meta description length for better search snippet display.",
            })

    # H1 checks
    if page["h1_count"] == 0:
        issues.append({
            "issue_type": "missing_h1",
            "severity": "high",
            "message": "Page has no H1 heading.",
            "recommendation": "Add exactly one H1 heading that describes the page's main topic.",
        })
    elif page["h1_count"] > 1:
        issues.append({
            "issue_type": "multiple_h1",
            "severity": "medium",
            "message": f"Page has {page['h1_count']} H1 headings.",
            "recommendation": "Use only one H1 heading per page for clear topical structure.",
        })

    # canonical check
    if not page["canonical"]:
        issues.append({
            "issue_type": "missing_canonical",
            "severity": "medium",
            "message": "Page has no canonical tag.",
            "recommendation": "Add a self-referencing canonical tag to avoid duplicate content issues.",
        })

    # alt text check
    if page["images_missing_alt"] > 0:
        issues.append({
            "issue_type": "missing_alt_text",
            "severity": "medium",
            "message": f"{page['images_missing_alt']} image(s) missing alt text.",
            "recommendation": "Add descriptive alt text to all images for accessibility and image SEO.",
        })

    # structured data check
    if not page["has_schema"]:
        issues.append({
            "issue_type": "missing_schema",
            "severity": "low",
            "message": "No structured data (JSON-LD) found on this page.",
            "recommendation": "Add relevant schema markup (Article, Organization, FAQ, etc).",
        })

    # indexability check - reported on its own, worded clearly so it is
    # understood as a separate fact from the empty-content check above.
    # NOTE: if this fires on EVERY page of a WordPress site, the real cause
    # is usually the sitewide "Discourage search engines from indexing this
    # site" checkbox under Settings > Reading in WordPress, not a per-page
    # mistake - the recommendation below reflects that.
    if page["robots_meta"] and "noindex" in page["robots_meta"].lower():
        issues.append({
            "issue_type": "noindex_page",
            "severity": "critical",
            "message": "Page has a noindex directive in its HTML, it will not appear in search results.",
            "recommendation": (
                "If this appears on EVERY page of the site, check WordPress Settings > Reading > "
                "'Discourage search engines from indexing this site' - that single checkbox adds "
                "noindex sitewide. If it's only on specific pages, remove the noindex tag from those."
            ),
        })

    # --- MOBILE FRIENDLINESS CHECK ---
    if not page.get("has_viewport_meta"):
        issues.append({
            "issue_type": "missing_viewport_meta",
            "severity": "high",
            "message": "Page has no responsive viewport meta tag.",
            "recommendation": "Add <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"> so the page scales correctly on mobile devices.",
        })

    # --- FRESHNESS CHECK ---
    modified_date = _parse_date_safe(page.get("modified_date"))
    published_date = _parse_date_safe(page.get("published_date"))
    reference_date = modified_date or published_date

    if not reference_date:
        issues.append({
            "issue_type": "no_freshness_signal",
            "severity": "low",
            "message": "No published or last-modified date could be found on this page.",
            "recommendation": "Add a visible or structured (schema/meta) published/updated date, especially for time-sensitive content.",
        })
    else:
        months_old = (datetime.now(timezone.utc) - reference_date).days / 30
        if months_old > FRESHNESS_STALE_MONTHS:
            issues.append({
                "issue_type": "content_may_be_outdated",
                "severity": "medium",
                "message": f"Content was last updated/published about {int(months_old)} months ago.",
                "recommendation": "Review this page and refresh outdated information, especially for topics that change over time.",
            })

    # --- E-E-A-T: AUTHOR SIGNAL CHECK ---
    if not page.get("author_detected"):
        issues.append({
            "issue_type": "missing_author_info",
            "severity": "medium",
            "message": "No author or byline information detected on this page.",
            "recommendation": "Add visible author information (name, credentials/bio link) to strengthen E-E-A-T signals, especially for YMYL (Your Money Your Life) topics.",
        })

    # --- BASIC PERFORMANCE HEURISTIC (crawler-measured, not a real Lighthouse score) ---
    load_time_ms = page.get("page_load_time_ms")
    if load_time_ms and load_time_ms > SLOW_LOAD_TIME_MS:
        issues.append({
            "issue_type": "slow_crawl_load_time",
            "severity": "medium",
            "message": f"This page took {round(load_time_ms / 1000, 1)}s to fully load during crawling.",
            "recommendation": "This is a rough heuristic, not a real Lighthouse score. Run the Page Speed check (PageSpeed Insights) for accurate, actionable performance data.",
        })

    return issues


def check_crawlability_issues(crawlability_data: dict) -> list[dict]:
    """
    Site-level (not per-page) issues from check_site_crawlability() in crawler.py.
    """
    issues = []

    if not crawlability_data.get("robots_txt_found"):
        issues.append({
            "url": None,
            "issue_type": "missing_robots_txt",
            "severity": "medium",
            "message": "No robots.txt file found at the site root.",
            "recommendation": "Add a robots.txt file to guide search engine crawlers.",
        })

    if not crawlability_data.get("sitemap_found"):
        issues.append({
            "url": None,
            "issue_type": "missing_sitemap",
            "severity": "medium",
            "message": "No XML sitemap found at common locations (/sitemap.xml, /sitemap_index.xml).",
            "recommendation": "Generate and submit an XML sitemap to help search engines discover and index your pages.",
        })

    return issues


def find_duplicate_titles_and_descriptions(pages: list[dict]) -> list[dict]:
    # cross-page check: detect duplicate titles and meta descriptions across the site
    issues = []

    title_map = {}
    desc_map = {}

    for page in pages:
        if page["title"]:
            title_map.setdefault(page["title"], []).append(page["url"])
        if page["meta_description"]:
            desc_map.setdefault(page["meta_description"], []).append(page["url"])

    for title, urls in title_map.items():
        if len(urls) > 1:
            issues.append({
                "url": urls[0],
                "issue_type": "duplicate_title",
                "severity": "medium",
                "message": f"Title '{title}' is used on {len(urls)} pages: {', '.join(urls)}",
                "recommendation": "Write a unique title for each page.",
            })

    for desc, urls in desc_map.items():
        if len(urls) > 1:
            issues.append({
                "url": urls[0],
                "issue_type": "duplicate_meta_description",
                "severity": "low",
                "message": f"Meta description is duplicated on {len(urls)} pages: {', '.join(urls)}",
                "recommendation": "Write a unique meta description for each page.",
            })

    return issues


# severity weights used for scoring
SEVERITY_WEIGHTS = {
    "critical": 20,
    "high": 10,
    "medium": 5,
    "low": 2,
}


def calculate_seo_score(all_issues: list[dict], total_pages: int) -> dict:
    """
    Calculate a transparent SEO score out of 100.
    Score = 100 - (weighted penalty per issue, normalized by page count).
    """
    if total_pages == 0:
        return {"score": 0, "explanation": "No pages were crawled."}

    total_penalty = sum(SEVERITY_WEIGHTS.get(issue["severity"], 0) for issue in all_issues)

    # normalize penalty so a bigger site isn't unfairly punished for having more pages
    normalized_penalty = total_penalty / total_pages

    score = max(0, round(100 - normalized_penalty, 1))

    issue_counts = {}
    for issue in all_issues:
        issue_counts[issue["severity"]] = issue_counts.get(issue["severity"], 0) + 1

    return {
        "score": score,
        "total_issues": len(all_issues),
        "issues_by_severity": issue_counts,
        "explanation": f"Score starts at 100 and is reduced based on issue severity, "
                        f"normalized across {total_pages} page(s) crawled.",
    }