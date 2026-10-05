# Production Migration Roadmap
**From Proof-of-Concept (PoC) to a 100% Production-Ready Enterprise AI Agent**

This document outlines the step-by-step roadmap required to transition this Intelligence Client Delivery Agent from a local, mock-data-driven Proof of Concept into a highly secure, scalable, and fully integrated Enterprise application.

---

## Phase 1: Security & Identity Management
Currently, the application uses a simulated `USER_REGISTRY` in `auth.py` for Role-Based Access Control (RBAC). 

**Steps for Production:**
1. **Microsoft Entra ID (Azure AD) Integration:** Register the application in the Azure Portal to obtain a `Tenant ID` and `Client ID`.
2. **Token Validation:** Replace the mock authentication logic in `auth.py` with the Microsoft Authentication Library (`msal` for Python) or `fastapi-azure-auth` to validate JWT Bearer tokens sent from the frontend.
3. **Enterprise RBAC:** Map Azure AD App Roles to the local roles (Manager, Admin, Viewer) to ensure strict scope limitation and Zero Trust security.

---

## Phase 2: Live Data Sources Integration
Currently, the application relies on local files (`mock_devops.json` and `mock_d365.csv`) to simulate external systems.

**Steps for Production:**
1. **Azure DevOps:** Update the MCP server (`devops_mcp.py`). Replace local JSON parsing with live REST API calls (`https://dev.azure.com/{organization}/_apis/...`). Authenticate using a Service Account PAT or Azure Managed Identity.
2. **SharePoint (Graph API):** Update the `DataRetriever` agent. Instead of reading local files for RAG, integrate **Microsoft Graph API** to search and fetch live meeting notes and documents directly from SharePoint Document Libraries.
3. **Dynamics 365:** Integrate the Dataverse / D365 Web API to fetch live financial/budgetary data.

---

## Phase 3: AI Model Migration (The Brain)
Currently, the application uses Groq (Qwen 27B) via an API key. For enterprise compliance, third-party open APIs are generally restricted.

**Steps for Production:**
1. **Azure AI Foundry (Azure OpenAI):** Provision an Azure OpenAI resource in the Azure Portal.
2. **Model Deployment:** Deploy an enterprise-grade model (e.g., GPT-4o or Phi-3) within your secure tenant boundary.
3. **Framework Configuration:** Update Semantic Kernel and AutoGen configurations. Swap standard OpenAI/Groq clients with `AzureOpenAIChatCompletionClient`. Manage credentials using Azure Managed Identities rather than raw API keys in the `.env` file.

---

## Phase 4: Vector Database & RAG Upgrade
Currently, the application uses an ephemeral, in-memory `ChromaDB` instance that resets when the script stops.

**Steps for Production:**
1. **Persistent Vector Database:** Deploy an enterprise vector database such as **Azure AI Search** (formerly Cognitive Search), Pinecone, or Qdrant.
2. **Data Ingestion Pipeline:** Build an automated CRON job / data pipeline that runs nightly to fetch new SharePoint documents, generate embeddings, and upsert them into the persistent Vector DB.
3. **Update Retriever:** Modify `retrieval_agent.py` to point to this external cloud database instead of the local ChromaDB client.

---

## Phase 5: Hosting & Observability
Currently, the application is run locally via `run_demo.bat`.

**Steps for Production:**
1. **Containerization:** Write a `Dockerfile` to package the FastAPI application, its dependencies, and Python environment into a standard container image.
2. **Cloud Hosting:** Deploy the Docker container to **Azure App Service** or **Azure Kubernetes Service (AKS)** for high availability and autoscaling.
3. **Telemetry & Monitoring:** In `telemetry.py`, supply the `APPLICATIONINSIGHTS_CONNECTION_STRING`. The existing `azure-monitor-opentelemetry` implementation will automatically begin streaming logs, traces, and agent performance KPIs (Latency, Success Rate) to the live Azure Application Insights dashboard.
