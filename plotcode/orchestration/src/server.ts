import express, { Application, Request, Response } from 'express';
import slackRoutes from './routes/slack';
import telegramRoutes from './routes/telegram';
import webhookRoutes from './routes/webhooks';
import logger from './services/logger';

export function createApp(): Application {
  const app = express();

  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));

  // Health check
  app.get('/health', (_req: Request, res: Response) => {
    res.json({ status: 'ok', service: 'plotcode-orchestration', timestamp: new Date().toISOString() });
  });

  // Routes
  app.use('/slack', slackRoutes);
  app.use('/telegram', telegramRoutes);
  app.use('/webhooks', webhookRoutes);

  // 404 handler
  app.use((_req: Request, res: Response) => {
    res.status(404).json({ error: 'Not found' });
  });

  // Error handler
  app.use((err: any, _req: Request, res: Response, _next: any) => {
    logger.error('Unhandled error', { err });
    res.status(500).json({ error: 'Internal server error' });
  });

  return app;
}
