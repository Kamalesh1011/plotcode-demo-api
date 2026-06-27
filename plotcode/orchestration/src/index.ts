import dotenv from 'dotenv';
import { createApp } from './server';
import logger from './services/logger';

dotenv.config({ path: '../.env' });

const PORT = process.env.PORT || 3000;

const app = createApp();
app.listen(PORT, () => {
  logger.info(`Plotcode orchestration server running on port ${PORT}`);
});
