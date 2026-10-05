"""
Unit Tests — Risk Scoring Algorithm
Tests the compute_risk_score function with known inputs.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from orchestrator.insight_orchestrator import compute_risk_score


def test_healthy_project():
    """Test: A project with no issues should be Healthy."""
    score, status, color, breakdown = compute_risk_score(
        blockers=0, open_bugs=0, total_bugs_opened=0,
        velocity=40, target_velocity=35,
        cost_actual=10000, cost_budget=15000
    )
    assert score < 20
    assert status == "Healthy"
    assert color == "#10b981"


def test_critical_project():
    """Test: A project with many issues should be Critical."""
    score, status, color, breakdown = compute_risk_score(
        blockers=2, open_bugs=11, total_bugs_opened=15,
        velocity=20, target_velocity=35,
        cost_actual=45000, cost_budget=33000
    )
    assert score >= 70
    assert status == "Critical"
    assert color == "#ef4444"


def test_at_risk_project():
    """Test: A project with moderate issues should be At Risk."""
    score, status, color, breakdown = compute_risk_score(
        blockers=1, open_bugs=1, total_bugs_opened=4,
        velocity=28, target_velocity=35,
        cost_actual=7600, cost_budget=6300
    )
    assert 40 <= score < 70
    assert status == "At Risk"


def test_blocker_weight():
    """Test: Blockers should heavily impact the score."""
    score_no_blockers, _, _, _ = compute_risk_score(
        blockers=0, open_bugs=0, total_bugs_opened=0,
        velocity=35, target_velocity=35,
        cost_actual=1000, cost_budget=1000
    )
    score_with_blockers, _, _, _ = compute_risk_score(
        blockers=2, open_bugs=0, total_bugs_opened=0,
        velocity=35, target_velocity=35,
        cost_actual=1000, cost_budget=1000
    )
    assert score_with_blockers > score_no_blockers + 20


def test_budget_overrun_impact():
    """Test: Budget overrun should increase risk score."""
    score_on_budget, _, _, _ = compute_risk_score(
        blockers=0, open_bugs=0, total_bugs_opened=0,
        velocity=35, target_velocity=35,
        cost_actual=10000, cost_budget=10000
    )
    score_over_budget, _, _, _ = compute_risk_score(
        blockers=0, open_bugs=0, total_bugs_opened=0,
        velocity=35, target_velocity=35,
        cost_actual=20000, cost_budget=10000
    )
    assert score_over_budget > score_on_budget + 20


def test_breakdown_structure():
    """Test: Breakdown dict should have correct structure."""
    _, _, _, breakdown = compute_risk_score(
        blockers=1, open_bugs=3, total_bugs_opened=5,
        velocity=30, target_velocity=35,
        cost_actual=12000, cost_budget=10000
    )
    assert "blockers" in breakdown
    assert "bugs" in breakdown
    assert "velocity" in breakdown
    assert "budget" in breakdown
    for key in breakdown:
        assert "raw" in breakdown[key]
        assert "weighted" in breakdown[key]
        assert "weight" in breakdown[key]


def test_zero_budgets():
    """Test: Zero budget should not cause division by zero."""
    score, status, _, _ = compute_risk_score(
        blockers=0, open_bugs=0, total_bugs_opened=0,
        velocity=0, target_velocity=0,
        cost_actual=0, cost_budget=0
    )
    assert score == 0
    assert status == "Healthy"
