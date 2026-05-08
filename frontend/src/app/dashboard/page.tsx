'use client';

import Link from 'next/link';
import { useGaiaSocket } from '@/hooks/useSocket';
import SuggestionCard from '@/components/SuggestionCard';
import { useSuggestions } from '@/store/suggestionsStore';

export default function DashboardPage() {
  useGaiaSocket();
  const items = useSuggestions((s) => s.items);

  return (
    <main className="min-h-screen px-4 py-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">לוח הצעות</h1>
        <nav className="flex gap-2 text-sm">
          <Link href="/permissions" className="btn-ghost">הרשאות</Link>
          <Link href="/learn" className="btn-ghost">לימוד</Link>
          <Link href="/analytics" className="btn-ghost">סטטיסטיקות</Link>
          <Link href="/settings" className="btn-ghost">הגדרות</Link>
        </nav>
      </div>

      {items.length === 0 ? (
        <div className="card text-center text-gray-500">
          אין הצעות פעילות. הצעות חדשות יופיעו כאן בזמן אמת כשמגיעות הודעות.
        </div>
      ) : (
        items.map((s) => <SuggestionCard key={s.suggestion_id} s={s} />)
      )}
    </main>
  );
}
