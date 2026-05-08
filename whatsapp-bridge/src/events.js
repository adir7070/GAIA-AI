/**
 * Webhook out: bridge -> backend, HMAC-signed.
 */
const axios = require('axios');
const crypto = require('crypto');

const BACKEND = process.env.BACKEND_INTERNAL_URL || 'http://backend:8000';
const SECRET = process.env.BRIDGE_SECRET || '';

function sign(bodyStr) {
  return crypto.createHmac('sha256', SECRET).update(bodyStr).digest('hex');
}

async function sendWebhook(userId, type, payload) {
  const body = { user_id: Number(userId), type, payload };
  const bodyStr = JSON.stringify(body);
  const signature = sign(bodyStr);
  try {
    await axios.post(`${BACKEND}/whatsapp/internal/event`, body, {
      headers: {
        'Content-Type': 'application/json',
        'X-Bridge-Signature': signature,
      },
      timeout: 5000,
    });
  } catch (err) {
    const msg = err?.response?.status
      ? `${err.response.status} ${JSON.stringify(err.response.data)}`
      : err.message;
    console.error(`[bridge] webhook ${type} failed: ${msg}`);
  }
}

module.exports = { sendWebhook };
