/**
 * Session manager: one whatsapp-web.js Client per user_id.
 * Sessions persist across restarts via LocalAuth on `.wwebjs_auth/`.
 */

const fs = require('fs');
const path = require('path');
const { Client, LocalAuth } = require('whatsapp-web.js');
const QRCode = require('qrcode');
const { sendWebhook } = require('./events');

const clients = new Map(); // userId -> { client, status, qr }
const AUTH_PATH = '.wwebjs_auth';

function _exec() {
  // In docker we install chromium and point puppeteer at it.
  return process.env.PUPPETEER_EXECUTABLE_PATH || undefined;
}

/**
 * Remove stale Chromium Singleton* lock files left behind when a previous
 * Chromium process for this user did not shut down cleanly (crash/restart).
 * Without this, a fresh launch fails with "profile appears to be in use by
 * another Chromium process" (Code: 21).
 */
function clearStaleLocks(userId) {
  const dir = path.join(AUTH_PATH, `session-${String(userId)}`);
  try {
    if (!fs.existsSync(dir)) return;
    for (const name of fs.readdirSync(dir)) {
      if (name.startsWith('Singleton')) {
        try {
          fs.rmSync(path.join(dir, name), { force: true, recursive: true });
        } catch (_) {
          /* ignore */
        }
      }
    }
    console.log(`[bridge] cleared stale locks for user=${userId}`);
  } catch (err) {
    console.error(`[bridge] clearStaleLocks error for user=${userId}:`, err.message);
  }
}

async function start(userId) {
  if (clients.has(userId)) {
    return clients.get(userId);
  }
  clearStaleLocks(userId);
  const session = {
    userId,
    status: 'pending',
    qr: null,
    contacts: [],
  };
  const client = new Client({
    authStrategy: new LocalAuth({ clientId: String(userId), dataPath: '.wwebjs_auth' }),
    puppeteer: {
      headless: true,
      executablePath: _exec(),
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    },
  });

  client.on('qr', async (qr) => {
    try {
      session.qr = await QRCode.toDataURL(qr);
      session.status = 'pending';
      sendWebhook(userId, 'qr', { qr_base64: session.qr });
    } catch (err) {
      console.error('[bridge] qr encode error', err);
    }
  });

  client.on('ready', async () => {
    session.status = 'ready';
    session.qr = null;
    console.log(`[bridge] user=${userId} ready`);
    sendWebhook(userId, 'ready', { ts: Date.now() });
  });

  client.on('authenticated', () => {
    session.status = 'authenticated';
  });

  client.on('auth_failure', (msg) => {
    session.status = 'error';
    console.error(`[bridge] user=${userId} auth_failure`, msg);
    sendWebhook(userId, 'disconnected', { reason: 'auth_failure', detail: msg });
  });

  client.on('disconnected', (reason) => {
    session.status = 'disconnected';
    console.log(`[bridge] user=${userId} disconnected: ${reason}`);
    sendWebhook(userId, 'disconnected', { reason });
    clients.delete(userId);
  });

  client.on('message', async (m) => {
    // Forward inbound message to backend
    try {
      const contact = await m.getContact();
      sendWebhook(userId, 'message', {
        from: m.from,
        direction: 'in',
        text: m.body,
        ts: m.timestamp ? m.timestamp * 1000 : Date.now(),
        meta: {
          chat_id: m.from,
          contact_name: contact?.pushname || contact?.name || null,
          is_group: m.from.endsWith('@g.us'),
        },
      });
    } catch (err) {
      console.error('[bridge] message handler err', err);
    }
  });

  client.initialize().catch((err) => {
    session.status = 'error';
    console.error(`[bridge] user=${userId} init error`, err);
  });

  const entry = { client, session };
  clients.set(userId, entry);
  return entry;
}

function get(userId) {
  return clients.get(userId);
}

async function destroy(userId) {
  const entry = clients.get(userId);
  if (!entry) return;
  try {
    await entry.client.logout();
  } catch (_) {
    /* ignore */
  }
  try {
    await entry.client.destroy();
  } catch (_) {
    /* ignore */
  }
  clients.delete(userId);
}

async function send(userId, to, text) {
  const entry = clients.get(userId);
  if (!entry) throw new Error('no_session');
  if (entry.session.status !== 'ready') throw new Error('not_ready');
  return entry.client.sendMessage(to, text);
}

async function fetchHistory(userId, contactId, limit = 1000) {
  const entry = clients.get(userId);
  if (!entry) throw new Error('no_session');
  if (entry.session.status !== 'ready') throw new Error('not_ready');
  const chat = await entry.client.getChatById(contactId);
  const msgs = await chat.fetchMessages({ limit });
  return msgs.map((m) => ({
    from: m.from,
    to: m.to,
    direction: m.fromMe ? 'out' : 'in',
    text: m.body,
    ts: m.timestamp ? m.timestamp * 1000 : null,
    meta: { id: m.id?._serialized },
  }));
}

async function listContacts(userId) {
  const entry = clients.get(userId);
  if (!entry) throw new Error('no_session');
  const cs = await entry.client.getContacts();
  return cs
    .filter((c) => c.id?._serialized && (c.isUser || c.isGroup))
    .map((c) => ({
      wa_id: c.id._serialized,
      name: c.name || c.pushname || c.shortName || null,
      is_group: !!c.isGroup,
    }));
}

async function shutdown() {
  for (const [uid] of clients) {
    await destroy(uid);
  }
}

module.exports = { start, get, destroy, send, fetchHistory, listContacts, shutdown };
