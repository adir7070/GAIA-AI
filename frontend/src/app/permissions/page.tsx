'use client';

import { useEffect, useState } from 'react';
import { listContacts, type Contact } from '@/services/api';
import ContactToggle from '@/components/ContactToggle';

export default function PermissionsPage() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listContacts()
      .then(setContacts)
      .finally(() => setLoading(false));
  }, []);

  const filtered = contacts.filter((c) =>
    [c.name, c.wa_id].filter(Boolean).join(' ').toLowerCase().includes(filter.toLowerCase()),
  );

  return (
    <main className="min-h-screen px-4 py-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">הרשאות</h1>
      <p className="text-sm text-gray-600 mb-4">
        בחר עבור אילו אנשי קשר/קבוצות המערכת רשאית להציע תשובות. אף תשובה לא נשלחת ללא אישור שלך.
      </p>
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
          <div className="text-sm text-gray-500">לא נמצאו אנשי קשר.</div>
        ) : (
          filtered.map((c) => <ContactToggle key={c.id} c={c} />)
        )}
      </div>
    </main>
  );
}
