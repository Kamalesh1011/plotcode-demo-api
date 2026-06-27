"""
Telegram Notifier — shared utility for sending messages from agents.
All agents call this to push notifications with inline approval buttons.
"""

import os
import json
import logging
import requests
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

PRIORITY_EMOJI = {"P0": "🚨", "P1": "🔴", "P2": "🟡", "P3": "🟢"}
STATUS_EMOJI = {
    "submitted": "📋",
    "approved": "✅",
    "rejected": "❌",
    "plan_pending_approval": "🧠",
    "plan_approved": "✅",
    "ci_running": "⚙️",
    "ci_passed": "✅",
    "ci_failed": "❌",
    "pr_open": "🔀",
    "pr_merged": "✅",
    "qa_deployed": "🚀",
    "qa_passed": "✅",
    "qa_failed": "❌",
    "deployed": "🎉",
    "closed": "🏁",
}


class TelegramNotifier:
    """Sends Telegram messages with optional inline keyboards from any agent."""

    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.admin_chat_id = TELEGRAM_ADMIN_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        if not self.token:
            logger.warning("TELEGRAM_BOT_TOKEN not set — notifications disabled")

    def _post(self, method: str, payload: Dict[str, Any]) -> Optional[Dict]:
        """Make a Telegram Bot API call."""
        if not self.token:
            logger.info(f"[TELEGRAM DISABLED] Would call {method}: {payload.get('text', '')[:100]}")
            return None
        try:
            resp = requests.post(
                f"{self.base_url}/{method}",
                json=payload,
                timeout=10
            )
            data = resp.json()
            if not data.get("ok"):
                logger.error(f"Telegram API error: {data}")
            return data
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return None

    def send_message(
        self,
        text: str,
        chat_id: Optional[str] = None,
        parse_mode: str = "HTML",
        reply_markup: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Send a plain or inline-keyboard message."""
        payload = {
            "chat_id": chat_id or self.admin_chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return self._post("sendMessage", payload)

    def build_inline_keyboard(self, buttons: List[List[Dict]]) -> Dict:
        """Build an inline keyboard markup."""
        return {"inline_keyboard": buttons}

    # ─── Request Intake ──────────────────────────────────────────────────────

    def notify_new_request(self, req: Dict[str, Any]) -> None:
        """Notify admins of a new feature request awaiting approval."""
        rid = req["request_id"]
        priority = req.get("priority", "P2")
        emoji = PRIORITY_EMOJI.get(priority, "🟡")
        text = (
            f"📋 <b>NEW REQUEST: {rid}</b>\n\n"
            f"<b>Title:</b> {req.get('title', 'N/A')}\n"
            f"<b>By:</b> {req.get('requester_name', 'Unknown')}\n"
            f"<b>Priority:</b> {emoji} {priority}\n"
            f"<b>Service:</b> {req.get('affected_service', 'N/A')}\n\n"
            f"<b>Business Need:</b>\n{req.get('business_need', 'N/A')}\n\n"
            f"<b>Expected Behavior:</b>\n{req.get('expected_behavior', 'N/A')}"
        )
        keyboard = self.build_inline_keyboard([
            [
                {"text": "✅ Approve", "callback_data": f"approve_req:{rid}"},
                {"text": "❌ Reject", "callback_data": f"reject_req:{rid}"},
            ]
        ])
        self.send_message(text, reply_markup=keyboard)

    # ─── Analysis / Plan ─────────────────────────────────────────────────────

    def notify_plan_ready(self, req: Dict[str, Any]) -> None:
        """Notify admins that an implementation plan is ready for approval."""
        rid = req["request_id"]
        plan = req.get("implementation_plan", "No plan generated")
        # Truncate plan for Telegram (4096 char limit)
        plan_preview = plan[:1500] + ("\n\n...[truncated]" if len(plan) > 1500 else "")
        text = (
            f"🧠 <b>IMPLEMENTATION PLAN READY: {rid}</b>\n\n"
            f"<b>Title:</b> {req.get('title', 'N/A')}\n"
            f"<b>Service:</b> {req.get('affected_service', 'N/A')}\n\n"
            f"<b>Plan Preview:</b>\n<pre>{plan_preview}</pre>"
        )
        keyboard = self.build_inline_keyboard([
            [
                {"text": "✅ Approve Plan", "callback_data": f"approve_plan:{rid}"},
                {"text": "❌ Reject Plan", "callback_data": f"reject_plan:{rid}"},
            ]
        ])
        self.send_message(text, reply_markup=keyboard)

    # ─── Code / Branch ───────────────────────────────────────────────────────

    def notify_code_applied(self, req: Dict[str, Any], branch: str, files: List[str]) -> None:
        """Notify that code changes have been committed to a branch."""
        rid = req["request_id"]
        service = req.get("affected_service", "N/A")
        files_str = "\n".join(f"  • {f}" for f in files[:10]) or "  (no files)"
        text = (
            f"💻 <b>CODE COMMITTED: {rid}</b>\n\n"
            f"<b>Branch:</b> <code>{branch}</code>\n"
            f"<b>Service:</b> {service}\n\n"
            f"<b>Files Changed:</b>\n{files_str}\n\n"
            f"⚙️ <i>CI pipeline is now running...</i>"
        )
        self.send_message(text)

    # ─── CI / Validation ─────────────────────────────────────────────────────

    def notify_ci_running(self, req: Dict[str, Any], attempt: int = 1) -> None:
        rid = req["request_id"]
        text = (
            f"⚙️ <b>CI RUNNING: {rid}</b>\n"
            f"Attempt {attempt} of 3\n"
            f"Branch: <code>{req.get('feature_branch', 'N/A')}</code>"
        )
        self.send_message(text)

    def notify_ci_failed_healing(self, req: Dict[str, Any], attempt: int, error: str) -> None:
        rid = req["request_id"]
        text = (
            f"🔄 <b>CI FAILED (attempt {attempt}/3): {rid}</b>\n\n"
            f"AI is self-healing the errors...\n\n"
            f"<b>Error:</b>\n<pre>{error[:500]}</pre>"
        )
        self.send_message(text)

    def notify_ci_passed(self, req: Dict[str, Any]) -> None:
        rid = req["request_id"]
        text = (
            f"✅ <b>CI PASSED: {rid}</b>\n"
            f"All checks passed. Creating PR now..."
        )
        self.send_message(text)

    def notify_ci_exhausted(self, req: Dict[str, Any], last_error: str) -> None:
        rid = req["request_id"]
        text = (
            f"🚨 <b>CI FAILED (all 3 attempts): {rid}</b>\n\n"
            f"AI could not auto-fix. Manual intervention required.\n\n"
            f"<b>Last error:</b>\n<pre>{last_error[:800]}</pre>"
        )
        self.send_message(text)

    # ─── PR ──────────────────────────────────────────────────────────────────

    def notify_pr_created(self, req: Dict[str, Any], pr_url: str, pr_number: int) -> None:
        rid = req["request_id"]
        text = (
            f"🔀 <b>PR CREATED: {rid}</b>\n\n"
            f"<b>PR #{pr_number}</b>\n"
            f"<a href='{pr_url}'>View Pull Request</a>\n\n"
            f"Review the PR and approve merge when ready."
        )
        keyboard = self.build_inline_keyboard([
            [
                {"text": "✅ Approve Merge", "callback_data": f"merge_pr:{rid}"},
                {"text": "🔗 View PR", "url": pr_url},
            ]
        ])
        self.send_message(text, reply_markup=keyboard)

    # ─── QA / Deployment ─────────────────────────────────────────────────────

    def notify_qa_deployed(self, req: Dict[str, Any], staging_url: str) -> None:
        rid = req["request_id"]
        text = (
            f"🚀 <b>DEPLOYED TO QA: {rid}</b>\n\n"
            f"<b>Staging URL:</b> {staging_url}\n\n"
            f"Please validate the feature and report back."
        )
        keyboard = self.build_inline_keyboard([
            [
                {"text": "✅ QA Passed", "callback_data": f"qa_pass:{rid}"},
                {"text": "❌ QA Failed", "callback_data": f"qa_fail:{rid}"},
            ]
        ])
        self.send_message(text, reply_markup=keyboard)

    def notify_prod_approval_needed(self, req: Dict[str, Any]) -> None:
        rid = req["request_id"]
        text = (
            f"🔐 <b>PRODUCTION APPROVAL REQUIRED: {rid}</b>\n\n"
            f"QA has been validated. Approve production deployment?\n\n"
            f"<b>⚠️ This will deploy to PRODUCTION.</b>"
        )
        keyboard = self.build_inline_keyboard([
            [
                {"text": "✅ Approve Production", "callback_data": f"approve_prod:{rid}"},
                {"text": "❌ Hold", "callback_data": f"hold_prod:{rid}"},
            ]
        ])
        self.send_message(text, reply_markup=keyboard)

    def notify_deployed_production(self, req: Dict[str, Any], prod_url: str) -> None:
        rid = req["request_id"]
        text = (
            f"🎉 <b>DEPLOYED TO PRODUCTION: {rid}</b>\n\n"
            f"<b>Production URL:</b> {prod_url}\n"
            f"<b>Title:</b> {req.get('title', 'N/A')}\n\n"
            f"Monitoring post-deploy metrics..."
        )
        self.send_message(text)

    # ─── Closure ─────────────────────────────────────────────────────────────

    def notify_closed(self, req: Dict[str, Any]) -> None:
        rid = req["request_id"]
        pr_url = req.get("pr_url", "N/A")
        prod_url = req.get("production_url", "N/A")
        deploy_ts = req.get("deploy_timestamp", "N/A")
        text = (
            f"🏁 <b>REQUEST COMPLETED: {rid}</b>\n\n"
            f"<b>Title:</b> {req.get('title', 'N/A')}\n"
            f"<b>PR:</b> <a href='{pr_url}'>View PR</a>\n"
            f"<b>Production:</b> {prod_url}\n"
            f"<b>Deployed:</b> {deploy_ts}\n\n"
            f"✅ Full delivery cycle complete."
        )
        self.send_message(text)

    # ─── Generic Status ───────────────────────────────────────────────────────

    def notify_status(self, request_id: str, message: str) -> None:
        text = f"ℹ️ <b>{request_id}</b>\n{message}"
        self.send_message(text)

    def notify_error(self, request_id: str, agent: str, error: str) -> None:
        text = (
            f"🚨 <b>AGENT ERROR: {request_id}</b>\n"
            f"<b>Agent:</b> {agent}\n"
            f"<b>Error:</b> <pre>{error[:1000]}</pre>"
        )
        self.send_message(text)


_notifier: Optional[TelegramNotifier] = None


def get_notifier() -> TelegramNotifier:
    global _notifier
    if _notifier is None:
        _notifier = TelegramNotifier()
    return _notifier
