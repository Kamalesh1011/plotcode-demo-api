-- ==========================================
-- Plotcode: Supabase Schema
-- Central state store for AI delivery automation
-- ==========================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================
-- 1. Requests (Central feature request table)
-- ==========================================
CREATE TABLE IF NOT EXISTS requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id TEXT NOT NULL UNIQUE,              -- e.g. REQ-2025-0042
    title TEXT NOT NULL,
    business_need TEXT NOT NULL,
    expected_behavior TEXT NOT NULL,
    priority TEXT NOT NULL CHECK (priority IN ('P0','P1','P2','P3')),
    affected_service TEXT,
    requester_name TEXT NOT NULL,
    requester_slack_id TEXT,
    requester_team TEXT,
    status TEXT NOT NULL DEFAULT 'submitted'
        CHECK (status IN (
            'submitted','pending_review','approved','rejected',
            'planning','plan_pending_approval','plan_approved',
            'coding','ci_running','ci_failed','ci_passed',
            'pr_open','pr_reviewing','pr_approved','pr_merged',
            'qa_deployed','qa_validating','qa_passed','qa_failed',
            'prod_pending_approval','prod_approved','deploying','deployed',
            'monitoring','closed','cancelled'
        )),
    phase TEXT NOT NULL DEFAULT 'MVP'
        CHECK (phase IN ('MVP','Phase 2','Phase 3')),
    source TEXT NOT NULL DEFAULT 'slack'
        CHECK (source IN ('slack','telegram','api')),
    
    -- HITL tracking
    initial_approver_slack_id TEXT,
    initial_approved_at TIMESTAMPTZ,
    initial_rejection_reason TEXT,
    
    plan_approver_slack_id TEXT,
    plan_approved_at TIMESTAMPTZ,
    plan_rejection_reason TEXT,
    
    pr_merger_slack_id TEXT,
    pr_merged_at TIMESTAMPTZ,
    
    qa_validator_slack_id TEXT,
    qa_validated_at TIMESTAMPTZ,
    qa_failure_reason TEXT,
    
    prod_approver_slack_id TEXT,
    prod_approved_at TIMESTAMPTZ,
    
    -- Implementation details
    implementation_plan TEXT,
    risk_notes TEXT,
    rollback_plan TEXT,
    
    -- Git tracking
    feature_branch TEXT,
    base_branch TEXT DEFAULT 'main',
    pr_number INTEGER,
    pr_url TEXT,
    merged_sha TEXT,
    
    -- Deployment tracking
    staging_url TEXT,
    production_url TEXT,
    deploy_timestamp TIMESTAMPTZ,
    release_version TEXT,
    
    -- SLA tracking
    sla_breach_alert_sent BOOLEAN DEFAULT FALSE,
    sla_deadline TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);
CREATE INDEX IF NOT EXISTS idx_requests_priority ON requests(priority);
CREATE INDEX IF NOT EXISTS idx_requests_requester ON requests(requester_slack_id);
CREATE INDEX IF NOT EXISTS idx_requests_created_at ON requests(created_at DESC);

-- ==========================================
-- 2. Audit Log (Immutable action log)
-- ==========================================
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id TEXT NOT NULL REFERENCES requests(request_id) ON DELETE CASCADE,
    actor_type TEXT NOT NULL CHECK (actor_type IN ('human','ai','system')),
    actor_id TEXT NOT NULL,                        -- slack_id for humans, agent_name for AI
    action TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_request ON audit_log(request_id);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log(created_at DESC);

-- ==========================================
-- 3. Users & RBAC
-- ==========================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slack_id TEXT UNIQUE,
    telegram_id TEXT UNIQUE,
    email TEXT UNIQUE,
    name TEXT NOT NULL,
    team TEXT,
    role TEXT NOT NULL DEFAULT 'requester'
        CHECK (role IN ('requester','reviewer','approver','prod_owner','admin')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_slack ON users(slack_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- ==========================================
-- 4. Service Registry
-- ==========================================
CREATE TABLE IF NOT EXISTS services (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    repo_url TEXT NOT NULL,
    default_branch TEXT DEFAULT 'main',
    team_owner TEXT,
    tech_stack TEXT[],
    ci_workflow_path TEXT,
    staging_env TEXT,
    production_env TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- 5. AI Prompt Log (for auditing AI behavior)
-- ==========================================
CREATE TABLE IF NOT EXISTS ai_prompt_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id TEXT NOT NULL REFERENCES requests(request_id) ON DELETE CASCADE,
    agent_name TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_hash TEXT NOT NULL,                     -- SHA-256 of prompt
    prompt_preview TEXT,                           -- First 1000 chars
    response_hash TEXT,                            -- SHA-256 of response
    response_preview TEXT,                        -- First 1000 chars
    tokens_input INTEGER,
    tokens_output INTEGER,
    latency_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_prompt_request ON ai_prompt_log(request_id);

-- ==========================================
-- 6. Functions & Triggers
-- ==========================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_requests_updated_at ON requests;
CREATE TRIGGER update_requests_updated_at
    BEFORE UPDATE ON requests
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) policies
ALTER TABLE requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_prompt_log ENABLE ROW LEVEL SECURITY;

-- Allow service role full access (used by backend)
CREATE POLICY service_role_all_requests ON requests FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY service_role_all_audit ON audit_log FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY service_role_all_users ON users FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY service_role_all_prompts ON ai_prompt_log FOR ALL USING (true) WITH CHECK (true);

-- ==========================================
-- 7. Seed Data (Optional)
-- ==========================================

-- Example service
INSERT INTO services (name, repo_url, default_branch, team_owner, tech_stack, staging_env, production_env)
VALUES (
    'demo-api',
    'https://github.com/plotcode/demo-api',
    'main',
    'Platform Team',
    ARRAY['python','fastapi','postgresql'],
    'https://staging-api.plotcode.dev',
    'https://api.plotcode.dev'
)
ON CONFLICT (name) DO NOTHING;
