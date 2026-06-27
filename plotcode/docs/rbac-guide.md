# RBAC Guide — Plotcode Delivery Automation

## Overview

Plotcode enforces **Role-Based Access Control (RBAC)** at two layers:
1. **Telegram Bot** — via `telegram_rbac.py` (`RBACChecker`)
2. **HTTP API** — via `middleware/auth.py` (FastAPI dependencies)

---

## Roles

| Role | Description |
|------|-------------|
| `admin` | Full platform access. Can manage all requests, users, and deployments. |
| `product_owner` | Reviews and approves/rejects requests and plans. Validates QA. |
| `developer` | Approves technical plans and merges PRs. |
| `qa_engineer` | Approves or fails QA validation. |
| `requester` | Submits feature requests only. Default role for new users. |

---

## Permission Matrix

| Permission | admin | product_owner | developer | qa_engineer | requester |
|------------|:-----:|:-------------:|:---------:|:-----------:|:---------:|
| `submit_request` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `approve_request` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `reject_request` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `approve_plan` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `reject_plan` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `merge_pr` | ✅ | ❌ | ✅ | ❌ | ❌ |
| `approve_qa` | ✅ | ✅ | ❌ | ✅ | ❌ |
| `fail_qa` | ✅ | ❌ | ❌ | ✅ | ❌ |
| `approve_prod` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `hold_prod` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `list_requests` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `view_audit` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `manage_users` | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## Human-in-the-Loop Checkpoints

Each checkpoint is enforced by RBAC before any action is taken:

```
Stage 3:  Initial Approval   → product_owner / admin
Stage 5:  Plan Approval      → developer / product_owner / admin
Stage 9:  PR Review & Merge  → developer / admin
Stage 11: QA Validation      → qa_engineer / product_owner / admin
Stage 12: Production Approval→ admin only
```

---

## How to Assign Roles

### Via Telegram Bot
```
/setrole <telegram_user_id> <role>
```
Example:
```
/setrole 123456789 developer
```
> Only `admin` users can run `/setrole`.

### Via Dashboard
1. Navigate to **RBAC** page in the dashboard
2. Find the user in the Users table
3. Select a new role from the dropdown
4. Change is applied immediately via `PATCH /users/{telegram_id}/role`

### Via API
```bash
curl -X PATCH http://localhost:8001/users/123456789/role \
  -H "Content-Type: application/json" \
  -H "X-API-Key: plotcode-dev-key-change-in-prod" \
  -d '{"role": "developer"}'
```

---

## Bootstrap Admin

Admin users can be pre-configured via environment variables **before** any Telegram interaction:

```env
ADMIN_TELEGRAM_IDS=1457080673,987654321
PROD_OWNER_TELEGRAM_IDS=1457080673
```

Bootstrap admins always have admin privileges regardless of DB role. This prevents lockout.

---

## Auto-Registration

When an unknown user sends any Telegram message, they are **automatically registered** as `requester`. They can then be promoted by an admin.

---

## API Key Authentication

All HTTP API endpoints accept an API key via header:
```
X-API-Key: <your-api-key>
```

Set your key in `.env`:
```env
AGENT_API_KEY=your-secret-key-here
```

Default (dev only — change in production): `plotcode-dev-key-change-in-prod`

---

## Security Considerations

> [!WARNING]
> **Never** use the default API key in production. Generate a strong random key:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

> [!IMPORTANT]
> MongoDB Atlas connection string contains credentials. Store it in `.env` and **never** commit `.env` to version control.

> [!NOTE]
> RBAC is enforced at both the Telegram bot layer and the HTTP API layer independently. A user cannot bypass Telegram RBAC by calling the API directly if proper API key auth is configured.
