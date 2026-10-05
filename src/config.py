"""
Centralized Configuration — Intelligent Client Delivery Agent
All settings, paths, thresholds, and environment-driven config in one place.

STEP UP: In production, these would be sourced from Azure Key Vault
and managed via Azure App Configuration.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ---------- Base Paths ----------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
CHROMA_DB_PATH = os.path.join(DATA_DIR, "chroma_db")

# ---------- Data Source Paths ----------
SHAREPOINT_FILE = os.path.join(DATA_DIR, "mock_sharepoint.json")
D365_FILE = os.path.join(DATA_DIR, "mock_d365.csv")
DEVOPS_FILE = os.path.join(DATA_DIR, "mock_devops.json")

# ---------- Embedding Model ----------
EMBEDDING_MODEL_NAME = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
# STEP UP: Replace with Azure OpenAI embeddings model deployment name
# AZURE_OPENAI_EMBEDDING_MODEL = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")

# ---------- LLM Integration (Groq) ----------
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set. Please add it to the .env file.")

# ---------- ChromaDB ----------
CHROMA_COLLECTION_NAME = "project_data"

# ---------- Risk Scoring Thresholds ----------
TARGET_VELOCITY = int(os.environ.get("TARGET_VELOCITY", "35"))
RISK_CRITICAL_THRESHOLD = 70
RISK_AT_RISK_THRESHOLD = 40
RISK_CAUTION_THRESHOLD = 20

# Risk weights (must sum to 1.0)
RISK_WEIGHT_BLOCKERS = 0.30
RISK_WEIGHT_BUGS = 0.20
RISK_WEIGHT_VELOCITY = 0.20
RISK_WEIGHT_BUDGET = 0.30

# ---------- API Server ----------
API_HOST = os.environ.get("API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("API_PORT", "8000"))
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")

# ---------- Telemetry ----------
# Application Insights free tier connection string
APPINSIGHTS_CONNECTION_STRING = os.environ.get(
    "APPLICATIONINSIGHTS_CONNECTION_STRING",
    ""  # Empty = fallback to file/console logging
)
TELEMETRY_LOG_FILE = os.path.join(PROJECT_ROOT, "telemetry_log.jsonl")

# ---------- Simulated Auth ----------
# In production, this would be Entra ID (Azure AD) configuration
# STEP UP: AZURE_AD_TENANT_ID = os.environ.get("AZURE_AD_TENANT_ID")
# STEP UP: AZURE_AD_CLIENT_ID = os.environ.get("AZURE_AD_CLIENT_ID")
SIMULATED_AUTH_ENABLED = True

# ---------- HTML Report Output ----------
HTML_REPORT_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "reports")
os.makedirs(HTML_REPORT_OUTPUT_DIR, exist_ok=True)
