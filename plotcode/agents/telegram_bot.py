"""
Plotcode Telegram Bot — The nerve center of the delivery automation system.

Handles all human-in-the-loop checkpoints:
  1. /request — Submit a new feature request (guided conversation)
  2. Inline buttons — Approve/Reject at each pipeline stage
  3. /status — Check request status
  4. /list — List open requests (admin/PM only)
  5. /rbac — View RBAC assignments
  6. /setrole — Change a user's role (admin only)

Run: python telegram_bot.py
"""

import asyncio
import json
import logging
import os
import sys
import threading
from datetime import datetime, timezone
from typing import Dict, Optional

from dotenv import load_dotenv
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Add parent dir so we can import agents
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from shared.state import get_state_store
from telegram_rbac import get_rbac
from intake_agent import IntakeAgent
from analysis_agent import AnalysisAgent
from coder_agent import CoderAgent
from pr_agent import PRAgent
from deployment_agent import DeploymentAgent
from monitoring_agent import MonitoringAgent
from shared.telegram_notifier import get_notifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("telegram_bot")

# Conversation states for /request command
(
    REQ_TITLE,
    REQ_BUSINESS_NEED,
    REQ_EXPECTED_BEHAVIOR,
    REQ_PRIORITY,
    REQ_SERVICE,
    REQ_CONFIRM,
) = range(6)

PRIORITY_EMOJI = {"P0": "🚨 P0 Critical", "P1": "🔴 P1 High", "P2": "🟡 P2 Medium", "P3": "🟢 P3 Low"}


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _get_user_info(update: Update) -> tuple[str, str, str]:
    """Extract telegram_id, name, username from update."""
    user = update.effective_user
    telegram_id = str(user.id)
    name = f"{user.first_name} {user.last_name or ''}".strip()
    username = user.username or telegram_id
    return telegram_id, name, username


def _ensure_user(update: Update) -> dict:
    """Ensure user is in DB and return their record."""
    tid, name, uname = _get_user_info(update)
    rbac = get_rbac()
    return rbac.ensure_user_exists(tid, name, uname)


async def _deny(update: Update, message: str) -> None:
    """Send an access denied message."""
    await update.effective_message.reply_text(f"🚫 {message}")


def _run_agent_background(coro_factory, request_id: str, agent_name: str):
    """Run an async agent in a background thread with a fresh event loop."""
    def target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(coro_factory())
        except Exception as e:
            notifier = get_notifier()
            notifier.notify_error(request_id, agent_name, str(e))
            logger.exception(f"Agent {agent_name} failed for {request_id}: {e}")
        finally:
            loop.close()
    t = threading.Thread(target=target, daemon=True)
    t.start()


# ─── /start ────────────────────────────────────────────────────────────────────


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _ensure_user(update)
    tid, name, _ = _get_user_info(update)
    rbac = get_rbac()
    role = rbac.get_user_role(tid)
    await update.message.reply_text(
        f"👋 Welcome to <b>Plotcode Delivery Bot</b>, {name}!\n\n"
        f"Your role: <b>{role}</b>\n\n"
        "Commands:\n"
        "  /request — Submit a feature request\n"
        "  /status &lt;REQ-ID&gt; — Check request status\n"
        "  /list — View open requests\n"
        "  /rbac — View user roles\n"
        "  /help — Show this message",
        parse_mode="HTML",
    )


# ─── /help ─────────────────────────────────────────────────────────────────────


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await cmd_start(update, context)


# ─── /request — ConversationHandler ───────────────────────────────────────────


async def req_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the feature request conversation."""
    user = _ensure_user(update)
    tid, _, _ = _get_user_info(update)
    rbac = get_rbac()

    if not rbac.can(tid, "submit_request"):
        await _deny(update, "You are not authorized to submit requests.")
        return ConversationHandler.END

    context.user_data.clear()
    await update.message.reply_text(
        "📋 <b>New Feature Request</b>\n\n"
        "Step 1/5: What is the <b>title</b> of your request?\n"
        "<i>(e.g. 'Add /version endpoint to user-api')</i>\n\n"
        "Type /cancel to abort.",
        parse_mode="HTML",
    )
    return REQ_TITLE


async def req_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["title"] = update.message.text.strip()
    await update.message.reply_text(
        "Step 2/5: What is the <b>business need</b>?\n"
        "<i>(Why is this needed? What problem does it solve?)</i>",
        parse_mode="HTML",
    )
    return REQ_BUSINESS_NEED


async def req_business_need(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["business_need"] = update.message.text.strip()
    await update.message.reply_text(
        "Step 3/5: What is the <b>expected behavior</b>?\n"
        "<i>(What should the system do after this change?)</i>",
        parse_mode="HTML",
    )
    return REQ_EXPECTED_BEHAVIOR


async def req_expected_behavior(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["expected_behavior"] = update.message.text.strip()
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚨 P0 Critical", callback_data="priority:P0"),
            InlineKeyboardButton("🔴 P1 High", callback_data="priority:P1"),
        ],
        [
            InlineKeyboardButton("🟡 P2 Medium", callback_data="priority:P2"),
            InlineKeyboardButton("🟢 P3 Low", callback_data="priority:P3"),
        ],
    ])
    await update.message.reply_text(
        "Step 4/5: Select <b>priority</b>:",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    return REQ_PRIORITY


async def req_priority_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    priority = query.data.split(":")[1]
    context.user_data["priority"] = priority

    # Fetch available services
    store = get_state_store()
    services_list = store.list_services()
    services = [row["name"] for row in services_list]

    if not services:
        services = ["demo-api"]

    buttons = [[InlineKeyboardButton(s, callback_data=f"service:{s}")] for s in services]
    keyboard = InlineKeyboardMarkup(buttons)

    await query.edit_message_text(
        f"Priority set: <b>{priority}</b>\n\n"
        "Step 5/5: Select the <b>affected service</b>:",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    return REQ_SERVICE


async def req_service_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    service = query.data.split(":")[1]
    context.user_data["affected_service"] = service

    data = context.user_data
    summary = (
        f"📋 <b>Request Summary</b>\n\n"
        f"<b>Title:</b> {data.get('title')}\n"
        f"<b>Business Need:</b> {data.get('business_need')}\n"
        f"<b>Expected Behavior:</b> {data.get('expected_behavior')}\n"
        f"<b>Priority:</b> {data.get('priority')}\n"
        f"<b>Service:</b> {data.get('affected_service')}\n\n"
        f"Submit this request?"
    )
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Submit", callback_data="req_submit:yes"),
            InlineKeyboardButton("❌ Cancel", callback_data="req_submit:no"),
        ]
    ])
    await query.edit_message_text(summary, parse_mode="HTML", reply_markup=keyboard)
    return REQ_CONFIRM


async def req_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "req_submit:no":
        await query.edit_message_text("❌ Request cancelled.")
        return ConversationHandler.END

    tid, name, username = _get_user_info(update)
    data = context.user_data
    store = get_state_store()

    req_data = {
        "title": data["title"],
        "business_need": data["business_need"],
        "expected_behavior": data["expected_behavior"],
        "priority": data.get("priority", "P2"),
        "affected_service": data.get("affected_service", "demo-api"),
        "requester_name": name,
        "requester_slack_id": tid,  # using slack_id column for telegram ID
        "source": "telegram",
        "status": "submitted",
    }

    req = store.create_request(req_data)
    rid = req["request_id"]
    store.log_audit(rid, "human", tid, "request_submitted", {"source": "telegram"})

    await query.edit_message_text(
        f"✅ <b>Request submitted: {rid}</b>\n\n"
        f"An admin will review your request shortly.\n"
        f"Track with: /status {rid}",
        parse_mode="HTML",
    )

    # Notify all admins
    notifier = get_notifier()
    notifier.notify_new_request(req)

    return ConversationHandler.END


async def req_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Request cancelled.")
    context.user_data.clear()
    return ConversationHandler.END


# ─── /status ───────────────────────────────────────────────────────────────────


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _ensure_user(update)
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /status REQ-2025-0001")
        return

    rid = args[0].upper()
    store = get_state_store()
    req = store.get_request(rid)

    if not req:
        await update.message.reply_text(f"❌ Request {rid} not found.")
        return

    status = req.get("status", "unknown")
    audit = store.get_audit_log(rid)
    last_action = audit[-1] if audit else {}

    text = (
        f"📊 <b>Status: {rid}</b>\n\n"
        f"<b>Title:</b> {req.get('title')}\n"
        f"<b>Status:</b> <code>{status}</code>\n"
        f"<b>Priority:</b> {req.get('priority')}\n"
        f"<b>Service:</b> {req.get('affected_service')}\n"
        f"<b>Branch:</b> <code>{req.get('feature_branch') or 'not yet created'}</code>\n"
        f"<b>PR:</b> {req.get('pr_url') or 'not yet created'}\n"
        f"<b>Staging:</b> {req.get('staging_url') or 'N/A'}\n"
        f"<b>Production:</b> {req.get('production_url') or 'N/A'}\n"
    )
    if last_action:
        text += f"\n<b>Last Action:</b> {last_action.get('action')} by {last_action.get('actor_id')}"

    await update.message.reply_text(text, parse_mode="HTML")


# ─── /list ─────────────────────────────────────────────────────────────────────


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _ensure_user(update)
    tid, _, _ = _get_user_info(update)
    rbac = get_rbac()

    if not rbac.can(tid, "list_requests"):
        await _deny(update, "You need developer role or above to list requests.")
        return

    store = get_state_store()
    open_statuses = [
        "submitted", "approved", "plan_pending_approval", "plan_approved",
        "ci_running", "ci_passed", "ci_failed", "pr_open", "pr_merged",
        "qa_deployed", "qa_passed",
    ]

    lines = []
    for s in open_statuses:
        reqs = store.list_requests(status=s)
        for r in reqs:
            lines.append(f"• <code>{r['request_id']}</code> [{r['status']}] {r['title'][:40]}")

    if not lines:
        await update.message.reply_text("✅ No open requests.")
        return

    text = "<b>Open Requests</b>\n\n" + "\n".join(lines[:20])
    await update.message.reply_text(text, parse_mode="HTML")


# ─── /rbac ─────────────────────────────────────────────────────────────────────


async def cmd_rbac(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _ensure_user(update)
    tid, _, _ = _get_user_info(update)
    rbac = get_rbac()

    if not rbac.can(tid, "list_requests"):
        await _deny(update, "Insufficient permissions.")
        return

    users = rbac.list_users()
    if not users:
        await update.message.reply_text("No users registered yet.")
        return

    lines = [f"👤 <b>{u['name']}</b> [{u['role']}] — TG: <code>{u['telegram_id']}</code>" for u in users]
    text = "<b>RBAC — All Users</b>\n\n" + "\n".join(lines[:30])
    await update.message.reply_text(text, parse_mode="HTML")


# ─── /setrole ──────────────────────────────────────────────────────────────────


async def cmd_setrole(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _ensure_user(update)
    tid, _, _ = _get_user_info(update)
    rbac = get_rbac()

    if not rbac.can(tid, "manage_users"):
        await _deny(update, "Only admins can change roles.")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Usage: /setrole &lt;telegram_id&gt; &lt;role&gt;\n"
            "Roles: admin, product_owner, developer, qa_engineer, requester",
            parse_mode="HTML",
        )
        return

    target_id, new_role = args[0], args[1]
    if rbac.set_role(target_id, new_role):
        await update.message.reply_text(f"✅ User {target_id} role set to <b>{new_role}</b>.", parse_mode="HTML")
    else:
        await update.message.reply_text(f"❌ Invalid role: {new_role}")


# ─── Inline Callback Dispatcher ────────────────────────────────────────────────


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route all inline keyboard button presses."""
    query = update.callback_query
    await query.answer()

    tid, name, _ = _get_user_info(update)
    _ensure_user(update)
    rbac = get_rbac()
    data = query.data

    # Priority / service selection for /request flow — handled by ConversationHandler
    if data.startswith("priority:") or data.startswith("service:") or data.startswith("req_submit:"):
        return  # ConversationHandler handles these

    action, _, rid = data.partition(":")
    if not rid:
        return

    store = get_state_store()
    req = store.get_request(rid)
    if not req:
        await query.edit_message_text(f"❌ Request {rid} not found.")
        return

    notifier = get_notifier()
    now = datetime.now(timezone.utc).isoformat()

    # ── Approve initial request ──
    if action == "approve_req":
        if not rbac.can(tid, "approve_request"):
            await query.answer("🚫 You don't have permission to approve requests.", show_alert=True)
            return
        store.update_request(rid, {
            "status": "approved",
            "initial_approver_slack_id": tid,
            "initial_approved_at": now,
        })
        store.log_audit(rid, "human", tid, "request_approved", {"approver": name})
        await query.edit_message_text(
            f"✅ <b>{rid} APPROVED</b> by {name}\n\nStarting AI analysis...",
            parse_mode="HTML",
        )
        # Trigger analysis in background
        def run_analysis():
            agent = AnalysisAgent()
            result = agent.run(rid)
            updated = store.get_request(rid)
            notifier.notify_plan_ready(updated)
        _run_agent_background(asyncio.coroutine(lambda: None), rid, "analysis_agent")
        threading.Thread(target=run_analysis, daemon=True).start()

    # ── Reject initial request ──
    elif action == "reject_req":
        if not rbac.can(tid, "reject_request"):
            await query.answer("🚫 Insufficient permissions.", show_alert=True)
            return
        store.update_request(rid, {
            "status": "rejected",
            "initial_rejection_reason": f"Rejected by {name}",
        })
        store.log_audit(rid, "human", tid, "request_rejected", {"by": name})
        await query.edit_message_text(
            f"❌ <b>{rid} REJECTED</b> by {name}",
            parse_mode="HTML",
        )

    # ── Approve implementation plan ──
    elif action == "approve_plan":
        if not rbac.can(tid, "approve_plan"):
            await query.answer("🚫 Insufficient permissions.", show_alert=True)
            return
        store.update_request(rid, {
            "status": "plan_approved",
            "plan_approver_slack_id": tid,
            "plan_approved_at": now,
        })
        store.log_audit(rid, "human", tid, "plan_approved", {"by": name})
        await query.edit_message_text(
            f"✅ <b>Plan APPROVED: {rid}</b> by {name}\n\nAI is writing code now...",
            parse_mode="HTML",
        )
        def run_coding():
            try:
                coder = CoderAgent()
                result = coder.run(rid)
                updated = store.get_request(rid)
                notifier.notify_code_applied(updated, result.get("branch", ""), result.get("files", []))
                notifier.notify_ci_running(updated, attempt=1)
            except Exception as e:
                notifier.notify_error(rid, "coder_agent", str(e))
        threading.Thread(target=run_coding, daemon=True).start()

    # ── Reject implementation plan ──
    elif action == "reject_plan":
        if not rbac.can(tid, "reject_plan"):
            await query.answer("🚫 Insufficient permissions.", show_alert=True)
            return
        store.update_request(rid, {
            "status": "plan_rejected",
            "plan_rejection_reason": f"Rejected by {name}",
        })
        store.log_audit(rid, "human", tid, "plan_rejected", {"by": name})
        await query.edit_message_text(
            f"❌ <b>Plan REJECTED: {rid}</b> by {name}\n\n"
            "Send revised requirements and re-submit.",
            parse_mode="HTML",
        )

    # ── Approve PR merge ──
    elif action == "merge_pr":
        if not rbac.can(tid, "merge_pr"):
            await query.answer("🚫 Insufficient permissions.", show_alert=True)
            return
        pr_url = req.get("pr_url", "")
        pr_number = req.get("pr_number")
        store.update_request(rid, {
            "status": "pr_approved",
            "pr_merger_slack_id": tid,
            "pr_merged_at": now,
        })
        store.log_audit(rid, "human", tid, "pr_merge_approved", {"by": name, "pr": pr_number})
        await query.edit_message_text(
            f"✅ <b>PR Merge APPROVED: {rid}</b> by {name}\n\nMerging PR #{pr_number}...",
            parse_mode="HTML",
        )
        def run_merge_and_deploy():
            try:
                from shared.git_client import get_git_client
                git = get_git_client()
                service_name = req.get("affected_service", "demo-api")
                service = store.get_service(service_name)
                repo_name = service["name"] if service else service_name
                branch = req.get("feature_branch", "")
                base = req.get("base_branch", "main")
                pr_num = req.get("pr_number")
                if pr_num:
                    merge_result = git.merge_pr(repo_name, pr_num)
                    sha = merge_result.get("sha", "")
                    store.update_request(rid, {
                        "status": "pr_merged",
                        "merged_sha": sha,
                    })
                    store.log_audit(rid, "ai", "git_client", "pr_merged", {"sha": sha})
                deploy_agent = DeploymentAgent()
                result = deploy_agent.deploy_qa(rid)
                staging_url = result.get("url", os.getenv("STAGING_ENV_URL", "https://staging.example.com"))
                notifier.notify_qa_deployed(store.get_request(rid), staging_url)
            except Exception as e:
                notifier.notify_error(rid, "merge+deploy", str(e))
        threading.Thread(target=run_merge_and_deploy, daemon=True).start()

    # ── QA Passed ──
    elif action == "qa_pass":
        if not rbac.can(tid, "approve_qa"):
            await query.answer("🚫 Insufficient permissions.", show_alert=True)
            return
        store.update_request(rid, {
            "status": "qa_passed",
            "qa_validator_slack_id": tid,
            "qa_validated_at": now,
        })
        store.log_audit(rid, "human", tid, "qa_passed", {"by": name})
        await query.edit_message_text(
            f"✅ <b>QA PASSED: {rid}</b> by {name}\n\nRequesting production approval...",
            parse_mode="HTML",
        )
        notifier.notify_prod_approval_needed(store.get_request(rid))

    # ── QA Failed ──
    elif action == "qa_fail":
        if not rbac.can(tid, "fail_qa"):
            await query.answer("🚫 Insufficient permissions.", show_alert=True)
            return
        store.update_request(rid, {"status": "qa_failed"})
        store.log_audit(rid, "human", tid, "qa_failed", {"by": name})
        await query.edit_message_text(
            f"❌ <b>QA FAILED: {rid}</b> by {name}\n\nSending back for fixes.",
            parse_mode="HTML",
        )

    # ── Approve Production ──
    elif action == "approve_prod":
        if not rbac.can(tid, "approve_prod"):
            await query.answer("🚫 Only admins can approve production deployments.", show_alert=True)
            return
        store.update_request(rid, {
            "status": "prod_approved",
            "prod_approver_slack_id": tid,
            "prod_approved_at": now,
        })
        store.log_audit(rid, "human", tid, "prod_approved", {"by": name})
        await query.edit_message_text(
            f"✅ <b>PRODUCTION APPROVED: {rid}</b> by {name}\n\nDeploying to production...",
            parse_mode="HTML",
        )
        def run_prod_deploy():
            try:
                deploy_agent = DeploymentAgent()
                result = deploy_agent.deploy_production(rid)
                prod_url = result.get("url", os.getenv("PRODUCTION_ENV_URL", "https://app.example.com"))
                notifier.notify_deployed_production(store.get_request(rid), prod_url)
                # Run monitoring/closure
                mon = MonitoringAgent()
                mon.run(rid)
                notifier.notify_closed(store.get_request(rid))
            except Exception as e:
                notifier.notify_error(rid, "deployment+monitoring", str(e))
        threading.Thread(target=run_prod_deploy, daemon=True).start()

    # ── Hold Production ──
    elif action == "hold_prod":
        store.log_audit(rid, "human", tid, "prod_held", {"by": name})
        await query.edit_message_text(
            f"⏸️ <b>Production HELD: {rid}</b> by {name}\n\nUse /status {rid} to re-trigger.",
            parse_mode="HTML",
        )

    else:
        await query.edit_message_text(f"Unknown action: {action}")


# ─── /approve (emergency text command) ────────────────────────────────────────


async def cmd_approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Emergency approve for a request (for terminal admins)."""
    _ensure_user(update)
    tid, name, _ = _get_user_info(update)
    rbac = get_rbac()
    args = context.args

    if not args:
        await update.message.reply_text("Usage: /approve REQ-2025-0001")
        return

    rid = args[0].upper()
    store = get_state_store()
    req = store.get_request(rid)
    if not req:
        await update.message.reply_text(f"❌ Request {rid} not found.")
        return

    status = req.get("status")
    now = datetime.now(timezone.utc).isoformat()

    if status == "submitted":
        if not rbac.can(tid, "approve_request"):
            await _deny(update, "Insufficient permissions.")
            return
        store.update_request(rid, {
            "status": "approved",
            "initial_approver_slack_id": tid,
            "initial_approved_at": now,
        })
        await update.message.reply_text(f"✅ {rid} approved. Starting analysis...")
        notifier = get_notifier()
        def run_analysis():
            agent = AnalysisAgent()
            result = agent.run(rid)
            updated = store.get_request(rid)
            notifier.notify_plan_ready(updated)
        threading.Thread(target=run_analysis, daemon=True).start()
    elif status == "plan_pending_approval":
        if not rbac.can(tid, "approve_plan"):
            await _deny(update, "Insufficient permissions.")
            return
        store.update_request(rid, {
            "status": "plan_approved",
            "plan_approver_slack_id": tid,
            "plan_approved_at": now,
        })
        await update.message.reply_text(f"✅ Plan approved for {rid}. Starting coding...")
        def run_coding():
            coder = CoderAgent()
            result = coder.run(rid)
            notifier = get_notifier()
            updated = store.get_request(rid)
            notifier.notify_code_applied(updated, result.get("branch", ""), result.get("files", []))
        threading.Thread(target=run_coding, daemon=True).start()
    else:
        await update.message.reply_text(
            f"Request {rid} is in status '{status}'. Nothing to approve at this stage."
        )


# ─── CI Webhook (called by api.py, not Telegram) ──────────────────────────────


def handle_ci_result(request_id: str, status: str, logs: str = "") -> None:
    """Called from api.py when GitHub Actions posts CI results."""
    store = get_state_store()
    req = store.get_request(request_id)
    if not req:
        logger.error(f"CI webhook: request {request_id} not found")
        return

    notifier = get_notifier()

    if status == "success":
        store.update_request(request_id, {"status": "ci_passed"})
        store.log_audit(request_id, "system", "ci", "ci_passed", {})
        notifier.notify_ci_passed(req)
        # Trigger PR creation
        def run_pr():
            pr_agent = PRAgent()
            result = pr_agent.run(request_id)
            updated = store.get_request(request_id)
            notifier.notify_pr_created(updated, result.get("pr_url", ""), result.get("pr_number", 0))
        threading.Thread(target=run_pr, daemon=True).start()

    elif status in ("failure", "cancelled"):
        from validation_agent import ValidationAgent
        current_req = store.get_request(request_id)
        attempt = current_req.get("ci_attempt", 0) + 1
        store.update_request(request_id, {
            "status": "ci_failed",
            "ci_attempt": attempt,
        })

        if attempt >= 3:
            notifier.notify_ci_exhausted(req, logs)
            store.update_request(request_id, {"status": "ci_exhausted"})
        else:
            notifier.notify_ci_failed_healing(req, attempt, logs)
            def run_healing():
                v_agent = ValidationAgent()
                v_agent.run(request_id, logs)
            threading.Thread(target=run_healing, daemon=True).start()


# ─── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set in .env")
        sys.exit(1)

    app = Application.builder().token(token).build()

    # /request ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("request", req_start)],
        states={
            REQ_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, req_title)],
            REQ_BUSINESS_NEED: [MessageHandler(filters.TEXT & ~filters.COMMAND, req_business_need)],
            REQ_EXPECTED_BEHAVIOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, req_expected_behavior)],
            REQ_PRIORITY: [CallbackQueryHandler(req_priority_callback, pattern=r"^priority:")],
            REQ_SERVICE: [CallbackQueryHandler(req_service_callback, pattern=r"^service:")],
            REQ_CONFIRM: [CallbackQueryHandler(req_confirm_callback, pattern=r"^req_submit:")],
        },
        fallbacks=[CommandHandler("cancel", req_cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("rbac", cmd_rbac))
    app.add_handler(CommandHandler("setrole", cmd_setrole))
    app.add_handler(CommandHandler("approve", cmd_approve))
    app.add_handler(CallbackQueryHandler(handle_callback))

    logger.info("Plotcode Telegram Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
