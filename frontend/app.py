# This is the Streamlit dashboard - professional SaaS-style interface
# Phase 1-5 features preserved. Phase 6 added Orchestrator Agent & Human
# Approval page. Phase 7 added Internal Linking, Schema/JSON-LD & AEO/GEO
# page. Phase 8 added WordPress Publishing page. Phase 9 added Monitoring &
# Refresh page.
# Post-9 update #1: Technical SEO Audit page shows crawlability/mobile/
# freshness/E-E-A-T. Content Optimizer shows E-E-A-T + keyword intent.
# New "SEO Signals & Speed" page added (PageSpeed/Backlinks/User Signals).
# Post-9 update #2: max_pages input restored, crawl_note shown honestly.
# Post-9 update #3: Keyword Research now has a short-tail/long-tail/both
# dropdown. Monitoring & Refresh page now has a "Generate Full Report"
# button that builds a complete Markdown project report and offers it
# for download.
# Project selection bug fix (per-page dropdowns, session_state
# ["active_website_id"] as canonical source of truth) preserved.

import html
import json
import subprocess
import sys
import threading

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from streamlit_option_menu import option_menu

BACKEND_URL = "http://127.0.0.1:8000"


@st.cache_resource(show_spinner="Starting SEOPilot AI backend, please wait...")
def _start_backend_once():
    try:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=False,
            timeout=300,
        )
    except Exception:
        pass

    def _run_backend():
        import uvicorn
        from backend.main import app as fastapi_app
        uvicorn.run(fastapi_app, host="127.0.0.1", port=8000, log_level="info")

    thread = threading.Thread(target=_run_backend, daemon=True)
    thread.start()
    return True


_start_backend_once()

st.set_page_config(
    page_title="SEOPilot AI | Autonomous SEO Agent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- COLOR PALETTE ----------
COLOR_PRIMARY = "#6C5CE7"
COLOR_PRIMARY_DARK = "#4834D4"
COLOR_CORAL = "#FF7675"
COLOR_TEAL = "#00B894"
COLOR_AMBER = "#FDB44B"
COLOR_RED = "#E74C3C"
COLOR_GRAY = "#95A5A6"

SEVERITY_COLORS = {"critical": COLOR_RED, "high": COLOR_CORAL, "medium": COLOR_AMBER, "low": COLOR_TEAL}
PRIORITY_COLORS = {"high": COLOR_CORAL, "medium": COLOR_AMBER, "low": COLOR_TEAL}
INTENT_COLORS = {
    "informational": COLOR_PRIMARY,
    "commercial": COLOR_TEAL,
    "transactional": COLOR_CORAL,
    "navigational": COLOR_AMBER,
}
GAP_TYPE_COLORS = {"new_content": COLOR_PRIMARY, "content_expansion": COLOR_TEAL}
YES_NO_COLORS = {"yes": COLOR_TEAL, "no": COLOR_GRAY}
RUN_STATUS_COLORS = {
    "planning": COLOR_GRAY,
    "running": COLOR_AMBER,
    "awaiting_approval": COLOR_PRIMARY,
    "approved": COLOR_TEAL,
    "rejected": COLOR_RED,
    "failed": COLOR_RED,
}
STEP_STATUS_COLORS = {
    "pending": COLOR_GRAY,
    "running": COLOR_AMBER,
    "completed": COLOR_TEAL,
    "failed": COLOR_RED,
    "skipped": COLOR_GRAY,
}
JOB_STATUS_COLORS = {
    "pending": COLOR_GRAY,
    "success": COLOR_TEAL,
    "failed": COLOR_RED,
}
ALERT_TYPE_COLORS = {
    "score_drop": COLOR_RED,
    "new_critical_issue": COLOR_CORAL,
}


# ---------- GLOBAL CSS ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

    .stApp { background-color: #FAF9FF; color: #2D2A3D; }
    h1, h2, h3, h4, p, label, span { color: #2D2A3D !important; }
    h2, h3 { color: #4834D4 !important; font-weight: 700 !important; }
    .stCaption, [data-testid="stCaptionContainer"] { color: #7C7A94 !important; }

    section[data-testid="stSidebar"] {
        background-color: #F5F3FD;
        border-right: 1px solid #E0DBF7;
    }
    section[data-testid="stSidebar"] * { color: #2D2A3D !important; }

    .stTextInput input, .stTextArea textarea, .stNumberInput input {
        background-color: #FFFFFF !important;
        color: #2D2A3D !important;
        border: 1.5px solid #D8D2F5 !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border: 1.5px solid #6C5CE7 !important;
        box-shadow: 0 0 0 2px rgba(108, 92, 231, 0.15) !important;
    }
    .stSelectbox div[data-baseweb="select"], .stMultiSelect div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        border-radius: 8px !important;
    }

    .stButton button, .stFormSubmitButton button {
        background-color: #6C5CE7 !important;
        color: #FFFFFF !important;
        font-weight: 600;
        border-radius: 8px;
        border: none;
        transition: background-color 0.2s ease;
    }
    .stButton button:hover, .stFormSubmitButton button:hover {
        background-color: #FF7675 !important;
        color: #FFFFFF !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border-radius: 14px;
        padding: 6px;
        border: 1px solid #EDEAFB;
        box-shadow: 0 2px 14px rgba(108, 92, 231, 0.07);
    }

    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border-radius: 14px;
        padding: 18px;
        border: 1px solid #EDEAFB;
        box-shadow: 0 2px 14px rgba(108, 92, 231, 0.07);
    }
    div[data-testid="stMetricLabel"] { color: #6C5CE7 !important; font-weight: 600 !important; font-size: 13px !important; }
    div[data-testid="stMetricValue"] { color: #2D2A3D !important; font-weight: 800 !important; }

    .stDataFrame, .stTable {
        background-color: #FFFFFF !important;
        border-radius: 10px;
        border: 1px solid #EDEAFB;
    }

    .stAlert { border-radius: 10px; }
    div[data-baseweb="notification"] { border-radius: 10px; }

    div[data-testid="stAlertContainer"][kind="success"] {
        background-color: #E8FBF5 !important; border-left: 4px solid #00B894 !important;
    }
    div[data-testid="stAlertContainer"][kind="info"] {
        background-color: #EFEDFC !important; border-left: 4px solid #6C5CE7 !important;
    }
    div[data-testid="stAlertContainer"][kind="warning"] {
        background-color: #FFF6E5 !important; border-left: 4px solid #FDB44B !important;
    }
    div[data-testid="stAlertContainer"][kind="error"] {
        background-color: #FFEDED !important; border-left: 4px solid #FF7675 !important;
    }

    hr { border-color: #E5E0F7 !important; }
    span[data-baseweb="tag"] {
        background-color: #6C5CE7 !important; color: #FFFFFF !important; border-radius: 6px !important;
    }

    /* project switcher box on top of each page */
    .project-switcher-box {
        background: #FFFFFF;
        border: 1.5px solid #E0DBF7;
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 18px;
        box-shadow: 0 2px 10px rgba(108, 92, 231, 0.06);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- HELPER FUNCTIONS ----------

def api_get(path: str, timeout: int = 10):
    try:
        response = requests.get(f"{BACKEND_URL}{path}", timeout=timeout)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []


def status_code_color(value) -> str:
    try:
        code = int(value)
    except (TypeError, ValueError):
        return COLOR_GRAY
    if code == 0:
        return COLOR_GRAY
    if 200 <= code < 300:
        return COLOR_TEAL
    if 300 <= code < 400:
        return COLOR_PRIMARY
    if 400 <= code < 500:
        return COLOR_CORAL
    return COLOR_RED


def badge_span(value, color: str) -> str:
    text = html.escape("" if value is None else str(value))
    return (
        f"<span style='background-color:{color}22; color:{color}; padding:4px 12px; "
        f"border-radius:20px; font-weight:600; font-size:12px; text-transform:capitalize; "
        f"white-space:nowrap;'>{text}</span>"
    )


def render_styled_table(records: list[dict], columns: list[tuple], badge_columns: dict | None = None):
    badge_columns = badge_columns or {}

    if not records:
        st.markdown(
            "<p style='color:#7C7A94; padding:12px;'>No data available yet.</p>",
            unsafe_allow_html=True,
        )
        return

    header_cells = "".join(
        f"<th style='text-align:left; padding:10px 14px; font-size:11.5px; text-transform:uppercase; "
        f"letter-spacing:0.04em; color:#7C7A94; border-bottom:2px solid #EDEAFB; white-space:nowrap;'>"
        f"{html.escape(label)}</th>"
        for key, label in columns
    )

    body_rows = ""
    for row in records:
        cells = ""
        for key, label in columns:
            value = row.get(key)
            if key in badge_columns:
                spec = badge_columns[key]
                if spec == "status_code":
                    color = status_code_color(value)
                else:
                    color = spec.get(str(value).lower(), COLOR_GRAY) if value else COLOR_GRAY
                cell_html = badge_span(value, color)
            else:
                text = "" if value is None else str(value)
                cell_html = html.escape(text)
            cells += (
                f"<td style='padding:10px 14px; font-size:13.5px; color:#2D2A3D; "
                f"border-bottom:1px solid #F3F1FC; vertical-align:top;'>{cell_html}</td>"
            )
        body_rows += f"<tr>{cells}</tr>"

    table_html = f"""
    <div style='overflow-x:auto; border-radius:12px; border:1px solid #EDEAFB; background:#FFFFFF; margin-top:8px;'>
    <table style='width:100%; border-collapse:collapse;'>
    <thead><tr>{header_cells}</tr></thead>
    <tbody>{body_rows}</tbody>
    </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)


def style_fig(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#2D2A3D", family="Inter, sans-serif"),
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
    )
    return fig


def project_dropdown(page_key: str, websites: list[dict]):
    """
    Renders a project selector dropdown for the given page.
    Uses a single canonical value (session_state['active_website_id']) so the
    selection is consistent no matter which page's dropdown was last used.
    """
    if not websites:
        st.info("No projects yet. Create one on the 'Project Setup' page first.", icon="ℹ️")
        return None

    valid_ids = [w["id"] for w in websites]

    if st.session_state.get("active_website_id") not in valid_ids:
        st.session_state["active_website_id"] = valid_ids[0]

    labels = [f"{w['url']} (ID: {w['id']})" for w in websites]
    id_by_label = dict(zip(labels, valid_ids))
    label_by_id = dict(zip(valid_ids, labels))

    current_id = st.session_state["active_website_id"]
    current_label = label_by_id[current_id]
    default_index = labels.index(current_label)

    widget_key = f"proj_dd_{page_key}_{current_id}"

    with st.container():
        st.markdown("<div class='project-switcher-box'>", unsafe_allow_html=True)
        chosen_label = st.selectbox(
            "📁 Select Project to Work On",
            labels,
            index=default_index,
            key=widget_key,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.session_state["active_website_id"] = id_by_label[chosen_label]
    return st.session_state["active_website_id"]


# ---------- BRANDED HEADER ----------
st.markdown(
    """
    <div style='background: linear-gradient(135deg, #6C5CE7 0%, #4834D4 100%);
                padding:26px 32px; border-radius:16px; margin-bottom:22px;
                box-shadow:0 8px 24px rgba(108,92,231,0.25);
                display:flex; align-items:center; gap:16px;'>
        <span style='font-size:38px;'>🚀</span>
        <div>
            <h1 style='color:#FFFFFF !important; margin:0; font-size:26px; font-weight:800 !important;'>
                SEOPilot AI
            </h1>
            <p style='color:#E8E4FC !important; margin:4px 0 0 0; font-size:13.5px;'>
                Autonomous SEO Agent Platform — Crawl · Research · Analyze · Optimize · Orchestrate · Publish · Monitor
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- FETCH WEBSITES (once per run) ----------
websites = api_get("/websites")

# ---------- SIDEBAR: NAVIGATION + READ-ONLY ACTIVE PROJECT BADGE ----------
with st.sidebar:
    st.markdown(
        """
        <div style='text-align:center; padding:4px 0 14px 0;'>
            <span style='font-size:36px;'>🤖</span>
            <h3 style='color:#6C5CE7 !important; margin:6px 0 0 0; font-weight:800 !important;'>SEOPilot AI</h3>
            <p style='color:#7C7A94 !important; font-size:11.5px; margin:2px 0 0 0;'>v1.4</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nav_selection = option_menu(
        menu_title=None,
        options=[
            "Dashboard",
            "Project Setup",
            "Technical SEO Audit",
            "Keyword Research",
            "Competitors & Content Gaps",
            "Content Briefs & Optimizer",
            "Orchestrator & Approval",
            "Linking, Schema & AEO/GEO",
            "SEO Signals & Speed",
            "WordPress Publishing",
            "Monitoring & Refresh",
        ],
        icons=[
            "speedometer2", "folder-plus", "search", "key", "people",
            "file-earmark-text", "diagram-3", "link-45deg", "lightning-charge",
            "wordpress", "activity",
        ],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0", "background-color": "transparent"},
            "icon": {"color": "#6C5CE7", "font-size": "16px"},
            "nav-link": {
                "font-size": "14px",
                "text-align": "left",
                "margin": "3px 0",
                "border-radius": "8px",
                "color": "#2D2A3D",
                "--hover-color": "#EFEDFC",
            },
            "nav-link-selected": {"background-color": "#6C5CE7", "color": "white"},
        },
    )

    st.markdown("---")
    st.markdown("#### 📌 Currently Active Project")

    if websites:
        valid_ids = [w["id"] for w in websites]
        if st.session_state.get("active_website_id") not in valid_ids:
            st.session_state["active_website_id"] = valid_ids[0]
        active_website = next(w for w in websites if w["id"] == st.session_state["active_website_id"])
        st.markdown(
            f"<span style='background-color:{COLOR_PRIMARY}22; color:{COLOR_PRIMARY}; "
            f"padding:6px 12px; border-radius:8px; font-weight:600; font-size:12.5px; "
            f"display:inline-block; word-break:break-all;'>{html.escape(active_website['url'])}</span>",
            unsafe_allow_html=True,
        )
        st.caption("Change project using the dropdown at the top of each page.")
    else:
        st.info("No projects yet.", icon="ℹ️")

    st.markdown("---")
    st.caption("Built with FastAPI, Streamlit & Gemini AI")


# ==========================================================
# PAGE: DASHBOARD (OVERVIEW)
# ==========================================================
if nav_selection == "Dashboard":

    st.caption("📊 Project Overview")

    selected_id = project_dropdown("dashboard", websites)

    if not websites:
        st.info("No projects yet. Head to 'Project Setup' to create your first SEO project.", icon="👋")
    elif selected_id:
        selected_website = next(w for w in websites if w["id"] == selected_id)

        st.markdown(f"### {selected_website['url']}")
        if selected_website.get("goal"):
            st.caption(f"🎯 Goal: {selected_website['goal']}")

        pages = api_get(f"/websites/{selected_id}/pages")
        issues = api_get(f"/websites/{selected_id}/issues")
        keywords = api_get(f"/websites/{selected_id}/keywords")
        competitors = api_get(f"/websites/{selected_id}/competitors")
        content_gaps = api_get(f"/websites/{selected_id}/content-gaps")
        content_briefs = api_get(f"/websites/{selected_id}/content-briefs")
        orchestrator_runs = api_get(f"/websites/{selected_id}/orchestrator/runs")
        internal_links = api_get(f"/websites/{selected_id}/internal-linking")
        schema_markups = api_get(f"/websites/{selected_id}/schema")
        publish_jobs = api_get(f"/websites/{selected_id}/cms/jobs")
        monitoring_snapshots = api_get(f"/websites/{selected_id}/monitoring/snapshots")
        monitoring_alerts = api_get(f"/websites/{selected_id}/monitoring/alerts")

        critical_count = sum(1 for i in issues if i.get("severity") == "critical")

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            with st.container(border=True):
                st.metric("📄 Pages Crawled", len(pages))
        with k2:
            with st.container(border=True):
                st.metric("⚠️ Total Issues", len(issues), delta=f"{critical_count} critical", delta_color="inverse")
        with k3:
            with st.container(border=True):
                st.metric("🔑 Keywords", len(keywords))
        with k4:
            with st.container(border=True):
                st.metric("🏆 Competitors", len(competitors))

        k5, k6, k7, k8, k9, k10, k11 = st.columns(7)
        with k5:
            with st.container(border=True):
                st.metric("💡 Content Gaps", len(content_gaps))
        with k6:
            with st.container(border=True):
                st.metric("📝 Content Briefs", len(content_briefs))
        with k7:
            with st.container(border=True):
                st.metric("🧭 Orchestrator Runs", len(orchestrator_runs))
        with k8:
            with st.container(border=True):
                st.metric("🔗 Link Suggestions", len(internal_links))
        with k9:
            with st.container(border=True):
                st.metric("🏷️ Schema Blocks", len(schema_markups))
        with k10:
            with st.container(border=True):
                st.metric("📤 Publish Jobs", len(publish_jobs))
        with k11:
            with st.container(border=True):
                st.metric("🔔 Active Alerts", len(monitoring_alerts))

        pending_approvals = [r for r in orchestrator_runs if r.get("status") == "awaiting_approval"]
        if pending_approvals:
            st.warning(
                f"⏳ {len(pending_approvals)} orchestrator run(s) are waiting for your approval. "
                "Go to 'Orchestrator & Approval' to review them.",
                icon="⏳",
            )

        if monitoring_alerts:
            st.error(
                f"🔔 {len(monitoring_alerts)} monitoring alert(s) recorded (score drops / new critical issues). "
                "Go to 'Monitoring & Refresh' to review them.",
                icon="🔔",
            )

        if monitoring_snapshots:
            latest_score = monitoring_snapshots[0]["score"]
            st.success(f"✅ Latest monitored SEO Score for this project: **{latest_score} / 100**", icon="✅")
        elif "audit_result" in st.session_state and st.session_state["audit_result"].get("website_id") == selected_id:
            score = st.session_state["audit_result"]["score"]
            st.success(f"✅ Last SEO Score for this project: **{score} / 100**", icon="✅")
        else:
            st.info("Run a Technical SEO Audit (or a Monitoring Check) to see your latest SEO Score here.", icon="ℹ️")

        st.divider()

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            with st.container(border=True):
                st.markdown("##### Issues by Severity")
                if issues:
                    severity_counts = pd.Series([i["severity"] for i in issues]).value_counts().reset_index()
                    severity_counts.columns = ["severity", "count"]
                    fig = px.pie(
                        severity_counts, names="severity", values="count", hole=0.55,
                        color="severity", color_discrete_map=SEVERITY_COLORS,
                    )
                    st.plotly_chart(style_fig(fig), use_container_width=True)
                else:
                    st.caption("Run a Technical SEO Audit to see issues breakdown.")

        with chart_col2:
            with st.container(border=True):
                st.markdown("##### Keywords by Intent")
                if keywords:
                    intent_counts = pd.Series([k.get("intent") or "unknown" for k in keywords]).value_counts().reset_index()
                    intent_counts.columns = ["intent", "count"]
                    fig = px.bar(
                        intent_counts, x="intent", y="count", color="intent",
                        color_discrete_map=INTENT_COLORS,
                    )
                    fig.update_layout(showlegend=False)
                    st.plotly_chart(style_fig(fig), use_container_width=True)
                else:
                    st.caption("Run Keyword Research to see intent distribution.")

        st.divider()

        list_col1, list_col2 = st.columns(2)

        with list_col1:
            st.markdown("##### 🔴 Top Priority Issues")
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            top_issues = sorted(issues, key=lambda i: severity_order.get(i.get("severity"), 4))[:5]
            issue_rows = [
                {"severity": i.get("severity"), "issue_type": i.get("issue_type"), "page_url": i.get("page_url")}
                for i in top_issues
            ]
            render_styled_table(
                issue_rows,
                [("severity", "Severity"), ("issue_type", "Issue"), ("page_url", "Page")],
                badge_columns={"severity": SEVERITY_COLORS},
            )

        with list_col2:
            st.markdown("##### 💡 Top Content Opportunities")
            priority_order = {"high": 0, "medium": 1, "low": 2}
            top_gaps = sorted(content_gaps, key=lambda g: priority_order.get(g.get("priority"), 3))[:5]
            gap_rows = [
                {"priority": g.get("priority"), "opportunity": g.get("opportunity")}
                for g in top_gaps
            ]
            render_styled_table(
                gap_rows,
                [("priority", "Priority"), ("opportunity", "Opportunity")],
                badge_columns={"priority": PRIORITY_COLORS},
            )

        st.divider()
        st.caption(
            "ℹ️ SERP, Backlinks & User Signals are running in mock/demo or not-configured mode — "
            "no paid API or OAuth configured yet. Page Speed uses the real Google PageSpeed Insights "
            "API when configured. Use 'Orchestrator & Approval' to run the multi-agent workflow, "
            "'SEO Signals & Speed' for performance/backlink/engagement checks, 'WordPress Publishing' "
            "to push approved content live, and 'Monitoring & Refresh' to track SEO score changes "
            "and generate a full report."
        )

# ==========================================================
# PAGE: PROJECT SETUP
# ==========================================================
elif nav_selection == "Project Setup":

    st.caption("Phase 1 — Project Setup")

    st.subheader("System Status")
    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            try:
                health = requests.get(f"{BACKEND_URL}/", timeout=5).json()
                st.success(f"Backend: {health['message']}")
            except Exception:
                st.error("Backend not reachable. Run the FastAPI server first.")

    with col2:
        with st.container(border=True):
            if st.button("Test LLM Connection", use_container_width=True):
                try:
                    result = requests.get(f"{BACKEND_URL}/test-llm", timeout=15).json()
                    response_text = result.get("llm_response", "")
                    if "error" in response_text.lower() or "not configured" in response_text.lower():
                        st.error(response_text)
                    else:
                        st.success(f"LLM says: {response_text}")
                except Exception as e:
                    st.error(f"LLM test failed: {e}")

    st.divider()
    st.subheader("Create New SEO Project")

    with st.container(border=True):
        with st.form("new_project_form"):
            url = st.text_input("Website URL", placeholder="https://example.com")
            business = st.text_area("Business Description", placeholder="Online AI courses")

            col_a, col_b = st.columns(2)
            with col_a:
                country = st.text_input("Target Country", placeholder="Pakistan")
            with col_b:
                language = st.text_input("Target Language", placeholder="English")

            goal = st.text_area("SEO Goal", placeholder="Increase organic traffic for top service pages")

            submitted = st.form_submit_button("Create Project", use_container_width=True)

            if submitted:
                if not url:
                    st.warning("Website URL is required.")
                else:
                    payload = {
                        "url": url,
                        "business_description": business,
                        "country": country,
                        "language": language,
                        "goal": goal,
                    }
                    try:
                        res = requests.post(f"{BACKEND_URL}/websites", json=payload, timeout=10)
                        if res.status_code == 200:
                            new_project = res.json()
                            st.session_state["active_website_id"] = new_project["id"]
                            st.success("Project created successfully! It is now your active project.")
                            st.rerun()
                        else:
                            st.error(f"Failed: {res.text}")
                    except Exception as e:
                        st.error(f"Could not reach backend: {e}")

    st.divider()
    st.subheader("Your Projects")
    st.caption("Click 'Set Active' to work on a project across all other pages.")

    if websites:
        for w in websites:
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 2, 1.3])
                with col1:
                    st.markdown(f"**{w['url']}**")
                    if w.get("business_description"):
                        st.caption(w["business_description"])
                with col2:
                    tags = []
                    if w.get("country"):
                        tags.append(w["country"])
                    if w.get("language"):
                        tags.append(w["language"])
                    st.caption(" · ".join(tags) if tags else "-")
                with col3:
                    is_active = st.session_state.get("active_website_id") == w["id"]
                    if is_active:
                        st.markdown(badge_span("✓ Active", COLOR_TEAL), unsafe_allow_html=True)
                    else:
                        if st.button("Set Active", key=f"set_active_{w['id']}", use_container_width=True):
                            st.session_state["active_website_id"] = w["id"]
                            st.rerun()
    else:
        st.info("No projects yet. Create one above.")

# ==========================================================
# PAGE: TECHNICAL SEO AUDIT
# ==========================================================
elif nav_selection == "Technical SEO Audit":

    st.caption("Phase 2 — Website Crawler & Technical SEO Audit")

    selected_id = project_dropdown("audit", websites)

    if not selected_id:
        st.warning("No projects found. Please create a project first on the 'Project Setup' page.")
    else:
        col1, col2 = st.columns([1, 3])
        with col1:
            max_pages = st.number_input(
                "Max pages to crawl", min_value=1, value=10, step=1,
                help="Type any number - if the site has fewer pages than this, you'll be told exactly how many exist.",
            )
        with col2:
            st.write("")
            st.write("")
            run_audit = st.button("Run Crawl & Audit", use_container_width=True)

        if run_audit:
            with st.spinner("Crawling website and running SEO checks... this may take a while for larger limits."):
                try:
                    res = requests.post(
                        f"{BACKEND_URL}/websites/{selected_id}/crawl",
                        json={"max_pages": int(max_pages)},
                        timeout=1800,
                    )
                    if res.status_code == 200:
                        st.session_state["audit_result"] = res.json()
                        st.success("Audit completed!")
                    else:
                        st.error(f"Audit failed: {res.text}")
                except Exception as e:
                    st.error(f"Could not reach backend: {e}")

        if "audit_result" in st.session_state and st.session_state["audit_result"].get("website_id") == selected_id:
            summary = st.session_state["audit_result"]

            st.divider()

            if summary.get("crawl_note"):
                if summary.get("pages_crawled", 0) == 0:
                    st.error(summary["crawl_note"])
                elif summary.get("fully_crawled", True):
                    st.success(summary["crawl_note"], icon="✅")
                else:
                    st.warning(summary["crawl_note"], icon="⚠️")

            if summary.get("pages_crawled", 0) > 0:
                st.subheader("Audit Summary")

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("SEO Score", f"{summary['score']} / 100")
                m2.metric("Pages Crawled", summary["pages_crawled"])
                m3.metric("Total Issues", summary["total_issues"])
                severity_counts = summary["issues_by_severity"]
                m4.metric("Critical Issues", severity_counts.get("critical", 0))

                st.caption(summary["explanation"])

                crawlability = summary.get("crawlability")
                if crawlability:
                    st.markdown("##### Crawlability")
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        robots_status = "Found" if crawlability.get("robots_txt_found") else "Not found"
                        st.markdown(
                            f"**robots.txt:** " + badge_span(robots_status, COLOR_TEAL if crawlability.get("robots_txt_found") else COLOR_RED),
                            unsafe_allow_html=True,
                        )
                    with cc2:
                        sitemap_status = "Found" if crawlability.get("sitemap_found") else "Not found"
                        st.markdown(
                            f"**XML Sitemap:** " + badge_span(sitemap_status, COLOR_TEAL if crawlability.get("sitemap_found") else COLOR_RED),
                            unsafe_allow_html=True,
                        )
                        if crawlability.get("sitemap_url"):
                            st.caption(crawlability["sitemap_url"])

                st.divider()

                st.subheader("Crawled Pages")
                pages = api_get(f"/websites/{selected_id}/pages")
                if pages:
                    page_rows = []
                    for p in pages:
                        page_rows.append({
                            "url": p["url"],
                            "status_code": p["status_code"],
                            "title": p["title"] or "(missing)",
                            "word_count": p["word_count"],
                            "h1_count": p["h1_count"],
                            "mobile_friendly": "yes" if p.get("has_viewport_meta") else "no",
                            "author_detected": "yes" if p.get("author_detected") else "no",
                            "has_schema": "yes" if p["has_schema"] else "no",
                        })
                    render_styled_table(
                        page_rows,
                        [
                            ("url", "URL"), ("status_code", "Status"), ("title", "Title"),
                            ("word_count", "Words"), ("h1_count", "H1s"),
                            ("mobile_friendly", "Mobile OK"), ("author_detected", "Author Info"),
                            ("has_schema", "Schema"),
                        ],
                        badge_columns={"status_code": "status_code", "mobile_friendly": YES_NO_COLORS, "author_detected": YES_NO_COLORS, "has_schema": YES_NO_COLORS},
                    )
                else:
                    st.info("No pages found.")

                st.subheader("SEO Issues")
                issues = api_get(f"/websites/{selected_id}/issues")
                if issues:
                    severity_filter = st.multiselect(
                        "Filter by severity",
                        options=["critical", "high", "medium", "low"],
                        default=["critical", "high", "medium", "low"],
                    )
                    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
                    filtered = [i for i in issues if i["severity"] in severity_filter]
                    filtered.sort(key=lambda i: severity_order.get(i["severity"], 4))

                    issue_rows = [
                        {
                            "severity": i["severity"],
                            "issue_type": i["issue_type"],
                            "page_url": i["page_url"] or "(site-wide)",
                            "message": i["message"],
                            "recommendation": i["recommendation"],
                        }
                        for i in filtered
                    ]
                    render_styled_table(
                        issue_rows,
                        [
                            ("severity", "Severity"), ("issue_type", "Type"), ("page_url", "Page"),
                            ("message", "Message"), ("recommendation", "Recommendation"),
                        ],
                        badge_columns={"severity": SEVERITY_COLORS},
                    )
                else:
                    st.info("No issues found. Great job!")
        else:
            st.info("Run a crawl & audit above to see results for this project.")

# ==========================================================
# PAGE: KEYWORD RESEARCH
# ==========================================================
elif nav_selection == "Keyword Research":

    st.caption("Phase 3 — AI Keyword Research Agent")

    selected_id = project_dropdown("keywords", websites)

    st.info(
        "⚠️ These keywords are AI-suggested based on your business context. "
        "They are NOT real search volume, difficulty, or ranking data. "
        "Connect a real SERP/keyword API later for verified metrics.",
        icon="ℹ️",
    )

    if not selected_id:
        st.warning("No projects found. Please create a project first on the 'Project Setup' page.")
    else:
        col1, col2, col3 = st.columns([2.5, 1.5, 1])
        with col1:
            seed_keyword = st.text_input("Seed Keyword", placeholder="e.g. AI course, medical billing software")
        with col2:
            keyword_type_label = st.selectbox(
                "Keyword Type",
                ["Both (short + long-tail)", "Short-tail (1-2 words)", "Long-tail (4+ words)"],
            )
        with col3:
            st.write("")
            st.write("")
            run_research = st.button("Research Keywords", use_container_width=True)

        keyword_type_map = {
            "Both (short + long-tail)": "both",
            "Short-tail (1-2 words)": "short_tail",
            "Long-tail (4+ words)": "long_tail",
        }

        if run_research:
            if not seed_keyword:
                st.warning("Please enter a seed keyword.")
            else:
                with st.spinner("Generating keyword ideas with AI..."):
                    try:
                        res = requests.post(
                            f"{BACKEND_URL}/websites/{selected_id}/keywords/research",
                            json={
                                "seed_keyword": seed_keyword,
                                "keyword_type": keyword_type_map[keyword_type_label],
                            },
                            timeout=60,
                        )
                        if res.status_code == 200:
                            st.success("Keyword research completed!")
                        else:
                            st.error(f"Failed: {res.text}")
                    except Exception as e:
                        st.error(f"Could not reach backend: {e}")

        st.divider()
        st.subheader("Keyword Ideas")

        col_a, col_b = st.columns([4, 1])
        with col_b:
            if st.button("Clear All Keywords", use_container_width=True):
                try:
                    requests.delete(f"{BACKEND_URL}/websites/{selected_id}/keywords", timeout=10)
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not clear keywords: {e}")

        keywords = api_get(f"/websites/{selected_id}/keywords")
        if keywords:
            df_kw = pd.DataFrame(keywords)
            cluster_options = sorted(df_kw["cluster"].dropna().unique().tolist())
            cluster_filter = st.multiselect("Filter by cluster", options=cluster_options, default=cluster_options)
            filtered_kw = [k for k in keywords if k.get("cluster") in cluster_filter]

            kw_rows = [
                {"keyword": k["keyword"], "intent": k["intent"], "cluster": k["cluster"], "reason": k["reason"]}
                for k in filtered_kw
            ]
            render_styled_table(
                kw_rows,
                [("keyword", "Keyword"), ("intent", "Intent"), ("cluster", "Cluster"), ("reason", "Reason")],
                badge_columns={"intent": INTENT_COLORS},
            )
        else:
            st.info("No keywords yet. Enter a seed keyword above and click 'Research Keywords'.")

        st.divider()
        st.subheader("SERP Provider Status")
        with st.container(border=True):
            st.warning(
                "SERP provider not configured. Real ranking data requires a paid API "
                "(e.g. SerpApi, DataForSEO). Currently running in mock/demo mode.",
                icon="⚠️",
            )

# ==========================================================
# PAGE: COMPETITORS & CONTENT GAPS
# ==========================================================
elif nav_selection == "Competitors & Content Gaps":

    st.caption("Phase 4 — Competitor Analysis & Content Gap Agent")

    selected_id = project_dropdown("competitors", websites)

    if not selected_id:
        st.warning("No projects found. Please create a project first on the 'Project Setup' page.")
    else:
        st.subheader("Add a Competitor")
        st.caption("We will crawl a few pages of the competitor's site to understand their topic coverage.")

        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                competitor_url = st.text_input("Competitor Website URL", placeholder="https://competitor.com")
            with col2:
                st.write("")
                st.write("")
                add_competitor_btn = st.button("Add & Analyze", use_container_width=True)

            if add_competitor_btn:
                if not competitor_url:
                    st.warning("Please enter a competitor URL.")
                else:
                    with st.spinner("Crawling competitor website... this may take a minute."):
                        try:
                            res = requests.post(
                                f"{BACKEND_URL}/websites/{selected_id}/competitors",
                                json={"competitor_url": competitor_url},
                                timeout=120,
                            )
                            if res.status_code == 200:
                                st.success("Competitor added and analyzed!")
                                st.rerun()
                            else:
                                st.error(f"Failed: {res.text}")
                        except Exception as e:
                            st.error(f"Could not reach backend: {e}")

        st.divider()
        st.subheader("Your Competitors")

        competitors = api_get(f"/websites/{selected_id}/competitors")
        if competitors:
            for comp in competitors:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    col1.markdown(f"**{comp['competitor_url']}**")
                    col2.write(f"{comp['pages_analyzed']} pages analyzed")
                    if col3.button("Remove", key=f"remove_{comp['id']}"):
                        try:
                            requests.delete(
                                f"{BACKEND_URL}/websites/{selected_id}/competitors/{comp['id']}", timeout=10,
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(f"Could not remove competitor: {e}")
        else:
            st.info("No competitors added yet. Add one above.")

        st.divider()
        st.subheader("Content Gap Analysis")
        st.caption(
            "Compares your crawled pages, your researched keywords, and your competitors' pages "
            "to find topics you might be missing."
        )

        run_gap_analysis = st.button("Run Content Gap Analysis", use_container_width=True)

        if run_gap_analysis:
            with st.spinner("Analyzing content gaps with AI..."):
                try:
                    res = requests.post(f"{BACKEND_URL}/websites/{selected_id}/content-gaps/analyze", timeout=60)
                    if res.status_code == 200:
                        st.success("Content gap analysis completed!")
                    else:
                        st.error(f"Failed: {res.json().get('detail', res.text)}")
                except Exception as e:
                    st.error(f"Could not reach backend: {e}")

        st.subheader("Content Gap Opportunities")
        gaps = api_get(f"/websites/{selected_id}/content-gaps")
        if gaps:
            priority_filter = st.multiselect(
                "Filter by priority", options=["high", "medium", "low"], default=["high", "medium", "low"]
            )
            priority_order = {"high": 0, "medium": 1, "low": 2}
            filtered_gaps = [g for g in gaps if g.get("priority") in priority_filter]
            filtered_gaps.sort(key=lambda g: priority_order.get(g.get("priority"), 3))

            gap_rows = [
                {
                    "priority": g["priority"], "opportunity": g["opportunity"], "gap_type": g["gap_type"],
                    "suggested_page": g["suggested_page"], "reason": g["reason"],
                }
                for g in filtered_gaps
            ]
            render_styled_table(
                gap_rows,
                [
                    ("priority", "Priority"), ("opportunity", "Opportunity"), ("gap_type", "Type"),
                    ("suggested_page", "Suggested Page"), ("reason", "Reason"),
                ],
                badge_columns={"priority": PRIORITY_COLORS, "gap_type": GAP_TYPE_COLORS},
            )
        else:
            st.info("No content gaps yet. Add competitors and run the analysis above.")

# ==========================================================
# PAGE: CONTENT BRIEFS & OPTIMIZER
# ==========================================================
elif nav_selection == "Content Briefs & Optimizer":

    st.caption("Phase 5 — Content Brief Generator & Content Optimizer")

    selected_id = project_dropdown("content", websites)

    if not selected_id:
        st.warning("No projects found. Please create a project first on the 'Project Setup' page.")
    else:
        tab1, tab2 = st.tabs(["📝 Content Brief Generator", "🔧 Content Optimizer"])

        with tab1:
            st.subheader("Generate a Content Brief")

            gaps = api_get(f"/websites/{selected_id}/content-gaps")

            with st.container(border=True):
                use_gap = st.checkbox("Use an existing Content Gap opportunity as the topic")

                topic = ""
                if use_gap and gaps:
                    gap_options = {f"{g['opportunity']} ({g['priority']} priority)": g for g in gaps}
                    selected_gap_label = st.selectbox("Select Opportunity", list(gap_options.keys()))
                    topic = gap_options[selected_gap_label]["opportunity"]
                    st.caption(f"Reason: {gap_options[selected_gap_label]['reason']}")
                else:
                    topic = st.text_input("Topic", placeholder="e.g. Medical Billing Software Comparison Guide")

                generate_brief_btn = st.button("Generate Content Brief", use_container_width=True)

                if generate_brief_btn:
                    if not topic:
                        st.warning("Please provide a topic.")
                    else:
                        with st.spinner("Generating content brief with AI..."):
                            try:
                                res = requests.post(
                                    f"{BACKEND_URL}/websites/{selected_id}/content-briefs/generate",
                                    json={"topic": topic},
                                    timeout=60,
                                )
                                if res.status_code == 200:
                                    st.success("Content brief generated!")
                                    st.rerun()
                                else:
                                    st.error(f"Failed: {res.json().get('detail', res.text)}")
                            except Exception as e:
                                st.error(f"Could not reach backend: {e}")

            st.divider()
            st.subheader("Saved Content Briefs")

            briefs = api_get(f"/websites/{selected_id}/content-briefs")
            if briefs:
                for brief in briefs:
                    with st.expander(f"📄 {brief['topic']} — {brief['suggested_title'] or 'No title'}"):
                        try:
                            data = json.loads(brief["brief_json"]) if brief["brief_json"] else {}
                        except json.JSONDecodeError:
                            data = {}

                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Primary Keyword:** {data.get('primary_keyword', '-')}")
                            st.markdown(f"**Search Intent:** {data.get('search_intent', '-')}")
                            st.markdown(f"**Target Audience:** {data.get('target_audience', '-')}")
                            st.markdown(f"**Suggested Title:** {data.get('suggested_title', '-')}")
                            st.markdown(f"**H1:** {data.get('h1', '-')}")
                        with col2:
                            secondary = data.get("secondary_keywords", [])
                            st.markdown("**Secondary Keywords:**")
                            st.write(", ".join(secondary) if secondary else "-")
                            st.markdown(f"**Suggested CTA:** {data.get('suggested_cta', '-')}")

                        st.markdown("**H2s:**")
                        for h2 in data.get("h2s", []):
                            st.write(f"- {h2}")

                        st.markdown("**H3s:**")
                        for h3 in data.get("h3s", []):
                            st.write(f"- {h3}")

                        st.markdown("**Questions to Answer:**")
                        for q in data.get("questions_to_answer", []):
                            st.write(f"- {q}")

                        st.markdown("**Topics to Cover:**")
                        for t in data.get("topics_to_cover", []):
                            st.write(f"- {t}")

                        st.markdown("**FAQ Opportunities:**")
                        for faq in data.get("faq_opportunities", []):
                            st.write(f"- {faq}")

                        st.markdown("**Internal Linking Opportunities:**")
                        for link in data.get("internal_linking_opportunities", []):
                            st.write(f"- {link}")

                        st.markdown("**External Reference Opportunities:**")
                        for ext in data.get("external_reference_opportunities", []):
                            st.write(f"- {ext}")

                        st.markdown(
                            f"**Content Requirements (needs human verification):** "
                            f"{data.get('content_requirements', '-')}"
                        )

                        if st.button("Delete Brief", key=f"del_brief_{brief['id']}"):
                            try:
                                requests.delete(
                                    f"{BACKEND_URL}/websites/{selected_id}/content-briefs/{brief['id']}", timeout=10,
                                )
                                st.rerun()
                            except Exception as e:
                                st.error(f"Could not delete brief: {e}")
            else:
                st.info("No content briefs yet. Generate one above.")

        with tab2:
            st.subheader("Optimize Existing Content")
            st.caption(
                "Select a page you already crawled (Technical SEO Audit page), "
                "optionally paste its article text for deeper analysis."
            )

            pages = api_get(f"/websites/{selected_id}/pages")

            if not pages:
                st.warning("No crawled pages found. Please run a Technical SEO Audit first.")
            else:
                with st.container(border=True):
                    page_options = {f"{p['url']}": p for p in pages}
                    selected_page_label = st.selectbox("Select Page to Optimize", list(page_options.keys()))
                    selected_page = page_options[selected_page_label]

                    col1, col2 = st.columns(2)
                    col1.markdown(f"**Current Title:** {selected_page['title'] or '(missing)'}")
                    col1.markdown(f"**Current Word Count:** {selected_page['word_count']}")
                    col2.markdown(f"**Current Meta Description:** {selected_page['meta_description'] or '(missing)'}")
                    col2.markdown(f"**Current H1:** {selected_page['h1_text'] or '(missing)'}")
                    st.caption(f"Author/byline detected on this page: {'Yes' if selected_page.get('author_detected') else 'No'}")

                    target_keywords_input = st.text_input(
                        "Target keywords for this page (comma-separated, optional)",
                        placeholder="e.g. medical billing software, healthcare billing automation",
                    )

                    article_text = st.text_area(
                        "Paste article content (optional, improves analysis quality)",
                        placeholder="Paste the page's main content here for deeper analysis...",
                        height=150,
                    )

                    optimize_btn = st.button("Analyze & Optimize", use_container_width=True)

                    if optimize_btn:
                        with st.spinner("Analyzing content with AI..."):
                            try:
                                target_keywords_list = (
                                    [k.strip() for k in target_keywords_input.split(",") if k.strip()]
                                    if target_keywords_input else None
                                )
                                res = requests.post(
                                    f"{BACKEND_URL}/websites/{selected_id}/content-optimizer/analyze",
                                    json={
                                        "page_id": selected_page["id"],
                                        "article_text": article_text,
                                        "target_keywords": target_keywords_list,
                                    },
                                    timeout=60,
                                )
                                if res.status_code == 200:
                                    st.session_state["optimize_result"] = res.json()
                                    st.session_state["optimize_result_page_url"] = selected_page["url"]
                                    st.success("Analysis completed!")
                                else:
                                    st.error(f"Failed: {res.json().get('detail', res.text)}")
                            except Exception as e:
                                st.error(f"Could not reach backend: {e}")

                if "optimize_result" in st.session_state:
                    result = st.session_state["optimize_result"]

                    st.divider()
                    st.subheader("Analysis Results")

                    st.markdown("### Current State")
                    st.write(result.get("current_state_summary", "-"))

                    if result.get("keyword_intent_alignment"):
                        st.markdown("### Keyword Intent Alignment")
                        st.write(result["keyword_intent_alignment"])

                    st.markdown("### Problems Found")
                    for problem in result.get("problems", []):
                        st.write(f"🔴 {problem}")

                    st.markdown("### Why This Matters")
                    for reason in result.get("why_it_matters", []):
                        st.write(f"💡 {reason}")

                    st.markdown("### Recommendations")
                    for rec in result.get("recommendations", []):
                        st.write(f"✅ {rec}")

                    if result.get("eeat_signals_present") or result.get("eeat_signals_missing"):
                        st.divider()
                        st.markdown("### E-E-A-T Review")
                        eeat_col1, eeat_col2 = st.columns(2)
                        with eeat_col1:
                            st.markdown("**✅ Signals Present:**")
                            for sig in result.get("eeat_signals_present", []):
                                st.write(f"- {sig}")
                            if not result.get("eeat_signals_present"):
                                st.caption("None detected.")
                        with eeat_col2:
                            st.markdown("**⚠️ Signals Missing:**")
                            for sig in result.get("eeat_signals_missing", []):
                                st.write(f"- {sig}")
                            if not result.get("eeat_signals_missing"):
                                st.caption("None flagged.")

                    st.divider()
                    st.markdown("### Optimized Metadata")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_area("Optimized Title", value=result.get("optimized_title", ""), height=70)
                        st.text_area("Optimized H1", value=result.get("optimized_h1", ""), height=70)
                    with col2:
                        st.text_area(
                            "Optimized Meta Description",
                            value=result.get("optimized_meta_description", ""),
                            height=140,
                        )

                    if result.get("notes"):
                        st.info(result["notes"], icon="📌")

                    st.caption(
                        "💡 To push this optimized title/meta description/H1 to WordPress, "
                        "go to 'WordPress Publishing' → 'On-Page Meta Update' tab."
                    )

# ==========================================================
# PAGE: ORCHESTRATOR & APPROVAL
# ==========================================================
elif nav_selection == "Orchestrator & Approval":

    st.caption("Phase 6 — Orchestrator Agent & Human Approval")

    selected_id = project_dropdown("orchestrator", websites)

    if not selected_id:
        st.warning("No projects found. Please create a project first on the 'Project Setup' page.")
    else:
        st.subheader("Start a New Orchestrator Run")
        st.caption(
            "Describe your goal in plain language. The Orchestrator will decide which agents to run, "
            "run them in order, and give you a final strategy to review before anything is acted on. "
            "Note: the Orchestrator never publishes to WordPress and never runs monitoring/PageSpeed "
            "checks - all of those always require a separate manual step."
        )

        with st.container(border=True):
            goal_text = st.text_area(
                "What do you want the Orchestrator to do?",
                placeholder="e.g. Research keywords for our medical billing software page and find content gaps against competitor.com",
                height=100,
            )
            max_pages_orch = st.number_input(
                "Max pages to crawl (only used if a technical audit is needed)",
                min_value=1, value=10, step=1, key="orch_max_pages",
            )
            run_orchestrator_btn = st.button("Run Orchestrator", use_container_width=True)

            if run_orchestrator_btn:
                if not goal_text:
                    st.warning("Please describe your goal.")
                else:
                    with st.spinner("Orchestrator is planning and running agents... this may take a few minutes."):
                        try:
                            res = requests.post(
                                f"{BACKEND_URL}/websites/{selected_id}/orchestrator/runs",
                                json={"goal": goal_text, "max_pages": int(max_pages_orch)},
                                timeout=1800,
                            )
                            if res.status_code == 200:
                                st.session_state["active_run_id"] = res.json()["id"]
                                st.success("Orchestrator run completed! Review it below.")
                                st.rerun()
                            else:
                                st.error(f"Failed: {res.text}")
                        except Exception as e:
                            st.error(f"Could not reach backend: {e}")

        st.divider()
        st.subheader("Past Runs")

        runs = api_get(f"/websites/{selected_id}/orchestrator/runs")

        if runs:
            for run in runs:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([4, 1.3, 1.3])
                    with col1:
                        goal_preview = run["goal"] if len(run["goal"]) <= 80 else run["goal"][:80] + "..."
                        st.markdown(f"**{goal_preview}**")
                        st.caption(f"Run #{run['id']} · {run['created_at'][:16].replace('T', ' ')}")
                    with col2:
                        st.markdown(
                            badge_span(run["status"].replace("_", " "), RUN_STATUS_COLORS.get(run["status"], COLOR_GRAY)),
                            unsafe_allow_html=True,
                        )
                    with col3:
                        if st.button("View", key=f"view_run_{run['id']}", use_container_width=True):
                            st.session_state["active_run_id"] = run["id"]
                            st.rerun()
        else:
            st.info("No orchestrator runs yet. Start one above.")

        st.divider()

        active_run_id = st.session_state.get("active_run_id")
        if active_run_id:
            run_detail = api_get(f"/orchestrator/runs/{active_run_id}")
            if not run_detail:
                st.warning("Could not load this run.")
            else:
                st.subheader(f"Run #{run_detail['id']} Details")
                st.markdown(f"**Goal:** {run_detail['goal']}")
                st.markdown(
                    badge_span(
                        run_detail["status"].replace("_", " "),
                        RUN_STATUS_COLORS.get(run_detail["status"], COLOR_GRAY),
                    ),
                    unsafe_allow_html=True,
                )

                if run_detail.get("error_message"):
                    st.error(run_detail["error_message"])

                st.markdown("##### Execution Steps")
                steps = run_detail.get("steps", [])
                if steps:
                    step_rows = [
                        {
                            "step_number": s["step_number"],
                            "tool_name": s["tool_name"],
                            "purpose": s["purpose"],
                            "status": s["status"],
                        }
                        for s in steps
                    ]
                    render_styled_table(
                        step_rows,
                        [("step_number", "#"), ("tool_name", "Tool"), ("purpose", "Purpose"), ("status", "Status")],
                        badge_columns={"status": STEP_STATUS_COLORS},
                    )
                    for s in steps:
                        if s["status"] == "failed" and s.get("error_message"):
                            st.caption(f"⚠️ Step {s['step_number']} ({s['tool_name']}) error: {s['error_message']}")
                else:
                    st.caption("No steps recorded for this run.")

                if run_detail["status"] == "failed":
                    if st.button("Resume This Run", use_container_width=True):
                        with st.spinner("Resuming orchestrator run..."):
                            try:
                                res = requests.post(
                                    f"{BACKEND_URL}/orchestrator/runs/{active_run_id}/resume", timeout=1800,
                                )
                                if res.status_code == 200:
                                    st.success("Run resumed!")
                                    st.rerun()
                                else:
                                    st.error(f"Failed: {res.text}")
                            except Exception as e:
                                st.error(f"Could not reach backend: {e}")

                if run_detail.get("final_strategy_json"):
                    st.markdown("##### Final Strategy (Orchestrator Recommendation)")
                    try:
                        strategy = json.loads(run_detail["final_strategy_json"])
                    except json.JSONDecodeError:
                        strategy = {}

                    st.write(strategy.get("summary", "-"))

                    st.markdown("**Key Findings:**")
                    for f in strategy.get("key_findings", []):
                        st.write(f"- {f}")

                    st.markdown("**Recommended Actions:**")
                    for a in strategy.get("recommended_actions", []):
                        st.write(f"- {a}")

                    st.markdown("**Risks / Gaps:**")
                    for r in strategy.get("risks_or_gaps", []):
                        st.write(f"- {r}")

                    st.markdown("**Next Steps Needing Human Input:**")
                    for n in strategy.get("next_steps_needing_human_input", []):
                        st.write(f"- {n}")

                    if run_detail["status"] == "awaiting_approval":
                        st.divider()
                        st.markdown("##### Human Approval")
                        st.caption(
                            "Approving this only marks the strategy as reviewed and accepted. "
                            "To actually publish anything, go to 'WordPress Publishing' afterward."
                        )

                        approval_action = st.radio(
                            "Your decision", ["Approve as-is", "Edit & Approve", "Reject"],
                            key=f"approval_choice_{active_run_id}",
                        )

                        edited_text = ""
                        if approval_action == "Edit & Approve":
                            edited_text = st.text_area(
                                "Edit the strategy text before approving",
                                value=json.dumps(strategy, indent=2),
                                height=200,
                            )

                        approval_notes = st.text_input("Notes (optional)", key=f"approval_notes_{active_run_id}")

                        if st.button("Submit Decision", use_container_width=True):
                            action_map = {"Approve as-is": "approve", "Edit & Approve": "edit", "Reject": "reject"}
                            payload = {
                                "action": action_map[approval_action],
                                "approval_notes": approval_notes or None,
                            }
                            if approval_action == "Edit & Approve":
                                payload["edited_strategy_text"] = edited_text
                            try:
                                res = requests.post(
                                    f"{BACKEND_URL}/orchestrator/runs/{active_run_id}/approval",
                                    json=payload, timeout=15,
                                )
                                if res.status_code == 200:
                                    st.success("Decision submitted!")
                                    st.rerun()
                                else:
                                    st.error(f"Failed: {res.text}")
                            except Exception as e:
                                st.error(f"Could not reach backend: {e}")

                    elif run_detail["approval_status"] in ("approved", "edited"):
                        st.success(f"✅ This strategy was {run_detail['approval_status']}.", icon="✅")
                        if run_detail.get("approved_strategy_text"):
                            with st.expander("View edited strategy text"):
                                st.text(run_detail["approved_strategy_text"])

                    elif run_detail["approval_status"] == "rejected":
                        st.error("❌ This strategy was rejected.")

# ==========================================================
# PAGE: LINKING, SCHEMA & AEO/GEO
# ==========================================================
elif nav_selection == "Linking, Schema & AEO/GEO":

    st.caption("Phase 7 — Internal Linking, Schema/JSON-LD & AEO/GEO Agents")

    selected_id = project_dropdown("linking_schema_aeo", websites)

    if not selected_id:
        st.warning("No projects found. Please create a project first on the 'Project Setup' page.")
    else:
        pages = api_get(f"/websites/{selected_id}/pages")

        tab1, tab2, tab3 = st.tabs(["🔗 Internal Linking", "🏷️ Schema / JSON-LD", "🌐 AEO/GEO"])

        # ---------------- TAB 1: INTERNAL LINKING ----------------
        with tab1:
            st.subheader("Internal Linking Suggestions")
            st.caption(
                "Suggests links BETWEEN pages you've already crawled. This agent never invents "
                "new pages, and nothing is auto-applied to your site - these are recommendations only."
            )

            if not pages or len(pages) < 2:
                st.warning("Need at least 2 crawled pages. Please run a Technical SEO Audit with more pages first.")
            else:
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.write("")
                with col_b:
                    run_linking_btn = st.button("Run Internal Linking Analysis", use_container_width=True)

                if run_linking_btn:
                    with st.spinner("Analyzing internal linking opportunities with AI..."):
                        try:
                            res = requests.post(
                                f"{BACKEND_URL}/websites/{selected_id}/internal-linking/analyze", timeout=60,
                            )
                            if res.status_code == 200:
                                st.success("Internal linking analysis completed!")
                                st.rerun()
                            else:
                                st.error(f"Failed: {res.json().get('detail', res.text)}")
                        except Exception as e:
                            st.error(f"Could not reach backend: {e}")

                st.divider()

                col_c, col_d = st.columns([4, 1])
                with col_d:
                    if st.button("Clear Suggestions", use_container_width=True, key="clear_linking"):
                        try:
                            requests.delete(f"{BACKEND_URL}/websites/{selected_id}/internal-linking", timeout=10)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Could not clear suggestions: {e}")

                suggestions = api_get(f"/websites/{selected_id}/internal-linking")
                if suggestions:
                    suggestion_rows = [
                        {
                            "source_page_url": s["source_page_url"],
                            "target_page_url": s["target_page_url"],
                            "anchor_text": s["anchor_text"],
                            "reason": s["reason"],
                        }
                        for s in suggestions
                    ]
                    render_styled_table(
                        suggestion_rows,
                        [
                            ("source_page_url", "Add Link On"), ("target_page_url", "Link To"),
                            ("anchor_text", "Suggested Anchor Text"), ("reason", "Reason"),
                        ],
                    )
                else:
                    st.info("No internal linking suggestions yet. Run the analysis above.")

        # ---------------- TAB 2: SCHEMA / JSON-LD ----------------
        with tab2:
            st.subheader("Schema / JSON-LD Markup Suggestions")
            st.caption(
                "Generates structured data (JSON-LD) suggestions for a page, chosen only from a "
                "curated set of schema types: Organization, WebSite, Article, BlogPosting, FAQPage, "
                "BreadcrumbList, Product, LocalBusiness, HowTo."
            )

            if not pages:
                st.warning("No crawled pages found. Please run a Technical SEO Audit first.")
            else:
                with st.container(border=True):
                    page_options_schema = {f"{p['url']}": p for p in pages}
                    selected_page_label_schema = st.selectbox(
                        "Select Page", list(page_options_schema.keys()), key="schema_page_select",
                    )
                    selected_page_schema = page_options_schema[selected_page_label_schema]

                    generate_schema_btn = st.button("Generate Schema Suggestions", use_container_width=True)

                    if generate_schema_btn:
                        with st.spinner("Generating schema markup with AI..."):
                            try:
                                res = requests.post(
                                    f"{BACKEND_URL}/websites/{selected_id}/schema/generate",
                                    json={"page_id": selected_page_schema["id"]},
                                    timeout=60,
                                )
                                if res.status_code == 200:
                                    st.success("Schema markup generated!")
                                    st.rerun()
                                else:
                                    st.error(f"Failed: {res.json().get('detail', res.text)}")
                            except Exception as e:
                                st.error(f"Could not reach backend: {e}")

                st.divider()
                st.subheader("Saved Schema Markups")

                schema_markups = api_get(f"/websites/{selected_id}/schema")
                if schema_markups:
                    for markup in schema_markups:
                        with st.expander(f"🏷️ {markup['schema_type']} — {markup['page_url']}"):
                            try:
                                json_ld_data = json.loads(markup["schema_json"]) if markup["schema_json"] else {}
                            except json.JSONDecodeError:
                                json_ld_data = {}

                            if markup.get("notes"):
                                st.caption(f"📌 {markup['notes']}")

                            st.code(json.dumps(json_ld_data, indent=2), language="json")

                            if st.button("Delete", key=f"del_schema_{markup['id']}"):
                                try:
                                    requests.delete(
                                        f"{BACKEND_URL}/websites/{selected_id}/schema/{markup['id']}", timeout=10,
                                    )
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Could not delete: {e}")
                    st.caption("💡 To push this schema to WordPress, go to 'WordPress Publishing' → 'Schema Injection' tab.")
                else:
                    st.info("No schema markups yet. Select a page above and generate one.")

        # ---------------- TAB 3: AEO/GEO ----------------
        with tab3:
            st.subheader("AEO/GEO Suggestions")
            st.caption(
                "Answer Engine Optimization / Generative Engine Optimization: FAQ items, a concise "
                "answer block, and structure tips to help AI search engines (ChatGPT, Perplexity, "
                "Google AI Overviews) cite this page correctly."
            )

            if not pages:
                st.warning("No crawled pages found. Please run a Technical SEO Audit first.")
            else:
                with st.container(border=True):
                    page_options_aeo = {f"{p['url']}": p for p in pages}
                    selected_page_label_aeo = st.selectbox(
                        "Select Page", list(page_options_aeo.keys()), key="aeo_page_select",
                    )
                    selected_page_aeo = page_options_aeo[selected_page_label_aeo]

                    generate_aeo_btn = st.button("Generate AEO/GEO Suggestions", use_container_width=True)

                    if generate_aeo_btn:
                        with st.spinner("Generating AEO/GEO suggestions with AI..."):
                            try:
                                res = requests.post(
                                    f"{BACKEND_URL}/websites/{selected_id}/aeo-geo/generate",
                                    json={"page_id": selected_page_aeo["id"]},
                                    timeout=60,
                                )
                                if res.status_code == 200:
                                    st.success("AEO/GEO suggestions generated!")
                                    st.rerun()
                                else:
                                    st.error(f"Failed: {res.json().get('detail', res.text)}")
                            except Exception as e:
                                st.error(f"Could not reach backend: {e}")

                st.divider()
                st.subheader("Saved AEO/GEO Suggestions")

                aeo_suggestions = api_get(f"/websites/{selected_id}/aeo-geo")
                if aeo_suggestions:
                    for suggestion in aeo_suggestions:
                        with st.expander(f"🌐 {suggestion['page_url']}"):
                            try:
                                data = json.loads(suggestion["suggestion_json"]) if suggestion["suggestion_json"] else {}
                            except json.JSONDecodeError:
                                data = {}

                            st.markdown("**Concise Answer Block:**")
                            st.write(data.get("concise_answer_block", "-"))

                            st.markdown("**FAQ Items:**")
                            for faq in data.get("faq_items", []):
                                st.markdown(f"**Q: {faq.get('question', '-')}**")
                                st.write(f"A: {faq.get('answer', '-')}")

                            st.markdown("**Structure Suggestions:**")
                            for tip in data.get("structure_suggestions", []):
                                st.write(f"- {tip}")

                            if st.button("Delete", key=f"del_aeo_{suggestion['id']}"):
                                try:
                                    requests.delete(
                                        f"{BACKEND_URL}/websites/{selected_id}/aeo-geo/{suggestion['id']}", timeout=10,
                                    )
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Could not delete: {e}")
                else:
                    st.info("No AEO/GEO suggestions yet. Select a page above and generate one.")

# ==========================================================
# PAGE: SEO SIGNALS & SPEED
# ==========================================================
elif nav_selection == "SEO Signals & Speed":

    st.caption("Page Speed, Backlinks & User Signals")

    selected_id = project_dropdown("signals", websites)

    if not selected_id:
        st.warning("No projects found. Please create a project first on the 'Project Setup' page.")
    else:
        tab1, tab2, tab3 = st.tabs(["⚡ Page Speed", "🔗 Backlinks", "👥 User Signals"])

        # ---------------- TAB 1: PAGE SPEED ----------------
        with tab1:
            st.subheader("Page Speed & Mobile Friendliness (Google PageSpeed Insights)")
            st.caption(
                "Uses the real Google PageSpeed Insights API (Lighthouse scores). If no API key is "
                "configured, this will clearly say so instead of showing a fake score."
            )

            pages = api_get(f"/websites/{selected_id}/pages")
            if not pages:
                st.warning("No crawled pages found. Please run a Technical SEO Audit first.")
            else:
                col1, col2, col3 = st.columns([3, 1.5, 1])
                with col1:
                    page_options_speed = {f"{p['url']}": p for p in pages}
                    selected_page_label_speed = st.selectbox("Select Page", list(page_options_speed.keys()), key="speed_page_select")
                    selected_page_speed = page_options_speed[selected_page_label_speed]
                with col2:
                    strategy = st.selectbox("Device", ["mobile", "desktop"], key="speed_strategy")
                with col3:
                    st.write("")
                    st.write("")
                    run_speed_btn = st.button("Check Speed", use_container_width=True)

                if run_speed_btn:
                    with st.spinner("Running PageSpeed Insights check (this can take 20-30 seconds)..."):
                        try:
                            res = requests.post(
                                f"{BACKEND_URL}/websites/{selected_id}/pagespeed/check",
                                json={"page_id": selected_page_speed["id"], "strategy": strategy},
                                timeout=90,
                            )
                            if res.status_code == 200:
                                check_result = res.json()
                                if not check_result.get("configured"):
                                    st.warning(check_result.get("message"), icon="⚠️")
                                elif not check_result.get("success"):
                                    st.error(check_result.get("message"))
                                else:
                                    st.success("PageSpeed check completed!")
                                    st.rerun()
                            else:
                                st.error(f"Failed: {res.text}")
                        except Exception as e:
                            st.error(f"Could not reach backend: {e}")

            st.divider()
            st.subheader("PageSpeed Results History")

            pagespeed_results = api_get(f"/websites/{selected_id}/pagespeed")
            if pagespeed_results:
                for r in pagespeed_results[:10]:
                    with st.container(border=True):
                        st.markdown(f"**{r['page_url']}** — {r['strategy']} · {r['created_at'][:16].replace('T', ' ')}")
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Performance", f"{r['performance_score']}/100" if r['performance_score'] is not None else "-")
                        m2.metric("SEO", f"{r['seo_score']}/100" if r['seo_score'] is not None else "-")
                        m3.metric("Accessibility", f"{r['accessibility_score']}/100" if r['accessibility_score'] is not None else "-")
                        m4.metric("Best Practices", f"{r['best_practices_score']}/100" if r['best_practices_score'] is not None else "-")
                        if r.get("metrics_json"):
                            try:
                                metrics = json.loads(r["metrics_json"])
                                st.caption(
                                    f"FCP: {metrics.get('first_contentful_paint', '-')} · "
                                    f"LCP: {metrics.get('largest_contentful_paint', '-')} · "
                                    f"TBT: {metrics.get('total_blocking_time', '-')} · "
                                    f"CLS: {metrics.get('cumulative_layout_shift', '-')} · "
                                    f"Speed Index: {metrics.get('speed_index', '-')}"
                                )
                            except json.JSONDecodeError:
                                pass
            else:
                st.info("No PageSpeed checks run yet. Select a page above and click 'Check Speed'.")

        # ---------------- TAB 2: BACKLINKS ----------------
        with tab2:
            st.subheader("Backlinks")

            backlink_status = api_get(f"/websites/{selected_id}/backlinks/check")
            if backlink_status:
                st.warning(backlink_status.get("message", "Backlink data not configured."), icon="⚠️")
                st.caption(
                    "To enable this, connect a paid backlink API (Ahrefs, Moz, SEMrush, or Majestic) "
                    "and the code is ready to display real backlink counts, referring domains, and "
                    "authority scores once one is added."
                )
            else:
                st.info("Could not reach the backlink check endpoint.")

        # ---------------- TAB 3: USER SIGNALS ----------------
        with tab3:
            st.subheader("User Signals (CTR, Dwell Time, Bounce Rate)")

            pages_for_signals = api_get(f"/websites/{selected_id}/pages")
            if not pages_for_signals:
                st.warning("No crawled pages found. Please run a Technical SEO Audit first.")
            else:
                page_options_signals = {f"{p['url']}": p for p in pages_for_signals}
                selected_page_label_signals = st.selectbox("Select Page", list(page_options_signals.keys()), key="signals_page_select")
                selected_page_signals = page_options_signals[selected_page_label_signals]

                signals_result = api_get(
                    f"/websites/{selected_id}/user-signals/check?page_url={selected_page_signals['url']}"
                )
                if signals_result:
                    st.warning(signals_result.get("message", "User signals not configured."), icon="⚠️")
                    st.caption(
                        "To enable this, connect Google Search Console (for CTR/impressions) and "
                        "Google Analytics (for dwell time/bounce rate) via OAuth. The code is ready "
                        "to display real engagement metrics once these are connected."
                    )
                else:
                    st.info("Could not reach the user signals check endpoint.")

# ==========================================================
# PAGE: WORDPRESS PUBLISHING
# ==========================================================
elif nav_selection == "WordPress Publishing":

    st.caption("Phase 8 — WordPress/CMS Execution")

    selected_id = project_dropdown("wordpress", websites)

    if not selected_id:
        st.warning("No projects found. Please create a project first on the 'Project Setup' page.")
    else:
        st.subheader("WordPress Connection")

        connection = api_get(f"/websites/{selected_id}/cms/connection")

        with st.container(border=True):
            if connection:
                status_color = COLOR_TEAL if connection.get("is_connected") else COLOR_AMBER
                status_text = "Connected" if connection.get("is_connected") else "Not verified yet"
                st.markdown(
                    f"**Site:** {connection['site_url']} · **User:** {connection['wp_username']} · "
                    + badge_span(status_text, status_color),
                    unsafe_allow_html=True,
                )
                if connection.get("last_test_message"):
                    st.caption(f"Last test: {connection['last_test_message']}")

            with st.form("cms_connection_form"):
                st.write("Set up or update your WordPress connection:")
                site_url_input = st.text_input(
                    "WordPress Site URL", value=connection["site_url"] if connection else "",
                    placeholder="https://yoursite.com",
                )
                username_input = st.text_input(
                    "WordPress Username", value=connection["wp_username"] if connection else "",
                )
                app_password_input = st.text_input(
                    "Application Password", type="password",
                    placeholder="Generate this under WP Admin → Users → Profile → Application Passwords",
                )
                save_connection_btn = st.form_submit_button("Save Connection", use_container_width=True)

                if save_connection_btn:
                    if not site_url_input or not username_input or not app_password_input:
                        st.warning("All three fields are required.")
                    else:
                        try:
                            res = requests.post(
                                f"{BACKEND_URL}/websites/{selected_id}/cms/connection",
                                json={
                                    "site_url": site_url_input,
                                    "wp_username": username_input,
                                    "wp_app_password": app_password_input,
                                },
                                timeout=15,
                            )
                            if res.status_code == 200:
                                st.success("Connection saved! Now click 'Test Connection' below to verify it.")
                                st.rerun()
                            else:
                                st.error(f"Failed: {res.text}")
                        except Exception as e:
                            st.error(f"Could not reach backend: {e}")

            if connection:
                if st.button("Test Connection", use_container_width=True):
                    with st.spinner("Testing WordPress connection..."):
                        try:
                            res = requests.post(f"{BACKEND_URL}/websites/{selected_id}/cms/test", timeout=20)
                            if res.status_code == 200:
                                result = res.json()
                                if result["connected"]:
                                    st.success(result["message"])
                                else:
                                    st.error(result["message"])
                                st.rerun()
                            else:
                                st.error(f"Failed: {res.text}")
                        except Exception as e:
                            st.error(f"Could not reach backend: {e}")

        st.divider()

        if not connection or not connection.get("is_connected"):
            st.warning(
                "⚠️ No verified WordPress connection yet. Publishing actions below will fail until "
                "you save a connection above and successfully test it.",
                icon="⚠️",
            )

        st.subheader("Publish Actions")
        st.caption("All actions below only create drafts or update existing content - nothing is ever auto-published live.")

        tab1, tab2, tab3 = st.tabs(["📝 Publish Content Brief", "🏷️ Schema Injection", "✏️ On-Page Meta Update"])

        # ---------------- TAB 1: PUBLISH CONTENT BRIEF AS DRAFT ----------------
        with tab1:
            st.markdown("##### Create a WordPress Draft from a Content Brief")
            st.caption(
                "Creates a new WordPress post (status: draft) with a structured outline built from the "
                "brief's headings and FAQs. The actual article paragraphs still need to be written by a "
                "human - this only sets up the structure, per this project's no-fabrication rule."
            )

            briefs = api_get(f"/websites/{selected_id}/content-briefs")
            if not briefs:
                st.info("No content briefs yet. Generate one on 'Content Briefs & Optimizer' first.")
            else:
                brief_options = {f"{b['topic']} — {b['suggested_title'] or 'No title'}": b for b in briefs}
                selected_brief_label = st.selectbox("Select Content Brief", list(brief_options.keys()))
                selected_brief = brief_options[selected_brief_label]

                if st.button("Create Draft in WordPress", use_container_width=True, key="publish_brief_btn"):
                    with st.spinner("Creating draft in WordPress..."):
                        try:
                            res = requests.post(
                                f"{BACKEND_URL}/websites/{selected_id}/cms/publish/content-brief",
                                json={"content_brief_id": selected_brief["id"]},
                                timeout=30,
                            )
                            if res.status_code == 200:
                                job = res.json()
                                if job["status"] == "success":
                                    st.success(job["result_message"])
                                    if job.get("wp_edit_link"):
                                        st.markdown(f"[Open draft in WordPress]({job['wp_edit_link']})")
                                else:
                                    st.error(job["result_message"])
                            else:
                                st.error(f"Failed: {res.text}")
                        except Exception as e:
                            st.error(f"Could not reach backend: {e}")

        # ---------------- TAB 2: SCHEMA INJECTION ----------------
        with tab2:
            st.markdown("##### Inject Schema Markup into an Existing WordPress Post")
            st.caption(
                "Finds the WordPress post/page matching the page URL (by slug) and appends the saved "
                "JSON-LD schema block(s) to its content."
            )

            schema_markups = api_get(f"/websites/{selected_id}/schema")
            if not schema_markups:
                st.info("No saved schema markups yet. Generate some on 'Linking, Schema & AEO/GEO' first.")
            else:
                unique_page_urls = sorted(set(m["page_url"] for m in schema_markups))
                selected_page_url_schema = st.selectbox("Select Page URL", unique_page_urls, key="publish_schema_page")

                matching_markups = [m for m in schema_markups if m["page_url"] == selected_page_url_schema]
                st.caption(f"{len(matching_markups)} schema block(s) will be injected: {', '.join(m['schema_type'] for m in matching_markups)}")

                if st.button("Inject Schema into WordPress", use_container_width=True, key="publish_schema_btn"):
                    with st.spinner("Injecting schema into WordPress..."):
                        try:
                            res = requests.post(
                                f"{BACKEND_URL}/websites/{selected_id}/cms/publish/schema",
                                json={"page_url": selected_page_url_schema},
                                timeout=30,
                            )
                            if res.status_code == 200:
                                job = res.json()
                                if job["status"] == "success":
                                    st.success(job["result_message"])
                                else:
                                    st.error(job["result_message"])
                            else:
                                st.error(f"Failed: {res.json().get('detail', res.text)}")
                        except Exception as e:
                            st.error(f"Could not reach backend: {e}")

        # ---------------- TAB 3: ON-PAGE META UPDATE ----------------
        with tab3:
            st.markdown("##### Update Title / Meta Description / H1 on an Existing WordPress Post")
            st.caption(
                "Title updates natively. Meta description only works if the Yoast SEO plugin is active "
                "on the site. H1 is NOT auto-applied (WordPress has no dedicated H1 field) - it is "
                "returned as a manual note instead."
            )

            pages_for_meta = api_get(f"/websites/{selected_id}/pages")
            if not pages_for_meta:
                st.info("No crawled pages found. Please run a Technical SEO Audit first.")
            else:
                page_options_meta = {f"{p['url']}": p for p in pages_for_meta}
                selected_page_label_meta = st.selectbox("Select Page", list(page_options_meta.keys()), key="publish_meta_page")
                selected_page_meta = page_options_meta[selected_page_label_meta]

                prefill_title = ""
                prefill_meta = ""
                prefill_h1 = ""
                if (
                    "optimize_result" in st.session_state
                    and st.session_state.get("optimize_result_page_url") == selected_page_meta["url"]
                ):
                    opt = st.session_state["optimize_result"]
                    prefill_title = opt.get("optimized_title", "") or ""
                    prefill_meta = opt.get("optimized_meta_description", "") or ""
                    prefill_h1 = opt.get("optimized_h1", "") or ""

                new_title = st.text_input("New Title (leave blank to skip)", value=prefill_title, key="meta_new_title")
                new_meta_description = st.text_area(
                    "New Meta Description (leave blank to skip)", value=prefill_meta, key="meta_new_desc", height=100,
                )
                new_h1 = st.text_input("New H1 (will be shown as a manual note only)", value=prefill_h1, key="meta_new_h1")

                if st.button("Update in WordPress", use_container_width=True, key="publish_meta_btn"):
                    if not new_title and not new_meta_description and not new_h1:
                        st.warning("Please provide at least one field to update.")
                    else:
                        with st.spinner("Updating post in WordPress..."):
                            try:
                                res = requests.post(
                                    f"{BACKEND_URL}/websites/{selected_id}/cms/publish/meta",
                                    json={
                                        "page_url": selected_page_meta["url"],
                                        "optimized_title": new_title or None,
                                        "optimized_meta_description": new_meta_description or None,
                                        "optimized_h1": new_h1 or None,
                                    },
                                    timeout=30,
                                )
                                if res.status_code == 200:
                                    job = res.json()
                                    if job["status"] == "success":
                                        st.success(job["result_message"])
                                    else:
                                        st.error(job["result_message"])
                                else:
                                    st.error(f"Failed: {res.json().get('detail', res.text)}")
                            except Exception as e:
                                st.error(f"Could not reach backend: {e}")

        st.divider()
        st.subheader("Publish Job History")

        jobs = api_get(f"/websites/{selected_id}/cms/jobs")
        if jobs:
            job_rows = [
                {
                    "job_type": j["job_type"].replace("_", " "),
                    "source_description": j["source_description"] or "-",
                    "target_page_url": j["target_page_url"] or "-",
                    "status": j["status"],
                    "result_message": j["result_message"] or "-",
                }
                for j in jobs
            ]
            render_styled_table(
                job_rows,
                [
                    ("job_type", "Action"), ("source_description", "Source"),
                    ("target_page_url", "Target Page"), ("status", "Status"), ("result_message", "Result"),
                ],
                badge_columns={"status": JOB_STATUS_COLORS},
            )
        else:
            st.info("No publish jobs yet. Actions you run above will show up here.")

# ==========================================================
# PAGE: MONITORING & REFRESH
# ==========================================================
elif nav_selection == "Monitoring & Refresh":

    st.caption("Phase 9 — Autonomous Monitoring, Alerts & Content Refresh Loop")

    selected_id = project_dropdown("monitoring", websites)

    if not selected_id:
        st.warning("No projects found. Please create a project first on the 'Project Setup' page.")
    else:
        st.info(
            "ℹ️ 'Ranking drop detection' here means SEO score drops and newly appeared critical "
            "issues - the only real, measurable signals available without a paid ranking API. "
            "SERP data shown below is mock/demo only and never drives an alert.",
            icon="ℹ️",
        )

        col1, col2 = st.columns([1, 3])
        with col1:
            monitoring_max_pages = st.number_input(
                "Max pages to crawl", min_value=1, value=10, step=1, key="monitoring_max_pages",
            )
        with col2:
            st.write("")
            st.write("")
            run_monitoring_btn = st.button("Run Monitoring Check", use_container_width=True)

        if run_monitoring_btn:
            with st.spinner("Running technical audit, checking keywords, and comparing to the last snapshot..."):
                try:
                    res = requests.post(
                        f"{BACKEND_URL}/websites/{selected_id}/monitoring/run",
                        json={"max_pages": int(monitoring_max_pages)},
                        timeout=1800,
                    )
                    if res.status_code == 200:
                        snapshot = res.json()
                        if snapshot.get("alerts"):
                            st.error(f"🔔 Monitoring check completed with {len(snapshot['alerts'])} alert(s)!")
                        else:
                            st.success("✅ Monitoring check completed. No alerts.")
                        st.rerun()
                    else:
                        st.error(f"Failed: {res.text}")
                except Exception as e:
                    st.error(f"Could not reach backend: {e}")

        st.divider()
        st.subheader("Score History")

        snapshots = api_get(f"/websites/{selected_id}/monitoring/snapshots")
        if snapshots:
            df_snap = pd.DataFrame(snapshots)
            df_snap["created_at"] = pd.to_datetime(df_snap["created_at"])
            df_snap = df_snap.sort_values("created_at")

            fig = px.line(df_snap, x="created_at", y="score", markers=True)
            fig.update_traces(line_color=COLOR_PRIMARY, marker=dict(size=8, color=COLOR_PRIMARY))
            fig.update_layout(yaxis_range=[0, 100], yaxis_title="SEO Score", xaxis_title="")
            st.plotly_chart(style_fig(fig), use_container_width=True)

            latest = snapshots[0]
            m1, m2, m3 = st.columns(3)
            m1.metric("Latest Score", f"{latest['score']} / 100")
            m2.metric("Total Issues", latest["total_issues"])
            m3.metric("Pages Crawled", latest["pages_crawled"])
        else:
            st.info("No monitoring snapshots yet. Click 'Run Monitoring Check' above to create the first one.")

        st.divider()
        st.subheader("Active Alerts")

        alerts = api_get(f"/websites/{selected_id}/monitoring/alerts")
        if alerts:
            alert_rows = [
                {
                    "alert_type": a["alert_type"].replace("_", " "),
                    "message": a["message"],
                    "page_url": a["page_url"] or "-",
                    "created_at": a["created_at"][:16].replace("T", " "),
                }
                for a in alerts
            ]
            render_styled_table(
                alert_rows,
                [("alert_type", "Type"), ("message", "Message"), ("page_url", "Page"), ("created_at", "When")],
                badge_columns={"alert_type": ALERT_TYPE_COLORS},
            )
            st.caption(
                "💡 When alerts are raised, the Content Gap Agent automatically re-runs to surface fresh "
                "opportunities - check 'Competitors & Content Gaps' for updated results. Affected pages "
                "above are good candidates to re-analyze on 'Content Briefs & Optimizer'."
            )
        else:
            st.info("No alerts recorded yet. Alerts appear here after a monitoring check detects a score drop or a new critical issue.")

        st.divider()
        st.subheader("Snapshot History")

        if snapshots:
            snapshot_options = {f"{s['created_at'][:16].replace('T', ' ')} — Score {s['score']}": s for s in snapshots}
            selected_snapshot_label = st.selectbox("View a past snapshot's summary", list(snapshot_options.keys()))
            selected_snapshot_id = snapshot_options[selected_snapshot_label]["id"]

            snapshot_detail = api_get(f"/monitoring/snapshots/{selected_snapshot_id}")
            if snapshot_detail:
                if snapshot_detail.get("summary_text"):
                    st.markdown("**AI Summary:**")
                    st.write(snapshot_detail["summary_text"])

                if snapshot_detail.get("issues_by_severity_json"):
                    try:
                        severity_breakdown = json.loads(snapshot_detail["issues_by_severity_json"])
                        st.markdown("**Issues by Severity at this snapshot:**")
                        st.write(severity_breakdown)
                    except json.JSONDecodeError:
                        pass
        else:
            st.caption("No snapshots to show yet.")

        # ---------------- FULL PROJECT REPORT ----------------
        st.divider()
        st.subheader("📋 Full Project Report")
        st.caption(
            "Generates a complete summary of everything done on this project so far - technical "
            "audit, keywords, competitors, content gaps, briefs, internal linking, schema, AEO/GEO, "
            "page speed, WordPress publish history, and monitoring history. Built entirely from real "
            "saved data - nothing here is fabricated."
        )

        generate_report_btn = st.button("Generate Full Report", use_container_width=True)

        if generate_report_btn:
            with st.spinner("Building the full project report..."):
                try:
                    res = requests.get(f"{BACKEND_URL}/websites/{selected_id}/report", timeout=30)
                    if res.status_code == 200:
                        st.session_state["full_report"] = res.json()
                        st.success("Report generated!")
                    else:
                        st.error(f"Failed: {res.text}")
                except Exception as e:
                    st.error(f"Could not reach backend: {e}")

        if "full_report" in st.session_state and st.session_state["full_report"].get("website_id") == selected_id:
            report = st.session_state["full_report"]

            selected_website_obj = next((w for w in websites if w["id"] == selected_id), None)
            site_label = selected_website_obj["url"].replace("https://", "").replace("http://", "").replace("/", "_") if selected_website_obj else "site"
            filename = f"seo_report_{site_label}.md"

            st.download_button(
                label="⬇️ Download Report (Markdown)",
                data=report["report_markdown"],
                file_name=filename,
                mime="text/markdown",
                use_container_width=True,
            )

            with st.expander("Preview Report", expanded=True):
                st.markdown(report["report_markdown"])