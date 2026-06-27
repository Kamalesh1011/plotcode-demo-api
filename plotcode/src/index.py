"""
Vercel Python Serverless Function — Plotcode Backend Entry Point

Located in src/ (not api/) to avoid module name conflict with agents/api.py.
Vercel detects FastAPI apps in src/index.py automatically.

This file:
  1. Creates a FastAPI app (so Vercel's AST detection finds it)
  2. Adds agents/ to sys.path
  3. Imports the agents FastAPI app
  4. Mounts it under /api prefix
"""

import sys
import os

from fastapi import FastAPI

# Create the top-level FastAPI app that Vercel will detect
app = FastAPI(title="Plotcode API Gateway")

# Health endpoint at root
@app.get("/health")
async def root_health():
    return {"status": "ok", "service": "plotcode-vercel"}

# ─── Load the agents FastAPI app ─────────────────────────────────────────────
# Add agents/ to sys.path so `from api import app` finds agents/api.py
# (not src/api.py or any other api module)
AGENTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..',
    'agents'
)
sys.path.insert(0, AGENTS_DIR)

# Now import the agents app — since agents/ is first in sys.path,
# `api` resolves to agents/api.py
from api import app as agents_app

# Mount the agents app under /api prefix
# Routes like /auth/login become accessible at /api/auth/login
app.mount("/api", agents_app)
