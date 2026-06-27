# Analysis Agent — Prompt Specification

**File:** `agents/analysis_agent.py`
**Class:** `AnalysisAgent`
**Prompt Version:** `analysis-v2.0`
**Model:** `openai/gpt-4o` via OpenRouter
**LLM Usage:** Core — generates the full implementation plan

---

## Role

Clones the target repository, performs static analysis on the codebase, and
generates a detailed Markdown implementation plan with risk assessment, rollback
plan, and an AI confidence score (0–100).

---

## System Prompt

```
You are an expert software architect and senior developer. Your task is to
analyze a feature request and a codebase, then produce a detailed implementation
plan.

Your output must be a structured Markdown document with these sections:
1. **Summary** — One-line summary of the change
2. **Impacted Files** — List of files to modify/create with brief rationale
3. **Implementation Plan** — Step-by-step changes for each file
4. **Test Plan** — Unit tests and integration tests to write
5. **Risk Assessment** — Breaking changes, dependencies, performance concerns
6. **Rollback Plan** — How to undo this change (git revert, feature flags, etc.)
7. **Config Changes** — Any env vars, secrets, or infra changes needed
8. **Confidence Score** — End your response with a line:
   `CONFIDENCE: <0-100>` reflecting how complete and accurate this plan is.

Be specific. Include exact function names, API endpoints, and data structures
where possible.
```

---

## User Prompt Template

```
Feature Request:
- Title: {title}
- Business Need: {business_need}
- Expected Behavior: {expected_behavior}
- Priority: {priority}
- Service: {affected_service}

Repository Context:
{context}

Generate the implementation plan according to the system instructions.
End with: CONFIDENCE: <0-100>
```

### Parameters
| Parameter            | Source                          |
|----------------------|---------------------------------|
| `title`              | Request record                  |
| `business_need`      | Request record                  |
| `expected_behavior`  | Request record                  |
| `priority`           | Request record (P0–P3)          |
| `affected_service`   | Request record                  |
| `context`            | Repo files (README, package.json, requirements.txt, relevant source — truncated to 15,000 chars) |

---

## Context Building

`_build_context()` reads:
1. **Structural files:** `README.md`, `package.json`, `requirements.txt`, `pyproject.toml`, `Dockerfile` (first 2,000 chars each)
2. **Relevant source files:** Files whose paths contain keywords from `business_need` + `expected_behavior` (top 10, first 3,000 chars each)

---

## LLM Settings

- `temperature`: 0.2 (low — deterministic but flexible)
- `max_tokens`: 4,096
- `prompt_version`: `analysis-v2.0-{sha256_hash[:12]}` (hash of system+user prompt)

---

## Output Parsing

`_parse_plan()` extracts via regex:
- **Risk Assessment** → stored in `risk_notes`
- **Rollback Plan** → stored in `rollback_plan`
- **Impacted Files** → stored in audit log

`_extract_confidence()` parses `CONFIDENCE: <0-100>` from the plan tail.
Default: 75.0 if not found.

---

## Trigger

- `POST /trigger { agent: "analysis", request_id: "..." }`
- Auto-triggered after request approval: `POST /requests/{id}/approve`
- Worker polling: requests with `status: "approved"`

---

## State Updates

After completion:
- `status` → `plan_pending_approval`
- `implementation_plan` → generated plan text
- `risk_notes` → extracted risks
- `rollback_plan` → extracted rollback
- `feature_branch` → `feat/{request_id}-{slug(title)[:30]}`
- `ai_confidence` → parsed score
- `prompt_version` → version string

Event published: `agent.plan_generated`
