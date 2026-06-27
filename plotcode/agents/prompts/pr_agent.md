# PR Agent — Prompt Specification

**File:** `agents/pr_agent.py`
**Class:** `PRAgent`
**Prompt Version:** `pr-v1.0`
**Model:** `openai/gpt-4o` via OpenRouter
**LLM Usage:** Review response only — PR creation is orchestration

---

## Role

Creates structured pull requests with comprehensive descriptions (summary,
changes, test evidence, risk notes, rollback plan, checklist). Responds to
human review comments by generating code fixes when needed.

---

## PR Creation (No LLM)

PR creation is pure orchestration — no LLM call. The PR description is built
from the `PR_TEMPLATE` using data stored during earlier pipeline stages.

### PR Template

```markdown
## Summary
{summary}

## Changes
{changes}

## Test Evidence
{tests}

## Risk Notes
{risk_notes}

## Rollback Plan
{rollback_plan}

## Linked Request
{request_id}

## Checklist
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Linting passes
- [ ] Security scan clean
- [ ] Rollback plan verified
```

### Template Parameters
| Parameter        | Source                                   |
|------------------|------------------------------------------|
| `summary`        | Request title                            |
| `changes`        | `git diff {base}...{branch} --stat`      |
| `tests`          | Test evidence file detection (coverage/lcov, test-results.xml, pytest-report.html) |
| `risk_notes`     | From Analysis Agent (`risk_notes` field) |
| `rollback_plan`  | From Analysis Agent (`rollback_plan` field) |
| `request_id`     | Request ID                               |

---

## Review Response Prompt (LLM)

When a human reviewer leaves a comment, the agent generates a response and
proposes fixes.

### System Prompt

```
You are a helpful code reviewer. Be polite, explain your reasoning, and provide
precise fixes.
```

### User Prompt Template

```
Review comment: {review_comment}

Code context:
{context}

Respond to the review comment. If a code change is needed, provide the fix in
the format:
### FILE: <path>
```<language>
<fixed code>
```
```

### Parameters
| Parameter        | Source                                              |
|------------------|-----------------------------------------------------|
| `review_comment` | Human reviewer's comment text                       |
| `context`        | Source files extracted from comment (file paths matching `[\w/\-]+\.(?:py|js|ts|...)`, 3,000 chars each) |

---

## LLM Settings (Review Response)

- `temperature`: 0.2
- `max_tokens`: 4,096

---

## Output Parsing

`_apply_changes()` parses `### FILE: <path>` blocks and writes fixes to the
working tree, commits with `refactor: address PR review feedback [{branch}]`,
and pushes.

---

## Trigger

- `POST /trigger { agent: "pr", request_id: "..." }`
- Worker polling: requests with `status: "ci_passed"`
- `respond_to_review()` called when review comments arrive

---

## State Updates

After PR creation:
- `status` → `pr_open`
- `pr_number` → PR number
- `pr_url` → PR HTML URL
- Audit: `pr_created`

After review response:
- Audit: `review_changes_applied` with comment and files

---

## Output Schema

```json
{
  "request_id": "REQ-YYYY-NNNN",
  "pr_number": 42,
  "pr_url": "https://github.com/org/repo/pull/42"
}
```
