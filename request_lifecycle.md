# The Pro-Code Request Lifecycle: "What is the health of Project Beta?"

This document traces the complete, end-to-end execution path of a user query through the **100% Pro-Code Intelligent Client Delivery Agent**.

---

### Step 1: Client Query & Context Dispatch (Frontend Web App)
1. **User Action:** The Delivery Manager types *"What is the health of Project Beta?"* into the web dashboard or clicks the quick-action button.
2. **Context Enrichment:** The frontend captures the query, attaches the simulated authentication context (`user_id = "mgr123"`), and initiates an `HTTP POST` request to `/api/query_project_health`.
3. **UI State Transition:** The dashboard initializes the **Agent Execution Trace** component with a live shimmer loader, preparing to visualize the multi-agent chain of thought.

---

### Step 2: Gateway Layer & Request Telemetry (`src/api.py`)
4. **FastAPI Ingestion:** The FastAPI router catches the request payload and validates it using the Pydantic `QueryRequest` schema.
5. **Correlation ID Generation:** The request timing middleware attaches a unique `X-Correlation-Id` and starts a high-resolution performance counter.
6. **Telemetry Tracking:** The API records a `QueryReceived` event and invokes `track_request()` via `src/utils/telemetry.py` (logging to Application Insights / local JSONL).

---

### Step 3: Identity & Access Management (`src/utils/auth.py`)
7. **Simulated Entra ID Verification:** The request reaches the Auth Service. `authenticate_user("mgr123")` looks up the user registry.
8. **RBAC Resolution:** The user is validated as `Sarah Chen` with role `manager` and assigned projects `['P-001', 'P-002', 'P-004']`.
9. **Project Access Check:** Access to `P-002` (Project Beta) is confirmed. Trace Step 1 is recorded.

---

### Step 4: Pro-Code Intake Agent (`src/agents/intake_agent.py`)
10. **NLP Intent Classification:** The pro-code `IntakeAgent` parses the natural language string using regex-based intent matching.
11. **Entity Extraction:** The classifier extracts project aliases:
    - `"beta"` maps to canonical ID `P-002` (`Project Beta`).
12. **Intent Classification Result:** Classified as `project_health` (confidence: 90%, focus: health signals). Trace Step 2 is recorded.

---

### Step 5: Insight Orchestrator Invocation (`src/orchestrator/insight_orchestrator.py`)
13. **Semantic Kernel Kernel Execution:** The kernel routes the request to the native `ProjectHealthPlugin.synthesize_project_health()` function.
14. **Orchestration Plan:** Recognizing a single-project health query, the orchestrator begins multi-source signal harvesting.

---

### Step 6: Multi-Source Data Harvesting (`src/agents/retrieval_agent.py` & `src/mcp_server/devops_mcp.py`)
15. **SharePoint Project Metadata:** Loads `mock_sharepoint.json` to retrieve client (`Northwind Traders`), manager (`mgr123`), phase (`Execution`), priority (`Critical`), and description. Trace Step 3 is recorded.
16. **Azure DevOps via FastMCP:** The orchestrator invokes the FastMCP tool server:
    - `get_sprint_status("P-002")`: Sprint 12, Velocity: 20, Bugs: 15 open / 4 closed, Blockers: 2. Trace Step 4 is recorded.
    - `get_work_items("P-002")`: Active bugs (credential expiration, staging down, ETL null errors). Trace Step 5 is recorded.
    - `get_sprint_burndown("P-002")`: 20/45 story points completed (44.4%). Trace Step 6 is recorded.
17. **D365 Project Operations Financials:** Reads `mock_d365.csv` to aggregate actual cost ($45,000) vs budget ($33,000) and hours logged (450 hrs) across 3 team members. Trace Step 7 is recorded.

---

### Step 7: AutoGen Agent Grounding via Hybrid RAG (`src/agents/retrieval_agent.py`)
18. **AutoGen AssistantAgent Instantiation:** AutoGen's `DataRetriever` agent is invoked for contextual grounding.
19. **Dual Search Execution:**
    - **ChromaDB:** Generates dense semantic embeddings with `all-MiniLM-L6-v2` to query meaning-matched documents.
    - **BM25 Retriever:** Performs sparse keyword matching via LlamaIndex for exact term hits.
20. **Reciprocal Rank Fusion (RRF):** Merges both ranked result lists using $RRF(d) = \sum \frac{1}{k + rank}$ to eliminate bias and produce the most relevant context. Trace Step 8 is recorded.

---

### Step 8: Risk Scoring & Report Synthesis (`src/orchestrator/insight_orchestrator.py`)
21. **Weighted Risk Calculation:** The orchestrator evaluates the composite risk formula:
    $$\text{Score} = (100 \times 0.30) + (73.3 \times 0.20) + (85.7 \times 0.20) + (72.7 \times 0.30) = 83.6 \rightarrow \mathbf{84/100}$$
22. **Risk Classification:** Evaluated as **Critical** ($\ge 70$, color: `#ef4444`). Trace Step 9 is recorded.
23. **Markdown Synthesis:** Constructs the structured Markdown report with signal tables, financial status, resource allocation, and active work items.
24. **HTML Report Generation:** Calls `generate_html_report()` to create a standalone styled HTML report in `reports/`. Trace Step 10 is recorded.

---

### Step 9: Delivery & Visualization (Frontend Web App)
25. **JSON Payload Delivery:** FastAPI returns the complete response containing `report`, `agent_trace` (10 steps), `risk_score`, `risk_status`, and `sources_used`.
26. **Trace Animation:** The UI animates each of the 10 execution steps with real elapsed execution times.
27. **Report Rendering:** Formats markdown with marked.js, displays the Critical risk badge, renders data source attribution pills, and provides an **"Export HTML Report"** download button.
