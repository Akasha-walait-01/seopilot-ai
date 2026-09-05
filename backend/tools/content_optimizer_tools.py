# This file is our Existing Content Optimizer
# Spec section 14: analyze an existing page and return
# CURRENT STATE -> PROBLEMS -> RECOMMENDATIONS -> OPTIMIZED VERSION
# Prefers targeted improvements over full rewrites.
#
# UPDATE: added E-E-A-T (Experience, Expertise, Authoritativeness,
# Trustworthiness) review and keyword intent alignment check, based only
# on what is actually present in the page/article text - never inventing
# credentials, experience, or trust signals that were not shown.

import json
import re
from backend.providers.llm_provider import ask_llm


def optimize_content(
    page_url: str,
    current_title: str,
    current_meta_description: str,
    current_h1: str,
    word_count: int,
    article_text: str,
    business_description: str,
    author_detected: bool = False,
    target_keywords: list[str] | None = None,
) -> dict:
    """
    Ask the LLM to analyze an existing page and suggest targeted improvements,
    including an E-E-A-T review and keyword intent alignment check.
    Returns a structured dict, or an empty dict if parsing fails.
    """
    text_snippet = article_text.strip() if article_text else "(No article text provided, analyze based on metadata only.)"
    keywords_text = ", ".join(target_keywords) if target_keywords else "None provided"

    prompt = f"""
You are an SEO content optimizer. Analyze this existing page and suggest
TARGETED improvements, not a full rewrite unless truly necessary.

Business description: {business_description or "Not provided"}

Page URL: {page_url}
Current title: {current_title or "(missing)"}
Current meta description: {current_meta_description or "(missing)"}
Current H1: {current_h1 or "(missing)"}
Current word count: {word_count}
Author/byline detected on page: {author_detected}
Target keywords for this page: {keywords_text}

Article content (may be partial):
{text_snippet}

Analyze:
- Search intent alignment: does the content actually match what someone
  searching the target keywords above would expect to find (informational
  vs commercial vs transactional)? Only comment on keywords actually given.
- Topic coverage and structure/readability
- Missing information
- AEO readiness (clear direct answers, extractable facts)
- E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness):
  based ONLY on what is visible in the content/metadata above, note what
  E-E-A-T signals are present (e.g. first-hand examples, credentials
  mentioned, citations/sources linked, author byline) and what is missing.
  Do NOT invent or assume any author credentials, experience, or trust
  signals that are not actually shown in the text - if nothing indicates
  a signal, say it is missing, don't guess.

Do not fabricate statistics or claims. Prefer small, targeted fixes.

Respond ONLY with a valid JSON object, no other text, no markdown code fences.
Format:
{{
  "current_state_summary": "...",
  "problems": ["...", "..."],
  "why_it_matters": ["...", "..."],
  "recommendations": ["...", "..."],
  "optimized_title": "...",
  "optimized_meta_description": "...",
  "optimized_h1": "...",
  "keyword_intent_alignment": "one or two sentences on whether the content matches search intent for the given keywords, or 'No target keywords provided' if none were given",
  "eeat_signals_present": ["...", "..."],
  "eeat_signals_missing": ["...", "..."],
  "notes": "..."
}}
"""

    raw_response = ask_llm(prompt)
    cleaned = re.sub(r"^```json|```$", "", raw_response.strip(), flags=re.MULTILINE).strip()

    try:
        result = json.loads(cleaned)
        if not isinstance(result, dict):
            raise ValueError("Response was not a JSON object.")
        return result
    except (json.JSONDecodeError, ValueError):
        return {}