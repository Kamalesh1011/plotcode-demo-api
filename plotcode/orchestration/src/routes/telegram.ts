import { Router, Request, Response } from 'express';
import { v4 as uuidv4 } from 'uuid';
import { createRequest, updateRequest, getRequest, logAudit } from '../services/database';
import { postMessage, buildStatusUpdateBlocks } from '../services/slack';
import logger from '../services/logger';

const router = Router();

// Telegram webhook handler
router.post('/webhook', async (req: Request, res: Response) => {
  const update = req.body;

  if (!update.message || !update.message.text) {
    res.status(200).send('ok');
    return;
  }

  const text = update.message.text;
  const chatId = update.message.chat.id;
  const user = update.message.from;

  // Handle /request command
  if (text.startsWith('/request')) {
    const parts = text.split('\n');
    const header = parts[0].replace('/request', '').trim();

    // Simple parsing: /request <title>
    // Then business need, expected behavior, priority in subsequent lines
    // For MVP, we'll do a simple structured format
    const year = new Date().getFullYear();
    const seq = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
    const requestId = `REQ-${year}-${seq}`;

    const title = header || 'Untitled Request';
    const businessNeed = parts[1] || title;
    const expectedBehavior = parts[2] || 'To be defined';
    const priority = 'P2'; // Default

    const request = await createRequest({
      request_id: requestId,
      title,
      business_need: businessNeed,
      expected_behavior: expectedBehavior,
      priority: priority as any,
      requester_name: user.first_name || 'Telegram User',
      requester_telegram_id: String(user.id),
      status: 'submitted',
      phase: 'MVP',
      source: 'telegram'
    });

    await logAudit({
      request_id: requestId,
      actor_type: 'human',
      actor_id: String(user.id),
      action: 'request_submitted',
      details: { source: 'telegram', title }
    });

    res.status(200).json({
      method: 'sendMessage',
      chat_id: chatId,
      text: `✅ Request received!\nID: ${requestId}\nStatus: Submitted\nTitle: ${title}\n\nAwaiting human approval...`
    });
    return;
  }

  // Handle /status <request_id>
  if (text.startsWith('/status')) {
    const requestId = text.split(' ')[1];
    if (!requestId) {
      res.status(200).json({ method: 'sendMessage', chat_id: chatId, text: 'Usage: /status REQ-2025-0042' });
      return;
    }

    const req = await getRequest(requestId);
    if (!req) {
      res.status(200).json({ method: 'sendMessage', chat_id: chatId, text: `Request ${requestId} not found.` });
      return;
    }

    res.status(200).json({
      method: 'sendMessage',
      chat_id: chatId,
      text: `📋 *${requestId}*\nStatus: ${req.status}\nPriority: ${req.priority}\nService: ${req.affected_service || 'N/A'}\nUpdated: ${req.updated_at}`
    });
    return;
  }

  res.status(200).send('ok');
});

export default router;
