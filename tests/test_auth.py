"""
Unit Tests — Simulated Authentication & RBAC
Tests user authentication, role assignment, and project access control.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from utils.auth import authenticate_user, AuthContext


def test_known_manager():
    """Test: Known manager user should be authenticated with correct role."""
    ctx = authenticate_user("mgr123")
    assert ctx.is_authenticated is True
    assert ctx.role == "manager"
    assert ctx.display_name == "Sarah Chen"
    assert ctx.is_manager is True
    assert ctx.is_admin is False


def test_known_admin():
    """Test: Admin user should have admin role."""
    ctx = authenticate_user("admin001")
    assert ctx.is_authenticated is True
    assert ctx.role == "admin"
    assert ctx.is_admin is True


def test_unknown_user():
    """Test: Unknown user should get viewer role and not be authenticated."""
    ctx = authenticate_user("unknown_user")
    assert ctx.is_authenticated is False
    assert ctx.role == "viewer"


def test_project_access_manager():
    """Test: Manager should only access their managed projects."""
    ctx = authenticate_user("mgr123")
    assert ctx.can_access_project("P-001") is True
    assert ctx.can_access_project("P-002") is True
    assert ctx.can_access_project("P-003") is False  # mgr456's project


def test_project_access_admin():
    """Test: Admin should access all projects."""
    ctx = authenticate_user("admin001")
    assert ctx.can_access_project("P-001") is True
    assert ctx.can_access_project("P-002") is True
    assert ctx.can_access_project("P-003") is True
    assert ctx.can_access_project("P-999") is True  # Any project


def test_get_accessible_projects_manager():
    """Test: Manager should get their specific projects list."""
    ctx = authenticate_user("mgr123")
    accessible = ctx.get_accessible_projects()
    assert accessible is not None
    assert "P-001" in accessible
    assert "P-002" in accessible


def test_get_accessible_projects_admin():
    """Test: Admin should get None (no filter = see all)."""
    ctx = authenticate_user("admin001")
    accessible = ctx.get_accessible_projects()
    assert accessible is None


def test_viewer_limited_access():
    """Test: Viewer should have limited project access."""
    ctx = authenticate_user("viewer001")
    assert ctx.role == "viewer"
    assert ctx.can_access_project("P-001") is True
    assert ctx.can_access_project("P-002") is False
