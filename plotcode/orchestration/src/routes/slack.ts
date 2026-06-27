import { Router, Request, Response } from 'express';
import { v4 as uuidv4 } from 'uuid';
import { createRequest, updateRequest, getRequest, logAudit, getUserBySlack, createUser } from '../services/database';
import { postMessage, sendDM, openModal, buildApprovalBlocks, postThreadReply, buildStatusUpdateBlocks } from '../services/slack';
import { slackAuthMiddleware, AuthenticatedRequest, requireApprover, requireReviewer, requireProdOwner } from '../middleware/rbac';
import logger from '../services/logger';
import { WorkflowEngine } from '../workflows/engine';

const router = Router();
const engine = new WorkflowEngine();

// ==========================================
// Slack Slash Command: /request
// Opens the feature request modal
// ==========================================
router.post('/command', slackAuthMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  const { trigger_id, user_id, channel_id } = req.body;

  // Ensure user exists in DB
  let user = await getUserBySlack(user_id);
  if (!user) {
    user = await createUser({
      slack_id: user_id,
      name: req.body.user_name || 'Unknown',
      role: 'requester'
    });
  }

  const modalView = {
    type: 'modal',
    callback_id: 'feature_request_modal',
    title: { type: 'plain_text', text: 'Feature Request' },
    submit: { type: 'plain_text', text: 'Submit' },
    close: { type: 'plain_text', text: 'Cancel' },
    blocks: [
      {
        type: 'input',
        block_id: 'business_need_block',
        element: { type: 'plain_text_input', action_id: 'business_need', multiline: true, placeholder: { type: 'plain_text', text: 'What is the business need?' } },
        label: { type: 'plain_text', text: 'Business Need' }
      },
      {
        type: 'input',
        block_id: 'expected_behavior_block',
        element: { type: 'plain_text_input', action_id: 'expected_behavior', multiline: true, placeholder: { type: 'plain_text', text: 'What is the expected behavior?' } },
        label: { type: 'plain_text', text: 'Expected Behavior' }
      },
      {
        type: 'input',
        block_id: 'priority_block',
        element: {
          type: 'static_select',
          action_id: 'priority',
          options: [
            { text: { type: 'plain_text', text: 'P0 — Critical' }, value: 'P0' },
            { text: { type: 'plain_text', text: 'P1 — High' }, value: 'P1' },
            { text: { type: 'plain_text', text: 'P2 — Medium' }, value: 'P2' },
            { text: { type: 'plain_text', text: 'P3 — Low' }, value: 'P3' }
          ]
        },
        label: { type: 'plain_text', text: 'Priority' }
      },
      {
        type: 'input',
        block_id: 'service_block',
        element: { type: 'plain_text_input', action_id: 'service', placeholder: { type: 'plain_text', text: 'e.g. demo-api' } },
        label: { type: 'plain_text', text: 'Affected Service' },
        optional: true
      },
      {
        type: 'input',
        block_id: 'team_block',
        element: { type: 'plain_text_input', action_id: 'team', placeholder: { type: 'plain_text', text: 'Your team' } },
        label: { type: 'plain_text', text: 'Team' },
        optional: true
      }
    ],
    private_metadata: JSON.stringify({ channel_id, user_id })
  };

  await openModal(trigger_id, modalView);
  res.status(200).send('');
});

// ==========================================
// Modal Submission Handler
// ==========================================
router.post('/interaction', slackAuthMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  const payload = JSON.parse(req.body.payload || '{}');

  if (payload.type === 'view_submission' && payload.view?.callback_id === 'feature_request_modal') {
    const state = payload.view.state.values;
    const meta = JSON.parse(payload.view.private_metadata || '{}');

    const businessNeed = state.business_need_block?.business_need?.value || '';
    const expectedBehavior = state.expected_behavior_block?.expected_behavior?.value || '';
    const priority = state.priority_block?.priority?.selected_option?.value || 'P2';
    const service = state.service_block?.service?.value || '';
    const team = state.team_block?.team?.value || '';

    // Generate request ID
    const year = new Date().getFullYear();
    const seq = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
    const requestId = `REQ-${year}-${seq}`;

    const request = await createRequest({
      request_id: requestId,
      title: `${businessNeed.substring(0, 60)}...`,
      business_need: businessNeed,
      expected_behavior: expectedBehavior,
      priority: priority as any,
      affected_service: service,
      requester_name: payload.user?.name || 'Unknown',
      requester_slack_id: payload.user?.id,
      requester_team: team,
      status: 'submitted',
      phase: 'MVP',
      source: 'slack'
    });

    await logAudit({
      request_id: requestId,
      actor_type: 'human',
      actor_id: payload.user?.id,
      action: 'request_submitted',
      details: { business_need: businessNeed, priority, service }
    });

    // Post to channel
    const blocks = buildStatusUpdateBlocks(
      requestId,
      'Submitted',
      `*Priority:* ${priority}\n*Service:* ${service || 'N/A'}\n*Requester:* ${request.requester_name}\n\nWaiting for initial human approval.`
    );
    await postMessage(meta.channel_id, `New feature request: ${requestId}`, blocks);

    // Send to approvers
    await sendApprovalRequest(requestId, 'initial', 'approver');

    res.status(200).send('');
    return;
  }

  // Handle button actions (approvals)
  if (payload.type === 'block_actions') {
    const action = payload.actions?.[0];
    if (!action) {
      res.status(200).send('');
      return;
    }

    const actionId = action.action_id;
    const value = JSON.parse(action.value || '{}');
    const { request_id, gate } = value;
    const userId = payload.user?.id;

    if (!request_id || !gate) {
      res.status(200).send('');
      return;
    }

    const req = await getRequest(request_id);
    if (!req) {
      res.status(200).send('');
      return;
    }

    // Handle approval
    if (actionId.startsWith('approve_')) {
      await handleApproval(request_id, gate, userId, 'approved');
      res.status(200).send('');
      return;
    }

    // Handle rejection
    if (actionId.startsWith('reject_')) {
      // Open a modal to collect rejection reason
      await handleApproval(request_id, gate, userId, 'rejected', 'Rejected via button');
      res.status(200).send('');
      return;
    }

    // Handle request changes
    if (actionId.startsWith('changes_')) {
      await handleApproval(request_id, gate, userId, 'changes_requested', 'Changes requested');
      res.status(200).send('');
      return;
    }
  }

  res.status(200).send('');
});

// ==========================================
// Event Subscriptions (e.g. app mentions)
// ==========================================
router.post('/events', async (req: Request, res: Response) => {
  // Slack challenge verification
  if (req.body.challenge) {
    res.status(200).json({ challenge: req.body.challenge });
    return;
  }

  const event = req.body.event;
  if (event?.type === 'app_mention') {
    // Handle app mention if needed
    logger.info('App mention received', { event });
  }

  res.status(200).send('');
});

// ==========================================
// Helper: Send approval request to right people
// ==========================================
async function sendApprovalRequest(requestId: string, gate: string, requiredRole: string): Promise<void> {
  const req = await getRequest(requestId);
  if (!req) return;

  const blocks = buildApprovalBlocks(
    `⏳ Approval Required: ${gate}`,
    `Request *${requestId}* needs your approval to proceed to the next stage.\n\n*Business Need:* ${req.business_need.substring(0, 200)}...`,
    requestId,
    gate,
    { Priority: req.priority, Service: req.affected_service || 'N/A', Requester: req.requester_name }
  );

  // In production, look up all users with the required role and DM them
  // For MVP, DM the configured admin/prod owner IDs
  const adminIds = (process.env.ADMIN_SLACK_IDS || '').split(',').filter(Boolean);
  const prodOwnerIds = (process.env.PROD_OWNER_SLACK_IDS || '').split(',').filter(Boolean);
  const targets = gate === 'prod' ? [...new Set([...adminIds, ...prodOwnerIds])] : adminIds;

  for (const userId of targets) {
    await sendDM(userId, `Approval request for ${requestId}`, blocks);
  }
}

// ==========================================
// Handle approval action
// ==========================================
async function handleApproval(requestId: string, gate: string, approverId: string, decision: string, reason?: string): Promise<void> {
  const req = await getRequest(requestId);
  if (!req) return;

  const now = new Date().toISOString();
  const updates: any = {};

  if (gate === 'initial') {
    if (decision === 'approved') {
      updates.status = 'approved';
      updates.initial_approver_slack_id = approverId;
      updates.initial_approved_at = now;
    } else {
      updates.status = 'rejected';
      updates.initial_rejection_reason = reason || 'No reason provided';
    }
  } else if (gate === 'plan') {
    if (decision === 'approved') {
      updates.status = 'plan_approved';
      updates.plan_approver_slack_id = approverId;
      updates.plan_approved_at = now;
    } else {
      updates.status = 'plan_pending_approval'; // stay pending, maybe add a changes requested state
      updates.plan_rejection_reason = reason || 'No reason provided';
    }
  } else if (gate === 'pr') {
    if (decision === 'approved') {
      updates.status = 'pr_approved';
      updates.pr_merger_slack_id = approverId;
      updates.pr_merged_at = now;
    }
  } else if (gate === 'qa') {
    if (decision === 'approved') {
      updates.status = 'qa_passed';
      updates.qa_validator_slack_id = approverId;
      updates.qa_validated_at = now;
    } else {
      updates.status = 'qa_failed';
      updates.qa_failure_reason = reason || 'QA validation failed';
    }
  } else if (gate === 'prod') {
    if (decision === 'approved') {
      updates.status = 'prod_approved';
      updates.prod_approver_slack_id = approverId;
      updates.prod_approved_at = now;
    }
  }

  await updateRequest(requestId, updates);

  await logAudit({
    request_id: requestId,
    actor_type: 'human',
    actor_id: approverId,
    action: `${gate}_${decision}`,
    details: { reason, gate }
  });

  // Notify requester
  if (req.requester_slack_id) {
    const msg = decision === 'approved'
      ? `✅ Your request *${requestId}* has been **approved** for *${gate}*.`
      : `❌ Your request *${requestId}* was **rejected** at *${gate}*.\nReason: ${reason || 'No reason provided'}`;
    await sendDM(req.requester_slack_id, msg);
  }

  // Trigger workflow engine to advance the pipeline
  await engine.advance(requestId);
}

export default router;
