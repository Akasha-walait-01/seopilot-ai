# This file builds the final "everything so far" project report.
# IMPORTANT: this is pure formatting, NOT an LLM call. Every line in the
# report comes directly from data already saved in the database - nothing
# here is generated or guessed, so the report can never contain fabricated
# numbers, findings, or claims.

from datetime import datetime


def _section(title: str) -> str:
    return f"\n## {title}\n"


def build_full_report(context: dict) -> str:
    """
    context is a dict with all the raw data collected from the database:
    website, pages, issues, keywords, competitors, content_gaps,
    content_briefs, internal_links, schema_markups, aeo_geo_suggestions,
    pagespeed_results, publish_jobs, monitoring_snapshots, monitoring_alerts.
    Returns a Markdown-formatted report string.
    """
    website = context["website"]
    pages = context.get("pages", [])
    issues = context.get("issues", [])
    keywords = context.get("keywords", [])
    competitors = context.get("competitors", [])
    content_gaps = context.get("content_gaps", [])
    content_briefs = context.get("content_briefs", [])
    internal_links = context.get("internal_links", [])
    schema_markups = context.get("schema_markups", [])
    aeo_geo_suggestions = context.get("aeo_geo_suggestions", [])
    pagespeed_results = context.get("pagespeed_results", [])
    publish_jobs = context.get("publish_jobs", [])
    monitoring_snapshots = context.get("monitoring_snapshots", [])
    monitoring_alerts = context.get("monitoring_alerts", [])

    lines = []
    lines.append(f"# SEO Report — {website['url']}")
    lines.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    if website.get("business_description"):
        lines.append(f"\n**Business:** {website['business_description']}")
    if website.get("goal"):
        lines.append(f"**Goal:** {website['goal']}")

    # ---------- Overview ----------
    lines.append(_section("Overview"))
    lines.append(f"- Pages crawled: **{len(pages)}**")
    critical_count = sum(1 for i in issues if i.get("severity") == "critical")
    lines.append(f"- Total SEO issues found: **{len(issues)}** ({critical_count} critical)")
    lines.append(f"- Keywords researched: **{len(keywords)}**")
    lines.append(f"- Competitors analyzed: **{len(competitors)}**")
    lines.append(f"- Content gap opportunities: **{len(content_gaps)}**")
    lines.append(f"- Content briefs generated: **{len(content_briefs)}**")
    lines.append(f"- Internal linking suggestions: **{len(internal_links)}**")
    lines.append(f"- Schema markup blocks: **{len(schema_markups)}**")
    lines.append(f"- AEO/GEO suggestions: **{len(aeo_geo_suggestions)}**")
    lines.append(f"- PageSpeed checks run: **{len(pagespeed_results)}**")
    lines.append(f"- WordPress publish actions: **{len(publish_jobs)}**")
    lines.append(f"- Monitoring snapshots recorded: **{len(monitoring_snapshots)}**")
    lines.append(f"- Active monitoring alerts: **{len(monitoring_alerts)}**")

    # ---------- Technical SEO Audit ----------
    lines.append(_section("Technical SEO Audit"))
    if pages:
        severity_counts = {}
        for i in issues:
            severity_counts[i["severity"]] = severity_counts.get(i["severity"], 0) + 1
        for sev in ["critical", "high", "medium", "low"]:
            if sev in severity_counts:
                lines.append(f"- {sev.capitalize()}: {severity_counts[sev]}")

        lines.append("\n**Top Critical/High Issues:**")
        top_issues = [i for i in issues if i["severity"] in ("critical", "high")][:15]
        if top_issues:
            for i in top_issues:
                page_ref = i.get("page_url") or "(site-wide)"
                lines.append(f"- [{i['severity'].upper()}] {i['issue_type']} — {page_ref}: {i['message']}")
        else:
            lines.append("- None found.")
    else:
        lines.append("No technical audit has been run yet.")

    # ---------- Keywords ----------
    lines.append(_section("Keyword Research"))
    if keywords:
        for k in keywords[:30]:
            lines.append(f"- **{k['keyword']}** — intent: {k.get('intent', '-')}, cluster: {k.get('cluster', '-')}")
        if len(keywords) > 30:
            lines.append(f"- ... and {len(keywords) - 30} more.")
    else:
        lines.append("No keywords researched yet.")

    # ---------- Competitors ----------
    lines.append(_section("Competitor Analysis"))
    if competitors:
        for c in competitors:
            lines.append(f"- {c['competitor_url']} — {c['pages_analyzed']} pages analyzed")
    else:
        lines.append("No competitors added yet.")

    # ---------- Content Gaps ----------
    lines.append(_section("Content Gap Opportunities"))
    if content_gaps:
        for g in content_gaps[:20]:
            lines.append(f"- [{g.get('priority', '-').upper()}] {g['opportunity']} — {g.get('reason', '-')}")
    else:
        lines.append("No content gaps identified yet.")

    # ---------- Content Briefs ----------
    lines.append(_section("Content Briefs"))
    if content_briefs:
        for b in content_briefs:
            lines.append(f"- {b['topic']} — suggested title: \"{b.get('suggested_title', '-')}\"")
    else:
        lines.append("No content briefs generated yet.")

    # ---------- Internal Linking ----------
    lines.append(_section("Internal Linking Suggestions"))
    if internal_links:
        for l in internal_links[:20]:
            lines.append(f"- {l['source_page_url']} → {l['target_page_url']} (anchor: \"{l.get('anchor_text', '-')}\")")
    else:
        lines.append("No internal linking suggestions yet.")

    # ---------- Schema ----------
    lines.append(_section("Schema / JSON-LD"))
    if schema_markups:
        for s in schema_markups:
            lines.append(f"- {s['schema_type']} — {s['page_url']}")
    else:
        lines.append("No schema markup generated yet.")

    # ---------- AEO/GEO ----------
    lines.append(_section("AEO/GEO (AI Search Optimization)"))
    if aeo_geo_suggestions:
        for a in aeo_geo_suggestions:
            lines.append(f"- {a['page_url']}")
    else:
        lines.append("No AEO/GEO suggestions generated yet.")

    # ---------- PageSpeed ----------
    lines.append(_section("Page Speed (Google PageSpeed Insights)"))
    if pagespeed_results:
        for p in pagespeed_results[:10]:
            lines.append(
                f"- {p['page_url']} ({p['strategy']}) — Performance: {p.get('performance_score', '-')}/100, "
                f"SEO: {p.get('seo_score', '-')}/100"
            )
    else:
        lines.append("No PageSpeed checks run yet.")

    # ---------- WordPress Publishing ----------
    lines.append(_section("WordPress Publish History"))
    if publish_jobs:
        for j in publish_jobs[:20]:
            lines.append(f"- [{j['status'].upper()}] {j['job_type'].replace('_', ' ')} — {j.get('result_message', '-')}")
    else:
        lines.append("No publish actions taken yet.")

    # ---------- Monitoring ----------
    lines.append(_section("Monitoring History"))
    if monitoring_snapshots:
        lines.append("**Score history (most recent first):**")
        for s in monitoring_snapshots[:10]:
            lines.append(f"- {s['created_at'][:16].replace('T', ' ')} — Score: {s['score']}/100, Issues: {s['total_issues']}")
    else:
        lines.append("No monitoring checks run yet.")

    if monitoring_alerts:
        lines.append("\n**Active Alerts:**")
        for a in monitoring_alerts:
            lines.append(f"- [{a['alert_type'].replace('_', ' ').upper()}] {a['message']}")
    else:
        lines.append("\nNo active monitoring alerts.")

    lines.append("\n---")
    lines.append(
        "*This report reflects only real, measured data captured by the platform. "
        "SERP rankings, backlinks, and user engagement metrics are shown elsewhere in the app "
        "in mock/demo or not-configured mode and are intentionally excluded from this report "
        "to avoid presenting non-real data as fact.*"
    )

    return "\n".join(lines)