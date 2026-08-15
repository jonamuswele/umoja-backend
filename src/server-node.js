import { serve } from '@hono/node-server';
import app from './index.js';
import { getDb } from './db.js';

// Initialize DB schema
getDb();

const PORT = Number(process.env.PORT) || 8000;

console.log(`🚀 Umoja Terra Hono JS Server running on http://localhost:${PORT}`);

serve({
  fetch: app.fetch,
  port: PORT
});
