"""
Vercel Python Serverless Function — Plotcode Backend Entry Point

Uses FastAPI's native app.mount() to mount the agents app under /api prefix.
This keeps `app` as a FastAPI instance, which Vercel's AST-based detection requires.

Request flow:
  Browser: GET /api/auth/login
  → Vercel rewrite: /api/:path* → /api/index.py
  → FastAPI receives: /api/auth/login
  → app.mount("/api", agents_app) → delegates to agents_app with path /auth/login
  → agents_app matches /auth/login route → returns response
"""

import sys
import os
import importlib.util

from fastapi import FastAPI

# Create the top-level FastAPI app that Vercel will detect
app = FastAPI(title="Plotcode API Gateway")

# Add health endpoint at root (for Vercel health checks)
@app.get("/health")
async def root_health():
    return {"status": "ok", "service": "plotcode-vercel"}

# ─── Load the agents FastAPI app ─────────────────────────────────────────────
# Use importlib to avoid module name conflict between api/ dir and agents/api.py
AGENTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'agents')
sys.path.insert(0, AGENTS_DIR)

spec = importlib.util.spec_from_file_location(
    "plotcode_agents_api",
    os.path.join(AGENTS_DIR, "api.py")
)
plotcode_agents = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plotcode_agents)

# Mount the agents app under /api prefix
# All routes like /auth/login become accessible at /api/auth/login
app.mount("/api", plotcode_agents.app)
