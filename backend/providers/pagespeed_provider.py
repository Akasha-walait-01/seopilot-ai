# This file is our Google PageSpeed Insights integration.
# Real performance data (Lighthouse scores) for a given URL, for both
# mobile and desktop strategies. If no API key is configured, this
# returns a clear "not configured" result instead of a fake score.
# API docs: https://developers.google.com/speed/docs/insights/v5/get-started

import requests
from backend.config import settings

PAGESPEED_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


def check_pagespeed(page_url: str, strategy: str = "mobile") -> dict:
    """
    Calls the real Google PageSpeed Insights API for one URL and strategy
    ("mobile" or "desktop"). Returns real Lighthouse scores/metrics, or a
    clear "not configured"/error result - never a fabricated score.
    """
    if not settings.pagespeed_api_key:
        return {
            "configured": False,
            "message": "PageSpeed Insights API key not configured. Add PAGESPEED_API_KEY to your .env file.",
        }

    params = {
        "url": page_url,
        "key": settings.pagespeed_api_key,
        "strategy": strategy,
        "category": ["PERFORMANCE", "SEO", "ACCESSIBILITY", "BEST_PRACTICES"],
    }

    try:
        response = requests.get(PAGESPEED_ENDPOINT, params=params, timeout=60)
        if response.status_code != 200:
            return {
                "configured": True,
                "success": False,
                "message": f"PageSpeed Insights API returned an error ({response.status_code}): {response.text[:300]}",
            }

        data = response.json()
        lighthouse = data.get("lighthouseResult", {})
        categories = lighthouse.get("categories", {})
        audits = lighthouse.get("audits", {})

        def category_score(name):
            cat = categories.get(name)
            if not cat or cat.get("score") is None:
                return None
            return round(cat["score"] * 100)

        def audit_value(audit_id, key="displayValue"):
            audit = audits.get(audit_id)
            return audit.get(key) if audit else None

        return {
            "configured": True,
            "success": True,
            "strategy": strategy,
            "performance_score": category_score("performance"),
            "seo_score": category_score("seo"),
            "accessibility_score": category_score("accessibility"),
            "best_practices_score": category_score("best-practices"),
            "first_contentful_paint": audit_value("first-contentful-paint"),
            "largest_contentful_paint": audit_value("largest-contentful-paint"),
            "total_blocking_time": audit_value("total-blocking-time"),
            "cumulative_layout_shift": audit_value("cumulative-layout-shift"),
            "speed_index": audit_value("speed-index"),
        }

    except requests.exceptions.RequestException as e:
        return {"configured": True, "success": False, "message": f"Could not reach PageSpeed Insights API: {e}"}