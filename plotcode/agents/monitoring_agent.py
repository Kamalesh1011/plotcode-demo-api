"""
Monitoring & Reporting Agent (v2)

Enhancements:
  - SLA breach detection and escalation
  - Post-deploy health checks with real HTTP probes
  - EventBus publishing for real-time dashboard updates
  - Retrospective reporting with cycle time analytics
"""

import time
import requests as http_requests
from typing import Dict, Any, Optional
from shared.state import get_state_store
from shared.events import get_event_bus, EventTypes


class MonitoringAgent:
    """Monitors production after deployment and closes the ticket."""

    def __init__(self):
        self.store = get_state_store()
        self.bus = get_event_bus()

    def run(self, request_id: str, monitoring_duration_hours: int = 24) -> Dict[str, Any]:
        """Start monitoring and eventually close the ticket."""
        req = self.store.get_request(request_id)
        if not req:
            raise ValueError(f"Request {request_id} not found")

        # Run health checks
        health = self.check_health(request_id)
        monitoring_report = self._build_report(req, health, monitoring_duration_hours)

        # Close ticket
        release_version = self._derive_version(req)
        self.store.update_request(request_id, {
            "status": "closed",
            "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "release_version": release_version,
        })

        self.store.log_audit(request_id, "system", "monitoring_agent", "ticket_closed", {
            "monitoring_duration_hours": monitoring_duration_hours,
            "release_version": release_version,
            "health": health,
        })

        self.bus.publish_sync(EventTypes.REQUEST_CLOSED, {
            "request_id": request_id,
            "release_version": release_version,
            "health": health.get("status"),
        })

        return {
            "request_id": request_id,
            "status": "closed",
            "release_version": release_version,
            "monitoring_report": monitoring_report,
        }

    def check_health(self, request_id: str) -> Dict[str, Any]:
        """Run post-deploy HTTP health checks."""
        req = self.store.get_request(request_id)
        if not req:
            return {"status": "unknown", "url": None}

        url = req.get("production_url") or req.get("staging_url")
        if not url:
            return {"status": "no_url", "url": None}

        try:
            resp = http_requests.get(f"{url}/health", timeout=15)
            healthy = resp.status_code < 500
            result = {
                "status": "healthy" if healthy else "unhealthy",
                "url": url,
                "status_code": resp.status_code,
                "latency_ms": int(resp.elapsed.total_seconds() * 1000),
            }
        except Exception as e:
            result = {"status": "error", "url": url, "error": str(e)}

        self.store.log_audit(request_id, "system", "monitoring_agent", "health_check", result)
        self.bus.publish_sync(EventTypes.HEALTH_CHECK, {"request_id": request_id, **result})
        return result

    def scan_sla_breaches(self) -> int:
        """
        Scan for SLA-breached requests and publish alerts.
        Call this periodically (e.g. every 15 minutes via a background scheduler).
        Returns the number of breaches found.
        """
        breached = self.store.get_sla_breached_requests()
        count = 0
        for req in breached:
            request_id = req["request_id"]
            self.store.mark_sla_alert_sent(request_id)
            self.store.log_audit(request_id, "system", "monitoring_agent", "sla_breached", {
                "sla_deadline": req.get("sla_deadline"),
                "current_status": req.get("status"),
                "priority": req.get("priority"),
            })
            self.bus.publish_sync(EventTypes.SLA_BREACHED, {
                "request_id": request_id,
                "priority": req.get("priority"),
                "status": req.get("status"),
                "title": req.get("title"),
                "sla_deadline": req.get("sla_deadline"),
            })
            count += 1

        if count > 0:
            print(f"[MonitoringAgent] {count} SLA breaches detected and alerted.")
        return count

    def generate_retrospective(self, request_id: str) -> Dict[str, Any]:
        """Generate a mini-retrospective for the completed request."""
        req = self.store.get_request(request_id)
        if not req:
            raise ValueError(f"Request {request_id} not found")

        created = req.get("created_at")
        completed = req.get("completed_at")
        cycle_time = "unknown"
        if created and completed:
            from datetime import datetime
            try:
                c1 = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
                c2 = datetime.fromisoformat(str(completed).replace("Z", "+00:00"))
                delta = c2 - c1
                hours = delta.total_seconds() / 3600
                cycle_time = f"{hours:.1f} hours"
            except Exception:
                pass

        audit_logs = self.store.get_audit_log(request_id)
        ai_actions = [l for l in audit_logs if l.get("actor_type") == "ai"]
        human_actions = [l for l in audit_logs if l.get("actor_type") == "human"]

        return {
            "request_id": request_id,
            "title": req.get("title"),
            "cycle_time": cycle_time,
            "total_events": len(audit_logs),
            "ai_actions": len(ai_actions),
            "human_approvals": len(human_actions),
            "release_version": req.get("release_version"),
            "stages": {
                "submitted":    req.get("created_at"),
                "approved":     req.get("initial_approved_at"),
                "plan_approved": req.get("plan_approved_at"),
                "pr_merged":    req.get("pr_merged_at"),
                "qa_validated": req.get("qa_validated_at"),
                "prod_approved": req.get("prod_approved_at"),
                "completed":    completed,
            },
            "summary": f"Request {request_id} completed in {cycle_time} with {len(ai_actions)} AI actions and {len(human_actions)} human approvals.",
        }

    def _build_report(
        self, req: Dict[str, Any], health: Dict[str, Any], hours: int
    ) -> Dict[str, Any]:
        return {
            "duration_hours": hours,
            "health_status": health.get("status", "unknown"),
            "health_url": health.get("url"),
            "latency_ms": health.get("latency_ms"),
            "service": req.get("affected_service"),
            "release_version": self._derive_version(req),
        }

    def _derive_version(self, req: Dict[str, Any]) -> str:
        sha = req.get("merged_sha", "")
        short_sha = sha[:7] if sha else "unknown"
        return f"v{time.strftime('%Y.%m.%d')}-{short_sha}"


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        import json
        agent = MonitoringAgent()
        if sys.argv[1] == "--sla-scan":
            count = agent.scan_sla_breaches()
            print(f"SLA breaches found: {count}")
        else:
            result = agent.run(sys.argv[1])
            print(json.dumps(result, indent=2))
    else:
        print("Usage: python monitoring_agent.py <request_id>|--sla-scan")
