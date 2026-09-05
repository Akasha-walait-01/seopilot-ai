# This file is our Keyword Research tool
# Uses the LLM to expand a seed keyword into related keywords and
# classify search intent. This is NOT real search volume/ranking data,
# it is AI-suggested keyword ideas based on the business context.
# This is clearly labeled everywhere it is shown to the user.
#
# UPDATE: added keyword_type parameter - "short_tail" (1-2 words, broad,
# high competition), "long_tail" (4+ words, specific, lower competition),
# or "both" (default mix). This only changes the LLM's generation
# instructions - it does not fabricate any search volume/competition
# numbers either way.

import json
import re
from backend.providers.llm_provider import ask_llm


def research_keywords(
    seed_keyword: str, business_description: str, country: str, language: str,
    keyword_type: str = "both",
) -> list[dict]:
    """
    Ask the LLM to generate related keyword ideas with intent classification.
    Returns a list of dicts. Data is AI-suggested, not from a real search API.
    keyword_type controls the STYLE of keywords requested: "short_tail",
    "long_tail", or "both".
    """
    if keyword_type == "short_tail":
        length_instruction = (
            "Generate ONLY short-tail keywords: 1-2 words, broad and high search volume in "
            "concept, typically high competition (e.g. 'medical billing', 'billing software')."
        )
    elif keyword_type == "long_tail":
        length_instruction = (
            "Generate ONLY long-tail keywords: 4 or more words, highly specific phrases that "
            "reflect a precise search intent, typically lower competition "
            "(e.g. 'best medical billing software for small clinics in Pakistan')."
        )
    else:
        length_instruction = (
            "Generate a MIX of both short-tail keywords (1-2 words, broad) and long-tail "
            "keywords (4+ words, specific) - roughly half and half."
        )

    prompt = f"""
You are an SEO keyword research assistant.

Business description: {business_description or "Not provided"}
Target country: {country or "Not specified"}
Target language: {language or "English"}
Seed keyword: {seed_keyword}

Generate 12 relevant keyword ideas related to the seed keyword above.
{length_instruction}

For each keyword, classify the search intent as one of:
"informational", "navigational", "commercial", or "transactional".

Also assign a topic cluster name that groups similar keywords together.

Respond ONLY with a valid JSON array, no other text, no markdown code fences.
Format:
[
  {{"keyword": "...", "intent": "...", "cluster": "...", "reason": "..."}}
]
"""

    raw_response = ask_llm(prompt)

    # defensive parsing: strip markdown fences if the model added them anyway
    cleaned = re.sub(r"^```json|```$", "", raw_response.strip(), flags=re.MULTILINE).strip()

    try:
        keywords = json.loads(cleaned)
        if not isinstance(keywords, list):
            raise ValueError("Response was not a JSON list.")
        return keywords
    except (json.JSONDecodeError, ValueError):
        # if the LLM output could not be parsed, return an empty list
        # rather than fabricating or guessing data
        return []