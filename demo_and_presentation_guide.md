# 30-Minute Capstone Demo & Presentation Guide

This guide is designed for the 30-minute final evaluation of the **Intelligent Client Delivery Agent for MAQ Software**.

---

## ⏱️ Presentation Agenda (30 Minutes)

| Time | Agenda Item | Key Speaker Takeaways |
|:---:|:---|:---|
| **00:00 – 05:00** | **Executive Problem & Vision** | Manual project reporting across SharePoint, DevOps, and D365 is slow, fragmented, and prone to late risk detection. |
| **05:00 – 15:00** | **Live Interactive Query Demo** | Show the dashboard, execute portfolio and project queries, demonstrate live multi-agent execution traces, and download the HTML report. |
| **15:00 – 22:00** | **Technical Architecture Walkthrough** | Multi-agent collaboration (Intake, AutoGen, Semantic Kernel, FastMCP, ChromaDB + BM25 Hybrid RAG). Free stack vs. Step Up to Azure. |
| **22:00 – 26:00** | **Business Value & ROI Presentation** | Quantified hours saved per manager, cost avoidance from early blocker mitigation, and developer velocity acceleration. |
| **26:00 – 30:00** | **Security, Governance & Q&A** | Role-based data isolation, auditability, zero data leakage to public models, and enterprise Entra ID integration. |

---

## 🎯 Part 1: Live Demo Script & Query Flow (10 Minutes)

### Pre-Demo Checklist
1. Double-click `run_demo.bat` to launch the FastMCP server, run the 24 Pytest unit tests, and start FastAPI.
2. Open browser at `http://127.0.0.1:8000`.

### Demo Sequence
1. **Portfolio Health Overview:**
   - Click the **"Portfolio Overview"** chip or type:  
     `"What is the health of our active Power BI delivery projects?"`
   - **Talking Point:** *"Notice how the Intake Agent immediately classifies this as a portfolio inquiry, and the orchestrator aggregates data across all 5 delivery projects. You get a consolidated health table with risk scores, velocities, open bugs, and blockers."*

2. **Deep-Dive into an At-Risk Project (Project Beta):**
   - Click **"Project Beta Health"** or type:  
     `"What is the health of Project Beta?"`
   - **Talking Point:** *"Watch the live Agent Execution Trace. In 10 sequential, transparent steps, the Intake Agent classifies the intent, the Auth Service checks permissions, FastMCP queries Azure DevOps for bugs and blockers, D365 timesheets are pulled, and Hybrid RAG grounds the context. Project Beta is flagged as Critical (84/100) due to 2 blockers, 11 open bugs, low velocity (20/35), and a $12,000 budget overrun."*

3. **Financial & Timesheet Drilldown:**
   - Click **"Alpha Budget"** or type:  
     `"What is the budget and cost for Project Alpha?"`
   - **Talking Point:** *"The agent narrows its focus to D365 financial data, breaking down hours logged vs budgeted, and showing per-resource timesheets for developers and QA."*

4. **HTML Report Export:**
   - Scroll to the bottom of the Project Beta report and click **"Export HTML Report"**.
   - Open the downloaded file in the browser.
   - **Talking Point:** *"The system generates standalone, beautifully styled HTML delivery reports complete with timestamping, execution traces, and source attribution—ready to share with stakeholders."*

5. **Architecture Panel:**
   - Click the **"Arch"** tab in the sidebar navigation to display the live component flow and the Free Stack vs. Azure Step Up comparison.

---

## 🏗️ Part 2: Technical Architecture Walkthrough (7 Minutes)

### Core Agent Roster
1. **Intake Agent (Pro-Code NLP Classifier):**
   - **Role:** First line of contact for manager requests.
   - **Tech:** Pure Python NLP with regex keyword matching and entity extraction across 6 intents and 5 projects.
   - **Benefit:** 100% pro-code with zero low-code dependencies or subscription overhead.

2. **Data Retrieval Agent (AutoGen + Hybrid RAG):**
   - **Role:** Grounding agent that gathers truth from enterprise data sources.
   - **Tech:** AutoGen `AssistantAgent` paired with Hybrid RAG:
     - **ChromaDB:** Dense vector similarity using HuggingFace `all-MiniLM-L6-v2`.
     - **LlamaIndex BM25:** Sparse keyword search for exact project ID hits.
     - **Reciprocal Rank Fusion (RRF):** Merges both ranked lists to eliminate search bias.

3. **FastMCP Tool Server (Azure DevOps Integration):**
   - **Role:** Provides structured tool calling following the open Model Context Protocol (MCP).
   - **Tools:** 5 registered tools (`get_sprint_status`, `get_all_sprint_statuses`, `get_work_items`, `get_sprint_burndown`, `get_team_members`).

4. **Insight Orchestrator (Semantic Kernel):**
   - **Role:** Master brain synthesizing signals into decisions.
   - **Tech:** Microsoft Semantic Kernel native plugin with `@kernel_function`.
   - **Risk Algorithm:** Evaluates blockers (30%), open bug delta (20%), velocity deficit (20%), and budget overrun (30%).

### Free Stack vs. Enterprise Step Up

| Capability | Free / OSS Stack (Demonstrated) | Enterprise Step Up (Production) |
|:---|:---|:---|
| **Intake / Front Door** | Custom Web Dashboard + FastAPI | Teams Bot via Azure Bot Service |
| **Agent Framework** | AutoGen AssistantAgent (OSS) | Azure AI Foundry Agent Service |
| **Vector Store** | ChromaDB (Local SQLite) | Azure AI Search (Semantic Ranker) |
| **Embeddings** | HuggingFace `all-MiniLM-L6-v2` (Local) | Azure OpenAI `text-embedding-ada-002` |
| **DevOps Integration** | FastMCP Server (Local JSON export) | Azure DevOps REST API via Managed Identity |
| **Authentication** | Simulated `user_id` context variables | Microsoft Entra ID (Azure AD) + MSAL Bearer JWT |
| **Telemetry** | Application Insights Free Tier + JSONL | Azure Monitor + Log Analytics + Alerts |
| **CI/CD** | Azure DevOps Pipelines (3 stages) | Multi-region Blue/Green Deployment |

---

## 💰 Part 3: ROI Presentation & Business Value (4 Minutes)

### Quantified Metrics for a 50-Project Delivery Org (e.g., MAQ Software)

1. **Manager Time Reclaimed:**
   - **Before:** Delivery managers spend an average of **3.5 hours per week per project** manually reconciling SharePoint status pages, Azure DevOps sprint boards, and D365 timesheets to prepare status reports.
   - **With Agent:** On-demand health synthesis takes **< 5 seconds**.
   - **Annual Savings:** 3.5 hrs/wk × 50 projects × 48 weeks = **8,400 hours saved annually**.
   - **Financial Equivalent:** At $65/hr fully loaded manager cost = **$546,000 in annual productivity reclaimed**.

2. **Early Risk Mitigation & Cost Avoidance:**
   - **The Problem:** Project Beta ran $12,000 over budget and was blocked for 2 weeks before manual detection.
   - **With Agent:** Automated velocity deficit and blocker detection flags projects at day 3 of a sprint.
   - **Avoidance Value:** Mitigating just **2 critical project overruns per quarter** saves an estimated **$120,000+ annually** in rework and SLA penalty credits.

3. **Total Cost of Ownership (TCO):**
   - Built on a **100% Free / Open-Source Stack**, requiring zero upfront subscription licenses for evaluation.
   - Migration to Azure Step Up can be completed incrementally with zero architectural rewrites.

---

## 🛡️ Part 4: Security, Governance & Compliance Q&A (4 Minutes)

### Prepared Questions & Answers for Evaluators

**Q1: How does the system protect sensitive financial and client data?**
> **A:** The system enforces Role-Based Access Control (RBAC) at the authentication gateway (`src/utils/auth.py`). Managers are restricted strictly to their assigned projects (e.g., `mgr123` can only query P-001, P-002, and P-004). Attempting to query another manager's project generates an automatic "Access Denied" trace step without exposing any underlying financial or metadata records.

**Q2: Are company secrets or client data sent to public AI models?**
> **A:** No. In our demonstrated stack, all embeddings are generated locally using HuggingFace `all-MiniLM-L6-v2` running on the CPU, and vector search runs locally in ChromaDB. Zero client data leaves the secure perimeter. In the enterprise Step Up, data remains within MAQ Software's private Azure tenant with Customer-Managed Keys (CMK) and Virtual Network service endpoints.

**Q3: How is the agent auditable?**
> **A:** Every query generates a complete, immutable **Agent Execution Trace** recording each step, tool invoked, execution duration in milliseconds, and status. Furthermore, all requests, dependencies, and exceptions are logged with correlation IDs to Azure Application Insights and structured JSONL logs.

**Q4: How do we promote changes safely from Development to Production?**
> **A:** Our `azure-pipelines.yml` implements a 3-stage pipeline:
> 1. **Dev:** Runs Flake8 linting and 24 automated Pytest unit tests, then packages the artifact.
> 2. **Test:** Deploys to the test environment and runs automated smoke checks.
> 3. **Production:** Requires explicit manual approval and runs production health checks against `/api/health`.
