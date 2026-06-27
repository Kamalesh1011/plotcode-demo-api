# Validation Agent — Prompt Specification

**File:** `agents/validation_agent.py`
**Class:** `ValidationAgent`
**Prompt Version:** `validation-v1.0`
**Model:** `openai/gpt-4o` via OpenRouter
**LLM Usage:** Core — diagnoses CI failures and generates fixes

---

## Role

Monitors CI status, reads failure logs (via GitHub Checks API), diagnoses the
root cause, and proposes minimal targeted fixes. Retries up to `CI_MAX_RETRY`
times (default: 3) before escalating to a human.

---

## System Prompt

```
You are a CI/CD debugging expert. You will be given CI failure logs and the
codebase. Your task is to diagnose the root cause and propose a precise fix.

Rules:
- Analyze the error logs carefully. Identify the file and line causing the
  failure.
- Propose minimal, targeted changes to fix the issue.
- Do not change unrelated code.
- If the fix requires adding a dependency, specify it exactly.
- Output in the same format as the Coder Agent: ### FILE: path with code blocks.

If you cannot determine the cause, state that clearly and explain what
additional information would help.
```

---

## User Prompt Template

```
CI Failure Logs:
{logs}

Relevant Code:
{context}

Request Context: {business_need}

Diagnose the failure and propose the fix. Output in the format:
### FILE: <path>
```<language>
<corrected code>
```
```

### Parameters
| Parameter       | Source                                                        |
|-----------------|---------------------------------------------------------------|
| `logs`          | GitHub Checks API (failed check run logs/annotations) — truncated to 8,000 chars |
| `context`       | Source files extracted from log file paths (top 5, 3,000 chars each) |
| `business_need` | Request record                                                |

---

## CI Log Fetching

`_fetch_ci_logs()` retrieves failure logs via the GitHub Checks API:
1. Get the latest commit SHA for the feature branch
2. List check runs for that SHA
3. Find failed check runs
4. Fetch annotations and log excerpts from failed checks
5. Falls back to webhook-provided `error_summary` if API fetch fails

---

## Context Building

`_build_context()` extracts file paths from logs using:
```
(?:File\s+"|\s)([\w/\-]+\.(?:py|js|ts|jsx|tsx|go|rs|java|kt|swift))
```
Reads up to 5 matching files (3,000 chars each) from the working tree.

---

## LLM Settings

- `temperature`: 0.2
- `max_tokens`: 4,096

---

## Retry Loop

1. Receive CI failure (via `/ci-webhook` or polling `status: "ci_failed"`)
2. Fetch CI logs from GitHub Checks API
3. Build context from files mentioned in logs
4. LLM diagnoses and generates fix
5. Apply fix to files, commit, push
6. Re-trigger CI
7. Repeat up to `CI_MAX_RETRY` times
8. **Escalate to human** if max retries exceeded or no fix generated

---

## Escalation

`_escalate()` sets:
- `status` → `ci_failed`
- `risk_notes` → `"Escalated: {reason}"`

Audit log: `escalated` with reason.

---

## Trigger

- `POST /trigger { agent: "validation", request_id: "...", payload: { "ci_logs": "..." } }`
- `POST /ci-webhook` → background handler
- Worker polling: requests with `status: "ci_failed"`

---

## State Updates

After successful fix:
- `status` → `ci_running`
- Audit: `fix_applied` with retry count, files, log snippet

After escalation:
- `status` → `ci_failed`
- Audit: `escalated` with reason

---

## Output Schema

```json
{
  "request_id": "REQ-YYYY-NNNN",
  "status": "ci_running|escalated",
  "retry_count": 1,
  "files": ["path/to/fixed_file.py"]
}
```
