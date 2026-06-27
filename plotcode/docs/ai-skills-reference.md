# AI Skills & Prompt Reference
> Auto-generated documentation for all Plotcode AI agents.
> Prompt versions are stored in MongoDB `ai_prompt_log` collection.
>
> **Full prompt specifications** for each agent live in [`agents/prompts/`](../agents/prompts/).
> See the [prompts README](../agents/prompts/README.md) for the complete index.

---

## Overview

Plotcode uses 7 specialized AI agents, each with a versioned system prompt. All LLM calls go through **OpenRouter** (primary) with GPT-4o as the default model.

Every agent call is logged in `ai_prompt_log` with:
- `prompt_hash` — SHA-256 of the prompt (for deduplication)
- `prompt_version` — Semantic version string (e.g., `analysis-v2.0-abc123def456`)
- `confidence_score` — AI self-reported confidence (0–100)
- `tokens_input` / `tokens_output` — Token counts
- `latency_ms` — Wall-clock latency

---

## Agent 0: Intake Agent

**File:** `agents/intake_agent.py`
**Prompt spec:** [`agents/prompts/intake_agent.md`](../agents/prompts/intake_agent.md)
**Version:** `intake-v1.0`
**Model:** `openai/gpt-4o` via OpenRouter (priority suggestion only)

### Role
Processes incoming feature requests from Telegram/API, validates structure, extracts metadata, and uses the LLM to suggest priority.

### System Prompt (Priority Suggestion)
```
Analyze this feature request and suggest a priority:
- P0: Critical, production blocking, security issue
- P1: High, significant user impact
- P2: Medium, nice to have
- P3: Low, cosmetic, cleanup

Respond with ONLY the priority code (P0, P1, P2, or P3).
```

### Trigger
- Telegram bot `/request` command
- API `POST /requests`

---

## Agent 1: Analysis Agent

**File:** `agents/analysis_agent.py`
**Prompt spec:** [`agents/prompts/analysis_agent.md`](../agents/prompts/analysis_agent.md)
**Version:** `analysis-v2.0`
**Model:** `openai/gpt-4o` via OpenRouter

### Role
Analyzes the target repository, identifies impacted files/modules, and produces a structured implementation plan with confidence scoring.

### System Prompt
```
You are an expert software architect and senior developer. Your task is to analyze a feature request and a codebase, then produce a detailed implementation plan.

Output sections:
1. Summary — One-line summary
2. Impacted Files — Files to modify/create
3. Implementation Plan — Step-by-step per file
4. Test Plan — Unit and integration tests
5. Risk Assessment — Breaking changes, dependencies
6. Rollback Plan — How to undo (git revert, feature flags)
7. Config Changes — Env vars, secrets, infra
8. Confidence Score — End with: CONFIDENCE: <0-100>
```

### Input
- Feature request (title, business_need, expected_behavior, priority, service)
- Repository context (README, package.json, requirements.txt, relevant source files)

### Output
- Structured Markdown implementation plan
- `CONFIDENCE: <score>` at end (parsed and stored)

### Trigger
- `POST /trigger { agent: "analysis", request_id: "..." }`
- Auto-triggered after request approval via `/requests/{id}/approve`

---

## Agent 2: Coder Agent

**File:** `agents/coder_agent.py`
**Prompt spec:** [`agents/prompts/coder_agent.md`](../agents/prompts/coder_agent.md)
**Model:** `openai/gpt-4o` via OpenRouter

### Role
Creates a feature branch, generates code changes based on the approved implementation plan, and writes unit tests.

### System Prompt
```
You are an expert software engineer.

Rules:
- Follow existing code style and conventions.
- Include comprehensive unit tests for all new logic.
- Write clean, maintainable code with appropriate comments.
- Do not modify unrelated files.

Output format:
### FILE: <path>
```language
<full file content>
```
```

### Input
- Approved implementation plan
- Existing code context (files referenced in plan)

### Output
- Code changes in `### FILE: <path>` blocks
- Applied to feature branch and committed

---

## Agent 3: Validation Agent (Loop Engineer)

**File:** `agents/validation_agent.py`
**Prompt spec:** [`agents/prompts/validation_agent.md`](../agents/prompts/validation_agent.md)
**Model:** `openai/gpt-4o` via OpenRouter

### Role
Monitors CI results, reads failure logs, diagnoses issues, and applies fixes. Retries up to `CI_MAX_RETRY` times (default: 3) before escalating.

### System Prompt
```
You are a CI/CD debugging expert.

Rules:
- Analyze error logs carefully. Identify the file and line.
- Propose minimal, targeted changes.
- Do not change unrelated code.
- If a dependency fix is needed, specify it exactly.
- If you cannot determine the cause, explain what information would help.
```

### Input
- CI failure logs (from GitHub Actions webhook)
- Relevant source files (extracted from log file paths)

### Retry Loop
1. Receive CI failure logs via `/ci-webhook`
2. LLM diagnoses and generates fix
3. Apply fix, commit, push
4. CI re-runs automatically
5. Repeat up to `CI_MAX_RETRY` times
6. Escalate to human if max retries exceeded

---

## Agent 4: PR Agent

**File:** `agents/pr_agent.py`
**Prompt spec:** [`agents/prompts/pr_agent.md`](../agents/prompts/pr_agent.md)
**Model:** `openai/gpt-4o` via OpenRouter

### Role
Creates structured pull requests with full context, and responds to human review comments with code fixes.

### PR Template Sections
- **Summary** — Feature description
- **Changes** — Git diff stat
- **Test Evidence** — CI results reference
- **Risk Notes** — From implementation plan
- **Rollback Plan** — From implementation plan
- **Linked Request** — `REQ-YYYY-NNNN`
- **Checklist** — Unit tests, integration tests, linting, security, rollback

### Review Response Prompt
```
You are a helpful code reviewer. Be polite, explain your reasoning,
and provide precise fixes in ### FILE: <path> format.
```

---

## Agent 5: Deployment Agent

**File:** `agents/deployment_agent.py`
**Prompt spec:** [`agents/prompts/deployment_agent.md`](../agents/prompts/deployment_agent.md)

### Role
Triggers deployments to staging (QA) and production environments via GitHub Actions workflow dispatch.

### Guardrails
- **Production deploy requires** `prod_approved_at` to be set (explicit human approval)
- Both QA and production deploys are logged to audit trail
- Events published to EventBus for real-time dashboard updates

### No LLM — Pure Orchestration
This agent does not call an LLM. It orchestrates GitHub Actions workflows.

---

## Agent 6: Monitoring Agent

**File:** `agents/monitoring_agent.py`
**Prompt spec:** [`agents/prompts/monitoring_agent.md`](../agents/prompts/monitoring_agent.md)

### Role
Post-deployment health monitoring, SLA breach detection, and ticket closure.

### Features
- **HTTP health probes** — GET `{env_url}/health` with timeout
- **SLA breach scanner** — Queries MongoDB for overdue requests
- **EventBus publisher** — Broadcasts health check results to dashboard
- **Retrospective** — Cycle time, AI vs human action counts

### No LLM — Pure Observability
This agent does not call an LLM. It performs operational monitoring.

---

## Prompt Engineering Best Practices

1. **Specificity wins** — Include exact function names, file paths, and data structures in prompts
2. **Confidence scoring** — Always request `CONFIDENCE: <0-100>` at end of planning prompts
3. **Output format constraints** — Enforce `### FILE: <path>` blocks for code output to enable reliable parsing
4. **Temperature: 0.2** — Low temperature for deterministic, accurate outputs (not creative writing)
5. **Context window management** — Truncate codebase context at 15,000 chars to stay within limits
6. **Version your prompts** — Bump `PROMPT_VERSION` constant whenever system prompt changes

---

## Token Budget Reference

| Agent | Typical Input | Typical Output | Max Tokens |
|-------|--------------|----------------|-----------|
| Analysis | 5,000–15,000 | 2,000–4,000 | 4,096 |
| Coder | 5,000–15,000 | 2,000–4,000 | 4,096 |
| Validation | 3,000–8,000 | 500–2,000 | 4,096 |
| PR | 1,000–3,000 | 500–1,500 | 4,096 |

---

*This document is maintained alongside the agent code. Update `PROMPT_VERSION` constants when system prompts change.*
