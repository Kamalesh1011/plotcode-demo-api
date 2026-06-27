"""
Vercel Python Serverless Function — Plotcode Backend Entry Point

This file is the entry point for Vercel's Python runtime.
It imports the FastAPI app from agents/api.py and wraps it to handle
the /api path prefix that the frontend uses.

Vercel Limitations (handled in this setup):
  - No WebSocket → frontend uses polling fallback
  - Read-only filesystem → file uploads stored in MongoDB (not disk)
  - 10s timeout (free) / 60s (pro) → agent execution runs in background
  - Cold starts → first request may be slower
"""

import sys
import os

# Add the agents directory to Python path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents'))

# Import the FastAPI app
from api import app as fastapi_app


# ─── ASGI wrapper that strips /api prefix ────────────────────────────────────
# The frontend calls /api/auth/login, /api/requests, etc.
# But FastAPI routes are /auth/login, /requests (no /api prefix).
# This wrapper strips /api from the path before passing to FastAPI.

class PrefixStrippingASGI:
    """ASGI middleware that strips a path prefix before passing to the app."""

    def __init__(self, app, prefix="/api"):
        self.app = app
        self.prefix = prefix

    async def __call__(self, scope, receive, send):
        # Only modify HTTP requests
        if scope["type"] == "http":
            path = scope.get("path", "")
            # Strip the /api prefix if present
            if path.startswith(self.prefix):
                scope["path"] = path[len(self.prefix):] or "/"
                # Also update raw_path
                scope["raw_path"] = scope["path"].encode("utf-8")

        return await self.app(scope, receive, send)


# Export the wrapped app — Vercel uses the `app` variable as ASGI handler
app = PrefixStrippingASGI(fastapi_app, prefix="/api")
