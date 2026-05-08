'use client';

import { useGaiaSocket } from '@/hooks/useSocket';
import { useSuggestions } from '@/store/suggestionsStore';
import SuggestionCard from '@/components/SuggestionCard';

export default function LearnPage() {
  useGaiaSocket();
  const items = useSuggestions((s) => s.items.filter((i) => i.label !== 'ANSWER_NOW'));

  return (
    <main className="min-h-screen px-4 py-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">מרכז למידה</h1>
      <p className="text-sm text-gray-600 mb-4">
        כאן מופיעות שאלות שהמערכת לא בטוחה איך לענות. עריכה שלך תהפוך לדוגמה לאימון עתידי.
      </p>
      {items.length === 0 ? (
        <div className="card text-center text-gray-500">לא נמצאו פריטים ללימוד כרגע.</div>
      ) : (
        items.map((s) => <SuggestionCard key={s.suggestion_id} s={s} />)
      )}
    </main>
  );
}
