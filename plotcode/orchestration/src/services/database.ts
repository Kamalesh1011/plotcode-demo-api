/**
 * Local SQLite database service — replaces Supabase for local development.
 * Uses sql.js (pure JS, no native compilation needed).
 */

import initSqlJs, { Database as SqlJsDatabase } from 'sql.js';
import path from 'path';
import fs from 'fs';
import { v4 as uuidv4 } from 'uuid';
import { FeatureRequest, AuditLogEntry, User, Service } from '../types';
import logger from './logger';

const DB_PATH = process.env.DATABASE_PATH || path.join(__dirname, '..', '..', '..', 'plotcode.db');

let db: SqlJsDatabase | null = null;

async function getDb(): Promise<SqlJsDatabase> {
  if (!db) {
    const SQL = await initSqlJs();
    if (fs.existsSync(DB_PATH)) {
      const buffer = fs.readFileSync(DB_PATH);
      db = new SQL.Database(buffer);
    } else {
      db = new SQL.Database();
    }
    db.run('PRAGMA journal_mode = WAL');
    db.run('PRAGMA foreign_keys = ON');
    initSchema();
    saveDb();
  }
  return db;
}

function saveDb() {
  if (db) {
    const data = db.export();
    const buffer = Buffer.from(data);
    fs.writeFileSync(DB_PATH, buffer);
  }
}

function initSchema() {
  db!.run(`
    CREATE TABLE IF NOT EXISTS requests (
      id TEXT PRIMARY KEY,
      request_id TEXT NOT NULL UNIQUE,
      title TEXT NOT NULL,
      business_need TEXT NOT NULL DEFAULT '',
      expected_behavior TEXT NOT NULL DEFAULT '',
      priority TEXT NOT NULL DEFAULT 'P2',
      affected_service TEXT,
      requester_name TEXT NOT NULL DEFAULT 'user',
      requester_slack_id TEXT,
      requester_telegram_id TEXT,
      requester_team TEXT,
      status TEXT NOT NULL DEFAULT 'submitted',
      phase TEXT NOT NULL DEFAULT 'MVP',
      source TEXT NOT NULL DEFAULT 'api',
      thread_ts TEXT,
      slack_channel_id TEXT,
      initial_approver_slack_id TEXT,
      initial_approved_at TEXT,
      initial_rejection_reason TEXT,
      plan_approver_slack_id TEXT,
      plan_approved_at TEXT,
      plan_rejection_reason TEXT,
      pr_merger_slack_id TEXT,
      pr_merged_at TEXT,
      qa_validator_slack_id TEXT,
      qa_validated_at TEXT,
      qa_failure_reason TEXT,
      prod_approver_slack_id TEXT,
      prod_approved_at TEXT,
      implementation_plan TEXT,
      risk_notes TEXT,
      rollback_plan TEXT,
      feature_branch TEXT,
      base_branch TEXT DEFAULT 'main',
      pr_number INTEGER,
      pr_url TEXT,
      merged_sha TEXT,
      staging_url TEXT,
      production_url TEXT,
      deploy_timestamp TEXT,
      release_version TEXT,
      sla_breach_alert_sent INTEGER DEFAULT 0,
      sla_deadline TEXT,
      created_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now')),
      completed_at TEXT
    );

    CREATE TABLE IF NOT EXISTS audit_log (
      id TEXT PRIMARY KEY,
      request_id TEXT NOT NULL,
      actor_type TEXT NOT NULL,
      actor_id TEXT NOT NULL,
      action TEXT NOT NULL,
      details TEXT DEFAULT '{}',
      metadata TEXT DEFAULT '{}',
      created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY,
      slack_id TEXT UNIQUE,
      telegram_id TEXT UNIQUE,
      email TEXT UNIQUE,
      name TEXT NOT NULL,
      team TEXT,
      role TEXT NOT NULL DEFAULT 'requester',
      is_active INTEGER DEFAULT 1,
      created_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS services (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL UNIQUE,
      repo_url TEXT NOT NULL,
      default_branch TEXT DEFAULT 'main',
      team_owner TEXT,
      tech_stack TEXT,
      ci_workflow_path TEXT,
      staging_env TEXT,
      production_env TEXT,
      is_active INTEGER DEFAULT 1,
      created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS ai_prompt_log (
      id TEXT PRIMARY KEY,
      request_id TEXT NOT NULL,
      agent_name TEXT NOT NULL,
      model TEXT NOT NULL,
      prompt_hash TEXT NOT NULL,
      prompt_preview TEXT,
      response_hash TEXT,
      response_preview TEXT,
      tokens_input INTEGER DEFAULT 0,
      tokens_output INTEGER DEFAULT 0,
      latency_ms INTEGER DEFAULT 0,
      success INTEGER DEFAULT 1,
      error_message TEXT,
      created_at TEXT DEFAULT (datetime('now'))
    );
  `);

  // Seed default service if empty
  const result = db!.exec('SELECT COUNT(*) as cnt FROM services');
  const count = result.length > 0 ? result[0].values[0][0] : 0;
  if (count === 0) {
    db!.run(
      `INSERT OR IGNORE INTO services (id, name, repo_url, team_owner, tech_stack) VALUES (?, ?, ?, ?, ?)`,
      [uuidv4(), 'demo-api', 'https://github.com/plotcode/demo-api', 'Platform Team', 'python,fastapi']
    );
  }
}

function rowsToObjects(result: any[]): any[] {
  if (!result || result.length === 0) return [];
  const columns = result[0].columns;
  return result[0].values.map((row: any[]) => {
    const obj: any = {};
    columns.forEach((col: string, i: number) => { obj[col] = row[i]; });
    return obj;
  });
}

// ==========================================
// Request CRUD
// ==========================================

export async function createRequest(req: Partial<FeatureRequest>): Promise<FeatureRequest> {
  const d = await getDb();
  const id = uuidv4();
  const requestId = req.request_id || `REQ-${new Date().getFullYear()}-${String(Math.floor(Math.random() * 10000)).padStart(4, '0')}`;
  const now = new Date().toISOString();

  const fullReq: FeatureRequest = {
    id,
    request_id: requestId,
    title: req.title || 'Untitled',
    business_need: req.business_need || '',
    expected_behavior: req.expected_behavior || '',
    priority: req.priority || 'P2',
    affected_service: req.affected_service,
    requester_name: req.requester_name || 'user',
    requester_slack_id: req.requester_slack_id,
    requester_telegram_id: req.requester_telegram_id,
    requester_team: req.requester_team,
    status: req.status || 'submitted',
    phase: req.phase || 'MVP',
    source: req.source || 'api',
    thread_ts: req.thread_ts,
    slack_channel_id: req.slack_channel_id,
    created_at: now,
    updated_at: now,
  };

  const cols = Object.keys(fullReq).filter(k => fullReq[k as keyof FeatureRequest] !== undefined);
  const placeholders = cols.map(() => '?').join(', ');
  const values = cols.map(k => fullReq[k as keyof FeatureRequest]);

  d.run(`INSERT INTO requests (${cols.join(', ')}) VALUES (${placeholders})`, values);
  saveDb();
  return getRequest(requestId) as Promise<FeatureRequest>;
}

export async function getRequest(requestId: string): Promise<FeatureRequest | null> {
  const d = await getDb();
  const result = d.exec('SELECT * FROM requests WHERE request_id = ?', [requestId]);
  const rows = rowsToObjects(result);
  return rows[0] || null;
}

export async function updateRequest(requestId: string, updates: Partial<FeatureRequest>): Promise<FeatureRequest> {
  const d = await getDb();
  const now = new Date().toISOString();
  (updates as any).updated_at = now;

  const setClauses = Object.keys(updates).map(k => `${k} = ?`);
  const values = Object.values(updates);

  d.run(`UPDATE requests SET ${setClauses.join(', ')} WHERE request_id = ?`, [...values, requestId]);
  saveDb();
  return getRequest(requestId) as Promise<FeatureRequest>;
}

export async function listRequests(status?: string): Promise<FeatureRequest[]> {
  const d = await getDb();
  let result;
  if (status) {
    result = d.exec('SELECT * FROM requests WHERE status = ? ORDER BY created_at DESC', [status]);
  } else {
    result = d.exec('SELECT * FROM requests ORDER BY created_at DESC');
  }
  return rowsToObjects(result);
}

// ==========================================
// Audit Log
// ==========================================

export async function logAudit(entry: Partial<AuditLogEntry>): Promise<void> {
  const d = await getDb();
  const id = uuidv4();
  d.run(
    `INSERT INTO audit_log (id, request_id, actor_type, actor_id, action, details, metadata)
     VALUES (?, ?, ?, ?, ?, ?, ?)`,
    [id, entry.request_id, entry.actor_type, entry.actor_id, entry.action,
     JSON.stringify(entry.details || {}), JSON.stringify(entry.metadata || {})]
  );
  saveDb();
}

export async function getAuditLog(requestId: string): Promise<AuditLogEntry[]> {
  const d = await getDb();
  const result = d.exec('SELECT * FROM audit_log WHERE request_id = ? ORDER BY created_at ASC', [requestId]);
  return rowsToObjects(result);
}

// ==========================================
// Users & RBAC
// ==========================================

export async function getUserBySlack(slackId: string): Promise<User | null> {
  const d = await getDb();
  const result = d.exec('SELECT * FROM users WHERE slack_id = ?', [slackId]);
  const rows = rowsToObjects(result);
  return rows[0] || null;
}

export async function createUser(user: Partial<User>): Promise<User> {
  const d = await getDb();
  const id = uuidv4();
  const now = new Date().toISOString();
  d.run(
    `INSERT INTO users (id, slack_id, telegram_id, email, name, team, role, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [id, user.slack_id || null, user.telegram_id || null, user.email || null, user.name, user.team || null, user.role || 'requester', now, now]
  );
  saveDb();
  const result = d.exec('SELECT * FROM users WHERE id = ?', [id]);
  return rowsToObjects(result)[0];
}

export async function hasRole(slackId: string, requiredRoles: string[]): Promise<boolean> {
  const user = await getUserBySlack(slackId);
  if (!user) return false;
  return requiredRoles.includes(user.role);
}

// ==========================================
// Service Registry
// ==========================================

export async function getService(name: string): Promise<Service | null> {
  const d = await getDb();
  const result = d.exec('SELECT * FROM services WHERE name = ?', [name]);
  const rows = rowsToObjects(result);
  return rows[0] || null;
}

export async function listServices(): Promise<Service[]> {
  const d = await getDb();
  const result = d.exec('SELECT * FROM services WHERE is_active = 1');
  return rowsToObjects(result);
}
