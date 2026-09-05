# This file is our AEO/GEO Agent (Answer Engine Optimization / Generative
# Engine Optimization). Goal: make a page's content easier for AI search
# engines (ChatGPT, Perplexity, Google AI Overviews, etc.) to understand,
# quote, and cite correctly.
# Scope for this phase: FAQ items, a concise answer block, and structure
# suggestions. Does NOT generate llms.txt (kept out of scope for now).

import json
import re
from backend.providers.llm_provider import ask_llm


def generate_aeo_geo_suggestions(
    page_url: str,
    title: str,
    meta_description: str,
    h1_text: str,
    word_count: int,
    business_description: str,
    article_text: str = "",
) -> dict:
    """
    Ask the LLM to generate AEO/GEO suggestions for one page: FAQ items,
    a concise answer block, and structure tips. Returns a dict, or an
    empty dict if parsing fails.
    """
    content_note = (
        f"Article text provided below for deeper analysis:\n{article_text[:3000]}"
        if article_text else
        "No article text provided - base suggestions on the title, meta description, and H1 only."
    )

    prompt = f"""
You are an SEO AEO/GEO Agent (Answer Engine Optimization / Generative Engine
Optimization). Your job is to help this page get quoted and cited correctly
by AI search engines and AI chat assistants.

Business description: {business_description or "Not provided"}

Page details:
URL: {page_url}
Title: {title or "(missing)"}
Meta description: {meta_description or "(missing)"}
H1: {h1_text or "(missing)"}
Word count: {word_count}

{content_note}

Do NOT invent facts, statistics, or claims not supported by the page details
or article text above. If you cannot generate a good FAQ or answer from what
is given, produce fewer items rather than making things up.

Generate:
1. 3-6 FAQ items (question + concise answer, each answer under 40 words,
   phrased the way a person would ask an AI assistant)
2. One concise_answer_block: a 2-3 sentence direct answer to "what is this
   page about", written to be easily quotable/citable by an AI engine
3. 3-5 structure_suggestions: concrete tips to make the page more
   citation-friendly (e.g. "add a definition near the top", "use a numbered
   list for the steps", "add a summary sentence under each H2")

Respond ONLY with a valid JSON object, no other text, no markdown code fences.
Format:
{{
  "faq_items": [{{"question": "...", "answer": "..."}}],
  "concise_answer_block": "...",
  "structure_suggestions": ["...", "..."]
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