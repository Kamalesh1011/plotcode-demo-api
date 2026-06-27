import { Request, Response, NextFunction } from 'express';
import { getUserBySlack, hasRole } from '../services/database';
import { RoleType } from '../types';
import logger from '../services/logger';

export interface AuthenticatedRequest extends Request {
  slackUserId?: string;
  userRole?: string;
}

export async function slackAuthMiddleware(req: AuthenticatedRequest, res: Response, next: NextFunction): Promise<void> {
  // In production, verify Slack request signature here
  // For now, extract from body or headers
  const slackUserId = req.body?.user?.id || req.body?.user_id || req.body?.user?.user_id;
  if (!slackUserId) {
    res.status(401).json({ error: 'Unauthorized: Slack user ID not found' });
    return;
  }
  req.slackUserId = slackUserId;
  next();
}

export function requireRoles(...roles: RoleType[]) {
  return async (req: AuthenticatedRequest, res: Response, next: NextFunction): Promise<void> => {
    const userId = req.slackUserId;
    if (!userId) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const allowed = await hasRole(userId, roles);
    if (!allowed) {
      logger.warn('RBAC denied', { userId, requiredRoles: roles, path: req.path });
      res.status(403).json({ error: `Forbidden: requires one of [${roles.join(', ')}]` });
      return;
    }

    const user = await getUserBySlack(userId);
    if (user) req.userRole = user.role;
    next();
  };
}

export function requireAdmin() {
  return requireRoles('admin');
}

export function requireApprover() {
  return requireRoles('approver', 'admin', 'prod_owner');
}

export function requireProdOwner() {
  return requireRoles('prod_owner', 'admin');
}

export function requireReviewer() {
  return requireRoles('reviewer', 'approver', 'admin', 'prod_owner');
}
