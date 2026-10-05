"""
Simulated Authentication & RBAC — Intelligent Client Delivery Agent

Provides user_id-based context variables for authentication simulation.
Maps users to roles (manager/viewer/admin) and to their managed projects.

STEP UP (Production):
    - Replace with Microsoft Entra ID (Azure AD) integration
    - Use MSAL for token validation
    - Use managed identity for service-to-service auth
    - RBAC via Azure AD App Roles
"""
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("IntelligentDeliveryAgent")

# ── Simulated User Registry ──
# Maps user_id → user profile (role, display name, managed projects)
USER_REGISTRY = {
    "mgr123": {
        "display_name": "Sarah Chen",
        "role": "manager",
        "email": "sarah.chen@maqsoftware.com",
        "managed_projects": ["P-001", "P-002", "P-004"],
    },
    "mgr456": {
        "display_name": "Raj Patel",
        "role": "manager",
        "email": "raj.patel@maqsoftware.com",
        "managed_projects": ["P-003", "P-005"],
    },
    "admin001": {
        "display_name": "Admin User",
        "role": "admin",
        "email": "admin@maqsoftware.com",
        "managed_projects": [],  # Admin sees all
    },
    "viewer001": {
        "display_name": "Alex Viewer",
        "role": "viewer",
        "email": "alex.viewer@maqsoftware.com",
        "managed_projects": ["P-001"],  # Read-only access to P-001
    },
}


@dataclass
class AuthContext:
    """
    Represents the authenticated user context for a request.

    In production (Step Up), this would be populated from a decoded
    Entra ID JWT token via MSAL middleware.

    Attributes:
        user_id: Unique user identifier (simulated; maps to Entra ID OID in production)
        display_name: User's display name
        role: User role — 'admin', 'manager', or 'viewer'
        email: User email address
        managed_projects: List of project IDs the user manages/can access
        is_authenticated: Whether the user was found in the registry
    """
    user_id: str
    display_name: str = "Unknown User"
    role: str = "viewer"
    email: str = ""
    managed_projects: list = field(default_factory=list)
    is_authenticated: bool = False

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_manager(self) -> bool:
        return self.role == "manager"

    def can_access_project(self, project_id: str) -> bool:
        """Check if user has access to a specific project."""
        if self.is_admin:
            return True  # Admin sees everything
        return project_id in self.managed_projects

    def get_accessible_projects(self) -> Optional[list]:
        """
        Returns list of project IDs accessible to this user, or None if admin (all access).
        """
        if self.is_admin:
            return None  # None = no filter = see all
        return self.managed_projects


def authenticate_user(user_id: str) -> AuthContext:
    """
    Simulated authentication via user_id context variable.

    In production (Step Up):
        - Validate JWT Bearer token from Entra ID
        - Extract OID, roles, and groups from token claims
        - Map Azure AD App Roles to local roles
        - Use managed identity for downstream service calls

    Args:
        user_id: The user identifier (simulated Entra ID OID)

    Returns:
        AuthContext with user details and permissions
    """
    user_data = USER_REGISTRY.get(user_id)

    if user_data:
        ctx = AuthContext(
            user_id=user_id,
            display_name=user_data["display_name"],
            role=user_data["role"],
            email=user_data["email"],
            managed_projects=user_data["managed_projects"],
            is_authenticated=True,
        )
        logger.info(
            f"[Auth] Authenticated user: {ctx.display_name} (role={ctx.role}, "
            f"projects={ctx.managed_projects})"
        )
        return ctx
    else:
        logger.warning(f"[Auth] Unknown user_id='{user_id}'. Granting viewer-only access.")
        return AuthContext(
            user_id=user_id,
            display_name=f"User {user_id}",
            role="viewer",
            is_authenticated=False,
        )
