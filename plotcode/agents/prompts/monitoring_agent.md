# Monitoring Agent — Prompt Specification

**File:** `agents/monitoring_agent.py`
**Class:** `MonitoringAgent`
**Prompt Version:** `monitoring-v2.0`
**Model:** N/A — no LLM calls
**LLM Usage:** None — pure observability agent

---

## Role

Post-deployment health monitoring, SLA breach detection, retrospective
reporting, and ticket closure. Publishes real-time events to the EventBus for
dashboard updates.

---

## No LLM — Pure Observability

This agent does **not** call an LLM. It performs HTTP health probes, queries
MongoDB for SLA breaches, and generates retrospective analytics.

---

## Methods

### `run(request_id, monitoring_duration_hours=24)`

Main entry point — runs health checks, builds a monitoring report, and closes
the ticket.

**Steps:**
1. Run `check_health()` — HTTP probe
2. Build monitoring report (duration, health status, latency, service, version)
3. Derive release version: `v{YYYY.MM.DD}-{short_sha}`
4. Update request: `status` → `closed`, `completed_at`, `release_version`
5. Audit: `ticket_closed` with monitoring details
6. Publish event: `request.closed`

### `check_health(request_id)`

HTTP health probe against the deployed environment.

**Steps:**
1. Get `production_url` or `staging_url` from request
2. HTTP GET `{url}/health` with 15s timeout
3. Healthy if `status_code < 500`
4. Record latency in milliseconds
5. Audit: `health_check`
6. Publish event: `monitoring.health_check`

### `scan_sla_breaches()`

Scans for SLA-breached requests and publishes alerts. Designed to be called
periodically (e.g., every 15 minutes via a background scheduler).

**Steps:**
1. Query MongoDB for requests where `sla_deadline < now` and not terminal
2. For each breach:
   - Mark `sla_breach_alert_sent = True`
   - Audit: `sla_breached` with deadline, status, priority
   - Publish event: `sla.breached`
3. Returns count of breaches found

### `generate_retrospective(request_id)`

Generates a mini-retrospective for a completed request.

**Calculates:**
- **Cycle time:** `completed_at - created_at` (in hours)
- **Total events:** audit log count
- **AI actions:** audit logs where `actor_type == "ai"`
- **Human approvals:** audit logs where `actor_type == "human"`
- **Stage timeline:** submitted → approved → plan_approved → pr_merged → qa_validated → prod_approved → completed

---

## SLA Hours Mapping

| Priority | SLA Hours |
|----------|-----------|
| P0       | 4         |
| P1       | 24        |
| P2       | 72        |
| P3       | 168       |

---

## Events Published

| Event Type              | Trigger                    |
|-------------------------|----------------------------|
| `request.closed`        | Ticket closed after monitoring |
| `monitoring.health_check` | Health probe completed    |
| `sla.breached`          | SLA deadline passed        |

---

## Trigger

- `POST /trigger { agent: "monitoring", request_id: "..." }`
- Worker polling: requests with `status: "deployed"`
- `scan_sla_breaches()` — scheduled background task
- `generate_retrospective()` — on-demand via API or CLI

---

## State Updates

After `run()`:
- `status` → `closed`
- `completed_at` → ISO timestamp
- `release_version` → `v{YYYY.MM.DD}-{short_sha}`
- Audit: `ticket_closed`

---

## Output Schema

```json
{
  "request_id": "REQ-YYYY-NNNN",
  "status": "closed",
  "release_version": "v2025.06.27-abc1234",
  "monitoring_report": {
    "duration_hours": 24,
    "health_status": "healthy",
    "health_url": "https://...",
    "latency_ms": 142,
    "service": "demo-api",
    "release_version": "v2025.06.27-abc1234"
  }
}
```
