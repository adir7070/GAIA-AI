'use client';

import { useEffect, useState } from 'react';
import { useGaiaSocket } from '@/hooks/useSocket';
import { useSuggestions } from '@/store/suggestionsStore';
import SuggestionCard from '@/components/SuggestionCard';
import { teachGap, listTaught, deleteTaught, type TaughtPair } from '@/services/api';
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
        <button onClick={() => onDelete(gap.id)} className="text-gray-300 hover:text-rose-400 text-lg leading-none flex-shrink-0" title="הסר">✕</button>
      </div>
      <div className="text-xs text-gray-400 mb-1">תשובת המודל (לא ידע):</div>
      <div className="text-sm text-gray-500 mb-3 italic">{gap.reply}</div>
      <div className="text-xs font-semibold text-amber-800 mb-1">איך היית עונה אמיתית על זה?</div>
      <textarea
        className="field resize-none w-full mb-2"
        rows={2}
        placeholder="כתוב את התשובה האמיתית שלך…"
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), submit())}
      />
      <div className="flex gap-2 items-center">
        <button className="btn-primary text-sm" disabled={busy || !answer.trim()} onClick={submit}>
          {busy ? 'שומר…' : '✓ לימד את המודל'}
        </button>
        <span className="text-xs text-gray-400">Enter לשמירה מהירה</span>
      </div>
    </div>
  );
}

function AddPairForm({ onAdded }: { onAdded: () => void }) {
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  const submit = async () => {
    if (!question.trim() || !answer.trim() || busy) return;
    setBusy(true);
    try {
      await teachGap(question.trim(), answer.trim());
      setDone(true);
      setQuestion('');
      setAnswer('');
      setTimeout(() => { setDone(false); setOpen(false); onAdded(); }, 1000);
    } finally {
      setBusy(false);
    }
  };

  if (!open) {
    return (
      <button
        className="btn-primary w-full mb-6"
        onClick={() => setOpen(true)}
      >
        + הוסף שאלה ותשובה ידנית
      </button>
    );
  }

  return (
    <div className="card border-brand-200 bg-brand-50 mb-6">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold">הוסף זוג שאלה ותשובה</h3>
        <button onClick={() => setOpen(false)} className="text-gray-400 hover:text-gray-600 text-lg leading-none">✕</button>
      </div>
      {done ? (
        <div className="text-sm text-emerald-700 text-center py-2">✓ נשמר! המודל ילמד מזה.</div>
      ) : (
        <>
          <div className="mb-2">
            <label className="block text-xs text-gray-600 mb-1">שאלה שאפשר לשאול אותך</label>
            <input
              className="field w-full"
              placeholder='למשל: "מה אתה הכי אוהב לאכול?"'
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
          </div>
          <div className="mb-3">
            <label className="block text-xs text-gray-600 mb-1">התשובה האמיתית שלך</label>
            <textarea
              className="field resize-none w-full"
              rows={2}
              placeholder='למשל: "מלוואח פיצה, אני משוגע עליה 😍"'
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), submit())}
            />
          </div>
          <div className="flex gap-2">
            <button className="btn-primary" disabled={busy || !question.trim() || !answer.trim()} onClick={submit}>
              {busy ? 'שומר…' : 'שמור'}
            </button>
            <button className="btn-ghost" onClick={() => setOpen(false)}>ביטול</button>
          </div>
        </>
      )}
    </div>
  );
}

function TaughtHistory({ pairs, onDelete }: { pairs: TaughtPair[]; onDelete: (id: string) => void }) {
  const [deleting, setDeleting] = useState<string | null>(null);

  const handleDelete = async (id: string) => {
    setDeleting(id);
    try {
      await deleteTaught(id);
      onDelete(id);
    } finally {
      setDeleting(null);
    }
  };

  if (pairs.length === 0) return null;

  return (
    <section className="mt-6">
      <div className="flex items-center gap-1.5 mb-3">
        <span>📚</span>
        <h2 className="text-sm font-semibold text-gray-700">היסטוריית לימוד — כל מה שלימדת את המודל ({pairs.length})</h2>
      </div>
      <div className="text-xs text-gray-500 mb-3 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2">
        ✓ עובדות אלה נשמרות לצמיתות ב-Qdrant — הן קיימות גם אחרי איפוס צ׳אט ומשפיעות על כל תשובה עתידית.
      </div>
      <div className="space-y-2">
        {pairs.map((p) => (
          <div key={p.id} className="card py-2 flex items-start gap-3">
            <div className="flex-1 min-w-0">
              <div className="text-xs text-gray-400 mb-0.5">שאלה</div>
              <div className="text-sm text-gray-700 truncate">{p.incoming}</div>
              <div className="text-xs text-gray-400 mt-1 mb-0.5">תשובה שלימדת</div>
              <div className="text-sm font-medium">{p.reply}</div>
            </div>
            <button
              onClick={() => handleDelete(p.id)}
              disabled={deleting === p.id}
              className="text-gray-300 hover:text-rose-400 text-sm flex-shrink-0 mt-1"
              title="מחק"
            >
              {deleting === p.id ? '…' : '✕'}
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}

export default function LearnPage() {
  useGaiaSocket();
  const items = useSuggestions((s) => s.items.filter((i) => i.label !== 'ANSWER_NOW'));
  const [gaps, setGaps] = useState<ProfileGap[]>([]);
  const [taught, setTaught] = useState<TaughtPair[]>([]);
  const [loadingTaught, setLoadingTaught] = useState(true);

  useEffect(() => {
    setGaps(loadGaps());
    listTaught()
      .then(setTaught)
      .finally(() => setLoadingTaught(false));
  }, []);

  const onTaught = (id: string) => {
    setGaps((g) => {
      const next = g.filter((x) => x.id !== id);
      persistGaps(next);
      return next;
    });
    // Refresh taught list
    listTaught().then(setTaught);
  };

  const onDeleteGap = (id: string) => {
    setGaps((g) => {
      const next = g.filter((x) => x.id !== id);
      persistGaps(next);
      return next;
    });
  };

  const onDeleteTaught = (id: string) => {
    setTaught((t) => t.filter((x) => x.id !== id));
  };

  return (
    <main className="min-h-screen px-4 py-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">מרכז למידה</h1>
      <p className="text-sm text-gray-600 mb-4">
        כאן מופיעות שאלות שהמודל לא ידע לענות. תשובתך תהפוך להדגמה אמיתית — המודל ילמד ממנה לצמיתות.
      </p>

      {/* Manual add */}
      <AddPairForm onAdded={() => listTaught().then(setTaught)} />

      {/* Unanswered gaps from playground */}
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
              <GapCard key={g.id} gap={g} onTaught={onTaught} onDelete={onDeleteGap} />
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
        <div className="card text-center text-gray-500 text-sm">
          אין פערים ללימוד כרגע — כל שאלה שהמודל לא ידע לענות עליה תופיע כאן.
        </div>
      )}

      {/* Taught history */}
      {!loadingTaught && (
        <TaughtHistory pairs={taught} onDelete={onDeleteTaught} />
      )}
    </main>
  );
}
