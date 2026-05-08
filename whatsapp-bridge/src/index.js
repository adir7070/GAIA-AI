/**
 * Gaia WhatsApp Bridge
 * --------------------
 * Express HTTP service that wraps whatsapp-web.js. One Client per user.
 *
 * Endpoints:
 *   POST   /sessions                       { user_id }
 *   GET    /sessions/:userId/qr            -> { qr_base64, status }
 *   GET    /sessions/:userId/status        -> { status }
 *   POST   /sessions/:userId/send          { to, text }
 *   GET    /sessions/:userId/history       ?contact_id=&limit=
 *   DELETE /sessions/:userId
 *
 * Outgoing webhook (to backend):
 *   POST {BACKEND_INTERNAL_URL}/whatsapp/internal/event
 *   Header: X-Bridge-Signature: HMAC-SHA256(BRIDGE_SECRET, body)
 */

require('dotenv').config();
const express = require('express');
const sessions = require('./session');
const { register } = require('./routes');

const app = express();
app.use(express.json({ limit: '2mb' }));

app.get('/healthz', (_req, res) => res.json({ status: 'ok' }));

register(app, sessions);

const port = process.env.BRIDGE_PORT || 4000;
app.listen(port, () => {
  console.log(`[bridge] listening on :${port}`);
});

process.on('SIGTERM', () => {
  console.log('[bridge] SIGTERM, shutting down');
  sessions.shutdown().then(() => process.exit(0));
});
