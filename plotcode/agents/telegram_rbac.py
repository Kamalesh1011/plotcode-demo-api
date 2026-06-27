"""
RBAC enforcement for the Plotcode Telegram bot.
Checks user roles before allowing sensitive actions.
"""

import os
import logging
from typing import Optional, List
from shared.state import get_state_store

logger = logging.getLogger(__name__)

# Role hierarchy - each role inherits permissions from roles below it
ROLE_PERMISSIONS = {
    "admin": [
        "submit_request",
        "approve_request",
        "reject_request",
        "approve_plan",
        "reject_plan",
        "merge_pr",
        "approve_qa",
        "fail_qa",
        "approve_prod",
        "hold_prod",
        "list_requests",
        "view_audit",
        "manage_users",
    ],
    "product_owner": [
        "submit_request",
        "approve_request",
        "reject_request",
        "approve_plan",
        "reject_plan",
        "approve_qa",
        "list_requests",
        "view_audit",
    ],
    "developer": [
        "submit_request",
        "approve_plan",
        "reject_plan",
        "merge_pr",
        "list_requests",
        "view_audit",
    ],
    "qa_engineer": [
        "submit_request",
        "approve_qa",
        "fail_qa",
        "list_requests",
    ],
    "requester": [
        "submit_request",
    ],
}

# Bootstrap admin IDs from environment (comma-separated Telegram user IDs)
BOOTSTRAP_ADMIN_IDS = [
    uid.strip()
    for uid in os.getenv("ADMIN_TELEGRAM_IDS", "").split(",")
    if uid.strip()
]


class RBACChecker:
    """Checks if a Telegram user has permission to perform an action."""

    def __init__(self):
        self.store = get_state_store()

    def get_user_role(self, telegram_id: str) -> str:
        """Get the role for a Telegram user. Bootstrap admins always get admin."""
        if telegram_id in BOOTSTRAP_ADMIN_IDS:
            return "admin"

        user = self.store.get_user(telegram_id=telegram_id)
        if user and user.get("is_active"):
            return user.get("role", "requester")

        # Auto-register unknown users as requesters
        return "requester"

    def can(self, telegram_id: str, permission: str) -> bool:
        """Check if a user has a specific permission."""
        role = self.get_user_role(telegram_id)
        allowed = ROLE_PERMISSIONS.get(role, [])
        return permission in allowed

    def require(self, telegram_id: str, permission: str) -> None:
        """Raise PermissionError if user lacks the permission."""
        if not self.can(telegram_id, permission):
            role = self.get_user_role(telegram_id)
            raise PermissionError(
                f"Access denied. Your role '{role}' cannot perform '{permission}'."
            )

    def ensure_user_exists(self, telegram_id: str, name: str, username: Optional[str] = None) -> dict:
        """Create user in DB if they don't exist yet."""
        import uuid
        from datetime import datetime, timezone

        existing = self.store.get_user(telegram_id=telegram_id)
        if existing:
            return existing

        # Determine role
        role = "admin" if telegram_id in BOOTSTRAP_ADMIN_IDS else "requester"

        user_data = {
            "id": str(uuid.uuid4()),
            "telegram_id": telegram_id,
            "name": name or username or f"user_{telegram_id}",
            "team": None,
            "role": role,
            "is_active": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        self.store.create_user(user_data)
        return self.store.get_user(telegram_id=telegram_id) or {}

    def list_users(self) -> List[dict]:
        """List all users."""
        return self.store.list_users()

    def set_role(self, telegram_id: str, new_role: str) -> bool:
        """Change a user's role (admin only action)."""
        if new_role not in ROLE_PERMISSIONS:
            return False
        return self.store.update_user_role(telegram_id, new_role)


_rbac: Optional[RBACChecker] = None


def get_rbac() -> RBACChecker:
    global _rbac
    if _rbac is None:
        _rbac = RBACChecker()
    return _rbac
