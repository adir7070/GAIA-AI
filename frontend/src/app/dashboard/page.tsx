'use client';

import { useEffect } from 'react';
import { useGaiaSocket } from '@/hooks/useSocket';
import SuggestionCard from '@/components/SuggestionCard';
import { useSuggestions } from '@/store/suggestionsStore';
import { listSuggestions } from '@/services/api';

export default function DashboardPage() {
  useGaiaSocket();
  const { items, push } = useSuggestions((s) => ({ items: s.items, push: s.push }));

  useEffect(() => {
    listSuggestions(50).then((history) => {
      const existingIds = new Set(items.map((i) => i.suggestion_id));
      history.forEach((s) => {
        if (!existingIds.has(s.suggestion_id)) {
          push({
            suggestion_id: s.suggestion_id,
            contact_id: s.contact_id,
            contact_name: s.contact_name ?? String(s.contact_id),
            incoming: s.incoming,
            suggestion: s.suggestion,
            confidence: s.confidence,
            label: s.label,
          });
        }
      });
    }).catch(() => {/* history is non-critical */});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
