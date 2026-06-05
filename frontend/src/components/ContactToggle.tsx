'use client';

import { useState } from 'react';
import type { Contact } from '@/services/api';
import { patchContact } from '@/services/api';

// Controlled: reads `allowed` from the `c` prop so bulk actions (allow-all)
// and re-fetches are reflected immediately.
export default function ContactToggle({
  c,
  onChange,
}: {
  c: Contact;
  onChange?: (c: Contact) => void;
}) {
  const [busy, setBusy] = useState(false);

  const toggle = async () => {
    setBusy(true);
    try {
      const updated = await patchContact(c.id, { allowed: !c.allowed });
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
        className={`btn ${c.allowed ? 'bg-brand-600 text-white' : 'bg-gray-200 text-gray-700'}`}
      >
        {busy ? '…' : c.allowed ? 'מופעל' : 'כבוי'}
      </button>
    </div>
  );
}
