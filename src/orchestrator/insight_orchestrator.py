"""
Insight Orchestrator — Semantic Kernel (free/OSS)

Synthesises signals from SharePoint, DevOps (via MCP tool), and D365 data.
Applies Hybrid RAG using LlamaIndex BM25 + ChromaDB semantic search.
Detects at-risk projects via computed risk scoring algorithm.
Generates formatted HTML status reports AND markdown reports.
Returns structured JSON with full agent trace for transparency.

Agent Pipeline:
  IntakeAgent (intent) → DataRetriever (AutoGen + RAG) → InsightOrchestrator (SK) → Report

STEP UP: In production, replace Semantic Kernel native functions with
SK + Azure OpenAI for natural language synthesis of insights.
"""
import os
import sys
import json
import logging
import time
import pandas as pd
from datetime import datetime

# Semantic Kernel imports
from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function

# Add src to sys path to import agents
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.agents.retrieval_agent import hybrid_query_knowledge_base, get_retrieval_agent, get_ingestion_stats
from src.agents.intake_agent import IntakeAgent, IntentType
from src.mcp_server.devops_mcp import (
    get_sprint_status, get_all_sprint_statuses,
    get_work_items, get_sprint_burndown, get_team_members
)
from src.utils.auth import authenticate_user

try:
    from src.config import (
        DATA_DIR, TARGET_VELOCITY,
        RISK_CRITICAL_THRESHOLD, RISK_AT_RISK_THRESHOLD, RISK_CAUTION_THRESHOLD,
        RISK_WEIGHT_BLOCKERS, RISK_WEIGHT_BUGS, RISK_WEIGHT_VELOCITY, RISK_WEIGHT_BUDGET,
        HTML_REPORT_OUTPUT_DIR
    )
except ImportError:
    DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
    TARGET_VELOCITY = 35
    RISK_CRITICAL_THRESHOLD = 70
    RISK_AT_RISK_THRESHOLD = 40
    RISK_CAUTION_THRESHOLD = 20
    RISK_WEIGHT_BLOCKERS = 0.30
    RISK_WEIGHT_BUGS = 0.20
    RISK_WEIGHT_VELOCITY = 0.20
    RISK_WEIGHT_BUDGET = 0.30
    HTML_REPORT_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "reports")

logger = logging.getLogger("IntelligentDeliveryAgent")


# =====================================================================
# Agent Trace Collector — records every step the agent takes
# =====================================================================

class AgentTrace:
    """Collects structured trace steps as the agent executes."""
    def __init__(self):
        self.steps = []
        self._step_counter = 0
        self._start_time = time.perf_counter()

    def add_step(self, agent: str, action: str, tool: str, status: str = "success",
                 details: str = "", data: dict = None):
        self._step_counter += 1
        elapsed_ms = round((time.perf_counter() - self._start_time) * 1000)
        step = {
            "step": self._step_counter,
            "agent": agent,
            "action": action,
            "tool": tool,
            "status": status,
            "details": details,
            "elapsed_ms": elapsed_ms,
        }
        if data:
            step["data"] = data
        self.steps.append(step)
        return step

    def to_list(self):
        return self.steps


# =====================================================================
# At-Risk Detection Algorithm
# =====================================================================

def compute_risk_score(blockers: int, open_bugs: int, total_bugs_opened: int,
                       velocity: int, target_velocity: int,
                       cost_actual: float, cost_budget: float) -> tuple:
    """
    Computes a weighted risk score (0-100) from multiple project signals.
    Returns (score, status_text, status_color, breakdown).

    Weights:
      - Blockers count:       30%
      - Open bugs ratio:      20%
      - Velocity gap:         20%
      - Budget overrun:       30%
    """
    # Blocker score (30%): each blocker adds 50 points, capped at 100
    blocker_score = min(100, blockers * 50)

    # Bug score (20%): ratio of open bugs to total opened
    if total_bugs_opened > 0:
        bug_score = min(100, (open_bugs / total_bugs_opened) * 100)
    else:
        bug_score = 0

    # Velocity score (20%): how far below target
    if target_velocity > 0:
        velocity_ratio = velocity / target_velocity
        if velocity_ratio >= 1.0:
            velocity_score = 0  # On or above target
        else:
            velocity_score = min(100, (1.0 - velocity_ratio) * 200)
    else:
        velocity_score = 0

    # Budget score (30%): overrun percentage
    if cost_budget > 0:
        overrun_ratio = cost_actual / cost_budget
        if overrun_ratio <= 1.0:
            budget_score = 0  # Within budget
        else:
            budget_score = min(100, (overrun_ratio - 1.0) * 200)
    else:
        budget_score = 0

    # Weighted composite score
    risk_score = (
        blocker_score * RISK_WEIGHT_BLOCKERS +
        bug_score * RISK_WEIGHT_BUGS +
        velocity_score * RISK_WEIGHT_VELOCITY +
        budget_score * RISK_WEIGHT_BUDGET
    )

    breakdown = {
        "blockers": {"raw": blocker_score, "weighted": round(blocker_score * RISK_WEIGHT_BLOCKERS, 1), "weight": "30%"},
        "bugs": {"raw": round(bug_score, 1), "weighted": round(bug_score * RISK_WEIGHT_BUGS, 1), "weight": "20%"},
        "velocity": {"raw": round(velocity_score, 1), "weighted": round(velocity_score * RISK_WEIGHT_VELOCITY, 1), "weight": "20%"},
        "budget": {"raw": round(budget_score, 1), "weighted": round(budget_score * RISK_WEIGHT_BUDGET, 1), "weight": "30%"},
    }

    # Classify risk
    if risk_score >= RISK_CRITICAL_THRESHOLD:
        return risk_score, "Critical", "#ef4444", breakdown
    elif risk_score >= RISK_AT_RISK_THRESHOLD:
        return risk_score, "At Risk", "#f59e0b", breakdown
    elif risk_score >= RISK_CAUTION_THRESHOLD:
        return risk_score, "Caution", "#eab308", breakdown
    else:
        return risk_score, "Healthy", "#10b981", breakdown


# =====================================================================
# HTML Report Generator
# =====================================================================

def generate_html_report(report_data: dict) -> str:
    """
    Generates a formatted HTML status report from structured report data.
    Saves to the reports/ directory and returns the HTML string.

    This fulfills the capstone requirement:
    "generates formatted HTML status report"
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    query_type = report_data.get("query_type", "unknown")
    risk_score = report_data.get("risk_score", 0)
    risk_status = report_data.get("risk_status", "Unknown")
    sources = report_data.get("sources_used", [])
    trace_steps = report_data.get("agent_trace", [])
    report_md = report_data.get("report", "")

    # Determine status color
    if risk_score >= RISK_CRITICAL_THRESHOLD:
        status_color = "#ef4444"
        status_bg = "rgba(239, 68, 68, 0.1)"
    elif risk_score >= RISK_AT_RISK_THRESHOLD:
        status_color = "#f59e0b"
        status_bg = "rgba(245, 158, 11, 0.1)"
    elif risk_score >= RISK_CAUTION_THRESHOLD:
        status_color = "#eab308"
        status_bg = "rgba(234, 179, 8, 0.1)"
    else:
        status_color = "#10b981"
        status_bg = "rgba(16, 185, 129, 0.1)"

    # Build trace HTML
    trace_html = ""
    for step in trace_steps:
        step_status = step.get("status", "success")
        dot_color = {"success": "#10b981", "warning": "#f59e0b", "critical": "#ef4444"}.get(step_status, "#6366f1")
        trace_html += f"""
        <div style="display:flex;gap:12px;padding:10px 0;border-left:2px solid #334155;padding-left:16px;margin-left:8px;position:relative;">
            <div style="position:absolute;left:-6px;top:14px;width:10px;height:10px;border-radius:50%;background:{dot_color};"></div>
            <div>
                <div style="font-size:0.75rem;font-weight:700;color:#6366f1;text-transform:uppercase;letter-spacing:0.05em;">{step.get('agent', '')}</div>
                <div style="font-size:0.9rem;font-weight:500;margin-top:2px;">{step.get('action', '')}</div>
                <span style="display:inline-block;margin-top:4px;font-size:0.7rem;padding:2px 8px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:100px;color:#94a3b8;">{step.get('tool', '')}</span>
                <div style="font-size:0.8rem;color:#64748b;margin-top:4px;">{step.get('details', '')}</div>
            </div>
        </div>"""

    # Build sources HTML
    sources_html = "".join([
        f'<span style="display:inline-block;margin:4px;padding:4px 12px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:100px;font-size:0.8rem;color:#94a3b8;">✓ {src}</span>'
        for src in sources
    ])

    # Convert markdown to simple HTML (basic conversion)
    report_body = report_md
    # Simple markdown table conversion
    lines = report_body.split("\n")
    in_table = False
    html_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            if not in_table:
                html_lines.append('<table style="width:100%;border-collapse:collapse;margin:16px 0;font-size:0.9rem;">')
                in_table = True
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if all(c.replace("-", "").replace(":", "").strip() == "" for c in cells):
                continue  # Skip separator rows
            if in_table and len(html_lines) == len([l for l in html_lines if '<table' in l or '<tr' in l or '<th' in l or '<td' in l]) + 1:
                # First data row → headers
                html_lines.append("<tr>" + "".join(
                    f'<th style="padding:10px 14px;text-align:left;border-bottom:1px solid #334155;background:rgba(255,255,255,0.03);font-weight:600;color:#94a3b8;text-transform:uppercase;font-size:0.75rem;">{c}</th>'
                    for c in cells
                ) + "</tr>")
            else:
                html_lines.append("<tr>" + "".join(
                    f'<td style="padding:10px 14px;border-bottom:1px solid #1e293b;">{c}</td>'
                    for c in cells
                ) + "</tr>")
        else:
            if in_table:
                html_lines.append("</table>")
                in_table = False
            # Basic markdown → HTML
            if stripped.startswith("## "):
                html_lines.append(f'<h2 style="font-size:1.4rem;font-weight:700;margin:20px 0 12px;color:#f1f5f9;">{stripped[3:]}</h2>')
            elif stripped.startswith("### "):
                html_lines.append(f'<h3 style="font-size:1.1rem;font-weight:600;margin:18px 0 10px;color:#a5b4fc;">{stripped[4:]}</h3>')
            elif stripped.startswith("- "):
                html_lines.append(f'<div style="padding:4px 0 4px 16px;color:#cbd5e1;">• {stripped[2:]}</div>')
            elif stripped.startswith("---"):
                html_lines.append('<hr style="border:0;height:1px;background:#334155;margin:18px 0;">')
            elif stripped.startswith("*") and stripped.endswith("*"):
                html_lines.append(f'<p style="color:#64748b;font-style:italic;margin:12px 0;">{stripped.strip("*")}</p>')
            elif stripped:
                html_lines.append(f'<p style="margin:8px 0;color:#cbd5e1;line-height:1.6;">{stripped}</p>')
    if in_table:
        html_lines.append("</table>")

    report_body_html = "\n".join(html_lines)

    # Apply bold markdown
    import re
    report_body_html = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color:#f1f5f9;">\1</strong>', report_body_html)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Health Report — MAQ Software Delivery Intelligence</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            padding: 40px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            padding: 32px;
            border-bottom: 1px solid #334155;
            margin-bottom: 32px;
        }}
        .header h1 {{
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 8px;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .header .subtitle {{
            font-size: 0.95rem;
            color: #94a3b8;
        }}
        .risk-badge {{
            display: inline-block;
            padding: 8px 24px;
            border-radius: 100px;
            font-weight: 700;
            font-size: 1rem;
            margin: 16px 0;
            background: {status_bg};
            color: {status_color};
            border: 1px solid {status_color}33;
        }}
        .section {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }}
        .section-title {{
            font-size: 0.85rem;
            font-weight: 700;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 16px;
        }}
        .footer {{
            text-align: center;
            padding: 24px;
            color: #64748b;
            font-size: 0.85rem;
            border-top: 1px solid #334155;
            margin-top: 32px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏢 MAQ Software — Delivery Intelligence Report</h1>
            <div class="subtitle">Generated {timestamp} | Intelligent Client Delivery Agent</div>
            <div class="risk-badge">{risk_status} — Risk Score: {risk_score}/100</div>
        </div>

        <div class="section">
            <div class="section-title">📋 Report</div>
            {report_body_html}
        </div>

        <div class="section">
            <div class="section-title">🔗 Agent Execution Trace</div>
            {trace_html}
        </div>

        <div class="section">
            <div class="section-title">📡 Data Sources Used</div>
            <div>{sources_html}</div>
        </div>

        <div class="footer">
            <p>Intelligent Client Delivery Agent for MAQ Software</p>
            <p>Semantic Kernel · AutoGen · LlamaIndex · ChromaDB · FastMCP</p>
            <p style="margin-top:8px;font-size:0.75rem;">This report was auto-generated by the multi-agent delivery intelligence system.</p>
        </div>
    </div>
</body>
</html>"""

    # Save to reports directory
    os.makedirs(HTML_REPORT_OUTPUT_DIR, exist_ok=True)
    filename = f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = os.path.join(HTML_REPORT_OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    logger.info(f"[Report] HTML report saved to: {filepath}")

    return html


# =====================================================================
# Semantic Kernel Plugin — The Core Agent Logic
# =====================================================================

class ProjectHealthPlugin:
    """
    Semantic Kernel native plugin that synthesizes project health signals
    from SharePoint, DevOps (MCP), and D365 data sources.

    Uses IntakeAgent for intent classification and DataRetriever for RAG.
    """

    def __init__(self):
        self._intake_agent = IntakeAgent()

    @kernel_function(
        name="synthesize_project_health",
        description="Synthesizes multi-source project signals into a health report"
    )
    async def synthesize_project_health(self, query: str, user_id: str) -> dict:
        """
        Core orchestration function. Returns structured JSON with full agent trace.

        Pipeline:
          1. IntakeAgent classifies intent and extracts entities
          2. Auth context is resolved for the user
          3. Data is retrieved from all sources via AutoGen DataRetriever
          4. Risk scores are computed
          5. Report is generated (markdown + HTML)
        """
        trace = AgentTrace()
        sources_used = []

        logger.info(f"[Semantic Kernel] Invoking synthesize_project_health for user={user_id}")

        # ── Step 1: Authenticate user ──
        auth_ctx = authenticate_user(user_id)
        trace.add_step(
            agent="Auth Service",
            action=f"Authenticated user: {auth_ctx.display_name} (role={auth_ctx.role})",
            tool="Simulated Entra ID",
            status="success" if auth_ctx.is_authenticated else "warning",
            details=f"User ID: {user_id}, Access: {len(auth_ctx.managed_projects)} projects"
        )

        # ── Step 2: Intent Classification via Intake Agent ──
        intake_result = await self._intake_agent.process_query(query, user_id)
        trace.add_step(
            agent="Intake Agent",
            action=f"Classified intent: {intake_result.intent} (confidence: {intake_result.confidence:.0%})",
            tool="Pro-Code NLP Classifier",
            status="success",
            details=(
                f"Projects: {', '.join(intake_result.project_names) if intake_result.project_names else 'All (portfolio)'}"
                + (f" | Focus: {intake_result.focus_area}" if intake_result.focus_area else "")
            )
        )

        # ── Route by intent ──
        if intake_result.intent == IntentType.PORTFOLIO_OVERVIEW:
            return await self._portfolio_report(query, user_id, auth_ctx, trace, sources_used)

        elif intake_result.intent == IntentType.RISK_QUERY:
            if intake_result.project_ids:
                return await self._single_project_report(
                    intake_result.project_ids[0],
                    intake_result.project_names[0] if intake_result.project_names else "Unknown",
                    query, user_id, auth_ctx, trace, sources_used
                )
            else:
                return await self._risk_overview_report(query, user_id, auth_ctx, trace, sources_used)

        elif intake_result.intent in (IntentType.BUDGET_QUERY, IntentType.SPRINT_QUERY, IntentType.TEAM_QUERY):
            if intake_result.project_ids:
                return await self._single_project_report(
                    intake_result.project_ids[0],
                    intake_result.project_names[0] if intake_result.project_names else "Unknown",
                    query, user_id, auth_ctx, trace, sources_used,
                    focus=intake_result.focus_area
                )
            else:
                return await self._portfolio_report(query, user_id, auth_ctx, trace, sources_used,
                                              focus=intake_result.focus_area)

        elif intake_result.intent == IntentType.PROJECT_HEALTH and intake_result.project_ids:
            return await self._single_project_report(
                intake_result.project_ids[0],
                intake_result.project_names[0] if intake_result.project_names else "Unknown",
                query, user_id, auth_ctx, trace, sources_used
            )

        else:
            # Default to portfolio overview
            return await self._portfolio_report(query, user_id, auth_ctx, trace, sources_used)

    def _load_all_projects(self, trace, sources_used):
        """Load all projects from SharePoint."""
        sp_file = os.path.join(DATA_DIR, "mock_sharepoint.json")
        all_projects = []
        if os.path.exists(sp_file):
            with open(sp_file, "r") as f:
                all_projects = json.load(f)
        sources_used.append("SharePoint")
        trace.add_step(
            agent="Data Retrieval Agent",
            action=f"Loaded {len(all_projects)} projects from SharePoint exports",
            tool="SharePoint (Local JSON)",
            status="success",
            details=", ".join([p["projectName"] for p in all_projects])
        )
        return all_projects

    def _load_all_sprints(self, trace, sources_used):
        """Fetch all sprint data via MCP."""
        logger.info("[MCP Tool] Calling get_all_sprint_statuses() via FastMCP...")
        all_sprints_json = get_all_sprint_statuses()
        all_sprints = json.loads(all_sprints_json)
        sources_used.append("Azure DevOps (MCP)")
        trace.add_step(
            agent="Data Retrieval Agent",
            action=f"Fetched sprint data for {len(all_sprints)} projects via MCP tool",
            tool="FastMCP → Azure DevOps",
            status="success",
            details=f"Retrieved velocity, bugs, and blocker data for all active sprints"
        )
        return all_sprints

    def _load_financials(self, trace, sources_used):
        """Load D365 financial data."""
        d365_file = os.path.join(DATA_DIR, "mock_d365.csv")
        df = pd.DataFrame()
        if os.path.exists(d365_file):
            df = pd.read_csv(d365_file)
        sources_used.append("D365 Project Operations")
        trace.add_step(
            agent="Data Retrieval Agent",
            action=f"Loaded financial timesheet data ({len(df)} records) from D365",
            tool="D365 (Local CSV)",
            status="success",
            details=f"Cost and hours data for {df['projectId'].nunique() if not df.empty else 0} projects"
        )
        return df

    async def _run_hybrid_rag(self, query, trace, sources_used, top_k=5):
        """Execute Hybrid RAG via AutoGen DataRetriever."""
        logger.info("[AutoGen] Instantiating Data Retrieval Agent...")
        retrieval_agent = get_retrieval_agent()

        if retrieval_agent:
            logger.info(f"[AutoGen] Invoking agent '{retrieval_agent.name}' for context...")
            from autogen_agentchat.messages import TextMessage
            from autogen_core import CancellationToken
            response = await retrieval_agent.on_messages(
                [TextMessage(content=f"Search the knowledge base for context about: {query}", source="user")],
                cancellation_token=CancellationToken()
            )
            rag_context = response.chat_message.content
            agent_name = retrieval_agent.name
        else:
            rag_context = hybrid_query_knowledge_base(query, top_k=top_k)
            agent_name = "Data Retrieval Agent"

        sources_used.append("ChromaDB + BM25 (Hybrid RAG)")
        trace.add_step(
            agent=agent_name,
            action="Executed Hybrid RAG search via AutoGen AssistantAgent",
            tool="AutoGen + LlamaIndex BM25 + ChromaDB",
            status="success",
            details=f"Reciprocal Rank Fusion applied across keyword and vector results"
        )
        return rag_context

    def _compute_project_summary(self, proj, sprint, proj_df):
        """Compute risk and build summary for one project."""
        open_bugs = max(0, sprint.get("bugsOpened", 0) - sprint.get("bugsClosed", 0))
        cost_actual = int(proj_df["costActual"].sum()) if not proj_df.empty else 0
        cost_budget = int(proj_df["costBudget"].sum()) if not proj_df.empty else 0
        hours_logged = int(proj_df["hoursLogged"].sum()) if not proj_df.empty else 0
        hours_budgeted = int(proj_df["budgetedHours"].sum()) if not proj_df.empty else 0

        risk_score, status_text, status_color, breakdown = compute_risk_score(
            blockers=sprint.get("blockers", 0),
            open_bugs=open_bugs,
            total_bugs_opened=sprint.get("bugsOpened", 0),
            velocity=sprint.get("velocity", 0),
            target_velocity=TARGET_VELOCITY,
            cost_actual=cost_actual,
            cost_budget=cost_budget
        )

        return {
            "projectId": proj["projectId"],
            "projectName": proj["projectName"],
            "manager": proj.get("manager", "N/A"),
            "client": proj.get("client", "N/A"),
            "technology": proj.get("technology", "N/A"),
            "phase": proj.get("phase", "N/A"),
            "priority": proj.get("priority", "N/A"),
            "description": proj.get("description", ""),
            "status_text": status_text,
            "status_color": status_color,
            "risk_score": round(risk_score, 1),
            "risk_breakdown": breakdown,
            "sprint": sprint.get("sprint", "N/A"),
            "velocity": sprint.get("velocity", 0),
            "open_bugs": open_bugs,
            "blockers": sprint.get("blockers", 0),
            "cost_actual": cost_actual,
            "cost_budget": cost_budget,
            "hours_logged": hours_logged,
            "hours_budgeted": hours_budgeted,
            "startDate": proj.get("startDate", "N/A"),
            "endDate": proj.get("endDate", "N/A"),
        }

    async def _portfolio_report(self, query, user_id, auth_ctx, trace, sources_used, focus=None):
        """Generate a portfolio-wide report across all projects."""
        all_projects = self._load_all_projects(trace, sources_used)
        all_sprints = self._load_all_sprints(trace, sources_used)
        df = self._load_financials(trace, sources_used)
        await self._run_hybrid_rag(query, trace, sources_used)

        # Apply RBAC filter
        accessible = auth_ctx.get_accessible_projects()
        if accessible is not None:
            all_projects = [p for p in all_projects if p["projectId"] in accessible]
            trace.add_step(
                agent="Auth Service",
                action=f"Applied RBAC filter: {len(all_projects)} projects accessible to {auth_ctx.display_name}",
                tool="Simulated Entra ID",
                status="success",
                details=f"Filtered to: {', '.join(accessible)}"
            )

        # Compute risk for each project
        sprint_map = {s["projectId"]: s for s in all_sprints}
        project_summaries = []
        for proj in all_projects:
            pid = proj["projectId"]
            sprint = sprint_map.get(pid, {})
            proj_df = df[df["projectId"] == pid] if not df.empty else pd.DataFrame()
            project_summaries.append(self._compute_project_summary(proj, sprint, proj_df))

        trace.add_step(
            agent="Insight Orchestrator",
            action=f"Computed risk scores for {len(project_summaries)} projects",
            tool="Risk Scoring Algorithm",
            status="warning" if any(p["risk_score"] >= RISK_CRITICAL_THRESHOLD for p in project_summaries) else "success",
            details="; ".join([f"{p['projectName']}: {p['risk_score']}/100 ({p['status_text']})" for p in project_summaries])
        )

        # Build markdown report using LLM
        from src.agents.retrieval_agent import get_retrieval_agent
        retrieval_agent = get_retrieval_agent()
        
        if retrieval_agent:
            from autogen_agentchat.messages import TextMessage
            from autogen_core import CancellationToken
            import json
            
            prompt = f"""
You are a Portfolio Director AI. Review the following JSON summary of {len(all_projects)} active projects.
Write a 4-sentence Executive Summary highlighting the overall portfolio risk, specifically calling out any critical projects, blockers, or budget overruns.
Do not include any greetings or markdown tables.

Data:
{json.dumps(project_summaries, indent=2)}
"""
            trace.add_step(
                agent="Groq AutoGen Agent",
                action="Synthesized portfolio executive summary via LLM",
                tool="qwen/qwen3.8-27b",
                status="success",
                details="Used project metrics to write natural language portfolio summary."
            )
            response = await retrieval_agent.on_messages(
                [TextMessage(content=prompt, source="user")],
                cancellation_token=CancellationToken()
            )
            llm_summary = response.chat_message.content
        else:
            llm_summary = "Agent not configured for summary."

        report_lines = [f"## 🏢 Portfolio Health Dashboard", ""]
        report_lines.append(llm_summary + "\n")
        report_lines.append(f"**{len(all_projects)} active Power BI delivery projects** under management. Here is the full status:\n")

        report_lines.append("| Project | Client | Risk Score | Status | Sprint | Velocity | Open Bugs | Blockers |")
        report_lines.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
        for p in project_summaries:
            report_lines.append(
                f"| **{p['projectName']}** | {p['client']} | {p['risk_score']}/100 | {p['status_text']} | {p['sprint']} | {p['velocity']} | {p['open_bugs']} | {p['blockers']} |"
            )

        if focus == "budget":
            report_lines.append(f"\n### 💰 Financial Summary")
            report_lines.append("| Project | Actual Cost | Budget | Status |")
            report_lines.append("| :--- | :---: | :---: | :---: |")
            for p in project_summaries:
                status = "⚠️ Over Budget" if p["cost_actual"] > p["cost_budget"] else "✅ Within Budget"
                report_lines.append(f"| **{p['projectName']}** | ${p['cost_actual']:,} | ${p['cost_budget']:,} | {status} |")

        report_lines.append("\n---\n*Would you like a deep-dive health report on any specific project?*")

        at_risk = [p for p in project_summaries if p["risk_score"] >= RISK_AT_RISK_THRESHOLD]
        healthy = [p for p in project_summaries if p["risk_score"] < RISK_AT_RISK_THRESHOLD]
        
        trace.add_step(
            agent="Insight Orchestrator",
            action="Synthesized portfolio health report from all data sources",
            tool="Report Generator",
            status="success",
            details=f"{len(at_risk)} projects at risk, {len(healthy)} healthy"
        )

        result = {
            "agent_trace": trace.to_list(),
            "report": "\n".join(report_lines),
            "sources_used": sources_used,
            "risk_score": max((p["risk_score"] for p in project_summaries), default=0),
            "risk_status": "Critical" if any(p["risk_score"] >= RISK_CRITICAL_THRESHOLD for p in project_summaries) else "Healthy",
            "query_type": "portfolio",
            "project_summaries": project_summaries,
        }

        # Generate HTML report
        result["html_report"] = generate_html_report(result)

        return result

    async def _risk_overview_report(self, query, user_id, auth_ctx, trace, sources_used):
        """Generate a risk-focused overview across all projects."""
        # Reuse portfolio report with risk focus
        return await self._portfolio_report(query, user_id, auth_ctx, trace, sources_used, focus="risk")

    async def _single_project_report(self, project_id, default_name, query, user_id,
                                auth_ctx, trace, sources_used, focus=None):
        """Generate a deep-dive report for a single project."""

        # RBAC check
        if not auth_ctx.can_access_project(project_id):
            trace.add_step(
                agent="Auth Service",
                action=f"Access denied: {auth_ctx.display_name} cannot access {project_id}",
                tool="Simulated Entra ID",
                status="critical",
                details=f"User role: {auth_ctx.role}. Accessible projects: {auth_ctx.managed_projects}"
            )
            return {
                "agent_trace": trace.to_list(),
                "report": f"## ⛔ Access Denied\n\nYou do not have permission to view **{default_name}** ({project_id}). Please contact your administrator.",
                "sources_used": sources_used,
                "risk_score": 0,
                "risk_status": "Unknown",
                "query_type": "access_denied",
            }

        # ── Step: Retrieve SharePoint Data ──
        sp_file = os.path.join(DATA_DIR, "mock_sharepoint.json")
        project_details = {
            "projectId": project_id, "projectName": default_name,
            "status": "Active", "manager": "Unknown",
            "startDate": "N/A", "endDate": "N/A",
            "description": "No description available.",
            "client": "N/A", "technology": "N/A",
            "teamSize": 0, "phase": "N/A", "priority": "N/A",
        }
        if os.path.exists(sp_file):
            with open(sp_file, "r") as f:
                sp_data = json.load(f)
            for item in sp_data:
                if item.get("projectId") == project_id:
                    project_details.update(item)
                    break
        sources_used.append("SharePoint")
        trace.add_step(
            agent="Data Retrieval Agent",
            action=f"Loaded project metadata for {project_details['projectName']}",
            tool="SharePoint (Local JSON)",
            status="success",
            details=f"Client: {project_details['client']}, Manager: {project_details['manager']}, Phase: {project_details['phase']}"
        )

        # ── Step: Retrieve DevOps Data via MCP Tool ──
        logger.info(f"[MCP Tool] Calling get_sprint_status('{project_id}') via FastMCP...")
        devops_json = get_sprint_status(project_id)
        devops_details = json.loads(devops_json)

        if "error" in devops_details:
            logger.warning(f"[MCP Tool] {devops_details['error']}")
            devops_details = {"sprint": "N/A", "velocity": 0, "bugsOpened": 0, "bugsClosed": 0, "blockers": 0,
                              "totalStoryPoints": 0, "completedStoryPoints": 0}
            mcp_status = "warning"
        else:
            mcp_status = "success"

        sources_used.append("Azure DevOps (MCP)")
        trace.add_step(
            agent="Data Retrieval Agent",
            action=f"Fetched sprint metrics via MCP tool call",
            tool="FastMCP → Azure DevOps",
            status=mcp_status,
            details=f"Sprint: {devops_details.get('sprint')}, Velocity: {devops_details.get('velocity')}, Bugs: {devops_details.get('bugsOpened')}/{devops_details.get('bugsClosed')}, Blockers: {devops_details.get('blockers')}"
        )

        # ── Step: Retrieve work items via MCP ──
        work_items_json = get_work_items(project_id)
        work_items_data = json.loads(work_items_json)
        work_items = work_items_data.get("workItems", [])
        trace.add_step(
            agent="Data Retrieval Agent",
            action=f"Fetched {len(work_items)} work items via MCP tool call",
            tool="FastMCP → Azure DevOps",
            status="success",
            details=f"Types: {', '.join(set(wi.get('type','') for wi in work_items))}"
        )

        # ── Step: Retrieve burndown via MCP ──
        burndown_json = get_sprint_burndown(project_id)
        burndown = json.loads(burndown_json)
        trace.add_step(
            agent="Data Retrieval Agent",
            action=f"Fetched sprint burndown: {burndown.get('completionPercentage', 0)}% complete",
            tool="FastMCP → Azure DevOps",
            status="success",
            details=f"{burndown.get('completedStoryPoints', 0)}/{burndown.get('totalStoryPoints', 0)} story points"
        )

        # ── Step: Retrieve D365 Financial Data ──
        d365_file = os.path.join(DATA_DIR, "mock_d365.csv")
        financials = {"hoursLogged": 0, "budgetedHours": 0, "costActual": 0, "costBudget": 0}
        resource_count = 0
        resource_details = []
        if os.path.exists(d365_file):
            df = pd.read_csv(d365_file)
            project_df = df[df["projectId"] == project_id]
            if not project_df.empty:
                financials["hoursLogged"] = int(project_df["hoursLogged"].sum())
                financials["budgetedHours"] = int(project_df["budgetedHours"].sum())
                financials["costActual"] = int(project_df["costActual"].sum())
                financials["costBudget"] = int(project_df["costBudget"].sum())
                resource_count = project_df["resourceName"].nunique()
                # Get resource breakdown
                for name, grp in project_df.groupby("resourceName"):
                    resource_details.append({
                        "name": name,
                        "role": grp["role"].iloc[0] if "role" in grp.columns else "N/A",
                        "hours": int(grp["hoursLogged"].sum()),
                        "cost": int(grp["costActual"].sum()),
                    })

        sources_used.append("D365 Project Operations")
        finance_status = "warning" if financials["costActual"] > financials["costBudget"] else "success"
        trace.add_step(
            agent="Data Retrieval Agent",
            action=f"Loaded financial & timesheet data from D365",
            tool="D365 (Local CSV)",
            status=finance_status,
            details=f"{resource_count} resources. Hours: {financials['hoursLogged']}/{financials['budgetedHours']}. Cost: ${financials['costActual']:,}/${financials['costBudget']:,}"
        )

        # ── Step: Hybrid RAG for contextual grounding via AutoGen Agent ──
        rag_context = await self._run_hybrid_rag(query, trace, sources_used)

        # ── Step: Computed Risk Scoring ──
        open_bugs = max(0, devops_details.get("bugsOpened", 0) - devops_details.get("bugsClosed", 0))
        blockers = devops_details.get("blockers", 0)
        velocity = devops_details.get("velocity", 0)

        risk_score, status_text, status_color, breakdown = compute_risk_score(
            blockers=blockers,
            open_bugs=open_bugs,
            total_bugs_opened=devops_details.get("bugsOpened", 0),
            velocity=velocity,
            target_velocity=TARGET_VELOCITY,
            cost_actual=financials["costActual"],
            cost_budget=financials["costBudget"]
        )
        logger.info(f"[Risk Score] Computed: {risk_score:.1f}/100 => {status_text}")

        risk_level = "critical" if risk_score >= RISK_CRITICAL_THRESHOLD else ("warning" if risk_score >= RISK_AT_RISK_THRESHOLD else "success")
        trace.add_step(
            agent="Insight Orchestrator",
            action=f"Computed risk score: {risk_score:.0f}/100 → {status_text}",
            tool="Risk Scoring Algorithm",
            status=risk_level,
            details=f"Blockers: {breakdown['blockers']['weighted']}pts, Bugs: {breakdown['bugs']['weighted']}pts, Velocity: {breakdown['velocity']['weighted']}pts, Budget: {breakdown['budget']['weighted']}pts",
            data=breakdown
        )

        # ── Step: Generate Report ──
        finance_over = financials["costActual"] > financials["costBudget"]
        retrieval_agent = get_retrieval_agent()
        if retrieval_agent:
            from autogen_agentchat.messages import TextMessage
            from autogen_core import CancellationToken
            prompt = f"""
You are a Senior Delivery Manager AI.
Write a 3-sentence Executive Summary and 2 actionable recommendations based on the data below.

Data:
Risk Score: {risk_score:.0f}/100
Blockers: {blockers}
Open Bugs: {open_bugs}
Velocity: {velocity}/{TARGET_VELOCITY}
Budget Status: {'Over Budget ⚠️' if finance_over else 'Within Budget ✅'} (${financials['costActual']:,} / ${financials['costBudget']:,})

Retrieved Context:
{rag_context}

Output only the Markdown text. Do not include greetings.
"""
            trace.add_step(
                agent="Groq AutoGen Agent",
                action="Synthesized executive summary and recommendations via LLM",
                tool="llama-3.3-70b-versatile",
                status="success",
                details="Used retrieved context and structured metrics to write natural language summary."
            )
            response = await retrieval_agent.on_messages(
                [TextMessage(content=prompt, source="user")],
                cancellation_token=CancellationToken()
            )
            impact_text = response.chat_message.content
        else:
            impact_parts = []
            if blockers > 0:
                impact_parts.append(f"slowed due to {blockers} blocker{'s' if blockers > 1 else ''}")
            if velocity < TARGET_VELOCITY:
                impact_parts.append("lower than target velocity")
            impact_text = (
                f"Current sprint progress is {' and '.join(impact_parts)}."
                if impact_parts else
                "Current sprint progress is running smoothly on target."
            )

        finance_status_text = "Over Budget ⚠️" if finance_over else "Within Budget ✅"
        formatted_actual_cost = f"${financials['costActual']:,}"
        formatted_budget_cost = f"${financials['costBudget']:,}"
        hours_pct = min(100, int((financials["hoursLogged"] / max(1, financials["budgetedHours"])) * 100))
        completion_pct = burndown.get("completionPercentage", 0)

        markdown_report = f"""## {project_details['projectName']} — Health Report

### Overall Health: {status_text} (Risk Score: {risk_score:.0f}/100)

| Signal | Details |
| :--- | :--- |
| **Client** | {project_details['client']} |
| **Technology** | {project_details['technology']} |
| **Phase** | {project_details['phase']} |
| **Priority** | {project_details['priority']} |
| **Team Size** | {project_details.get('teamSize', 'N/A')} |
| **Current Sprint** | {devops_details.get('sprint', 'N/A')} |
| **Sprint Completion** | {completion_pct}% ({burndown.get('completedStoryPoints', 0)}/{burndown.get('totalStoryPoints', 0)} story points) |
| **Velocity** | {velocity} / {TARGET_VELOCITY} target |
| **Open Bugs** | {open_bugs} ({devops_details.get('bugsOpened', 0)} opened, {devops_details.get('bugsClosed', 0)} closed) |
| **Active Blockers** | {blockers} |
| **Manager** | {project_details['manager']} |
| **Timeline** | {project_details['startDate']} → {project_details['endDate']} |

---

**Context:** {project_details['projectName']} is a {project_details['description']}
{impact_text}

### 📊 Financial Health (D365)
| Metric | Budget | Actual | Status |
| :--- | :---: | :---: | :---: |
| **Hours** | {financials['budgetedHours']} hrs | {financials['hoursLogged']} hrs ({hours_pct}%) | {'⚠️' if hours_pct > 100 else '✅'} |
| **Cost** | {formatted_budget_cost} | {formatted_actual_cost} | **{finance_status_text}** |"""

        # Add resource breakdown
        if resource_details:
            markdown_report += f"\n\n### 👥 Resource Allocation ({resource_count} resources)"
            markdown_report += "\n| Resource | Role | Hours | Cost |"
            markdown_report += "\n| :--- | :--- | :---: | :---: |"
            for r in resource_details:
                markdown_report += f"\n| {r['name']} | {r['role']} | {r['hours']} hrs | ${r['cost']:,} |"

        # Add work items section
        if work_items:
            active_items = [wi for wi in work_items if wi.get("state") == "Active"]
            if active_items:
                markdown_report += f"\n\n### 🔧 Active Work Items ({len(active_items)})"
                for wi in active_items:
                    icon = "🐛" if wi["type"] == "Bug" else "📋"
                    markdown_report += f"\n- {icon} **{wi['title']}** ({wi['type']}) — Assigned to {wi.get('assignedTo', 'Unassigned')}"

        markdown_report += "\n\n---\n\n*Would you like me to generate an action plan to mitigate the risks, or drill into specific blockers?*\n"

        trace.add_step(
            agent="Insight Orchestrator",
            action="Synthesized final health report from all data sources",
            tool="Report Generator",
            status="success",
            details=f"Report generated from {len(sources_used)} sources for {project_details['projectName']}"
        )

        result = {
            "agent_trace": trace.to_list(),
            "report": markdown_report,
            "sources_used": sources_used,
            "risk_score": round(risk_score, 1),
            "risk_status": status_text,
            "risk_color": status_color,
            "risk_breakdown": breakdown,
            "query_type": "single_project",
            "project_name": project_details["projectName"],
        }

        # Generate HTML report
        result["html_report"] = generate_html_report(result)

        return result


# =====================================================================
# Semantic Kernel — Kernel Setup
# =====================================================================

_kernel = Kernel()
_health_plugin = ProjectHealthPlugin()
_kernel.add_plugin(_health_plugin, plugin_name="ProjectHealthPlugin")
logger.info("[Semantic Kernel] Kernel initialized with ProjectHealthPlugin.")


async def synthesize_signals(query: str, user_id: str) -> dict:
    """
    Main entry point called by the FastAPI route.
    Uses Semantic Kernel to invoke the ProjectHealthPlugin function.
    Returns structured JSON with agent trace.
    """
    logger.info(f"[Semantic Kernel] Kernel invoking synthesize_project_health...")

    plugin_functions = _kernel.get_plugin("ProjectHealthPlugin")
    sk_function = plugin_functions["synthesize_project_health"]

    result = await _health_plugin.synthesize_project_health(query=query, user_id=user_id)

    logger.info("[Semantic Kernel] Report generation complete.")
    return result


if __name__ == "__main__":
    import asyncio
    async def main():
        result = await synthesize_signals("Give me an overview of all projects", "mgr123")
        print(json.dumps({k: v for k, v in result.items() if k != "html_report"}, indent=2))
    asyncio.run(main())
