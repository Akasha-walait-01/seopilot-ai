# This file is the Orchestrator Agent's "brain" functions.
# It does NOT talk to the database directly - it only calls the LLM to:
# 1. Decide which tools/agents to run for a given user goal (planning)
# 2. Combine all the step results into one final strategy (synthesis)
# The actual tool execution happens in main.py, since that needs database access.
# Phase 7: internal_linking_analysis, schema_generation, aeo_geo_generation added.

import json
import re
from backend.providers.llm_provider import ask_llm

# these are the only tool names the orchestrator is allowed to plan with
# main.py has a matching executor branch for each one of these
AVAILABLE_TOOLS = [
    "technical_audit",
    "keyword_research",
    "competitor_analysis",
    "content_gap_analysis",
    "content_brief_generation",
    "content_optimizer",
    "internal_linking_analysis",
    "schema_generation",
    "aeo_geo_generation",
]


def build_plan(goal: str, context: dict) -> list[dict]:
    """
    Ask the LLM to turn a free-text goal into an ordered list of tool calls.
    context should include: business_description, country, language,
    existing_pages_count, existing_keywords_count, existing_competitors_count,
    existing_content_gaps_count, existing_page_urls (list), and
    existing_content_gap_opportunities (list).
    Returns a list of step dicts, or an empty list if the LLM output could not be parsed.
    """
    existing_pages_text = ", ".join(context.get("existing_page_urls", [])) or "None yet"
    existing_gaps_text = ", ".join(context.get("existing_content_gap_opportunities", [])) or "None yet"

    prompt = f"""
You are the Orchestrator Agent of an autonomous SEO platform. You do not do the
work yourself - you plan an ordered sequence of tool calls for other agents to run.

User's goal (free text, may be in Roman Urdu or English): {goal}

Business description: {context.get("business_description") or "Not provided"}
Target country: {context.get("country") or "Not specified"}
Target language: {context.get("language") or "English"}

Current project state:
- Pages already crawled: {context.get("existing_pages_count", 0)}
- Keywords already researched: {context.get("existing_keywords_count", 0)}
- Competitors already added: {context.get("existing_competitors_count", 0)}
- Content gaps already found: {context.get("existing_content_gaps_count", 0)}
- Existing crawled page URLs (only these can be optimized, schema'd, linked, or AEO/GEO'd): {existing_pages_text}
- Existing content gap opportunities (can be used as brief topics): {existing_gaps_text}

Available tools, EXACT names you must use, and their required tool_input fields:
1. "technical_audit" -> tool_input: {{"max_pages": <integer, default 10>}}
   Crawls the website and runs a technical SEO audit. No other input needed.
2. "keyword_research" -> tool_input: {{"seed_keyword": "<string>"}}
   Generates AI-suggested keyword ideas around one seed keyword.
3. "competitor_analysis" -> tool_input: {{"competitor_url": "<string>"}}
   ONLY include this step if the user's goal text contains an actual competitor
   website URL. NEVER invent or guess a competitor URL. You may include multiple
   competitor_analysis steps if multiple URLs are mentioned.
4. "content_gap_analysis" -> tool_input: {{}}
   Requires at least one crawled page AND at least one competitor to already
   exist (either already in the project, or planned earlier in this same plan).
   Do not include this step if neither condition can be met.
5. "content_brief_generation" -> tool_input: {{"topic": "<string>"}}
   Pick a topic from the goal, or from an existing content gap opportunity.
6. "content_optimizer" -> tool_input: {{"page_url": "<string, must be one of the existing crawled page URLs listed above>"}}
   Only include this if there is at least one existing crawled page URL listed above.
7. "internal_linking_analysis" -> tool_input: {{}}
   Suggests internal links between existing crawled pages. Requires at least
   2 existing crawled page URLs listed above. Do not include otherwise.
8. "schema_generation" -> tool_input: {{"page_url": "<string, must be one of the existing crawled page URLs listed above>"}}
   Generates JSON-LD schema suggestions for one existing page. Only include
   if there is at least one existing crawled page URL listed above. You may
   include multiple schema_generation steps for different pages if the goal
   asks for schema across several pages.
9. "aeo_geo_generation" -> tool_input: {{"page_url": "<string, must be one of the existing crawled page URLs listed above>"}}
   Generates FAQ/answer-block/structure suggestions for one existing page to
   help AI search engines cite it. Only include if there is at least one
   existing crawled page URL listed above.

Rules:
- Only use tool_name values from the list above, exactly as spelled.
- Choose the SMALLEST set of steps that actually accomplishes the user's goal.
  Do not add a step just because a tool exists - only add it if it is needed.
- Order steps logically (e.g. technical_audit before content_optimizer,
  schema_generation, aeo_geo_generation, or internal_linking_analysis, since
  those all need crawled pages to exist first).
- Give a short "purpose" for each step explaining why it is needed for this goal.

Respond ONLY with a valid JSON array, no other text, no markdown code fences.
Format:
[
  {{"step_number": 1, "tool_name": "...", "tool_input": {{...}}, "purpose": "..."}}
]
If no steps are needed or the goal is unclear, respond with an empty JSON array: []
"""

    raw_response = ask_llm(prompt)
    cleaned = re.sub(r"^```json|```$", "", raw_response.strip(), flags=re.MULTILINE).strip()

    try:
        plan = json.loads(cleaned)
        if not isinstance(plan, list):
            raise ValueError("Response was not a JSON list.")
        # keep only steps that use a real tool name, ignore anything else
        # rather than crashing on an unexpected LLM response
        valid_plan = [step for step in plan if step.get("tool_name") in AVAILABLE_TOOLS]
        return valid_plan
    except (json.JSONDecodeError, ValueError):
        return []


def synthesize_final_strategy(goal: str, step_results: list[dict]) -> dict:
    """
    Ask the LLM to combine all completed step outputs into one final strategy
    the user can review, edit, and approve. step_results is a list of dicts:
    [{"tool_name": "...", "purpose": "...", "output_summary": "..."}]
    Returns a structured dict, or an empty dict if parsing fails.
    """
    results_text = ""
    for result in step_results:
        results_text += (
            f"\n- Tool: {result.get('tool_name')}\n"
            f"  Purpose: {result.get('purpose')}\n"
            f"  Result: {result.get('output_summary')}\n"
        )
    if not results_text:
        results_text = "No steps produced usable output."

    prompt = f"""
You are the Orchestrator Agent of an autonomous SEO platform. Multiple specialist
agents have already run. Combine their results into one clear final strategy
for a human to review before anything gets published or acted on.

User's original goal: {goal}

Completed step results:
{results_text}

Do NOT invent any data, statistics, or rankings that were not in the results above.
If a step failed or was skipped, mention that plainly instead of guessing what it
would have found.

Respond ONLY with a valid JSON object, no other text, no markdown code fences.
Format:
{{
  "summary": "2-3 sentence overview of the overall strategy",
  "key_findings": ["...", "..."],
  "recommended_actions": ["...", "..."],
  "risks_or_gaps": ["...", "..."],
  "next_steps_needing_human_input": ["...", "..."]
}}
"""

    raw_response = ask_llm(prompt)
    cleaned = re.sub(r"^```json|```$", "", raw_response.strip(), flags=re.MULTILINE).strip()

    try:
        strategy = json.loads(cleaned)
        if not isinstance(strategy, dict):
            raise ValueError("Response was not a JSON object.")
        return strategy
    except (json.JSONDecodeError, ValueError):
        return {}