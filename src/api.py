"""
FastAPI Backend — Intelligent Client Delivery Agent

Serves the frontend and exposes API endpoints for the agent system.
Includes CORS, auth dependency, request timing, and structured error handling.

Endpoints:
  POST /api/query_project_health  — Main agent query endpoint
  GET  /api/health                — Health check
  GET  /api/sources               — Connected data source metadata
  GET  /api/projects              — Project list
  POST /api/export_html           — Export HTML report
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
import time
import logging

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from orchestrator.insight_orchestrator import synthesize_signals
from utils.telemetry import (
    setup_telemetry, log_request, log_error,
    track_request, track_exception, new_correlation_id
)
from utils.auth import authenticate_user
from agents.retrieval_agent import get_ingestion_stats

try:
    from config import API_HOST, API_PORT, CORS_ORIGINS
except ImportError:
    API_HOST = "0.0.0.0"
    API_PORT = 8000
    CORS_ORIGINS = ["*"]

logger = logging.getLogger("IntelligentDeliveryAgent")

app = FastAPI(
    title="Intelligent Client Delivery Agent API",
    description="Multi-agent system for project health monitoring using Semantic Kernel, AutoGen, LlamaIndex, ChromaDB, and FastMCP.",
    version="1.0.0"
)

# ── CORS Middleware ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize telemetry
setup_telemetry()


# ── Request Models ──

class QueryRequest(BaseModel):
    query: str
    user_id: str


class ExportRequest(BaseModel):
    query: str
    user_id: str


# ── Request Timing Middleware ──

@app.middleware("http")
async def add_request_timing(request: Request, call_next):
    """Adds request timing and correlation ID to all requests."""
    correlation_id = new_correlation_id()
    start_time = time.perf_counter()

    response = await call_next(request)

    duration_ms = (time.perf_counter() - start_time) * 1000
    response.headers["X-Correlation-Id"] = correlation_id
    response.headers["X-Response-Time-Ms"] = f"{duration_ms:.1f}"

    return response


# ── API Endpoints ──

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint for Azure DevOps pipeline and monitoring.
    Returns service status, component health, and version info.
    """
    ingestion_stats = get_ingestion_stats()
    return JSONResponse(content={
        "status": "healthy",
        "service": "Intelligent Client Delivery Agent",
        "version": "1.0.0",
        "components": {
            "semantic_kernel": "active",
            "autogen_agent": "active",
            "chromadb": "active",
            "bm25_index": "active" if ingestion_stats.get("bm25_available") else "degraded",
            "fastmcp": "active",
            "telemetry": "active",
        },
        "data": {
            "total_documents": ingestion_stats.get("total_documents", 0),
            "last_ingested": ingestion_stats.get("last_ingested", "N/A"),
        }
    })


@app.get("/api/sources")
async def get_sources():
    """
    Returns metadata about connected data sources.
    Used by the frontend Sources panel.
    """
    ingestion_stats = get_ingestion_stats()
    return JSONResponse(content={
        "sources": [
            {
                "name": "SharePoint Project Pages",
                "type": "JSON Export",
                "agent": "Data Retrieval Agent",
                "status": "connected",
                "documents": ingestion_stats.get("sharepoint_docs", 0),
            },
            {
                "name": "Azure DevOps Sprint Data",
                "type": "MCP Tool (FastMCP)",
                "agent": "Data Retrieval Agent",
                "status": "connected",
                "documents": ingestion_stats.get("devops_docs", 0),
            },
            {
                "name": "D365 Project Operations",
                "type": "CSV Export",
                "agent": "Data Retrieval Agent",
                "status": "connected",
                "documents": ingestion_stats.get("d365_docs", 0),
            },
            {
                "name": "Hybrid RAG Vector Store",
                "type": "ChromaDB + LlamaIndex BM25",
                "agent": "Data Retrieval Agent",
                "status": "connected",
                "documents": ingestion_stats.get("total_documents", 0),
                "bm25_available": ingestion_stats.get("bm25_available", False),
            },
        ],
        "total_indexed": ingestion_stats.get("total_documents", 0),
    })


@app.get("/api/projects")
async def get_projects():
    """
    Returns the list of all projects.
    Used by the frontend for project selection.
    """
    import json
    sp_file = os.path.join(os.path.dirname(__file__), "..", "data", "mock_sharepoint.json")
    if os.path.exists(sp_file):
        with open(sp_file, "r") as f:
            projects = json.load(f)
        return JSONResponse(content={
            "projects": [
                {
                    "projectId": p["projectId"],
                    "projectName": p["projectName"],
                    "status": p.get("status", "Active"),
                    "client": p.get("client", "N/A"),
                    "manager": p.get("manager", "N/A"),
                    "technology": p.get("technology", "N/A"),
                    "phase": p.get("phase", "N/A"),
                    "priority": p.get("priority", "N/A"),
                }
                for p in projects
            ],
            "total": len(projects)
        })
    return JSONResponse(content={"projects": [], "total": 0})


@app.post("/api/query_project_health")
async def query_project_health(request: QueryRequest):
    """
    Main endpoint for the frontend to call with natural language query.
    Returns structured JSON with agent_trace, report, sources, and risk data.

    Pipeline:
      1. Authenticate user via simulated Entra ID
      2. Forward query to Insight Orchestrator (Semantic Kernel)
      3. Orchestrator invokes IntakeAgent → DataRetriever → Risk Scoring → Report
      4. Return structured JSON response
    """
    start_time = time.perf_counter()
    log_request(request.user_id, request.query)
    logger.info(f"Received query from user_id={request.user_id}: {request.query}")

    try:
        # Call the orchestrator — returns structured dict with agent trace
        result = await synthesize_signals(request.query, request.user_id)

        # Track successful request
        duration_ms = (time.perf_counter() - start_time) * 1000
        track_request(
            user_id=request.user_id,
            query=request.query,
            duration_ms=duration_ms,
            success=True,
            properties={"query_type": result.get("query_type", "unknown")}
        )

        # Remove html_report from JSON response (too large), keep it available via export endpoint
        response_data = {k: v for k, v in result.items() if k != "html_report"}
        return JSONResponse(content=response_data)

    except Exception as e:
        error_msg = str(e)
        log_error(error_msg)
        track_exception(e, {"user_id": request.user_id, "query": request.query})
        logger.error(f"Error processing query: {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "An error occurred while generating the report.",
                "message": error_msg,
            }
        )


@app.post("/api/export_html")
async def export_html_report(request: ExportRequest):
    """
    Generates and returns an HTML health report for download.
    Runs the full agent pipeline and returns the HTML output.
    """
    logger.info(f"[API] HTML export requested by user_id={request.user_id}: {request.query}")

    try:
        result = await synthesize_signals(request.query, request.user_id)
        html_content = result.get("html_report", "<h1>No report generated</h1>")
        return HTMLResponse(content=html_content)
    except Exception as e:
        log_error(str(e))
        track_exception(e)
        raise HTTPException(status_code=500, detail="Failed to generate HTML report.")


# Mount static files for the frontend
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
