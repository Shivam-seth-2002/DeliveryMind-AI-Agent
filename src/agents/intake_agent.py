"""
Intake Agent — Pro-Code Natural Language Intent Classifier

Replaces Copilot Studio low-code with a fully pro-code Python implementation.
Takes natural language questions from managers and classifies:
  - Intent type (project_health, portfolio_overview, budget_query, risk_query, sprint_query)
  - Target project(s) extracted from the query
  - Query context (urgency, focus area)

Architecture note: In the real capstone, this would be a Copilot Studio bot deployed
to Microsoft Teams. This pro-code version replicates the same intent classification
and entity extraction logic that Copilot Studio Topics would provide, but in Python
so it runs anywhere without a low-code dependency.

STEP UP: For Teams integration without Copilot Studio, use Bot Framework SDK (Python)
with Azure Bot Service to deploy as a Teams app.
"""
import re
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("IntelligentDeliveryAgent")


# ── Intent Definitions ──
class IntentType:
    """Enumeration of recognized query intents."""
    PROJECT_HEALTH = "project_health"
    PORTFOLIO_OVERVIEW = "portfolio_overview"
    BUDGET_QUERY = "budget_query"
    RISK_QUERY = "risk_query"
    SPRINT_QUERY = "sprint_query"
    TEAM_QUERY = "team_query"
    UNKNOWN = "unknown"


# ── Project Entity Registry ──
# Maps known keywords / aliases to canonical project IDs
PROJECT_ALIASES = {
    # Project Alpha
    "alpha": "P-001",
    "p-001": "P-001",
    "p001": "P-001",
    "project alpha": "P-001",
    "sales dashboard": "P-001",
    "power bi sales": "P-001",
    # Project Beta
    "beta": "P-002",
    "p-002": "P-002",
    "p002": "P-002",
    "project beta": "P-002",
    "marketing analytics": "P-002",
    "data warehouse": "P-002",
    # Project Gamma
    "gamma": "P-003",
    "p-003": "P-003",
    "p003": "P-003",
    "project gamma": "P-003",
    "finance reporting": "P-003",
    "synapse": "P-003",
    # Project Delta
    "delta": "P-004",
    "p-004": "P-004",
    "p004": "P-004",
    "project delta": "P-004",
    "hr analytics": "P-004",
    "employee insights": "P-004",
    # Project Epsilon
    "epsilon": "P-005",
    "p-005": "P-005",
    "p005": "P-005",
    "project epsilon": "P-005",
    "supply chain": "P-005",
    "logistics dashboard": "P-005",
}

# ── Intent Keyword Patterns ──
# Each pattern maps to an intent type. Evaluated in priority order.
INTENT_PATTERNS = [
    # Budget/Financial queries
    {
        "intent": IntentType.BUDGET_QUERY,
        "keywords": [
            r"\bbudget\b", r"\bcost\b", r"\bfinancial\b", r"\bspend\b",
            r"\bexpense\b", r"\boverrun\b", r"\bunder.?budget\b",
            r"\bover.?budget\b", r"\bhours?\s+logged\b", r"\btimesheet\b",
            r"\bd365\b", r"\bfinance\b",
        ],
    },
    # Risk-focused queries
    {
        "intent": IntentType.RISK_QUERY,
        "keywords": [
            r"\brisk\b", r"\bat.?risk\b", r"\bblocker\b", r"\bblocked\b",
            r"\bcritical\b", r"\bdanger\b", r"\bwarning\b", r"\balert\b",
            r"\bescalat\w*\b", r"\btrouble\b", r"\bproblem\b",
            r"\bconcern\b", r"\bflagged\b",
        ],
    },
    # Sprint/Velocity queries
    {
        "intent": IntentType.SPRINT_QUERY,
        "keywords": [
            r"\bsprint\b", r"\bvelocity\b", r"\biteration\b",
            r"\bbacklog\b", r"\bburn.?down\b", r"\bstory.?points?\b",
            r"\bwork.?items?\b", r"\bdevops\b", r"\bbug\w*\b",
        ],
    },
    # Team queries
    {
        "intent": IntentType.TEAM_QUERY,
        "keywords": [
            r"\bteam\b", r"\bresource\w*\b", r"\bassign\w*\b",
            r"\bwho\s+is\b", r"\bmember\w*\b", r"\bstaff\b",
            r"\bdeveloper\b", r"\bengineer\b",
        ],
    },
    # Portfolio-level queries (must be checked before project health)
    {
        "intent": IntentType.PORTFOLIO_OVERVIEW,
        "keywords": [
            r"\ball\s+project\w*\b", r"\bportfolio\b", r"\boverview\b",
            r"\bsummary\b", r"\bdashboard\b", r"\bactive\s+project\w*\b",
            r"\bacross\b", r"\bentire\b", r"\beverything\b",
            r"\bhow\s+are\s+(?:our|the|my)\b",
        ],
    },
    # Single project health (broadest — catches "health of Project X")
    {
        "intent": IntentType.PROJECT_HEALTH,
        "keywords": [
            r"\bhealth\b", r"\bstatus\b", r"\bhow\s+is\b",
            r"\bupdate\b", r"\breport\b", r"\bcheck\b",
            r"\btell\s+me\s+about\b", r"\bshow\s+me\b",
            r"\bwhat\s+is\s+the\b", r"\bgive\s+me\b",
        ],
    },
]


@dataclass
class IntakeResult:
    """
    Structured output from the Intake Agent.

    Attributes:
        intent: The classified intent type
        project_ids: List of extracted project IDs (empty for portfolio queries)
        project_names: Human-readable names for extracted projects
        confidence: Confidence score (0.0–1.0) based on keyword match density
        focus_area: Optional sub-focus (e.g., 'budget', 'velocity', 'blockers')
        original_query: The original query text
        user_id: The authenticated user context
    """
    intent: str = IntentType.UNKNOWN
    project_ids: list = field(default_factory=list)
    project_names: list = field(default_factory=list)
    confidence: float = 0.0
    focus_area: Optional[str] = None
    original_query: str = ""
    user_id: str = ""


# ── Project name registry (for display) ──
PROJECT_DISPLAY_NAMES = {
    "P-001": "Project Alpha",
    "P-002": "Project Beta",
    "P-003": "Project Gamma",
    "P-004": "Project Delta",
    "P-005": "Project Epsilon",
}


class IntakeAgent:
    """
    Pro-Code Intake Agent for Natural Language Query Processing.

    This is the first agent in the multi-agent pipeline. It:
      1. Receives natural language queries from delivery managers
      2. Classifies the intent (project health, portfolio, budget, risk, sprint)
      3. Extracts project entities from the query
      4. Returns a structured IntakeResult for the Insight Orchestrator

    Architecture:
        Manager → IntakeAgent → IntakeResult → Orchestrator → Data Retrieval → Report

    In production (Step Up): This agent's logic would be deployed as:
      - Bot Framework SDK bot → Azure Bot Service → Teams channel
      - Or as an Azure Functions endpoint called by Power Automate
    """

    def __init__(self):
        self.name = "IntakeAgent"
        logger.info(f"[{self.name}] Initialized pro-code intent classifier.")

    async def process_query(self, query: str, user_id: str = "") -> IntakeResult:
        """
        Main entry point. Processes a natural language query using Groq LLM
        and returns structured IntakeResult. Falls back to rule-based NLP if LLM fails.
        """
        logger.info(f"[{self.name}] Processing query via LLM: '{query}' (user={user_id})")

        try:
            from autogen_agentchat.agents import AssistantAgent
            from autogen_agentchat.messages import TextMessage
            from autogen_core import CancellationToken
            from autogen_ext.models.openai import OpenAIChatCompletionClient
            from src.config import GROQ_API_KEY
            import json

            # Configure AutoGen to use Groq's OpenAI-compatible endpoint
            model_client = OpenAIChatCompletionClient(
                model="qwen/qwen3.8-27b",
                api_key=GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1",
                model_info={"vision": False, "function_calling": True, "json_output": True, "family": "unknown"}
            )

            agent = AssistantAgent(
                name="IntakeClassifier",
                description="Classifies project delivery intent from natural language queries.",
                model_client=model_client,
                system_message=f"""
You are an expert NLP classification agent. Analyze the user query and output ONLY valid JSON.
Valid Intents: project_health, portfolio_overview, budget_query, risk_query, sprint_query, team_query
Valid Project IDs (extract if mentioned):
P-001 (Project Alpha, Sales Dashboard)
P-002 (Project Beta, Marketing Analytics)
P-003 (Project Gamma, Finance Reporting)
P-004 (Project Delta, HR Analytics)
P-005 (Project Epsilon, Supply Chain)

Determine:
1. intent: The closest matching intent from the valid list above. (Default to portfolio_overview if no specific project is found and it's a general question).
2. project_ids: List of extracted project IDs (e.g. ["P-001"]).
3. focus_area: A short string if they mention budget, risk, blockers, velocity etc.
4. confidence: Float between 0.0 and 1.0.

JSON format:
{{
  "intent": "project_health",
  "project_ids": ["P-002"],
  "focus_area": "risk",
  "confidence": 0.95
}}
"""
            )

            response = await agent.on_messages(
                [TextMessage(content=query, source="user")],
                cancellation_token=CancellationToken()
            )
            
            # Parse JSON from LLM
            content = response.chat_message.content
            # Clean up markdown formatting if present
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()
                
            llm_data = json.loads(content)
            
            intent = llm_data.get("intent", IntentType.UNKNOWN)
            project_ids = llm_data.get("project_ids", [])
            project_names = [PROJECT_DISPLAY_NAMES.get(pid, pid) for pid in project_ids]
            
            result = IntakeResult(
                intent=intent,
                project_ids=project_ids,
                project_names=project_names,
                confidence=llm_data.get("confidence", 0.9),
                focus_area=llm_data.get("focus_area"),
                original_query=query,
                user_id=user_id,
            )
            logger.info(f"[{self.name}] LLM successfully classified intent: {result.intent} for {result.project_ids}")
            return result

        except Exception as e:
            logger.error(f"[{self.name}] LLM Classification failed ({e}). Falling back to rule-based NLP.")
            
            query_lower = query.lower().strip()
            project_ids, project_names = self._extract_projects(query_lower)
            intent, confidence, focus_area = self._classify_intent(query_lower, project_ids)

            if project_ids and intent == IntentType.PORTFOLIO_OVERVIEW:
                intent = IntentType.PROJECT_HEALTH

            if not project_ids and intent not in (IntentType.PORTFOLIO_OVERVIEW, IntentType.RISK_QUERY):
                if intent in (IntentType.PROJECT_HEALTH, IntentType.UNKNOWN):
                    intent = IntentType.PORTFOLIO_OVERVIEW

            return IntakeResult(
                intent=intent,
                project_ids=project_ids,
                project_names=project_names,
                confidence=confidence,
                focus_area=focus_area,
                original_query=query,
                user_id=user_id,
            )

    def _extract_projects(self, query_lower: str) -> tuple:
        """
        Extracts project IDs from the query using alias matching.
        Returns (project_ids, project_names).
        """
        found_ids = set()
        found_names = []

        # Sort aliases by length (longest first) to avoid partial matches
        sorted_aliases = sorted(PROJECT_ALIASES.keys(), key=len, reverse=True)

        for alias in sorted_aliases:
            # Use word boundary matching for single words, substring for multi-word
            if " " in alias:
                if alias in query_lower:
                    pid = PROJECT_ALIASES[alias]
                    if pid not in found_ids:
                        found_ids.add(pid)
                        found_names.append(PROJECT_DISPLAY_NAMES.get(pid, pid))
            else:
                pattern = r'\b' + re.escape(alias) + r'\b'
                if re.search(pattern, query_lower):
                    pid = PROJECT_ALIASES[alias]
                    if pid not in found_ids:
                        found_ids.add(pid)
                        found_names.append(PROJECT_DISPLAY_NAMES.get(pid, pid))

        return list(found_ids), found_names

    def _classify_intent(self, query_lower: str, project_ids: list) -> tuple:
        """
        Classifies the intent of the query by matching keyword patterns.
        Returns (intent, confidence, focus_area).
        """
        best_intent = IntentType.UNKNOWN
        best_score = 0
        best_focus = None

        for pattern_group in INTENT_PATTERNS:
            intent = pattern_group["intent"]
            keywords = pattern_group["keywords"]
            match_count = 0

            for kw in keywords:
                if re.search(kw, query_lower, re.IGNORECASE):
                    match_count += 1

            if match_count > 0:
                # Confidence = ratio of matched keywords to total, scaled up
                confidence = min(1.0, match_count / max(2, len(keywords) * 0.3))

                if confidence > best_score:
                    best_score = confidence
                    best_intent = intent

                    # Determine focus area from the intent type
                    if intent == IntentType.BUDGET_QUERY:
                        best_focus = "budget"
                    elif intent == IntentType.RISK_QUERY:
                        best_focus = "risk"
                    elif intent == IntentType.SPRINT_QUERY:
                        best_focus = "sprint"
                    elif intent == IntentType.TEAM_QUERY:
                        best_focus = "team"

        # Boost confidence if project entities were found
        if project_ids and best_intent != IntentType.UNKNOWN:
            best_score = min(1.0, best_score + 0.2)

        return best_intent, best_score, best_focus
