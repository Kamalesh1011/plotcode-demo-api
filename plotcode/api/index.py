"""
Vercel Python Serverless Function — Plotcode Backend Entry Point

This file is the entry point for Vercel's Python runtime.
It imports the FastAPI app from agents/api.py and exports it.

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

# Import the FastAPI app — Vercel detects the `app` variable
from api import app

# Vercel Python runtime automatically uses the `app` variable as ASGI handler
