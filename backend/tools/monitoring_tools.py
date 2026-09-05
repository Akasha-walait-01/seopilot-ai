# This file is our Autonomous Monitoring Agent.
# It compares a new technical audit snapshot against the previous one to
# detect "drops" - since there is no real ranking API, this only uses two
# honest, measurable signals: SEO score drop and newly appeared critical
# issues. It never claims a keyword ranking drop from mock SERP data.

import re
import json
from backend.providers.llm_provider import ask_llm

SCORE_DROP_THRESHOLD = 5  # points; a smaller change is treated as normal noise


def detect_alerts(previous_snapshot: dict | None, new_snapshot: dict, previous_issues: list[dict], new_issues: list[dict]) -> list[dict]:
    """
    Compares the new audit snapshot to the previous one (if any) and returns
    a list of alert dicts: {"alert_type": ..., "message": ..., "page_url": ...}
    Only based on real, measured data - no invented ranking claims.
    """
    alerts = []

    if previous_snapshot is not None:
        score_drop = previous_snapshot["score"] - new_snapshot["score"]
        if score_drop >= SCORE_DROP_THRESHOLD:
            alerts.append({
                "alert_type": "score_drop",
                "message": f"SEO score dropped from {previous_snapshot['score']} to {new_snapshot['score']} ({score_drop:.1f} point decrease).",
                "page_url": None,
            })

    # find issues that exist now but did not exist in the previous run,
    # identified by (page_url, issue_type) pair
    previous_keys = {(i.get("page_url"), i.get("issue_type")) for i in previous_issues}
    new_critical = [
        i for i in new_issues
        if i.get("severity") == "critical" and (i.get("page_url"), i.get("issue_type")) not in previous_keys
    ]

    for issue in new_critical:
        alerts.append({
            "alert_type": "new_critical_issue",
            "message": f"New critical issue on {issue.get('page_url')}: {issue.get('message')}",
            "page_url": issue.get("page_url"),
        })

    return alerts


def summarize_monitoring_run(
    previous_snapshot: dict | None,
    new_snapshot: dict,
    alerts: list[dict],
    serp_results: list[dict],
) -> str:
    """
    Asks the LLM for a short, plain-language summary of this monitoring run.
    Only describes what was actually measured - does not speculate about
    causes it cannot know (like why a competitor might be outranking).
    """
    if previous_snapshot is None:
        comparison_text = "This is the first monitoring snapshot for this project, so there is nothing to compare against yet."
    else:
        comparison_text = f"Previous score: {previous_snapshot['score']}/100. New score: {new_snapshot['score']}/100."

    alerts_text = "\n".join(f"- {a['alert_type']}: {a['message']}" for a in alerts) or "No alerts."

    serp_text = "SERP/ranking data is not connected (mock/demo mode) - not used for any conclusions." if not serp_results else (
        "SERP check results (mock/demo data, not real rankings): " + json.dumps(serp_results)[:500]
    )

    prompt = f"""
You are an SEO Monitoring Agent. Summarize this monitoring run in 2-4 plain
sentences for a human to read. Only describe what is given below - do NOT
guess at causes, competitor behavior, or ranking changes that were not
actually measured.

{comparison_text}
New audit: {new_snapshot['pages_crawled']} pages crawled, {new_snapshot['total_issues']} total issues.

Alerts detected:
{alerts_text}

{serp_text}

Respond with plain text only, no JSON, no markdown formatting.
"""

    return ask_llm(prompt).strip()