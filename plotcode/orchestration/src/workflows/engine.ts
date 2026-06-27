import { getRequest, updateRequest, logAudit, getService, getUserBySlack } from '../services/database';
import { sendDM, postMessage, buildApprovalBlocks, buildStatusUpdateBlocks } from '../services/slack';
import { createBranch, getDefaultBranchSha, createPR, triggerWorkflow } from '../services/github';
import logger from '../services/logger';
import { FeatureRequest } from '../types';

// ==========================================
// Workflow Engine
// Central state machine that advances requests
// through the 14-stage pipeline.
// ==========================================

export class WorkflowEngine {

  async advance(requestId: string): Promise<void> {
    const req = await getRequest(requestId);
    if (!req) {
      logger.error('WorkflowEngine: request not found', { requestId });
      return;
    }

    logger.info('WorkflowEngine: advancing', { requestId, status: req.status });

    switch (req.status) {
      case 'submitted':
        // Wait for human approval (HITL Gate 1)
        await this.notifyPendingApproval(req, 'initial');
        break;

      case 'approved':
        // Request approved — trigger AI analysis
        await this.triggerAnalysis(req);
        break;

      case 'planning':
        // AI is analyzing — will be updated by analysis agent webhook
        break;

      case 'plan_pending_approval':
        // Wait for human plan approval (HITL Gate 2)
        await this.notifyPendingApproval(req, 'plan');
        break;

      case 'plan_approved':
        // Plan approved — trigger code generation
        await this.triggerCoding(req);
        break;

      case 'coding':
        // AI is coding — will be updated by coder agent webhook
        break;

      case 'ci_running':
        // CI is running — will be updated by CI webhook
        break;

      case 'ci_failed':
        // CI failed — trigger self-healing loop
        await this.triggerSelfHeal(req);
        break;

      case 'ci_passed':
        // CI passed — create PR
        await this.triggerPRCreation(req);
        break;

      case 'pr_open':
        // PR is open — wait for human review (HITL Gate 3)
        await this.notifyPendingApproval(req, 'pr');
        break;

      case 'pr_approved':
        // PR approved — merge and deploy to QA
        await this.mergeAndDeployQA(req);
        break;

      case 'pr_merged':
        // PR merged — deploy to QA
        await this.deployQA(req);
        break;

      case 'qa_deployed':
        // Deployed to QA — wait for human validation (HITL Gate 4)
        await this.notifyPendingApproval(req, 'qa');
        break;

      case 'qa_passed':
        // QA passed — wait for production approval (HITL Gate 5)
        await this.notifyPendingApproval(req, 'prod');
        break;

      case 'prod_approved':
        // Production approved — deploy to production
        await this.deployProduction(req);
        break;

      case 'deployed':
        // Production deployed — start monitoring
        await this.triggerMonitoring(req);
        break;

      case 'monitoring':
        // Monitoring complete — close ticket
        await this.closeTicket(req);
        break;

      case 'closed':
        // Done
        logger.info('WorkflowEngine: request completed', { requestId });
        break;

      case 'rejected':
      case 'cancelled':
        // Terminal state
        logger.info('WorkflowEngine: request terminated', { requestId, status: req.status });
        break;

      default:
        logger.warn('WorkflowEngine: unhandled status', { requestId, status: req.status });
    }
  }

  // ==========================================
  // Stage Actions
  // ==========================================

  private async notifyPendingApproval(req: FeatureRequest, gate: string): Promise<void> {
    const title = gate === 'initial' ? 'Initial Request Approval' :
                  gate === 'plan' ? 'Implementation Plan Approval' :
                  gate === 'pr' ? 'Pull Request Review' :
                  gate === 'qa' ? 'QA Validation' :
                  gate === 'prod' ? 'Production Deploy Approval' : 'Approval Required';

    const blocks = buildApprovalBlocks(
      `⏳ ${title}`,
      `Request *${req.request_id}* is waiting for your approval.\n\n*Business Need:* ${req.business_need?.substring(0, 200)}...`,
      req.request_id,
      gate,
      { Priority: req.priority, Service: req.affected_service || 'N/A', Status: req.status }
    );

    // Send to all approvers
    const adminIds = (process.env.ADMIN_SLACK_IDS || '').split(',').filter(Boolean);
    const prodOwnerIds = (process.env.PROD_OWNER_SLACK_IDS || '').split(',').filter(Boolean);
    const targets = gate === 'prod' ? [...new Set([...adminIds, ...prodOwnerIds])] : adminIds;

    for (const userId of targets) {
      await sendDM(userId, `Approval required: ${req.request_id}`, blocks);
    }

    await logAudit({
      request_id: req.request_id,
      actor_type: 'system',
      actor_id: 'workflow_engine',
      action: 'approval_requested',
      details: { gate, targets }
    });
  }

  private async triggerAnalysis(req: FeatureRequest): Promise<void> {
    await updateRequest(req.request_id, { status: 'planning' });

    // In production: enqueue a message to the Python agent worker
    // For MVP: simulate by calling the agent HTTP endpoint or using a queue
    logger.info('WorkflowEngine: triggering analysis', { requestId: req.request_id });

    await logAudit({
      request_id: req.request_id,
      actor_type: 'system',
      actor_id: 'workflow_engine',
      action: 'trigger_analysis',
      details: { service: req.affected_service }
    });

    // Notify requester
    if (req.requester_slack_id) {
      await sendDM(req.requester_slack_id, `🔍 AI analysis starting for your request *${req.request_id}*. I'll let you know when the implementation plan is ready for review.`);
    }
  }

  private async triggerCoding(req: FeatureRequest): Promise<void> {
    await updateRequest(req.request_id, { status: 'coding' });

    logger.info('WorkflowEngine: triggering code generation', { requestId: req.request_id });

    await logAudit({
      request_id: req.request_id,
      actor_type: 'system',
      actor_id: 'workflow_engine',
      action: 'trigger_coding',
      details: { branch: req.feature_branch }
    });

    if (req.requester_slack_id) {
      await sendDM(req.requester_slack_id, `🤖 Writing code for *${req.request_id}* based on the approved plan. I'll run tests and let you know when the PR is ready.`);
    }
  }

  private async triggerSelfHeal(req: FeatureRequest): Promise<void> {
    logger.info('WorkflowEngine: triggering self-heal', { requestId: req.request_id });

    // This would trigger the Validation & Remediation Agent to read CI logs,
    // diagnose the issue, and push a fix. Then re-trigger CI.
    await logAudit({
      request_id: req.request_id,
      actor_type: 'ai',
      actor_id: 'validation_agent',
      action: 'self_heal_triggered',
      details: {}
    });

    if (req.requester_slack_id) {
      await sendDM(req.requester_slack_id, `⚠️ CI failed for *${req.request_id}*. The AI is investigating and will attempt to fix the issue automatically. I'll keep you updated.`);
    }
  }

  private async triggerPRCreation(req: FeatureRequest): Promise<void> {
    await updateRequest(req.request_id, { status: 'pr_open' });

    logger.info('WorkflowEngine: triggering PR creation', { requestId: req.request_id });

    await logAudit({
      request_id: req.request_id,
      actor_type: 'ai',
      actor_id: 'pr_agent',
      action: 'pr_creation_triggered',
      details: {}
    });

    if (req.requester_slack_id) {
      await sendDM(req.requester_slack_id, `📬 PR opened for *${req.request_id}*. It's now ready for human code review.`);
    }
  }

  private async mergeAndDeployQA(req: FeatureRequest): Promise<void> {
    logger.info('WorkflowEngine: merging PR and deploying to QA', { requestId: req.request_id });

    // In production: merge PR via GitHub API, then trigger QA deployment
    await logAudit({
      request_id: req.request_id,
      actor_type: 'system',
      actor_id: 'workflow_engine',
      action: 'merge_qa_deploy_triggered',
      details: { pr_number: req.pr_number }
    });

    if (req.requester_slack_id) {
      await sendDM(req.requester_slack_id, `🚀 *${req.request_id}* has been merged and is deploying to QA/staging. You'll be notified when it's ready for validation.`);
    }
  }

  private async deployQA(req: FeatureRequest): Promise<void> {
    logger.info('WorkflowEngine: deploying to QA', { requestId: req.request_id });
    // Trigger QA deployment workflow
  }

  private async deployProduction(req: FeatureRequest): Promise<void> {
    await updateRequest(req.request_id, { status: 'deploying' });

    logger.info('WorkflowEngine: deploying to production', { requestId: req.request_id });

    await logAudit({
      request_id: req.request_id,
      actor_type: 'system',
      actor_id: 'workflow_engine',
      action: 'production_deploy_triggered',
      details: {}
    });

    if (req.requester_slack_id) {
      await sendDM(req.requester_slack_id, `🎉 *${req.request_id}* is being deployed to production! You'll get the final confirmation shortly.`);
    }
  }

  private async triggerMonitoring(req: FeatureRequest): Promise<void> {
    await updateRequest(req.request_id, { status: 'monitoring' });

    logger.info('WorkflowEngine: triggering monitoring', { requestId: req.request_id });

    await logAudit({
      request_id: req.request_id,
      actor_type: 'system',
      actor_id: 'monitoring_agent',
      action: 'monitoring_triggered',
      details: {}
    });

    if (req.requester_slack_id) {
      await sendDM(req.requester_slack_id, `✅ *${req.request_id}* is now live in production! Monitoring for 24 hours. You'll receive a final summary once the observation period is complete.`);
    }
  }

  private async closeTicket(req: FeatureRequest): Promise<void> {
    const now = new Date().toISOString();
    await updateRequest(req.request_id, {
      status: 'closed',
      completed_at: now
    });

    logger.info('WorkflowEngine: request closed', { requestId: req.request_id });

    await logAudit({
      request_id: req.request_id,
      actor_type: 'system',
      actor_id: 'workflow_engine',
      action: 'request_closed',
      details: { completed_at: now }
    });

    if (req.requester_slack_id) {
      await sendDM(req.requester_slack_id,
        `🎊 *${req.request_id}* has been successfully completed and closed!\n\n` +
        `• PR: ${req.pr_url || 'N/A'}\n` +
        `• Merged SHA: ${req.merged_sha || 'N/A'}\n` +
        `• Production URL: ${req.production_url || 'N/A'}\n` +
        `• Release: ${req.release_version || 'N/A'}\n\n` +
        `Thank you for using Plotcode!`
      );
    }
  }
}
