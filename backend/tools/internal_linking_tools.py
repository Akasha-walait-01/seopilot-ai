# This file is our Internal Linking Agent.
# It only suggests links between pages that are ALREADY crawled for this
# website - it never invents new pages or URLs that don't exist yet.
# This is suggestions only - nothing gets auto-edited into any page.

import json
import re
from backend.providers.llm_provider import ask_llm


def analyze_internal_linking(
    our_pages: list[dict],
    business_description: str,
    country: str,
    language: str,
) -> list[dict]:
    """
    Ask the LLM to find internal linking opportunities between pages that
    already exist on this website. our_pages is a list of dicts with keys:
    url, title, h1, word_count, internal_links_count.
    Returns a list of suggestion dicts, or an empty list if parsing fails.
    """
    if len(our_pages) < 2:
        # need at least 2 pages to link between
        return []

    pages_text = ""
    for p in our_pages:
        pages_text += (
            f"\n- URL: {p.get('url')}\n"
            f"  Title: {p.get('title') or '(missing)'}\n"
            f"  H1: {p.get('h1') or '(missing)'}\n"
            f"  Word count: {p.get('word_count', 0)}\n"
            f"  Current internal links on this page: {p.get('internal_links_count', 0)}\n"
        )

    prompt = f"""
You are an SEO Internal Linking Agent.

Business description: {business_description or "Not provided"}
Target country: {country or "Not specified"}
Target language: {language or "English"}

Here are the ONLY pages that exist on this website (already crawled):
{pages_text}

Suggest internal linking opportunities BETWEEN these existing pages only.
Do NOT invent, guess, or suggest links to any URL not listed above.
Prioritize pages with low internal_links_count as link targets, and pages
that are topically related to each other.

For each suggestion, give:
- source_page_url: which existing page should ADD the link (must be from the list above)
- target_page_url: which existing page it should link TO (must be from the list above, and different from source)
- anchor_text: suggested clickable text for the link
- reason: why this link makes sense (topical relevance, orphaned page, etc.)

Suggest at most 15 links total, only where there is a genuine topical connection.

Respond ONLY with a valid JSON array, no other text, no markdown code fences.
Format:
[
  {{"source_page_url": "...", "target_page_url": "...", "anchor_text": "...", "reason": "..."}}
]
If no genuine opportunities exist, respond with an empty JSON array: []
"""

    raw_response = ask_llm(prompt)
    cleaned = re.sub(r"^```json|```$", "", raw_response.strip(), flags=re.MULTILINE).strip()

    try:
        suggestions = json.loads(cleaned)
        if not isinstance(suggestions, list):
            raise ValueError("Response was not a JSON list.")

        # defensive filter: only keep suggestions where both URLs are
        # actually from our crawled pages list, since the LLM could still
        # hallucinate a URL despite instructions
        valid_urls = {p.get("url") for p in our_pages}
        valid_suggestions = [
            s for s in suggestions
            if s.get("source_page_url") in valid_urls
            and s.get("target_page_url") in valid_urls
            and s.get("source_page_url") != s.get("target_page_url")
        ]
        return valid_suggestions
    except (json.JSONDecodeError, ValueError):
        return []