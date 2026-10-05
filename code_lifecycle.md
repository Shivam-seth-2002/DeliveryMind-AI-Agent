# The Pro-Code Codebase Architecture & File Lifecycle

This document provides a technical walkthrough of every module in `src/`, showing how they interact during execution.

---

## 1. Central Configuration: `src/config.py`
Centralizes environment variables, file paths, model identifiers, risk scoring weights, and thresholds.

```python
TARGET_VELOCITY = int(os.environ.get("TARGET_VELOCITY", "35"))
RISK_CRITICAL_THRESHOLD = 70
RISK_WEIGHT_BLOCKERS = 0.30
RISK_WEIGHT_BUGS = 0.20
RISK_WEIGHT_VELOCITY = 0.20
RISK_WEIGHT_BUDGET = 0.30
```

---

## 2. Gateway Layer: `src/api.py`
The FastAPI application serving as the system's entry point.

**Key responsibilities:**
- Request validation with Pydantic (`QueryRequest`, `ExportRequest`).
- Request timing middleware with `X-Correlation-Id`.
- Centralized CORS configuration.
- Endpoints:
  - `POST /api/query_project_health` — Executes the full multi-agent pipeline.
  - `POST /api/export_html` — Generates and downloads a styled HTML status report.
  - `GET /api/health` — Returns status of all agent subsystems.
  - `GET /api/sources` — Returns real-time ingestion metadata for connected sources.
  - `GET /api/projects` — Returns the list of 5 delivery projects.

---

## 3. Identity & Access: `src/utils/auth.py`
Provides simulated Entra ID authentication and Role-Based Access Control (RBAC).

**Key components:**
- `USER_REGISTRY`: Pre-configured user profiles (`mgr123`, `mgr456`, `admin001`, `viewer001`).
- `AuthContext`: Dataclass encapsulating user identity, role, and authorized projects.
- `can_access_project(project_id)`: Enforces project-level data isolation.
- **Step Up to Production:** Comments document how to replace this with Microsoft Authentication Library (MSAL) and Azure AD Bearer tokens.

---

## 4. Intake Agent: `src/agents/intake_agent.py`
The pro-code natural language intent classifier replacing low-code tools.

**Key components:**
- `IntentType`: Defines 6 distinct query intents (`PROJECT_HEALTH`, `PORTFOLIO_OVERVIEW`, `BUDGET_QUERY`, `RISK_QUERY`, `SPRINT_QUERY`, `TEAM_QUERY`).
- `PROJECT_ALIASES`: Maps common names, codenames, and abbreviations to canonical project IDs (`P-001` through `P-005`).
- `IntakeResult`: Structured output returning classified intent, target projects, confidence score, and focus area.

---

## 5. Insight Orchestrator: `src/orchestrator/insight_orchestrator.py`
The central brain powered by **Microsoft Semantic Kernel**.

**Key components:**
- `ProjectHealthPlugin`: Native Semantic Kernel plugin with `@kernel_function` annotation.
- `AgentTrace`: Captures a structured, step-by-step audit trail of every agent action with millisecond timing.
- `compute_risk_score()`: Weighted composite algorithm assessing blockers, bug backlogs, sprint velocity deficit, and budget burn rate.
- `generate_html_report()`: Generates standalone, dark-themed HTML status reports.
- Intent Routing: Dynamically routes to portfolio overviews, deep-dive project audits, or budget/sprint summaries.

---

## 6. Data Retrieval Agent: `src/agents/retrieval_agent.py`
The researcher powered by **AutoGen AssistantAgent** and **Hybrid RAG**.

**Key components:**
- `SentenceTransformer("all-MiniLM-L6-v2")`: Local, open-source embedding model generating dense vectors.
- `chromadb.PersistentClient`: Local vector store for semantic similarity queries.
- `llama_index.retrievers.bm25.BM25Retriever`: Sparse keyword search engine.
- `_reciprocal_rank_fusion()`: Fuses dense semantic and sparse keyword results using Reciprocal Rank Fusion (RRF).
- `get_retrieval_agent()`: Instantiates an AutoGen `AssistantAgent` configured with registered retrieval tools.

---

## 7. FastMCP DevOps Tool Server: `src/mcp_server/devops_mcp.py`
Implements the Model Context Protocol (MCP) using `FastMCP`.

**Registered MCP Tools:**
1. `get_sprint_status(project_id)`: Retrieves sprint number, velocity, bug delta, and blocker count.
2. `get_all_sprint_statuses()`: Retrieves portfolio-wide sprint summaries.
3. `get_work_items(project_id)`: Fetches user stories, bugs, and tasks with assignee details.
4. `get_sprint_burndown(project_id)`: Calculates story point completion rates.
5. `get_team_members(project_id)`: Lists assigned engineering resources.

---

## 8. Telemetry & Observability: `src/utils/telemetry.py`
Centralized telemetry logging to Azure Application Insights (free tier) with JSONL fallback.

**Tracked telemetry primitives:**
- `track_request()`: Tracks endpoint latency, status codes, and user context.
- `track_event()`: Custom business events (e.g., `QueryProcessed`, `ReportGenerated`).
- `track_dependency()`: Times external subsystem calls (ChromaDB, BM25, MCP Server).
- `track_exception()`: Structured error and exception logging.
- `timed_dependency()`: Python context manager for timing dependency blocks.
