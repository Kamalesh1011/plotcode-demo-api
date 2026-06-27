"""
API Authentication & RBAC Middleware

Provides:
  1. JWT token authentication (Bearer token) — primary for dashboard
  2. API key authentication via X-API-Key header — for programmatic access
  3. Role-based HTTP endpoint protection
  4. Request logging for audit trail
"""

import os
import logging
from functools import wraps
from typing import Callable, List, Optional

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import APIKeyHeader, HTTPBearer

logger = logging.getLogger(__name__)

# ─── API Key Auth ─────────────────────────────────────────────────────────────

_API_KEY = os.getenv("AGENT_API_KEY", "plotcode-dev-key-change-in-prod")

api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


async def require_api_key(x_api_key: Optional[str] = Depends(api_key_scheme)) -> str:
    """FastAPI dependency: validates X-API-Key header."""
    if not x_api_key or x_api_key != _API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return x_api_key


# ─── JWT Token Auth ───────────────────────────────────────────────────────────

async def get_current_user(request: Request) -> Optional[dict]:
    """
    Extract the authenticated user from a JWT Bearer token.
    Returns user dict or None if not authenticated.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    from shared.auth import decode_token, get_auth_store
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    try:
        store = get_auth_store()
        user = store.get_by_id(user_id)
        if user:
            return user
    except Exception:
        pass
    # Fall back to token payload if user not in DB (e.g. env admin)
    return {
        "id": user_id,
        "username": payload.get("username", ""),
        "role": payload.get("role", "requester"),
        "name": payload.get("name", ""),
    }


async def require_auth(user: Optional[dict] = Depends(get_current_user)) -> dict:
    """FastAPI dependency: requires a valid JWT Bearer token."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# ─── Role-Based Permission Map ────────────────────────────────────────────────

# Matches telegram_rbac.py ROLE_PERMISSIONS
ROLE_PERMISSIONS = {
    "admin":         {"*"},   # all permissions
    "product_owner": {"read", "approve_request", "approve_plan", "reject_request", "reject_plan", "approve_qa"},
    "developer":     {"read", "approve_plan", "reject_plan", "merge_pr"},
    "qa_engineer":   {"read", "approve_qa", "fail_qa"},
    "requester":     {"read", "submit_request"},
}


def _has_permission(role: str, permission: str) -> bool:
    perms = ROLE_PERMISSIONS.get(role, set())
    return "*" in perms or permission in perms


async def get_current_user_role(request: Request) -> str:
    """
    Extract the caller's role — checks JWT token first, then X-Telegram-ID.
    Defaults to 'requester' for unauthenticated requests (read-only).
    """
    # Try JWT token first
    user = await get_current_user(request)
    if user:
        return user.get("role", "requester")

    # Fall back to Telegram ID header
    telegram_id = request.headers.get("X-Telegram-ID")
    if not telegram_id:
        return "requester"
    try:
        from shared.state import get_state_store
        store = get_state_store()
        user = store.get_user(telegram_id=telegram_id)
        if user:
            return user.get("role", "requester")
    except Exception:
        pass
    return "requester"


def require_role(*allowed_roles: str):
    """
    FastAPI dependency factory that restricts access to specified roles.

    Usage:
        @app.post("/admin/action", dependencies=[Depends(require_role("admin"))])
    """
    async def _check(role: str = Depends(get_current_user_role)):
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' is not authorized. Required: {list(allowed_roles)}",
            )
        return role
    return _check


def require_permission(permission: str):
    """
    FastAPI dependency factory that restricts by permission string.

    Usage:
        @app.post("/approve", dependencies=[Depends(require_permission("approve_request"))])
    """
    async def _check(role: str = Depends(get_current_user_role)):
        if not _has_permission(role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' denied for role '{role}'.",
            )
        return role
    return _check
