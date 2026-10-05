"""
Unit Tests — Intake Agent (Pro-Code Intent Classifier)
Tests intent classification and project entity extraction.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agents.intake_agent import IntakeAgent, IntentType


def test_project_health_single():
    """Test: Specific project health query should classify as project_health."""
    agent = IntakeAgent()
    result = agent.process_query("What is the health of Project Beta?", "mgr123")
    assert result.intent == IntentType.PROJECT_HEALTH
    assert "P-002" in result.project_ids
    assert result.confidence > 0.3


def test_portfolio_overview():
    """Test: General query about all projects should classify as portfolio_overview."""
    agent = IntakeAgent()
    result = agent.process_query("Show me all active projects", "mgr123")
    assert result.intent == IntentType.PORTFOLIO_OVERVIEW
    assert len(result.project_ids) == 0


def test_budget_query():
    """Test: Budget-related query should classify as budget_query."""
    agent = IntakeAgent()
    result = agent.process_query("What is the budget and cost for Project Alpha?", "mgr123")
    assert result.intent == IntentType.BUDGET_QUERY
    assert "P-001" in result.project_ids
    assert result.focus_area == "budget"


def test_risk_query():
    """Test: Risk-related query should classify as risk_query."""
    agent = IntakeAgent()
    result = agent.process_query("Which projects are at risk?", "mgr123")
    assert result.intent == IntentType.RISK_QUERY


def test_sprint_query():
    """Test: Sprint/velocity query should classify as sprint_query."""
    agent = IntakeAgent()
    result = agent.process_query("What is the sprint velocity for Project Gamma?", "mgr123")
    assert result.intent == IntentType.SPRINT_QUERY
    assert "P-003" in result.project_ids
    assert result.focus_area == "sprint"


def test_multiple_project_aliases():
    """Test: Different aliases for the same project should resolve correctly."""
    agent = IntakeAgent()

    result1 = agent.process_query("Tell me about alpha", "mgr123")
    assert "P-001" in result1.project_ids

    result2 = agent.process_query("How is P-002 doing?", "mgr123")
    assert "P-002" in result2.project_ids

    result3 = agent.process_query("Status of project delta", "mgr123")
    assert "P-004" in result3.project_ids


def test_project_epsilon():
    """Test: Project Epsilon (P-005) should be detected."""
    agent = IntakeAgent()
    result = agent.process_query("What is the health of Project Epsilon?", "mgr456")
    assert "P-005" in result.project_ids


def test_unknown_query():
    """Test: Completely unrelated query should fall back to portfolio overview."""
    agent = IntakeAgent()
    result = agent.process_query("hello world", "mgr123")
    # Should fall back to portfolio_overview since no projects and no intent matched
    assert result.intent == IntentType.PORTFOLIO_OVERVIEW


def test_general_health_query():
    """Test: 'How are our projects?' should classify as portfolio_overview."""
    agent = IntakeAgent()
    result = agent.process_query("How are our active Power BI delivery projects?", "mgr123")
    assert result.intent == IntentType.PORTFOLIO_OVERVIEW
