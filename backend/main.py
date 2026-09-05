# This is the FastAPI entry point
# Phase 1: website projects + LLM test
# Phase 2: crawl + technical SEO audit + scoring routes
# Phase 3: keyword research agent + SERP provider check routes
# Phase 4: competitor analysis + content gap agent routes
# Phase 5: content brief generator + content optimizer routes added
# Phase 6: Orchestrator Agent + Human Approval routes added
# Phase 7: Internal Linking, Schema/JSON-LD, AEO/GEO agent routes added
# Phase 8: WordPress/CMS connection + publish routes added
# Phase 9: Autonomous Monitoring + Content Refresh Loop routes added
# Post-9: crawlability, mobile, freshness, E-E-A-T, PageSpeed, Backlinks,
#   User Signals, max_pages restored, keyword_type dropdown, full report
#   generation (Monitoring & Refresh page) all added.
# CRITICAL FIX: Windows needs WindowsProactorEventLoopPolicy set BEFORE
# uvicorn creates its event loop, or Playwright's Chromium subprocess
# launch fails with NotImplementedError. This must be the very first
# thing in this file, before any other import.

import sys
import asyncio

def crawl_website(website_id: int, max_pages: int = 10):  # existing function signature
    # Windows fix: Playwright needs its own Proactor event loop in THIS thread
    if sys.platform == "win32":
        try:
            asyncio.set_event_loop(asyncio.ProactorEventLoop())
        except Exception:
            pass
    
    # ... existing code (sync_playwright() waghera) yahan se shuru hota hai
import json
from datetime import datetime
from urllib.parse import urlparse
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import Base, engine, get_db
from backend import models, schemas
from backend.providers.llm_provider import ask_llm
from backend.providers.serp_provider import get_serp_provider
from backend.providers.wordpress_provider import WordPressProvider
from backend.providers.pagespeed_provider import check_pagespeed
from backend.providers.authority_signals_provider import check_backlinks, check_user_signals
from backend.tools.crawler import crawl_website, check_site_crawlability
from backend.tools.keyword_tools import research_keywords
from backend.tools.competitor_tools import analyze_competitor
from backend.tools.content_gap_tools import find_content_gaps
from backend.tools.content_brief_tools import generate_content_brief
from backend.tools.content_optimizer_tools import optimize_content
from backend.tools.orchestrator_tools import build_plan, synthesize_final_strategy
from backend.tools.internal_linking_tools import analyze_internal_linking
from backend.tools.schema_tools import generate_schema_for_page
from backend.tools.aeo_geo_tools import generate_aeo_geo_suggestions
from backend.tools.monitoring_tools import detect_alerts, summarize_monitoring_run
from backend.tools.report_tools import build_full_report
from backend.tools.seo_rules import (
    audit_single_page,
    find_duplicate_titles_and_descriptions,
    check_crawlability_issues,
    calculate_seo_score,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI SEO Agent")


class ToolExecutionError(Exception):
    """Raised by a _do_... helper when a tool fails in a way the caller must handle."""
    pass


@app.get("/")
def health_check():
    return {"status": "ok", "message": "SEO Agent backend is running"}


@app.get("/test-llm")
def test_llm():
    result = ask_llm("Reply with exactly one word: Working")
    return {"llm_response": result}


# ---------- Website routes ----------

@app.post("/websites", response_model=schemas.WebsiteResponse)
def create_website(website: schemas.WebsiteCreate, db: Session = Depends(get_db)):
    new_website = models.Website(
        url=website.url,
        business_description=website.business_description,
        country=website.country,
        language=website.language,
        goal=website.goal,
    )
    db.add(new_website)
    db.commit()
    db.refresh(new_website)
    return new_website


@app.get("/websites", response_model=list[schemas.WebsiteResponse])
def list_websites(db: Session = Depends(get_db)):
    return db.query(models.Website).all()


# ---------- Crawl + Audit helper & routes ----------

def _do_crawl_and_audit(website_id: int, db: Session, max_pages: int) -> dict:
    db.query(models.Page).filter(models.Page.website_id == website_id).delete()
    db.query(models.SeoIssue).filter(models.SeoIssue.website_id == website_id).delete()
    db.commit()

    website = db.query(models.Website).filter(models.Website.id == website_id).first()

    crawled_pages, fully_crawled = crawl_website(website.url, max_pages=max_pages)

    only_start_url_failed = (
        len(crawled_pages) == 1
        and crawled_pages[0]["status_code"] == 0
        and crawled_pages[0].get("error")
    )

    all_issues = []
    for page_data in crawled_pages:
        new_page = models.Page(
            website_id=website_id,
            url=page_data["url"],
            status_code=page_data["status_code"],
            title=page_data["title"],
            meta_description=page_data["meta_description"],
            h1_count=page_data["h1_count"],
            h1_text=page_data["h1_text"],
            h2_count=page_data["h2_count"],
            h3_count=page_data["h3_count"],
            canonical=page_data["canonical"],
            robots_meta=page_data["robots_meta"],
            images_count=page_data["images_count"],
            images_missing_alt=page_data["images_missing_alt"],
            internal_links_count=page_data["internal_links_count"],
            external_links_count=page_data["external_links_count"],
            word_count=page_data["word_count"],
            has_schema=page_data["has_schema"],
            has_viewport_meta=page_data.get("has_viewport_meta", False),
            published_date=page_data.get("published_date"),
            modified_date=page_data.get("modified_date"),
            author_detected=page_data.get("author_detected", False),
            page_load_time_ms=page_data.get("page_load_time_ms"),
        )
        db.add(new_page)

        page_issues = audit_single_page(page_data)
        for issue in page_issues:
            issue["url"] = page_data["url"]
            all_issues.append(issue)

    duplicate_issues = find_duplicate_titles_and_descriptions(crawled_pages)
    all_issues.extend(duplicate_issues)

    crawlability_data = check_site_crawlability(website.url)
    crawlability_issues = check_crawlability_issues(crawlability_data)
    all_issues.extend(crawlability_issues)

    for issue in all_issues:
        new_issue = models.SeoIssue(
            website_id=website_id,
            page_url=issue.get("url"),
            issue_type=issue["issue_type"],
            severity=issue["severity"],
            message=issue["message"],
            recommendation=issue["recommendation"],
        )
        db.add(new_issue)

    db.commit()

    score_data = calculate_seo_score(all_issues, len(crawled_pages))

    if only_start_url_failed:
        crawl_note = f"Could not crawl the site at all: {crawled_pages[0]['error']}"
    elif fully_crawled:
        crawl_note = (
            f"This appears to be the entire website (up to your limit of {max_pages}) - "
            f"{len(crawled_pages)} page(s) were found and all {len(crawled_pages)} were crawled."
        )
    else:
        crawl_note = (
            f"Crawling stopped at your limit of {max_pages} pages, but more internal pages were "
            f"still queued. This site has more than {max_pages} pages - increase the limit to "
            f"crawl further."
        )

    return {
        "website_id": website_id,
        "pages_crawled": len(crawled_pages),
        "score": score_data["score"],
        "total_issues": score_data.get("total_issues", 0),
        "issues_by_severity": score_data.get("issues_by_severity", {}),
        "explanation": score_data["explanation"],
        "crawlability": crawlability_data,
        "fully_crawled": fully_crawled or bool(only_start_url_failed),
        "crawl_note": crawl_note,
    }


@app.post("/websites/{website_id}/crawl", response_model=schemas.AuditSummaryResponse)
def crawl_and_audit(website_id: int, request: schemas.CrawlRequest, db: Session = Depends(get_db)):
    website = db.query(models.Website).filter(models.Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    result = _do_crawl_and_audit(website_id, db, request.max_pages)
    return schemas.AuditSummaryResponse(**result)


@app.get("/websites/{website_id}/pages", response_model=list[schemas.PageResponse])
def get_pages(website_id: int, db: Session = Depends(get_db)):
    return db.query(models.Page).filter(models.Page.website_id == website_id).all()


@app.get("/websites/{website_id}/issues", response_model=list[schemas.IssueResponse])
def get_issues(website_id: int, db: Session = Depends(get_db)):
    return db.query(models.SeoIssue).filter(models.SeoIssue.website_id == website_id).all()


# ---------- Keyword Research helper & routes ----------

def _do_keyword_research(website: models.Website, db: Session, seed_keyword: str, keyword_type: str) -> list[models.Keyword]:
    keyword_ideas = research_keywords(
        seed_keyword=seed_keyword,
        business_description=website.business_description,
        country=website.country,
        language=website.language,
        keyword_type=keyword_type,
    )

    if not keyword_ideas:
        raise ToolExecutionError("Keyword research failed. The LLM did not return usable data.")

    saved_keywords = []
    for idea in keyword_ideas:
        new_keyword = models.Keyword(
            website_id=website.id,
            keyword=idea.get("keyword", ""),
            intent=idea.get("intent"),
            cluster=idea.get("cluster"),
            reason=idea.get("reason"),
            source="ai_suggested",
        )
        db.add(new_keyword)
        saved_keywords.append(new_keyword)

    db.commit()
    for kw in saved_keywords:
        db.refresh(kw)

    return saved_keywords


@app.post("/websites/{website_id}/keywords/research", response_model=list[schemas.KeywordResponse])
def run_keyword_research(website_id: int, request: schemas.KeywordResearchRequest, db: Session = Depends(get_db)):
    website = db.query(models.Website).filter(models.Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    try:
        saved_keywords = _do_keyword_research(website, db, request.seed_keyword, request.keyword_type)
    except ToolExecutionError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return saved_keywords


@app.get("/websites/{website_id}/keywords", response_model=list[schemas.KeywordResponse])
def get_keywords(website_id: int, db: Session = Depends(get_db)):
    return db.query(models.Keyword).filter(models.Keyword.website_id == website_id).all()


@app.delete("/websites/{website_id}/keywords")
def clear_keywords(website_id: int, db: Session = Depends(get_db)):
    db.query(models.Keyword).filter(models.Keyword.website_id == website_id).delete()
    db.commit()
    return {"status": "ok", "message": "Keywords cleared."}


# ---------- SERP routes ----------

@app.post("/serp/check")
def check_serp(request: schemas.SerpCheckRequest):
    provider = get_serp_provider()
    result = provider.search(request.keyword)
    return result


# ---------- Competitor Analysis helper & routes ----------

def _do_add_competitor(website: models.Website, db: Session, competitor_url: str) -> models.Competitor:
    competitor_page_summaries = analyze_competitor(competitor_url)

    new_competitor = models.Competitor(
        website_id=website.id,
        competitor_url=competitor_url,
        pages_analyzed=len(competitor_page_summaries),
    )
    db.add(new_competitor)
    db.commit()
    db.refresh(new_competitor)

    for page in competitor_page_summaries:
        new_page = models.CompetitorPage(
            competitor_id=new_competitor.id,
            url=page["url"],
            title=page["title"],
            h1_text=page["h1"],
            word_count=page["word_count"],
        )
        db.add(new_page)

    db.commit()
    db.refresh(new_competitor)

    return new_competitor


@app.post("/websites/{website_id}/competitors", response_model=schemas.CompetitorResponse)
def add_competitor(website_id: int, request: schemas.CompetitorAddRequest, db: Session = Depends(get_db)):
    website = db.query(models.Website).filter(models.Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    return _do_add_competitor(website, db, request.competitor_url)


@app.get("/websites/{website_id}/competitors", response_model=list[schemas.CompetitorResponse])
def list_competitors(website_id: int, db: Session = Depends(get_db)):
    return db.query(models.Competitor).filter(models.Competitor.website_id == website_id).all()


@app.get("/competitors/{competitor_id}/pages", response_model=list[schemas.CompetitorPageResponse])
def get_competitor_pages(competitor_id: int, db: Session = Depends(get_db)):
    return db.query(models.CompetitorPage).filter(models.CompetitorPage.competitor_id == competitor_id).all()


@app.delete("/websites/{website_id}/competitors/{competitor_id}")
def delete_competitor(website_id: int, competitor_id: int, db: Session = Depends(get_db)):
    db.query(models.CompetitorPage).filter(models.CompetitorPage.competitor_id == competitor_id).delete()
    db.query(models.Competitor).filter(
        models.Competitor.id == competitor_id, models.Competitor.website_id == website_id
    ).delete()
    db.commit()
    return {"status": "ok", "message": "Competitor removed."}


# ---------- Content Gap helper & routes ----------

def _do_content_gap_analysis(website: models.Website, db: Session) -> list[models.ContentGap]:
    our_pages = db.query(models.Page).filter(models.Page.website_id == website.id).all()
    keywords = db.query(models.Keyword).filter(models.Keyword.website_id == website.id).all()
    competitors = db.query(models.Competitor).filter(models.Competitor.website_id == website.id).all()

    if not our_pages:
        raise ToolExecutionError("No crawled pages found. Please run a Technical SEO Audit first.")
    if not competitors:
        raise ToolExecutionError("No competitors added. Please add at least one competitor first.")

    our_pages_data = [
        {"url": p.url, "title": p.title, "h1": p.h1_text} for p in our_pages
    ]
    keywords_data = [
        {"keyword": k.keyword, "intent": k.intent, "cluster": k.cluster} for k in keywords
    ]

    competitor_pages_by_url = {}
    for competitor in competitors:
        pages = db.query(models.CompetitorPage).filter(
            models.CompetitorPage.competitor_id == competitor.id
        ).all()
        competitor_pages_by_url[competitor.competitor_url] = [
            {"url": p.url, "title": p.title, "h1": p.h1_text} for p in pages
        ]

    db.query(models.ContentGap).filter(models.ContentGap.website_id == website.id).delete()
    db.commit()

    gap_ideas = find_content_gaps(
        business_description=website.business_description,
        our_pages=our_pages_data,
        competitor_pages_by_url=competitor_pages_by_url,
        researched_keywords=keywords_data,
    )

    if not gap_ideas:
        raise ToolExecutionError("Content gap analysis failed. The LLM did not return usable data.")

    saved_gaps = []
    for gap in gap_ideas:
        new_gap = models.ContentGap(
            website_id=website.id,
            opportunity=gap.get("opportunity", ""),
            gap_type=gap.get("gap_type"),
            priority=gap.get("priority"),
            reason=gap.get("reason"),
            suggested_page=gap.get("suggested_page"),
        )
        db.add(new_gap)
        saved_gaps.append(new_gap)

    db.commit()
    for gap in saved_gaps:
        db.refresh(gap)

    return saved_gaps


@app.post("/websites/{website_id}/content-gaps/analyze", response_model=list[schemas.ContentGapResponse])
def run_content_gap_analysis(website_id: int, db: Session = Depends(get_db)):
    website = db.query(models.Website).filter(models.Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    try:
        saved_gaps = _do_content_gap_analysis(website, db)
    except ToolExecutionError as e:
        status_code = 400 if "first" in str(e) else 502
        raise HTTPException(status_code=status_code, detail=str(e))

    return saved_gaps


@app.get("/websites/{website_id}/content-gaps", response_model=list[schemas.ContentGapResponse])
def get_content_gaps(website_id: int, db: Session = Depends(get_db)):
    return db.query(models.ContentGap).filter(models.ContentGap.website_id == website_id).all()


# ---------- Content Brief helper & routes ----------

def _do_content_brief_generation(website: models.Website, db: Session, topic: str) -> models.ContentBrief:
    keywords = db.query(models.Keyword).filter(models.Keyword.website_id == website.id).all()
    related_keywords = [k.keyword for k in keywords]

    brief_data = generate_content_brief(
        topic=topic,
        business_description=website.business_description,
        country=website.country,
        language=website.language,
        related_keywords=related_keywords,
    )

    if not brief_data:
        raise ToolExecutionError("Content brief generation failed. The LLM did not return usable data.")

    new_brief = models.ContentBrief(
        website_id=website.id,
        topic=topic,
        primary_keyword=brief_data.get("primary_keyword"),
        suggested_title=brief_data.get("suggested_title"),
        brief_json=json.dumps(brief_data),
    )
    db.add(new_brief)
    db.commit()
    db.refresh(new_brief)

    return new_brief


@app.post("/websites/{website_id}/content-briefs/generate", response_model=schemas.ContentBriefResponse)
def create_content_brief(website_id: int, request: schemas.ContentBriefRequest, db: Session = Depends(get_db)):
    website = db.query(models.Website).filter(models.Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    try:
        new_brief = _do_content_brief_generation(website, db, request.topic)
    except ToolExecutionError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return new_brief


@app.get("/websites/{website_id}/content-briefs", response_model=list[schemas.ContentBriefResponse])
def get_content_briefs(website_id: int, db: Session = Depends(get_db)):
    return db.query(models.ContentBrief).filter(models.ContentBrief.website_id == website_id).all()


@app.delete("/websites/{website_id}/content-briefs/{brief_id}")
def delete_content_brief(website_id: int, brief_id: int, db: Session = Depends(get_db)):
    db.query(models.ContentBrief).filter(
        models.ContentBrief.id == brief_id, models.ContentBrief.website_id == website_id
    ).delete()
    db.commit()
    return {"status": "ok", "message": "Content brief removed."}


# ---------- Content Optimizer helper & routes ----------

def _do_content_optimizer(
    website: models.Website, db: Session, page: models.Page,
    article_text: str = "", target_keywords: list[str] | None = None,
) -> dict:
    result = optimize_content(
        page_url=page.url,
        current_title=page.title,
        current_meta_description=page.meta_description,
        current_h1=page.h1_text,
        word_count=page.word_count,
        article_text=article_text or "",
        business_description=website.business_description,
        author_detected=page.author_detected,
        target_keywords=target_keywords,
    )

    if not result:
        raise ToolExecutionError("Content optimization failed. The LLM did not return usable data.")

    return result


@app.post("/websites/{website_id}/content-optimizer/analyze", response_model=schemas.ContentOptimizeResponse)
def run_content_optimizer(website_id: int, request: schemas.ContentOptimizeRequest, db: Session = Depends(get_db)):
    website = db.query(models.Website).filter(models.Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    page = db.query(models.Page).filter(
        models.Page.id == request.page_id, models.Page.website_id == website_id
    ).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    try:
        result = _do_content_optimizer(website, db, page, request.article_text or "", request.target_keywords)
    except ToolExecutionError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return schemas.ContentOptimizeResponse(**result)


# ---------- Internal Linking helper & routes (Phase 7) ----------

def _do_internal_linking_analysis(website: models.Website, db: Session) -> list[models.InternalLinkSuggestion]:
    pages = db.query(models.Page).filter(models.Page.website_id == website.id).all()
    if len(pages) < 2:
        raise ToolExecutionError("Need at least 2 crawled pages to suggest internal links. Please run a Technical SEO Audit with more pages first.")

    pages_data = [
        {
            "url": p.url, "title": p.title, "h1": p.h1_text,
            "word_count": p.word_count, "internal_links_count": p.internal_links_count,
        }
        for p in pages
    ]

    suggestions = analyze_internal_linking(
        our_pages=pages_data,
        business_description=website.business_description,
        country=website.country,
        language=website.language,
    )

    if not suggestions:
        raise ToolExecutionError("Internal linking analysis found no suggestions, or the LLM did not return usable data.")

    db.query(models.InternalLinkSuggestion).filter(models.InternalLinkSuggestion.website_id == website.id).delete()
    db.commit()

    saved = []
    for s in suggestions:
        new_suggestion = models.InternalLinkSuggestion(
            website_id=website.id,
            source_page_url=s.get("source_page_url", ""),
            target_page_url=s.get("target_page_url", ""),
            anchor_text=s.get("anchor_text"),
            reason=s.get("reason"),
        )
        db.add(new_suggestion)
        saved.append(new_suggestion)

    db.commit()
    for s in saved:
        db.refresh(s)

    return saved


@app.post("/websites/{website_id}/internal-linking/analyze", response_model=list[schemas.InternalLinkSuggestionResponse])
def run_internal_linking_analysis(website_id: int, db: Session = Depends(get_db)):
    website = db.query(models.Website).filter(models.Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    try:
        saved = _do_internal_linking_analysis(website, db)
    except ToolExecutionError as e:
        status_code = 400 if "at least" in str(e) else 502
        raise HTTPException(status_code=status_code, detail=str(e))

    return saved


@app.get("/websites/{website_id}/internal-linking", response_model=list[schemas.InternalLinkSuggestionResponse])
def get_internal_linking_suggestions(website_id: int, db: Session = Depends(get_db)):
    return db.query(models.InternalLinkSuggestion).filter(models.InternalLinkSuggestion.website_id == website_id).all()


@app.delete("/websites/{website_id}/internal-linking")
def clear_internal_linking_suggestions(website_id: int, db: Session = Depends(get_db)):
    db.query(models.InternalLinkSuggestion).filter(models.InternalLinkSuggestion.website_id == website_id).delete()
    db.commit()
    return {"status": "ok", "message": "Internal link suggestions cleared."}


# ---------- Schema / JSON-LD helper & routes (Phase 7) ----------

def _do_schema_generation(website: models.Website, db: Session, page: models.Page) -> list[models.SchemaMarkup]:
    result = generate_schema_for_page(
        page_url=page.url,
        title=page.title,
        meta_description=page.meta_description,
        h1_text=page.h1_text,
        word_count=page.word_count,
        has_schema=page.has_schema,
        business_description=website.business_description,
    )

    if not result or not result.get("schema_blocks"):
        raise ToolExecutionError("Schema generation found no applicable schema types for this page, or the LLM did not return usable data.")

    saved = []
    for block in result["schema_blocks"]:
        new_markup = models.SchemaMarkup(
            website_id=website.id,
            page_url=page.url,
            schema_type=block.get("schema_type", ""),
            schema_json=json.dumps(block.get("json_ld", {})),
            notes=block.get("notes"),
        )
        db.add(new_markup)
        saved.append(new_markup)

    db.commit()
    for s in saved:
        db.refresh(s)

    return saved


@app.post("/websites/{website_id}/schema/generate", response_model=list[schemas.SchemaMarkupResponse])
def create_schema_markup(website_id: int, request: schemas.SchemaGenerateRequest, db: Session = Depends(get_db)):
    website = db.query(models.Website).filter(models.Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    page = db.query(models.Page).filter(
        models.Page.id == request.page_id, models.Page.website_id == website_id
    ).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    try:
        saved = _do_schema_generation(website, db, page)
    except ToolExecutionError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return saved


@app.get("/websites/{website_id}/schema", response_model=list[schemas.SchemaMarkupResponse])
def get_schema_markups(website_id: int, db: Session = Depends(get_db)):
    return db.query(models.SchemaMarkup).filter(models.SchemaMarkup.website_id == website_id).all()


@app.delete("/websites/{website_id}/schema/{markup_id}")
def delete_schema_markup(website_id: int, markup_id: int, db: Session = Depends(get_db)):
    db.query(models.SchemaMarkup).filter(
        models.SchemaMarkup.id == markup_id, models.SchemaMarkup.website_id == website_id
    ).delete()
    db.commit()
    return {"status": "ok", "message": "Schema markup removed."}


# ---------- AEO / GEO helper & routes (Phase 7) ----------

def _do_aeo_geo_generation(website: models.Website, db: Session, page: models.Page, article_text: str = "") -> models.AeoGeoSuggestion:
    result = generate_aeo_geo_suggestions(
        page_url=page.url,
        title=page.title,
        meta_description=page.meta_description,
        h1_text=page.h1_text,
        word_count=page.word_count,
        business_description=website.business_description,
        article_text=article_text or "",
    )

    if not result:
        raise ToolExecutionError("AEO/GEO suggestion generation failed. The LLM did not return usable data.")

    new_suggestion = models.AeoGeoSuggestion(
        website_id=website.id,
        page_url=page.url,
        suggestion_json=json.dumps(result),
    )
    db.add(new_suggestion)
    db.commit()
    db.refresh(new_suggestion)

    return new_suggestion


@app.post("/websites/{website_id}/aeo-geo/generate", response_model=schemas.AeoGeoSuggestionResponse)
def create_aeo_geo_suggestion(website_id: int, request: schemas.AeoGeoGenerateRequest, db: Session = Depends(get_db)):
    website = db.query(models.Website).filter(models.Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    page = db.query(models.Page).filter(
        models.Page.id == request.page_id, models.Page.website_id == website_id
    ).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    try:
        new_suggestion = _do_aeo_geo_generation(website, db, page)
    except ToolExecutionError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return new_suggestion


@app.get("/websites/{website_id}/aeo-geo", response_model=list[schemas.AeoGeoSuggestionResponse])
def get_aeo_geo_suggestions(website_id: int, db: Session = Depends(get_db)):
    return db.query(models.AeoGeoSuggestion).filter(models.AeoGeoSuggestion.website_id == website_id).all()


@app.delete("/websites/{website_id}/aeo-geo/{suggestion_id}")
def delete_aeo_geo_suggestion(website_id: int, suggestion_id: int, db: Session = Depends(get_db)):
    db.query(models.AeoGeoSuggestion).filter(
        models.AeoGeoSuggestion.id == suggestion_id, models.AeoGeoSuggestion.website_id == website_id
    ).delete()
    db.commit()
    return {"status": "ok", "message": "AEO/GEO suggestion removed."}


# ---------- CMS Connection routes (Phase 8) ----------

def _get_active_cms_connection(website_id: int, db: Session) -> models.CMSConnection:
    connection = db.query(models.CMSConnection).filter(
        models.CMSConnection.website_id == website_id
    ).order_by(models.CMSConnection.updated_at.desc()).first()

    if not connection:
        raise ToolExecutionError("No WordPress connection configured for this project yet. Please set one up first.")

    return connection


@app.post("/websites/{website_id}/cms/connection", response_model=schemas.CMSConnectionResponse)
def save_cms_connection(website_id: int, request: schemas.CMSConnectionCreate, db: Session = Depends(get_db)):
    website = db.query(models.Website).filter(models.Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    existing = db.query(models.CMSConnection).filter(models.CMSConnection.website_id == website_id).first()
    if existing:
        db.delete(existing)
        db.commit()

    new_connection = models.CMSConnection(
        website_id=website_id,
        site_url=request.site_url,
        wp_username=request.wp_username,
        wp_app_password=request.wp_app_password,
        is_connected=False,
    )
    db.add(new_connection)
    db.commit()
    db.refresh(new_connection)

    return new_connection


@app.get("/websites/{website_id}/cms/connection", response_model=schemas.CMSConnectionResponse | None)
def get_cms_connection(website_id: int, db: Session = Depends(get_db)):
    return db.query(models.CMSConnection).filter(
        models.CMSConnection.website_id == website_id
    ).order_by(models.CMSConnection.updated_at.desc()).first()


@app.post("/websites/{website_id}/cms/test", response_model=schemas.CMSTestConnectionResponse)
def test_cms_connection(website_id: int, db: Session = Depends(get_db)):
    try:
        connection = _get_active_cms_connection(website_id, db)
    except ToolExecutionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    provider = WordPressProvider(connection.site_url, connection.wp_username, connection.wp_app_password)
    result = provider.test_connection()

    connection.is_connected = result["connected"]
    connection.last_tested_at = datetime.utcnow()
    connection.last_test_message = result["message"]
    db.commit()

    return schemas.CMSTestConnectionResponse(**result)


# ---------- Publish helper & routes (Phase 8) ----------

def _get_connected_provider(website_id: int, db: Session) -> WordPressProvider:
    connection = _get_active_cms_connection(website_id, db)
    if not connection.is_connected:
        raise ToolExecutionError(
            "This WordPress connection has not been verified yet (or the last test failed). "
            "Please test the connection successfully before publishing."
        )
    return WordPressProvider(connection.site_url, connection.wp_username, connection.wp_app_password)


def _log_publish_job(
    db: Session, website_id: int, job_type: str, source_description: str | None,
    target_page_url: str | None, status: str, wp_post_id: int | None,
    wp_edit_link: str | None, result_message: str | None,
) -> models.PublishJob:
    job = models.PublishJob(
        website_id=website_id, job_type=job_type, source_description=source_description,
        target_page_url=target_page_url, status=status, wp_post_id=wp_post_id,
        wp_edit_link=wp_edit_link, result_message=result_message,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _build_draft_content_from_brief(brief: models.ContentBrief) -> str:
    try:
        data = json.loads(brief.brief_json) if brief.brief_json else {}
    except json.JSONDecodeError:
        data = {}

    html_parts = [f"<h1>{data.get('h1', brief.suggested_title or brief.topic)}</h1>"]
    html_parts.append("<p><em>[Draft outline generated by AI - please write the actual article content for each section below]</em></p>")

    for h2 in data.get("h2s", []):
        html_parts.append(f"<h2>{h2}</h2>")
        html_parts.append("<p>[Write content for this section]</p>")

    for h3 in data.get("h3s", []):
        html_parts.append(f"<h3>{h3}</h3>")
        html_parts.append("<p>[Write content for this subsection]</p>")

    if data.get("faq_opportunities"):
        html_parts.append("<h2>Frequently Asked Questions</h2>")
        for faq in data.get("faq_opportunities", []):
            html_parts.append(f"<h3>{faq}</h3>")
            html_parts.append("<p>[Write the answer here]</p>")

    return "\n".join(html_parts)


@app.post("/websites/{website_id}/cms/publish/content-brief", response_model=schemas.PublishJobResponse)
def publish_draft_from_brief(website_id: int, request: schemas.PublishDraftFromBriefRequest, db: Session = Depends(get_db)):
    website = db.query(models.Website).filter(models.Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    brief = db.query(models.ContentBrief).filter(
        models.ContentBrief.id == request.content_brief_id, models.ContentBrief.website_id == website_id
    ).first()
    if not brief:
        raise HTTPException(status_code=404, detail="Content brief not found")

    try:
        provider = _get_connected_provider(website_id, db)
    except ToolExecutionError as e:
        return _log_publish_job(
            db, website_id, "draft_post", brief.topic, None,
            "failed", None, None, str(e),
        )

    content_html = _build_draft_content_from_brief(brief)
    result = provider.create_draft_post(
        title=brief.suggested_title or brief.topic,
        content_html=content_html,
    )

    return _log_publish_job(
        db, website_id, "draft_post", brief.topic, None,
        "success" if result["success"] else "failed",
        result.get("post_id"), result.get("edit_link"), result["message"],
    )


@app.post("/websites/{website_id}/cms/publish/schema", response_model=schemas.PublishJobResponse)
def publish_schema_to_wordpress(website_id: int, request: schemas.PublishSchemaRequest, db: Session = Depends(get_db)):
    website = db.query(models.Website).filter(models.Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    markups = db.query(models.SchemaMarkup).filter(
        models.SchemaMarkup.website_id == website_id, models.SchemaMarkup.page_url == request.page_url
    ).all()
    if not markups:
        raise HTTPException(status_code=404, detail="No saved schema markups found for this page URL.")

    try:
        provider = _get_connected_provider(website_id, db)
    except ToolExecutionError as e:
        return _log_publish_job(
            db, website_id, "schema_injection", None, request.page_url,
            "failed", None, None, str(e),
        )

    wp_post = provider.find_post_or_page_by_url(request.page_url)
    if not wp_post:
        return _log_publish_job(
            db, website_id, "schema_injection", None, request.page_url,
            "failed", None, None, "Could not find a matching WordPress post or page for this URL.",
        )

    schema_blocks = [json.loads(m.schema_json) for m in markups]
    result = provider.inject_schema_into_post(wp_post["id"], schema_blocks)

    return _log_publish_job(
        db, website_id, "schema_injection", f"{len(markups)} schema block(s)", request.page_url,
        "success" if result["success"] else "failed",
        wp_post["id"], wp_post.get("link"), result["message"],
    )


@app.post("/websites/{website_id}/cms/publish/meta", response_model=schemas.PublishJobResponse)
def publish_meta_to_wordpress(website_id: int, request: schemas.PublishMetaUpdateRequest, db: Session = Depends(get_db)):
    website = db.query(models.Website).filter(models.Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    try:
        provider = _get_connected_provider(website_id, db)
    except ToolExecutionError as e:
        return _log_publish_job(
            db, website_id, "meta_update", None, request.page_url,
            "failed", None, None, str(e),
        )

    wp_post = provider.find_post_or_page_by_url(request.page_url)
    if not wp_post:
        return _log_publish_job(
            db, website_id, "meta_update", None, request.page_url,
            "failed", None, None, "Could not find a matching WordPress post or page for this URL.",
        )

    result = provider.update_post_title_and_meta_description(
        wp_post["id"], request.optimized_title, request.optimized_meta_description,
    )

    final_message = result["message"]
    if request.optimized_h1:
        final_message += (
            f" H1 was NOT auto-applied (WordPress has no dedicated H1 field) - "
            f"please manually update the content's H1 to: '{request.optimized_h1}'."
        )

    return _log_publish_job(
        db, website_id, "meta_update", None, request.page_url,
        "success" if result["success"] else "failed",
        wp_post["id"], wp_post.get("link"), final_message,
    )


@app.get("/websites/{website_id}/cms/jobs", response_model=list[schemas.PublishJobResponse])
def get_publish_jobs(website_id: int, db: Session = Depends(get_db)):
    return db.query(models.PublishJob).filter(
        models.PublishJob.website_id == website_id
    ).order_by(models.PublishJob.created_at.desc()).all()


# ---------- Monitoring routes (Phase 9) ----------

@app.post("/websites/{website_id}/monitoring/run", response_model=schemas.MonitoringSnapshotResponse)
def run_monitoring_check(website_id: int, request: schemas.MonitoringRunRequest, db: Session = Depends(get_db)):
    website = db.query(models.Website).filter(models.Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    previous_snapshot_row = db.query(models.MonitoringSnapshot).filter(
        models.MonitoringSnapshot.website_id == website_id
    ).order_by(models.MonitoringSnapshot.created_at.desc()).first()

    previous_snapshot = None
    previous_issues = []
    if previous_snapshot_row:
        previous_snapshot = {"score": previous_snapshot_row.score}
        previous_issues_rows = db.query(models.SeoIssue).filter(models.SeoIssue.website_id == website_id).all()
        previous_issues = [{"page_url": i.page_url, "issue_type": i.issue_type, "severity": i.severity} for i in previous_issues_rows]

    audit_result = _do_crawl_and_audit(website_id, db, request.max_pages)
    new_issues_rows = db.query(models.SeoIssue).filter(models.SeoIssue.website_id == website_id).all()
    new_issues = [{"page_url": i.page_url, "issue_type": i.issue_type, "severity": i.severity, "message": i.message} for i in new_issues_rows]

    serp_provider = get_serp_provider()
    saved_keywords = db.query(models.Keyword).filter(models.Keyword.website_id == website_id).all()
    serp_results = []
    for kw in saved_keywords[:5]:
        serp_results.append({"keyword": kw.keyword, "result": serp_provider.search(kw.keyword)})

    alerts = detect_alerts(previous_snapshot, audit_result, previous_issues, new_issues)

    summary_text = summarize_monitoring_run(previous_snapshot, audit_result, alerts, serp_results)

    new_snapshot = models.MonitoringSnapshot(
        website_id=website_id,
        score=audit_result["score"],
        total_issues=audit_result["total_issues"],
        issues_by_severity_json=json.dumps(audit_result["issues_by_severity"]),
        pages_crawled=audit_result["pages_crawled"],
        summary_text=summary_text,
    )
    db.add(new_snapshot)
    db.commit()
    db.refresh(new_snapshot)

    for alert in alerts:
        new_alert = models.MonitoringAlert(
            website_id=website_id,
            snapshot_id=new_snapshot.id,
            alert_type=alert["alert_type"],
            message=alert["message"],
            page_url=alert.get("page_url"),
        )
        db.add(new_alert)
    db.commit()

    if alerts:
        try:
            _do_content_gap_analysis(website, db)
        except ToolExecutionError:
            pass

    db.refresh(new_snapshot)
    return new_snapshot


@app.get("/websites/{website_id}/monitoring/snapshots", response_model=list[schemas.MonitoringSnapshotListResponse])
def list_monitoring_snapshots(website_id: int, db: Session = Depends(get_db)):
    return db.query(models.MonitoringSnapshot).filter(
        models.MonitoringSnapshot.website_id == website_id
    ).order_by(models.MonitoringSnapshot.created_at.desc()).all()


@app.get("/monitoring/snapshots/{snapshot_id}", response_model=schemas.MonitoringSnapshotResponse)
def get_monitoring_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    snapshot = db.query(models.MonitoringSnapshot).filter(models.MonitoringSnapshot.id == snapshot_id).first()
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return snapshot


@app.get("/websites/{website_id}/monitoring/alerts", response_model=list[schemas.MonitoringAlertResponse])
def list_monitoring_alerts(website_id: int, db: Session = Depends(get_db)):
    return db.query(models.MonitoringAlert).filter(
        models.MonitoringAlert.website_id == website_id
    ).order_by(models.MonitoringAlert.created_at.desc()).all()


# ---------- Full Report route (new) ----------

@app.get("/websites/{website_id}/report", response_model=schemas.ReportResponse)
def generate_full_report(website_id: int, db: Session = Depends(get_db)):
    website = db.query(models.Website).filter(models.Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    context = {
        "website": {
            "url": website.url,
            "business_description": website.business_description,
            "goal": website.goal,
        },
        "pages": [
            {"url": p.url} for p in db.query(models.Page).filter(models.Page.website_id == website_id).all()
        ],
        "issues": [
            {"severity": i.severity, "issue_type": i.issue_type, "page_url": i.page_url, "message": i.message}
            for i in db.query(models.SeoIssue).filter(models.SeoIssue.website_id == website_id).all()
        ],
        "keywords": [
            {"keyword": k.keyword, "intent": k.intent, "cluster": k.cluster}
            for k in db.query(models.Keyword).filter(models.Keyword.website_id == website_id).all()
        ],
        "competitors": [
            {"competitor_url": c.competitor_url, "pages_analyzed": c.pages_analyzed}
            for c in db.query(models.Competitor).filter(models.Competitor.website_id == website_id).all()
        ],
        "content_gaps": [
            {"opportunity": g.opportunity, "priority": g.priority, "reason": g.reason}
            for g in db.query(models.ContentGap).filter(models.ContentGap.website_id == website_id).all()
        ],
        "content_briefs": [
            {"topic": b.topic, "suggested_title": b.suggested_title}
            for b in db.query(models.ContentBrief).filter(models.ContentBrief.website_id == website_id).all()
        ],
        "internal_links": [
            {"source_page_url": l.source_page_url, "target_page_url": l.target_page_url, "anchor_text": l.anchor_text}
            for l in db.query(models.InternalLinkSuggestion).filter(models.InternalLinkSuggestion.website_id == website_id).all()
        ],
        "schema_markups": [
            {"schema_type": s.schema_type, "page_url": s.page_url}
            for s in db.query(models.SchemaMarkup).filter(models.SchemaMarkup.website_id == website_id).all()
        ],
        "aeo_geo_suggestions": [
            {"page_url": a.page_url}
            for a in db.query(models.AeoGeoSuggestion).filter(models.AeoGeoSuggestion.website_id == website_id).all()
        ],
        "pagespeed_results": [
            {"page_url": p.page_url, "strategy": p.strategy, "performance_score": p.performance_score, "seo_score": p.seo_score}
            for p in db.query(models.PageSpeedResult).filter(models.PageSpeedResult.website_id == website_id).all()
        ],
        "publish_jobs": [
            {"status": j.status, "job_type": j.job_type, "result_message": j.result_message}
            for j in db.query(models.PublishJob).filter(models.PublishJob.website_id == website_id).all()
        ],
        "monitoring_snapshots": [
            {"created_at": s.created_at.isoformat(), "score": s.score, "total_issues": s.total_issues}
            for s in db.query(models.MonitoringSnapshot).filter(
                models.MonitoringSnapshot.website_id == website_id
            ).order_by(models.MonitoringSnapshot.created_at.desc()).all()
        ],
        "monitoring_alerts": [
            {"alert_type": a.alert_type, "message": a.message}
            for a in db.query(models.MonitoringAlert).filter(models.MonitoringAlert.website_id == website_id).all()
        ],
    }

    report_markdown = build_full_report(context)

    return schemas.ReportResponse(
        website_id=website_id,
        generated_at=datetime.utcnow(),
        report_markdown=report_markdown,
    )


# ---------- PageSpeed Insights routes (post-Phase-9 update) ----------

@app.post("/websites/{website_id}/pagespeed/check", response_model=schemas.PageSpeedCheckResponse)
def run_pagespeed_check(website_id: int, request: schemas.PageSpeedCheckRequest, db: Session = Depends(get_db)):
    website = db.query(models.Website).filter(models.Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    page = db.query(models.Page).filter(
        models.Page.id == request.page_id, models.Page.website_id == website_id
    ).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    result = check_pagespeed(page.url, request.strategy)

    if not result.get("configured"):
        return schemas.PageSpeedCheckResponse(configured=False, message=result["message"])

    if not result.get("success"):
        return schemas.PageSpeedCheckResponse(configured=True, success=False, message=result.get("message"))

    metrics = {
        "first_contentful_paint": result.get("first_contentful_paint"),
        "largest_contentful_paint": result.get("largest_contentful_paint"),
        "total_blocking_time": result.get("total_blocking_time"),
        "cumulative_layout_shift": result.get("cumulative_layout_shift"),
        "speed_index": result.get("speed_index"),
    }

    new_result = models.PageSpeedResult(
        website_id=website_id,
        page_url=page.url,
        strategy=request.strategy,
        performance_score=result.get("performance_score"),
        seo_score=result.get("seo_score"),
        accessibility_score=result.get("accessibility_score"),
        best_practices_score=result.get("best_practices_score"),
        metrics_json=json.dumps(metrics),
    )
    db.add(new_result)
    db.commit()
    db.refresh(new_result)

    return schemas.PageSpeedCheckResponse(configured=True, success=True, result=new_result)


@app.get("/websites/{website_id}/pagespeed", response_model=list[schemas.PageSpeedResultResponse])
def get_pagespeed_results(website_id: int, db: Session = Depends(get_db)):
    return db.query(models.PageSpeedResult).filter(
        models.PageSpeedResult.website_id == website_id
    ).order_by(models.PageSpeedResult.created_at.desc()).all()


# ---------- Backlinks / User Signals routes (not configured, ready for future) ----------

@app.get("/websites/{website_id}/backlinks/check", response_model=schemas.BacklinkCheckResponse)
def run_backlink_check(website_id: int, db: Session = Depends(get_db)):
    website = db.query(models.Website).filter(models.Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    domain = urlparse(website.url).netloc
    result = check_backlinks(domain)
    return schemas.BacklinkCheckResponse(**result)


@app.get("/websites/{website_id}/user-signals/check")
def run_user_signals_check(website_id: int, page_url: str, db: Session = Depends(get_db)):
    website = db.query(models.Website).filter(models.Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    result = check_user_signals(page_url)
    return schemas.UserSignalsCheckResponse(**result)


# ---------- Orchestrator Agent + Human Approval (Phase 6, extended in Phase 7) ----------

def _gather_orchestrator_context(website: models.Website, db: Session) -> dict:
    pages = db.query(models.Page).filter(models.Page.website_id == website.id).all()
    keywords = db.query(models.Keyword).filter(models.Keyword.website_id == website.id).all()
    competitors = db.query(models.Competitor).filter(models.Competitor.website_id == website.id).all()
    gaps = db.query(models.ContentGap).filter(models.ContentGap.website_id == website.id).all()

    return {
        "business_description": website.business_description,
        "country": website.country,
        "language": website.language,
        "existing_pages_count": len(pages),
        "existing_keywords_count": len(keywords),
        "existing_competitors_count": len(competitors),
        "existing_content_gaps_count": len(gaps),
        "existing_page_urls": [p.url for p in pages][:20],
        "existing_content_gap_opportunities": [g.opportunity for g in gaps][:10],
    }


def _execute_agent_step(step: models.AgentStep, website: models.Website, db: Session) -> dict:
    step.status = "running"
    step.started_at = datetime.utcnow()
    db.commit()

    try:
        tool_input = json.loads(step.tool_input_json) if step.tool_input_json else {}
        output_summary = ""

        if step.tool_name == "technical_audit":
            result = _do_crawl_and_audit(website.id, db, tool_input.get("max_pages", 10))
            output_summary = (
                f"Crawled {result['pages_crawled']} pages ({result['crawl_note']}), "
                f"SEO score {result['score']}/100, {result['total_issues']} issues found."
            )
            step.tool_output_json = json.dumps(result)

        elif step.tool_name == "keyword_research":
            saved = _do_keyword_research(website, db, tool_input.get("seed_keyword", ""), "both")
            keyword_list = [k.keyword for k in saved]
            output_summary = f"Generated {len(saved)} keyword ideas: {', '.join(keyword_list[:10])}."
            step.tool_output_json = json.dumps({"keywords": keyword_list})

        elif step.tool_name == "competitor_analysis":
            competitor = _do_add_competitor(website, db, tool_input.get("competitor_url", ""))
            output_summary = f"Analyzed competitor {competitor.competitor_url}, {competitor.pages_analyzed} pages."
            step.tool_output_json = json.dumps({
                "competitor_url": competitor.competitor_url,
                "pages_analyzed": competitor.pages_analyzed,
            })

        elif step.tool_name == "content_gap_analysis":
            gaps = _do_content_gap_analysis(website, db)
            gap_list = [g.opportunity for g in gaps]
            output_summary = f"Found {len(gaps)} content gap opportunities: {', '.join(gap_list[:10])}."
            step.tool_output_json = json.dumps({"opportunities": gap_list})

        elif step.tool_name == "content_brief_generation":
            brief = _do_content_brief_generation(website, db, tool_input.get("topic", ""))
            output_summary = f"Generated content brief for topic '{brief.topic}' (title: {brief.suggested_title})."
            step.tool_output_json = json.dumps({"topic": brief.topic, "suggested_title": brief.suggested_title})

        elif step.tool_name == "content_optimizer":
            page_url = tool_input.get("page_url", "")
            page = db.query(models.Page).filter(
                models.Page.website_id == website.id, models.Page.url == page_url
            ).first()
            if not page:
                raise ToolExecutionError(f"Page '{page_url}' not found in this project's crawled pages.")
            result = _do_content_optimizer(website, db, page)
            output_summary = f"Optimization recommendations generated for {page_url}."
            step.tool_output_json = json.dumps(result)

        elif step.tool_name == "internal_linking_analysis":
            suggestions = _do_internal_linking_analysis(website, db)
            output_summary = f"Found {len(suggestions)} internal linking opportunities."
            step.tool_output_json = json.dumps({
                "suggestions": [
                    {"source": s.source_page_url, "target": s.target_page_url, "anchor_text": s.anchor_text}
                    for s in suggestions
                ]
            })

        elif step.tool_name == "schema_generation":
            page_url = tool_input.get("page_url", "")
            page = db.query(models.Page).filter(
                models.Page.website_id == website.id, models.Page.url == page_url
            ).first()
            if not page:
                raise ToolExecutionError(f"Page '{page_url}' not found in this project's crawled pages.")
            markups = _do_schema_generation(website, db, page)
            types_list = [m.schema_type for m in markups]
            output_summary = f"Generated schema markup for {page_url}: {', '.join(types_list)}."
            step.tool_output_json = json.dumps({"page_url": page_url, "schema_types": types_list})

        elif step.tool_name == "aeo_geo_generation":
            page_url = tool_input.get("page_url", "")
            page = db.query(models.Page).filter(
                models.Page.website_id == website.id, models.Page.url == page_url
            ).first()
            if not page:
                raise ToolExecutionError(f"Page '{page_url}' not found in this project's crawled pages.")
            suggestion = _do_aeo_geo_generation(website, db, page)
            suggestion_data = json.loads(suggestion.suggestion_json)
            faq_count = len(suggestion_data.get("faq_items", []))
            output_summary = f"Generated {faq_count} FAQ items and AEO/GEO structure suggestions for {page_url}."
            step.tool_output_json = suggestion.suggestion_json

        else:
            raise ToolExecutionError(f"Unknown tool: {step.tool_name}")

        step.status = "completed"
        step.completed_at = datetime.utcnow()
        db.commit()
        return {"tool_name": step.tool_name, "purpose": step.purpose, "output_summary": output_summary}

    except ToolExecutionError as e:
        step.status = "failed"
        step.error_message = str(e)
        step.completed_at = datetime.utcnow()
        db.commit()
        return {"tool_name": step.tool_name, "purpose": step.purpose, "output_summary": f"FAILED: {e}"}
    except Exception as e:
        step.status = "failed"
        step.error_message = f"Unexpected error: {e}"
        step.completed_at = datetime.utcnow()
        db.commit()
        return {"tool_name": step.tool_name, "purpose": step.purpose, "output_summary": f"FAILED: {e}"}


def _run_remaining_steps_and_synthesize(agent_run: models.AgentRun, website: models.Website, db: Session) -> models.AgentRun:
    agent_run.status = "running"
    db.commit()

    steps = db.query(models.AgentStep).filter(
        models.AgentStep.agent_run_id == agent_run.id
    ).order_by(models.AgentStep.step_number).all()

    for step in steps:
        if step.status in ("pending", "failed"):
            _execute_agent_step(step, website, db)

    all_steps = db.query(models.AgentStep).filter(
        models.AgentStep.agent_run_id == agent_run.id
    ).order_by(models.AgentStep.step_number).all()

    completed_results = []
    for step in all_steps:
        if step.status == "completed":
            output = json.loads(step.tool_output_json) if step.tool_output_json else {}
            completed_results.append({
                "tool_name": step.tool_name,
                "purpose": step.purpose,
                "output_summary": json.dumps(output),
            })
        elif step.status == "failed":
            completed_results.append({
                "tool_name": step.tool_name,
                "purpose": step.purpose,
                "output_summary": f"This step failed: {step.error_message}",
            })

    strategy = synthesize_final_strategy(agent_run.goal, completed_results)

    if not strategy:
        agent_run.status = "failed"
        agent_run.error_message = "Could not synthesize a final strategy. The LLM did not return usable data."
    else:
        agent_run.final_strategy_json = json.dumps(strategy)
        agent_run.status = "awaiting_approval"
        agent_run.error_message = None

    db.commit()
    db.refresh(agent_run)
    return agent_run


@app.post("/websites/{website_id}/orchestrator/runs", response_model=schemas.AgentRunResponse)
def create_orchestrator_run(website_id: int, request: schemas.OrchestratorRunRequest, db: Session = Depends(get_db)):
    website = db.query(models.Website).filter(models.Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    context = _gather_orchestrator_context(website, db)
    plan = build_plan(request.goal, context)

    agent_run = models.AgentRun(
        website_id=website_id,
        goal=request.goal,
        status="planning",
        plan_json=json.dumps(plan),
    )
    db.add(agent_run)
    db.commit()
    db.refresh(agent_run)

    if not plan:
        agent_run.status = "failed"
        agent_run.error_message = (
            "The Orchestrator could not build a plan for this goal. "
            "Try rephrasing the goal or being more specific."
        )
        db.commit()
        db.refresh(agent_run)
        return agent_run

    for step_data in plan:
        tool_input = step_data.get("tool_input", {})
        if step_data.get("tool_name") == "technical_audit":
            tool_input["max_pages"] = request.max_pages

        new_step = models.AgentStep(
            agent_run_id=agent_run.id,
            step_number=step_data.get("step_number", 0),
            tool_name=step_data.get("tool_name"),
            purpose=step_data.get("purpose"),
            tool_input_json=json.dumps(tool_input),
            status="pending",
        )
        db.add(new_step)

    db.commit()

    agent_run = _run_remaining_steps_and_synthesize(agent_run, website, db)
    return agent_run


@app.get("/websites/{website_id}/orchestrator/runs", response_model=list[schemas.AgentRunListResponse])
def list_orchestrator_runs(website_id: int, db: Session = Depends(get_db)):
    return db.query(models.AgentRun).filter(
        models.AgentRun.website_id == website_id
    ).order_by(models.AgentRun.created_at.desc()).all()


@app.get("/orchestrator/runs/{run_id}", response_model=schemas.AgentRunResponse)
def get_orchestrator_run(run_id: int, db: Session = Depends(get_db)):
    agent_run = db.query(models.AgentRun).filter(models.AgentRun.id == run_id).first()
    if not agent_run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return agent_run


@app.post("/orchestrator/runs/{run_id}/resume", response_model=schemas.AgentRunResponse)
def resume_orchestrator_run(run_id: int, db: Session = Depends(get_db)):
    agent_run = db.query(models.AgentRun).filter(models.AgentRun.id == run_id).first()
    if not agent_run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    website = db.query(models.Website).filter(models.Website.id == agent_run.website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    agent_run = _run_remaining_steps_and_synthesize(agent_run, website, db)
    return agent_run


@app.post("/orchestrator/runs/{run_id}/approval", response_model=schemas.AgentRunResponse)
def submit_orchestrator_approval(run_id: int, request: schemas.ApprovalActionRequest, db: Session = Depends(get_db)):
    agent_run = db.query(models.AgentRun).filter(models.AgentRun.id == run_id).first()
    if not agent_run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    if request.action == "approve":
        agent_run.approval_status = "approved"
        agent_run.status = "approved"
    elif request.action == "edit":
        if not request.edited_strategy_text:
            raise HTTPException(status_code=400, detail="edited_strategy_text is required for the 'edit' action.")
        agent_run.approval_status = "edited"
        agent_run.approved_strategy_text = request.edited_strategy_text
        agent_run.status = "approved"
    elif request.action == "reject":
        agent_run.approval_status = "rejected"
        agent_run.status = "rejected"
    else:
        raise HTTPException(status_code=400, detail="action must be 'approve', 'edit', or 'reject'.")

    agent_run.approval_notes = request.approval_notes
    db.commit()
    db.refresh(agent_run)
    return agent_run