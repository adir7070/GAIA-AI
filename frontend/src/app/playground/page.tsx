'use client';

import { useRef, useState } from 'react';
import { testReply, type ReplySource } from '@/services/api';

type Turn = { role: 'incoming' | 'model'; text: string; sources?: ReplySource[] };

export default function PlaygroundPage() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  const send = async () => {
    const text = input.trim();
    if (!text || busy) return;
    setErr(null);
    setInput('');
    setTurns((t) => [...t, { role: 'incoming', text }]);
    setBusy(true);
    try {
      const r = await testReply(text);
      setTurns((t) => [...t, { role: 'model', text: r.suggestion, sources: r.sources }]);
    } catch (e: any) {
      setErr(e?.response?.data?.detail || 'יצירת התשובה נכשלה');
    } finally {
      setBusy(false);
      setTimeout(() => endRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
    }
  };

  return (
    <main className="min-h-screen px-4 py-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">צ׳אט עם עצמי (בדיקת המודל)</h1>
      <p className="text-sm text-gray-600 mb-4">
        כתוב הודעה כאילו מישהו שלח לך אותה — והמודל יענה <b>בסגנון שלך</b>. כך אפשר לבחון איך המודל למד אותך,
        ולכוונן את הפרופיל בהתאם.
      </p>

      <div className="card min-h-[50vh] flex flex-col gap-3 mb-3">
        {turns.length === 0 ? (
          <div className="text-sm text-gray-400 m-auto text-center">
            לדוגמה: "היי מה קורה? יש לך זמן לשיחה מחר?"<br />— ותראה איך המודל יענה כמוך.
          </div>
        ) : (
          turns.map((t, i) => (
            <div
              key={i}
              className={`flex flex-col gap-1 ${t.role === 'incoming' ? 'items-start' : 'items-end'}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-3 py-2 text-sm whitespace-pre-wrap ${
                  t.role === 'incoming'
                    ? 'bg-gray-100 text-gray-800 rounded-bl-sm'
                    : 'bg-brand-600 text-white rounded-br-sm'
                }`}
              >
                {t.role === 'model' && (
                  <div className="text-[10px] opacity-70 mb-0.5">המודל (בסגנון שלך)</div>
                )}
                {t.text}
              </div>
              {t.role === 'model' && t.sources && t.sources.length > 0 && (
                <details className="max-w-[85%] text-xs text-gray-600 bg-gray-50 border border-gray-100 rounded-lg px-2 py-1">
                  <summary className="cursor-pointer select-none">
                    למה ענה ככה? — דוגמאות אמיתיות שלך לשיחות דומות ({t.sources.length})
                  </summary>
                  <ul className="mt-1 space-y-1.5">
                    {t.sources.map((s, j) => (
                      <li key={j} className="border-r-2 border-gray-200 pr-2">
                        <div className="text-gray-500">קיבלת: {s.incoming}</div>
                        <div className="text-gray-800">ענית: {s.reply}</div>
                        <div className="opacity-40">דמיון: {s.score}</div>
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          ))
        )}
        {busy && <div className="text-xs text-gray-400 self-end">המודל מנסח…</div>}
        <div ref={endRef} />
      </div>

      {err && <div className="text-sm text-rose-700 mb-2">{err}</div>}

      <div className="flex gap-2">
        <input
          className="field flex-1"
          placeholder="כתוב הודעה נכנסת לבדיקה…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
        />
        <button className="btn-primary" onClick={send} disabled={busy || !input.trim()}>
          {busy ? '…' : 'שלח'}
        </button>
      </div>
      <p className="text-xs text-gray-400 mt-2">
        טיפ: ערוך את <b>הפרופיל שלי</b> ואז חזור לכאן — תראה איך התשובות משתנות.
      </p>
    </main>
  );
}
