# Deployment Agent — Prompt Specification

**File:** `agents/deployment_agent.py`
**Class:** `DeploymentAgent`
**Prompt Version:** `deployment-v1.0`
**Model:** N/A — no LLM calls
**LLM Usage:** None — pure orchestration agent

---

## Role

Manages deployments to QA/staging and production environments via CI/CD
workflow triggers. Requires explicit human approval for production deployments.

---

## No LLM — Pure Orchestration

This agent does **not** call an LLM. It orchestrates GitHub Actions workflow
dispatches and records deployment state. All actions are logged to the audit
trail for compliance.

---

## Methods

### `deploy_qa(request_id)`

Deploys merged code to the QA/staging environment.

**Steps:**
1. Look up request and service
2. Get staging URL from service record or `STAGING_ENV_URL` env var
3. Trigger staging deployment workflow (`deploy.yml` with `environment=staging`)
4. Update request: `status` → `qa_deployed`, `staging_url` → URL
5. Audit: `qa_deploy_triggered`

### `deploy_production(request_id)`

Deploys approved code to production.

**Guardrail:** Requires `prod_approved_at` to be set on the request.
Raises `PermissionError` if not approved.

**Steps:**
1. Verify `prod_approved_at` exists (HITL gate)
2. Look up request and service
3. Get production URL from service record or `PRODUCTION_ENV_URL` env var
4. Trigger production deployment workflow (`deploy.yml` with `environment=production`)
5. Update request: `status` → `deployed`, `production_url`, `deploy_timestamp`
6. Audit: `production_deploy_triggered` (includes approver ID)

### `check_health(request_id)`

Runs a post-deploy HTTP smoke test.

**Steps:**
1. Get `production_url` or `staging_url` from request
2. HTTP GET with 30s timeout
3. Healthy if `status_code < 500`
4. Audit: `health_check` or `health_check_failed`

---

## Workflow Trigger

`_trigger_deploy()` dispatches a GitHub Actions workflow:
```python
# workflow file: deploy.yml with inputs: environment, sha
self.git._trigger_workflow(repo_name, 'deploy.yml', branch, {
    'environment': environment,  # "staging" | "production"
    'sha': sha
})
```

For MVP/local mode, this logs the action without actual dispatch.

---

## Trigger

- `POST /trigger { agent: "deployment", request_id: "...", payload: { "environment": "qa|production" } }`
- Worker polling:
  - `status: "pr_merged"` → `deploy_qa()`
  - `status: "qa_passed"` + `prod_approved_at` → `deploy_production()`

---

## State Updates

| Method             | Status After   | Audit Action              |
|--------------------|----------------|---------------------------|
| `deploy_qa`        | `qa_deployed`  | `qa_deploy_triggered`     |
| `deploy_production`| `deployed`     | `production_deploy_triggered` |
| `check_health`     | (no change)    | `health_check`            |

---

## Output Schema

```json
{
  "request_id": "REQ-YYYY-NNNN",
  "environment": "staging|production",
  "status": "qa_deployed|deployed",
  "url": "https://..."
}
```

---

## Guardrails (Non-Negotiable)

- **Never** deploys to production without `prod_approved_at`
- All deploys logged with approver identity
- Environment URLs sourced from service registry or env vars (never hardcoded)
