# Agent Prompt Templates

This directory contains the prompt specifications for all 7 Plotcode AI agents.
Each file documents the agent's role, system prompt, input/output format, LLM
settings, trigger conditions, and state updates.

## Agents

| # | Agent        | File                          | LLM  | Prompt Version     |
|---|--------------|-------------------------------|------|--------------------|
| 1 | Intake       | `intake_agent.md`             | Minimal | `intake-v1.0`   |
| 2 | Analysis     | `analysis_agent.md`           | Core | `analysis-v2.0`    |
| 3 | Coder        | `coder_agent.md`              | Core | `coder-v1.0`       |
| 4 | Validation   | `validation_agent.md`         | Core | `validation-v1.0`  |
| 5 | PR           | `pr_agent.md`                 | Review only | `pr-v1.0`     |
| 6 | Deployment   | `deployment_agent.md`         | None | `deployment-v1.0`  |
| 7 | Monitoring   | `monitoring_agent.md`         | None | `monitoring-v2.0`  |

## Prompt Versioning

Every LLM call is logged in MongoDB `ai_prompt_log` with:
- `prompt_hash` — SHA-256 of the full prompt (for deduplication)
- `prompt_version` — Semantic version string (e.g., `analysis-v2.0-abc123def456`)
- `confidence_score` — AI self-reported confidence (0–100)
- `tokens_input` / `tokens_output` — Token counts
- `latency_ms` — Wall-clock latency

**Rule:** Bump the `PROMPT_VERSION` constant in the agent source file whenever
the system prompt changes. Update the corresponding `.md` file in this directory
to match.

## LLM Configuration

- **Provider:** OpenRouter (primary), NVIDIA NIM (fallback)
- **Default model:** `openai/gpt-4o`
- **Temperature:** 0.2 (low — deterministic but flexible)
- **Max tokens:** 4,096
- **Context truncation:** 15,000 chars max per call

## Best Practices

1. **Specificity wins** — Include exact function names, file paths, and data structures
2. **Confidence scoring** — Always request `CONFIDENCE: <0-100>` for planning prompts
3. **Output format constraints** — Enforce `### FILE: <path>` blocks for code output
4. **Low temperature** — 0.2 for deterministic, accurate outputs
5. **Context window management** — Truncate codebase context to stay within limits
6. **Version your prompts** — Bump `PROMPT_VERSION` whenever system prompt changes
