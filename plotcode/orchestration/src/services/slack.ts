import { WebClient } from '@slack/web-api';
import logger from './logger';

const token = process.env.SLACK_BOT_TOKEN;
if (!token) {
  logger.warn('SLACK_BOT_TOKEN not set — Slack integration disabled');
}

const slack = token ? new WebClient(token) : null;

export async function postMessage(channel: string, text: string, blocks?: any[]): Promise<void> {
  if (!slack) {
    logger.warn('Slack not configured, would send:', { channel, text });
    return;
  }
  try {
    await slack.chat.postMessage({ channel, text, blocks });
  } catch (err) {
    logger.error('Slack postMessage failed', { err, channel });
  }
}

export async function postThreadReply(channel: string, threadTs: string, text: string, blocks?: any[]): Promise<void> {
  if (!slack) {
    logger.warn('Slack not configured, would thread reply:', { channel, threadTs, text });
    return;
  }
  try {
    await slack.chat.postMessage({ channel, thread_ts: threadTs, text, blocks });
  } catch (err) {
    logger.error('Slack thread reply failed', { err, channel });
  }
}

export async function sendDM(userId: string, text: string, blocks?: any[]): Promise<void> {
  if (!slack) {
    logger.warn('Slack not configured, would DM:', { userId, text });
    return;
  }
  try {
    // Open a conversation if needed
    const conv = await slack.conversations.open({ users: userId });
    if (conv.channel?.id) {
      await slack.chat.postMessage({ channel: conv.channel.id, text, blocks });
    }
  } catch (err) {
    logger.error('Slack DM failed', { err, userId });
  }
}

export async function openModal(triggerId: string, view: any): Promise<void> {
  if (!slack) {
    logger.warn('Slack not configured, would open modal');
    return;
  }
  try {
    await slack.views.open({ trigger_id: triggerId, view });
  } catch (err) {
    logger.error('Slack openModal failed', { err });
  }
}

export async function updateMessage(channel: string, ts: string, text: string, blocks?: any[]): Promise<void> {
  if (!slack) return;
  try {
    await slack.chat.update({ channel, ts, text, blocks });
  } catch (err) {
    logger.error('Slack updateMessage failed', { err, channel });
  }
}

export async function deleteMessage(channel: string, ts: string): Promise<void> {
  if (!slack) return;
  try {
    await slack.chat.delete({ channel, ts });
  } catch (err) {
    logger.error('Slack deleteMessage failed', { err, channel });
  }
}

// ==========================================
// Approval Message Builders
// ==========================================

export function buildApprovalBlocks(
  title: string,
  description: string,
  requestId: string,
  gateName: string,
  metadata?: Record<string, string>
): any[] {
  const fields = Object.entries(metadata || {}).map(([key, val]) => ({
    type: 'mrkdwn',
    text: `*${key}:*\n${val}`
  }));

  return [
    { type: 'header', text: { type: 'plain_text', text: title } },
    { type: 'section', text: { type: 'mrkdwn', text: description } },
    ...(fields.length > 0 ? [{ type: 'section', fields }] : []),
    { type: 'divider' },
    {
      type: 'actions',
      elements: [
        {
          type: 'button',
          text: { type: 'plain_text', text: '✅ Approve' },
          style: 'primary',
          action_id: `approve_${gateName}`,
          value: JSON.stringify({ request_id: requestId, gate: gateName })
        },
        {
          type: 'button',
          text: { type: 'plain_text', text: '❌ Reject' },
          style: 'danger',
          action_id: `reject_${gateName}`,
          value: JSON.stringify({ request_id: requestId, gate: gateName })
        },
        {
          type: 'button',
          text: { type: 'plain_text', text: '💬 Request Changes' },
          action_id: `changes_${gateName}`,
          value: JSON.stringify({ request_id: requestId, gate: gateName })
        }
      ]
    }
  ];
}

export function buildStatusUpdateBlocks(requestId: string, status: string, details: string): any[] {
  return [
    { type: 'header', text: { type: 'plain_text', text: `📋 Request ${requestId} — Status Update` } },
    { type: 'section', text: { type: 'mrkdwn', text: `*Status:* ${status}\n${details}` } }
  ];
}

export default slack;
