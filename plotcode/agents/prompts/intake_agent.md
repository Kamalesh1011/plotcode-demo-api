# Intake Agent — Prompt Specification

**File:** `agents/intake_agent.py`
**Class:** `IntakeAgent`
**Prompt Version:** `intake-v1.0`
**Model:** `openai/gpt-4o` via OpenRouter (priority suggestion only)
**LLM Usage:** Minimal — only used for `auto_suggest_priority()`

---

## Role

Processes incoming feature requests from secondary channels (Telegram, API) and
records them in the central tracking system. Validates request structure,
extracts metadata (priority, service, team), and uses the LLM to suggest a
priority when one is not explicitly provided.

Primary Slack intake is handled by the Node.js orchestration layer; this agent
covers Telegram and direct API submissions.

---

## System Prompt (Priority Suggestion)

```
Analyze this feature request and suggest a priority:
- P0: Critical, production blocking, security issue, major revenue impact
- P1: High, significant user impact, important feature
- P2: Medium, nice to have, minor improvement
- P3: Low, cosmetic, cleanup, documentation

Business Need: {business_need}
Expected Behavior: {expected_behavior}

Respond with ONLY the priority code (P0, P1, P2, or P3).
```

### Parameters
| Parameter         | Source                          |
|-------------------|---------------------------------|
| `business_need`   | Parsed from request text line 2 |
| `expected_behavior` | Parsed from request text line 3 |

### Output
A single priority code: `P0`, `P1`, `P2`, or `P3`.

### LLM Settings
- `temperature`: 0.0 (deterministic)
- `max_tokens`: 10

---

## Input Parsing (No LLM)

The `process_telegram_request` method parses raw Telegram `/request` messages:

```
/request
<title>
<business_need>
<expected_behavior>
```

Metadata extraction via regex:
- **Priority:** `\b(P[0-3])\b` (case-insensitive)
- **Service:** `service[:\s]+(\w+)`
- **Team:** `team[:\s]+(\w+)`

---

## Validation Rules (No LLM)

`validate_request()` enforces:
1. Required fields: `business_need`, `expected_behavior`, `requester_name`
2. `business_need` must be ≥ 10 characters (reject vague requests)
3. `affected_service` must exist in the service registry

---

## Trigger

- Telegram bot `/request` command → `process_telegram_request()`
- API `POST /requests` → validation + storage
- Not directly triggerable via `/trigger` endpoint (orchestration-only agent)

---

## Output Schema

```json
{
  "title": "string",
  "business_need": "string",
  "expected_behavior": "string",
  "priority": "P0|P1|P2|P3",
  "affected_service": "string",
  "requester_name": "string",
  "requester_telegram_id": "string",
  "requester_team": "string|null",
  "source": "telegram|api"
}
```
