"""
Telemetry & Observability — Intelligent Client Delivery Agent

Structured telemetry with Application Insights (free tier) integration.
Tracks events, dependencies, requests, and exceptions with custom dimensions.

When Application Insights is not configured, falls back to structured
JSON-Lines file logging for offline analysis.

STEP UP: In production, use azure-monitor-opentelemetry with managed identity
and correlate traces across all agents via W3C Trace Context.
"""
import os
import sys
import json
import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from functools import wraps
from contextlib import contextmanager

# Add src to path for config import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from config import APPINSIGHTS_CONNECTION_STRING, TELEMETRY_LOG_FILE
except ImportError:
    APPINSIGHTS_CONNECTION_STRING = ""
    TELEMETRY_LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "telemetry_log.jsonl")

try:
    from azure.monitor.opentelemetry import configure_azure_monitor
except ImportError:
    configure_azure_monitor = None

# Set up standard logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("IntelligentDeliveryAgent")


# ── Correlation Context ──
_current_correlation_id = None


def new_correlation_id() -> str:
    """Generate a new correlation ID for request tracing."""
    global _current_correlation_id
    _current_correlation_id = str(uuid.uuid4())[:8]
    return _current_correlation_id


def get_correlation_id() -> str:
    """Get the current correlation ID or create one."""
    global _current_correlation_id
    if not _current_correlation_id:
        return new_correlation_id()
    return _current_correlation_id


# ── Setup ──

def setup_telemetry():
    """
    Configures Azure Application Insights for telemetry.
    Falls back to file/console logging if no connection string is set.

    STEP UP: In production with Azure:
      - Set APPLICATIONINSIGHTS_CONNECTION_STRING environment variable
      - Enable distributed tracing with W3C Trace Context
      - Use managed identity for auth
    """
    try:
        if configure_azure_monitor and APPINSIGHTS_CONNECTION_STRING:
            configure_azure_monitor(
                connection_string=APPINSIGHTS_CONNECTION_STRING
            )
            logger.info("[Telemetry] Azure Monitor OpenTelemetry configured successfully.")
        elif APPINSIGHTS_CONNECTION_STRING:
            logger.warning("[Telemetry] azure-monitor-opentelemetry not installed. Using file logging.")
        else:
            logger.info("[Telemetry] No App Insights connection string. Using file/console logging.")
    except Exception as e:
        logger.warning(f"[Telemetry] Could not configure Azure Monitor: {e}. Using file logging.")


# ── Structured Event Logging ──

def _write_telemetry_record(record: dict):
    """Write a structured telemetry record to the JSONL log file."""
    record["timestamp"] = datetime.now(timezone.utc).isoformat()
    record["correlationId"] = get_correlation_id()
    try:
        with open(TELEMETRY_LOG_FILE, "a") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        logger.error(f"[Telemetry] Failed to write telemetry: {e}")


def track_event(event_name: str, properties: Optional[dict] = None):
    """
    Track a custom event with optional properties/dimensions.

    Args:
        event_name: Name of the event (e.g., 'QueryProcessed', 'AgentInvoked')
        properties: Custom dimensions dict
    """
    props = properties or {}
    logger.info(f"[Telemetry:Event] {event_name} | {props}")
    _write_telemetry_record({
        "type": "event",
        "name": event_name,
        "properties": props
    })


def track_dependency(dependency_name: str, dependency_type: str,
                     duration_ms: float, success: bool = True,
                     data: str = "", properties: Optional[dict] = None):
    """
    Track a dependency call (ChromaDB, BM25, MCP, etc.).

    Args:
        dependency_name: Name of the dependency (e.g., 'ChromaDB', 'FastMCP')
        dependency_type: Type (e.g., 'VectorStore', 'MCPTool', 'BM25')
        duration_ms: Duration in milliseconds
        success: Whether the call succeeded
        data: Additional data (e.g., query text)
        properties: Custom dimensions
    """
    props = properties or {}
    logger.info(
        f"[Telemetry:Dependency] {dependency_name} ({dependency_type}) "
        f"{'OK' if success else 'FAIL'} {duration_ms:.1f}ms"
    )
    _write_telemetry_record({
        "type": "dependency",
        "name": dependency_name,
        "dependencyType": dependency_type,
        "durationMs": round(duration_ms, 1),
        "success": success,
        "data": data,
        "properties": props
    })


def track_request(user_id: str, query: str, duration_ms: float,
                  success: bool = True, response_code: int = 200,
                  properties: Optional[dict] = None):
    """
    Track an API request with user context and timing.

    Args:
        user_id: The authenticated user ID
        query: The user's query text
        duration_ms: Total request duration in ms
        success: Whether the request succeeded
        response_code: HTTP response code
        properties: Custom dimensions
    """
    props = properties or {}
    logger.info(
        f"[Telemetry:Request] user={user_id} code={response_code} "
        f"{'OK' if success else 'FAIL'} {duration_ms:.1f}ms | {query[:80]}"
    )
    _write_telemetry_record({
        "type": "request",
        "userId": user_id,
        "query": query,
        "durationMs": round(duration_ms, 1),
        "success": success,
        "responseCode": response_code,
        "properties": props
    })


def track_exception(exception: Exception, properties: Optional[dict] = None):
    """
    Track an exception with context.

    Args:
        exception: The exception object
        properties: Custom dimensions
    """
    props = properties or {}
    logger.error(f"[Telemetry:Exception] {type(exception).__name__}: {exception}", exc_info=True)
    _write_telemetry_record({
        "type": "exception",
        "exceptionType": type(exception).__name__,
        "message": str(exception),
        "properties": props
    })


# ── Convenience: Backward-compatible wrappers ──

def log_request(user_id: str, query: str):
    """Legacy wrapper — logs a user request."""
    logger.info(f"[Request] user_id={user_id}: {query}")
    track_event("QueryReceived", {"user_id": user_id, "query": query[:200]})


def log_error(error_msg: str):
    """Legacy wrapper — logs an error."""
    logger.error(f"[Error] {error_msg}")
    _write_telemetry_record({
        "type": "error",
        "message": error_msg
    })


# ── Timing Context Manager ──

@contextmanager
def timed_dependency(dependency_name: str, dependency_type: str, data: str = ""):
    """
    Context manager that times a dependency call and tracks it.

    Usage:
        with timed_dependency("ChromaDB", "VectorStore", query):
            results = collection.query(...)
    """
    start = time.perf_counter()
    success = True
    try:
        yield
    except Exception as e:
        success = False
        track_exception(e, {"dependency": dependency_name})
        raise
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        track_dependency(dependency_name, dependency_type, duration_ms, success, data)
