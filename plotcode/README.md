# Plotcode: AI-Assisted End-to-End Delivery Automation

An agentic platform that automates the software development lifecycle from Slack feature request to production deployment, with strict human-in-the-loop (HITL) checkpoints.

## Architecture

```
┌─────────┐     ┌──────────────┐     ┌─────────────────┐     ┌──────────┐
│  Slack  │────▶│ Orchestration│────▶│  Python Agents  │────▶│  GitHub  │
│Telegram │     │  (Node.js)   │     │  (AI + Tools)   │     │  CI/CD   │
└─────────┘     └──────────────┘     └─────────────────┘     └──────────┘
                     │
                     ▼
               ┌──────────┐
               │ Supabase │
               │(State DB)│
               └──────────┘
```

## 14-Stage Workflow

1. **Request Submission** — Slack/Telegram form intake
2. **Intake & Tracking** — Request ID generated, ticket created in Supabase
3. **HITL Gate 1** — Human approves the initial request
4. **AI Repo Analysis** — Agent clones repo, maps impact, proposes plan
5. **HITL Gate 2** — Human approves the implementation plan
6. **Branch & Code** — Agent creates feature branch, writes code + tests
7. **CI Validation** — Lint, tests, build. AI self-heals failures
8. **PR Creation** — Structured PR with summary, risks, rollback plan
9. **HITL Gate 3** — Human code review & merge
10. **QA Deploy** — Auto-deploy to staging
11. **HITL Gate 4** — QA validation by requester
12. **HITL Gate 5** — Production Owner approval
13. **Production Deploy** — Deploy with monitoring
14. **Closure** — Ticket closed, changelog updated, Slack notified

## Project Structure

```
plotcode/
├── orchestration/          # Node.js/TypeScript event orchestration
│   ├── src/
│   │   ├── routes/         # Slack/Telegram webhook handlers
│   │   ├── services/       # Supabase, GitHub, Slack clients
│   │   ├── middleware/       # RBAC, auth
│   │   └── types/          # TypeScript definitions
│   └── package.json
├── agents/                 # Python AI agents
│   ├── intake_agent.py
│   ├── analysis_agent.py
│   ├── coder_agent.py
│   ├── validation_agent.py
│   ├── pr_agent.py
│   ├── deployment_agent.py
│   ├── monitoring_agent.py
│   ├── shared/
│   │   ├── state.py        # Central state store interface
│   │   ├── llm_client.py   # OpenAI/NVIDIA NIM wrapper
│   │   └── git_client.py   # Git/GitHub operations
│   └── prompts/            # LLM prompt templates
├── supabase/
│   └── schema.sql          # Database schema
└── docker-compose.yml      # Local dev stack
```

## Quick Start

### 1. Environment Setup

```bash
cp .env.example .env
# Fill in your API keys and configuration
```

### 2. Start Infrastructure

```bash
docker-compose up -d
```

### 3. Install Dependencies

```bash
# Node.js orchestration
cd orchestration
npm install

# Python agents
cd ../agents
pip install -r requirements.txt
```

### 4. Run

```bash
# Terminal 1: Orchestration server
cd orchestration
npm run dev

# Terminal 2: Python agent worker
cd agents
python -m intake_agent
```

## Environment Variables

See `.env.example` for all required configuration.

## Human-in-the-Loop Checkpoints

| Gate | Action | Required Role |
|------|--------|---------------|
| Gate 1 | Approve initial request | Product/Technical Owner |
| Gate 2 | Approve implementation plan | Developer/Architect |
| Gate 3 | Approve PR / merge | Reviewer |
| Gate 4 | Validate in QA | Requester/QA Owner |
| Gate 5 | Approve production deploy | Production Owner |

## AI Guardrails (Non-Negotiable)

- AI **never** merges a PR without human approval
- AI **never** deploys to production without explicit human approval
- AI **never** reads, logs, or transmits secrets
- AI **never** modifies RBAC or pipeline configuration
- AI **never** skips a defined HITL gate
- Self-healing loop halts after max retries and escalates to human
- All AI actions are logged with prompt, response hash, and timestamp

## License

Internal — Confidential
