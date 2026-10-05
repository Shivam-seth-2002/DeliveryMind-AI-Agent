# Complete Project Architecture & Request Lifecycle

This diagram illustrates the full end-to-end architecture of the **Intelligent Client Delivery Agent**. The numbered steps (1-10) trace the exact journey of a single user query through the system.

```mermaid
graph TD
    %% Styling Definitions
    classDef user fill:#ffdd99,stroke:#e69900,stroke-width:2px,color:#000,font-weight:bold;
    classDef api fill:#b3d9ff,stroke:#0066cc,stroke-width:2px,color:#000,font-weight:bold;
    classDef orchestrator fill:#d9b3ff,stroke:#8000ff,stroke-width:3px,color:#000,font-weight:bold;
    classDef agents fill:#ffd9b3,stroke:#ff6600,stroke-width:2px,color:#000,font-weight:bold;
    classDef db fill:#ccebc5,stroke:#33cc33,stroke-width:2px,color:#000,font-weight:bold;
    classDef output fill:#ffb3e6,stroke:#cc0099,stroke-width:2px,color:#000,font-weight:bold;

    %% 1. The User
    User(("👨‍💼 User (Delivery Manager)")):::user
    UI["🌐 Web UI Dashboard"]:::user

    %% 2. The Gateway
    API["⚡ FastAPI Server (api.py)"]:::api
    Auth["🔐 Auth Service (auth.py)"]:::api

    %% 3. The Brain (Semantic Kernel)
    SK{"🧠 Semantic Kernel Orchestrator<br/>(insight_orchestrator.py)"}:::orchestrator

    %% 4. The Specialized Agents
    Intake["💬 Intake Agent<br/>(NLP & Intent Classifier)"]:::agents
    Retriever["🤖 AutoGen Data Retriever<br/>(Hybrid RAG Tool)"]:::agents
    MCP["🔌 FastMCP Server<br/>(devops_mcp.py)"]:::agents

    %% 5. The Databases
    Chroma[(🗄️ ChromaDB<br/>Semantic)]:::db
    Llama[(🔍 LlamaIndex<br/>Keyword)]:::db
    DevOps[(🛠️ Azure DevOps<br/>JSON Mock)]:::db
    D365[(💰 Dynamics 365<br/>CSV Mock)]:::db

    %% 6. Processors & Output
    Risk["📊 Risk Scoring Algorithm"]:::output
    Report["📋 Report Generator<br/>(HTML & MD)"]:::output

    %% ==========================================
    %% THE QUERY LIFECYCLE (Numbered Steps)
    %% ==========================================

    User -- "1. 'P-001 ka budget aur risk kya hai?'" --> UI
    UI -- "2. POST /query" --> API
    API -- "3. Passes Query" --> SK
    
    SK -- "4. Check Role" --> Auth
    Auth -. "Returns: User has 'Manager' Access" .-> SK

    SK -- "5. Extract Intent & Project ID" --> Intake
    Intake -. "Returns: Intent=PROJECT_HEALTH, ID='P-001'" .-> SK

    SK -- "6a. Fetch Unstructured Data" --> Retriever
    Retriever --> Chroma
    Retriever --> Llama
    Chroma -. "Merged via RRF" .-> Retriever
    Retriever -. "Context: Risk is high" .-> SK

    SK -- "6b. Fetch Sprint Data" --> MCP
    MCP --> DevOps
    DevOps -. "Sprint: Delayed, 5 Bugs" .-> MCP
    MCP -. "Returns DevOps Data" .-> SK

    SK -- "6c. Fetch Financial Data" --> D365
    D365 -. "Returns: $5000 Overrun" .-> SK

    SK -- "7. Feed all Data" --> Risk
    Risk -. "Computes Risk Score: 85/100 (Critical)" .-> SK

    SK -- "8. Synthesize Answer (Groq LLM)" --> Report
    Report -. "9. Generates HTML/Markdown" .-> API
    API -- "10. Returns Final Report" --> UI
    UI -- "Displays Animated Dashboard" --> User
```

### Legend of Operations
- **Yellow:** User Interaction Layer
- **Blue:** Security and API Gateway
- **Purple:** The Core Orchestrator (The "Boss")
- **Orange:** The Worker AI Agents
- **Green:** The Grounding Data Sources
- **Pink:** Processing and Report Generation
