# Capstone Deep Audit — Part 2: Evidence Matrix, Implemented Details, and Gap Analysis

---

# PHASE 4: EVIDENCE MATRIX

## A. Agent Foundations

| # | Concept | Status | Confidence | File Path | Class/Function/Config | Code Evidence | What It Does | Gap |
|:---:|:---|:---|:---:|:---|:---|:---|:---|:---|
| A1 | AI Agent vs LLM App | Conceptually Present | Medium | `src/orchestrator/` | Pipeline architecture | Rule-based agent pipeline, no LLM | Processes NL queries via agent roles | No LLM reasoning |
| A2 | Agentic-first architecture | Partially Implemented | Medium | `src/agents/`, `src/orchestrator/` | IntakeAgent, ProjectHealthPlugin | Named agent roles with traces | Structured agent pipeline | Fixed path, no autonomy |
| A3 | Perception→Plan→Act→Reflect | Partially Implemented | Medium | Multiple | IntakeAgent, synthesize_project_health | P→P→A present, no R | 3 of 4 loop stages | Missing Reflection |
| A4 | Autonomous vs Assistive | Fully Implemented | High | Entire system | — | Answers queries, generates reports | Assistive agent | By design |
| A5 | Single vs Multi-agent | Conceptually Present | High | `insight_orchestrator.py:534-554` | get_retrieval_agent() | Sequential function calls | Claims multi-agent; runtime is single pipeline | No independent agents |
| A6 | Agent maturity model | Not Implemented | High | — | — | — | — | Not documented |
| A7 | Stateless vs Stateful | Partially Implemented | High | — | — | Each request is independent | Stateless per request | No chat history |

## B. Reasoning and Planning

| # | Concept | Status | Confidence | File Path | Class/Function/Config | Code Evidence | What It Does | Gap |
|:---:|:---|:---|:---:|:---|:---|:---|:---|:---|
| B1 | Chain of Thought | Not Implemented | High | — | — | No LLM, no CoT prompts | — | No LLM |
| B2 | Tree of Thought | Not Implemented | High | — | — | — | — | — |
| B3 | Least-to-Most | Not Implemented | High | — | — | — | — | — |
| B4 | Workflow decomposition | Partially Implemented | High | `insight_orchestrator.py:450-484` | Intent routing switch | Routes by classified intent | Fixed pipeline routing | Not dynamic |
| B5 | Policy-constrained reasoning | Partially Implemented | Medium | `config.py:28-38` | Risk thresholds | Config-driven thresholds | Fixed policy parameters | No dynamic policies |
| B6 | Human-in-the-loop | Not Implemented | High | — | — | — | — | No approval gates |
| B7 | Reflection/self-correction | Not Implemented | High | — | — | — | — | No retry or quality check |

## C. Prompt Engineering and Safety

| # | Concept | Status | Confidence | File Path | Class/Function/Config | Code Evidence | What It Does | Gap |
|:---:|:---|:---|:---:|:---|:---|:---|:---|:---|
| C1 | System prompts | Not Implemented | High | — | — | No LLM | — | N/A without LLM |
| C2 | Context-aware prompts | Not Implemented | High | — | — | — | — | — |
| C3 | Query rewriting | Not Implemented | High | — | — | — | — | — |
| C4 | Prompt libraries | Not Implemented | High | — | — | — | — | — |
| C5 | Prompt versioning | Not Implemented | High | — | — | — | — | — |
| C6 | Language detection | Not Implemented | High | — | — | — | — | — |
| C7 | PII detection | Not Implemented | High | — | — | No Presidio, no masking | — | Queries logged in full |
| C8 | Prompt injection defense | Not Applicable | High | — | — | No LLM target | — | Would need if LLM added |
| C9 | Fallback strategies | Partially Implemented | High | `intake_agent.py:229-231`, `auth.py:128` | Intent fallback, unknown user | Unknown → portfolio, unknown user → viewer | Graceful degradation | Limited to 2 fallbacks |
| C10 | Input validation | Partially Implemented | High | `api.py:65-72` | QueryRequest BaseModel | Pydantic validates structure | Schema validation | No content validation |
| C11 | Output validation | Not Implemented | High | — | — | — | — | — |
| C12 | Guardrails | Not Implemented | High | — | — | — | — | — |

## D. Frameworks

| # | Concept | Status | Confidence | File Path | Class/Function/Config | Code Evidence | What It Does | Gap |
|:---:|:---|:---|:---:|:---|:---|:---|:---|:---|
| D1 | Semantic Kernel | Fully Implemented | High | `insight_orchestrator.py:25-26,951-968` | Kernel, @kernel_function, add_plugin | Plugin registered, function decorated | Orchestration framework | No SK planner/memory/LLM |
| D2 | AutoGen | Configured but Not Used | High | `retrieval_agent.py:418-437` | AssistantAgent, MockModelClient | Agent created, .name accessed, never invoked | Label only | Agent never processes messages |
| D3 | LangChain | Not Implemented | High | — | — | — | — | — |
| D4 | LangGraph | Not Implemented | High | — | — | — | — | — |
| D5 | CrewAI | Not Implemented | High | — | — | — | — | — |
| D6 | LlamaIndex | Partially Implemented | High | `retrieval_agent.py:28-34,286-290` | BM25Retriever, TextNode | BM25 search executed | Keyword retrieval only | No LI indices or engines |
| D7 | Copilot Studio | Not Implemented | High | — | — | Pro-code replacement | — | Documented as Step Up |
| D8 | Foundry agents | Not Implemented | High | — | — | — | — | — |

## E. Memory

| # | Concept | Status | Confidence | File Path | Class/Function/Config | Code Evidence | What It Does | Gap |
|:---:|:---|:---|:---:|:---|:---|:---|:---|:---|
| E1 | Short-term memory | Not Implemented | High | — | — | — | — | No conversation buffer |
| E2 | Long-term memory | Not Implemented | High | — | — | — | — | — |
| E3 | Episodic memory | Not Implemented | High | — | — | — | — | — |
| E4 | Semantic memory | Partially Implemented | Medium | `retrieval_agent.py:59-60` | ChromaDB collection | Persisted document embeddings | Knowledge store (not conversational) | Not user-specific |
| E5 | Chat history | Not Implemented | High | — | — | — | — | — |

## F. RAG and Retrieval

| # | Concept | Status | Confidence | File Path | Class/Function/Config | Code Evidence | What It Does | Gap |
|:---:|:---|:---|:---:|:---|:---|:---|:---|:---|
| F1 | Document ingestion | Fully Implemented | High | `retrieval_agent.py:188-236` | ingest_data() | Auto-runs at import | Loads + embeds all data sources | — |
| F2 | Chunking | Partially Implemented | Medium | `retrieval_agent.py:75-185` | _build_all_documents() | One record = one chunk | Works for small data | No splitter for large docs |
| F3 | Embedding model | Fully Implemented | High | `retrieval_agent.py:56` | SentenceTransformer("all-MiniLM-L6-v2") | .encode() at ingest + query | Dense vector generation | — |
| F4 | ChromaDB | Fully Implemented | High | `retrieval_agent.py:59-60,205-210` | PersistentClient, .upsert(), .query() | Full read/write cycle | Vector similarity search | — |
| F5 | BM25 keyword search | Fully Implemented | High | `retrieval_agent.py:279-302` | BM25Retriever.from_defaults() | .retrieve() called | Sparse keyword matching | — |
| F6 | Hybrid RAG (RRF) | Fully Implemented | High | `retrieval_agent.py:305-367` | _reciprocal_rank_fusion() | RRF formula implemented | Fuses semantic + keyword | — |
| F7 | Metadata filters | Partially Implemented | High | `retrieval_agent.py:255-262` | where_filter in .query() | Source-level filter | Filter by data source | No user_id filter |
| F8 | Re-ranking | Not Implemented | High | — | — | — | — | No cross-encoder |
| F9 | Source citation | Partially Implemented | Medium | `insight_orchestrator.py:547,681` | sources_used list | System-level sources | Tracks which systems were used | Not document-level |
| F10 | Hallucination prevention | Fully Implemented | High | — | No LLM | Template-based output | Cannot hallucinate | By architectural choice |

## G. Tools, Plugins, and Actions

| # | Concept | Status | Confidence | File Path | Class/Function/Config | Code Evidence | What It Does | Gap |
|:---:|:---|:---|:---:|:---|:---|:---|:---|:---|
| G1 | Tool-calling | Partially Implemented | High | `devops_mcp.py:41-152` | 5 @mcp.tool() functions | Called as Python functions | Structured data access | Not dynamically selected |
| G2 | Tool schema (JSON) | Not Implemented | High | — | — | — | — | No JSON schemas |
| G3 | Error handling | Partially Implemented | High | `devops_mcp.py:57`, `insight_orchestrator.py:751` | Error JSON + default values | Graceful fallback | Handles missing project | No retry |
| G4 | Retry/timeout | Not Implemented | High | — | — | — | — | — |

## H. Multi-Agent Architecture

| # | Concept | Status | Confidence | File Path | Class/Function/Config | Code Evidence | What It Does | Gap |
|:---:|:---|:---|:---:|:---|:---|:---|:---|:---|
| H1 | Supervisor–Worker | Conceptually Present | Medium | `insight_orchestrator.py` | Orchestrator calls agents | Sequential function calls | Simulates supervision | Not true delegation |
| H2 | Agent isolation | Not Implemented | High | — | — | Shared process | — | — |
| H3 | Message passing | Not Implemented | High | — | — | — | — | — |
| H4 | Handoffs | Partially Implemented | Medium | `insight_orchestrator.py:437-447` | IntakeResult → Orchestrator | Return value as handoff | Data passes between stages | Not protocol-based |
| H5 | A2A protocol | Not Implemented | High | — | — | — | — | — |
| H6 | GroupChat | Not Implemented | High | — | — | — | — | — |

## I. MCP and A2A

| # | Concept | Status | Confidence | File Path | Class/Function/Config | Code Evidence | What It Does | Gap |
|:---:|:---|:---|:---:|:---|:---|:---|:---|:---|
| I1 | MCP server | Partially Implemented | High | `devops_mcp.py:27` | FastMCP("DevOpsServer") | Server created, tools decorated | MCP tool definitions | Not run during API requests |
| I2 | MCP client | Not Implemented | High | — | — | — | — | No client code |
| I3 | MCP transport | Not Implemented | High | — | — | No stdio/SSE/HTTP | — | Direct import instead |
| I4 | Tool discovery | Not Implemented | High | — | — | — | — | Hard-coded imports |
| I5 | A2A | Not Implemented | High | — | — | — | — | — |

## J–K. Model Routing & Enterprise Integrations

| # | Concept | Status | Confidence | Evidence | Gap |
|:---:|:---|:---|:---:|:---|:---|
| J1 | Model router | Not Implemented | High | No LLM used | — |
| K1 | Teams | Not Implemented | High | Mentioned Step Up | — |
| K2 | SharePoint | Simulated (Mock) | High | mock_sharepoint.json | Not live API |
| K3 | Azure DevOps | Simulated (Mock) | High | mock_devops.json | Not REST API |
| K4 | D365 | Simulated (Mock) | High | mock_d365.csv | Not live API |
| K5 | Power Automate | Not Implemented | High | — | — |

## L. Security and Responsible AI

| # | Concept | Status | Confidence | File Path | Code Evidence | Gap |
|:---:|:---|:---|:---:|:---|:---|:---|
| L1 | Authentication | Simulated | High | `auth.py:95-134` | Dict lookup, no JWT | No real auth |
| L2 | RBAC | Partially Implemented | High | `auth.py:80-84`, `insight_orchestrator.py:703-718` | can_access_project(), Access Denied | Not at retrieval layer |
| L3 | user_id propagation | Partially Implemented | High | `app.js:8` → API → auth | Hard-coded mgr123 in frontend | — |
| L4 | Secret management | Partially Implemented | Medium | `config.py:47-49` | os.environ.get() | No Key Vault |
| L5 | AI disclaimer | Partially Implemented | Medium | `insight_orchestrator.py:374` | Footer text | Not on every response |
| L6 | STRIDE | Not Implemented | High | — | — | No document |
| L7 | RAI checklist | Documentation Only | Medium | `demo_and_presentation_guide.md` | Q&A answers only | No formal checklist |
| L8 | Audit trails | Partially Implemented | High | `telemetry.py`, AgentTrace | JSONL + trace steps | Not immutable |
| L9 | PII protection | Not Implemented | High | — | — | Queries logged raw |
| L10 | Least privilege | Partially Implemented | Medium | `auth.py` roles | Role-based access levels | No infra-level |

## M. Observability

| # | Concept | Status | Confidence | File Path | Code Evidence | Gap |
|:---:|:---|:---|:---:|:---|:---|:---|
| M1 | Logging | Fully Implemented | High | Throughout | logging.getLogger() | — |
| M2 | Tracing | Partially Implemented | High | `insight_orchestrator.py:66-92` | AgentTrace class | Not OpenTelemetry spans |
| M3 | App Insights | Configured not Used | High | `telemetry.py:78-89` | configure_azure_monitor() | Empty conn string |
| M4 | Latency | Fully Implemented | High | `api.py:77-89`, AgentTrace | elapsed_ms per step | — |
| M5 | Unit tests | Fully Implemented | High | `tests/` | 24 tests, 3 files | — |
| M6 | Integration tests | Not Implemented | High | — | — | — |
| M7 | Eval datasets | Not Implemented | High | — | — | — |

## N. Deployment

| # | Concept | Status | Confidence | File Path | Code Evidence | Gap |
|:---:|:---|:---|:---:|:---|:---|:---|
| N1 | CI/CD pipeline | Partially Implemented | High | `azure-pipelines.yml` | 3 stages defined | Deploy steps are echo stubs |
| N2 | Dev/Test/Prod | Partially Implemented | Medium | `azure-pipelines.yml:64-115` | Environment gates | No actual config separation |
| N3 | Containerization | Not Implemented | High | — | No Dockerfile | — |
| N4 | Approval gates | Partially Implemented | High | `azure-pipelines.yml:98` | environment: 'production' | Relies on ADO environment approval |

---

# PHASE 5: DETAILED EXPLANATION OF IMPLEMENTED CONCEPTS

## 5.1 Semantic Kernel Plugin Architecture

**Simple meaning:** Semantic Kernel is Microsoft's framework for building AI applications. A "plugin" is a collection of functions the AI kernel can call.

**Project-specific implementation:**
- A `Kernel()` is created at module level ([`insight_orchestrator.py:951`](file:///c:/Users/ShivamSethMAQSoftwar/Downloads/Intelligence%20Client%20Delivery%20Agent%20for%20MAQ%20Software-Mock%20Data/src/orchestrator/insight_orchestrator.py#L951))
- `ProjectHealthPlugin` class contains the core orchestration method `synthesize_project_health()` decorated with `@kernel_function` ([L406-409](file:///c:/Users/ShivamSethMAQSoftwar/Downloads/Intelligence%20Client%20Delivery%20Agent%20for%20MAQ%20Software-Mock%20Data/src/orchestrator/insight_orchestrator.py#L406-L409))
- The plugin is registered: `_kernel.add_plugin(_health_plugin, plugin_name="ProjectHealthPlugin")` ([L953](file:///c:/Users/ShivamSethMAQSoftwar/Downloads/Intelligence%20Client%20Delivery%20Agent%20for%20MAQ%20Software-Mock%20Data/src/orchestrator/insight_orchestrator.py#L953))

**Step-by-step internal working:**
1. `synthesize_signals()` is called from the API
2. It retrieves the plugin from the kernel: `_kernel.get_plugin("ProjectHealthPlugin")`
3. It calls the plugin method directly (not through `kernel.invoke()`)
4. Inside, it runs: Auth → Intake → Data Loading → RAG → Risk → Report

**Data flow:** `query + user_id` → `synthesize_project_health()` → `{agent_trace, report, risk_score, sources_used, html_report}`

**Current limitation:** SK is used as a plugin registry only. No SK planner, no SK memory connector, no LLM invocation through SK. The function is called directly on the Python object, not through the kernel's invocation mechanism.

**Demo explanation:** "We use Microsoft Semantic Kernel as our orchestration framework. The Insight Orchestrator is registered as a native SK plugin using the `@kernel_function` decorator. In the free stack, the kernel function contains all the orchestration logic. In the enterprise Step Up, this same plugin code would work with an Azure OpenAI model for natural language synthesis — only the KernelBuilder configuration changes."

---

## 5.2 Hybrid RAG with Reciprocal Rank Fusion

**Simple meaning:** Instead of relying on just one search method, we run two — one that understands meaning (semantic) and one that matches exact keywords (BM25) — then mathematically combine their results.

**Project-specific implementation:**
- **Semantic search:** ChromaDB with `all-MiniLM-L6-v2` embeddings
- **Keyword search:** LlamaIndex BM25Retriever
- **Fusion:** Reciprocal Rank Fusion (RRF) at [`retrieval_agent.py:305-332`](file:///c:/Users/ShivamSethMAQSoftwar/Downloads/Intelligence%20Client%20Delivery%20Agent%20for%20MAQ%20Software-Mock%20Data/src/agents/retrieval_agent.py#L305-L332)

**Step-by-step internal working:**
1. User query is encoded via `SentenceTransformer.encode()` → embedding vector
2. ChromaDB `.query()` returns top-k semantically similar documents with distances
3. Distances converted to similarity: `score = 1.0 / (1.0 + distance)` ([L272](file:///c:/Users/ShivamSethMAQSoftwar/Downloads/Intelligence%20Client%20Delivery%20Agent%20for%20MAQ%20Software-Mock%20Data/src/agents/retrieval_agent.py#L272))
4. BM25Retriever `.retrieve()` returns keyword-matched documents with scores
5. RRF assigns each document: `rrf_score += 1/(k + rank + 1)` for each result list where it appears (k=60)
6. Documents sorted by fused score descending
7. Top-k returned as concatenated text

**Dependencies:** `sentence-transformers`, `chromadb`, `llama-index-retrievers-bm25`, `llama-index-core`

**Failure behavior:** If BM25 is unavailable, falls back to semantic-only ([`retrieval_agent.py:281-283`](file:///c:/Users/ShivamSethMAQSoftwar/Downloads/Intelligence%20Client%20Delivery%20Agent%20for%20MAQ%20Software-Mock%20Data/src/agents/retrieval_agent.py#L281-L283)). If no results, returns "No relevant information found."

**Critical limitation:** The RAG output is **not used in report generation** — the orchestrator calls `_run_hybrid_rag()` but discards its return value. Reports are built from structured data.

**Demo explanation:** "Our Hybrid RAG combines dense vector search via ChromaDB with sparse keyword matching via LlamaIndex BM25, fused using Reciprocal Rank Fusion. This eliminates the bias of any single retrieval method — semantic search catches meaning while BM25 catches exact project IDs and technical terms."

---

## 5.3 Risk Scoring Algorithm

**Simple meaning:** A formula that takes four project signals and produces a 0-100 risk score, with "Critical", "At Risk", "Caution", or "Healthy" classifications.

**Project-specific implementation:** [`compute_risk_score()`](file:///c:/Users/ShivamSethMAQSoftwar/Downloads/Intelligence%20Client%20Delivery%20Agent%20for%20MAQ%20Software-Mock%20Data/src/orchestrator/insight_orchestrator.py#L99-L164)

**Step-by-step internal working:**
1. **Blocker score (30%):** Each blocker = 50 points, capped at 100. `min(100, blockers * 50)`
2. **Bug score (20%):** `(open_bugs / total_bugs_opened) * 100`, capped at 100
3. **Velocity score (20%):** `(1.0 - velocity/target) * 200`, capped at 100. 0 if on target.
4. **Budget score (30%):** `(overrun_ratio - 1.0) * 200`, capped at 100. 0 if within budget.
5. **Composite:** `Σ(component × weight)` → 0-100 score
6. **Classify:** ≥70 Critical, ≥40 At Risk, ≥20 Caution, <20 Healthy

**Demo explanation:** "The risk algorithm evaluates four weighted signals: active blockers (30%), open bug ratio (20%), sprint velocity deficit (20%), and budget overrun (30%). Project Beta scores 84/100 Critical because of 2 blockers, 11 open bugs, velocity at 20/35, and $12K over budget."

---

## 5.4 Simulated RBAC

**Simple meaning:** Users can only see projects they manage. Admins see everything.

**Project-specific implementation:** [`auth.py`](file:///c:/Users/ShivamSethMAQSoftwar/Downloads/Intelligence%20Client%20Delivery%20Agent%20for%20MAQ%20Software-Mock%20Data/src/utils/auth.py)

**Step-by-step internal working:**
1. `authenticate_user(user_id)` looks up `USER_REGISTRY` dict
2. Returns `AuthContext` with `role`, `managed_projects`, `is_authenticated`
3. Portfolio queries: `get_accessible_projects()` returns project list (or None for admin)
4. Single project: `can_access_project(pid)` checks membership
5. If denied: orchestrator returns "Access Denied" with trace step

**Security implication:** RBAC is enforced at the **application layer**, not at the data layer. ChromaDB queries return all documents regardless of user. The orchestrator filters results post-retrieval for portfolio queries, and pre-access for single project queries.

---

## 5.5 Intake Agent (Intent Classification)

**Simple meaning:** The first "agent" that reads the user's question, determines what they want (portfolio overview? specific project health? budget query?), and identifies which project they're asking about.

**Project-specific implementation:** [`IntakeAgent`](file:///c:/Users/ShivamSethMAQSoftwar/Downloads/Intelligence%20Client%20Delivery%20Agent%20for%20MAQ%20Software-Mock%20Data/src/agents/intake_agent.py#L175-L249)

**Step-by-step internal working:**
1. Query lowercased and stripped
2. **Entity extraction** ([L251-278](file:///c:/Users/ShivamSethMAQSoftwar/Downloads/Intelligence%20Client%20Delivery%20Agent%20for%20MAQ%20Software-Mock%20Data/src/agents/intake_agent.py#L251-L278)): 30+ aliases sorted by length, matched via regex word boundaries
3. **Intent classification** ([L280-320](file:///c:/Users/ShivamSethMAQSoftwar/Downloads/Intelligence%20Client%20Delivery%20Agent%20for%20MAQ%20Software-Mock%20Data/src/agents/intake_agent.py#L280-L320)): 6 pattern groups with 5-12 keyword regexes each, scored by match density
4. **Ambiguity resolution** ([L221-231](file:///c:/Users/ShivamSethMAQSoftwar/Downloads/Intelligence%20Client%20Delivery%20Agent%20for%20MAQ%20Software-Mock%20Data/src/agents/intake_agent.py#L221-L231)): If specific project found but portfolio intent → re-classify to project_health

**Demo explanation:** "The Intake Agent is our pro-code replacement for Copilot Studio Topics. It uses regex-based NLP to classify 6 query intents and extract project entities from 30+ aliases. 'What is the health of Project Beta?' → intent: `project_health`, project: `P-002`, confidence: 90%."

---

# PHASE 6: MISSING AND WEAKLY IMPLEMENTED CONCEPTS

## Priority 0: Security or Correctness Blockers

### P0-1: RAG Output Discarded
- **Current state:** `_run_hybrid_rag()` is called but its return value is never used in report generation
- **Why it matters:** The RAG system runs correctly but provides zero value to the output — wasted computation and misleading claims of "grounded" responses
- **Files:** [`insight_orchestrator.py:534-555`](file:///c:/Users/ShivamSethMAQSoftwar/Downloads/Intelligence%20Client%20Delivery%20Agent%20for%20MAQ%20Software-Mock%20Data/src/orchestrator/insight_orchestrator.py#L534-L555), [`605`](file:///c:/Users/ShivamSethMAQSoftwar/Downloads/Intelligence%20Client%20Delivery%20Agent%20for%20MAQ%20Software-Mock%20Data/src/orchestrator/insight_orchestrator.py#L605), [`825`](file:///c:/Users/ShivamSethMAQSoftwar/Downloads/Intelligence%20Client%20Delivery%20Agent%20for%20MAQ%20Software-Mock%20Data/src/orchestrator/insight_orchestrator.py#L825)
- **Fix:** Store `rag_context = self._run_hybrid_rag(...)` and include it in the report (e.g., "Additional context from knowledge base: ...")
- **Effort:** Small
- **Acceptance criteria:** RAG text appears in final report output

### P0-2: RBAC Not Enforced at Retrieval Layer
- **Current state:** ChromaDB queries do not filter by user_id/project_id. All documents are searchable by all users.
- **Why it matters:** A user could potentially see RAG results from projects they shouldn't access (if RAG results were used)
- **Files:** [`retrieval_agent.py:244-263`](file:///c:/Users/ShivamSethMAQSoftwar/Downloads/Intelligence%20Client%20Delivery%20Agent%20for%20MAQ%20Software-Mock%20Data/src/agents/retrieval_agent.py#L244-L263)
- **Fix:** Pass `auth_ctx.managed_projects` to `hybrid_query_knowledge_base()` and add `where={"projectId": {"$in": accessible_projects}}` to ChromaDB query
- **Effort:** Small
- **Risk:** Could reduce recall for admin users if not handled carefully
- **Acceptance criteria:** ChromaDB query includes project filter for non-admin users

### P0-3: PII in Logs
- **Current state:** User queries are logged in full to `telemetry_log.jsonl` and stdout with no PII masking
- **Why it matters:** Queries could contain sensitive project names, client names, or financial references
- **Fix:** Add basic PII scrubbing before logging (e.g., mask email patterns, numeric sequences)
- **Effort:** Medium
- **Acceptance criteria:** Telemetry logs do not contain raw user queries with identifiable information

## Priority 1: Required for Capstone Deliverables

### P1-1: AutoGen Not Actually Used
- **Current state:** `AssistantAgent` created but never invoked — `.name` accessed only
- **Why it matters:** Capstone deliverables require "Multi-agent system: AutoGen + Copilot Studio + SK"
- **Files:** [`retrieval_agent.py:402-437`](file:///c:/Users/ShivamSethMAQSoftwar/Downloads/Intelligence%20Client%20Delivery%20Agent%20for%20MAQ%20Software-Mock%20Data/src/agents/retrieval_agent.py#L402-L437), [`insight_orchestrator.py:536-554`](file:///c:/Users/ShivamSethMAQSoftwar/Downloads/Intelligence%20Client%20Delivery%20Agent%20for%20MAQ%20Software-Mock%20Data/src/orchestrator/insight_orchestrator.py#L536-L554)
- **Fix:** Actually invoke the AutoGen agent: `result = await retriever.run(task="Retrieve context for: {query}")`. This requires replacing `MockModelClient` with a real model client or wrapping the function to be called via the agent's tool mechanism.
- **Effort:** Medium
- **Risk:** Requires a model client (even a local one) or significant refactoring
- **Acceptance criteria:** AutoGen agent `.run()` or `.on_messages()` is called and returns results

### P1-2: MCP Transport Not Used
- **Current state:** MCP tools called as direct Python function imports, not via MCP protocol
- **Why it matters:** Capstone requires MCP integration demonstration
- **Files:** [`devops_mcp.py`](file:///c:/Users/ShivamSethMAQSoftwar/Downloads/Intelligence%20Client%20Delivery%20Agent%20for%20MAQ%20Software-Mock%20Data/src/mcp_server/devops_mcp.py), [`insight_orchestrator.py:34-37`](file:///c:/Users/ShivamSethMAQSoftwar/Downloads/Intelligence%20Client%20Delivery%20Agent%20for%20MAQ%20Software-Mock%20Data/src/orchestrator/insight_orchestrator.py#L34-L37)
- **Fix:** Start MCP server in a subprocess, create an MCP client in the orchestrator, and call tools via the protocol. Alternatively, use `fastmcp` client SDK.
- **Effort:** Medium-Large
- **Acceptance criteria:** Tools are called via MCP transport (stdio or HTTP), not direct import

### P1-3: STRIDE Threat Model Missing
- **Current state:** No STRIDE document exists
- **Why it matters:** Required capstone deliverable
- **Fix:** Create a STRIDE analysis document covering Spoofing (auth bypass), Tampering (data modification), Repudiation (no audit trail), Information Disclosure (RBAC gaps), DoS (no rate limiting), Elevation (role escalation)
- **Effort:** Small (documentation)
- **Acceptance criteria:** STRIDE document exists with threats and mitigations for each category

### P1-4: Responsible AI Checklist Missing
- **Current state:** Only Q&A in presentation guide
- **Fix:** Create formal checklist covering Fairness (tested for bias?), Reliability (error handling), Privacy (PII), Inclusiveness (accessibility), Transparency (AI disclaimer), Accountability (audit)
- **Effort:** Small
- **Acceptance criteria:** RAI checklist document with assessment per principle

### P1-5: Copilot Studio Integration Absent
- **Current state:** Pro-code replacement, no actual Copilot Studio artifacts
- **Why it matters:** Capstone deliverable lists "Copilot Studio"
- **Fix:** Document clearly that Intake Agent is the pro-code equivalent. Alternatively, if available, create a Copilot Studio topic that calls the `/api/query_project_health` endpoint.
- **Effort:** Large (if actually building) / Small (if documenting justification)

## Priority 2: Important Production-Readiness Improvements

### P2-1: No LLM Reasoning
- **Current state:** 100% rule-based; no generative AI
- **Why it matters:** Limits the system's ability to handle novel queries or provide insightful analysis
- **Fix:** Add an LLM (Ollama local, or Azure OpenAI) to synthesize the report from RAG context + structured data
- **Effort:** Medium
- **Acceptance criteria:** At least one LLM call generates part of the response

### P2-2: No Chat History / Stateful Conversations
- **Current state:** Each request is independent
- **Fix:** Add in-memory `ChatHistory` (SK provides this) keyed by user_id
- **Effort:** Small
- **Acceptance criteria:** Follow-up queries reference previous context

### P2-3: No Integration Tests
- **Current state:** Only unit tests
- **Fix:** Add `tests/test_integration.py` using `httpx.AsyncClient` to test the full FastAPI pipeline
- **Effort:** Small
- **Acceptance criteria:** Integration test calls `/api/query_project_health` and validates response structure

### P2-4: CI/CD Deploy Stages are Stubs
- **Current state:** `echo` commands replace actual `az webapp deployment` commands
- **Fix:** Uncomment or implement actual deployment commands (or document clearly that they're placeholders with exact Step Up instructions)
- **Effort:** Small (if documenting) / Medium (if implementing)

### P2-5: Hard-coded User ID in Frontend
- **Current state:** `const currentUserId = "mgr123"` ([`app.js:8`](file:///c:/Users/ShivamSethMAQSoftwar/Downloads/Intelligence%20Client%20Delivery%20Agent%20for%20MAQ%20Software-Mock%20Data/frontend/app.js#L8))
- **Fix:** Add a user selector dropdown or login simulation in the UI
- **Effort:** Small
- **Acceptance criteria:** Different users produce different access results

## Priority 3: Optional Enhancements

### P3-1: No Reflection or Self-correction
- **Fix:** Add a validation step after report generation that checks completeness
- **Effort:** Medium

### P3-2: No Query Rewriting/Expansion
- **Fix:** Normalize synonyms before passing to RAG
- **Effort:** Small

### P3-3: No Re-ranking
- **Fix:** Add a cross-encoder re-ranker after RRF fusion
- **Effort:** Medium

### P3-4: No Dockerfile
- **Fix:** Add a multi-stage Dockerfile for containerized deployment
- **Effort:** Small

### P3-5: `timed_dependency()` Context Manager Never Used
- **Fix:** Wrap ChromaDB and BM25 calls with `timed_dependency()` to get dependency timing telemetry
- **Effort:** Small
