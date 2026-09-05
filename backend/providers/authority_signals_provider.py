# This file covers two SEO signals that need real external data this
# project does not have access to yet:
# 1. Backlinks - needs a paid API (Ahrefs, Moz, SEMrush, Majestic)
# 2. User Signals (CTR, dwell time, bounce rate) - needs real data from
#    Google Search Console (CTR) and Google Analytics (dwell time), which
#    require OAuth setup this project has not done (same as the SERP
#    provider's status).
# Per this project's rule against fabricated SEO data, both return a clear
# "not configured" result. This file is ready to be filled in once a real
# provider (e.g. Ahrefs API key, or Search Console OAuth) is connected.


def check_backlinks(domain: str) -> dict:
    return {
        "configured": False,
        "domain": domain,
        "message": (
            "Backlink data is not configured. This requires a paid API such as Ahrefs, "
            "Moz, SEMrush, or Majestic. No backlink numbers are shown until a real "
            "provider is connected, to avoid displaying fabricated data."
        ),
    }


def check_user_signals(page_url: str) -> dict:
    return {
        "configured": False,
        "page_url": page_url,
        "message": (
            "User engagement signals (CTR, dwell time, bounce rate) are not configured. "
            "CTR requires Google Search Console OAuth, and dwell time/bounce rate require "
            "Google Analytics. No numbers are shown until these are connected, to avoid "
            "displaying fabricated data."
        ),
    }