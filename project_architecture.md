# Intelligent Client Delivery Agent: Architecture & Deep Dive

This document contains the complete visual architecture and an in-depth technical breakdown of every component in the Intelligent Client Delivery Agent project.

## Architecture Diagram

```mermaid
flowchart TD
    %% Define Styles
    classDef frontend fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#fff
    classDef auth fill:#312e81,stroke:#6366f1,stroke-width:2px,color:#fff
    classDef intake fill:#065f46,stroke:#10b981,stroke-width:2px,color:#fff
    classDef orch fill:#4c1d95,stroke:#8b5cf6,stroke-width:2px,color:#fff
    classDef agents fill:#701a75,stroke:#ec4899,stroke-width:2px,color:#fff
    classDef mcp fill:#78350f,stroke:#f59e0b,stroke-width:2px,color:#fff
    classDef data fill:#0f172a,stroke:#64748b,stroke-width:2px,color:#fff
    classDef cicd fill:#881337,stroke:#f43f5e,stroke-width:2px,color:#fff

    %% User Interaction Layer
    subgraph UI ["User Interface Layer"]
        User(["👨‍💼 Delivery Manager"])
        WebApp["🌐 Web Dashboard (HTML5 / Vanilla CSS / JS)"]
    end
    class User,WebApp frontend

    %% Gateway & Auth Layer
    subgraph Gateway ["Gateway & Auth Layer"]
        FastAPI["⚡ FastAPI Web Server (Python)"]
        AuthService["🔐 Simulated Entra ID & RBAC (auth.py)"]
    end
    class FastAPI,AuthService auth

    %% Pro-Code Intake Layer
    subgraph Intake ["Agent 1: Intake Layer"]
        IntakeAgent["💬 Pro-Code Intake Agent (NLP Classifier)"]
    end
    class IntakeAgent intake

    %% Orchestration Layer
    subgraph Orchestrator ["Agent 3: Insight Orchestration"]
        SK["🧠 Semantic Kernel (Insight Orchestrator)"]
        RiskAlgo["📊 Weighted Risk Scoring Algorithm"]
        ReportGen["📋 Multi-Format Report Generator (MD + HTML)"]
    end
    class SK,RiskAlgo,ReportGen orch

    %% Multi-Agent & Tool Layer
    subgraph AgentsLayer ["Agent 2: Data Retrieval & MCP"]
        AutoGen["🤖 AutoGen AssistantAgent (Data Retriever)"]
        FastMCP["🔌 FastMCP DevOps Server (5 Tools)"]
    end
    class AutoGen agents
    class FastMCP mcp

    %% Data Retrieval & Knowledge Base
    subgraph Retrieval ["Hybrid RAG & Grounded Data Sources"]
        Chroma["🗄️ ChromaDB Vector Store (all-MiniLM-L6-v2)"]
        BM25["🔍 LlamaIndex BM25 Retriever"]
        RRF["⚡ Reciprocal Rank Fusion (RRF)"]
        SPData["📁 SharePoint Project Pages (5 Projects)"]
        D365Data["💰 D365 Project Operations (26 Rows, 10 Resources)"]
        DevOpsData["🛠️ Azure DevOps Sprint & Work Item Data"]
    end
    class Chroma,BM25,RRF,SPData,D365Data,DevOpsData data

    %% CI/CD & Observability
    subgraph DevOpsPipe ["CI/CD & Observability"]
        AzurePipe["⚙️ Azure DevOps Pipelines (3 Stages)"]
        Telemetry["📡 Telemetry & App Insights (Free Tier)"]
        Pytest["🧪 Pytest Suite (24 Automated Tests)"]
    end
    class AzurePipe,Telemetry,Pytest cicd

    %% Data Connections
    User -- "Submits Query" --> WebApp
    WebApp -- "POST /api/query_project_health" --> FastAPI
    FastAPI -- "Validate User Context" --> AuthService
    FastAPI -- "Classify Intent & Extract Entities" --> IntakeAgent
    IntakeAgent -- "IntakeResult" --> SK
    
    SK -- "Project Metadata" --> SPData
    SK -- "Financials & Timesheets" --> D365Data
    SK -- "Sprint Metrics, Work Items, Burndown" --> FastMCP
    FastMCP -- "Reads" --> DevOpsData
    
    SK -- "Context Grounding Query" --> AutoGen
    AutoGen -- "Semantic Embeddings" --> Chroma
    AutoGen -- "Keyword Matching" --> BM25
    Chroma & BM25 --> RRF
    RRF -- "Fused Grounded Context" --> AutoGen
    AutoGen -- "Context" --> SK
    
    SK --> RiskAlgo
    RiskAlgo --> ReportGen
    ReportGen -- "JSON Trace + MD + HTML" --> FastAPI
    FastAPI -- "Animated Trace & Dashboard" --> WebApp
    
    FastAPI -. "Logged to" .-> Telemetry
    AzurePipe --> Pytest
```

---

## Hybrid RAG Architecture

This diagram details how the Data Retrieval Agent executes Hybrid RAG by combining Semantic Vectors (ChromaDB) with Keyword Matching (LlamaIndex BM25) and applying Reciprocal Rank Fusion (RRF).

```mermaid
graph TD
    User["User Query"] --> |"Question"| Engine["Hybrid RAG Engine (retrieval_agent.py)"]
    
    subgraph Data_Ingestion ["1. Data Ingestion Phase"]
        RawData["Mock Data (SharePoint, D365, DevOps)"] --> |"Record-based Chunking"| Chunks["Text Chunks"]
        Chunks --> |"all-MiniLM-L6-v2 Embeddings"| Chroma["Chroma DB (Vector Store)"]
        Chunks --> |"Raw Text Indexing"| BM25Store["LlamaIndex (BM25 Keyword Store)"]
    end

    subgraph Retrieval_Phase ["2. Retrieval Phase"]
        Engine --> |"Embed Query"| QEmbed["Query Embedding (all-MiniLM-L6-v2)"]
        Engine --> |"Tokenize Query"| QToken["Query Tokenization"]

        QEmbed --> |"Semantic Search (_chromadb_search)"| Chroma
        QToken --> |"Keyword Search (_bm25_search)"| BM25Store
        
        Chroma -.-> |"Semantic Results"| RRF["Reciprocal Rank Fusion (_reciprocal_rank_fusion)"]
        BM25Store -.-> |"Keyword Results"| RRF
    end
    
    RRF --> |"3. Best Merged Chunks"| Prompt["Master Prompt Construction"]
    Prompt --> LLM["Groq LLM (Qwen 27B)"]
    LLM --> FinalAnswer["Final Generated Answer"]
    
    %% Styling
    classDef database fill:#fbb4ae,stroke:#333,stroke-width:2px,color:#000,font-weight:bold;
    classDef process fill:#b3cde3,stroke:#333,stroke-width:2px,color:#000,font-weight:bold;
    classDef default fill:#ccebc5,stroke:#333,stroke-width:2px,color:#000,font-weight:bold;
    
    class Chroma,BM25Store database;
    class Engine,RRF,Prompt,QEmbed,QToken process;
```

---

## Technical Component Breakdown

### 1. User Interface Layer
- **Pro-Code Web Dashboard:** Built with HTML, Vanilla CSS, and JavaScript without third-party framework overhead.
- **Agent Execution Trace:** Visualizes the agent's 10-step chain of thought in real-time, displaying elapsed milliseconds and individual agent statuses.
- **Three Core Panels:**
  - **Agent Chat:** Interactive natural language interface with 6 instant query chips.
  - **Data Sources:** Live view of connected data sources with ingestion metrics.
  - **Architecture:** Architectural diagram and tech stack mapping (Free Stack vs Step Up).

### 2. Gateway & Authentication Layer
- **FastAPI Backend:** Asynchronous Python API server with CORS middleware, request timing headers, and OpenAPI documentation.
- **Simulated Entra ID RBAC:** Validates `user_id` context variables, assigns roles (`manager`, `admin`, `viewer`), and restricts project access to authorized managers.

### 3. Agent 1: Intake Agent (Pro-Code NLP Classifier)
- **Zero Low-Code Dependencies:** Built in pure Python, eliminating the need for Copilot Studio.
- **6 Query Intents:** Accurately classifies queries across `portfolio_overview`, `project_health`, `budget_query`, `risk_query`, `sprint_query`, and `team_query`.
- **Entity Extraction:** Maps colloquial project names and codenames to canonical IDs (`P-001` through `P-005`).

### 4. Agent 2: Data Retrieval Agent & FastMCP
- **AutoGen AssistantAgent:** Encapsulates the hybrid retrieval tools for conversational agent workflows.
- **Hybrid RAG:** Fuses dense semantic vector search (ChromaDB + HuggingFace `all-MiniLM-L6-v2`) with sparse keyword search (LlamaIndex BM25) using Reciprocal Rank Fusion (RRF).
- **FastMCP Tool Server:** Exposes 5 MCP tools (`get_sprint_status`, `get_all_sprint_statuses`, `get_work_items`, `get_sprint_burndown`, `get_team_members`).

### 5. Agent 3: Insight Orchestrator (Semantic Kernel)
- **Microsoft Semantic Kernel:** Initializes a native `ProjectHealthPlugin` with the `@kernel_function` decorator.
- **Multi-Factor Risk Scoring:** Computes risk scores (0–100) using a weighted algorithm:
  - Active Blockers: 30%
  - Open Bug Delta: 20%
  - Sprint Velocity Deficit: 20%
  - Budget Overrun: 30%
- **Dual Format Reporting:** Synthesizes structured Markdown for interactive chat and generates standalone styled HTML reports.

### 6. Observability & CI/CD
- **Application Insights (Free Tier):** Logs custom events, dependency timing, API requests, and exception stack traces.
- **Azure DevOps Pipelines:** A 3-stage CI/CD pipeline (`BuildAndTest` → `DeployToTest` → `PromoteToProduction`) with flake8 linting and automated test runs.
- **24 Pytest Unit Tests:** Validates authentication, intent classification, entity extraction, and risk calculation.
