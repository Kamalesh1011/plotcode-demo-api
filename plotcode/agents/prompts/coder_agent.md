# Coder Agent — Prompt Specification

**File:** `agents/coder_agent.py`
**Class:** `CoderAgent`
**Prompt Version:** `coder-v1.0`
**Model:** `openai/gpt-4o` via OpenRouter
**LLM Usage:** Core — generates code changes and unit tests

---

## Role

Creates a feature branch from the approved implementation plan, generates code
changes for all impacted files, writes unit tests, applies changes to the
working tree, runs best-effort formatting, commits, and pushes.

---

## System Prompt

```
You are an expert software engineer. You will be given an implementation plan
and asked to write code changes.

Rules:
- Follow existing code style and conventions in the repository.
- Include comprehensive unit tests for all new logic.
- Use the project's existing testing framework.
- Write clean, maintainable code with appropriate comments.
- Do not modify unrelated files.
- Prefer small, focused commits.

For each file to change, output in this format:

### FILE: <path>
```<language>
<full file content or diff>
```

If the change is small, output the complete new file content.
If the change is large, output a clear diff-style description.
```

---

## User Prompt Template

```
Implementation Plan:
{implementation_plan}

Existing Code Context:
{context}

Write the complete code changes for all files mentioned in the plan.
Include tests.
```

### Parameters
| Parameter              | Source                                      |
|------------------------|---------------------------------------------|
| `implementation_plan`  | Stored plan from Analysis Agent             |
| `context`              | Existing file contents referenced in plan (top 10 files, 4,000 chars each, truncated to 15,000 total) |

---

## Context Building

`_build_coding_context()` extracts file paths from the plan using
`###?\s*FILE:\s*(\S+)` regex, reads each file's current content, and provides
it to the LLM so changes are based on real existing code.

---

## LLM Settings

- `temperature`: 0.2
- `max_tokens`: 4,096

---

## Output Parsing

`_apply_changes()` parses `### FILE: <path>` blocks with code fences:
```
###\s*FILE:\s*(\S+)[\s\S]*?```(?:\w+)?\n([\s\S]*?)```
```
Each matched file path + content is written to the working tree via
`git.write_file()`.

---

## Post-Processing

1. **Formatting (best-effort):** Runs `npx prettier --write` or `black` on changed files
2. **Commit:** `feat({service}): {title} [{request_id}]`
3. **Push:** Feature branch pushed to origin

---

## Trigger

- `POST /trigger { agent: "coding", request_id: "..." }`
- Worker polling: requests with `status: "plan_approved"`

---

## State Updates

After completion:
- `status` → `ci_running`
- `feature_branch` → branch name
- Audit: `code_changes_applied` with branch, commit SHA, files list

---

## Output Schema

```json
{
  "request_id": "REQ-YYYY-NNNN",
  "branch": "feat/...",
  "commit_sha": "abc123...",
  "files": ["path/to/file1.py", "path/to/test_file1.py"]
}
```
