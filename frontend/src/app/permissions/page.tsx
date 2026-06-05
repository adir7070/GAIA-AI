'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  allowAllContacts,
  disallowAllContacts,
  listContacts,
  syncContacts,
  type Contact,
} from '@/services/api';
import ContactToggle from '@/components/ContactToggle';

type StatusFilter = 'all' | 'allowed' | 'blocked';

export default function PermissionsPage() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [filter, setFilter] = useState('');
  const [status, setStatus] = useState<StatusFilter>('all');
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [bulking, setBulking] = useState(false);
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
    listContacts()
      .then(async (list) => {
        setContacts(list);
        if (list.length === 0) await doSync();
      })
      .finally(() => setLoading(false));
  }, [doSync]);

  const onChange = (updated: Contact) =>
    setContacts((cs) => cs.map((c) => (c.id === updated.id ? updated : c)));

  const allowedCount = useMemo(() => contacts.filter((c) => c.allowed).length, [contacts]);

  const bulk = async (allow: boolean) => {
    const verb = allow ? 'לתת הרשאה ל' : 'לבטל הרשאה מ';
    if (!window.confirm(`האם אתה בטוח שברצונך ${verb}כל ${contacts.length} אנשי הקשר?`)) return;
    setBulking(true);
    setMsg(null);
    try {
      const list = allow ? await allowAllContacts() : await disallowAllContacts();
      setContacts(list);
      setMsg(allow ? `ניתנה הרשאה לכל ${list.length} אנשי הקשר` : 'בוטלה ההרשאה לכל אנשי הקשר');
    } catch {
      setMsg('הפעולה נכשלה');
    } finally {
      setBulking(false);
    }
  };

  const matches = useMemo(() => {
    const q = filter.toLowerCase();
    return contacts
      .filter((c) => (status === 'all' ? true : status === 'allowed' ? c.allowed : !c.allowed))
      .filter((c) => [c.name, c.wa_id].filter(Boolean).join(' ').toLowerCase().includes(q))
      // allowed first, then by name
      .sort((a, b) => Number(b.allowed) - Number(a.allowed) || (a.name || '').localeCompare(b.name || ''));
  }, [contacts, filter, status]);

  const shown = matches.slice(0, 300);

  const Tab = ({ v, label }: { v: StatusFilter; label: string }) => (
    <button
      onClick={() => setStatus(v)}
      className={`btn text-sm ${status === v ? 'bg-brand-600 text-white' : 'bg-gray-100 text-gray-700'}`}
    >
      {label}
    </button>
  );

  return (
    <main className="min-h-screen px-4 py-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-1 gap-2 flex-wrap">
        <h1 className="text-2xl font-bold">הרשאות</h1>
        <div className="flex gap-2 flex-wrap">
          <button className="btn-ghost text-sm" onClick={doSync} disabled={syncing || bulking}>
            {syncing ? 'מסנכרן…' : '↻ סנכרן'}
          </button>
          <button className="btn-primary text-sm" onClick={() => bulk(true)} disabled={bulking || syncing}>
            {bulking ? '…' : 'אשר הכל'}
          </button>
          <button className="btn-danger text-sm" onClick={() => bulk(false)} disabled={bulking || syncing}>
            בטל הכל
          </button>
        </div>
      </div>
      <p className="text-sm text-gray-600 mb-3">
        בחר עבור אילו אנשי קשר/קבוצות המערכת רשאית להציע תשובות. אף תשובה לא נשלחת ללא אישור שלך.
      </p>

      {msg && <div className="text-sm text-brand-700 mb-3">{msg}</div>}

      <div className="flex items-center gap-2 mb-3 flex-wrap">
        <Tab v="all" label={`הכל (${contacts.length})`} />
        <Tab v="allowed" label={`מורשים (${allowedCount})`} />
        <Tab v="blocked" label={`לא מורשים (${contacts.length - allowedCount})`} />
      </div>

      <input
        className="field mb-4"
        placeholder="חיפוש…"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
      />
      <div className="card">
        {loading ? (
          <div className="text-sm text-gray-500">טוען…</div>
        ) : shown.length === 0 ? (
          <div className="text-sm text-gray-500">
            לא נמצאו אנשי קשר. ודא ש-WhatsApp מחובר, ואז לחץ "↻ סנכרן".
          </div>
        ) : (
          <>
            {matches.length > shown.length && (
              <div className="text-xs text-gray-500 mb-2">
                מציג {shown.length} מתוך {matches.length} — חפש כדי לצמצם.
              </div>
            )}
            {shown.map((c) => (
              <ContactToggle key={c.id} c={c} onChange={onChange} />
            ))}
          </>
        )}
      </div>
    </main>
  );
}
