'use client';

import { useEffect, useState } from 'react';
import { analyticsSummary } from '@/services/api';

export default function AnalyticsPage() {
  const [data, setData] = useState<any>(null);
  useEffect(() => {
    analyticsSummary().then(setData);
  }, []);

  if (!data) return <main className="p-6">טוען…</main>;

  const Stat = ({ label, value }: { label: string; value: string | number | null }) => (
    <div className="card">
      <div className="text-sm text-gray-500">{label}</div>
      <div className="text-2xl font-bold mt-1">{value ?? '—'}</div>
    </div>
  );

  return (
    <main className="min-h-screen px-4 py-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">סטטיסטיקות (30 ימים)</h1>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Stat label="הצעות" value={data.suggestions} />
        <Stat label="פידבק" value={data.feedback} />
        <Stat label="אושרו" value={data.approved} />
        <Stat label="נערכו" value={data.edited} />
        <Stat
          label="אחוז אישור"
          value={data.approval_rate != null ? `${(data.approval_rate * 100).toFixed(0)}%` : '—'}
        />
      </div>
    </main>
  );
}
