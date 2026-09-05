# This file is our Content Gap Agent
# Compares our website's pages against competitor pages and our
# researched keywords, then asks the LLM to identify missing topics,
# weakly covered topics, and new content opportunities.
# The LLM does NOT invent search volume or ranking claims here,
# it only reasons about topic coverage.

import json
import re
from backend.providers.llm_provider import ask_llm


def _summarize_pages(pages: list[dict], limit: int = 15) -> str:
    # build a compact text summary of pages for the LLM prompt
    # (keeps token usage reasonable, avoids sending full page content)
    lines = []
    for page in pages[:limit]:
        title = page.get("title") or "(no title)"
        h1 = page.get("h1") or page.get("h1_text") or "(no H1)"
        lines.append(f"- URL: {page.get('url')} | Title: {title} | H1: {h1}")
    return "\n".join(lines) if lines else "No pages available."


def _summarize_keywords(keywords: list[dict], limit: int = 20) -> str:
    lines = []
    for kw in keywords[:limit]:
        lines.append(f"- {kw.get('keyword')} (intent: {kw.get('intent')}, cluster: {kw.get('cluster')})")
    return "\n".join(lines) if lines else "No researched keywords available."


def find_content_gaps(
    business_description: str,
    our_pages: list[dict],
    competitor_pages_by_url: dict[str, list[dict]],
    researched_keywords: list[dict],
) -> list[dict]:
    """
    Ask the LLM to compare our site vs competitors vs researched keywords,
    and identify content gap opportunities.
    Returns a list of structured opportunity dicts.
    """
    our_pages_summary = _summarize_pages(our_pages)
    keywords_summary = _summarize_keywords(researched_keywords)

    competitor_summary_blocks = []
    for competitor_url, pages in competitor_pages_by_url.items():
        competitor_summary_blocks.append(
            f"Competitor: {competitor_url}\n{_summarize_pages(pages)}"
        )
    competitors_summary = "\n\n".join(competitor_summary_blocks) if competitor_summary_blocks else "No competitor data available."

    prompt = f"""
You are an SEO content strategist doing a content gap analysis.

Business description: {business_description or "Not provided"}

OUR WEBSITE PAGES:
{our_pages_summary}

COMPETITOR PAGES:
{competitors_summary}

OUR RESEARCHED KEYWORDS:
{keywords_summary}

Compare our website against the competitors and our researched keywords.
Identify content gap opportunities. A content gap is a topic that is:
- covered by competitors but missing on our site, OR
- relevant to our researched keywords but not covered on our site, OR
- covered on our site but very weakly (thin content) compared to competitors

For each opportunity, consider business relevance, not just keyword overlap.
Do not invent statistics or search volume. Do not guarantee ranking improvements.

Respond ONLY with a valid JSON array, no other text, no markdown code fences.
Format:
[
  {{
    "opportunity": "short topic name",
    "gap_type": "new_content" or "content_expansion",
    "priority": "high" or "medium" or "low",
    "reason": "why this matters, based on the data above",
    "suggested_page": "/suggested-url-slug"
  }}
]

Generate at most 8 opportunities, focus on quality over quantity.
"""

    raw_response = ask_llm(prompt)

    cleaned = re.sub(r"^```json|```$", "", raw_response.strip(), flags=re.MULTILINE).strip()

    try:
        gaps = json.loads(cleaned)
        if not isinstance(gaps, list):
            raise ValueError("Response was not a JSON list.")
        return gaps
    except (json.JSONDecodeError, ValueError):
        return []