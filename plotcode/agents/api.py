"""
Plotcode Agent API v3 — Production-grade FastAPI server.

New in v3:
  - WebSocket /ws/events — real-time event streaming to dashboard
  - GET  /metrics        — aggregated pipeline metrics
  - GET  /requests/search — full-text search
  - POST /requests/bulk   — bulk status updates
  - GET  /audit/export    — CSV/JSON audit export
  - GET  /prompts         — AI prompt log explorer
  - GET  /agents/status   — live agent health
  - RBAC middleware on write endpoints
  - API key authentication
"""

import asyncio
import csv
import io
import json
import logging
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    HTTPException,
    Query,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

# Agents
from analysis_agent import AnalysisAgent
from coder_agent import CoderAgent
from validation_agent import ValidationAgent
from pr_agent import PRAgent
from deployment_agent import DeploymentAgent
from monitoring_agent import MonitoringAgent

# Shared
from shared.state import get_state_store
from shared.events import get_event_bus, EventTypes
from shared.auth import (
    get_auth_store, create_token_pair, decode_token,
    get_github_oauth_url, exchange_github_code,
    get_google_oauth_url, exchange_google_code,
)
from middleware.auth import get_current_user, require_auth

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("api")

# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Plotcode Delivery Automation API",
    version="3.0.0",
    description="AI-assisted end-to-end delivery automation platform",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Agent Registry ───────────────────────────────────────────────────────────

_agents: Dict[str, Any] = {}


def _get_agents() -> Dict[str, Any]:
    global _agents
    if not _agents:
        _agents = {
            "analysis":   AnalysisAgent(),
            "coding":     CoderAgent(),
            "validation": ValidationAgent(),
            "pr":         PRAgent(),
            "deployment": DeploymentAgent(),
            "monitoring": MonitoringAgent(),
        }
    return _agents


# ─── Pydantic Models ──────────────────────────────────────────────────────────

class TriggerRequest(BaseModel):
    request_id: str
    agent: str
    payload: Dict[str, Any] = {}


class CIWebhookPayload(BaseModel):
    repo: str
    branch: str
    status: str          # "success" | "failure" | "cancelled"
    sha: Optional[str] = None
    run_id: Optional[str] = None
    logs_url: Optional[str] = None
    error_summary: Optional[str] = None


class CreateRequestBody(BaseModel):
    title: str
    business_need: str
    expected_behavior: str
    priority: str = "P2"
    affected_service: str = "demo-api"
    requester_name: str = "api-user"
    requester_team: Optional[str] = None
    source: str = "api"


class BulkUpdateBody(BaseModel):
    request_ids: List[str]
    new_status: str
    actor_id: str = "api"


class ApprovalBody(BaseModel):
    actor_id: str
    reason: Optional[str] = None


# ─── Auth Models ──────────────────────────────────────────────────────────────

class LoginBody(BaseModel):
    username: str
    password: str


class RegisterBody(BaseModel):
    username: str
    password: str
    email: str = ""
    name: str = ""
    role: str = "requester"


class RefreshBody(BaseModel):
    refresh_token: str


class GitHubCallbackBody(BaseModel):
    code: str
    state: Optional[str] = None


class GoogleCallbackBody(BaseModel):
    code: str
    state: Optional[str] = None


class ChatMessage(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health():
    store = get_state_store()
    return {
        "status": "ok",
        "service": "plotcode-agents",
        "version": "3.0.0",
        "db": store.db_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "websocket_subscribers": get_event_bus().subscriber_count,
    }


# ─── Authentication ───────────────────────────────────────────────────────────

@app.post("/auth/login", tags=["Auth"])
async def login(body: LoginBody):
    """Authenticate with username/password and receive JWT tokens."""
    store = get_auth_store()
    user = store.authenticate(body.username, body.password)
    if not user:
        raise HTTPException(401, "Invalid username or password")
    tokens = create_token_pair(user)
    return {"user": user, **tokens}


@app.post("/auth/register", tags=["Auth"])
async def register(body: RegisterBody):
    """Register a new user account."""
    store = get_auth_store()
    existing = store.get_by_username(body.username)
    if existing:
        raise HTTPException(409, f"Username '{body.username}' already exists")
    user = store.create_user(
        username=body.username,
        password=body.password,
        email=body.email,
        name=body.name,
        role=body.role,
    )
    tokens = create_token_pair(user)
    return {"user": user, **tokens}


@app.post("/auth/refresh", tags=["Auth"])
async def refresh_token(body: RefreshBody):
    """Exchange a refresh token for a new access token."""
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid or expired refresh token")
    store = get_auth_store()
    user = store.get_by_id(payload.get("sub"))
    if not user:
        raise HTTPException(401, "User not found")
    tokens = create_token_pair(user)
    return tokens


@app.get("/auth/me", tags=["Auth"])
async def get_me(user: dict = Depends(require_auth)):
    """Get the current authenticated user's profile."""
    return {"user": user}


@app.get("/auth/github", tags=["Auth"])
async def github_oauth_url():
    """Get the GitHub OAuth authorization URL."""
    if not os.getenv("GITHUB_CLIENT_ID"):
        raise HTTPException(503, "GitHub OAuth not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET.")
    state = os.urandom(16).hex()
    return {"url": get_github_oauth_url(state=state), "state": state}


@app.post("/auth/github/callback", tags=["Auth"])
async def github_oauth_callback(body: GitHubCallbackBody):
    """Handle GitHub OAuth callback — exchange code for token, upsert user."""
    github_data = exchange_github_code(body.code)
    if not github_data:
        raise HTTPException(400, "Failed to exchange GitHub OAuth code")
    store = get_auth_store()
    user = store.upsert_github_user(github_data)
    tokens = create_token_pair(user)
    return {"user": user, **tokens}


@app.post("/auth/github/link", tags=["Auth"])
async def link_github_account(body: GitHubCallbackBody, user: dict = Depends(require_auth)):
    """Link a GitHub account to the current authenticated user."""
    github_data = exchange_github_code(body.code)
    if not github_data:
        raise HTTPException(400, "Failed to exchange GitHub OAuth code. Check that GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, and GITHUB_OAUTH_REDIRECT_URI are correct in .env")
    store = get_auth_store()
    updated = store.link_github(user["id"], github_data)
    if not updated:
        raise HTTPException(404, "User not found in auth store")
    return {"user": updated}


@app.get("/auth/google", tags=["Auth"])
async def google_oauth_url():
    """Get the Google OAuth authorization URL."""
    if not os.getenv("GOOGLE_CLIENT_ID"):
        raise HTTPException(503, "Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.")
    state = os.urandom(16).hex()
    return {"url": get_google_oauth_url(state=state), "state": state}


@app.post("/auth/google/callback", tags=["Auth"])
async def google_oauth_callback(body: GoogleCallbackBody):
    """Handle Google OAuth callback — exchange code for token, upsert user."""
    google_data = exchange_google_code(body.code)
    if not google_data:
        raise HTTPException(400, "Failed to exchange Google OAuth code")
    store = get_auth_store()
    user = store.upsert_google_user(google_data)
    tokens = create_token_pair(user)
    return {"user": user, **tokens}


@app.post("/auth/google/link", tags=["Auth"])
async def link_google_account(body: GoogleCallbackBody, user: dict = Depends(require_auth)):
    """Link a Google account to the current authenticated user."""
    google_data = exchange_google_code(body.code)
    if not google_data:
        raise HTTPException(400, "Failed to exchange Google OAuth code. Check that GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_OAUTH_REDIRECT_URI are correct in .env")
    store = get_auth_store()
    updated = store.link_google(user["id"], google_data)
    if not updated:
        raise HTTPException(404, "User not found in auth store")
    return {"user": updated}


@app.get("/auth/users", tags=["Auth"])
async def list_auth_users(user: dict = Depends(require_auth)):
    """List all authenticated users (admin only)."""
    if user.get("role") != "admin":
        raise HTTPException(403, "Admin access required")
    store = get_auth_store()
    return {"users": store.list_users()}


# ─── WebSocket Live Events ────────────────────────────────────────────────────

@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard updates.
    Clients receive JSON events whenever any pipeline state changes.
    """
    bus = get_event_bus()
    await websocket.accept()
    queue = await bus.subscribe()
    logger.info(f"[WS] Client connected. Total subscribers: {bus.subscriber_count}")
    try:
        # Send a welcome event
        await websocket.send_text(json.dumps({
            "type": "connection.established",
            "payload": {"message": "Connected to Plotcode live event stream"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }))
        while True:
            # Wait for events OR ping client every 30s to keep alive
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                await websocket.send_text(event.to_json())
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        logger.info("[WS] Client disconnected")
    except Exception as e:
        logger.error(f"[WS] Error: {e}")
    finally:
        await bus.unsubscribe(queue)


# ─── Requests ─────────────────────────────────────────────────────────────────

@app.get("/requests", tags=["Requests"])
async def list_requests(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    skip: int = Query(0),
):
    store = get_state_store()
    return {
        "requests": store.list_requests(status=status, priority=priority, service=service, limit=limit, skip=skip),
        "total": store.count_requests(),
    }


@app.get("/requests/search", tags=["Requests"])
async def search_requests(q: str = Query(..., min_length=2)):
    store = get_state_store()
    results = store.search_requests(q)
    return {"results": results, "count": len(results), "query": q}


@app.post("/requests", tags=["Requests"], status_code=201)
async def create_request(body: CreateRequestBody, background_tasks: BackgroundTasks):
    store = get_state_store()
    bus = get_event_bus()
    data = body.model_dump()
    req = store.create_request(data)
    store.log_audit(req["request_id"], "api", "api-user", "request_created", {
        "title": req["title"],
        "priority": req["priority"],
    })
    background_tasks.add_task(
        bus.publish, EventTypes.REQUEST_CREATED,
        {"request_id": req["request_id"], "title": req["title"], "priority": req["priority"]}
    )
    return req


@app.get("/requests/{request_id}", tags=["Requests"])
async def get_request(request_id: str):
    store = get_state_store()
    req = store.get_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return req


@app.patch("/requests/{request_id}", tags=["Requests"])
async def update_request(request_id: str, updates: Dict[str, Any]):
    store = get_state_store()
    req = store.get_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    updated = store.update_request(request_id, updates)
    bus = get_event_bus()
    asyncio.ensure_future(bus.publish(EventTypes.REQUEST_UPDATED, {
        "request_id": request_id, "updates": updates
    }))
    return updated


@app.post("/requests/bulk", tags=["Requests"])
async def bulk_update(body: BulkUpdateBody):
    store = get_state_store()
    count = store.bulk_update_status(body.request_ids, body.new_status, body.actor_id)
    return {"updated": count, "status": body.new_status}


@app.post("/requests/{request_id}/approve", tags=["Requests"])
async def approve_request(request_id: str, body: ApprovalBody, background_tasks: BackgroundTasks):
    store = get_state_store()
    bus = get_event_bus()
    req = store.get_request(request_id)
    if not req:
        raise HTTPException(404, "Request not found")
    store.update_request(request_id, {
        "status": "approved",
        "initial_approver_slack_id": body.actor_id,
        "initial_approved_at": datetime.now(timezone.utc).isoformat(),
    })
    store.log_audit(request_id, "human", body.actor_id, "request_approved", {})
    background_tasks.add_task(bus.publish, EventTypes.REQUEST_APPROVED, {"request_id": request_id})
    # Trigger analysis agent automatically
    background_tasks.add_task(_run_agent_bg, "analysis", request_id, {})
    return {"status": "approved", "request_id": request_id}


@app.get("/requests/{request_id}/audit", tags=["Requests"])
async def get_audit(request_id: str):
    store = get_state_store()
    logs = store.get_audit_log(request_id)
    return {"request_id": request_id, "logs": logs}


# ─── Agent Trigger ─────────────────────────────────────────────────────────────

@app.post("/trigger", tags=["Agents"])
async def trigger_agent(req: TriggerRequest, background_tasks: BackgroundTasks):
    agents = _get_agents()
    agent = agents.get(req.agent)
    if not agent:
        raise HTTPException(400, f"Unknown agent: {req.agent}. Valid: {list(agents.keys())}")
    background_tasks.add_task(_run_agent_bg, req.agent, req.request_id, req.payload)
    return {"status": "triggered", "request_id": req.request_id, "agent": req.agent}


@app.post("/trigger/sync", tags=["Agents"])
async def trigger_agent_sync(req: TriggerRequest):
    agents = _get_agents()
    agent = agents.get(req.agent)
    if not agent:
        raise HTTPException(400, f"Unknown agent: {req.agent}")
    try:
        result = _run_agent_sync(req.agent, req.request_id, req.payload)
        return {"status": "completed", "result": result}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/agents/status", tags=["Agents"])
async def agents_status():
    """Return live status of all registered agents."""
    store = get_state_store()
    agents_info = []
    for name in ["analysis", "coding", "validation", "pr", "deployment", "monitoring"]:
        # Get last run from prompt log
        logs = store.get_prompt_logs(agent_name=name, limit=1)
        last_run = logs[0] if logs else None
        agents_info.append({
            "name": name,
            "status": "ready",
            "last_run_at": last_run.get("created_at") if last_run else None,
            "last_success": last_run.get("success") if last_run else None,
            "avg_confidence": last_run.get("confidence_score") if last_run else None,
            "model": last_run.get("model") if last_run else None,
        })
    return {"agents": agents_info}


# ─── Metrics ──────────────────────────────────────────────────────────────────

@app.get("/metrics", tags=["Metrics"])
async def get_metrics():
    """Aggregated pipeline metrics for dashboard charts."""
    store = get_state_store()
    return store.get_metrics()


# ─── Prompts ──────────────────────────────────────────────────────────────────

@app.get("/prompts", tags=["AI Prompts"])
async def get_prompt_logs(
    request_id: Optional[str] = Query(None),
    agent_name: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
):
    store = get_state_store()
    logs = store.get_prompt_logs(request_id=request_id, agent_name=agent_name, limit=limit)
    return {"logs": logs, "count": len(logs)}


# ─── Users & RBAC ─────────────────────────────────────────────────────────────

@app.get("/users", tags=["RBAC"])
async def list_users():
    from telegram_rbac import get_rbac
    rbac = get_rbac()
    return {"users": rbac.list_users()}


@app.get("/users/{telegram_id}", tags=["RBAC"])
async def get_user(telegram_id: str):
    from telegram_rbac import get_rbac
    rbac = get_rbac()
    role = rbac.get_user_role(telegram_id)
    user = rbac.ensure_user_exists(telegram_id, name=f"User {telegram_id}")
    return {"telegram_id": telegram_id, "role": role, "name": user.get("name")}


@app.patch("/users/{telegram_id}/role", tags=["RBAC"])
async def update_user_role(telegram_id: str, body: Dict[str, str]):
    new_role = body.get("role")
    if not new_role:
        raise HTTPException(400, "role field required")
    from telegram_rbac import get_rbac, ROLE_PERMISSIONS
    if new_role not in ROLE_PERMISSIONS:
        raise HTTPException(400, f"Invalid role. Valid: {list(ROLE_PERMISSIONS.keys())}")
    rbac = get_rbac()
    success = rbac.set_role(telegram_id, new_role)
    if not success:
        raise HTTPException(404, "User not found")
    return {"telegram_id": telegram_id, "role": new_role, "updated": True}


# ─── Services ─────────────────────────────────────────────────────────────────

@app.get("/services", tags=["Services"])
async def list_services():
    store = get_state_store()
    return {"services": store.list_services()}


# ─── Audit Export ─────────────────────────────────────────────────────────────

@app.get("/audit/export", tags=["Audit"])
async def export_audit(
    format: str = Query("json", pattern="^(json|csv)$"),
    request_id: Optional[str] = Query(None),
):
    store = get_state_store()
    if request_id:
        logs = store.get_audit_log(request_id)
    else:
        logs = store.get_all_audit_logs(limit=5000)

    if format == "csv":
        output = io.StringIO()
        if logs:
            writer = csv.DictWriter(output, fieldnames=logs[0].keys())
            writer.writeheader()
            writer.writerows(logs)
        csv_content = output.getvalue()
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=audit_log.csv"},
        )
    return {"logs": logs, "count": len(logs)}


# ─── AI Chat ──────────────────────────────────────────────────────────────────

def _build_dashboard_context(store, body: ChatMessage) -> str:
    """Fetch live dashboard data and build a context string for the LLM."""
    parts = []

    try:
        # Fetch all requests
        all_reqs = store.list_requests(limit=500)
        total = len(all_reqs)

        # Count by status
        status_counts = {}
        for r in all_reqs:
            s = r.get("status", "unknown")
            status_counts[s] = status_counts.get(s, 0) + 1

        # Count by priority
        priority_counts = {}
        for r in all_reqs:
            p = r.get("priority", "unknown")
            priority_counts[p] = priority_counts.get(p, 0) + 1

        parts.append(f"DASHBOARD DATA (live):")
        parts.append(f"  Total requests: {total}")
        parts.append(f"  Status breakdown: {status_counts}")
        parts.append(f"  Priority breakdown: {priority_counts}")

        # Recent requests (last 10)
        recent = all_reqs[:10]
        if recent:
            parts.append(f"  Recent requests (last 10):")
            for r in recent:
                parts.append(
                    f"    - {r.get('request_id','?')} | {r.get('status','?')} | "
                    f"{r.get('priority','?')} | {r.get('title','?')[:60]} | "
                    f"service: {r.get('affected_service','?')} | "
                    f"confidence: {r.get('ai_confidence','—')}%"
                )

        # Requests needing action
        pending_approval = [r for r in all_reqs if r.get("status") == "plan_pending_approval"]
        ci_failed = [r for r in all_reqs if r.get("status") == "ci_failed"]
        pr_open = [r for r in all_reqs if r.get("status") == "pr_open"]
        qa_deployed = [r for r in all_reqs if r.get("status") == "qa_deployed"]

        parts.append(f"  Needs attention:")
        parts.append(f"    Plans awaiting approval: {len(pending_approval)}")
        parts.append(f"    CI failures (escalated): {len(ci_failed)}")
        parts.append(f"    PRs open: {len(pr_open)}")
        parts.append(f"    QA deployed (awaiting validation): {len(qa_deployed)}")

        # Agent status (same logic as /agents/status endpoint)
        try:
            agent_names = ["analysis", "coding", "validation", "pr", "deployment", "monitoring"]
            parts.append(f"  Agent status:")
            for name in agent_names:
                logs = store.get_prompt_logs(agent_name=name, limit=1)
                last_run = logs[0] if logs else None
                parts.append(
                    f"    - {name} | status: ready | "
                    f"last_run: {last_run.get('created_at', 'never') if last_run else 'never'} | "
                    f"confidence: {last_run.get('confidence_score', '—') if last_run else '—'}"
                )
        except Exception:
            pass

        # Metrics summary
        try:
            metrics = store.get_metrics()
            if metrics:
                # Summarize key metrics
                parts.append(f"  Metrics summary:")
                for k, v in metrics.items():
                    if isinstance(v, (int, float, str)):
                        parts.append(f"    {k}: {v}")
                    elif isinstance(v, dict):
                        parts.append(f"    {k}: {v}")
        except Exception:
            pass

        # SLA breaches
        sla_breached = [r for r in all_reqs if r.get("sla_breach_alert_sent")]
        parts.append(f"  SLA breaches: {len(sla_breached)}")

    except Exception as e:
        parts.append(f"  (Error fetching data: {e})")

    # User context from frontend
    if body.context:
        ctx = body.context
        if ctx.get("page"):
            parts.append(f"  User is currently on page: {ctx['page']}")
        if ctx.get("request_id"):
            parts.append(f"  User is viewing request: {ctx['request_id']}")

    return "\n".join(parts)


@app.post("/chat", tags=["AI"])
async def chat(body: ChatMessage, user: dict = Depends(require_auth)):
    """
    AI chatbot endpoint — uses a fast model via OpenRouter.
    Fetches live dashboard data so the assistant can answer questions with real numbers.
    """
    from shared.llm_client import get_llm_client
    chat_model = os.getenv("CHAT_LLM_MODEL", "openai/gpt-4o-mini")
    llm = get_llm_client(model=chat_model)

    store = get_state_store()

    # Build live dashboard context
    dashboard_data = _build_dashboard_context(store, body)

    system = (
        "You are Plotcode Assistant, an AI helper integrated into the Plotcode "
        "delivery automation dashboard. You have access to LIVE dashboard data "
        "shown below. Answer questions using this real data — give specific numbers, "
        "counts, and details. Do NOT tell users to check the dashboard; instead, "
        "give them the answer directly from the data provided.\n\n"
        "When asked about counts (e.g. 'how many approved'), count from the status "
        "breakdown data. When asked about specific requests, reference them by ID. "
        "Be concise but specific. Use bullet points for lists.\n\n"
        f"{dashboard_data}"
    )

    try:
        response = llm.generate(
            body.message,
            system=system,
            agent_name="chat_assistant",
            temperature=0.5,
            max_tokens=1024,
        )
        return {"response": response, "model": chat_model}
    except Exception as e:
        raise HTTPException(500, f"Chat failed: {e}")


# ─── GitHub: Repos, Branches, Commits, PRs ────────────────────────────────────

@app.get("/repos", tags=["GitHub"])
async def list_repos(user: dict = Depends(require_auth)):
    """List registered services/repos."""
    store = get_state_store()
    return {"repos": store.list_services()}


@app.get("/repos/{repo_name}/branches", tags=["GitHub"])
async def list_branches(repo_name: str, user: dict = Depends(require_auth)):
    """List branches in a repo (local or via GitHub API)."""
    from shared.git_client import get_git_client
    git = get_git_client()
    if git._is_local_fallback():
        from git import Repo
        import os
        local_path = os.path.join(git._workspace, repo_name)
        try:
            repo = Repo(local_path)
            branches = [{"name": h.name, "commit": h.commit.hexsha[:7]} for h in repo.heads]
            return {"branches": branches}
        except Exception as e:
            raise HTTPException(404, f"Repo not found: {e}")
    try:
        gh = git._get_github()
        repo = gh.get_repo(f"{git.org}/{repo_name}")
        branches = [{"name": b.name, "commit": b.commit.sha[:7]} for b in repo.get_branches()]
        return {"branches": branches}
    except Exception as e:
        raise HTTPException(500, f"Failed to list branches: {e}")


@app.get("/repos/{repo_name}/commits", tags=["GitHub"])
async def list_commits(
    repo_name: str,
    branch: str = Query("main"),
    limit: int = Query(20, le=100),
    user: dict = Depends(require_auth),
):
    """List recent commits on a branch."""
    from shared.git_client import get_git_client
    git = get_git_client()
    if git._is_local_fallback():
        from git import Repo
        import os
        local_path = os.path.join(git._workspace, repo_name)
        try:
            repo = Repo(local_path)
            if branch in repo.heads:
                repo.git.checkout(branch)
            commits = []
            for c in list(repo.iter_commits(max_count=limit)):
                commits.append({
                    "sha": c.hexsha[:7],
                    "message": c.message.strip().split("\n")[0][:100],
                    "author": str(c.author),
                    "date": c.committed_datetime.isoformat(),
                })
            return {"commits": commits}
        except Exception as e:
            raise HTTPException(404, f"Repo not found: {e}")
    try:
        gh = git._get_github()
        repo = gh.get_repo(f"{git.org}/{repo_name}")
        commits = []
        for c in repo.get_commits(sha=branch)[:limit]:
            commits.append({
                "sha": c.sha[:7],
                "message": c.commit.message.strip().split("\n")[0][:100],
                "author": c.commit.author.name,
                "date": c.commit.author.date.isoformat() if c.commit.author.date else None,
            })
        return {"commits": commits}
    except Exception as e:
        raise HTTPException(500, f"Failed to list commits: {e}")


@app.get("/repos/{repo_name}/pulls", tags=["GitHub"])
async def list_pulls(
    repo_name: str,
    state: str = Query("open", pattern="^(open|closed|all)$"),
    limit: int = Query(20, le=100),
    user: dict = Depends(require_auth),
):
    """List pull requests in a repo."""
    from shared.git_client import get_git_client
    git = get_git_client()
    if git._is_local_fallback():
        return {"pulls": [], "note": "PR listing requires GitHub API (online mode)"}
    try:
        gh = git._get_github()
        repo = gh.get_repo(f"{git.org}/{repo_name}")
        pulls = []
        for pr in repo.get_pulls(state=state)[:limit]:
            pulls.append({
                "number": pr.number,
                "title": pr.title,
                "state": pr.state,
                "author": pr.user.login if pr.user else "",
                "head": pr.head.ref,
                "base": pr.base.ref,
                "url": pr.html_url,
                "created_at": pr.created_at.isoformat() if pr.created_at else None,
                "merged": pr.merged,
            })
        return {"pulls": pulls}
    except Exception as e:
        raise HTTPException(500, f"Failed to list PRs: {e}")


@app.get("/repos/{repo_name}/issues", tags=["GitHub"])
async def list_issues(
    repo_name: str,
    state: str = Query("open", pattern="^(open|closed|all)$"),
    limit: int = Query(20, le=100),
    user: dict = Depends(require_auth),
):
    """List issues in a repo."""
    from shared.git_client import get_git_client
    git = get_git_client()
    if git._is_local_fallback():
        return {"issues": [], "note": "Issue listing requires GitHub API (online mode)"}
    try:
        gh = git._get_github()
        repo = gh.get_repo(f"{git.org}/{repo_name}")
        issues = []
        for issue in repo.get_issues(state=state)[:limit]:
            if issue.pull_request:  # Skip PRs (they show up in issues API)
                continue
            issues.append({
                "number": issue.number,
                "title": issue.title,
                "state": issue.state,
                "author": issue.user.login if issue.user else "",
                "url": issue.html_url,
                "labels": [l.name for l in issue.labels],
                "created_at": issue.created_at.isoformat() if issue.created_at else None,
            })
        return {"issues": issues}
    except Exception as e:
        raise HTTPException(500, f"Failed to list issues: {e}")


@app.get("/repos/{repo_name}/contents", tags=["GitHub"])
async def get_repo_contents(
    repo_name: str,
    path: str = Query(""),
    ref: str = Query("main"),
    user: dict = Depends(require_auth),
):
    """Browse repo file tree (file browser feature)."""
    from shared.git_client import get_git_client
    git = get_git_client()
    try:
        items = git.get_repo_contents(repo_name, path, ref)
        return {"items": items, "path": path, "ref": ref}
    except Exception as e:
        raise HTTPException(500, f"Failed to list contents: {e}")


@app.get("/repos/{repo_name}/file", tags=["GitHub"])
async def get_file_content(
    repo_name: str,
    path: str = Query(...),
    ref: str = Query("main"),
    user: dict = Depends(require_auth),
):
    """Read a file's content (file viewer feature)."""
    from shared.git_client import get_git_client
    git = get_git_client()
    try:
        content = git.get_file_via_api(repo_name, path, ref)
        return {"path": path, "content": content, "ref": ref}
    except Exception as e:
        raise HTTPException(500, f"Failed to read file: {e}")


@app.get("/repos/{repo_name}/check-runs", tags=["GitHub"])
async def list_check_runs(
    repo_name: str,
    branch: str = Query("main"),
    user: dict = Depends(require_auth),
):
    """List CI check runs for a branch (pipelines feature)."""
    from shared.git_client import get_git_client
    git = get_git_client()
    sha = git.get_branch_sha(repo_name, branch)
    if not sha:
        raise HTTPException(404, f"Could not find branch '{branch}'")
    runs = git.list_check_runs(repo_name, sha)
    return {"check_runs": runs, "sha": sha[:7], "branch": branch}


# ─── Webhooks CRUD ────────────────────────────────────────────────────────────

@app.get("/webhooks", tags=["Webhooks"])
async def list_webhooks(user: dict = Depends(require_auth)):
    """List all registered webhooks."""
    store = get_state_store()
    hooks = store.db.webhooks.find({})
    return {"webhooks": [{**{k: v for k, v in h.items() if k != '_id'}} for h in hooks]}


@app.post("/webhooks", tags=["Webhooks"])
async def create_webhook(
    url: str = Query(...),
    events: str = Query("push,pull_request"),
    user: dict = Depends(require_auth),
):
    """Register a new webhook endpoint."""
    store = get_state_store()
    import uuid as _uuid
    doc = {
        "id": str(_uuid.uuid4()),
        "url": url,
        "events": events.split(","),
        "active": True,
        "created_by": user.get("username", "unknown"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    store.db.webhooks.insert_one(doc)
    doc.pop("_id", None)
    return {"webhook": doc}


@app.patch("/webhooks/{webhook_id}", tags=["Webhooks"])
async def update_webhook(webhook_id: str, active: bool = Query(...), user: dict = Depends(require_auth)):
    """Toggle webhook active status."""
    store = get_state_store()
    result = store.db.webhooks.update_one({"id": webhook_id}, {"$set": {"active": active}})
    if result.modified_count == 0:
        raise HTTPException(404, "Webhook not found")
    return {"updated": True}


@app.delete("/webhooks/{webhook_id}", tags=["Webhooks"])
async def delete_webhook(webhook_id: str, user: dict = Depends(require_auth)):
    """Delete a webhook."""
    store = get_state_store()
    result = store.db.webhooks.delete_one({"id": webhook_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Webhook not found")
    return {"deleted": True}


# ─── Feature Flags ────────────────────────────────────────────────────────────

@app.get("/feature-flags", tags=["Feature Flags"])
async def list_feature_flags(user: dict = Depends(require_auth)):
    """List all feature flags."""
    store = get_state_store()
    flags = store.db.feature_flags.find({})
    return {"flags": [{**{k: v for k, v in f.items() if k != '_id'}} for f in flags]}


@app.post("/feature-flags", tags=["Feature Flags"])
async def create_feature_flag(
    key: str = Query(...),
    desc: str = Query(""),
    user: dict = Depends(require_auth),
):
    """Create a new feature flag."""
    store = get_state_store()
    existing = store.db.feature_flags.find_one({"key": key})
    if existing:
        raise HTTPException(409, f"Flag '{key}' already exists")
    doc = {
        "key": key,
        "desc": desc,
        "envs": {"dev": False, "staging": False, "prod": False},
        "updated_by": user.get("username", "unknown"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    store.db.feature_flags.insert_one(doc)
    doc.pop("_id", None)
    return {"flag": doc}


@app.patch("/feature-flags/{key}", tags=["Feature Flags"])
async def update_feature_flag(
    key: str,
    env: str = Query(...),
    enabled: bool = Query(...),
    user: dict = Depends(require_auth),
):
    """Toggle a feature flag for a specific environment."""
    store = get_state_store()
    result = store.db.feature_flags.update_one(
        {"key": key},
        {"$set": {f"envs.{env}": enabled, "updated_by": user.get("username", "unknown"), "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.modified_count == 0:
        raise HTTPException(404, "Flag not found")
    return {"updated": True}


@app.delete("/feature-flags/{key}", tags=["Feature Flags"])
async def delete_feature_flag(key: str, user: dict = Depends(require_auth)):
    """Delete a feature flag."""
    store = get_state_store()
    result = store.db.feature_flags.delete_one({"key": key})
    if result.deleted_count == 0:
        raise HTTPException(404, "Flag not found")
    return {"deleted": True}


# ─── System Config ────────────────────────────────────────────────────────────

@app.get("/system/config", tags=["System"])
async def get_system_config(user: dict = Depends(require_auth)):
    """Get system configuration (live values from backend)."""
    store = get_state_store()
    return {
        "api_endpoint": f"{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '8001')}",
        "api_online": True,
        "database": store.db_type,
        "database_name": getattr(store.db, 'name', 'plotcode_db'),
        "llm_provider": "OpenRouter",
        "llm_model": os.getenv("DEFAULT_LLM_MODEL", "openai/gpt-4o"),
        "chat_model": os.getenv("CHAT_LLM_MODEL", "openai/gpt-4o-mini"),
        "ci_platform": "GitHub Actions",
        "github_org": os.getenv("GITHUB_ORG", "—"),
        "github_configured": bool(os.getenv("GITHUB_CLIENT_ID")),
        "google_configured": bool(os.getenv("GOOGLE_CLIENT_ID")),
        "telegram_configured": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        "websocket_subscribers": get_event_bus().subscriber_count,
        "total_requests": store.db.requests.count_documents({}),
        "total_users": store.db.auth_users.count_documents({}),
        "total_services": store.db.services.count_documents({}),
        "version": "3.0.0",
    }


# ─── File Upload ──────────────────────────────────────────────────────────────

@app.post("/upload", tags=["Files"])
async def upload_file(
    file: UploadFile = File(...),
    user: dict = Depends(require_auth),
):
    """
    Upload a code file. Content stored in MongoDB (works on Vercel/serverless).
    Falls back to disk storage if UPLOAD_DIR is set (for VPS deployment).
    """
    import os, uuid as _uuid, base64

    # Read file content
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(413, "File too large. Maximum size is 10MB.")

    file_id = str(_uuid.uuid4())
    file_ext = os.path.splitext(file.filename or "")[1]

    store = get_state_store()

    # Try disk storage first (VPS), fall back to MongoDB (Vercel)
    upload_dir = os.getenv("UPLOAD_DIR")
    file_path = None
    if upload_dir:
        try:
            os.makedirs(upload_dir, exist_ok=True)
            saved_name = f"{file_id}{file_ext}"
            file_path = os.path.join(upload_dir, saved_name)
            with open(file_path, "wb") as f:
                f.write(content)
        except Exception:
            file_path = None  # Disk not available, use MongoDB

    # Store in MongoDB (always, as metadata + content if no disk)
    is_text = file.content_type and ("text" in file.content_type or "json" in file.content_type or "xml" in file.content_type)
    if not is_text and file_ext in ('.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.go', '.rs', '.c', '.cpp', '.h', '.html', '.css', '.yml', '.yaml', '.md', '.txt', '.sh', '.sql', '.json', '.xml', '.toml', '.ini', '.cfg', '.env'):
        is_text = True

    doc = {
        "id": file_id,
        "filename": file.filename,
        "size": len(content),
        "content_type": file.content_type or "application/octet-stream",
        "uploaded_by": user.get("username", "unknown"),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "path": file_path,
    }

    # If no disk path, store content in MongoDB
    if not file_path:
        if is_text:
            try:
                doc["content"] = content.decode("utf-8")
            except Exception:
                doc["content"] = base64.b64encode(content).decode("utf-8")
                doc["content_b64"] = True
        else:
            doc["content"] = base64.b64encode(content).decode("utf-8")
            doc["content_b64"] = True

    store.db.uploads.insert_one(doc)
    doc.pop("_id", None)

    return {"file": doc}


@app.get("/uploads", tags=["Files"])
async def list_uploads(user: dict = Depends(require_auth)):
    """List all uploaded files (metadata only, no content)."""
    store = get_state_store()
    files = store.db.uploads.find({}, {"content": 0})
    return {"files": [{**{k: v for k, v in f.items() if k != '_id'}} for f in files]}


@app.get("/uploads/{file_id}", tags=["Files"])
async def get_upload(file_id: str, user: dict = Depends(require_auth)):
    """Get uploaded file content (from disk or MongoDB)."""
    import os, base64
    store = get_state_store()
    doc = store.db.uploads.find_one({"id": file_id})
    if not doc:
        raise HTTPException(404, "File not found")
    doc.pop("_id", None)

    # Try disk first
    if doc.get("path") and os.path.exists(doc["path"]):
        try:
            with open(doc["path"], "r", encoding="utf-8") as f:
                doc["content"] = f.read()
        except Exception:
            try:
                with open(doc["path"], "rb") as f:
                    doc["content"] = base64.b64encode(f.read()).decode("utf-8")
                    doc["content_b64"] = True
            except Exception:
                doc["content"] = "(cannot read file)"
    elif "content" in doc:
        # Content stored in MongoDB — already there
        pass
    else:
        doc["content"] = "(content not available)"

    return {"file": doc}


@app.delete("/uploads/{file_id}", tags=["Files"])
async def delete_upload(file_id: str, user: dict = Depends(require_auth)):
    """Delete an uploaded file (from disk and/or MongoDB)."""
    import os
    store = get_state_store()
    doc = store.db.uploads.find_one({"id": file_id})
    if not doc:
        raise HTTPException(404, "File not found")

    # Delete from disk if exists
    if doc.get("path"):
        try:
            os.remove(doc["path"])
        except Exception:
            pass

    # Delete from MongoDB
    store.db.uploads.delete_one({"id": file_id})
    return {"deleted": True}


# ─── CI Webhook ───────────────────────────────────────────────────────────────

@app.post("/ci-webhook", tags=["CI/CD"])
async def ci_webhook(payload: CIWebhookPayload, background_tasks: BackgroundTasks):
    store = get_state_store()
    req = store.get_request_by_branch_and_status(
        payload.branch, ["ci_running", "ci_failed", "plan_approved"]
    )
    if not req:
        return {"status": "ignored", "reason": f"No active request for branch {payload.branch}"}

    request_id = req["request_id"]
    error_text = payload.error_summary or f"CI {payload.status} on branch {payload.branch}"
    background_tasks.add_task(_handle_ci_result_bg, request_id, payload.status, error_text)
    return {"status": "accepted", "request_id": request_id, "ci_status": payload.status}


def _handle_ci_result_bg(request_id: str, ci_status: str, logs: str):
    try:
        from telegram_bot import handle_ci_result
        handle_ci_result(request_id, ci_status, logs)
    except Exception as e:
        store = get_state_store()
        store.log_audit(request_id, "system", "ci_webhook", "handler_error", {"error": str(e)})


# ─── Agent Execution ──────────────────────────────────────────────────────────

def _run_agent_bg(agent_name: str, request_id: str, payload: Dict[str, Any]):
    try:
        result = _run_agent_sync(agent_name, request_id, payload)
        bus = get_event_bus()
        bus.publish_sync(f"agent.{agent_name}.completed", {
            "request_id": request_id,
            "result": str(result)[:500]
        })
    except Exception as e:
        store = get_state_store()
        store.log_audit(request_id, "system", "agent_api", "agent_error", {
            "agent": agent_name, "error": str(e)
        })
        bus = get_event_bus()
        bus.publish_sync(EventTypes.AGENT_ERROR, {
            "request_id": request_id,
            "agent": agent_name,
            "error": str(e),
        })


def _run_agent_sync(agent_name: str, request_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    agents = _get_agents()
    agent = agents[agent_name]
    if agent_name == "analysis":
        return agent.run(request_id)
    elif agent_name == "coding":
        return agent.run(request_id)
    elif agent_name == "validation":
        return agent.run(request_id, payload.get("ci_logs"))
    elif agent_name == "pr":
        return agent.run(request_id)
    elif agent_name == "deployment":
        env = payload.get("environment", "qa")
        if env == "production":
            return agent.deploy_production(request_id)
        return agent.deploy_qa(request_id)
    elif agent_name == "monitoring":
        return agent.run(request_id)
    else:
        raise ValueError(f"No handler for agent: {agent_name}")


# ─── Dashboard Static Files ───────────────────────────────────────────────────

DASHBOARD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dashboard"))
if os.path.exists(DASHBOARD_DIR):
    app.mount("/dashboard", StaticFiles(directory=DASHBOARD_DIR, html=True), name="dashboard")


@app.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/dashboard/index.html")


# ─── Startup / Shutdown ───────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Plotcode API v3 starting up...")
    try:
        store = get_state_store()
        logger.info(f"✅ MongoDB Atlas connected — DB: {store.db.name}")
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Plotcode API shutting down...")
    try:
        get_state_store().close()
    except Exception:
        pass


# ─── Entrypoint ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("AGENT_API_PORT", "8001"))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=True)
