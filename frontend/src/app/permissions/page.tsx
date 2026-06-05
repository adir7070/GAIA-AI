'use client';

import { useCallback, useEffect, useState } from 'react';
import { listContacts, syncContacts, type Contact } from '@/services/api';
import ContactToggle from '@/components/ContactToggle';

export default function PermissionsPage() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const doSync = useCallback(async () => {
    setSyncing(true);
    setMsg(null);
    try {
      const list = await syncContacts();
      setContacts(list);
      setMsg(`סונכרנו ${list.length} אנשי קשר`);
    } catch {
      setMsg('סנכרון נכשל — ודא שה-WhatsApp מחובר (עמוד "חבר WhatsApp")');
    } finally {
      setSyncing(false);
    }
  }, []);

  useEffect(() => {
    // Load existing contacts; if none yet, auto-sync from WhatsApp once.
    listContacts()
      .then(async (list) => {
        setContacts(list);
        if (list.length === 0) await doSync();
      })
      .finally(() => setLoading(false));
  }, [doSync]);

  const matches = contacts.filter((c) =>
    [c.name, c.wa_id].filter(Boolean).join(' ').toLowerCase().includes(filter.toLowerCase()),
  );
  // Cap rendering so a large address book doesn't freeze the page; search narrows it.
  const filtered = matches.slice(0, 300);

  return (
    <main className="min-h-screen px-4 py-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-1">
        <h1 className="text-2xl font-bold">הרשאות</h1>
        <button className="btn-ghost" onClick={doSync} disabled={syncing}>
          {syncing ? 'מסנכרן…' : '↻ סנכרן אנשי קשר'}
        </button>
      </div>
      <p className="text-sm text-gray-600 mb-2">
        בחר עבור אילו אנשי קשר/קבוצות המערכת רשאית להציע תשובות. אף תשובה לא נשלחת ללא אישור שלך.
      </p>
      {msg && <div className="text-sm text-brand-700 mb-3">{msg}</div>}
      <input
        className="field mb-4"
        placeholder="חיפוש…"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
      />
      <div className="card">
        {loading ? (
          <div className="text-sm text-gray-500">טוען…</div>
        ) : filtered.length === 0 ? (
          <div className="text-sm text-gray-500">
            לא נמצאו אנשי קשר. ודא ש-WhatsApp מחובר, ואז לחץ "↻ סנכרן אנשי קשר".
          </div>
        ) : (
          <>
            {matches.length > filtered.length && (
              <div className="text-xs text-gray-500 mb-2">
                מציג {filtered.length} מתוך {matches.length} — חפש כדי לצמצם.
              </div>
            )}
            {filtered.map((c) => <ContactToggle key={c.id} c={c} />)}
          </>
        )}
      </div>
    </main>
  );
}
