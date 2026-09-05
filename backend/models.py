# This file defines our database tables
# Phase 1: websites
# Phase 2: pages + seo_issues
# Phase 3: keywords
# Phase 4: competitors + competitor_pages + content_gaps
# Phase 5: content_briefs added
# Phase 6: agent_runs + agent_steps added (Orchestrator Agent + Human Approval)
# Phase 7: internal_link_suggestions + schema_markups + aeo_geo_suggestions added
# Phase 8: cms_connections + publish_jobs added (WordPress/CMS Execution)
# Phase 9: monitoring_snapshots + monitoring_alerts added (Autonomous Monitoring)
# Post-9 update: pagespeed_results added (real Google PageSpeed Insights data)

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.database import Base


class Website(Base):
    __tablename__ = "websites"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    business_description = Column(String, nullable=True)
    country = Column(String, nullable=True)
    language = Column(String, nullable=True)
    goal = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    pages = relationship("Page", back_populates="website")
    issues = relationship("SeoIssue", back_populates="website")
    keywords = relationship("Keyword", back_populates="website")
    competitors = relationship("Competitor", back_populates="website")
    content_gaps = relationship("ContentGap", back_populates="website")
    content_briefs = relationship("ContentBrief", back_populates="website")
    agent_runs = relationship("AgentRun", back_populates="website")
    internal_link_suggestions = relationship("InternalLinkSuggestion", back_populates="website")
    schema_markups = relationship("SchemaMarkup", back_populates="website")
    aeo_geo_suggestions = relationship("AeoGeoSuggestion", back_populates="website")
    cms_connections = relationship("CMSConnection", back_populates="website")
    publish_jobs = relationship("PublishJob", back_populates="website")
    monitoring_snapshots = relationship("MonitoringSnapshot", back_populates="website")
    monitoring_alerts = relationship("MonitoringAlert", back_populates="website")
    pagespeed_results = relationship("PageSpeedResult", back_populates="website")


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)

    url = Column(String, nullable=False)
    status_code = Column(Integer, nullable=True)
    title = Column(String, nullable=True)
    meta_description = Column(Text, nullable=True)
    h1_count = Column(Integer, default=0)
    h1_text = Column(String, nullable=True)
    h2_count = Column(Integer, default=0)
    h3_count = Column(Integer, default=0)
    canonical = Column(String, nullable=True)
    robots_meta = Column(String, nullable=True)
    images_count = Column(Integer, default=0)
    images_missing_alt = Column(Integer, default=0)
    internal_links_count = Column(Integer, default=0)
    external_links_count = Column(Integer, default=0)
    word_count = Column(Integer, default=0)
    has_schema = Column(Boolean, default=False)

    # new fields for mobile/freshness/E-E-A-T/performance checks
    has_viewport_meta = Column(Boolean, default=False)
    published_date = Column(String, nullable=True)
    modified_date = Column(String, nullable=True)
    author_detected = Column(Boolean, default=False)
    page_load_time_ms = Column(Float, nullable=True)

    crawled_at = Column(DateTime(timezone=True), server_default=func.now())

    website = relationship("Website", back_populates="pages")


class SeoIssue(Base):
    __tablename__ = "seo_issues"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)
    page_url = Column(String, nullable=True)

    issue_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    message = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    website = relationship("Website", back_populates="issues")


class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)

    keyword = Column(String, nullable=False)
    intent = Column(String, nullable=True)
    cluster = Column(String, nullable=True)
    reason = Column(Text, nullable=True)
    source = Column(String, default="ai_suggested")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    website = relationship("Website", back_populates="keywords")


class Competitor(Base):
    __tablename__ = "competitors"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)

    competitor_url = Column(String, nullable=False)
    pages_analyzed = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    website = relationship("Website", back_populates="competitors")
    pages = relationship("CompetitorPage", back_populates="competitor")


class CompetitorPage(Base):
    __tablename__ = "competitor_pages"

    id = Column(Integer, primary_key=True, index=True)
    competitor_id = Column(Integer, ForeignKey("competitors.id"), nullable=False)

    url = Column(String, nullable=False)
    title = Column(String, nullable=True)
    h1_text = Column(String, nullable=True)
    word_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    competitor = relationship("Competitor", back_populates="pages")


class ContentGap(Base):
    __tablename__ = "content_gaps"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)

    opportunity = Column(String, nullable=False)
    gap_type = Column(String, nullable=True)
    priority = Column(String, nullable=True)
    reason = Column(Text, nullable=True)
    suggested_page = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    website = relationship("Website", back_populates="content_gaps")


class ContentBrief(Base):
    __tablename__ = "content_briefs"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)

    topic = Column(String, nullable=False)
    primary_keyword = Column(String, nullable=True)
    suggested_title = Column(String, nullable=True)
    brief_json = Column(Text, nullable=True)  # full structured brief stored as JSON text

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    website = relationship("Website", back_populates="content_briefs")


class AgentRun(Base):
    """
    One Orchestrator Agent run: a user goal, the plan the LLM built for it,
    and the final strategy waiting for (or already given) human approval.
    """
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)

    goal = Column(Text, nullable=False)
    # planning, running, awaiting_approval, approved, rejected, failed
    status = Column(String, default="planning")

    plan_json = Column(Text, nullable=True)  # ordered list of planned steps
    final_strategy_json = Column(Text, nullable=True)  # combined recommendations

    approval_status = Column(String, default="pending")  # pending, approved, edited, rejected
    approved_strategy_text = Column(Text, nullable=True)  # filled in only if user edits before approving
    approval_notes = Column(Text, nullable=True)

    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    website = relationship("Website", back_populates="agent_runs")
    steps = relationship("AgentStep", back_populates="agent_run", order_by="AgentStep.step_number")


class AgentStep(Base):
    """
    One tool call inside an AgentRun. Storing every step (with its own status
    and output) is what lets an interrupted/failed run be resumed later
    instead of starting the whole plan over from scratch.
    """
    __tablename__ = "agent_steps"

    id = Column(Integer, primary_key=True, index=True)
    agent_run_id = Column(Integer, ForeignKey("agent_runs.id"), nullable=False)

    step_number = Column(Integer, nullable=False)
    tool_name = Column(String, nullable=False)
    purpose = Column(Text, nullable=True)  # why the orchestrator picked this step

    tool_input_json = Column(Text, nullable=True)
    tool_output_json = Column(Text, nullable=True)

    # pending, running, completed, failed, skipped
    status = Column(String, default="pending")
    error_message = Column(Text, nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    agent_run = relationship("AgentRun", back_populates="steps")


class InternalLinkSuggestion(Base):
    """
    One suggested internal link between two pages that are ALREADY crawled
    for this website. This agent never invents new pages - only links
    between pages that exist. Suggestions only, nothing is auto-applied.
    """
    __tablename__ = "internal_link_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)

    source_page_url = Column(String, nullable=False)
    target_page_url = Column(String, nullable=False)
    anchor_text = Column(String, nullable=True)
    reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    website = relationship("Website", back_populates="internal_link_suggestions")


class SchemaMarkup(Base):
    """
    One suggested JSON-LD schema block for a specific crawled page.
    schema_type comes from a curated list (see schema_tools.py), not
    freely invented by the LLM.
    """
    __tablename__ = "schema_markups"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)

    page_url = Column(String, nullable=False)
    schema_type = Column(String, nullable=False)
    schema_json = Column(Text, nullable=False)  # the actual JSON-LD block, stored as JSON text
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    website = relationship("Website", back_populates="schema_markups")


class AeoGeoSuggestion(Base):
    """
    AEO/GEO (Answer Engine / Generative Engine Optimization) suggestions for
    one crawled page: FAQ items, a concise answer block, and structure tips
    to make the page easier for AI search engines to cite.
    """
    __tablename__ = "aeo_geo_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)

    page_url = Column(String, nullable=False)
    suggestion_json = Column(Text, nullable=False)  # {"faq_items": [...], "concise_answer_block": "...", "structure_suggestions": [...]}

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    website = relationship("Website", back_populates="aeo_geo_suggestions")


class CMSConnection(Base):
    """
    Stores the WordPress site connection details for one website project.
    One connection per website (the most recently saved one is used).
    Note: the Application Password is stored as-is (not encrypted) - fine
    for local/dev use only, per the project's current scope.
    """
    __tablename__ = "cms_connections"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)

    site_url = Column(String, nullable=False)
    wp_username = Column(String, nullable=False)
    wp_app_password = Column(String, nullable=False)

    is_connected = Column(Boolean, default=False)  # result of the last test, not assumed
    last_tested_at = Column(DateTime(timezone=True), nullable=True)
    last_test_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    website = relationship("Website", back_populates="cms_connections")


class PublishJob(Base):
    """
    A log of every WordPress publish/update action attempted, successful
    or not. Nothing here auto-publishes - draft_post jobs always create a
    WordPress draft, and meta/schema jobs only update existing content.
    """
    __tablename__ = "publish_jobs"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)

    # draft_post, schema_injection, meta_update
    job_type = Column(String, nullable=False)
    source_description = Column(String, nullable=True)  # e.g. content brief topic, or page URL
    target_page_url = Column(String, nullable=True)

    status = Column(String, default="pending")  # pending, success, failed
    wp_post_id = Column(Integer, nullable=True)
    wp_edit_link = Column(String, nullable=True)
    result_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    website = relationship("Website", back_populates="publish_jobs")


class MonitoringSnapshot(Base):
    """
    One point-in-time technical SEO snapshot, taken each time "Run
    Monitoring Check" is used. Snapshots are compared to each other to
    detect score drops over time.
    """
    __tablename__ = "monitoring_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)

    score = Column(Float, nullable=False)
    total_issues = Column(Integer, default=0)
    issues_by_severity_json = Column(Text, nullable=True)
    pages_crawled = Column(Integer, default=0)
    summary_text = Column(Text, nullable=True)  # short AI-written summary of this run

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    website = relationship("Website", back_populates="monitoring_snapshots")
    alerts = relationship("MonitoringAlert", back_populates="snapshot")


class MonitoringAlert(Base):
    """
    One alert raised by a monitoring run: a score drop or a newly appeared
    critical issue. Only based on real, measured audit data - never on
    unverified/mock ranking data.
    """
    __tablename__ = "monitoring_alerts"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)
    snapshot_id = Column(Integer, ForeignKey("monitoring_snapshots.id"), nullable=False)

    alert_type = Column(String, nullable=False)  # score_drop, new_critical_issue
    message = Column(Text, nullable=False)
    page_url = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    website = relationship("Website", back_populates="monitoring_alerts")
    snapshot = relationship("MonitoringSnapshot", back_populates="alerts")


class PageSpeedResult(Base):
    """
    One real Google PageSpeed Insights check result for a page, for one
    strategy (mobile or desktop). Only stored when the API call succeeded -
    a failed/not-configured check is never saved as if it were real data.
    """
    __tablename__ = "pagespeed_results"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)

    page_url = Column(String, nullable=False)
    strategy = Column(String, nullable=False)  # mobile or desktop

    performance_score = Column(Integer, nullable=True)
    seo_score = Column(Integer, nullable=True)
    accessibility_score = Column(Integer, nullable=True)
    best_practices_score = Column(Integer, nullable=True)
    metrics_json = Column(Text, nullable=True)  # FCP, LCP, TBT, CLS, speed index

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    website = relationship("Website", back_populates="pagespeed_results")