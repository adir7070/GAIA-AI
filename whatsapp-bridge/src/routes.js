/**
 * HTTP routes registered on the Express app.
 */

function register(app, sessions) {
  app.post('/sessions', async (req, res) => {
    const userId = Number(req.body?.user_id);
    if (!userId) return res.status(400).json({ error: 'user_id required' });
    const entry = await sessions.start(userId);
    return res.json({ session_id: String(userId), status: entry.session.status });
  });

  app.get('/sessions/:userId/qr', (req, res) => {
    const userId = Number(req.params.userId);
    const entry = sessions.get(userId);
    if (!entry) return res.status(404).json({ status: 'not_found' });
    return res.json({ qr_base64: entry.session.qr, status: entry.session.status });
  });

  app.get('/sessions/:userId/status', (req, res) => {
    const userId = Number(req.params.userId);
    const entry = sessions.get(userId);
    if (!entry) return res.status(404).json({ status: 'not_found' });
    return res.json({ status: entry.session.status });
  });

  app.get('/sessions/:userId/contacts', async (req, res) => {
    const userId = Number(req.params.userId);
    try {
      const list = await sessions.listContacts(userId);
      return res.json({ contacts: list });
    } catch (err) {
      return res.status(400).json({ error: err.message });
    }
  });

  app.get('/sessions/:userId/history', async (req, res) => {
    const userId = Number(req.params.userId);
    const contactId = req.query.contact_id;
    const limit = Number(req.query.limit || 1000);
    if (!contactId) return res.status(400).json({ error: 'contact_id required' });
    try {
      const messages = await sessions.fetchHistory(userId, contactId, limit);
      return res.json({ messages });
    } catch (err) {
      return res.status(400).json({ error: err.message });
    }
  });

  app.post('/sessions/:userId/send', async (req, res) => {
    const userId = Number(req.params.userId);
    const { to, text } = req.body || {};
    if (!to || !text) return res.status(400).json({ error: 'to and text required' });
    try {
      await sessions.send(userId, to, text);
      return res.json({ ok: true });
    } catch (err) {
      return res.status(400).json({ error: err.message });
    }
  });

  app.delete('/sessions/:userId', async (req, res) => {
    const userId = Number(req.params.userId);
    await sessions.destroy(userId);
    return res.json({ ok: true });
  });
}

module.exports = { register };
