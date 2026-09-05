# This file defines Pydantic models
# These control what data the API accepts and returns (request/response shape)
#
# UPDATE: KeywordResearchRequest now accepts keyword_type (short_tail,
# long_tail, or both). New ReportResponse schema added for the full
# project report (Monitoring & Refresh page).

from pydantic import BaseModel
from datetime import datetime


# ---------- Website schemas ----------

class WebsiteCreate(BaseModel):
    url: str
    business_description: str | None = None
    country: str | None = None
    language: str | None = None
    goal: str | None = None


class WebsiteResponse(BaseModel):
    id: int
    url: str
    business_description: str | None
    country: str | None
    language: str | None
    goal: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Crawl / Audit schemas ----------

class CrawlRequest(BaseModel):
    max_pages: int = 10  # user can type any number - no artificial cap in the UI


class PageResponse(BaseModel):
    id: int
    url: str
    status_code: int | None
    title: str | None
    meta_description: str | None
    h1_count: int
    h1_text: str | None
    h2_count: int
    h3_count: int
    canonical: str | None
    images_count: int
    images_missing_alt: int
    word_count: int
    has_schema: bool
    has_viewport_meta: bool
    published_date: str | None
    modified_date: str | None
    author_detected: bool
    page_load_time_ms: float | None
    crawled_at: datetime

    class Config:
        from_attributes = True


class IssueResponse(BaseModel):
    id: int
    page_url: str | None
    issue_type: str
    severity: str
    message: str | None
    recommendation: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditSummaryResponse(BaseModel):
    website_id: int
    pages_crawled: int
    score: float
    total_issues: int
    issues_by_severity: dict
    explanation: str
    crawlability: dict | None = None
    fully_crawled: bool = True
    crawl_note: str = ""


# ---------- Keyword Research schemas ----------

class KeywordResearchRequest(BaseModel):
    seed_keyword: str
    keyword_type: str = "both"  # "short_tail", "long_tail", or "both"


class KeywordResponse(BaseModel):
    id: int
    keyword: str
    intent: str | None
    cluster: str | None
    reason: str | None
    source: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- SERP schemas ----------

class SerpCheckRequest(BaseModel):
    keyword: str


# ---------- Competitor schemas ----------

class CompetitorAddRequest(BaseModel):
    competitor_url: str


class CompetitorPageResponse(BaseModel):
    id: int
    url: str
    title: str | None
    h1_text: str | None
    word_count: int

    class Config:
        from_attributes = True


class CompetitorResponse(BaseModel):
    id: int
    competitor_url: str
    pages_analyzed: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Content Gap schemas ----------

class ContentGapResponse(BaseModel):
    id: int
    opportunity: str
    gap_type: str | None
    priority: str | None
    reason: str | None
    suggested_page: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Content Brief schemas ----------

class ContentBriefRequest(BaseModel):
    topic: str
    content_gap_id: int | None = None


class ContentBriefResponse(BaseModel):
    id: int
    topic: str
    primary_keyword: str | None
    suggested_title: str | None
    brief_json: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Content Optimizer schemas ----------

class ContentOptimizeRequest(BaseModel):
    page_id: int
    article_text: str | None = None
    target_keywords: list[str] | None = None


class ContentOptimizeResponse(BaseModel):
    current_state_summary: str | None = None
    problems: list[str] = []
    why_it_matters: list[str] = []
    recommendations: list[str] = []
    optimized_title: str | None = None
    optimized_meta_description: str | None = None
    optimized_h1: str | None = None
    keyword_intent_alignment: str | None = None
    eeat_signals_present: list[str] = []
    eeat_signals_missing: list[str] = []
    notes: str | None = None


# ---------- Orchestrator / Agent Run schemas ----------

class OrchestratorRunRequest(BaseModel):
    goal: str
    max_pages: int = 10


class AgentStepResponse(BaseModel):
    id: int
    step_number: int
    tool_name: str
    purpose: str | None
    tool_input_json: str | None
    tool_output_json: str | None
    status: str
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None

    class Config:
        from_attributes = True


class AgentRunResponse(BaseModel):
    id: int
    website_id: int
    goal: str
    status: str
    plan_json: str | None
    final_strategy_json: str | None
    approval_status: str
    approved_strategy_text: str | None
    approval_notes: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    steps: list[AgentStepResponse] = []

    class Config:
        from_attributes = True


class AgentRunListResponse(BaseModel):
    id: int
    website_id: int
    goal: str
    status: str
    approval_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApprovalActionRequest(BaseModel):
    action: str
    edited_strategy_text: str | None = None
    approval_notes: str | None = None


# ---------- Internal Linking schemas ----------

class InternalLinkSuggestionResponse(BaseModel):
    id: int
    source_page_url: str
    target_page_url: str
    anchor_text: str | None
    reason: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Schema / JSON-LD schemas ----------

class SchemaGenerateRequest(BaseModel):
    page_id: int


class SchemaMarkupResponse(BaseModel):
    id: int
    page_url: str
    schema_type: str
    schema_json: str
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- AEO / GEO schemas ----------

class AeoGeoGenerateRequest(BaseModel):
    page_id: int


class AeoGeoSuggestionResponse(BaseModel):
    id: int
    page_url: str
    suggestion_json: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- CMS Connection schemas (Phase 8) ----------

class CMSConnectionCreate(BaseModel):
    site_url: str
    wp_username: str
    wp_app_password: str


class CMSConnectionResponse(BaseModel):
    id: int
    site_url: str
    wp_username: str
    is_connected: bool
    last_tested_at: datetime | None
    last_test_message: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class CMSTestConnectionResponse(BaseModel):
    connected: bool
    message: str
    site_name: str | None = None


# ---------- Publish Job schemas (Phase 8) ----------

class PublishDraftFromBriefRequest(BaseModel):
    content_brief_id: int


class PublishSchemaRequest(BaseModel):
    page_url: str


class PublishMetaUpdateRequest(BaseModel):
    page_url: str
    optimized_title: str | None = None
    optimized_meta_description: str | None = None
    optimized_h1: str | None = None


class PublishJobResponse(BaseModel):
    id: int
    job_type: str
    source_description: str | None
    target_page_url: str | None
    status: str
    wp_post_id: int | None
    wp_edit_link: str | None
    result_message: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Monitoring schemas (Phase 9) ----------

class MonitoringAlertResponse(BaseModel):
    id: int
    alert_type: str
    message: str
    page_url: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class MonitoringSnapshotResponse(BaseModel):
    id: int
    score: float
    total_issues: int
    issues_by_severity_json: str | None
    pages_crawled: int
    summary_text: str | None
    created_at: datetime
    alerts: list[MonitoringAlertResponse] = []

    class Config:
        from_attributes = True


class MonitoringSnapshotListResponse(BaseModel):
    id: int
    score: float
    total_issues: int
    pages_crawled: int
    created_at: datetime

    class Config:
        from_attributes = True


class MonitoringRunRequest(BaseModel):
    max_pages: int = 10


# ---------- PageSpeed schemas (post-Phase-9 update) ----------

class PageSpeedCheckRequest(BaseModel):
    page_id: int
    strategy: str = "mobile"


class PageSpeedResultResponse(BaseModel):
    id: int
    page_url: str
    strategy: str
    performance_score: int | None
    seo_score: int | None
    accessibility_score: int | None
    best_practices_score: int | None
    metrics_json: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class PageSpeedCheckResponse(BaseModel):
    configured: bool
    success: bool | None = None
    message: str | None = None
    result: PageSpeedResultResponse | None = None


# ---------- Backlink / User Signals schemas (not configured, ready for future) ----------

class BacklinkCheckResponse(BaseModel):
    configured: bool
    domain: str
    message: str


class UserSignalsCheckResponse(BaseModel):
    configured: bool
    page_url: str
    message: str


# ---------- Full Report schema (new) ----------

class ReportResponse(BaseModel):
    website_id: int
    generated_at: datetime
    report_markdown: str