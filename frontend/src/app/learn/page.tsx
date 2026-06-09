'use client';

import { useEffect, useState } from 'react';
import { useGaiaSocket } from '@/hooks/useSocket';
import { useSuggestions } from '@/store/suggestionsStore';
import SuggestionCard from '@/components/SuggestionCard';
import { teachGap } from '@/services/api';
import type { ProfileGap } from '@/types/learn';

const GAPS_KEY = 'gaia_profile_gaps';

function loadGaps(): ProfileGap[] {
  try {
    const raw = localStorage.getItem(GAPS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
}

function persistGaps(gaps: ProfileGap[]) {
  try { localStorage.setItem(GAPS_KEY, JSON.stringify(gaps)); } catch { /* ignore */ }
}

function GapCard({ gap, onTaught, onDelete }: {
  gap: ProfileGap;
  onTaught: (id: string) => void;
  onDelete: (id: string) => void;
}) {
  const [answer, setAnswer] = useState('');
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  const submit = async () => {
    const text = answer.trim();
    if (!text || busy) return;
    setBusy(true);
    try {
      await teachGap(gap.question, text);
      setDone(true);
      setTimeout(() => onTaught(gap.id), 800);
    } catch {
      setBusy(false);
    }
  };

  if (done) {
    return (
      <div className="card border-emerald-200 bg-emerald-50 text-sm text-emerald-700 text-center py-3">
        ✓ נשמר — המודל ילמד מזה!
      </div>
    );
  }

  return (
    <div className="card border-amber-200 bg-amber-50">
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex-1">
          <div className="text-xs text-gray-500 mb-0.5">שאלה שנשאלתי:</div>
          <div className="text-sm font-medium">{gap.question}</div>
        </div>
        <button
          onClick={() => onDelete(gap.id)}
          className="text-gray-300 hover:text-rose-400 text-lg leading-none flex-shrink-0"
          title="הסר"
        >
          ✕
        </button>
      </div>

      <div className="text-xs text-gray-400 mb-1">תשובת המודל (לא ידע):</div>
      <div className="text-sm text-gray-500 mb-3 italic">{gap.reply}</div>

      <div className="text-xs font-semibold text-amber-800 mb-1">
        איך היית עונה אמיתית על זה?
      </div>
      <textarea
        className="field resize-none w-full mb-2"
        rows={2}
        placeholder="כתוב את התשובה האמיתית שלך…"
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), submit())}
      />
      <div className="flex gap-2 items-center">
        <button
          className="btn-primary text-sm"
          disabled={busy || !answer.trim()}
          onClick={submit}
        >
          {busy ? 'שומר…' : '✓ לימד את המודל'}
        </button>
        <span className="text-xs text-gray-400">Enter לשמירה מהירה</span>
      </div>
    </div>
  );
}

export default function LearnPage() {
  useGaiaSocket();
  const items = useSuggestions((s) => s.items.filter((i) => i.label !== 'ANSWER_NOW'));
  const [gaps, setGaps] = useState<ProfileGap[]>([]);

  useEffect(() => {
    setGaps(loadGaps());
  }, []);

  const onTaught = (id: string) => {
    setGaps((g) => {
      const next = g.filter((x) => x.id !== id);
      persistGaps(next);
      return next;
    });
  };

  const onDelete = (id: string) => {
    setGaps((g) => {
      const next = g.filter((x) => x.id !== id);
      persistGaps(next);
      return next;
    });
  };

  return (
    <main className="min-h-screen px-4 py-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">מרכז למידה</h1>
      <p className="text-sm text-gray-600 mb-4">
        כאן מופיעות שאלות שהמודל לא ידע לענות עליהן. תשובתך תהפוך להדגמה אמיתית — המודל ילמד ממנה.
      </p>

      {/* Profile gaps from playground */}
      {gaps.length > 0 && (
        <section className="mb-6">
          <div className="flex items-center gap-1.5 mb-3">
            <span>💡</span>
            <h2 className="text-sm font-semibold text-amber-700">
              פערי פרופיל — שאלות שהמודל לא ידע לענות עליהן ({gaps.length})
            </h2>
          </div>
          <div className="space-y-3">
            {gaps.map((g) => (
              <GapCard key={g.id} gap={g} onTaught={onTaught} onDelete={onDelete} />
            ))}
          </div>
        </section>
      )}

      {/* Real-time WhatsApp suggestions */}
      {items.length > 0 && (
        <section>
          <h2 className="text-sm font-semibold text-gray-500 mb-2">הצעות מוואטסאפ</h2>
          {items.map((s) => <SuggestionCard key={s.suggestion_id} s={s} />)}
        </section>
      )}

      {gaps.length === 0 && items.length === 0 && (
        <div className="card text-center text-gray-500">
          לא נמצאו פריטים ללימוד כרגע.
        </div>
      )}
    </main>
  );
}
