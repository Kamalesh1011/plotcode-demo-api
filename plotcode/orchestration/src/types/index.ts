import { z } from 'zod';

// ==========================================
// Request Types
// ==========================================

export const RequestStatus = z.enum([
  'submitted', 'pending_review', 'approved', 'rejected',
  'planning', 'plan_pending_approval', 'plan_approved',
  'coding', 'ci_running', 'ci_failed', 'ci_passed',
  'pr_open', 'pr_reviewing', 'pr_approved', 'pr_merged',
  'qa_deployed', 'qa_validating', 'qa_passed', 'qa_failed',
  'prod_pending_approval', 'prod_approved', 'deploying', 'deployed',
  'monitoring', 'closed', 'cancelled'
]);

export const Priority = z.enum(['P0', 'P1', 'P2', 'P3']);
export const Phase = z.enum(['MVP', 'Phase 2', 'Phase 3']);
export const Source = z.enum(['slack', 'telegram', 'api']);
export const Role = z.enum(['requester', 'reviewer', 'approver', 'prod_owner', 'admin']);
export const ActorType = z.enum(['human', 'ai', 'system']);

export type RequestStatusType = z.infer<typeof RequestStatus>;
export type PriorityType = z.infer<typeof Priority>;
export type PhaseType = z.infer<typeof Phase>;
export type SourceType = z.infer<typeof Source>;
export type RoleType = z.infer<typeof Role>;
export type ActorTypeType = z.infer<typeof ActorType>;

export interface FeatureRequest {
  id?: string;
  request_id: string;
  title: string;
  business_need: string;
  expected_behavior: string;
  priority: PriorityType;
  affected_service?: string;
  requester_name: string;
  requester_slack_id?: string;
  requester_telegram_id?: string;
  requester_team?: string;
  status: RequestStatusType;
  phase: PhaseType;
  source: SourceType;
  
  // Thread tracking (for Slack notifications)
  thread_ts?: string;
  slack_channel_id?: string;
  
  // HITL fields
  initial_approver_slack_id?: string;
  initial_approved_at?: string;
  initial_rejection_reason?: string;
  plan_approver_slack_id?: string;
  plan_approved_at?: string;
  plan_rejection_reason?: string;
  pr_merger_slack_id?: string;
  pr_merged_at?: string;
  qa_validator_slack_id?: string;
  qa_validated_at?: string;
  qa_failure_reason?: string;
  prod_approver_slack_id?: string;
  prod_approved_at?: string;
  
  // Implementation details
  implementation_plan?: string;
  risk_notes?: string;
  rollback_plan?: string;
  
  // Git tracking
  feature_branch?: string;
  base_branch?: string;
  pr_number?: number;
  pr_url?: string;
  merged_sha?: string;
  
  // Deployment
  staging_url?: string;
  production_url?: string;
  deploy_timestamp?: string;
  release_version?: string;
  
  // Timestamps
  created_at?: string;
  updated_at?: string;
  completed_at?: string;
}

export interface AuditLogEntry {
  id?: string;
  request_id: string;
  actor_type: ActorTypeType;
  actor_id: string;
  action: string;
  details?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  created_at?: string;
}

export interface User {
  id?: string;
  slack_id?: string;
  telegram_id?: string;
  email?: string;
  name: string;
  team?: string;
  role: RoleType;
  is_active?: boolean;
}

export interface Service {
  id?: string;
  name: string;
  repo_url: string;
  default_branch?: string;
  team_owner?: string;
  tech_stack?: string[];
  ci_workflow_path?: string;
  staging_env?: string;
  production_env?: string;
}

// ==========================================
// Slack Types
// ==========================================

export interface SlackPayload {
  type: 'view_submission' | 'block_actions' | 'event_callback';
  user?: { id: string; name: string };
  team?: { id: string };
  view?: {
    state: {
      values: Record<string, Record<string, { value: string; selected_option?: { value: string } }>>;
    };
    private_metadata?: string;
  };
  actions?: Array<{
    action_id: string;
    block_id: string;
    value: string;
  }>;
  trigger_id?: string;
  response_url?: string;
}

export interface SlackCommandBody {
  token: string;
  team_id: string;
  team_domain: string;
  channel_id: string;
  channel_name: string;
  user_id: string;
  user_name: string;
  command: string;
  text: string;
  response_url: string;
  trigger_id: string;
}

// ==========================================
// Telegram Types
// ==========================================

export interface TelegramUpdate {
  update_id: number;
  message?: {
    message_id: number;
    from: { id: number; first_name: string; username?: string };
    chat: { id: number; type: string };
    text?: string;
    date: number;
  };
}

// ==========================================
// GitHub Types
// ==========================================

export interface GitHubPR {
  number: number;
  html_url: string;
  state: string;
  merged: boolean;
  merge_commit_sha?: string;
}

export interface CIStatus {
  status: 'pending' | 'success' | 'failure' | 'error';
  conclusion?: string;
  check_runs: Array<{
    name: string;
    status: string;
    conclusion?: string;
    output?: { title?: string; summary?: string };
  }>;
}

// ==========================================
// Agent Message Types
// ==========================================

export interface AgentMessage {
  request_id: string;
  agent: string;
  action: string;
  payload: Record<string, unknown>;
  timestamp: string;
}

export interface HITLCheckpoint {
  gate: number;
  name: string;
  required_role: RoleType;
  status: 'pending' | 'approved' | 'rejected';
  approver_id?: string;
  approved_at?: string;
  rejection_reason?: string;
}
