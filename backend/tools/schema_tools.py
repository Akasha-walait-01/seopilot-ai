# This file is our Schema / JSON-LD Agent.
# It only picks schema types from a curated list below (not free-form),
# to keep generated markup reliable and valid.

import json
import re
from backend.providers.llm_provider import ask_llm

# curated list of schema.org types this agent is allowed to generate
CURATED_SCHEMA_TYPES = [
    "Organization",
    "WebSite",
    "Article",
    "BlogPosting",
    "FAQPage",
    "BreadcrumbList",
    "Product",
    "LocalBusiness",
    "HowTo",
]


def generate_schema_for_page(
    page_url: str,
    title: str,
    meta_description: str,
    h1_text: str,
    word_count: int,
    has_schema: bool,
    business_description: str,
) -> dict:
    """
    Ask the LLM to recommend and generate JSON-LD schema markup for one page,
    choosing only from CURATED_SCHEMA_TYPES. Returns a dict with the
    recommended schema blocks, or an empty dict if parsing fails.
    """
    types_text = ", ".join(CURATED_SCHEMA_TYPES)

    prompt = f"""
You are an SEO Schema/JSON-LD Agent.

Business description: {business_description or "Not provided"}

Page details:
URL: {page_url}
Title: {title or "(missing)"}
Meta description: {meta_description or "(missing)"}
H1: {h1_text or "(missing)"}
Word count: {word_count}
Already has some schema markup: {has_schema}

You may ONLY choose schema types from this exact list: {types_text}

Based on the page details above, decide which 1 to 3 schema types genuinely
apply to this page (e.g. a blog article page suits Article or BlogPosting +
BreadcrumbList; a homepage suits Organization + WebSite; a product page
suits Product). Do NOT pick a type that doesn't fit the page's actual content.

Generate valid, minimal, accurate JSON-LD for each chosen type. Use only
information given above - do NOT invent facts, prices, ratings, reviews,
addresses, or phone numbers that were not provided. Leave a field out of
the JSON-LD entirely rather than making up a value for it.

Respond ONLY with a valid JSON object, no other text, no markdown code fences.
Format:
{{
  "schema_blocks": [
    {{"schema_type": "...", "json_ld": {{...}}, "notes": "why this type fits this page, or what data is still missing"}}
  ]
}}
If no schema type genuinely fits this page, respond with: {{"schema_blocks": []}}
"""

    raw_response = ask_llm(prompt)
    cleaned = re.sub(r"^```json|```$", "", raw_response.strip(), flags=re.MULTILINE).strip()

    try:
        result = json.loads(cleaned)
        if not isinstance(result, dict) or "schema_blocks" not in result:
            raise ValueError("Response was not in the expected format.")

        # defensive filter: only keep blocks using a type from our curated list
        valid_blocks = [
            b for b in result["schema_blocks"]
            if b.get("schema_type") in CURATED_SCHEMA_TYPES and isinstance(b.get("json_ld"), dict)
        ]
        return {"schema_blocks": valid_blocks}
    except (json.JSONDecodeError, ValueError):
        return {}