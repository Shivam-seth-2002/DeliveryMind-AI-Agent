@echo off
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║  Intelligent Client Delivery Agent for MAQ Software          ║
echo ║  Multi-Agent System Demo Launcher                            ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

echo [1/3] Starting FastMCP DevOps Server (background)...
start /B cmd /k "python src\mcp_server\devops_mcp.py"
timeout /t 2 /nobreak > nul

echo [2/3] Running unit tests...
python -m pytest tests/ -v --tb=short
echo.

echo [3/3] Starting FastAPI Backend...
echo.
echo ══════════════════════════════════════════════════════════════
echo   Agent is running at: http://127.0.0.1:8000
echo   API Health Check:    http://127.0.0.1:8000/api/health
echo   HTML Report Export:  POST http://127.0.0.1:8000/api/export_html
echo ══════════════════════════════════════════════════════════════
echo.
echo   Demo queries to try:
echo   • "What is the health of our active Power BI delivery projects?"
echo   • "What is the health of Project Beta?"
echo   • "Which projects are at risk?"
echo   • "What is the budget status for Project Alpha?"
echo   • "Show me the sprint velocity for Project Gamma"
echo.
python src\api.py
