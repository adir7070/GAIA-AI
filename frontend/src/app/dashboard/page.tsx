'use client';

import { useGaiaSocket } from '@/hooks/useSocket';
import SuggestionCard from '@/components/SuggestionCard';
import { useSuggestions } from '@/store/suggestionsStore';

export default function DashboardPage() {
  useGaiaSocket();
  const items = useSuggestions((s) => s.items);

  return (
    <main className="min-h-screen px-4 py-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">לוח הצעות</h1>

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
