'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  analyzeStyleProfile,
  getStyleProfile,
  saveStyleProfile,
  type StyleProfile,
  type StyleTraits,
} from '@/services/api';

const SCALAR: { key: keyof StyleTraits; label: string }[] = [
  { key: 'tone', label: 'טון' },
  { key: 'formality', label: 'רמת רשמיות' },
  { key: 'typical_length', label: 'אורך תשובה אופייני' },
  { key: 'emoji_usage', label: "שימוש באימוג'י" },
  { key: 'slang', label: 'סלנג / שפה' },
  { key: 'punctuation', label: 'פיסוק' },
];
const LISTS: { key: keyof StyleTraits; label: string }[] = [
  { key: 'personality', label: 'תכונות אופי' },
  { key: 'common_phrases', label: 'ביטויים נפוצים' },
  { key: 'languages', label: 'שפות' },
];

export default function ProfilePage() {
  const [summary, setSummary] = useState('');
  const [traits, setTraits] = useState<StyleTraits>({});
  const [count, setCount] = useState(0);
  const [hasProfile, setHasProfile] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<'analyze' | 'save' | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const apply = (p: StyleProfile | null) => {
    if (!p) return;
    setSummary(p.summary || '');
    setTraits(p.traits || {});
    setHasProfile(true);
  };

  useEffect(() => {
    getStyleProfile()
      .then((d) => {
        setCount(d.message_count);
        apply(d.profile);
      })
      .finally(() => setLoading(false));
  }, []);

  const analyze = async () => {
    setBusy('analyze');
    setErr(null);
    setMsg(null);
    try {
      const d = await analyzeStyleProfile();
      apply(d.profile);
      setMsg('הניתוח הושלם — זה מה שהמודל הבין עליך. אפשר לערוך ולשמור.');
    } catch (e: any) {
      setErr(e?.response?.data?.detail || 'הניתוח נכשל');
    } finally {
      setBusy(null);
    }
  };

  const save = async () => {
    setBusy('save');
    setErr(null);
    setMsg(null);
    try {
      const d = await saveStyleProfile(summary, traits);
      apply(d.profile);
      setMsg('נשמר! מעכשיו המודל יענה לפי הפרופיל הזה.');
    } catch (e: any) {
      setErr(e?.response?.data?.detail || 'השמירה נכשלה');
    } finally {
      setBusy(null);
    }
  };

  const setScalar = (k: keyof StyleTraits, v: string) =>
    setTraits((t) => ({ ...t, [k]: v }));
  const setList = (k: keyof StyleTraits, v: string) =>
    setTraits((t) => ({ ...t, [k]: v.split(',').map((s) => s.trim()).filter(Boolean) }));
  const listVal = (k: keyof StyleTraits) => {
    const v = traits[k];
    return Array.isArray(v) ? v.join(', ') : (v ?? '');
  };

  return (
    <main className="min-h-screen px-4 py-6 max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-1">
        <h1 className="text-2xl font-bold">הפרופיל שלי</h1>
        <Link href="/dashboard" className="btn-ghost text-sm">← חזרה ללוח</Link>
      </div>
      <p className="text-sm text-gray-600 mb-4">
        כך המודל הבין מי אתה ואיך אתה עונה — מתוך ההודעות שלך. אפשר לערוך כל דבר; המודל יענה לפי מה שתשמור כאן.
      </p>

      {msg && <div className="text-sm text-emerald-700 bg-emerald-50 rounded-lg p-2 mb-3">{msg}</div>}
      {err && <div className="text-sm text-rose-700 bg-rose-50 rounded-lg p-2 mb-3">{err}</div>}

      {loading ? (
        <div className="card text-sm text-gray-500">טוען…</div>
      ) : !hasProfile ? (
        <div className="card text-center">
          <p className="text-gray-700 mb-1">עוד לא נותח פרופיל.</p>
          <p className="text-xs text-gray-500 mb-4">
            נמצאו {count} הודעות שלך לניתוח.{' '}
            {count === 0 && 'אשר אנשי קשר בעמוד "הרשאות" כדי לייבא היסטוריה, ואז נתח.'}
          </p>
          <button className="btn-primary" onClick={analyze} disabled={busy !== null}>
            {busy === 'analyze' ? 'מנתח…' : 'נתח את הסגנון שלי'}
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="card">
            <label className="block text-sm font-semibold mb-1">מי אני (סיכום)</label>
            <textarea
              className="field"
              rows={4}
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
            />
          </div>

          <div className="card">
            <h2 className="font-semibold mb-3">תכונות הסגנון</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {SCALAR.map(({ key, label }) => (
                <div key={key}>
                  <label className="block text-xs text-gray-600 mb-1">{label}</label>
                  <input
                    className="field"
                    value={(traits[key] as string) ?? ''}
                    onChange={(e) => setScalar(key, e.target.value)}
                  />
                </div>
              ))}
            </div>
            <div className="mt-3 space-y-3">
              {LISTS.map(({ key, label }) => (
                <div key={key}>
                  <label className="block text-xs text-gray-600 mb-1">{label} (מופרד בפסיקים)</label>
                  <input className="field" value={listVal(key)} onChange={(e) => setList(key, e.target.value)} />
                </div>
              ))}
            </div>
          </div>

          <div className="flex gap-2">
            <button className="btn-primary" onClick={save} disabled={busy !== null}>
              {busy === 'save' ? 'שומר…' : 'שמור שינויים'}
            </button>
            <button className="btn-ghost" onClick={analyze} disabled={busy !== null}>
              {busy === 'analyze' ? 'מנתח…' : '↻ נתח מחדש'}
            </button>
          </div>
          <p className="text-xs text-gray-400">מבוסס על {count} מההודעות שלך.</p>
        </div>
      )}
    </main>
  );
}
