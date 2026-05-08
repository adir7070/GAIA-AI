'use client';

import { useState } from 'react';
import type { Contact } from '@/services/api';
import { patchContact } from '@/services/api';

export default function ContactToggle({ c, onChange }: { c: Contact; onChange?: (c: Contact) => void }) {
  const [allowed, setAllowed] = useState(c.allowed);
  const [busy, setBusy] = useState(false);

  const toggle = async () => {
    setBusy(true);
    try {
      const updated = await patchContact(c.id, { allowed: !allowed });
      setAllowed(updated.allowed);
      onChange?.(updated);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex items-center justify-between border-b border-gray-100 py-2">
      <div>
        <div className="text-sm font-medium">{c.name || c.wa_id}</div>
        <div className="text-xs text-gray-500">
          {c.is_group ? 'קבוצה' : 'איש קשר'} · {c.wa_id}
        </div>
      </div>
      <button
        disabled={busy}
        onClick={toggle}
        className={`btn ${allowed ? 'bg-brand-600 text-white' : 'bg-gray-200 text-gray-700'}`}
      >
        {allowed ? 'מופעל' : 'כבוי'}
      </button>
    </div>
  );
}
