# This file is our Content Brief Generator
# Spec section 12: for every recommended article/page, generate a
# data-driven brief (keywords, structure, questions, entities, etc)
# The LLM does NOT fabricate statistics, studies, or citations here.

import json
import re
from backend.providers.llm_provider import ask_llm


def generate_content_brief(
    topic: str,
    business_description: str,
    country: str,
    language: str,
    related_keywords: list[str],
) -> dict:
    """
    Ask the LLM to generate a full content brief for a given topic.
    Returns a structured dict, or an empty dict if parsing fails.
    """
    keywords_text = ", ".join(related_keywords) if related_keywords else "None provided"

    prompt = f"""
You are an SEO content strategist creating a content brief for a writer.

Business description: {business_description or "Not provided"}
Target country: {country or "Not specified"}
Target language: {language or "English"}
Topic: {topic}
Related keywords available: {keywords_text}

Create a complete, data-driven content brief for this topic.
Do NOT invent statistics, studies, case studies, or citations.
Mark anything that needs human verification clearly in "content_requirements".

Respond ONLY with a valid JSON object, no other text, no markdown code fences.
Format:
{{
  "primary_keyword": "...",
  "secondary_keywords": ["...", "..."],
  "search_intent": "informational" or "commercial" or "transactional" or "navigational",
  "target_audience": "...",
  "suggested_title": "...",
  "h1": "...",
  "h2s": ["...", "..."],
  "h3s": ["...", "..."],
  "questions_to_answer": ["...", "..."],
  "important_entities": ["...", "..."],
  "topics_to_cover": ["...", "..."],
  "internal_linking_opportunities": ["...", "..."],
  "external_reference_opportunities": ["...", "..."],
  "suggested_cta": "...",
  "faq_opportunities": ["...", "..."],
  "content_requirements": "notes on what needs human verification or research"
}}
"""

    raw_response = ask_llm(prompt)
    cleaned = re.sub(r"^```json|```$", "", raw_response.strip(), flags=re.MULTILINE).strip()

    try:
        brief = json.loads(cleaned)
        if not isinstance(brief, dict):
            raise ValueError("Response was not a JSON object.")
        return brief
    except (json.JSONDecodeError, ValueError):
        return {}