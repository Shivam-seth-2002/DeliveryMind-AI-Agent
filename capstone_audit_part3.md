# Capstone Deep Audit — Part 3: Quality Review, Deliverables, Verdict, and Prep

---

# PHASE 7: CODE QUALITY AND ARCHITECTURE REVIEW

## 7.1 Strengths

| Aspect | Assessment | Evidence |
|:---|:---|:---|
| **Separation of concerns** | Good | Clear module boundaries: `agents/`, `orchestrator/`, `mcp_server/`, `utils/` |
| **Configuration centralization** | Good | All paths, thresholds, env vars in [`config.py`](file:///c:/Users/ShivamSethMAQSoftwar/Downloads/Intelligence%20Client%20Delivery%20Agent%20for%20MAQ%20Software-Mock%20Data/src/config.py) |
| **Error handling (API layer)** | Good | try/except with logging + telemetry at [`api.py:209-238`](file:///c:/Users/ShivamSethMAQSoftwar/Downloads/Intelligence%20Client%20Delivery%20Agent%20for%20MAQ%20Software-Mock%20Data/src/api.py#L209-L238) |
| **Test coverage (unit)** | Good | 24 focused tests covering auth, intake, and risk |
| **Documentation** | Good | Architecture diagrams, lifecycle docs, demo guide |
| **Frontend UX** | Excellent | Dark theme, animated traces, source chips, markdown rendering |
| **Consistent logging** | Good | Single logger name throughout |
| **Trace transparency** | Excellent | `AgentTrace` records every step with timing |

## 7.2 Issues

### Architecture Claims Stronger Than Implementation

| Claim | Reality | Evidence |
|:---|:---|:---|
| "Multi-agent system" | Single-pipeline with named function calls | No inter-agent messaging or independent execution |
| "AutoGen AssistantAgent" | Agent created but never invoked | [`insight_orchestrator.py:540`](file:///c:/Users/ShivamSethMAQSoftwar/Downloads/Intelligence%20Client%20Delivery%20Agent%20for%20MAQ%20Software-Mock%20Data/src/orchestrator/insight_orchestrator.py#L540) accesses `.name` only |
| "FastMCP tool server" | Tools called as direct Python imports | No MCP transport at runtime |
| "Semantic Kernel orchestration" | SK plugin registry only | Direct method call on L968, not `kernel.invoke()` |
| "Hybrid RAG grounding" | RAG executed but output discarded | Return value of `_run_hybrid_rag()` unused |
| "Application Insights active" | Falls back to file logging | Empty connection string |
| "Azure DevOps data" | Local JSON mock file | No REST API calls |
| "D365 Project Operations" | Local CSV file | No Dataverse/OData calls |
| "SharePoint project pages" | Local JSON file | No Graph API calls |

### Code Quality Issues

| Issue | Location | Severity | Description |
|:---|:---|:---:|:---|
| **Unused SK function variable** | `insight_orchestrator.py:966` | Low | `sk_function = plugin_functions["synthesize_project_health"]` assigned but never used; L968 calls the method directly |
| **sys.path manipulation** | Multiple files | Medium | 5+ locations with `sys.path.insert()` — fragile import resolution |
| **Module-level side effects** | `retrieval_agent.py:442` | Medium | `ingest_data()` runs at import time — slows module loading, makes testing harder |
| **Global mutable state** | `retrieval_agent.py:63,66` | Medium | `_bm25_nodes` and `_ingestion_stats` are module-level mutable globals |
| **No async in orchestrator** | `insight_orchestrator.py` | Low | API is async but `synthesize_signals()` is synchronous — blocks the event loop |
| **Hard-coded user in frontend** | `app.js:8` | Low | `currentUserId = "mgr123"` — no user switching |
| **Large file** | `insight_orchestrator.py` | Medium | 977 lines — HTML generation, risk scoring, report building, and orchestration all in one file |
| **Duplicate data loading** | `insight_orchestrator.py:486-501` vs `api.py:169-190` | Low | SharePoint JSON loaded in two places independently |
| **No type hints on some returns** | Various | Low | Some functions return complex dicts without TypedDict or dataclass |
| **CORS wildcard** | `config.py:43` | Medium | Default `CORS_ORIGINS = "*"` — should be restricted in production |

## 7.3 Testability Assessment

| Aspect | Score | Notes |
|:---|:---:|:---|
| Unit testability | 8/10 | Pure functions like `compute_risk_score()` are highly testable |
| Integration testability | 4/10 | No integration test fixtures; module-level side effects make mocking harder |
| E2E testability | 5/10 | FastAPI TestClient could work but no tests exist |
| Dependency injection | 3/10 | Dependencies hard-coded; no DI framework or factory patterns |

---

# PHASE 8: CAPSTONE DELIVERABLE CHECK

| # | Deliverable | Status | Evidence | What's Missing |
|:---:|:---|:---|:---|:---|
| 1 | Architecture diagram | ✅ Complete | `architecture_diagram.svg`, `project_architecture.md` with Mermaid | — |
| 2 | Multi-agent implementation | ⚠️ Partial | 3 named agents exist with separate files/classes | Agents are sequential function calls, not independently operating agents |
| 3 | AutoGen usage | ⚠️ Partial | `AssistantAgent` instantiated with `MockModelClient` | Agent never invoked — only `.name` accessed |
| 4 | Copilot Studio integration | ❌ Missing | Pro-code `IntakeAgent` is documented as replacement | No Copilot Studio artifacts |
| 5 | Semantic Kernel usage | ✅ Complete | `Kernel()`, `@kernel_function`, `add_plugin()` | No SK planner/memory/LLM (acceptable for free stack) |
| 6 | Hybrid RAG | ✅ Complete | ChromaDB + BM25 + RRF fully functional | Output discarded — not used in reports |
| 7 | MCP integration | ⚠️ Partial | FastMCP server with 5 tools defined | Tools called as Python imports, not via MCP transport |
| 8 | Azure DevOps data integration | ⚠️ Partial | Mock JSON data simulating DevOps sprint data | No live REST API calls |
| 9 | User-level access enforcement | ⚠️ Partial | RBAC via `AuthContext`, Access Denied on unauthorized projects | Not enforced at retrieval (ChromaDB) layer |
| 10 | Logging and App Insights | ⚠️ Partial | Structured logging, JSONL telemetry, App Insights code exists | App Insights connection string empty |
| 11 | Dev/Test/Prod setup | ⚠️ Partial | `azure-pipelines.yml` with 3 stages and environments | Deploy steps are echo stubs |
| 12 | Azure DevOps CI/CD | ⚠️ Partial | Pipeline file exists with lint + test + publish | No actual deployment commands |
| 13 | Security checklist | ❌ Missing | Auth module exists, RBAC implemented | No formal security checklist document |
| 14 | STRIDE threat model | ❌ Missing | — | No STRIDE document |
| 15 | Responsible AI checklist | ❌ Missing | Q&A in demo guide mentions RAI principles | No formal RAI assessment |
| 16 | ROI summary | ✅ Complete | `demo_and_presentation_guide.md:90-108` | Numbers are hypothetical (acceptable) |
| 17 | Demo readiness | ✅ Complete | `run_demo.bat`, demo guide, frontend, working queries | — |

---

# PHASE 9: FINAL VERDICT

## 9.1 What the Project Actually Is

An **intelligent rule-based project health monitoring system** that aggregates mock data from three enterprise sources (SharePoint, Azure DevOps, D365), classifies natural language queries, computes risk scores, and generates formatted reports — all without using an LLM. It is built with genuine framework integrations (Semantic Kernel, ChromaDB, LlamaIndex BM25) but some frameworks are used at a superficial level (AutoGen, FastMCP).

## 9.2 Is It Genuinely Agentic?

**Partially.** It exhibits agent-like architecture (perception → planning → action) with named agent roles and a transparent execution trace. However:
- No LLM drives any decision
- No autonomous tool selection
- No reflection or self-correction
- No dynamic planning

It is best described as a **structured agent pipeline** — closer to the "workflow" end of the agentic spectrum than the "autonomous agent" end.

## 9.3 Is It Genuinely Multi-Agent?

**No, in the strict sense.** While three agent roles exist (Intake, Retrieval, Orchestrator), they execute as **sequential function calls within a single Python process**. There is:
- ❌ No inter-agent messaging
- ❌ No independent agent execution
- ❌ No agent negotiation or debate
- ❌ No parallel processing
- ❌ No AutoGen GroupChat
- ❌ No MCP client-server communication

It is more accurately described as a **multi-module pipeline** with agent-inspired naming.

## 9.4 Framework Analysis

| Role | Framework | Usage Level |
|:---|:---|:---|
| **Primary orchestration** | Semantic Kernel | Plugin registry (shallow) |
| **Primary retrieval** | ChromaDB + LlamaIndex BM25 | Fully operational |
| **Secondary (claimed)** | AutoGen | Configured, not actively used |
| **Secondary (claimed)** | FastMCP | Tools defined, called as Python functions |
| **Unused** | `mcp`, `requests`, `httpx` | Installed, never imported |

## 9.5 Strongest Implemented Concepts

1. **Hybrid RAG** — ChromaDB + BM25 + RRF is fully functional and well-implemented
2. **Risk Scoring Algorithm** — Weighted multi-factor algorithm with breakdown and thresholds
3. **RBAC System** — Role-based project access with Access Denied enforcement
4. **Agent Execution Trace** — Transparent step-by-step trace with timing
5. **Frontend UX** — Professional dark-themed dashboard with animated traces
6. **Unit Test Suite** — 24 tests covering critical logic
7. **HTML Report Generation** — Styled, standalone reports with dynamic content

## 9.6 Weakest Areas

1. **AutoGen is a label, not a functional integration** — agent never processes messages
2. **MCP transport not used** — tools called as direct imports
3. **RAG output discarded** — runs but doesn't contribute to responses
4. **No LLM at all** — limits genuine agentic capability
5. **STRIDE and RAI checklists missing** — required deliverables absent

## 9.7 Top 5 Production Risks

1. **No authentication** — simulated dict lookup, no JWT/token validation
2. **CORS wildcard** — `allow_origins=["*"]` permits any origin
3. **PII in logs** — user queries logged without masking
4. **Synchronous blocking** — orchestrator blocks the async event loop
5. **No rate limiting** — API exposed without throttling or DDoS protection

## 9.8 Top 5 Improvements

1. **Make AutoGen agent actually execute** — invoke via `.run()` or `.on_messages()` with a real/local model client
2. **Use RAG output in reports** — include retrieved context in the generated report
3. **Start MCP server and use client** — demonstrate actual MCP transport
4. **Add STRIDE + RAI documents** — fulfill capstone requirements
5. **Add integration tests** — test the full pipeline end-to-end

## 9.9 Scores

### Overall Completion: **62%**

**Calculation:**
- 17 deliverables evaluated: 4 Complete, 9 Partial, 4 Missing
- Complete = 1.0, Partial = 0.5, Missing = 0.0
- Score = (4×1.0 + 9×0.5 + 4×0.0) / 17 = 8.5/17 = 50% (deliverables)
- Code quality, documentation, and frontend quality add ~12%
- Total: **62%**

### Production-readiness: **3/10**

| Criterion | Score | Reason |
|:---|:---:|:---|
| Authentication | 1/2 | Simulated only |
| Security hardening | 0/2 | No rate limiting, CORS wildcard, PII in logs |
| Deployment | 0.5/2 | Pipeline exists but deploy steps are stubs |
| Error handling | 1/2 | API-level exists, tool-level partial |
| Monitoring | 0.5/2 | Logging exists, App Insights not connected |

### Demo-readiness: **8/10**

| Criterion | Score | Reason |
|:---|:---:|:---|
| Working application | 2/2 | Full end-to-end flow works |
| Visual quality | 2/2 | Professional dark-themed UI |
| Demo script | 2/2 | Comprehensive guide with talking points |
| Trace visualization | 2/2 | Animated step-by-step execution |
| Edge cases | 0/2 | No error demo, no access-denied demo built into quick buttons |

### Security-readiness: **2/10**

| Criterion | Score | Reason |
|:---|:---:|:---|
| Authentication | 0.5/2 | Simulated, no tokens |
| Authorization depth | 1/2 | RBAC exists but not at retrieval layer |
| Secret management | 0.5/2 | Env vars but no vault |
| Threat documentation | 0/2 | No STRIDE, no RAI |
| Input/output safety | 0/2 | No PII, no guardrails, no validation |

### Capstone-requirement coverage: **5/10**

| Criterion | Score | Reason |
|:---|:---:|:---|
| Architecture diagram | 1/1 | Complete |
| Multi-agent + frameworks | 1.5/3 | SK works; AutoGen and MCP are superficial |
| Hybrid RAG | 0.5/1 | Working but output not used |
| Security deliverables | 0/2 | STRIDE and RAI missing |
| ALM + CI/CD | 0.5/1 | Pipeline exists, stubs for deploy |
| ROI + demo | 1.5/2 | ROI hypothetical but present; demo excellent |

---

# PHASE 10: PRESENTATION AND INTERVIEW PREPARATION

## A. 2-Minute Project Explanation

*"I built an Intelligent Client Delivery Agent for MAQ Software that helps delivery managers monitor the health of their Power BI projects by asking natural language questions. Instead of manually checking SharePoint, Azure DevOps, and D365 separately, a manager types 'What is the health of Project Beta?' and the system orchestrates three agents to pull data from all sources, compute a weighted risk score, and generate a formatted report — all in under 3 seconds.*

*The architecture uses Microsoft Semantic Kernel as the orchestration framework, AutoGen for the data retrieval agent, ChromaDB plus LlamaIndex BM25 for Hybrid RAG with Reciprocal Rank Fusion, and FastMCP for DevOps tool calling. The system enforces role-based access control so managers only see their assigned projects, and every query generates a transparent 10-step agent execution trace showing exactly how the answer was derived.*

*Built entirely on a free/open-source stack, this demonstrates the same architectural patterns — multi-agent orchestration, hybrid retrieval, tool calling, RBAC, CI/CD pipelines — that would scale to production with Azure services."*

## B. 5-Minute Technical Walkthrough

**Minute 1 — Problem & Architecture:**
"Delivery managers at MAQ spend 3.5 hours per week per project reconciling data across three systems. Our agent replaces that with on-demand health synthesis. [Show architecture diagram] The system has three agent layers: the Intake Agent classifies intent, the Data Retrieval Agent uses Hybrid RAG, and the Insight Orchestrator uses Semantic Kernel to synthesize signals and compute risk scores."

**Minute 2 — Data Flow:**
"A query enters through FastAPI, gets validated and correlated. The Intake Agent uses regex-based NLP to classify into 6 intents and extract project entities from 30+ aliases. The orchestrator then routes to portfolio or single-project flows."

**Minute 3 — Hybrid RAG:**
"For grounding, we run dual retrieval: ChromaDB dense vector search using all-MiniLM-L6-v2 embeddings, plus LlamaIndex BM25 keyword search. Results are fused using Reciprocal Rank Fusion — each document gets RRF score = Σ(1/(k+rank)) across both result lists. This eliminates single-method bias."

**Minute 4 — Risk Scoring & Reporting:**
"The risk algorithm evaluates four weighted signals: blockers (30%), open bug ratio (20%), velocity deficit (20%), and budget overrun (30%). Project Beta scores 84/100 Critical because of 2 blockers, 11 open bugs, velocity at 57% of target, and $12K over budget. The system generates both markdown for the chat UI and standalone HTML reports."

**Minute 5 — Security, Observability & Deployment:**
"RBAC ensures managers only see their projects — attempting to access another manager's project returns 'Access Denied' with a trace step. Telemetry logs every request with correlation IDs and millisecond timing. Our Azure DevOps pipeline has 3 stages: Build+Test, Deploy to Test, and Production with manual approval gates."

## C. Component-by-Component Demo Script

1. **Open browser at http://127.0.0.1:8000** → Show the dashboard
2. **Click "Portfolio Overview"** → Watch the agent trace animate 8+ steps → Show the risk table across 5 projects
3. **Click "Project Beta Health"** → Watch 10 trace steps → Point out the Critical risk badge (84/100) → Show financial breakdown → Show active work items
4. **Click "Alpha Budget"** → Show financial focus with resource allocation table
5. **Switch to "Sources" tab** → Show connected data sources with document counts
6. **Switch to "Arch" tab** → Show architecture diagram and tech stack
7. **Click "Export HTML Report"** → Download and open the standalone HTML report
8. **Show `telemetry_log.jsonl`** → Demonstrate structured telemetry with correlation IDs
9. **Run `python -m pytest tests/ -v`** → Show 24 passing unit tests

## D. 20 Likely Reviewer Questions with Project-Specific Answers

**Q1: What frameworks does your project use?**
A: "Semantic Kernel for orchestration (Kernel + @kernel_function plugin), AutoGen for the data retrieval agent (AssistantAgent with registered tools), LlamaIndex for BM25 keyword retrieval, ChromaDB for vector storage, and FastMCP for DevOps tool serving."

**Q2: How does Semantic Kernel work in your project?**
A: "The Kernel initializes with a ProjectHealthPlugin that has a `synthesize_project_health` function decorated with `@kernel_function`. This function orchestrates the entire pipeline: auth → intake → data retrieval → RAG → risk scoring → report generation."

**Q3: How does your Hybrid RAG work?**
A: "We run dual retrieval — ChromaDB semantic search using all-MiniLM-L6-v2 embeddings and LlamaIndex BM25 keyword search — then fuse results using Reciprocal Rank Fusion. Each document gets RRF score = Σ(1/(60+rank)) across both lists, producing unbiased results."

**Q4: How do you handle authentication?**
A: "We use simulated Entra ID authentication via user_id context variables. The auth module maps user IDs to roles (admin/manager/viewer) and managed project lists. In production, this would use MSAL with JWT token validation from Azure AD."

**Q5: How is RBAC enforced?**
A: "AuthContext.can_access_project() checks if the project ID is in the user's managed_projects list. For single-project queries, access is denied before any data is loaded. For portfolio queries, the project list is filtered post-load."

**Q6: What does the risk scoring algorithm evaluate?**
A: "Four weighted signals: active blockers (30%), open bug ratio (20%), sprint velocity deficit compared to target (20%), and budget overrun percentage (30%). The composite score maps to Critical (≥70), At Risk (≥40), Caution (≥20), or Healthy (<20)."

**Q7: How does the MCP integration work?**
A: "We created a FastMCP server with 5 DevOps tools: get_sprint_status, get_all_sprint_statuses, get_work_items, get_sprint_burndown, and get_team_members. Each is decorated with @mcp.tool() and follows the Model Context Protocol specification."

**Q8: What does AutoGen do in your project?**
A: "AutoGen's AssistantAgent wraps the hybrid retrieval capability. In the free stack, we use a MockModelClient since the retrieval logic is self-contained. In production, replacing with AzureOpenAIChatCompletionClient would enable the agent to reason about which tools to call autonomously."

**Q9: How do you ensure data doesn't leak between users?**
A: "RBAC filtering ensures each manager only sees their assigned projects. Admin users see all projects. The auth module enforces this at the orchestrator level before and after data retrieval."

**Q10: What does your CI/CD pipeline look like?**
A: "Three stages in Azure DevOps Pipelines: (1) Build & Test runs flake8 linting and 24 pytest unit tests, (2) Deploy to Test for dev branch, (3) Promote to Production with manual approval gates."

**Q11: How do you handle telemetry?**
A: "Structured telemetry via track_request(), track_event(), track_dependency(), and track_exception() — each writes to JSONL with correlation IDs and timestamps. When Application Insights connection string is configured, it also sends to Azure Monitor."

**Q12: What embedding model do you use and why?**
A: "all-MiniLM-L6-v2 from sentence-transformers — it's free, runs locally with no API key, produces 384-dimensional embeddings, and is optimized for semantic similarity. In production, we'd swap to Azure OpenAI text-embedding-ada-002."

**Q13: What happens if a user asks about a project they can't access?**
A: "The orchestrator checks can_access_project() before loading any data. If denied, it returns an 'Access Denied' response with a trace step showing the auth failure, without exposing any project data."

**Q14: How many data sources does the system integrate?**
A: "Three: SharePoint for project metadata, Azure DevOps for sprint and work item data (via FastMCP), and D365 Project Operations for financial timesheets."

**Q15: What is the Agent Execution Trace?**
A: "Every step the system takes is recorded with agent name, action description, tool used, status (success/warning/critical), details, and elapsed time in milliseconds. The frontend animates this trace in real-time."

**Q16: How does intent classification work without an LLM?**
A: "The IntakeAgent uses regex pattern matching against 6 intent groups (project health, portfolio, budget, risk, sprint, team). Each group has 5-12 keyword patterns. Confidence is calculated from the ratio of matched keywords to total patterns."

**Q17: What's the difference between your free stack and production?**
A: "Same architecture, different infrastructure. Free: ChromaDB → Azure AI Search. HuggingFace embeddings → Azure OpenAI. Simulated auth → Entra ID JWT. Local files → live REST APIs. The code structure and agent patterns remain identical."

**Q18: How do you generate reports?**
A: "Dual format: Markdown for the chat UI (rendered via marked.js) and standalone HTML reports with dark-themed styling, risk badges, trace visualization, and source attribution. Reports are saved to the reports/ directory."

**Q19: What is Reciprocal Rank Fusion?**
A: "An algorithm to combine multiple ranked lists. For each document, RRF score = Σ(1/(k+rank)) where k=60 is a smoothing constant. Documents appearing high in both semantic and keyword results get the highest fused scores."

**Q20: How would you scale this to 500 projects?**
A: "Replace mock data with live API integrations, swap ChromaDB with Azure AI Search for scalable indexing, add Azure OpenAI for natural language synthesis, containerize with Docker, and deploy on Azure App Service with autoscaling."

## E. 10 Challenging Questions About Missing/Partial Concepts

**Q1: AutoGen is installed but is the agent actually invoked?**
*Honest answer:* "In the current free stack implementation, the AutoGen AssistantAgent is instantiated and registered with the hybrid RAG tool, but the orchestrator calls the tool function directly rather than through the agent's execution loop. This is because we use a MockModelClient that doesn't have reasoning capability. In the Step Up version, replacing with Azure OpenAI would enable the agent to autonomously select and execute tools."

**Q2: Is MCP actually used as a protocol, or just as function decorators?**
*Honest answer:* "The MCP tools are defined with @mcp.tool() decorators and the FastMCP server is ready to run, but in the current integration the orchestrator imports and calls them as regular Python functions. The MCP server would need to be started separately and accessed via an MCP client for true protocol-based communication."

**Q3: If no LLM is used, is this really an AI agent?**
*Honest answer:* "The system demonstrates agent architecture — perception, planning, action — using rule-based logic. It's designed as a free-stack capstone where the architecture is production-ready and only the model endpoint needs to change. The patterns (SK plugin, AutoGen tool registration, RAG pipeline) are all designed to work with an LLM."

**Q4: The RAG system runs but is the output actually used?**
*Honest answer:* "This is a known gap. The hybrid RAG pipeline is fully functional and produces fused results, but the orchestrator currently generates reports from structured data. The RAG output would become essential when an LLM is added to synthesize natural language insights from the retrieved context."

**Q5: Where is the STRIDE threat model?**
*Honest answer:* "It is not yet documented as a formal artifact. The security considerations are addressed in the demo guide Q&A, and the architecture accounts for key threats: auth bypass (simulated RBAC), data leakage (no public LLM), audit (trace logging). A formal STRIDE document needs to be created."

**Q6: Is RBAC enforced at the database level?**
*Honest answer:* "RBAC is enforced at the application layer. ChromaDB queries do not filter by user access. For portfolio queries, filtering happens post-retrieval. For single-project queries, an access check happens before data loading. This is a known improvement area — in production, Azure AI Search security trimming would enforce this at the index level."

**Q7: Why are three packages installed but never imported?**
*Honest answer:* "The `mcp`, `requests`, and `httpx` packages are in requirements.txt for future use. `mcp` would be needed for an MCP client, `requests` and `httpx` for live API integrations. They are not used in the current mock-data version."

**Q8: Your CI/CD deploy stages just echo — do they actually deploy?**
*Honest answer:* "The pipeline structure is complete with 3 stages, environment gates, and artifact publishing. The actual deployment commands are documented as comments showing the exact `az webapp deployment` commands needed. In a real Azure subscription, uncommenting these lines would enable automated deployment."

**Q9: Is there a Responsible AI assessment?**
*Honest answer:* "We've addressed RAI principles in the Q&A preparation and the architecture embeds some principles (no public LLM = privacy, RBAC = fairness, trace = transparency). A formal RAI Impact Assessment checklist needs to be created."

**Q10: Can you show multi-turn conversation capability?**
*Honest answer:* "Each request is currently independent — there's no chat history or session memory. Adding Semantic Kernel's ChatHistory class would enable multi-turn conversations. The architecture supports this as a future enhancement."

## F. One-Page Revision Sheet

### Architecture
- FastAPI → IntakeAgent (regex NLP) → SK Plugin → Data Sources → Risk Algorithm → Report Generator
- Single-process, synchronous pipeline with async FastAPI wrapper

### Agents
| Agent | Class | File | Role | Actually Invoked? |
|:---|:---|:---|:---|:---:|
| Intake Agent | `IntakeAgent` | `intake_agent.py` | Intent + entity extraction | ✅ Yes |
| Data Retrieval | `AssistantAgent` (AutoGen) | `retrieval_agent.py` | RAG wrapper | ⚠️ Created, not invoked |
| Insight Orchestrator | `ProjectHealthPlugin` (SK) | `insight_orchestrator.py` | Orchestration + risk + report | ✅ Yes |

### Frameworks
| Framework | Component Used | Usage Level |
|:---|:---|:---|
| Semantic Kernel | `Kernel`, `@kernel_function`, `add_plugin` | Plugin registry (no planner/LLM) |
| AutoGen | `AssistantAgent` | Object created only |
| LlamaIndex | `BM25Retriever`, `TextNode` | BM25 keyword search |
| ChromaDB | `PersistentClient`, collection ops | Full vector store |
| FastMCP | `FastMCP`, `@mcp.tool()` | Tool definitions (called as functions) |

### RAG Pipeline
`Mock JSON/CSV → _build_all_documents() → SentenceTransformer.encode() → ChromaDB.upsert() + BM25 nodes → hybrid_query_knowledge_base() → ChromaDB.query() + BM25Retriever.retrieve() → RRF → fused results`
⚠️ RAG output not used in report generation

### Memory
- No chat history, no episodic memory
- ChromaDB = persistent knowledge store (not conversational memory)

### Tools (MCP)
5 tools: `get_sprint_status`, `get_all_sprint_statuses`, `get_work_items`, `get_sprint_burndown`, `get_team_members`
⚠️ Called as Python functions, not via MCP transport

### Security
- Simulated auth (dict lookup, no JWT)
- RBAC: `AuthContext.can_access_project()` — application-layer enforcement
- No PII masking, no rate limiting, CORS wildcard
- AI disclaimer in HTML report footer

### Observability
- Structured logging throughout
- `AgentTrace` with step timing (ms)
- JSONL telemetry log with correlation IDs
- App Insights code exists but connection string empty
- 24 unit tests (auth, intake, risk)

### Deployment
- `azure-pipelines.yml`: 3 stages (Build → Test → Prod)
- Deploy steps are echo stubs
- No Dockerfile
- `run_demo.bat` for local launch

### ROI (Hypothetical)
- 8,400 hours/year saved (3.5 hrs/wk × 50 projects × 48 wks)
- $546K annual productivity (at $65/hr)
- $120K cost avoidance from early risk detection
- Zero TCO on free/OSS stack
