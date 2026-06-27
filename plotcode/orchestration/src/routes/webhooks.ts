import { Router, Request, Response } from 'express';
import { updateRequest, getRequest, logAudit } from '../services/database';
import { sendDM, postThreadReply } from '../services/slack';
import logger from '../services/logger';
import { WorkflowEngine } from '../workflows/engine';

const router = Router();
const engine = new WorkflowEngine();

// ==========================================
// CI/CD Webhook Handler
// ==========================================
router.post('/ci', async (req: Request, res: Response) => {
  const event = req.body;
  const signature = req.headers['x-hub-signature-256'];

  // In production, verify GitHub webhook signature
  logger.info('CI webhook received', { action: event.action, repo: event.repository?.name });

  if (event.action === 'completed' && event.check_run) {
    const checkRun = event.check_run;
    const branch = checkRun.check_suite?.head_branch;
    const conclusion = checkRun.conclusion;

    // Find the request associated with this branch
    // Branch naming: feat/REQ-{ID}-{desc}
    if (branch && branch.startsWith('feat/REQ-')) {
      const match = branch.match(/feat\/(REQ-\d{4}-\d{4})/);
      if (match) {
        const requestId = match[1];
        const req = await getRequest(requestId);
        if (req) {
          if (conclusion === 'success') {
            await updateRequest(requestId, { status: 'ci_passed' });
            await logAudit({ request_id: requestId, actor_type: 'system', actor_id: 'github', action: 'ci_passed', details: { check_run: checkRun.name } });
            await engine.advance(requestId);
          } else {
            await updateRequest(requestId, { status: 'ci_failed' });
            await logAudit({ request_id: requestId, actor_type: 'system', actor_id: 'github', action: 'ci_failed', details: { check_run: checkRun.name, conclusion } });
            // Trigger self-healing loop via engine
            await engine.advance(requestId);
          }
        }
      }
    }
  }

  res.status(200).send('ok');
});

// ==========================================
// PR Webhook Handler
// ==========================================
router.post('/pr', async (req: Request, res: Response) => {
  const event = req.body;
  const action = event.action;
  const pr = event.pull_request;

  if (!pr) {
    res.status(200).send('ok');
    return;
  }

  // Extract request ID from PR title or branch
  const branch = pr.head?.ref || '';
  const title = pr.title || '';
  let requestId: string | null = null;

  const branchMatch = branch.match(/REQ-\d{4}-\d{4}/);
  const titleMatch = title.match(/REQ-\d{4}-\d{4}/);
  requestId = branchMatch ? branchMatch[0] : (titleMatch ? titleMatch[0] : null);

  if (!requestId) {
    res.status(200).send('ok');
    return;
  }

  const existing = await getRequest(requestId);
  if (!existing) {
    res.status(200).send('ok');
    return;
  }

  if (action === 'opened') {
    await updateRequest(requestId, { status: 'pr_open', pr_number: pr.number, pr_url: pr.html_url });
    await logAudit({ request_id: requestId, actor_type: 'ai', actor_id: 'pr_agent', action: 'pr_opened', details: { pr_number: pr.number, pr_url: pr.html_url } });
  } else if (action === 'closed' && pr.merged) {
    await updateRequest(requestId, { status: 'pr_merged', merged_sha: pr.merge_commit_sha });
    await logAudit({ request_id: requestId, actor_type: 'human', actor_id: pr.merged_by?.login || 'unknown', action: 'pr_merged', details: { sha: pr.merge_commit_sha } });
    await engine.advance(requestId);
  } else if (action === 'submitted' && event.review) {
    const review = event.review;
    if (review.state === 'changes_requested') {
      // Notify the AI agent to revise
      await updateRequest(requestId, { status: 'pr_reviewing' });
      await logAudit({ request_id: requestId, actor_type: 'human', actor_id: review.user?.login, action: 'pr_changes_requested', details: { body: review.body } });
      await engine.advance(requestId);
    }
  }

  res.status(200).send('ok');
});

// ==========================================
// Deployment Webhook Handler
// ==========================================
router.post('/deploy', async (req: Request, res: Response) => {
  const event = req.body;
  const { request_id, environment, status, url } = event;

  if (!request_id) {
    res.status(400).json({ error: 'request_id required' });
    return;
  }

  const deployReq = await getRequest(request_id);
  if (!deployReq) {
    res.status(404).json({ error: 'Request not found' });
    return;
  }

  if (environment === 'staging' && status === 'success') {
    await updateRequest(request_id, { status: 'qa_deployed', staging_url: url });
    await logAudit({ request_id, actor_type: 'system', actor_id: 'deploy_agent', action: 'staging_deployed', details: { url } });
    await engine.advance(request_id);
  } else if (environment === 'production' && status === 'success') {
    await updateRequest(request_id, { status: 'deployed', production_url: url, deploy_timestamp: new Date().toISOString() });
    await logAudit({ request_id, actor_type: 'system', actor_id: 'deploy_agent', action: 'production_deployed', details: { url } });
    await engine.advance(request_id);
  }

  res.status(200).send('ok');
});

export default router;
